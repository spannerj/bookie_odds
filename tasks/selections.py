from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import hashlib
import os
import psycopg2
import logging
import traceback
import time
import yagmail
import urllib.parse


URL_DICT = {
    "Double": "https://betracingnationclub.com/daily-double/",
    "Singles": "https://betracingnationclub.com/selections/",
    "Patent": "https://betracingnationclub.com/a-petes-patent/",
    "Trebles": "https://betracingnationclub.com/a-saturday-six-trebles/"
}


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


def get_db_hash(bet_type):

    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT bet_hash
                 FROM selections
                 WHERE bet_type = '{}'
                 fetch first 1 row only
                 """

    cursor.execute(select_sql.format(bet_type))
    result = cursor.fetchall()
    commit_and_close(connection)
    return result[0][0]


def xcheck(bet):
    stripped_bet = "".join(bet.split())
    if 'xxxxx' in stripped_bet:
        return True
    else:
        return False


def bet_list_length_check(bet_list):
    if len(bet_list) < 6:
        for i in range(6 - len(bet_list)):
            bet_list.append('')

    return bet_list


def insert_new_hashes(bet_hash, bet_type):
    connection = connect_to_db()
    cursor = connection.cursor()

    update_sql = """
                 UPDATE selections
                 SET bet_hash=%s
                 where bet_type = %s;
                 """
    try:
        cursor.execute(update_sql, (bet_hash, bet_type,))
    except Exception as e:
        logging.error(e)
    commit_and_close(connection)


def hash_check(hashed_bet_list, db_hash):
    changes = False
    if hashed_bet_list != db_hash:
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


def login_to_site():
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
    time.sleep(1)
    browser.find_element_by_id('user_login').send_keys(os.environ['WP_USER'])
    browser.find_element_by_id('user_pass').send_keys(os.environ['WP_PASSWORD'])
    time.sleep(1)
    browser.find_element_by_name('wp-submit').click()
    time.sleep(1)

    return browser


def parse_table(browser, url, bet_type):
    add_text = ''
    browser.get(url)
    time.sleep(2)
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    if bet_type != 'Singles':
        find_res = soup.find_all('section')[1].find('span')
        if find_res is None:
            find_res = soup.find_all('section')[1].find('strong')
        add_text = '\n' + find_res.text + '\n'

    table = soup.find('table')
    table_rows = table.find_all('tr')[1:]
    bet_list = []
    for tr in table_rows:
        bet = ''
        td = tr.find_all('td')
        for i in td:
            bet = bet + ' ' + i.text

        if bet.strip() != 'None':
            bet_list.append(bet.strip())
        else:
            bet_list.append('')

    return bet_list, add_text


def assemble_bets(bet_type, bet_list, add_text):
    message = ''

    for i in range(len(bet_list)):
        if bet_list[i] != '':
            if not xcheck(bet_list[i]):
                message = message + bet_list[i] + '\n'

    if message.strip() != '':
        if add_text == '':
            message = bet_type + '\n' + message
        else:
            message = bet_type + add_text + '\n' + message

    return message


def get_selections():
    try:
        browser = login_to_site()
        email_message = ''
        for bet_type, url in URL_DICT.items():
            bet_list, add_text = parse_table(browser, url, bet_type)

            bet_list = bet_list_length_check(bet_list)
            message = assemble_bets(bet_type, bet_list, add_text)

            hashed_bet_list = hash_it(message)

            db_hash = get_db_hash(bet_type)

            if hash_check(hashed_bet_list, db_hash):
                if message != '':
                    email_message = email_message + message + '\n\n'
                    logging.info(message)
                    send_message(message)
                    insert_new_hashes(hashed_bet_list, bet_type)
                    logging.info(' - New ' + bet_type + ' bet found.')
                else:
                    logging.info(' - No new ' + bet_type + ' bets.')
            else:
                logging.info(' - No new ' + bet_type + ' bets.')

        if email_message.strip() != '':
            send_email(email_message, 'Petes selections')

    except Exception as e:
        traceback.print_exc()
        logging.error(e)
    finally:
        browser.quit()


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    get_selections()
