from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from tasks.greyhounds_b365 import get_prices_b365
from tasks.greyhounds_pp import get_prices_pp
from tasks.greyhounds_sky import get_prices_sky
from tasks.greyhounds_lads import get_prices_lads
from tasks.greyhounds_wh import get_prices_wh

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()


# @sched.scheduled_job('cron', second='30')
# def daily_get_pp_greyhounds():
#     logging.info(' - Getting PP greyhounds')
#     get_prices_pp(False)


# @sched.scheduled_job('cron', second='0')
# def daily_get_b365_greyhounds():
#     logging.info(' - Getting B365 greyhounds')
#     get_prices_b365(False)


# @sched.scheduled_job('cron', second='15')
# def daily_get_sky_greyhounds():
#     logging.info(' - Getting Sky greyhounds')
#     get_prices_sky(False)


# @sched.scheduled_job('cron', second='45')
# def daily_get_lads_greyhounds():
#     logging.info(' - Getting Ladbrokes greyhounds')
#     get_prices_lads(True)


@sched.scheduled_job('cron', second='0')
def sky_and_lads():
    logging.info(' - Getting Sky greyhounds')
    try:
        get_prices_sky(False)
    except Exception as e:
        print(str(e))

    logging.info(' - Getting Ladbrokes greyhounds')
    try:
        get_prices_lads(False)
    except Exception as e:
        print(str(e))


@sched.scheduled_job('cron', second='30')
def wh_b365_pp():
    logging.info(' - Getting Bet365 greyhounds')
    try:
        get_prices_b365(False)
    except Exception as e:
        print(str(e))

    logging.info(' - Getting William Hill greyhounds')
    try:
        get_prices_wh(False)
    except Exception as e:
        print(str(e))

    logging.info(' - Getting Paddy Power greyhounds')
    try:
        get_prices_pp(False)
    except Exception as e:
        print(str(e))


logging.info(' - Schedule starting')
sched.start()
