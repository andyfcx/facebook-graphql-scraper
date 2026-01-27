# -*- coding: utf-8 -*-
"""
Facebook GraphQL Scraper - Login Test Script
==============================================
此腳本用於測試Facebook登錄功能，支持以下功能：
1. 從 .env 文件讀取帳號、密碼和chromedriver路徑
2. 自動打開瀏覽器
3. 模擬人類輸入行為（添加延遲和隨機延遲）
4. 驗證登錄是否成功
"""

import time
import sys
import getpass
from pathlib import Path
from dotenv import load_dotenv
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from fb_graphql_scraper.base.base_page import BasePage
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver


class FacebookLoginTester(BasePage):
    CDP_PORT = 9222
    
    def __init__(self, driver_path: str, open_browser: bool = True):
        """
        初始化登錄測試器
        
        Args:
            driver_path: Chrome驅動程序的路徑
            open_browser: 是否打開瀏覽器（True = 可視，False = 無頭模式）
        """
        # 不調用 super().__init__() 而是手動初始化驅動，以便添加 CDP 端口
        chrome_options = self._build_options(open_browser)
        # 添加 CDP 端口用於外部程式監控
        chrome_options.add_argument(f"--remote-debugging-port={self.CDP_PORT}")
        
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)
        
        print(f"\n✓ Chrome DevTools Protocol 端口已開啟: http://localhost:{self.CDP_PORT}")
        print("  外部程式可通過此端口監控瀏覽器狀態")
    
    @staticmethod
    def _build_options(open_browser: bool) -> webdriver.ChromeOptions:
        """構建Chrome選項"""
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        if not open_browser:
            options.add_argument("--headless=new")
        options.add_argument("--blink-settings=imagesEnabled=false")
        return options
    
    def simulate_human_typing(self, element, text, min_delay=0.05, max_delay=0.15):
        """
        模擬人類輸入行為，逐字輸入且每個字之間有隨機延遲
        
        Args:
            element: 要輸入的HTML元素
            text: 要輸入的文本
            min_delay: 最小延遲（秒）
            max_delay: 最大延遲（秒）
        """
        element.click()  # 先點擊元素確保焦點
        time.sleep(random.uniform(0.2, 0.5))  # 點擊後等待
        
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))
    
    def login(self, email: str, password: str):
        """
        執行Facebook登錄程序
        
        Args:
            email: Facebook帳號（郵箱或電話號碼）
            password: Facebook密碼
            
        Returns:
            bool: 登錄是否成功
        """
        try:
            print("\n" + "="*50)
            print("開始登錄Facebook...")
            print("="*50 + "\n")
            
            # 步驟1：打開Facebook登錄頁面
            print("[步驟 1/5] 打開Facebook登錄頁面...")
            self.driver.get("https://www.facebook.com/login/")
            time.sleep(2)  # 等待頁面加載
            
            # 步驟2：定位並填寫電子郵件/電話號碼
            print("[步驟 2/5] 輸入帳號...")
            try:
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                print("   ✓ 找到帳號輸入框")
                self.simulate_human_typing(email_input, email)
                print(f"   ✓ 已輸入帳號: {email[:3]}***")
            except Exception as e:
                print(f"   ✗ 無法找到帳號輸入框: {e}")
                return False
            
            time.sleep(random.uniform(0.5, 1.5))
            
            # 步驟3：定位並填寫密碼
            print("[步驟 3/5] 輸入密碼...")
            try:
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "pass"))
                )
                print("   ✓ 找到密碼輸入框")
                self.simulate_human_typing(password_input, password)
                print(f"   ✓ 已輸入密碼 (長度: {len(password)} 字符)")
            except Exception as e:
                print(f"   ✗ 無法找到密碼輸入框: {e}")
                return False
            
            time.sleep(random.uniform(1, 2))
            
            # 步驟4：點擊登錄按鈕
            print("[步驟 4/5] 提交登錄表單...")
            try:
                # 尋找登錄按鈕
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "login"))
                )
                print("   ✓ 找到登錄按鈕")
                
                # 使用ActionChains模擬人類點擊（可能有額外的延遲）
                time.sleep(random.uniform(0.3, 0.8))
                self.actions.move_to_element(login_button).click().perform()
                print("   ✓ 已點擊登錄按鈕")
            except Exception as e:
                print(f"   ✗ 無法點擊登錄按鈕: {e}")
                return False
            
            # 步驟5：等待登錄完成
            print("[步驟 5/5] 等待登錄完成...")
            time.sleep(3)  # 初始等待
            
            # 檢查是否登錄成功（通過檢查URL或特定元素）
            current_url = self.driver.current_url
            print(f"   當前URL: {current_url}")
            
            # 等待頁面完全加載
            try:
                # 如果看到首頁的標誌性元素，說明登錄成功
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Facebook']"))
                )
                print("   ✓ 登錄成功！已進入Facebook首頁")
                return True
            except Exception:
                # 檢查是否有錯誤訊息
                try:
                    error_message = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), '密碼') or contains(text(), '帳號')]"
                    )
                    print(f"   ✗ 登錄失敗: {error_message.text}")
                    return False
                except:
                    # 無法確定登錄狀態
                    print(f"   ⚠ 無法確定登錄狀態，請檢查瀏覽器")
                    print("   提示：如果需要驗證碼，請在瀏覽器中手動完成")
                    return False
        
        except Exception as e:
            print(f"\n✗ 登錄過程中出錯: {e}")
            return False
    
    def close(self):
        """
        關閉瀏覽器（可選操作）
        注意：瀏覽器將保持打開狀態，以便外部程式監控
        如需手動關閉瀏覽器，請直接關閉瀏覽器窗口
        """
        # 瀏覽器保持打開，不主動關閉
        print("\n提示: 瀏覽器保持打開狀態，可通過以下方式關閉:")
        print(f"  1. 直接關閉瀏覽器窗口")
        print(f"  2. 使用Chrome DevTools (http://localhost:{self.CDP_PORT})")


