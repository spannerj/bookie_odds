import json
import os
import requests
import psycopg2
from tqdm import tqdm
import yagmail
import logging


def safe_div(x, y):
    try:
        ret = x / y
    except Exception:
        ret = 0
    return ret


def send_email(message, send_to_all=False):
    password = os.environ['PWORD']
    yag = yagmail.SMTP('spencer.jago@digital.landregistry.gov.uk', password)
    contents = [message]
    emails = []
    emails.append('spencer.jago@gmail.com')
    if send_to_all:
        emails.append('spencer.jago@landregistry.gov.uk')
        emails.append('andy.reed@landregistry.gov.uk')

    yag.send(emails, 'LR Fantasy Football', contents)


def update_players(all_players, last_completed_week, latest_week):
    pg_database = os.environ['PG_DATABASE']
    pg_user = os.environ['PG_USER']
    pg_password = os.environ['PG_PASSWORD']
    pg_host = os.environ['PG_HOST']
    pg_port = os.environ['PG_PORT']
    conn = psycopg2.connect(database=pg_database,
                            user=pg_user,
                            password=pg_password,
                            host=pg_host,
                            port=pg_port)

    cur = conn.cursor()
    insert_sql = """
                    INSERT INTO players (players, last_week, current_week)
                    VALUES (%s, %s, %s)
                 """
    cur.execute(insert_sql, (json.dumps(all_players),
                             last_completed_week,
                             latest_week,))
    conn.commit()
    conn.close()


def select_latest_week():
    pg_database = os.environ['PG_DATABASE']
    pg_user = os.environ['PG_USER']
    pg_password = os.environ['PG_PASSWORD']
    pg_host = os.environ['PG_HOST']
    pg_port = os.environ['PG_PORT']
    conn = psycopg2.connect(database=pg_database,
                            user=pg_user,
                            password=pg_password,
                            host=pg_host,
                            port=pg_port)

    cur = conn.cursor()
    select_sql = """
                 SELECT last_week, current_week
                 FROM players
                 where created_at = (select max(created_at) from players limit 1)
                 """
    cur.execute(select_sql)
    result = cur.fetchall()
    conn.commit()
    conn.close()
    return result[0][0], result[0][1]


def get_fixtures():
    # find last completed week
    url = 'https://fantasyfootball.telegraph.co.uk/premier-league/json/fixtures/all'
    response = requests.get(url)
    fixtures_dict = {}
    fixtures_dict = response.json()
    latest_week = 42
    for fixture in fixtures_dict:
        if fixture['RESULT'] == 'X':
            if int(fixture['WEEK']) < latest_week:
                latest_week = int(fixture['WEEK'])
    last_completed_week = latest_week - 1

    return last_completed_week, latest_week


def get_players():
    process = True
    # get last week and current week from the last run
    last_completed_week_db, latest_week_db = select_latest_week()
    last_completed_week, latest_week = get_fixtures()
    if last_completed_week_db == last_completed_week:
        send_email('Schedule run, No updates')
        logging.info(' - Week not completed yet. Exit')
        process = False

    if process:
        print('last completed week is ' + str(last_completed_week))
        print('latest week is ' + str(latest_week))

        # get all players
        url = 'https://fantasyfootball.telegraph.co.uk/premier-league/json/getstatsjson'
        response = requests.get(url)
        players_dict = {}
        players_dict = response.json()
        all_players = []
        for player in tqdm(players_dict['playerstats']):
            # for each player get scores
            url = 'https://fantasyfootball.telegraph.co.uk/premier-league/json/playerstats/player/'
            response = requests.get(url)
            response = requests.get(url + player['PLAYERID'])
            scores_dict = {}
            scores_dict = response.json()
            try:
                new_player = {}
                new_player['id'] = player['PLAYERID']
                new_player['name'] = player['PLAYERNAME']
                new_player['club'] = player['TEAMCODE']
                new_player['value'] = player['VALUE']
                new_player['games'] = int(player['SXI']) + int(player['SUBS'])
                try:
                    float(player['POINTS'])
                    new_player['total'] = player['POINTS']
                except Exception:
                    new_player['total'] = 0
                new_player['ppg'] = round(safe_div(int(new_player['total']), new_player['games']), 2)
                new_player['ppm'] = round(safe_div(float(new_player['total']), float(player['VALUE'])), 2)
                new_player['ppmg'] = round(safe_div(new_player['ppm'], new_player['games']), 3)
                new_player['weeks'] = []
                for week in range(1, latest_week):
                    new_player['weeks'].append('')
                for score in scores_dict['DATA']['STATS'][1:]:
                    if int(score['WEEK']) <= last_completed_week:
                        week_total = new_player['weeks'][int(score['WEEK'])-1]
                        if week_total == '':
                            week_total = int(score['PTS'])
                        else:
                            week_total = week_total + int(score['PTS'])
                        new_player['weeks'][int(score['WEEK'])-1] = week_total
                # 6 game form stats
                six_total = 0
                six_games = 0
                for score in scores_dict['DATA']['STATS'][1:]:
                    if int(score['WEEK']) > last_completed_week - 6:
                        six_total = six_total + int(score['PTS'])
                        six_games += 1
                new_player['t6'] = six_total
                new_player['g6'] = six_games
                if six_games == 0:
                    new_player['ppg6'] = 0
                else:
                    new_player['ppg6'] = round(safe_div(six_total, six_games), 2)
                new_player['ppm6'] = round(safe_div(six_total,
                                        float(new_player['value'])), 2)
                all_players.append(new_player)
                # break # uncomment for faster testing of a single player

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                print(e)

        update_players(all_players, last_completed_week, latest_week)

        send_email('Scores updated for week ' + str(last_completed_week), True)


# This is present for running the file outside of the schedule for testing
# purposes. ie. python tasks/players.py
if __name__ == '__main__':
    get_players()
