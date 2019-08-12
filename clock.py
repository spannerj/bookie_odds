from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from tasks.players import get_players

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()


# @sched.scheduled_job('cron', minute='42', hour='00-23', month='1-5,8-12')
@sched.scheduled_job('cron', minute='59', hour='14-23', month='1-5,8-12')
def cron_get_players():
    logging.info(' - Getting players')
    get_players()


# @sched.scheduled_job('cron', hour=1, minute=0)
# def daily_get_players():
#     logging.info(' - Getting players')
#     get_players()

logging.info(' - Schedule starting')
sched.start()
