from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from tasks.greyhounds_b365 import get_prices_b365
from tasks.greyhounds_pp import get_prices_pp
from tasks.greyhounds_sky import get_prices_sky
from tasks.greyhounds_lads import get_prices_lads
from tasks.greyhounds_wh import get_prices_wh

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()


@sched.scheduled_job('cron', hour='6-23', second='30')
def daily_get_pp_greyhounds():
    logging.info(' - Getting PP greyhounds')
    get_prices_pp(False)


@sched.scheduled_job('cron', hour='6-23', second='0')
def daily_get_b365_greyhounds():
    logging.info(' - Getting B365 greyhounds')
    get_prices_b365(False)


@sched.scheduled_job('cron', hour='6-23', second='15')
def daily_get_sky_greyhounds():
    logging.info(' - Getting Sky greyhounds')
    get_prices_sky(False)


@sched.scheduled_job('cron', hour='6-23', second='45')
def daily_get_lads_greyhounds():
    logging.info(' - Getting Ladbrokes greyhounds')
    get_prices_lads(False)


@sched.scheduled_job('cron', hour='6-23', second='37')
def daily_get_wh_greyhounds():
    logging.info(' - Getting William Hill greyhounds')
    get_prices_wh(False)


logging.info(' - Schedule starting')
sched.start()