def get_credentials():
    """
    從 .env 文件獲取登錄憑據
    如果 .env 中的值為空，則提示用戶輸入
    
    Returns:
        tuple: (email, password)
    """
    # 加載 .env 文件
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    # 從環境變量讀取
    email = os.getenv("FB_EMAIL", "").strip()
    password = os.getenv("FB_PASSWORD", "").strip()
    
    print("\n" + "="*50)
    print("Facebook登錄測試 - 憑據配置")
    print("="*50)
    
    # 如果 .env 中沒有設置，則提示用戶輸入
    if not email:
        print("\n在 .env 文件中未找到 FB_EMAIL")
        print("請輸入您的Facebook帳號信息:\n")
        email = input("請輸入Facebook帳號 (郵箱或電話): ").strip()
        if not email:
            print("✗ 帳號不能為空！")
            return None, None
    else:
        print(f"\n✓ 已從 .env 加載帳號: {email[:3]}***")
    
    if not password:
        print("\n在 .env 文件中未找到 FB_PASSWORD")
        print("(系統將安全地處理密碼 - 輸入時不會顯示密碼)\n")
        password = getpass.getpass("請輸入Facebook密碼: ")
        if not password:
            print("✗ 密碼不能為空！")
            return None, None
    else:
        print(f"✓ 已從 .env 加載密碼")
    
    return email, password


def main():
    """主函數"""
    print("\n" + "="*60)
    print("  Facebook GraphQL Scraper - 登錄測試工具")
    print("="*60)
    
    # 加載 .env 文件
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    # 從環境變量讀取 ChromeDriver 路徑
    driver_path = os.getenv("CHROMEDRIVER_PATH", "").strip()
    
    # 如果 .env 中沒有設置，則提示用戶輸入
    if not driver_path:
        print("\n在 .env 文件中未找到 CHROMEDRIVER_PATH")
        print("\n請輸入Chrome驅動程序的完整路徑:")
        print("提示：可以通過以下方式獲取:")
        print("  1. 訪問 https://chromedriver.chromium.org/")
        print("  2. 下載與你Chrome版本相對應的驅動程序")
        print("  3. 將驅動程序放在上述路徑中\n")
        driver_path = input("請輸入Chrome驅動程序的完整路徑: ").strip()
    else:
        print(f"\n✓ 已從 .env 加載 ChromeDriver 路徑")
    
    if not Path(driver_path).exists():
        print(f"\n✗ 找不到Chrome驅動程序: {driver_path}")
        print("提示：可以通過以下方式獲取:")
        print("  1. 訪問 https://chromedriver.chromium.org/")
        print("  2. 下載與你Chrome版本相對應的驅動程序")
        print("  3. 將驅動程序放在上述路徑中")
        return
    
    print(f"✓ 已找到Chrome驅動程序: {driver_path}\n")
    
    # 獲取登錄憑據
    email, password = get_credentials()
    if not email or not password:
        return
    
    tester = None
    try:
        print("\n正在啟動Chrome瀏覽器...")
        tester = FacebookLoginTester(driver_path=driver_path, open_browser=True)
        
        success = tester.login(email, password)
        
        if success:
            print("\n" + "="*50)
            print("✓ 登錄測試完成 - 成功!")
            print("="*50)
            print("\n瀏覽器將在您按下Enter鍵後關閉...")
            input()
        else:
            print("\n" + "="*50)
            print("⚠ 登錄測試完成 - 檢查結果")
            print("="*50)
            print("\n可能的原因:")
            print("  • 帳號或密碼錯誤")
            print("  • 需要進行額外的驗證（如驗證碼、雙因素驗證）")
            print("  • Facebook網站可能有更新")
            print("\n瀏覽器將在您按下Enter鍵後關閉...")
            print("或者您可以在瀏覽器中手動驗證並測試...")
            input()
    
    except KeyboardInterrupt:
        print("\n\n✓ 用戶已中斷程序")
        print("   瀏覽器將保持打開狀態")
    except Exception as e:
        print(f"\n✗ 程序出錯: {e}")
    finally:
        if tester:
            print("\n" + "="*60)
            print("登錄測試已完成")
            print("="*60)
            print(f"\n瀏覽器已保持打開狀態，您可以:")
            print(f"  • 繼續在瀏覽器中進行手動操作")
            print(f"  • 通過 Chrome DevTools 監控狀態: http://localhost:{tester.CDP_PORT}")
            print(f"  • 直接關閉瀏覽器窗口以退出")
            print(f"\n進程將保持運行，按 Ctrl+C 可強制退出...\n")


if __name__ == "__main__":
    main()
