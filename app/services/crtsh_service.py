from app.clients.crtsh_client import CrtshClient
from datetime import datetime
from app.models.crtsh_subdomain import CrtshSubdomain
from sqlalchemy.orm import Session
from app.services.base_subdomain_service import BaseSubdomainService
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger

import concurrent.futures

# TODO: tengo que handlear el error {"timestamp": "2025-05-23T20:08:57.780432", "level": "ERROR", "message": 
# TODO: "error requesting subdomain: 429 Client Error: Too Many Requests for url: https://crt.sh/?q=spa.galicia.ar&output=json"}


class CrtshService(BaseSubdomainService):
    def __init__(self, max_depth=5, delay=5, max_workers=5):
        super().__init__(max_depth, delay, max_workers)
    
    def _extract_subdomains_data(self, certificates, target_domain, db: Session):
        """ extract unique subdomains from crtsh certificates data and store them in the db """
        subdomains = set()
        
        for cert in certificates:
            if 'name_value' in cert:
                names = cert['name_value'].split('\n')
                for name in names:
                    name = name.replace('*.', '').strip().lower() # duplicate logic to clean, i don't like it but ok
                    
                    # filter valid subdomains with the conditions of unique and no wildcard
                    if self.is_valid_subdomain(name, target_domain):
                        subdomains.add(name)
                        data = {
                            'subdomain': name,
                            'registered_on': str(cert['not_before']),
                            'expires_on': str(cert['not_after']),
                            }
                        self._store_subdomains_data(db, data)
                        
            if 'common_name' in cert:
                name = cert['common_name'].replace('*.', '').strip().lower().split('\n')[0]
                if self.is_valid_subdomain(name, target_domain):
                    subdomains.add(name)
                    data = {
                            'subdomain': name,
                            'registered_on': str(cert['not_before']),
                            'expires_on': str(cert['not_after']),
                            }
                    self._store_subdomains_data(db, data) 
                    
        return subdomains
    
    def recursive_search(self, db: Session, domain, current_depth=0):
        """Recursive search for subdomains"""
        crtsh_client = CrtshClient()
        with self.lock:
            # Avoid processing the same domain multiple times
            if domain in self.processed_domains:
                return set()
            
            self.processed_domains.add(domain)
        
        app_logger.info(f"{'  ' * current_depth}Looking: {domain} (depth: {current_depth})")
        
        # Search certificates for this domain
        certificates = crtsh_client.search_domain(domain)
        
        if not certificates:
            return set()
            
        # Extract subdomains from certificates
        new_subdomains = self._extract_subdomains_data(certificates, domain, db)
        
        
        with self.lock:
            # Add new subdomains found
            before_count = len(self.found_subdomains)
            self.found_subdomains.update(new_subdomains)
            new_count = len(self.found_subdomains) - before_count
            
        app_logger.info(f"{'  ' * current_depth}Found {len(new_subdomains)} subdomains for {domain} ({new_count} new)")
        
        # If we've reached the maximum depth, do not continue
        if current_depth >= self.max_depth:
            return new_subdomains
            
        # Recursively search in the new subdomains found
        domains_to_search = []
        for subdomain in new_subdomains:
            if subdomain not in self.processed_domains:
                domains_to_search.append(subdomain)
        
        # Use threading for parallel searches
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_domain = {}
            
            if not domains_to_search:
                return
            
            for subdomain in domains_to_search:
                if not isinstance(subdomain, str):
                    app_logger.warning(f"incorrect value for subdomain: {subdomain}")
                    continue
                
                future = executor.submit(self.recursive_search, db, subdomain, current_depth + 1)
                future_to_domain[future] = subdomain
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_domain):
                try:
                    future.result()
                except Exception as e:
                    app_logger.debug(f"error gathering results: {e}")
                    domain = future_to_domain[future]
        
        return new_subdomains

    def _store_subdomains_data(self, db: Session, data: dict):
        """ Store subdomains in the database """
        new_subdomain = CrtshSubdomain(**data)
        try:
            # app_logger.debug(f"subdomain object: {new_subdomain}")
            db.add(new_subdomain)
            db.commit()
            db.refresh(new_subdomain)
        except IntegrityError as e:
            app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
        