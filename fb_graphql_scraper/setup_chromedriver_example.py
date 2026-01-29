# -*- coding: utf-8 -*-
"""
ChromeDriver
====================
展示如何在項目中使用ChromeDriver Manager
"""

from pathlib import Path
from utils.chromedriver_manager import setup_chromedriver, ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


# 方法1: 使用快速設置函數
def example_quick_setup():
    """快速設置並使用ChromeDriver"""
    print("\n=== 方法1: 快速設置 ===\n")
    
    driver_path = setup_chromedriver()
    
    if driver_path:
        # 使用ChromeDriver創建Selenium WebDriver
        service = Service(str(driver_path))
        driver = webdriver.Chrome(service=service)
        driver.get("https://www.google.com")
        print(f"✅ 成功打開Google: {driver.title}")
        driver.quit()
    else:
        print("❌ ChromeDriver設置失敗")


def example_advanced_setup():
    """進階設置 - 指定保存路徑並獲取詳細信息"""
    print("\n=== 方法2: 進階設置 ===\n")
    
    save_path = Path.cwd() / "drivers"
    manager = ChromeDriverManager(save_path=str(save_path))
    
    version = manager.get_chrome_version()
    print(f"Chrome版本: {version}")
    
    driver_path = manager.get_chromedriver_path()
    
    if driver_path:
        # 使用ChromeDriver
        service = Service(str(driver_path))
        driver = webdriver.Chrome(service=service)
        driver.get("https://www.google.com")
        print(f"✅ 成功打開: {driver.title}")
        driver.quit()


def setup_driver_for_scraper():
    """為爬蟲項目設置WebDriver"""
    print("\n=== 方法3: 集成到項目 ===\n")
    
    project_root = Path(__file__).parent
    driver_path = setup_chromedriver(str(project_root / "drivers"))
    
    if driver_path:
        print(f"✅ ChromeDriver已準備: {driver_path}")
        print(f"💡 在代碼中使用:")
        print(f"   service = Service('{driver_path}')")
        print(f"   driver = webdriver.Chrome(service=service)")
        return driver_path
    else:
        return None


if __name__ == "__main__":
    # example_quick_setup()
    # example_advanced_setup()
    setup_driver_for_scraper()
