from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.utils.log import app_logger
from app.jobs.dixcover import run_scan
from app.services.database import engine
from app.jobs.probe_master import probe_master

# Use the application's SQLAlchemy engine so APScheduler persists jobs
_scheduler = BackgroundScheduler(jobstores={
    'default': SQLAlchemyJobStore(engine=engine)
})


def start_scheduler():
    if not _scheduler.running:
        _scheduler.start()
        app_logger.info("scheduler: started")


def shutdown_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=True)
        app_logger.info("scheduler: shutdown")


def add_daily_job(domain: str):
    """
    add a daily job for `domain`. Job id is normalized.
    if a job already exists do nothing.
    """
    job_id = f"scan_{domain.replace('.', '_')}"
    if _scheduler.get_job(job_id):
        app_logger.info(f"scheduler: job already exists {job_id}")
        return

    # schedule run_scan to run once a day - run immediately on next tick if desired
    _scheduler.add_job(run_scan, 'interval', days=1, args=[domain, True], id=job_id, replace_existing=False)
    app_logger.info(f"scheduler: added daily job {job_id} for {domain}")


def add_daily_probe_job():
    """Schedule the `probe_master` job to run once per day (persistent jobstore).

    If a probe job already exists, this is a no-op.
    """
    job_id = "probe_master_daily"
    if _scheduler.get_job(job_id):
        app_logger.info(f"scheduler: probe job already exists {job_id}")
        return

    _scheduler.add_job(probe_master, 'interval', days=1, id=job_id, replace_existing=False)
    app_logger.info(f"scheduler: added daily probe job {job_id}")


def remove_probe_job():
    job_id = "probe_master_daily"
    job = _scheduler.get_job(job_id)
    if job:
        _scheduler.remove_job(job_id)
        app_logger.info(f"scheduler: removed probe job {job_id}")


def remove_job(domain: str):
    job_id = f"scan_{domain.replace('.', '_')}"
    job = _scheduler.get_job(job_id)
    if job:
        _scheduler.remove_job(job_id)
        app_logger.info(f"scheduler: removed job {job_id}")