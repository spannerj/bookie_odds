from apscheduler.schedulers.blocking import BlockingScheduler
import sys
import logging
from tasks.players import get_players

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()

# @sched.scheduled_job('interval', seconds=5)
# def timed_job():
#     logging.info(' - Getting players')
#     get_players()


@sched.scheduled_job('cron', hour=1, minute=0)
def daily_get_players():
    logging.info(' - Getting players')
    get_players()

logging.info(' - Schedule starting')
sched.start()