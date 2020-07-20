import os
import time
from selenium import webdriver
from .settings import USERNAME, PASSWORD

def upload_post(image, description):
    user_agent = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16"
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", user_agent)
    driver = webdriver.Firefox(profile)
    driver.set_window_size(360,640)

    url = 'https://www.instagram.com/accounts/login/?source=auth_switcher'
    driver.get(url)
    time.sleep(10)

    field = driver.find_element_by_css_selector("input[type='text']")
    field.send_keys(USERNAME)
    field = driver.find_element_by_css_selector("input[type='password']")
    field.send_keys(PASSWORD)
    time.sleep(2)
    button=driver.find_elements_by_xpath("//*[contains(text(), 'Log In')]")
    button[0].click()

    time.sleep(5)
    button=driver.find_elements_by_xpath("//*[contains(text(), 'Not Now')]")
    if len(button) > 0:
        button[0].click()

    time.sleep(5)
    button=driver.find_elements_by_xpath("//*[contains(text(), 'Cancel')]")
    if len(button) > 0:
        button[0].click()

    time.sleep(2)
    button = driver.find_elements_by_css_selector('[aria-label="New Post"]')
    print('before click')
    button[0].click()
    print('after click')
    #button1 = driver.find_elements_by_css_selector('[role="menuitem"]')
    #button1[-1].click()

    # for window os
    # os.system('autokey-run -s select_image')

    # for linux XD
    current_path = os.getcwd()
    # os.system('xdg-open {}/{}'.format(current_path, image))
    field = driver.find_element_by_css_selector("input[type='file']")
    field.send_keys("{}/{}".format(current_path, image))

    time.sleep(10)
    button=driver.find_elements_by_xpath("//*[contains(text(), 'Expand')]")
    if len(button) > 0:
        button[0].click()

    time.sleep(20)
    button=driver.find_elements_by_xpath("//*[contains(text(), 'Next')]")
    button[0].click()

    time.sleep(10)
    field = driver.find_elements_by_tag_name('textarea')[0]
    field.click()


    field.send_keys(description)

    time.sleep(15)
    button=driver.find_elements_by_xpath("//*[contains(text(), 'Share')]")
    button[-1].click()


    print('Success!')
    time.sleep(15)
    driver.quit()
