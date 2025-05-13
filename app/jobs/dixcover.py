from fastapi import FastAPI, APIRouter
from app.config.config import Config
from app.services.database import DatabaseManager
from app.services.passive_scanner import PassiveScanner
from datetime import datetime

# Este job debe hacer el trabajo de escanear pasivamente los dominios, todos los dias, para ir detectando cambios o novedades.
# TODO: Para solucionar el problema de la conexion con la DB, debo crear un pool con DBUtils 

def store_subdomains(domain: str):
    db = DatabaseManager()
    try:
        all_subdomains_data = PassiveScanner(domain).get_subdomains_from_certificates()
        for subdomain in all_subdomains_data:
            db.insert_data(subdomain=subdomain['subdomain'], registered_on=subdomain['registered_on'], detected_at=datetime.now())
        return True
    except Exception as e:
        print(f"Error storing subdomains: {e}")
        return False