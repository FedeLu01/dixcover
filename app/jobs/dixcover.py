from fastapi import FastAPI, APIRouter, Depends
from app.services.database import get_db
from app.models.crtsh_subdomain import Subdomain
from sqlalchemy.orm import Session
from app.services.passive_scanner import PassiveScanner
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.config.settings import settings

# Este job debe hacer el trabajo de escanear pasivamente los dominios, todos los dias, para ir detectando cambios o novedades.

def store_subdomains(domain: str):
    db = next(get_db())
    all_subdomains_data = PassiveScanner(
        domain=domain,
        shodan_api_key=settings.SHODAN_API_KEY,
        vt_api_key=settings.VIRUS_TOTAL_API_KEY,
    ).get_subdomains_from_certificates()
    
    for subdomain in all_subdomains_data:
        try:
            #subdomain['detected_at'] = datetime.now()
            new_subdomain = Subdomain(**subdomain)
            db.add(new_subdomain)
            db.commit()
            db.refresh(new_subdomain)
            #db.insert_data(subdomain=subdomain['subdomain'], registered_on=subdomain['registered_on'], detected_at=datetime.now())
        except IntegrityError as e:
            db.rollback()
            print(f"Subdomain {subdomain['subdomain']} already exists in the database.")