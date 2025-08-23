from fastapi import APIRouter, Depends, BackgroundTasks, Response
from sqlalchemy.orm import Session
from app.services.database import get_db
from app.schemas.domainInput import DomainInput
from app.utils.log import app_logger
from app.services.crtsh_service import CrtshService
from app.services.virus_total_service import VirusTotalService
from app.services.shodan_service import ShodanService

router = APIRouter(tags=["crtsh_query"])

# TODO: tengo que resolver para que la busqueda sea async asi no dejo la response colgada
# TODO: si hago esto voy a tener que marcar un status del escaneo (puede ser en la db??)

@router.post(path="/")
def handle_recursive_search(
    req: DomainInput,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Controlador para buscar subdominios de un dominio específico.
    """
    crtsh_service = CrtshService()
    virus_total_service = VirusTotalService()
    shodan_service = ShodanService()
    try:
        background_task.add_task(crtsh_service.recursive_search, db=db, domain=req.domain)
        background_task.add_task(virus_total_service.recursive_search, db=db, domain=req.domain)
        background_task.add_task(shodan_service.extract_and_store_subdomains_data, db=db, target_domain=req.domain)
        return {"status":f'scan initiated for domain {req.domain}'}
    except Exception as e:
        app_logger.info(f"error in post req: {e}")