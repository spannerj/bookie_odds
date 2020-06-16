from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.firefox import GeckoDriverManager
# from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yagmail
import os
import psycopg2
import telegram
import logging


def send_email(message, subject):
    password = os.environ('PWORD')
    yag = yagmail.SMTP('spencer.jago@digital.landregistry.gov.uk', password)
    contents = [message]
    emails = []
    emails.append('spencer.jago@gmail.com')

    yag.send(emails, subject, contents)


def connect_to_db():
    try:
        pg_url = os.environ['PG_URL']
        connection = psycopg2.connect(pg_url)
    except Exception as e:
        logging.error(e)

    return connection


def commit_and_close(connection):
    connection.commit()
    connection.close()


def get_stadiums():

    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT stadium, date_updated
                 FROM greyhounds
                 order by stadium
                 """

    cursor.execute(select_sql)
    result = cursor.fetchall()
    commit_and_close(connection)
    return result


def insert_race(meeting):
    connection = connect_to_db()
    cursor = connection.cursor()

    insert_sql = """
                 INSERT INTO greyhounds (stadium)
                 VALUES(%s);
                 """
    try:
        cursor.execute(insert_sql, (meeting,))
    except Exception as e:
        logging.error(e)
    commit_and_close(connection)


def send_message(message, channel):
    logging.info('Sending Telegram message')
    token = os.environ['TELEGRAM_BOT']
    bot = telegram.Bot(token=token)
    message = message.replace('*', '')
    if channel == 'Alert':
        bot.send_message(chat_id='-1001229649531',
                         text=message, 
                         parse_mode=telegram.ParseMode.MARKDOWN)  # Greyhound Alerts
    else:
        bot.send_message(chat_id='-1001365813396',
                         text=message, 
                         parse_mode=telegram.ParseMode.MARKDOWN)  # Monitor Test


def alert_sent(stadiums, race):
    alerted = False
    for stadium in stadiums:
        if stadium[0] == race:
            alerted = True
            break
    return alerted


def get_prices():
    browser_options = Options()
    # browser_options.binary_location = '/usr/local/bin/geckodriver'
    browser_options.add_argument("--window-size=1920,1080")
    browser_options.add_argument("--disable-extensions")
    browser_options.add_argument('--ignore-certificate-errors')
    browser_options.add_argument("--start-maximized")

    try:
        # driver = webdriver.Firefox(firefox_options=browser_options)
        driver = webdriver.Chrome(chrome_options=browser_options, executable_path=ChromeDriverManager().install())
        # driver = webdriver.Firefox(executable_path='/home/spanner/.wdm/drivers/geckodriver/linux32/v0.26.0/geckodriver',
        #                            browser_options=browser_options)

        url = "https://www.bet365.com/#/AS/B4/"
        driver.get(url)
        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'rsl-RaceMeeting rsl-RaceMeeting_Uk'))
            WebDriverWait(driver, 10).until(element_present)
        except Exception:
            logging.error('Page load error')
            # print(str(e))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        races = {}

        meetings = soup.find_all("div", class_="rsl-RaceMeeting_Uk")
        for meet in meetings:
            race = meet.find("div", class_="rsl-MeetingHeader_RaceName").get_text()
            early = meet.find("div", class_="rsl-RaceMeeting_FixedWinPriceAvailable")
            if early is not None:
                early = early.get_text()

            races[race] = early

        stadiums = get_stadiums()

        for race, early in races.items():
            if early is not None:
                if not alert_sent(stadiums, race):
                    # send_email('priced up', race)
                    send_message('{} priced up!'.format(race), 'Alert')
                    insert_race(race)
                    logging.info('Priced up {}'.format(race))

    except Exception as e:
        send_message('Dog prices error - {}'.format(str(e)), 'Error')
        # send_email(str(e), 'Dog prices error')
        logging.error(str(e))

    finally:
        logging.info('Finished')


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    get_prices()
