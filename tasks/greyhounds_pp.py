from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import psycopg2
import logging
import requests
import argparse
import time
import random
from datetime import datetime as dt
from tasks.utils import send_message
# from utils import send_message
logging.getLogger(requests.packages.urllib3.__package__).setLevel(logging.ERROR)


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
                 FROM pp_early_prices
                 order by race_name
                 """

    try:
        cursor.execute(select_sql)
        races = cursor.fetchall()
        # commit_and_close(connection)
    except Exception as e:
        logging.error(e)
        connection.rollback()
    finally:
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
                 INSERT INTO pp_early_prices
                 (race_name, url, early_prices)
                 VALUES(%s, %s, %s);
                 """
    try:
        cursor.execute(insert_sql, (race['name'],  race['url'], early, ))
    except Exception as e:
        logging.error(e)
        connection.rollback()
    finally:
        commit_and_close(connection)


def update_race(race):
    connection = connect_to_db()
    cursor = connection.cursor()

    update_time = dt.now()

    update_sql = """
                 UPDATE pp_early_prices
                 SET odds_present = %s
                 WHERE race_name = %s;
                 """
    try:
        cursor.execute(update_sql, (update_time,  race['name']))
    except Exception as e:
        logging.error(e)
        connection.rollback()
    finally:
        commit_and_close(connection)


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


def all_priced_up(early_prices):
    for price in early_prices:
        if price[3] is None:
            return False
    return True


def get_prices_pp(test_mode):

    logging.info('Started')

    try:
        early_prices = get_early_prices()
        if (len(early_prices) == 0) or (not all_priced_up(early_prices)):

            browser_options = webdriver.ChromeOptions()
            browser_options.add_argument("start-maximized")
            browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            browser_options.add_experimental_option('useAutomationExtension', False)
            browser_options.add_argument("headless")

            with webdriver.Chrome(options=browser_options) as driver:

                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                        })
                    """
                })

                driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})

                driver.get('https://www.paddypower.com/greyhound-racing?tab=meetings')
                try:
                    element_present = EC.presence_of_element_located((By.CLASS_NAME, 'region-group__card-item'))
                    WebDriverWait(driver, 10).until(element_present)
                except Exception as e:
                    logging.error(str(e))

                races = []

                # meetings = (driver.find_elements_by_class_name("region-group__card-item"))

                meetings = (driver.find_elements_by_class_name("region-group")[0]
                            .find_elements_by_class_name("region-group__card-item"))

                num = len(meetings)
                logging.info('meetings = {}'.format(str(num)))
                # /html/body/page-container/div/main/div/content-managed-page/div/div[2]/div/div[2]/card-meetings-races/div/region-group[1]/div/abc-card/div/div/abc-card-content/meeting-card-item[2]/div/abc-accordion/div/div/div[2]/header-left/p[1]/span[1]
                # body > page-container > div > main > div > content-managed-page > div > div:nth-child(3) > div > div:nth-child(2) > card-meetings-races > div > region-group:nth-child(1) > div > abc-card > div > div > abc-card-content > meeting-card-item:nth-child(3) > div > abc-accordion > div > div > div.accordion__left > header-left > p.meeting-card-item__title_wrapper > span.meeting-card-item__title.accordion__title
                # # document.querySelector("body > page-container > div > main > div > content-managed-page > div > div:nth-child(3) > div > div:nth-child(2) > card-meetings-races > div > region-group:nth-child(1) > div > abc-card > div > div > abc-card-content > meeting-card-item:nth-child(3) > div > abc-accordion > div > div > div.accordion__left > header-left > p.meeting-card-item__title_wrapper > span.meeting-card-item__title.accordion__title")
                for i in range(num):
                    race = {}
                    try:
                        race_name = (driver.find_elements_by_class_name("region-group")[0]
                                     .find_elements_by_class_name("region-group__card-item")[i]
                                     .find_element_by_class_name("accordion__header")
                                     .find_element_by_class_name("meeting-card-item__title accordion__title").text)
                                    
                                    #  .find_element_by_class_name("meeting-card-item__title accordion__title").text)
                        # race_name = (driver.find_element_by_class_name("rsm-MarketGroupWithTabs_Wrapper")
                        #              .find_elements_by_class_name("rsm-RacingSplashScroller")[i]
                        #              .find_element_by_class_name("rsm-MeetingHeader_MeetingName").text)
                        logging.info(race_name)
                        exit()

                        saved_race = race_saved(early_prices, race_name)
                        if saved_race is None:
                            race['name'] = race_name

                            early = (len(driver.find_element_by_class_name("rsm-MarketGroupWithTabs_Wrapper")
                                     .find_elements_by_class_name("rsm-RacingSplashScroller")[i]
                                     .find_elements_by_class_name("rsm-RacingSplashScroller_EarlyPriceText ")) != 0)  # To Do - get early price element
                            # early = (len(driver.find_elements_by_class_name("rsl-MarketGroup")[1]
                            #         .find_elements_by_class_name("rsl-RaceMeeting_Uk")[i]
                            #         .find_elements_by_class_name("rsl-RaceMeeting_FixedWinPriceAvailable")) != 0)
                            race['early'] = early

                            elements = (driver.find_element_by_class_name("rsm-MarketGroupWithTabs_Wrapper")
                                        .find_elements_by_class_name("rsm-RacingSplashScroller")[i]
                                        .find_elements_by_class_name("rsm-UKRacingSplashParticipant_RaceName"))

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
                        print(race)
                        print(str(e))
                        pass

                for race in races:
                    if race['odds'] is None:
                        try:
                            driver.get(race['url'])
                            time.sleep(2)
                            driver.save_screenshot('odds.png')
                            odds = driver.find_element_by_class_name("srg-ParticipantGreyhoundsOdds_Odds").text

                            if odds != 'SP':
                                update_race(race)
                                send_message('{} priced up!'.format(race['name']), test_mode, race['name'])

                        except Exception as e:
                            result = driver.find_element_by_class_name("rlm-RacingStreamingWatchButtonRaceInfo_Result") # To do get result element
                            if result is not None:
                                update_race(race)
                                send_message('{} priced up and meeting already started!'.format(race['name']),
                                             test_mode, race['name'])
                            else:
                                send_message('Dog prices error - {}'.format(str(e)), True)

    except Exception as e:
        driver.save_screenshot("screenshot.png")
        logging.error(str(e))
        logging.error(race)
        try:
            send_message('Dog prices error - {}'.format(str(e)), True)
        except Exception as err:
            logging.error(str(err))
        # send_email(str(e), 'Dog prices error')

    finally:
        logging.info('Finished')
        if test_mode:
            from pprint import pprint
            pprint(races)
        # driver.quit()


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
        # send_message('testing', True)
        get_prices_pp(True)
    else:
        get_prices_pp(False)
