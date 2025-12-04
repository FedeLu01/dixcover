from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.services.database import get_db
from app.schemas.domainInput import DomainInput
from app.utils.log import app_logger
from app.middleware.security import Security
from app.services.crtsh_service import CrtshService
from app.services.virus_total_service import VirusTotalService
from app.services.shodan_service import ShodanService
from app.services.otx_service import OtxService
from app.services.database import SessionLocal

import asyncio

router = APIRouter(tags=["Subdomains_Gathering"])
security = Security()
# TODO: i have to set a status of the scan to not permit concurrent scans for the same domain

async def concurrent_tasks(tasks: list[asyncio.Future]) -> None:
    """Await multiple coroutines/futures in parallel."""
    await asyncio.gather(*tasks, return_exceptions=True)

@router.post(path="/")
async def subdomain_search(
    req: DomainInput,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),
    ) -> dict:
    """
    
    """
    crtsh_service = CrtshService()
    virus_total_service = VirusTotalService()
    shodan_service = ShodanService()
    otx_service = OtxService()
    
    # Con esto valido ligeramente el input del usuario, al menos, para que sea una url (y tambien le saco el scheme y URI para que no rompa).
    # hostname = security.is_valid_domain(req.domain) TODO: no me esta devolviendo el output esperado (debe ser porque estoy devolviendo el netloc y en realidad puede entrar como input el netloc directamente, por ej: "galicia.ar").
    
    try:
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
            #asyncio.to_thread(run_otx, req.domain),
            #asyncio.to_thread(run_shodan, req.domain),
            #asyncio.to_thread(run_virustotal, req.domain),
        ]

        app_logger.info(f"scheduling background tasks for {req.domain}")
        # schedule the concurrent execution of tasks in the background
        background_task.add_task(concurrent_tasks, tasks)

        return {"status": f'scan initiated for domain {req.domain}'}
    except Exception as e:
        app_logger.error(f"error in post req: {e}")