from app.clients.shodan_client import ShodanClient
from app.models.shodan_subdomain import ShodanSubdomain
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger
from app.services.base_subdomain_service import BaseSubdomainService


class ShodanService(BaseSubdomainService):
    def __init__(self, max_depth=5, delay=5, max_workers=8):
        super().__init__(max_depth, delay, max_workers)
        self.shodan = ShodanClient()
        
    def extract_and_store_subdomains_data(self, db: Session, target_domain):        
        data = self.shodan.search_domain(target_domain)    
        subdomains = set()

        try:
            for sub in data: 
                if "*" in sub:
                    continue 
                full_subdomain = f"{sub}.{target_domain}"
                if self.is_valid_subdomain(full_subdomain, target_domain):
                    subdomains.add(f"{sub}.{target_domain}") 
                    to_store = {
                        "subdomain": f"{sub}.{target_domain}",
                    }
                    self.store(db, to_store)
        except Exception as e:
            app_logger.error(f"error extracting and storing {e}")
            
        return subdomains


    def store(self, db: Session, data: dict):
        new_subdomain = ShodanSubdomain(**data)
        try:
            db.add(new_subdomain)
            db.commit()
            db.refresh(new_subdomain)
        except IntegrityError as e:
            app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
