import os
import time
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.keys import Keys

from .settings import USERNAME, PASSWORD

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HASH_TAGS = "\n \n #meme #memes #funny #dankmemes #memesdaily #funnymemes #lol #follow #dank #humor #like #love #dankmeme #tiktok #lmao #instagram #comedy #ol #anime #fun #dailymemes #memepage #edgymemes #offensivememes #memestagram #funnymeme"


def upload_post(posts):
    # image, description
    user_agent = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16"
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", user_agent)
    driver = webdriver.Firefox(profile)
    driver.set_window_size(360, 640)

    url = "https://www.instagram.com/accounts/login/?source=auth_switcher"
    driver.get(url)
    time.sleep(5)

    field = driver.find_element_by_css_selector("input[type='text']")
    field.send_keys(USERNAME)
    field = driver.find_element_by_css_selector("input[type='password']")
    field.send_keys(PASSWORD)
    time.sleep(2)
    button = driver.find_elements_by_xpath("//*[contains(text(), 'Log In')]")
    button[0].click()

    time.sleep(5)
    button = driver.find_elements_by_xpath("//*[contains(text(), 'Not Now')]")
    if len(button) > 0:
        button[0].click()

    time.sleep(5)
    button = driver.find_elements_by_xpath("//*[contains(text(), 'Cancel')]")
    if len(button) > 0:
        button[0].click()

    if isinstance(posts, list):
        for post in posts:
            if "file_name" in post and not "posted_on" in post:
                time.sleep(2)
                button = driver.find_elements_by_css_selector('[aria-label="New Post"]')
                button[0].click()
                # button1 = driver.find_elements_by_css_selector('[role="menuitem"]')
                # button1[-1].click()

                field = driver.find_element_by_css_selector("input[type='file']")
                field.send_keys("{}/assets/{}".format(ROOT_DIR["file_name"]))
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()

                time.sleep(7)
                button = driver.find_elements_by_xpath(
                    "//*[contains(text(), 'Expand')]"
                )
                if len(button) > 0:
                    button[0].click()

                time.sleep(10)
                button = driver.find_elements_by_xpath("//*[contains(text(), 'Next')]")
                button[0].click()

                time.sleep(6)
                field = driver.find_elements_by_tag_name("textarea")[0]
                field.click()

                field.send_keys(post["title"] + HASH_TAGS)

                time.sleep(8)
                button = driver.find_elements_by_xpath("//*[contains(text(), 'Share')]")
                button[-1].click()

                print("Upload Success! " + post["title"])
                time.sleep(2)
                meta = {}
                meta["posted_on"] = datetime.now().isoformat()
                post.update(meta)
    print("No more post to upload.")
    driver.quit()
    return posts
