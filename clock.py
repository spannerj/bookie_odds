from apscheduler.schedulers.blocking import BlockingScheduler
import os
import logging
import yagmail
from tasks.players import get_players

logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler()

# @sched.scheduled_job('interval', seconds=5)
# def timed_job():
#     password = os.environ['PWORD']
#     yag = yagmail.SMTP('spencer.jago@digital.landregistry.gov.uk', password)
#     contents = [ 'Site up to date. ']

#     yag.send('spencer.jago@gmail.com', 'LR Fantasy Football', contents)


@sched.scheduled_job('cron', hour=1, minute=0)
def daily_get_players():
    logging.info(' - Getting players')
    get_players()
    
    password = os.environ['PWORD']
    yag = yagmail.SMTP('spencer.jago@digital.landregistry.gov.uk', password)
    contents = [ 'Site up to date. ']
    yag.send('spencer.jago@gmail.com', 'LR Fantasy Football', contents)

logging.info(' - Schedule starting')
sched.start()