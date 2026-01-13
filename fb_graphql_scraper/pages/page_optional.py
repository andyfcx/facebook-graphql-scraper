# -*- coding: utf-8 -*-
from typing import List
from fb_graphql_scraper.utils.locator import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging

# Setup logging
logger = logging.getLogger(__name__)


class PageOptional(object):
    def __init__(self, driver=None, fb_account: str = None, fb_pwd: str = None,
                 session_manager=None, use_session_persistence: bool = True):
        self.locator = PageLocators
        self.xpath_elements = PageXpath
        self.class_elements = PageClass
        self.page_text = PageText
        self.driver = driver
        self.fb_account = fb_account
        self.fb_pwd = fb_pwd
        self.session_manager = session_manager
        self.use_session_persistence = use_session_persistence

        # Try to load existing session first
        if self.use_session_persistence and self.session_manager:
            # Try to load existing session
            if self._try_load_existing_session():
                print("Successfully loaded existing session")
                return

            # Try auto-login from saved credentials
            if self._try_auto_login_from_saved_credentials():
                print("Auto-logged in using saved credentials")
                return

        # Loggin account
        if self.fb_account and self.fb_pwd:
            login_page_url = "https://www.facebook.com/login"
            self.driver.get(url=login_page_url)
            self.login_page()

            # Save session after successful login
            if self.use_session_persistence and self.session_manager:
                self._save_session_after_login()

    def login_page(self):
        try:
            self.login_account(user=self.fb_account, 
                               password=self.fb_pwd,
            )
            time.sleep(5)
        except Exception as e:
            print(f"Login faield, message: {e}")

    def clean_requests(self):
        print(f"Before cleaning driver requests, the number of requests are: {len(self.driver.requests)}")
        try:
            print("Try to clear driver requests..")
            del self.driver.requests
            print(f"Clear, the number of requests are: {len(self.driver.requests)}")
        except Exception as e:
            print(f"Clear unsuccessfully, message: {e}")

    def get_in_url(self):
        self.driver.get(url=self.url)

    def login_account(self, user: str, password: str):
        user_element = self.driver.find_element(By.NAME, "email")
        user_element.send_keys(user)
        password_element = self.driver.find_element(By.NAME, "pass")
        password_element.send_keys(password)
        password_element.send_keys(Keys.ENTER)

        # Wait for page to process login
        time.sleep(3)

        # Check for captcha challenge
        if self._check_for_captcha():
            logger.warning("Login challenged by captcha. Attempting to solve captcha.")
            self._solve_captcha()

        # Verify login success
        time.sleep(2)
        if not self._is_logged_in():
            error_msg = "Login failed. Unable to verify successful login."
            logger.error(error_msg)
            raise Exception(error_msg)

    def scroll_window(self):
        self.driver.execute_script(
            "window.scrollTo(0,document.body.scrollHeight)")

    def scroll_window_with_parameter(self, parameter_in: str):
        self.driver.execute_script(f"window.scrollBy(0, {parameter_in});")

    def set_browser_zoom_percent(self, zoom_percent: int):
        zoom_percent = str(zoom_percent)
        self.driver.execute_script(
            f"document.body.style.zoom='{zoom_percent}%'")

    def move_to_element(self, element_in):
        ActionChains(self.driver).move_to_element(element_in).perform()

    def load_next_page(self, url:str, clear_limit:int=20):
        """>> Move on to target facebook user page,
        before moving, clean driver's requests first,
        or driver would store previous account's data.
        Args: url (str): user(kol) links"""
        i = 0
        while i <= clear_limit:
            self.clean_requests()
            if len(self.driver.requests) == 0:
                print("Cleared all driver requests!")
                break
            i += 1
        self.driver.get(url=url)

    def click_display_button(self):
        elements = self.driver.find_elements(self.locator.DISPLAY_MORE)
        for _ in range(10):
            for each_element in elements:
                if each_element.text == self.page_text.DISPLAY_MORE or each_element.text == self.page_text.DISPLAY_MORE2:
                    self.move_to_element(element_in=each_element)
                    self.scroll_window_with_parameter(parameter_in="500")
                    try:
                        each_element.click()
                        elements = self.driver.find_elements(
                            self.locator.DISPLAY_MORE)
                    except Exception as e:
                        print(
                            f"Click display more unsucessfully, error message:\n{e}")

    def click_display_button2(self):
        display_more_xpath = f"//div[@class='{PageClass.DISPLAY_MORE}' and @role='{PageRoleValue.DISPLAY_MORE}' and text()='{PageText.DISPLAY_MORE}']"
        elements = self.driver.find_elements(By.XPATH, display_more_xpath)
        for _ in range(10):
            for each_element in elements:
                if each_element.text == self.page_text.DISPLAY_MORE or each_element.text == self.page_text.DISPLAY_MORE2:
                    self.move_to_element(element_in=each_element)
                    self.scroll_window_with_parameter(parameter_in="500")
                    try:
                        each_element.click()
                        elements = self.driver.find_elements(
                            self.locator.DISPLAY_MORE)
                    except Exception as e:
                        print(
                            f"Click display more unsucessfully, error message:\n{e}")

    def click_reject_login_button(self):
        """Attempts to reject Facebook login popup with multiple fallback strategies"""

        # Strategy 1: Try primary locator
        try:
            reject_login_button = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.locator.CLOSELOGIN))
            reject_login_button.click()
            print("Successfully closed login popup using primary locator")
            return
        except Exception as e:
            print(f"Primary locator failed: {e}")

        # Strategy 2: Try alternative XPath from PageXpath
        try:
            reject_login_button = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, self.xpath_elements.CLOSE_LOGIN_BUTTON)))
            reject_login_button.click()
            print("Successfully closed login popup using alternative XPath")
            return
        except Exception as e:
            print(f"Alternative XPath failed: {e}")

        # Strategy 3: Try finding close button by aria-label
        try:
            close_buttons = self.driver.find_elements(By.XPATH, "//div[@aria-label='Close' or @aria-label='关闭' or @aria-label='關閉']")
            if close_buttons:
                close_buttons[0].click()
                print("Successfully closed login popup using aria-label")
                return
        except Exception as e:
            print(f"Aria-label strategy failed: {e}")

        # Strategy 4: Try finding "Not Now" or similar buttons
        try:
            not_now_buttons = self.driver.find_elements(By.XPATH,
                "//*[contains(text(), 'Not Now') or contains(text(), '暫時不要') or contains(text(), '以后再说')]")
            if not_now_buttons:
                not_now_buttons[0].click()
                print("Successfully dismissed login popup using 'Not Now' button")
                return
        except Exception as e:
            print(f"'Not Now' button strategy failed: {e}")

        # Strategy 5: Press ESC key to dismiss modal
        try:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            print("Successfully dismissed login popup using ESC key")
            return
        except Exception as e:
            print(f"ESC key strategy failed: {e}")

        # Strategy 6: Try clicking on modal overlay/backdrop
        try:
            overlay = self.driver.find_element(By.XPATH, "//div[@role='dialog']/..")
            ActionChains(self.driver).move_to_element_with_offset(overlay, 10, 10).click().perform()
            print("Successfully dismissed login popup by clicking overlay")
            return
        except Exception as e:
            print(f"Overlay click strategy failed: {e}")

        print("All strategies to reject login failed. Continuing without dismissing popup.")

    def quit_driver(self):
        self.driver.quit()

    def close_driver(self):
        self.driver.close()

    # Session Management Methods

    def _try_load_existing_session(self) -> bool:
        """
        Try to load existing session from disk.

        Returns:
            True if session loaded and validated successfully, False otherwise
        """
        try:
            if not self.session_manager.has_valid_session():
                print("No valid session file found")
                return False

            session_data = self.session_manager.load_session()
            if not session_data or not session_data.get('cookies'):
                print("No cookies in session data")
                return False

            print(f"Loading session with {len(session_data['cookies'])} cookies")

            # Inject cookies into driver
            if not self._inject_cookies_into_driver(session_data['cookies']):
                print("Failed to inject cookies")
                return False

            # Validate session
            if not self._is_logged_in():
                print("Session validation failed - cookies expired or invalid")
                self.session_manager.clear_session()
                return False

            print("Session loaded and validated successfully")
            return True

        except Exception as e:
            print(f"Error loading existing session: {e}")
            return False

    def _try_auto_login_from_saved_credentials(self) -> bool:
        """
        Try to auto-login using saved credentials.

        Returns:
            True if auto-login successful, False otherwise
        """
        try:
            session_data = self.session_manager.load_session()
            if not session_data or not session_data.get('credentials'):
                print("No saved credentials found")
                return False

            credentials = session_data['credentials']
            fb_account = credentials.get('fb_account')
            fb_pwd = credentials.get('fb_pwd')

            if not fb_account or not fb_pwd:
                print("Incomplete credentials in session data")
                return False

            print("Attempting auto-login with saved credentials")

            # Perform login
            login_page_url = "https://www.facebook.com/login"
            self.driver.get(url=login_page_url)
            time.sleep(2)

            self.login_account(user=fb_account, password=fb_pwd)
            time.sleep(5)

            # Validate login succeeded
            if not self._is_logged_in():
                print("Auto-login failed - credentials may be invalid")
                return False

            print("Auto-login successful")

            # Save new session
            self._save_session_after_login()

            return True

        except Exception as e:
            print(f"Error during auto-login: {e}")
            return False

    def _save_session_after_login(self):
        """Save session cookies and credentials after successful login."""
        try:
            cookies = self.driver.get_cookies()
            print(f"Saving session with {len(cookies)} cookies")

            credentials = None
            if self.fb_account and self.fb_pwd:
                credentials = {
                    'fb_account': self.fb_account,
                    'fb_pwd': self.fb_pwd
                }

            metadata = {
                'user_agent': self.driver.execute_script("return navigator.userAgent;"),
                'login_url': 'https://www.facebook.com/login'
            }

            self.session_manager.save_session(
                cookies=cookies,
                credentials=credentials,
                metadata=metadata
            )

        except Exception as e:
            print(f"Error saving session: {e}")

    def _is_logged_in(self) -> bool:
        """
        Check if currently logged into Facebook.

        Returns:
            True if logged in, False otherwise
        """
        try:
            current_url = self.driver.current_url

            # Check if on login page
            if 'login' in current_url.lower():
                return False

            # Check for login form (indicates NOT logged in)
            try:
                from selenium.webdriver.common.by import By
                login_forms = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="royal_login_form"]')
                if login_forms:
                    return False
            except:
                pass

            # Check for profile elements (indicates logged in)
            try:
                from selenium.webdriver.common.by import By
                # Look for navigation elements that only appear when logged in
                profile_elements = self.driver.find_elements(By.CSS_SELECTOR, '[aria-label*="Account"]')
                if not profile_elements:
                    profile_elements = self.driver.find_elements(By.CSS_SELECTOR, '[aria-label*="Your profile"]')
                if not profile_elements:
                    # Check for presence of feed or other logged-in indicators
                    profile_elements = self.driver.find_elements(By.CSS_SELECTOR, '[role="feed"]')
                if not profile_elements:
                    # Check for home link or other common elements
                    profile_elements = self.driver.find_elements(By.CSS_SELECTOR, '[href="/"]')

                if profile_elements:
                    return True
            except Exception as e:
                print(f"Error checking for profile elements: {e}")

            # If we can't definitively determine, check page source
            try:
                page_source = self.driver.page_source
                # If we see typical logged-in elements in the source
                if '"actorID"' in page_source or '"USER_ID"' in page_source:
                    return True
            except:
                pass

            return False

        except Exception as e:
            print(f"Error checking login status: {e}")
            return False

    def _inject_cookies_into_driver(self, cookies: List) -> bool:
        """
        Inject cookies into driver.

        Args:
            cookies: List of cookie dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            # Navigate to Facebook to set domain
            self.driver.get('https://www.facebook.com')
            time.sleep(2)

            # Clear existing cookies
            self.driver.delete_all_cookies()

            # Add each cookie
            current_time = time.time()
            for cookie in cookies:
                # Remove 'expiry' if it's in the past
                if 'expiry' in cookie:
                    if cookie['expiry'] < current_time:
                        print(f"Skipping expired cookie: {cookie['name']}")
                        continue

                try:
                    # Remove any keys that Selenium doesn't accept
                    clean_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.facebook.com'),
                        'path': cookie.get('path', '/'),
                    }

                    # Add optional fields if present
                    if 'expiry' in cookie:
                        clean_cookie['expiry'] = cookie['expiry']
                    if 'secure' in cookie:
                        clean_cookie['secure'] = cookie['secure']
                    if 'httpOnly' in cookie:
                        clean_cookie['httpOnly'] = cookie['httpOnly']

                    self.driver.add_cookie(clean_cookie)
                except Exception as e:
                    print(f"Failed to add cookie {cookie.get('name')}: {e}")

            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)

            return True

        except Exception as e:
            print(f"Error injecting cookies: {e}")
            return False

    def _check_for_captcha(self) -> bool:
        """
        Check if a captcha challenge is present on the page.

        Returns:
            True if captcha is detected, False otherwise
        """
        try:
            # Check for common captcha indicators
            captcha_indicators = [
                # Facebook captcha iframe
                (By.CSS_SELECTOR, 'iframe[title*="captcha"]'),
                (By.CSS_SELECTOR, 'iframe[src*="captcha"]'),
                # reCAPTCHA
                (By.CSS_SELECTOR, 'iframe[src*="recaptcha"]'),
                (By.CSS_SELECTOR, '.g-recaptcha'),
                # hCaptcha
                (By.CSS_SELECTOR, 'iframe[src*="hcaptcha"]'),
                (By.CSS_SELECTOR, '.h-captcha'),
                # Generic captcha elements
                (By.XPATH, "//*[contains(text(), 'Security Check')]"),
                (By.XPATH, "//*[contains(text(), 'captcha')]"),
                (By.XPATH, "//*[contains(text(), 'Captcha')]"),
                (By.XPATH, "//*[contains(text(), 'CAPTCHA')]"),
            ]

            for by, selector in captcha_indicators:
                try:
                    elements = self.driver.find_elements(by, selector)
                    if elements and elements[0].is_displayed():
                        logger.info(f"Captcha detected using selector: {selector}")
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.error(f"Error checking for captcha: {e}")
            return False

    def _solve_captcha(self):
        """
        Attempt to solve the captcha challenge.

        This method provides a framework for captcha solving. In production,
        you would integrate with a captcha solving service or implement
        manual intervention.
        """
        try:
            logger.warning("Captcha solving requires manual intervention or external service.")

            # Wait for potential manual solving
            # In production, you might integrate with services like:
            # - 2Captcha
            # - Anti-Captcha
            # - DeathByCaptcha
            # Or implement manual intervention with extended timeout

            max_wait_time = 120  # 2 minutes for manual solving
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                if not self._check_for_captcha():
                    logger.info("Captcha appears to be solved.")
                    return
                time.sleep(2)

            logger.warning("Captcha solving timeout reached. Continuing with login verification.")

        except Exception as e:
            logger.error(f"Error during captcha solving: {e}")
            raise
