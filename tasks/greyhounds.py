import requests
import os
import psycopg2
import logging
import yagmail
import urllib.parse
from telethon import TelegramClient, events, sync
from telethon.tl.types import InputChannel
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.sessions import StringSession


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


def get_last_message_id():

    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT bet_hash
                 FROM selections
                 WHERE bet_type = 'greyhounds'
                 fetch first 1 row only
                 """

    cursor.execute(select_sql)
    result = cursor.fetchall()
    commit_and_close(connection)
    return result[0][0]


def update_message_id(message_id):
    connection = connect_to_db()
    cursor = connection.cursor()

    update_sql = """
                 UPDATE selections
                 SET bet_hash=%s
                 where bet_type = 'greyhounds';
                 """
    try:
        cursor.execute(update_sql, (message_id,))
    except Exception as e:
        logging.error(e)
    commit_and_close(connection)


def send_message(message):
    message = urllib.parse.quote(message)
    # monitor channel
    url = 'https://api.telegram.org'
    url = url + '/bot810436987:AAESEw086nXGtqt_w9r09-By-5W2bt4fqbM/sendMessage'
    url = url + '?chat_id=-1001190331415&text={}'

    # JagoTest channel for testing
    # url = 'https://api.telegram.org'
    # url = url + '/bot810436987:AAESEw086nXGtqt_w9r09-By-5W2bt4fqbM/sendMessage'
    # url = url + '?chat_id=-1001365813396&text={}'

    requests.get(url.format(message))


def get_greyhounds():
    last_id = get_last_message_id()

    session_string = os.environ['SESSION_ID']

    client = TelegramClient(StringSession(session_string),
                            864949,
                            '11ba75ff41d658954810528446facd8e')

    client.connect()

    if not client.is_user_authorized():
        logging.info(' - Telegram not authorised'')
        print('not authorised')

    # set up output channel
    output_channel_entity = None
    for d in client.iter_dialogs():
        # if d.id == -1001365813396: # Jago test
        if d.id == -1001190331415:  # Monitor
            output_channel_entity = InputChannel(d.entity.id,
                                                 d.entity.access_hash)

    channel_entity = client.get_entity(-1001454675970) # 'Greyhounds November'

    posts = client(GetHistoryRequest(
        peer=channel_entity,
        limit=10,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=int(last_id),
        add_offset=0,
        hash=0))

    for message in reversed(posts.messages):
        client.send_message(output_channel_entity, message)
        update_message_id(str(message.id))


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    get_greyhounds()
