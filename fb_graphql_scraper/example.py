# -*- coding: utf-8 -*-
from fb_graphql_scraper.facebook_graphql_scraper import FacebookGraphqlScraper as fb_graphql_scraper


## Example.1 - without logging in
if __name__ == "__main__":
    facebook_user_name = "love.yuweishao"
    facebook_user_id = "subing.fb.u"
    days_limit = 3 # Number of days within which to scrape posts
    # driver_path = "/Users/hongshangren/Downloads/chromedriver-mac-arm64_136/chromedriver"
    driver_path = "/Users/andy/DTL/FB-GQL/chromedriver"
    fb_spider = fb_graphql_scraper(driver_path=driver_path, open_browser=False)
    res = fb_spider.get_user_posts(fb_username_or_userid=facebook_user_id, days_limit=days_limit,display_progress=True)


## Example.2 - login in your facebook account to collect data
# if __name__ == "__main__":
    # facebook_user_name = "love.yuweishao"
    # facebook_user_id = "100044253168423"
    # fb_account = "facebook_account"
    # fb_pwd = "facebook_paswword"
    # days_limit = 30 # Number of days within which to scrape posts
    # driver_path = "/Users/hongshangren/Downloads/chromedriver-mac-arm64_136/chromedriver"
    # fb_spider = fb_graphql_scraper(fb_account=fb_account,fb_pwd=fb_pwd, driver_path=driver_path, open_browser=False)
    # res = fb_spider.get_user_posts(fb_username_or_userid=facebook_user_name, days_limit=days_limit,display_progress=True)
    # print(res)


## Example.3 - with session persistence (saves login for next time)
# if __name__ == "__main__":
    # facebook_user_name = "love.yuweishao"
    # fb_account = "facebook_account"
    # fb_pwd = "facebook_password"
    # days_limit = 30
    # driver_path = "/Users/andy/DTL/FB-GQL/chromedriver"
    #
    # # First run: will login and save session to ~/.fb_scraper/
    # fb_spider = fb_graphql_scraper(
    #     fb_account=fb_account,
    #     fb_pwd=fb_pwd,
    #     driver_path=driver_path,
    #     open_browser=False
    # )
    # res = fb_spider.get_user_posts(fb_username_or_userid=facebook_user_name, days_limit=days_limit, display_progress=True)
    # print(res)
    #
    # # Second run: will load saved session (no credentials needed!)
    # # fb_spider = fb_graphql_scraper(driver_path=driver_path, open_browser=False)
    # # res = fb_spider.get_user_posts(fb_username_or_userid=facebook_user_name, days_limit=days_limit, display_progress=True)
    # # print(res)


## Example.4 - disable session persistence (always fresh login)
# if __name__ == "__main__":
    # facebook_user_name = "love.yuweishao"
    # fb_account = "facebook_account"
    # fb_pwd = "facebook_password"
    # days_limit = 30
    # driver_path = "/Users/andy/DTL/FB-GQL/chromedriver"
    #
    # fb_spider = fb_graphql_scraper(
    #     fb_account=fb_account,
    #     fb_pwd=fb_pwd,
    #     driver_path=driver_path,
    #     open_browser=False,
    #     use_session_persistence=False  # Disable session saving
    # )
    # res = fb_spider.get_user_posts(fb_username_or_userid=facebook_user_name, days_limit=days_limit, display_progress=True)
    # print(res)

