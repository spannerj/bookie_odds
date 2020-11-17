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

    insert_sql = """
                 INSERT INTO pp_early_prices
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
                 DELETE FROM pp_early_prices
                 """

    result = cursor.execute(delete_sql)
    commit_and_close(connection)
    return result


def get_last_update():
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT max(time_added)
                 FROM pp_early_prices
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
                send_message('PP database cleared', True)  
                return


def all_priced_up(early_prices):
    # Return false if any meeting is still waiting for prices
    for price in early_prices:
        if price[2] is None:
            return False
    return True


def get_prices_pp(test_mode):
    logging.info('PP Started at ' + dt.now().strftime('%H:%M:%S'))

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
                driver.get('https://www.paddypower.com/greyhound-racing?tab=meetings')
                try:
                    # wait for cookies alert to load. No need to accept but code below commented out if needed
                    element_present = EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
                    WebDriverWait(driver, 10).until(element_present)
                except Exception as e:
                    logging.error(str(e))

                # accept cookies
                # driver.find_element_by_css_selector("#onetrust-accept-btn-handler").click()

                # create empty list to hold meeting details
                meeting_list = []
                try:
                    # locate all the regions, UK, USA etc
                    groups = driver.find_elements_by_css_selector("card-meetings-races > div > region-group")

                    # look through groups until we find the UK
                    uk_group = None
                    for group in groups:   
                        location = group.find_element_by_css_selector("div.header-description > h2").text 
                        if location == 'UK & Ireland':
                            uk_group = group
                            break

                    # if we have found the UK find each meeting and store details
                    if uk_group is not None:
                        meetings = uk_group.find_elements_by_css_selector("div > abc-card-content > meeting-card-item")
                        for meeting in meetings: 
                            race = {}
                            race['name'] = meeting.find_element_by_css_selector("span.meeting-card-item__title.accordion__title").text

                            # populate meeting details from database or scrape them from the website if we don't have them yet
                            saved_meeting = populate_meeting(saved_meetings, race['name'])  

                            # if meeting isn't already saved get the last race link and save to the database
                            if saved_meeting is None:
                                # get all race links
                                links = get_all_links(meeting)

                                if len(links) > 0:
                                    # if we have found links store the final race link
                                    # race['url'] = links[len(links) -  1]
                                    race['url'] = links[1]
                                    # insert race to the database
                                    insert_race(race)
                                    race['odds'] = None
                                    # add the race to our meeting list
                                    meeting_list.append(race)
                                    next
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
                            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'btn-odds__label'))
                            WebDriverWait(driver, 10).until(element_present)
                        except Exception as e:
                            logging.error(str(e))

                        try:
                            # search for first odds element on page
                            odds = driver.find_element_by_css_selector('div.button__content-container > ng-transclude > span')

                            # if we aren't SP then we are priced up.
                            if odds.text != 'SP':
                                # update race on database
                                update_race(race)
                                send_message('Paddy Power - ' + race['name'] + ' priced up', test_mode, race['name']) 

                        except Exception as e:
                            if race['url'] != driver.current_url:
                                send_message('Paddy Power - It looks like ' + race['name'] + ' finished without being priced up', test_mode)    
                            print(str(e))
                            driver.save_screenshot("error.png")
                            print(meeting_list)
                            print(race)
        finally:
            driver.quit()
    else:
        logging.info('PP all meetings priced up.')

    logging.info('PP finished at ' + dt.now().strftime('%H:%M:%S'))

# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
    logging.basicConfig(level=LOGLEVEL)

    logging.debug('PP Started')
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    if args.test:
        print("running in test mode")
        # send_message('testing', True)
        get_prices_pp(True)
    else:
        get_prices_pp(False)
