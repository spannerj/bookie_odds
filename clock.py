from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from tasks.greyhounds import get_prices_b365
from tasks.greyhounds_pp import get_prices_pp

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()


@sched.scheduled_job('cron', second='30', hour='6-23')
def daily_get_pp_greyhounds():
    logging.info(' - Getting PP greyhounds')
    get_prices_pp(False)


@sched.scheduled_job('cron', second='0', hour='6-23')
def daily_get_b365_greyhounds():
    logging.info(' - Getting B365 greyhounds')
    get_prices_b365(False)


logging.info(' - Schedule starting')
sched.start()
