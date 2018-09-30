from apscheduler.schedulers.blocking import BlockingScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

import datetime

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def timed_job():
    # options = Options()  
    # options.add_argument("--headless")
    # # options.add_argument("--start-maximized")
    # options.add_argument("--window-size=1300,1000")
    # options.add_argument('--disable-gpu')
    # options.add_argument('--remote-debugging-port=9222')
    # options.add_argument('--no-sandbox')
    # options.binary_location = os.environ['GOOGLE_CHROME_BIN']
    # driver = webdriver.Chrome(options=options)

    CHROMEDRIVER_PATH = "/app/.chromedriver/bin/chromedriver"

    chrome_options = webdriver.ChromeOptions()

    chrome_options.binary_location = '/app/.apt/usr/bin/google-chrome-stable'
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argume('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=chrome_options)
    print('browser is ready')    

    driver.get("http://www.python.org")
    print(datetime.datetime.now())
    print(driver.title)
    driver.close()

@sched.scheduled_job('cron', day_of_week='fri-sat', hour=1, minute=30)
def scheduled_job():
    print(datetime.datetime.now())
    print('Scheduled job running.')

sched.start()