from app.clients.virus_total_client import VirusTotalClient
from app.models.virus_total_subdomain import VirusTotalSubdomain
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger
from app.services.base_subdomain_service import BaseSubdomainService
import time
import concurrent.futures


class VirusTotalService(BaseSubdomainService):
    def __init__(self, max_depth=5, delay=5, max_workers=8):
        super().__init__(max_depth, delay, max_workers)

    def extract_subdomains_data(self, data, target_domain, db: Session):
        subdomains = set()
        raw_subdomains = data['data']
        try:
            for sub in raw_subdomains:
                if sub['type'] == 'domain':
                    subdomain = sub['id']
                    if self._is_valid_subdomain(subdomain, target_domain):
                        subdomains.add(subdomain)
                        to_store = {
                            "subdomain": subdomain,
                        }
                        self.store_subdomains_data(db, to_store)
        except Exception as e:
            app_logger.error(f"error extracting and storing {e}")
        return subdomains

    def recursive_search(self, db: Session, domain, current_depth=0):
        virus_total_client = VirusTotalClient()
        with self.lock:
            if domain in self.processed_domains:
                return set()
            self.processed_domains.add(domain)

        app_logger.info(f"{'  ' * current_depth}Buscando: {domain} (profundidad: {current_depth})")
        data = virus_total_client.search_domain(domain)
        if not data:
            return set()

        new_subdomains = self.extract_subdomains_data(data, domain, db)

        with self.lock:
            before_count = len(self.found_subdomains)
            self.found_subdomains.update(new_subdomains)
            new_count = len(self.found_subdomains) - before_count

        app_logger.info(f"{'  ' * current_depth}Encontrados {len(new_subdomains)} subdominios para {domain} ({new_count} nuevos)")

        if current_depth >= self.max_depth:
            return new_subdomains

        domains_to_search = [s for s in new_subdomains if s not in self.processed_domains]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_domain = {}
            if not domains_to_search:
                return
            for subdomain in domains_to_search:
                if not isinstance(subdomain, str):
                    app_logger.warning(f"incorrect value for subdomain: {subdomain}")
                    continue
                time.sleep(self.delay)
                future = executor.submit(self.recursive_search, db, subdomain, current_depth + 1)
                future_to_domain[future] = subdomain
            for future in concurrent.futures.as_completed(future_to_domain):
                try:
                    future.result()
                except Exception as e:
                    app_logger.debug(f"error gathering results: {e}")
        return new_subdomains

    def store_subdomains_data(self, db: Session, data: dict):
        new_subdomain = VirusTotalSubdomain(**data)
        try:
            db.add(new_subdomain)
            db.commit()
            db.refresh(new_subdomain)
        except IntegrityError as e:
            app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
