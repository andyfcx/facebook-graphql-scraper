from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()

chrome_options = Options()
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument(
    "--user-data-dir=/Users/y/Library/Application Support/Google/Chrome"
)
chrome_options.add_argument("--profile-directory=Default")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"]
)
chrome_options.add_experimental_option(
    "useAutomationExtension", False
)

service = Service("/Users/y/facebook-graphql-scraper/drivers/chromedriver-mac-x64/chromedriver")

driver = webdriver.Chrome(
    service=service,
    options=chrome_options
)

driver.get("https://www.facebook.com")
