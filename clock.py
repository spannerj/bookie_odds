from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from tasks.players import get_players
from tasks.selections import get_selections
from tasks.mlt import get_mlt
from tasks.greyhounds import get_greyhounds
# from apscheduler.triggers.combining import AndTrigger
# from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()

# trigger = AndTrigger([
#    CronTrigger(hour='8-23'),
#    CronTrigger(minute='*/15')
# ])


@sched.scheduled_job('cron', minute='59', hour='23', month='1-5,8-12')
def cron_get_players():
    logging.info(' - Getting players')
    get_players()


@sched.scheduled_job('cron', minute='*/15', hour='7-22')
def daily_get_selections():
    logging.info(' - Getting selections')
    get_selections()
    get_mlt()
    get_greyhounds()


logging.info(' - Schedule starting')
# sched.add_job(daily_get_selections, trigger)
sched.start()
