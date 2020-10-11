from apscheduler.schedulers.blocking import BlockingScheduler
import logging
# from tasks.players import get_players
# from tasks.selections import get_selections
# from tasks.mlt import get_mlt
from tasks.greyhounds import get_prices
from tasks.greyhounds_pp import get_prices_pp
# from tasks.compare import get_bets
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

# # @sched.scheduled_job('cron', minute='*')
@sched.scheduled_job('cron', second='59')
# @sched.scheduled_job('cron', minute='*', hour='6-20')
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
