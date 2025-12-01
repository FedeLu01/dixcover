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

import asyncio

router = APIRouter(tags=["Subdomains_Gathering"])
security = Security()
# TODO: si hago esto voy a tener que marcar un status del escaneo (puede ser en la db??)

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
        tasks = [
            asyncio.to_thread(crtsh_service.recursive_search, db, req.domain),
            asyncio.to_thread(otx_service.extract_and_store_data, db, req.domain),
            asyncio.to_thread(shodan_service.extract_and_store_subdomains_data, db, req.domain),
            asyncio.to_thread(virus_total_service.search_subdomains, db, req.domain),
        ]
        
        # schedule the concurrent execution of tasks in the background
        background_task.add_task(concurrent_tasks, tasks)
        
        return {"status":f'scan initiated for domain {req.domain}'}
    except Exception as e:
        app_logger.info(f"error in post req: {e}")