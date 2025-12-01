from app.clients.otx_client import OtxClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.otx_subdomains import OtxSubdomain
from app.utils.log import app_logger
from app.config.settings import settings
from app.services.base_subdomain_service import BaseSubdomainService

# TODO: estoy teniendo error: error extracting and storing: list indices must be integers or slices, not str

class OtxService(BaseSubdomainService):
    def __init__(self):
        super().__init__()
        self.otx_client = OtxClient(settings.OTX_API_KEY)
        
    def extract_and_store_data(self, db: Session, target_domain):
        data = self.otx_client.get_subdomains(target_domain)
        try: 
            if data:
                for block in data:
                    if self.is_valid_subdomain(block["hostname"], target_domain):
                        to_store = {
                            "address": f"{block['address']}",
                            "subdomain": f"{block['hostname']}"
                        }
                        self.store(db, to_store)
            else:
                app_logger.info(f'no data found for domain {target_domain} in OTX')
                
        except Exception as e:
            app_logger.error(f'error extracting and storing: {e}')
            
    def store(self, db: Session, data: dict):
        new_subdomain = OtxSubdomain(**data)
        try:
            db.add(new_subdomain)
            db.commit()
            db.refresh(new_subdomain)
        except IntegrityError as e:
            db.rollback()
            app_logger.debug(f'error in insert: {str(e)}')
        