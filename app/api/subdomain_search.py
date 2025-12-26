from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.services.database import get_db
from app.schemas.domain_input import DomainInput
from app.utils.log import app_logger
from app.middleware.security import Security
from app.services.crtsh_service import CrtshService
from app.services.virus_total_service import VirusTotalService
from app.services.shodan_service import ShodanService
from app.services.otx_service import OtxService
from app.services.database import SessionLocal
from app.models.domain_requested import DomainRequested
from fastapi import HTTPException
from datetime import datetime
from app.jobs.scheduler import add_daily_job

import asyncio

router = APIRouter(tags=["Subdomains_Gathering"])

async def concurrent_tasks(tasks: list[asyncio.Future]) -> None:
    """Await multiple coroutines/futures in parallel."""
    await asyncio.gather(*tasks, return_exceptions=True)

@router.post(path="/")
async def subdomain_search(
    req: DomainInput,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),
    ) -> dict:
    
    crtsh_service = CrtshService()
    virus_total_service = VirusTotalService()
    shodan_service = ShodanService()
    otx_service = OtxService()
    sec = Security()
    if not sec.is_valid_domain(req.domain):
        raise HTTPException(status_code=400, detail=f"invalid domain: {req.domain}")
        
    try:
        # cleanup expired requests
        try:
            db.query(DomainRequested).filter(DomainRequested.time_to_zero <= datetime.now()).delete()
            db.commit()
        except Exception:
            db.rollback()

        # block if same domain already requested and not expired
        existing = db.query(DomainRequested).filter(
            DomainRequested.domain == req.domain,
            DomainRequested.time_to_zero > datetime.now()
        ).first()
        if existing:
            raise HTTPException(status_code=429, detail=f"scan already scheduled until {existing.time_to_zero}")

        # insert a lock row and mark as scheduled to prevent duplicate/manual scans
        try:
            lock = DomainRequested(domain=req.domain, scheduled=True)
            db.add(lock)
            db.commit()
            # register a daily scheduled job for this domain (idempotent)
            try:
                add_daily_job(req.domain)
            except Exception as e:
                app_logger.error(f"failed to schedule daily job for {req.domain}: {e}")
        except Exception:
            db.rollback()
        # prepare async tasks that run blocking service calls in the default threadpool
        # NOTE: do NOT pass the request-scoped `db` into background tasks — it will be closed.

        def run_crtsh(domain: str):
            app_logger.info(f"task: crtsh start {domain}")
            db_local = SessionLocal()
            try:
                crtsh_service.recursive_search(db_local, domain)
                app_logger.info(f"task: crtsh finished {domain}")
            except Exception as e:
                app_logger.error(f"task: crtsh error {domain}: {e}")
            finally:
                db_local.close()

        def run_otx(domain: str):
            app_logger.info(f"task: otx start {domain}")
            db_local = SessionLocal()
            try:
                otx_service.extract_and_store_data(db_local, domain)
                app_logger.info(f"task: otx finished {domain}")
            except Exception as e:
                app_logger.error(f"task: otx error {domain}: {e}")
            finally:
                db_local.close()

        def run_shodan(domain: str):
            app_logger.info(f"task: shodan start {domain}")
            db_local = SessionLocal()
            try:
                shodan_service.extract_and_store_subdomains_data(db_local, domain)
                app_logger.info(f"task: shodan finished {domain}")
            except Exception as e:
                app_logger.error(f"task: shodan error {domain}: {e}")
            finally:
                db_local.close()

        def run_virustotal(domain: str):
            app_logger.info(f"task: virustotal start {domain}")
            db_local = SessionLocal()
            try:
                virus_total_service.search_subdomains(db_local, domain)
                app_logger.info(f"task: virustotal finished {domain}")
            except Exception as e:
                app_logger.error(f"task: virustotal error {domain}: {e}")
            finally:
                db_local.close()

        tasks = [
            asyncio.to_thread(run_crtsh, req.domain),
            asyncio.to_thread(run_otx, req.domain),
            asyncio.to_thread(run_shodan, req.domain),
            asyncio.to_thread(run_virustotal, req.domain),
        ]

        app_logger.info(f"scheduling background tasks for {req.domain}")
        # schedule the concurrent execution of tasks in the background
        background_task.add_task(concurrent_tasks, tasks)

        return {"status": f'scan initiated for domain {req.domain}'}
    except HTTPException:
        # re-raise HTTPExceptions so FastAPI can handle them (429 for duplicates)
        raise
    except Exception as e:
        app_logger.error(f"error in post req: {e}")
        # return HTTP 500 with error detail instead of returning None
        raise HTTPException(status_code=500, detail=str(e))