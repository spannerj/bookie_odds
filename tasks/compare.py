from selenium import webdriver
from selenium.webdriver.support import ui
from tasks.utils import send_message
from bs4 import BeautifulSoup
import yagmail
import os


def get_bets():
    browser_options = webdriver.ChromeOptions()
    browser_options.add_argument("start-maximized")
    browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    browser_options.add_experimental_option('useAutomationExtension', False)
    browser_options.add_argument("headless")

    with webdriver.Chrome(options=browser_options) as driver:
        ui.WebDriverWait(driver, 10)
        driver.get("http://uksyndicate.com/challenge/frame.php")

        iframe = driver.find_element_by_id("InlineFrame2")

        driver.switch_to.default_content()
        driver.switch_to.frame(iframe)
        iframe_source = driver.page_source

        with open("tasks/output1.html", "r") as saved:
            saved_text = saved.read()

        if iframe_source == saved_text:
            print('bets same')
        else:
            print('bets different')
            try:
                soup = BeautifulSoup(iframe_source, 'html.parser')
                text = soup.find("div", {"id": "wb_Text5"}).text
                send_message(text, False, 'Magic')

                with open("tasks/output1.html", "w") as file:
                    file.write(iframe_source)
            except Exception as e:
                print(str(e))
