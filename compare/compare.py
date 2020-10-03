from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_prices(test_mode):
    browser_options = webdriver.ChromeOptions()
    browser_options.add_argument("start-maximized")
    browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    browser_options.add_experimental_option('useAutomationExtension', False)
    browser_options.add_argument("headless")

    try:
        with webdriver.Chrome(options=browser_options) as driver:

            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
             "source": """
                Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
             """
            })

            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})

            driver.get('http://uksyndicate.com/challenge/frame.php')
            elem = wait.until(lambda driver: driver.find_element_by_id("iframevideo"))
            print(elem.get_attribute("src"))
            # try:
            #     element_present = EC.presence_of_element_located((By.ID, 'wb_Text5'))
            #     WebDriverWait(driver, 10).until(element_present)
            # except Exception as e:
            #     print(e)

            page_source = driver.page_source

            with open("output1.html", "w") as file:
                file.write(page_source)

            print(page_source)

    except Exception as error:
        logger.exception(error)

    finally:
        print('Finished')
        driver.quit()


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    get_prices(False)


# def hash_it(text):
#     return hashlib.sha224(text.encode('utf-8')).hexdigest()


# res = requests.get('http://uksyndicate.com/challenge/frame.php')
# html_page = res.content

# soup = BeautifulSoup(html_page, 'html.parser')

# print(soup.prettify("utf-8"))
# html = soup.prettify("utf-8")
# with open("output1.html", "wb") as file:
#     file.write(html)