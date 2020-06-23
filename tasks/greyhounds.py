from selenium import webdriver
# from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import yagmail
import os
import psycopg2
import telegram
import logging
import requests
import argparse
import time
import random
from datetime import datetime as dt
logging.getLogger(requests.packages.urllib3.__package__).setLevel(logging.ERROR)


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


def get_early_prices():
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT race_name, url, early_prices, odds_present
                 FROM b365_early_prices
                 order by race_name
                 """

    cursor.execute(select_sql)
    races = cursor.fetchall()
    commit_and_close(connection)
    return races


def insert_race(race):
    connection = connect_to_db()
    cursor = connection.cursor()

    if race['early']:
        early = dt.now()
    else:
        early = None

    insert_sql = """
                 INSERT INTO b365_early_prices
                 (race_name, url, early_prices)
                 VALUES(%s, %s, %s);
                 """
    try:
        cursor.execute(insert_sql, (race['name'],  race['url'], early, ))
    except Exception as e:
        logging.error(e)
    commit_and_close(connection)


def update_race(race):
    connection = connect_to_db()
    cursor = connection.cursor()

    update_time = dt.now()

    update_sql = """
                 UPDATE b365_early_prices
                 SET odds_present = %s
                 WHERE race_name = %s;
                 """
    try:
        cursor.execute(update_sql, (update_time,  race['name']))
    except Exception as e:
        logging.error(e)
    commit_and_close(connection)


def send_message(message, test_mode):
    logging.info('Sending Telegram message')
    token = os.environ['TELEGRAM_BOT']
    bot = telegram.Bot(token=token)
    message = message.replace('*', '')
    # if channel == 'TEST':
    if test_mode:
        bot.send_message(chat_id='-1001365813396',
                         text=message,
                         parse_mode=telegram.ParseMode.MARKDOWN)  # Monitor Test
    else:
        bot.send_message(chat_id='-1001229649531',
                         text=message,
                         parse_mode=telegram.ParseMode.MARKDOWN)  # Greyhound Alerts


def alert_sent(stadiums, race):
    alerted = False
    for stadium in stadiums:
        if stadium[0] == race:
            alerted = True
            break
    return alerted


def race_saved(early_prices, race_name):
    race_saved = None
    for price in early_prices:
        if price[0] == race_name:
            race = {}
            race['name'] = price[0]
            race['url'] = price[1]
            race['early'] = price[2]
            race['odds'] = price[3]
            race_saved = race
            break
    return race_saved


def get_prices(test_mode):

    logging.info('Started')

    browser_options = webdriver.ChromeOptions()
    browser_options.add_argument("start-maximized")
    browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    browser_options.add_experimental_option('useAutomationExtension', False)

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

            driver.get('https://www.bet365.com/#/AS/B4/')
            try:
                element_present = EC.presence_of_element_located((By.CLASS_NAME, 'rsl-RaceMeeting_Uk'))
                WebDriverWait(driver, 10).until(element_present)
            except Exception as e:
                logging.error(str(e))

            # soup = BeautifulSoup(driver.page_source, 'html.parser')

            early_prices = get_early_prices()

            races = []

            # meetings = driver.find_elements_by_class_name("rsl-RaceMeeting_Uk")
            meetings = (driver.find_elements_by_class_name("rsl-MarketGroup")[1]
                        .find_elements_by_class_name("rsl-RaceMeeting_Uk"))
            num = len(meetings)

            for i in range(num):
                race = {}
                try:
                    race_name = (driver.find_elements_by_class_name("rsl-MarketGroup")[1]
                                 .find_elements_by_class_name("rsl-RaceMeeting_Uk")[i]
                                 .find_element_by_class_name("rsl-MeetingHeader_RaceName").text)

                    saved_race = race_saved(early_prices, race_name)
                    if saved_race is None:
                        race['name'] = race_name

                        early = (len(driver.find_elements_by_class_name("rsl-MarketGroup")[1]
                                 .find_elements_by_class_name("rsl-RaceMeeting_Uk")[i]
                                 .find_elements_by_class_name("rsl-RaceMeeting_FixedWinPriceAvailable")) != 0)
                        race['early'] = early

                        elements = (driver.find_elements_by_class_name("rsl-MarketGroup")[1]
                                    .find_elements_by_class_name("rsl-RaceMeeting_Uk")[i]
                                    .find_elements_by_class_name("rsl-UkRacingCouponLink_RaceNameTime"))
                        for element in elements:
                            try:
                                element.click()
                                race['url'] = driver.current_url
                                break
                            except Exception:
                                pass

                        race['odds'] = None
                        insert_race(race)
                        races.append(race)
                        driver.execute_script("window.history.go(-1)")

                        time.sleep(random.uniform(0.5, 1.5))
                    else:
                        races.append(saved_race)
                except Exception as e:
                    print(str(e))
                    pass

            for race in races:
                if race['odds'] is None:
                    driver.get(race['url'])
                    driver.save_screenshot('odds.png')
                    time.sleep(2)
                    driver.save_screenshot('odds2.png')
                    odds = driver.find_element_by_class_name("rl-RacingCouponParticipantOddsOnly_Odds").text

                    if odds != 'SP':
                        update_race(race)
                        send_message('{} priced up!'.format(race['name']), test_mode)




            # meetings = soup.find_all("div", class_="rsl-RaceMeeting_Uk")
            # for meet in meetings:
            #     race = meet.find("div", class_="rsl-MeetingHeader_RaceName").get_text()
            #     early = meet.find("div", class_="rsl-RaceMeeting_FixedWinPriceAvailable")
            #     first_race_time = meet.find("div", class_="rsl-UkRacingCouponLink_RaceNameTime").get_text()
            #     driver.find_element_by_class_name("rsl-UkRacingCouponLink_RaceNameTime").click()
            #     url = driver.current_url
            #     print(url)
            #     driver.save_screenshot('screenie.png')
            #     print(first_race_time)
            #     print('*')

            #     if early is not None:
            #         early = early.get_text()

            #     races[race] = early
            #     driver.execute_script("window.history.go(-1)")

            # driver.quit()

            # stadiums = get_stadiums()

            # print(races)
            # print(stadiums)

            # for race, early in races.items():
            #     if early is not None:
            #         if not alert_sent(stadiums, race):
            #             # send_email('priced up', race)
            #             send_message('{} priced up!'.format(race), test_mode)
            #             insert_race(race)
            #             logging.info('Priced up {}'.format(race))

    except Exception as e:
        # send_message('Dog prices error - {}'.format(str(e)), True)
        # send_email(str(e), 'Dog prices error')
        logging.error(str(e))

    finally:
        logging.info('Finished')
        if test_mode:
            from pprint import pprint
            pprint(races)
        driver.quit()


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
    logging.basicConfig(level=LOGLEVEL)

    logging.debug('Started')
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    if args.test:
        print("running in test mode")
        get_prices(True)
    else:
        get_prices(False)
