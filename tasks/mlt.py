from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import hashlib
import os
import psycopg2
import logging
import traceback
import yagmail
import urllib.parse


def send_email(message, subject):
    password = os.environ['PWORD']
    yag = yagmail.SMTP('spencer.jago@digital.landregistry.gov.uk', password)
    contents = [message]
    emails = []
    emails.append('spencer.jago@gmail.com')
    emails.append('andy@channie.co.uk')

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


def get_db_hash():

    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT bet_hash
                 FROM selections
                 WHERE bet_type = 'mlt_nap'
                 fetch first 1 row only
                 """

    cursor.execute(select_sql)
    result = cursor.fetchall()
    commit_and_close(connection)
    return result[0][0]


def insert_new_hashes(nap_hash):
    connection = connect_to_db()
    cursor = connection.cursor()

    update_sql = """
                 UPDATE selections
                 SET bet_hash=%s
                 where bet_type = 'mlt_nap';
                 """
    try:
        cursor.execute(update_sql, (nap_hash,))
    except Exception as e:
        logging.error(e)
    commit_and_close(connection)


def hash_check(hashed_nap, db_hash):
    changes = False
    if hashed_nap != db_hash:
        changes = True

    # return True
    return changes


def hash_it(text):
    return hashlib.sha224(text.encode('utf-8')).hexdigest()


def send_message(message):
    message = urllib.parse.quote(message)
    url = 'https://api.telegram.org'
    url = url + '/bot810436987:AAESEw086nXGtqt_w9r09-By-5W2bt4fqbM/sendMessage'
    url = url + '?chat_id=-1001190331415&text={}'
    # url = 'https://api.telegram.org'
    # url = url + '/bot810436987:AAESEw086nXGtqt_w9r09-By-5W2bt4fqbM/sendMessage'
    # url = url + '?chat_id=-1001365813396&text={}'

    requests.get(url.format(message))


def set_up():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')

    browser = webdriver.Chrome(options=chrome_options)

    return browser


def get_nap(browser):
    browser.get('https://www.mylittletip.co.uk/nap')
    html = browser.page_source

    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find_all("p", {"class": "font_7"})
    for item in div:
        if "NAP is" in item.text:
            nap = item.text
            break

    return nap


def get_mlt():
    try:
        browser = set_up()

        nap = get_nap(browser)

        hashed_nap = hash_it(nap.strip())

        db_hash = get_db_hash()

        if hash_check(hashed_nap, db_hash):
            logging.info(nap)
            send_message(nap)
            send_email(nap, 'MLT NAP')
            insert_new_hashes(hashed_nap)
            logging.info(' - New MLT NAP found.')
        else:
            logging.info(' - No new MLT NAP bets.')

    except Exception as e:
        traceback.print_exc()
        logging.error(e)
    finally:
        browser.quit()


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    get_mlt()
