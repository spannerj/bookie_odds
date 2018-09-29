from apscheduler.schedulers.blocking import BlockingScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import datetime

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def timed_job():
    options = Options()  
    options.add_argument("--headless")
    # options.add_argument("--start-maximized")
    options.add_argument("--window-size=1300,1000")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)

    driver.get("http://www.python.org")
    print(datetime.datetime.now())
    print(driver.title)
    driver.close()

@sched.scheduled_job('cron', day_of_week='fri-sat', hour=1, minute=30)
def scheduled_job():
    print(datetime.datetime.now())
    print('Scheduled job running.')

sched.start()