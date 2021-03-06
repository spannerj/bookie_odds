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


def get_meeting_status():
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT race_name, url, odds_present
                 FROM sky_early_prices
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


def excluded(race):
    excluded = False
    excluded_list = ['Orange Park', 'Iowa', 'Derby Lane', 'Palm Beach', 'Wheeling Island', 'Caliente', 'Caliente AM']
    if race in excluded_list:
        excluded = True
    return excluded


def insert_race(race):
    connection = connect_to_db()
    cursor = connection.cursor()

    insert_sql = """
                 INSERT INTO sky_early_prices
                 (race_name, url, time_added)
                 VALUES(%s, %s, %s);
                 """
    try:
        insert_time = dt.now()
        cursor.execute(insert_sql, (race['name'],  race['url'], insert_time, ))
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
                 UPDATE sky_early_prices
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
            race['odds'] = price[3]
            race_saved = race
            break
    return race_saved


def populate_meeting(saved_meetings, meeting_name):
    # match the meeting to the saved data or retun None 
    meeting = None
    for meet in saved_meetings:
        if meet[0] == meeting_name:
            race = {}
            race['name'] = meet[0]
            race['url'] = meet[1]
            race['odds'] = meet[2]
            meeting = race
            break
    return meeting


def get_all_links(driver):
    links = []
    elements = driver.find_elements_by_tag_name('a')
    for elem in elements:
        href = elem.get_attribute("href")
        links.append(href)
    return links


def clear_database():
    # clear old rows from the table ready to start again
    connection = connect_to_db()
    cursor = connection.cursor()

    delete_sql = """
                 DELETE FROM sky_early_prices
                 """

    result = cursor.execute(delete_sql)
    commit_and_close(connection)
    return result


def get_last_update():
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT max(time_added)
                 FROM sky_early_prices
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
            today = dt.now().date()
            if today > last_update.date():
                clear_database()
                send_message('Sky database cleared', True)  
                return


def all_priced_up(early_prices):
    # Return false if any meeting is still waiting for prices
    for price in early_prices:
        if price[2] is None:
            return False
    return True


def get_prices_sky(test_mode):
    logging.info('Sky Started at ' + dt.now().strftime('%H:%M:%S'))

    # check last update and clear db if required
    last_update = get_last_update()
    clear_database_check(last_update)

    # get meeting details from the database
    saved_meetings = get_meeting_status()

    # if database empty or meetings still to price up
    if (len(saved_meetings) == 0) or (not all_priced_up(saved_meetings)):

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

                # navigate to meetings page
                driver.get('https://m.skybet.com/greyhound-racing#tab:meetings')
                try:
                    # wait for cookies alert to load. No need to accept but code below commented out if needed
                    element_present = EC.presence_of_element_located((By.ID, 'page-content'))
                    WebDriverWait(driver, 10).until(element_present)
                except Exception as e:
                    logging.error(str(e))

                # accept cookies (need to find cookie accept element name)
                # driver.find_element_by_css_selector("#").click()

                # create empty list to hold meeting details
                meeting_list = []
                try:
                    meetings = driver.find_elements_by_css_selector('#events-by-meeting > li')

                    if meetings !=None:
                        for meeting in meetings:
                            race = {}
                            
                            if meeting.text == 'Today':
                                continue  

                            if meeting.text == 'Tomorrow':
                                break  

                            race['name'] = meeting.find_element_by_css_selector("h2 > span.accordion__title.split > span.split__title").text
                            
                            # populate meeting details from database or scrape them from the website if we don't have them yet
                            saved_meeting = populate_meeting(saved_meetings, race['name']) 

                            if saved_meeting is None:
                                # get all race links
                                links = get_all_links(meeting)

                                if len(links) > 0:
                                    race['url'] = links[0]
                                    race['odds'] = None

                                    if not excluded(race['name'].strip()):
                                        insert_race(race)
                                        meeting_list.append(race)
                            else:
                                # meeting already in the database so just add to the meeting list
                                meeting_list.append(saved_meeting)

                except Exception as e:
                    print(str(e))
                    driver.save_screenshot("screenshot.png")

                # loop over races
                for race in meeting_list:
                    # if race not yet priced navigate to race page
                    if race['odds'] is None:
                        driver.get(race['url'])

                        try:
                            # wait for odds element to load
                            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'event-meta__title'))
                            WebDriverWait(driver, 10).until(element_present)
                        except Exception as e:
                            logging.error(str(e))

                        try:
                            # search for first odds element on page
                            odds = driver.find_element_by_class_name('js-oc-price')

                            # if we aren't SP then we are priced up.
                            if odds.text != 'SP':
                                # update race on database
                                update_race(race)
                                send_message('Sky - ' + race['name'] + ' priced up', test_mode, race['name']) 
                                print(race['name'] + ' priced up')
                        except Exception as e:
                            if driver.find_element_by_css_selector("#page-content > section.islet.event-meta > h1 > span").text == 'Settled':
                                update_race(race)
                                send_message('Sky - It looks like ' + race['name'] + ' is in progress or finished without being priced up', test_mode)    
        finally:
            driver.quit()
    else:
        logging.info('Sky all meetings priced up.')

    logging.info('Sky finished at ' + dt.now().strftime('%H:%M:%S'))

# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
    logging.basicConfig(level=LOGLEVEL)

    logging.debug('Sky Started')
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    if args.test:
        print("running in test mode")
        # send_message('testing', True)
        get_prices_sky(True)
    else:
        get_prices_sky(False)
