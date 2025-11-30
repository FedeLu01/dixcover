from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.clients.virus_total_client import VirusTotalClient
from app.models.virus_total_subdomain import VirusTotalSubdomain
from app.utils.log import app_logger
from app.services.base_subdomain_service import BaseSubdomainService

import math
import time


class VirusTotalService(BaseSubdomainService):
    def __init__(self, delay=1):
        super().__init__(delay)

    def extract_subdomains_data(self, data, target_domain, db: Session):
        subdomains = set()
        raw_subdomains = data['data']
        try:
            for sub in raw_subdomains:
                if sub['type'] == 'domain':
                    subdomain = sub['id']
                    if self.is_valid_subdomain(subdomain, target_domain):
                        subdomains.add(subdomain)
                        to_store = {
                            "subdomain": subdomain,
                        }
                        self.store_subdomains_data(db, to_store)
        except Exception as e:
            app_logger.error(f"error extracting and storing {e}")
        return subdomains

    def search_subdomains(self, db: Session, domain):
        virus_total_client = VirusTotalClient()
        all_subdomains = set()
        next_url = None
        pages = 0
        MAX_PAGES = 0
        
        while True:
            if pages > MAX_PAGES:
                app_logger.warning(f"reached max pages ({MAX_PAGES}) for domain {domain}")
                break

            # prefer following the full `links.next` URL returned by VirusTotal when available
            data = virus_total_client.search_domain(domain, next_url=next_url)
            
            # metadata to create max pages to request
            MAX_PAGES = math.ceil(data.get('meta', {}).get('count', 0) / 40)
            
            if not data:
                break

            # extract and store subdomains from this page
            try:
                page_subs = self.extract_subdomains_data(data, domain, db)
                all_subdomains.update(page_subs)
            except Exception as e:
                app_logger.error(f"error processing page {pages} for {domain}: {e}")

            # prefer the `next` link (includes both limit and cursor) if VirusTotal provides it
            links = data.get('links', {}) if isinstance(data, dict) else {}
            next_link = links.get('next')

            if next_link:
                # set next_url to the absolute URL
                next_url = next_link

            # if no next_url, no more pages
            if not next_url:
                break

            # polite delay between paged requests
            time.sleep(self.delay)
            
            pages += 1
            
        return all_subdomains
                            

    def store_subdomains_data(self, db: Session, data: dict):
        new_subdomain = VirusTotalSubdomain(**data)
        try:
            db.add(new_subdomain)
            db.commit()
            db.refresh(new_subdomain)
        except IntegrityError as e:
            app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
