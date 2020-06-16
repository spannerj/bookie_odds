from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import yagmail
import os
import psycopg2
import telegram
import logging
from datetime import datetime, date


def send_email(message, subject):
    password = 'kwgapxywzylakeki'
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


def update_date(meeting):
    connection = connect_to_db()
    cursor = connection.cursor()

    update_sql = """
                 UPDATE greyhounds
                 SET date_updated = current_date
                 where stadium = %s;
                 """
    try:
        cursor.execute(update_sql, (meeting,))
    except Exception as e:
        logging.error(e)
    commit_and_close(connection)


def send_message(message, channel):
    token = os.environ['TELEGRAM_BOT']
    bot = telegram.Bot(token=token)
    message = message.replace('*', '')
    if channel == 'Alert':
        bot.send_message(chat_id='-1001229649531', text=message, parse_mode=telegram.ParseMode.MARKDOWN) #  Greyhound Alerts
    else:
        bot.send_message(chat_id='-1001365813396', text=message, parse_mode=telegram.ParseMode.MARKDOWN) #  Monitor Test
    # bot.send_message(chat_id='-1001365813396', text=message, parse_mode=telegram.ParseMode.MARKDOWN) #  Monitor Test


def get_prices():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--proxy-server='direct://'")
    # chrome_options.add_argument("--proxy-bypass-list=*")
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')

    # loop_ct = 1

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install(),
                                  options=chrome_options)

    # while True:
        meetings = []
        stadiums = get_stadiums()
        for stadium in stadiums:
            if (stadium[1] is None) or (stadium[1].date() < datetime.today().date()):
                meetings.append(stadium[0])

        for meeting in meetings:
            driver.get('https://www.oddschecker.com/greyhounds/{}'.format(meeting))

            if meeting in driver.current_url:
                logging.info('on the right page - {}'.format(driver.current_url))

                try:
                    driver.find_element_by_xpath('//*[@id="promo-modal"]/div[1]/div/span').click()
                except Exception:
                    pass

                time.sleep(1)
                elements = driver.find_elements_by_css_selector("div.fixture a")
                driver.get(elements[0].get_attribute("href"))
                elements = driver.find_elements_by_css_selector("td[data-bk='B3']")

                prices_found = True
                for element in elements[3:]:
                    if element.text != '':
                        if element.text == 'SP':
                            # starting price found so break
                            prices_found = False
                            break

                if prices_found:
                    send_email('priced up', meeting)
                    send_message('{} priced up!'.format(meeting), 'Alert')
                    update_date(meeting)
                    logging.info('Priced up {}'.format(meeting))

        # loop_ct = loop_ct + 1
        # if loop_ct == 30:
        #     send_email('ZZZZZZZZZ', 'Sleeping')
        #     loop_ct = 1
        # logging.info('sleeping - {}'.format(str(loop_ct)))
        # time.sleep(60)

    except Exception as e:
        driver.save_screenshot('error.png')
        send_message('Dog prices error - '.format(str(e)), 'Error')
        send_email(str(e), 'Dog prices error')
        print(e)

    finally:
        print('Finished')
        driver.quit()


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    get_prices()
