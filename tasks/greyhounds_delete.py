import os
import psycopg2
import logging
from utils import send_message


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


def clear_db():
    connection = connect_to_db()
    cursor = connection.cursor()

    delete_sql = """
                 DELETE FROM b365_early_prices
                 """

    result = cursor.execute(delete_sql)
    commit_and_close(connection)
    return result


def reset_db():
    try:
        clear_db()
        send_message('Database cleared', True)

    except Exception as e:
        logging.error(str(e))

    finally:
        logging.info('Database cleared')


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/selections.py
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    reset_db()
