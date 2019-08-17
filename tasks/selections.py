from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import time
from os import remove
import hashlib
import os
import csv
import psycopg2
import logging


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


def get_db_hashes():

    connection = connect_to_db() 
    cursor = connection.cursor()

    select_sql = """
                 SELECT bet_hash1,  bet_hash2, bet_hash3, bet_hash4, bet_hash5
                 FROM selections
                 fetch first 1 row only
                 """

    cursor.execute(select_sql)
    result = cursor.fetchall()
    commit_and_close(connection)
    return result[0]


def insert_new_hashes(bet_list):

    connection = connect_to_db() 
    cursor = connection.cursor()

    insert_sql = """
                 INSERT INTO selections (bet_hash1,  bet_hash2, bet_hash3, bet_hash4, bet_hash5)
                 VALUES (%s, %s, %s, %s, %s)
                 """

    cursor.execute('DELETE FROM selections')
    cursor.execute(insert_sql, (bet_list[0], bet_list[1], bet_list[2], bet_list[3], bet_list[4],))
    commit_and_close(connection)


def hash_check(hashed_bet_list, db_hashes, bet_list):
    changes = False
    for i in range(5):
        if hashed_bet_list[i] != db_hashes[i]:
            changes = True
            if bet_list[i] != 'None':
                logging.info(' - New bet found')
                send_message(bet_list[i])

    return changes


def hash_it(text):
    return hashlib.sha224(text.encode('utf-8')).hexdigest()


def send_message(message):
    requests.get("https://api.telegram.org/bot810436987:AAESEw086nXGtqt_w9r09-By-5W2bt4fqbM/sendMessage?chat_id=-1001190331415&text={}".format(message))


def get_selections():
    try:
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
        # browser.get('https://betracingnationclub.com/log-in/')
        browser.get('https://betracingnationclub.com/wp-login.php')
        # browser.save_screenshot("screenshot.png")
        browser.find_element_by_id('user_login').send_keys(os.environ['WP_USER'])
        browser.find_element_by_id('user_pass').send_keys('WP_PASSWORD')
        # browser.save_screenshot("screenshot1.png")
        browser.find_element_by_name('wp-submit').click()
        browser.get('https://betracingnationclub.com/selections/')
        # browser.save_screenshot('screenshot1.png')
        html = browser.page_source
        browser.quit()
        # with open("page.html","w") as fp:
        #     fp.write(html)
        soup = BeautifulSoup(html, 'html.parser')
        # with open("page.html", "r", encoding='utf-8') as f:
        #     html = f.read()

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        table_rows = table.find_all('tr')[1:]

        bet_list = []
        for tr in table_rows:
            bet = ''
            td = tr.find_all('td')
            for i in td:
                bet = bet + ' ' + i.text

            if bet != 'None':
                bet_list.append(bet.strip())

        hashed_bet_list = []
        for bet in bet_list:
            hashed_bet = hash_it(bet)
            hashed_bet_list.append(hashed_bet)

        db_hashes = get_db_hashes()

        if hash_check(hashed_bet_list, db_hashes, bet_list):
            insert_new_hashes(hashed_bet_list)
        else:
            logging.info(' - No new bets.')

    except Exception as e:
        logging.error(e)


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    get_selections()
