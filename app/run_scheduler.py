from apscheduler.schedulers.blocking import BlockingScheduler
from app.scheduler import run_pipeline

scheduler = BlockingScheduler()

scheduler.add_job(
    run_pipeline,
    trigger='interval',
    minutes=1,
)

print('Scheduler started...')
print('Pipeline will run every 1 minute.')

run_pipeline()

scheduler.start()