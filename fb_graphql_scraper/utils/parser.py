# -*- coding: utf-8 -*-
from seleniumwire.utils import decode
import json
from urllib.parse import parse_qs, unquote
from fb_graphql_scraper.utils.utils import *
from typing import Dict, List
from jsonpath_ng.ext import parse

def extract_json_path(data: Dict, path: str) -> List:
    """使用 JSONPath 從 JSON 資料中提取特定路徑的值"""
    json_path = parse(path)
    matches = json_path.find(data)
    return [match.value for match in matches]


class RequestsParser(object):
    def __init__(self, driver) -> None:
        self.driver = driver
        self.reaction_names = ["讚", "哈", "怒", "大心", "加油", "哇", "嗚"]
        self.en_reaction_names = ["like", "haha", "angry", "love", "care", "sorry", "wow"]

    def get_graphql_body_content(self, req_response, req_url):
        target_url = "https://www.facebook.com/api/graphql/"
        if req_response and req_url == target_url:
            response = req_response
            body = decode(response.body, response.headers.get(
                'Content-Encoding', 'identity'))
            body_content = body.decode("utf-8").split("\n")
            return body_content
        return None
    
    def _clean_res(self):
        self.feedback_list = []
        self.context_list = []
        self.creation_list = []
        self.owning_profile = []
        self.res_new = []
        self.attachments_list = []  # 新增附件列表的清理

    def parse_body(self, body_content):
        for each_body in body_content:
            json_data = json.loads(each_body)
            self.res_new.append(json_data)
            try:
                each_res = json_data['data']['node'].copy()
                each_feedback = find_feedback_with_subscription_target_id(each_res)
                if each_feedback:
                    self.feedback_list.append(each_feedback)
                    message_text = find_message_text(json_data)
                    creation_time = find_creation(json_data)
                    owing_profile = find_owning_profile(json_data)
                    
                    # 提取附件資訊並儲存到新的列表中
                    attachments = self.extract_attachments_from_json(json_data)
                    if not hasattr(self, 'attachments_list'):
                        self.attachments_list = []
                    self.attachments_list.append(attachments)
                    
                    if message_text:
                        self.context_list.append(message_text)
                    elif not message_text:
                        self.context_list.append(None)
                    if creation_time:
                        self.creation_list.append(creation_time)
                    self.owning_profile.append(owing_profile)

            # Did not display or record error message at here
            except Exception as e:
                pass

    def collect_posts(self):
        res_out = []
        for i, each in enumerate(self.feedback_list):
            # 建立反應字典 - 使用中文名稱
            reactions_dict = {}
            for reaction in each['top_reactions']['edges']:
                reaction_name = reaction['node']['localized_name']
                reaction_count = reaction['reaction_count']
                reactions_dict[reaction_name] = reaction_count
        
            # 確保所有反應類型都存在（如果沒有就設為0）
            reaction_names = ["讚", "哈", "哇", "怒", "加油", "大心", "嗚"]
            standardized_reactions = []
            for name in reaction_names:
                count = reactions_dict.get(name, 0)
                standardized_reactions.append({name: count})
        
            # 獲取對應的文字內容和創建時間
            text_content = self.context_list[i] if i < len(self.context_list) and self.context_list[i] else ""
            creation_timestamp = self.creation_list[i] if i < len(self.creation_list) else None
        
            # 將時間戳轉換為可讀格式
            if creation_timestamp:
                from datetime import datetime
                creation_time = datetime.fromtimestamp(int(creation_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                creation_time = ""
        
            # 建構貼文URL
            post_url = f"https://www.facebook.com/{each['subscription_target_id']}"
        
            # 使用 JSONPath 提取附件
            json_data = self.res_new[i] if i < len(self.res_new) else {}
            attachments = self.extract_attachments_from_json(json_data)
        
            res_out.append({
                "post_id": each['subscription_target_id'],
                "post_url": [post_url],
                "creation_time": creation_time,
                "attachments": attachments,
                "text": text_content,
                "total_reaction_count": each['reaction_count']['count'] if each['reaction_count'] else 0,
                "reactions": standardized_reactions,
                "comment_count": each['comment_rendering_instance']['comments']['total_count'] if each['comment_rendering_instance'] and each['comment_rendering_instance']['comments'] else 0,
                "share_count": each['share_count']['count'] if each['share_count'] else 0
            })
        return res_out

    def extract_attachments_from_json(self, json_data):
        """從 JSON 資料中提取附件 URL"""
        attachments = []

        try:
            # 使用 JSONPath 搜尋所有可能的附件 URL
            attachment_paths = [
                '$..attachments..url',  # 標準的 attachments.url 路徑
                # '$..image..uri',                 # 圖片 URI
                # '$..photo..image..uri',          # 照片圖片 URI
                # '$..video..playable_url',        # 影片播放 URL
                # '$..video..browser_native_hd_url', # 影片HD URL
                # '$..video..browser_native_sd_url', # 影片標清 URL
                # '$..media..image..uri',          # 媒體圖片 URI
                # '$..media..photo..image..uri'    # 媒體照片 URI
            ]

            # 搜尋每個路徑
            for path in attachment_paths:
                urls = extract_json_path(json_data, path)
                attachments.extend(urls)

            # 額外搜尋任何包含 Facebook CDN URL 的欄位
            video_urls = extract_json_path(json_data, '$..[?(@=~/https:\\/\\/video.*/))]')

            attachments.extend(video_urls)

        except Exception as e:
            # 如果 JSONPath 搜尋失敗，使用備用方法
            attachments = self.extract_attachments_fallback(json_data)

        unique_attachments = []
        for url in attachments:
            if (url and
                    isinstance(url, str) and
                    url not in unique_attachments and
                     url.startswith('https://video') or
                     url.startswith('https://external')):
                unique_attachments.append(url)

        return unique_attachments

    def extract_attachments_fallback(self, json_data):
        """備用的附件提取方法（遞迴搜尋）"""
        attachments = []

        def find_media_recursive(data):
            if isinstance(data, dict):
                # 查找圖片相關的 URL
                if 'image' in data and isinstance(data['image'], dict):
                    if 'uri' in data['image']:
                        attachments.append(data['image']['uri'])

                # 查找影片相關的 URL
                if 'video' in data and isinstance(data['video'], dict):
                    for video_key in ['playable_url', 'browser_native_hd_url', 'browser_native_sd_url']:
                        if video_key in data['video']:
                            attachments.append(data['video'][video_key])

                # 查找其他可能的媒體 URL
                for key, value in data.items():
                    if isinstance(value, str) and (
                            value.startswith('https://scontent') or value.startswith('https://video')):
                        attachments.append(value)
                    elif isinstance(value, (dict, list)):
                        find_media_recursive(value)

            elif isinstance(data, list):
                for item in data:
                    find_media_recursive(item)

        find_media_recursive(json_data)
        return attachments

    def convert_res_to_df(self, res_in):
        converted_data = []
        for post in res_in:
            converted_data.append({
                'post_id': post['post_id'],
                'post_url': post['post_url'][0] if post['post_url'] else '',
                'creation_time': post['creation_time'],
                'text': post['text'],
                'total_reaction_count': post['total_reaction_count'],
                'reactions': post['reactions'],
                'comment_count': post['comment_count'],
                'share_count': post['share_count']
            })
        return converted_data

    def process_reactions(self, reactions_in) -> dict:
        """Extract sub reaction value: 
        Args:
            reactions_in (_type_): _description_
        Returns:
            _dict_: {
                "like": value, 
                "haha": value, 
                "angry": value, 
                "love": value, 
                "care": value, 
                "sorry": value, 
                "wow": value
        }
        Note: 
        """
        reaction_hash = {}
        for each_react in reactions_in:
            reaction_hash[each_react['node']['localized_name']
                          ] = each_react['reaction_count']  # get reaction value
        return reaction_hash

    def extract_first_payload(self, payload:str):
        parsed_data = parse_qs(payload)
        decoded_data = {unquote(k): [unquote(v) for v in vals] for k, vals in parsed_data.items()} # 解碼 keys 和 values
        first_payload = {k: v[0] for k, v in decoded_data.items()} # 如果只需要第一個值作為字典中的單一值
        payload_variables = json.loads(first_payload['variables'])
        first_payload['variables'] = payload_variables
        return first_payload
