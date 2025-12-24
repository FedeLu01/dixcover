from app.clients.crtsh_client import CrtshClient
from app.models.crtsh_subdomain import CrtshSubdomain
from sqlalchemy.orm import Session
from app.services.base_subdomain_service import BaseSubdomainService
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger
from app.models.subdomains_master import MasterSubdomains
from sqlmodel import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

import concurrent.futures
import time
class CrtshService(BaseSubdomainService):
    def __init__(self, max_depth=3, delay=5, max_workers=2):
        super().__init__(max_depth, delay, max_workers)
    
    def _extract_subdomains_data(self, certificates, target_domain, db: Session):
        """ extract unique subdomains from crtsh certificates data and store them in the db """
        subdomains = set()
        app_logger.debug(f"Crtsh: extracting from {len(certificates) if certificates else 0} certificates for {target_domain}")
        
        for cert in certificates:
            if 'name_value' in cert:
                names = cert['name_value'].split('\n')
                for name in names:
                    name = name.replace('*.', '').strip().lower() # duplicate logic to clean, i don't like it but ok
                    
                    # filter valid subdomains with the conditions of unique and no wildcard
                    if self.is_valid_subdomain(name, target_domain):
                        app_logger.debug(f"Crtsh: found valid subdomain {name}")
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
                    app_logger.debug(f"Crtsh: found valid common_name {name}")
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
        # polite delay to avoid hitting crt.sh rate limits
        try:
            app_logger.debug(f"Crtsh: sleeping {self.delay}s to avoid rate limit")
            time.sleep(self.delay)
        except Exception:
            pass
        app_logger.debug(f"Crtsh: retrieved {len(certificates) if certificates else 0} certificates for {domain}")
        
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
        try:
            app_logger.debug(f"Crtsh: upserting {data.get('subdomain')}")
            table = CrtshSubdomain.__table__
            insert_stmt = pg_insert(table).values(data)
            update_stmt = {k: insert_stmt.excluded[k] for k in data.keys() if k != 'subdomain'}
            if update_stmt:
                stmt = insert_stmt.on_conflict_do_update(index_elements=['subdomain'], set_=update_stmt)
            else:
                stmt = insert_stmt.on_conflict_do_nothing(index_elements=['subdomain'])
            db.execute(stmt)
            db.commit()

            # Upsert into master table in Python so we can merge sources properly
            try:
                stmt = select(MasterSubdomains).where(MasterSubdomains.subdomain == data.get('subdomain'))
                master_obj = db.execute(stmt).scalars().one_or_none()
                incoming_first = data.get('first_seen') or data.get('detected_at')
                if master_obj is None:
                    master_obj = MasterSubdomains(
                        subdomain=data.get('subdomain'),
                        sources=['crtsh'],
                        first_seen=incoming_first,
                    )
                    db.add(master_obj)
                else:
                    # merge sources
                    if 'crtsh' not in (master_obj.sources or []):
                        master_obj.sources = (master_obj.sources or []) + ['crtsh']
                    # update first_seen to the earliest
                    if incoming_first:
                        try:
                            if master_obj.first_seen is None or incoming_first < master_obj.first_seen:
                                master_obj.first_seen = incoming_first
                        except Exception:
                            pass
                    db.add(master_obj)
                db.commit()
            except Exception:
                db.rollback()
        except IntegrityError:
            db.rollback()
        except Exception as e:
            db.rollback()
            app_logger.error(f'error upserting crtsh rows: {e}')