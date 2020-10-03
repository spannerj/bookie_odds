from apscheduler.schedulers.blocking import BlockingScheduler
import logging
# from tasks.players import get_players
# from tasks.selections import get_selections
# from tasks.mlt import get_mlt
from tasks.greyhounds import get_prices
from tasks.greyhounds_pp import get_prices_pp
# from tasks.compare import get_bets
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



# @sched.scheduled_job('cron', second='8', minute='1', hour='0')
# def daily_delete_greyhounds_eve():
#     logging.info(' - Clearing greyhounds database')
#     reset_db()


# @sched.scheduled_job('cron', minute='*')
@sched.scheduled_job('cron', second='9', minute='10', hour='6')
def daily_delete_greyhounds_morning():
    logging.info(' - Clearing greyhounds database')
    reset_db()


# # @sched.scheduled_job('cron', minute='*')
@sched.scheduled_job('cron', minute='10', hour='21-22')
def daily_delete_greyhounds_late():
    logging.info(' - Clearing greyhounds database')
    reset_db()


# # @sched.scheduled_job('cron', minute='*')
@sched.scheduled_job('cron', minute='*/15', hour='1')
def daily_delete_greyhounds_early():
    logging.info(' - Clearing greyhounds database')
    reset_db()


# # @sched.scheduled_job('cron', minute='*')
@sched.scheduled_job('cron', minute='*', hour='6-19')
def daily_get_greyhounds():
    logging.info(' - Getting greyhounds')
    get_prices(False)

# # testing
# @sched.scheduled_job('cron', second='30')
# def daily_get_greyhounds():
#     logging.info(' - Getting greyhounds')
#     get_prices_pp(False)

# # testing
# @sched.scheduled_job('cron', second='0')
# def daily_get_greyhounds():
#     logging.info(' - Getting greyhounds')
#     get_prices_pp(False)


# @sched.scheduled_job('cron', second='30', hour='13-21')
# def daily_get_bets30():
#     logging.info(' - Getting bets 30')
#     get_bets()


# @sched.scheduled_job('cron', second='0', hour='13-21')
# def daily_get_bets0():
#     logging.info(' - Getting bets 0')
#     get_bets()


logging.info(' - Schedule starting')
# sched.add_job(daily_get_selections, trigger)
sched.start()
