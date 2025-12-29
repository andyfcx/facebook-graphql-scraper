# -*- coding: utf-8 -*-
import pandas as pd
from seleniumwire.utils import decode
import json
from urllib.parse import parse_qs, unquote
from fb_graphql_scraper.utils.utils import *


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
        self.res_new = []
        self.feedback_list = []
        self.context_list = []
        self.creation_list = []
        self.author_id_list = []
        self.author_id_list2 = []
        self.owning_profile = []

    def parse_body(self, body_content):
        for each_body in body_content:
            json_data = json.loads(each_body)
            self.res_new.append(json_data)
            try:
                each_res = json_data['data']['node'].copy()
                each_feedback = find_feedback_with_subscription_target_id(
                    each_res)
                if each_feedback:
                    self.feedback_list.append(each_feedback)
                    message_text = find_message_text(json_data)
                    creation_time = find_creation(json_data)
                    owing_profile = find_owning_profile(json_data)
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
        
            res_out.append({
                "post_id": each['subscription_target_id'],
                "post_url": [post_url],
                "creation_time": creation_time,
                "attachments": [],  # 暫時設為空陣列，需要額外邏輯來提取附件
                "text": text_content,
                "total_reaction_count": each['reaction_count']['count'] if each['reaction_count'] else 0,
                "reactions": standardized_reactions,
                "comment_count": each['comment_rendering_instance']['comments']['total_count'] if each['comment_rendering_instance'] and each['comment_rendering_instance']['comments'] else 0,
                "share_count": each['share_count']['count'] if each['share_count'] else 0
            })
        return res_out

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