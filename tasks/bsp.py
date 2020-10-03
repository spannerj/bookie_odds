import pandas as pd
from pathlib import Path
import datetime
from datetime import datetime as dt, timedelta
import os
from datetime import timedelta, date
import psycopg2
import logging
from psycopg2.extras import execute_values
logging.getLogger().setLevel(logging.ERROR)


def connect_to_db():
    try:
        # pg_url = os.environ['PG_URL']
        # pg_url = 'postgresql://postgres:localhost:5432/betting'
        # pg_url = 'postgresql://land_register_enhancement_service:land_register_enhancement_service@localhost:5432/postgres'
        connection = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='betting',
            user='postgres',
        )
        # connection = psycopg2.connect(pg_url)
    except Exception as e:
        logging.error(e)
    return connection


def commit_and_close(connection):
    connection.commit()
    connection.close()


def insert_races(results_list, insert_sql):
    connection = connect_to_db()
    cursor = connection.cursor()

    try:
        execute_values(cursor, insert_sql, results_list)
    except Exception as e:
        logging.error(e)
        connection.rollback()
    finally:
        commit_and_close(connection)


def get_last_date():
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT last_date
                 FROM bsp.last_date
                 """

    try:
        cursor.execute(select_sql)
        result = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        connection.rollback()
    finally:
        commit_and_close(connection)

    return result[0][0]


def update_last_date(last_date):
    connection = connect_to_db()
    cursor = connection.cursor()

    update_sql = """
                 UPDATE bsp.last_date
                 SET last_date = %s
                 """
    try:
        cursor.execute(update_sql, (last_date, ))
    except Exception as e:
        logging.error(e)
        connection.rollback()
    finally:
        commit_and_close(connection)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + timedelta(n)


def process_csv(df, file_index):
    results_list = []
    for index, row in df.iterrows():
        if row['WIN_LOSE'] > 0:
            WIN = True
        else:
            WIN = False

        race_time = dt.strptime(row['EVENT_DT'].split(' ')[1], "%H:%M")
        race_date = dt.strptime(row['EVENT_DT'].split(' ')[0], "%d-%m-%Y")

        # results_list.append((row['EVENT_DT'], row['SELECTION_NAME'], WIN, round(float(row['BSP']), 2)))
        results_list.append((race_date, race_time, row['SELECTION_NAME'], WIN, round(float(row['BSP']), 2)))

    if file_index == 0:
        insert_sql = """
                    INSERT INTO bsp.bsp_results
                    (race_date, race_time, selection_name, win, bsp)
                    VALUES %s ON CONFLICT ON CONSTRAINT bsp_results_pk DO NOTHING
                    """
    else:
        insert_sql = """
                    INSERT INTO bsp.bsp_results_dogs
                    (race_date, race_time, selection_name, win, bsp)
                    VALUES %s ON CONFLICT ON CONSTRAINT bsp_results_dogs_pk DO NOTHING
                    """

    insert_races(results_list, insert_sql)


# start_date = date(2020, 7, 1)
# start_date = datetime.date.today()
start_date = get_last_date()
today = datetime.date.today()
end_date = today - timedelta(days=1)

files = ['dwbfpricesukwin', 'dwbfgreyhoundwin']

for i, file_name in enumerate(files):
    for single_date in daterange(start_date, end_date):
        today_fmt = single_date.strftime("%d%m%Y")
        full_file_name = "{}{}.csv".format(file_name, today_fmt)

        url = "https://promo.betfair.com/betfairsp/prices/{}".format(full_file_name)
        print(url)
        try:
            df = pd.read_csv(url)
            df = df.sort_values(by='EVENT_DT')
            process_csv(df, i)
        except Exception as e:
            print(str(e))
            pass

update_last_date(end_date)
