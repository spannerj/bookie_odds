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
    # connect to selected data base
    try:
        pg_url = os.environ['PG_URL']
        connection = psycopg2.connect(pg_url)
    except Exception as e:
        logging.error(e)

    return connection


def commit_and_close(connection):
    # commit and close the transaction
    connection.commit()
    connection.close()


def clear_database():
    # clear old rows from the table ready to start again
    connection = connect_to_db()
    cursor = connection.cursor()

    delete_sql = """
                 DELETE FROM b365_early_prices
                 """

    result = cursor.execute(delete_sql)
    commit_and_close(connection)
    return result


def get_last_update():
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT max(time_added)
                 FROM b365_early_prices
                 """

    try:
        cursor.execute(select_sql)
        result = cursor.fetchall()

    except Exception as e:
        logging.error(str(e))
        connection.rollback()
    finally:
        commit_and_close(connection)
    
    return result[0][0]


def clear_database_check(last_update):
    # delete database if date added was before today
        if last_update is None:
            return
        else:
            print('last update')
            print(last_update)
            today = dt.now().date()
            print('today')
            print(today)
            if today > last_update.date():
                clear_database()
                send_message('B365 database cleared', True)  
                return


def get_meeting_status():
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT race_name, url, odds_present
                 FROM b365_early_prices
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

    insert_sql = """
                 INSERT INTO b365_early_prices
                 (race_name, url)
                 VALUES(%s, %s);
                 """
    try:
        cursor.execute(insert_sql, (race['name'],  race['url'], ))
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
                 UPDATE b365_early_prices
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


def populate_meeting(early_prices, meeting_name):
    # match the meeting to the saved data or retun None 
    meeting = None
    for price in early_prices:
        if price[0] == meeting_name:
            race = {}
            race['name'] = price[0]
            race['url'] = price[1]
            race['odds'] = price[2]
            meeting = race
            break
    return meeting


def all_priced_up(early_prices):
    # Return false if any meeting is still waiting for prices
    for price in early_prices:
        if price[2] is None:
            return False
    return True


def get_prices_b365(test_mode):
    # main function to check for meeting prices
    logging.info('B365 started at ' + dt.now().strftime('%H:%M:%S'))

    try:
        # check last update and clear db if required
        last_update = get_last_update()
        clear_database_check(last_update)

        # get meeting details from the database
        early_prices = get_meeting_status()

        # if database empty or meetings still to price up
        if (len(early_prices) == 0) or (not all_priced_up(early_prices)):

            # Set up the chrome driver
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

                # set a regular header so we don't look like a scraper with a selenium header
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})

                # navigate to bet365 and wait up to 10 secs for page to load
                driver.get('https://www.bet365.com/#/AS/B4/')
                try:
                    logging.info('page started loading at ' + dt.now().strftime('%H:%M:%S'))
                    element_present = EC.presence_of_element_located((By.CLASS_NAME, 'rsm-MarketGroupWithTabs_Wrapper'))
                    WebDriverWait(driver, 10).until(element_present)
                    logging.info('page loaded at ' + dt.now().strftime('%H:%M:%S'))
                except Exception as e:
                    logging.error(str(e))
                    driver.save_screenshot("error.png")


                races = []
                number_of_meetings = len(driver.find_element_by_class_name("rsm-MarketGroupWithTabs_Wrapper")
                               .find_elements_by_class_name("rsm-RacingSplashScroller"))

                for i in range(number_of_meetings):
                    race = {}
                    try:
                        meeting_name = (driver.find_element_by_class_name("rsm-MarketGroupWithTabs_Wrapper")
                                     .find_elements_by_class_name("rsm-RacingSplashScroller")[i]
                                     .find_element_by_class_name("rsm-MeetingHeader_MeetingName").text)

                        # populate meeting details from database or scrape them from the website if we don't have them yet
                        saved_meeting = populate_meeting(early_prices, meeting_name)

                        if saved_meeting is None:
                            # meeting not on database so get details from the website
                            race['name'] = meeting_name

                            elements = (driver.find_element_by_class_name("rsm-MarketGroupWithTabs_Wrapper")
                                        .find_elements_by_class_name("rsm-RacingSplashScroller")[i]
                                        .find_elements_by_class_name("rsm-UKRacingSplashParticipant_RaceName"))

                            element_clickable = False
                            for element in elements:
                                try:
                                    # navigate to the individual meeting
                                    if element_clickable:
                                        element.click()                     
                                        race['url'] = driver.current_url
                                        break
                                    
                                    if element.is_displayed():
                                        element_clickable = True
                                        next
                                    else:
                                        next

                                except Exception as ex:
                                    print(race)
                                    print(str(ex))
                                    driver.save_screenshot(race['name'] + '_url.png')

                            race['odds'] = None

                            # insert the new meeting to the database and add to the list to process
                            insert_race(race)
                            races.append(race)

                            # navigate back to the meetings page
                            driver.execute_script("window.history.go(-1)")

                            # try and appear human with random pauses
                            time.sleep(random.uniform(0.5, 1.5))
                        else:
                            # meeting is already saved on the database so just add to the list to process
                            races.append(saved_meeting)
                    except Exception as e:
                        print(race)
                        print(str(e))
                        driver.save_screenshot(race['name'] + '_error.png')

                # loop through all the found meetings 
                for race in races:
                    # if no odds stored go and get them from the webpage
                    if race['odds'] is None:
                        try:
                            # navigate to meeting webpage
                            driver.get(race['url'])

                            try:
                                # load the page and sleep randomly to appear more human
                                logging.debug('Meeting page started loading at ' + dt.now().strftime('%H:%M:%S'))
                                element_present = EC.presence_of_element_located((By.CLASS_NAME, 'gl-MarketGroup_Wrapper'))
                                WebDriverWait(driver, 10).until(element_present)
                                time.sleep(random.uniform(0.5, 1.5))
                                logging.debug('Meeting page finished loading at ' + dt.now().strftime('%H:%M:%S'))
                            except Exception as e:
                                logging.error(str(e))
                                driver.save_screenshot(race['name'] + '_error.png')
                         
                            odds = driver.find_element_by_class_name("srg-ParticipantGreyhoundsOdds_Odds").text

                            if odds != 'SP':
                                update_race(race)
                                send_message('B365 {} priced up!'.format(race['name']), test_mode, race['name'])

                        except Exception as e:
                            result = driver.find_element_by_class_name("srr-MarketEventHeaderInfoUk_ResultsLabel") # To do get result element
                            if result is not None:
                                update_race(race)
                                send_message('B365 {} priced up and meeting already started!'.format(race['name']),
                                             test_mode, race['name'])
                            else:
                                send_message('B365 Dog prices error - {}'.format(str(e)), True)
                                driver.save_screenshot('price_error.png')
        else:
            logging.info('B365 all meetings priced up.')

    except Exception as e:
        logging.error(str(e))
        logging.error(race)
        try:
            send_message('B365 dog prices error - {}'.format(str(e)), True)
        except Exception as err:
            logging.error(str(err))
        driver.save_screenshot("error.png")

    finally:
        logging.info('B365 Finished at ' + dt.now().strftime('%H:%M:%S'))
        if test_mode:
            from pprint import pprint
            pprint(races)


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    from utils import send_message
    # LOGLEVEL = os.environ.get('LOGLEVEL', 'DEBUG').upper()
    LOGLEVEL = 'INFO'
    # LOGLEVEL = 'DEBUG'
    logging.basicConfig(level=LOGLEVEL)

    logging.debug('Started')
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    if args.test:
        print("running in test mode")
        # send_message('testing', True)
        get_prices_b365(True)
    else:
        get_prices_b365(False)
