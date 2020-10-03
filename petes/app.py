import os
from datetime import datetime as dt
from flask import Flask, render_template, request
import psycopg2
import logging
from decimal import Decimal


app = Flask(__name__)
# app.config.from_object(os.environ['APP_SETTINGS'])


def connect_to_db():
    try:
        # pg_url = os.environ['PG_URL']
        pg_url = 'postgresql://postgres:@localhost:5432/betting'
        connection = psycopg2.connect(pg_url)
    except Exception as e:
        logging.error(e)

    return connection


def commit_and_close(connection):
    connection.commit()
    connection.close()


def insert_bet(bet):
    connection = connect_to_db()
    cursor = connection.cursor()

    insert_sql = """
                 INSERT INTO bets.petes_bets
                 (race_time, course, odds, horse, bet_size_total, bet_type, bet_date, bsp)
                 VALUES(%s, %s, %s, %s, %s, %s, %s, %s);
                 """
    try:
        logging.info('insert bet')
        race_time = dt.strptime(bet['time'], "%H.%M")

        stake = Decimal(bet['stake'].replace('£', ''))

        if bet['type'] == 'EW':
            stake = stake * 2

        bet_date = dt.strptime(bet['bet_date'], "%Y-%m-%d")

        cursor.execute(insert_sql, (race_time, bet['track'], bet['odds'], bet['horse'],
                       stake, bet['type'], bet_date, bet['bsp'], ))
    except Exception as e:
        logging.error(str(e))
        connection.rollback()
    finally:
        commit_and_close(connection)


def get_bsp(bet):
    connection = connect_to_db()
    cursor = connection.cursor()

    select_sql = """
                 SELECT bsp
                 FROM bsp.bsp_results
                 WHERE lower(SELECTION_NAME) = LOWER(%s)
                 AND RACE_DATE = %s
                 """

    try:
        cursor.execute(select_sql, (bet['horse'], bet['bet_date'],))
        result = cursor.fetchall()
        # commit_and_close(connection)
    except Exception as e:
        logging.error(e)
        connection.rollback()
    finally:
        commit_and_close(connection)

    # print(cursor.query)
    print('*****')
    print(bet)
    print(result)
    try:
        bsp = result[0][0]
    except Exception as e:
        print(str(e))
        print(bet)

    return bsp


def is_float(str):
    try:
        float(str)
        return True
    except ValueError:
        return False


def starts_with_digit(str):
    try:
        int(str[0])
        return True
    except ValueError:
        return False


def contain(string_):
    bet_types = ['NAP', 'Nap', 'NB', 'NextBest', 'EW', 'EachWay', 'IWAC']
    for bet_type in bet_types:
        if bet_type in string_:
            if bet_type == 'NextBest':
                bet_type = 'Next Best'
            if bet_type == 'EachWay':
                bet_type = 'Each Way'
            if bet_type == 'Nap':
                bet_type = 'NAP'
            return bet_type

    return None


def convert_odds_to_decimal(odds_string):
    odds = odds_string.split('-')
    decimal_odds = (int(odds[0]) / int(odds[1])) + 1

    return decimal_odds


def split_bet(bet_string):
    # print(bet_string)
    bet = {}
    track_time_found = False
    odds_found = False
    type_found = False
    track = ''
    horse = ''
    remaining = ''
    for word in bet_string:
        word = word.strip()
        if track_time_found is False:
            if is_float(word):
                bet['time'] = word
                bet['track'] = track.strip()
                track_time_found = True
                continue
            else:
                track = track + word + ' '
                continue

        if odds_found is False:
            if starts_with_digit(word):
                decimal_odds = convert_odds_to_decimal(word)
                bet['odds'] = decimal_odds
                bet['horse'] = horse.strip()
                odds_found = True
                continue
            else:
                horse = horse + word + ' '
                continue

        if type_found is False:
            if word[0] == '£':
                bet['stake'] = word
                type_found = True
                continue

        remaining = remaining + word

    bet['type'] = contain(remaining)
    # bet['remaining'] = remaining

    return bet


@app.route('/')
def student():
    return render_template('student.html')


@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        # results = request.form
        results = request.form.to_dict()
        print(results)
        bets_list = []
        for k, v in results.items():
            bets = v.splitlines()
        for bet in bets:
            words = bet.split(' ')
            while("" in words):
                words.remove("")

            bet = split_bet(words)
            bet['bet_date'] = results['bets_date']
            bet['bsp'] = get_bsp(bet)
            insert_bet(bet)
            bets_list.append(bet)

        # print(bets_list)
        return render_template("result.html", bets=bets_list)


if __name__ == '__main__':
    app.run(debug=True)
