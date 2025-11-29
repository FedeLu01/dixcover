from fastapi import Depends, APIRouter, Request
from sqlalchemy.orm import Session
from app.services.database import get_db
from app.services.crtsh_service import CrtshService

router = APIRouter(tags=["crtsh_query"])

#@router.post("/")
def handle_recursive_search(domain: str):
    """
    Controlador para buscar subdominios de un dominio específico.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        return CrtshService().recursive_search(db, domain)
    finally:
        db_gen.close()
