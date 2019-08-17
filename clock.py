from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from tasks.players import get_players
from tasks.selections import get_selections

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()

from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger

trigger = OrTrigger([
   CronTrigger(hour='16-23'),
#    CronTrigger(hour='02-03'),
   CronTrigger(minute='*/15')
])


@sched.scheduled_job('cron', minute='59', hour='19-23', month='1-5,8-12')
def cron_get_players():
    logging.info(' - Getting players')
    get_players()


def daily_get_selections():
    logging.info(' - Getting selections')
    get_selections()


logging.info(' - Schedule starting')
sched.add_job(daily_get_selections, trigger)
sched.start()
