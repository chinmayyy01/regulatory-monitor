from apscheduler.schedulers.blocking import BlockingScheduler
from app.scheduler import run_pipeline

scheduler = BlockingScheduler()

scheduler.add_job(
    run_pipeline,
    trigger='interval',
    hours=12,
)

print('Scheduler started...')
print('Pipeline will run every 12 hours.')

run_pipeline()

scheduler.start()