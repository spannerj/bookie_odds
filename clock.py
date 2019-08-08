from apscheduler.schedulers.blocking import BlockingScheduler
import json
import os
import sys
import datetime
import time
import pprint
import requests
from tqdm import tqdm
import logging
import psycopg2

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()

def safe_div(x, y):
    try:
        ret = x / y
    except:
        ret = 0
    return ret

# @sched.scheduled_job('interval', seconds=5)
# def timed_job():
#     sys.stdout.write(str(datetime.datetime.now()))
#     sys.stdout.flush()

@sched.scheduled_job('cron', hour=00, minute=55)
def scheduled_job():
    start = time.time()
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
    print('last completed week is ' + str(last_completed_week))
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
            new_player['games'] = str(player['SXI']) + str(player['SUBS'])
            try:
                float(player['POINTS'])
                new_player['total'] = player['POINTS']
            except:
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
            new_player['ppm6'] = round(safe_div(six_total, float(new_player['value'])), 2)
            all_players.append(new_player)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            print(e)

    conn = psycopg2.connect(database='dftt883bqn2re8', user='rjsqvpzxaqqhaz', password='b415e2b7ea14fd964e4855c92dd6bb9831018d04d5e135dfc2895995ea63b4f3', host='ec2-54-235-206-118.compute-1.amazonaws.com', port='5432')

    cur = conn.cursor()
    cur.execute("DELETE from players")
    cur.execute("INSERT INTO players (players) VALUES (%s)", (json.dumps(all_players),))
    conn.commit()
    conn.close()

    # with open('result.json', 'w') as fp:
    #     json.dump(all_players, fp)

    end = time.time()
    print(end - start)

sys.stdout.write('schedule starting')
sys.stdout.flush()
sched.start()