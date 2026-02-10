from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os

load_dotenv()

user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
debugger_address = os.getenv("CHROME_DEBUGGER_ADDRESS")
profile_dir = os.getenv("CHROME_PROFILE_DIR", "Default")
log_path = os.getenv("CHROMEDRIVER_LOG_PATH", "./tmp/chromedriver.log")

if not user_data_dir:
    raise ValueError("CHROME_USER_DATA_DIR is required in .env")
if not chromedriver_path:
    raise ValueError("CHROMEDRIVER_PATH is required in .env")

chrome_options = Options()
chrome_options.add_argument("--remote-debugging-pipe")
chrome_options.add_argument(
    f"--user-data-dir={user_data_dir}"
)
chrome_options.add_argument(f"--profile-directory={profile_dir}")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"]
)
chrome_options.add_experimental_option(
    "useAutomationExtension", False
)
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--no-first-run")
chrome_options.add_argument("--no-default-browser-check")

if debugger_address:
    chrome_options.add_experimental_option("debuggerAddress", debugger_address)

service = Service(
    chromedriver_path,
    service_args=["--verbose", f"--log-path={log_path}"],
)

driver = webdriver.Chrome(
    service=service,
    options=chrome_options
)

driver.get("https://www.facebook.com")

# Detach from the session without closing the browser.
# driver.quit()
