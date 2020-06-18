from apscheduler.schedulers.blocking import BlockingScheduler
import logging
# from tasks.players import get_players
# from tasks.selections import get_selections
# from tasks.mlt import get_mlt
from tasks.greyhounds import get_prices
from tasks.greyhounds_delete import reset_db
# from apscheduler.triggers.combining import AndTrigger
# from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()

# trigger = AndTrigger([
#    CronTrigger(hour='8-23'),
#    CronTrigger(minute='*/15')
# ])


# @sched.scheduled_job('cron', minute='59', hour='23', month='1-5,8-12')
# def cron_get_players():
#     logging.info(' - Getting players')
#     get_players()


# @sched.scheduled_job('cron', minute='*/10', hour='7-23')
# def daily_get_selections():
#     logging.info(' - Getting selections')
#     get_selections()
#     # get_mlt()

@sched.scheduled_job('cron', minute='59', hour='6')
def daily_delete_greyhounds():
    logging.info(' - Clearing greyhounds database')
    reset_db()

# @sched.scheduled_job('cron', minute='*')
@sched.scheduled_job('cron', minute='*', hour='7-19')
def daily_get_greyhounds():
    logging.info(' - Getting greyhounds')
    get_prices()


logging.info(' - Schedule starting')
# sched.add_job(daily_get_selections, trigger)
sched.start()
