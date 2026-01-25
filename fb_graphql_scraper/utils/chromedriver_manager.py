# -*- coding: utf-8 -*-
"""
ChromeDriver Manager - 自動下載並管理ChromeDriver
===================================================
根據系統架構和Chrome版本自動下載正確的ChromeDriver版本
"""

import os
import sys
import platform
import subprocess
import re
import urllib.request
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Tuple


class ChromeDriverManager:
    """自動管理ChromeDriver下載和安裝"""
    
    # ChromeDriver下載源
    CHROMEDRIVER_REPO = "https://googlechromelabs.github.io/chrome-for-testing/"
    CHROMEDRIVER_API = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    
    # 備用下載源
    CHROMEDRIVER_MIRROR = "https://chromedriver.chromium.org/downloads"
    
    def __init__(self, save_path: Optional[str] = None):
        """
        初始化ChromeDriver管理器
        
        Args:
            save_path: ChromeDriver保存路徑，默認為當前目錄下的drivers文件夾
        """
        self.system = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'
        self.architecture = platform.machine()  # 'x86_64', 'arm64', etc.
        self.save_path = Path(save_path) if save_path else Path.cwd() / "drivers"
        self.save_path.mkdir(parents=True, exist_ok=True)
        
    def get_chrome_version(self) -> Optional[str]:
        """
        檢測系統上安裝的Chrome版本
        
        Returns:
            Chrome版本字符串 (例如: '130.0.1234.56')，如果未找到則返回None
        """
        try:
            if self.system == "Darwin":  # macOS
                # 檢查多個常見的Chrome安裝位置
                paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
                ]
                for path in paths:
                    if os.path.exists(path):
                        version = subprocess.check_output([path, "--version"]).decode().strip()
                        return version.split()[-1]
                        
            elif self.system == "Windows":
                # Windows路徑
                paths = [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                    os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
                ]
                for path in paths:
                    if os.path.exists(path):
                        version = subprocess.check_output([path, "--version"]).decode().strip()
                        return version.split()[-1]
                        
            elif self.system == "Linux":
                # Linux命令
                try:
                    version = subprocess.check_output(["google-chrome", "--version"]).decode().strip()
                    return version.split()[-1]
                except:
                    try:
                        version = subprocess.check_output(["chromium-browser", "--version"]).decode().strip()
                        return version.split()[-1]
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ 無法檢測Chrome版本: {e}")
            return None
    
    def get_major_version(self, version: str) -> int:
        """
        從完整版本號中提取主版本號
        
        Args:
            version: 完整版本字符串 (例如: '130.0.1234.56')
            
        Returns:
            主版本號 (例如: 130)
        """
        match = re.match(r'(\d+)', version)
        return int(match.group(1)) if match else None
    
    def get_download_url(self, chrome_version: str) -> Optional[str]:
        """
        獲取對應Chrome版本的ChromeDriver下載鏈接
        
        Args:
            chrome_version: Chrome版本字符串
            
        Returns:
            下載URL，如果找不到則返回None
        """
        try:
            import json
            
            print(f"🔍 正在查詢Chrome {chrome_version} 的ChromeDriver...")
            
            # 使用Google Chrome for Testing API
            with urllib.request.urlopen(self.CHROMEDRIVER_API, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            versions = data.get("versions", [])
            
            # 查找匹配的版本
            for version_info in versions:
                version = version_info.get("version", "")
                if version.startswith(chrome_version.split('.')[0]):  # 匹配主版本號
                    downloads = version_info.get("downloads", {})
                    chromedriver_urls = downloads.get("chromedriver", [])
                    
                    # 找到匹配系統和架構的下載鏈接
                    for download in chromedriver_urls:
                        platform_str = download.get("platform", "").lower()
                        url = download.get("url", "")
                        
                        if self._match_platform(platform_str):
                            return url
            
            print(f"⚠️ 未找到Chrome {chrome_version}的官方版本")
            return None
            
        except Exception as e:
            print(f"❌ 查詢下載鏈接失敗: {e}")
            return None
    
    def _match_platform(self, platform_str: str) -> bool:
        """
        檢查平台字符串是否與當前系統匹配
        
        Args:
            platform_str: 平台字符串 (例如: 'mac-x64', 'win64', 'linux64')
            
        Returns:
            是否匹配
        """
        if self.system == "Darwin":  # macOS
            return "mac" in platform_str
        elif self.system == "Windows":
            return "win" in platform_str
        elif self.system == "Linux":
            return "linux" in platform_str
        return False
    
    def download_chromedriver(self, url: str) -> Optional[Path]:
        """
        下載ChromeDriver
        
        Args:
            url: 下載URL
            
        Returns:
            ChromeDriver文件路徑，下載失敗則返回None
        """
        try:
            print(f"⬇️ 正在下載ChromeDriver...")
            filename = self.save_path / "chromedriver.zip"
            
            # 顯示下載進度
            def download_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                percent = min(downloaded * 100 // total_size, 100)
                print(f"\r⏳ 下載進度: {percent}%", end="")
            
            urllib.request.urlretrieve(url, filename, download_progress)
            print("\n✅ 下載完成")
            
            return self._extract_and_install(filename)
            
        except Exception as e:
            print(f"❌ 下載失敗: {e}")
            return None
    
    def _extract_and_install(self, zip_path: Path) -> Optional[Path]:
        """
        解壓縮並安裝ChromeDriver
        
        Args:
            zip_path: 下載的zip文件路徑
            
        Returns:
            ChromeDriver可執行文件的路徑
        """
        try:
            print(f"📦 正在解壓ChromeDriver...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.save_path)
            
            # 查找chromedriver可執行文件
            driver_path = None
            for root, dirs, files in os.walk(self.save_path):
                for file in files:
                    if file.startswith("chromedriver") and not file.endswith(".zip"):
                        driver_path = Path(root) / file
                        break
                if driver_path:
                    break
            
            if driver_path:
                # 設置執行權限（Unix系統）
                if self.system in ["Darwin", "Linux"]:
                    os.chmod(driver_path, 0o755)
                
                print(f"✅ ChromeDriver已安裝: {driver_path}")
                
                # 清理zip文件
                zip_path.unlink()
                
                return driver_path
            else:
                print("❌ 無法在解壓的文件中找到chromedriver")
                return None
                
        except Exception as e:
            print(f"❌ 安裝失敗: {e}")
            return None
    
    def get_chromedriver_path(self) -> Optional[Path]:
        """
        獲取或下載ChromeDriver
        
        Returns:
            ChromeDriver可執行文件的路徑
        """
        # 檢查系統PATH中是否已有chromedriver
        existing_driver = self._find_in_path("chromedriver")
        if existing_driver:
            print(f"✅ 找到現有的ChromeDriver: {existing_driver}")
            return Path(existing_driver)
        
        # 檢查保存路徑中是否已有chromedriver
        for file in self.save_path.rglob("chromedriver*"):
            if not str(file).endswith(".zip"):
                print(f"✅ 找到現有的ChromeDriver: {file}")
                return file
        
        # 獲取Chrome版本
        chrome_version = self.get_chrome_version()
        if not chrome_version:
            print("❌ 無法檢測到Chrome瀏覽器，請確保已安裝Chrome")
            return None
        
        print(f"✅ 檢測到Chrome版本: {chrome_version}")
        
        # 獲取下載URL
        url = self.get_download_url(chrome_version)
        if not url:
            print("❌ 無法獲取對應版本的ChromeDriver下載鏈接")
            return None
        
        # 下載並安裝
        return self.download_chromedriver(url)
    
    @staticmethod
    def _find_in_path(executable_name: str) -> Optional[str]:
        """
        在系統PATH中查找可執行文件
        
        Args:
            executable_name: 可執行文件名
            
        Returns:
            完整路徑，如果未找到則返回None
        """
        try:
            result = subprocess.check_output(["which" if platform.system() != "Windows" else "where", executable_name])
            return result.decode().strip()
        except:
            return None


def setup_chromedriver(save_path: Optional[str] = None) -> Optional[Path]:
    """
    快速設置ChromeDriver的便利函數
    
    Args:
        save_path: ChromeDriver保存路徑
        
    Returns:
        ChromeDriver可執行文件的路徑
    """
    print("=" * 60)
    print("🚀 ChromeDriver 自動管理工具")
    print("=" * 60)
    
    manager = ChromeDriverManager(save_path)
    print(f"📍 系統: {manager.system}")
    print(f"🏗️  架構: {manager.architecture}")
    print(f"💾 保存路徑: {manager.save_path}")
    print("-" * 60)
    
    driver_path = manager.get_chromedriver_path()
    
    print("=" * 60)
    if driver_path:
        print(f"✅ ChromeDriver 準備就緒!")
        print(f"📍 路徑: {driver_path}")
    else:
        print("❌ ChromeDriver 設置失敗")
    print("=" * 60)
    
    return driver_path


if __name__ == "__main__":
    # 命令行使用示例
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromeDriver 自動下載管理工具")
    parser.add_argument("--path", "-p", help="指定ChromeDriver保存路徑", default=None)
    parser.add_argument("--check", "-c", action="store_true", help="僅檢查Chrome版本")
    
    args = parser.parse_args()
    
    if args.check:
        manager = ChromeDriverManager()
        version = manager.get_chrome_version()
        if version:
            print(f"Chrome 版本: {version}")
        else:
            print("未檢測到Chrome")
    else:
        setup_chromedriver(args.path)
