from apscheduler.schedulers.blocking import BlockingScheduler
import datetime

sched = BlockingScheduler()

# @sched.scheduled_job('interval', minutes=1)
# def timed_job():
#     print(datetime.datetime.now())
#     print('This job is run every minute.')

@sched.scheduled_job('cron', day_of_week='fri-sat', hour=1, minute=25)
def scheduled_job():
    print(datetime.datetime.now())
    print('Scheduled job running.')

sched.start()