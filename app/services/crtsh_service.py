from app.clients.crtsh_client import CrtshClient
from datetime import datetime
from app.models.crtsh_subdomain import CrtshSubdomain
from sqlalchemy.orm import Session
from app.services.base_subdomain_service import BaseSubdomainService
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger

import time
import concurrent.futures

# TODO: tengo que handlear el error {"timestamp": "2025-05-23T20:08:57.780432", "level": "ERROR", "message": 
# TODO: "error requesting subdomain: 429 Client Error: Too Many Requests for url: https://crt.sh/?q=spa.galicia.ar&output=json"}


class CrtshService(BaseSubdomainService):
    def __init__(self, max_depth=5, delay=5, max_workers=8):
        super().__init__(max_depth, delay, max_workers)
    
    def extract_subdomains_data(self, certificates, target_domain, db: Session):
        """ Extraer subdominios unicos de los certificados """
        subdomains = set()
        
        for cert in certificates:
            # name_value = subdomain
            if 'name_value' in cert:
                names = cert['name_value'].split('\n')
                for name in names:
                    name = name.strip().lower()
                    
                    # filtrar por validos (no tiene que ser repetido ni tener wildcard)
                    if self._is_valid_subdomain(name, target_domain):
                        subdomains.add(name)
                        data = {
                            'subdomain': name,
                            'detected_at': str(datetime.now()),
                            'registered_on': str(cert['not_before']),
                            'expires_on': str(cert['not_after']),
                            }
                        self.store_subdomains_data(db, data)
                        
            # common_name = subdomain
            if 'common_name' in cert:
                name = cert['common_name'].strip().lower()
                if self._is_valid_subdomain(name, target_domain):
                    subdomains.add(name)
                    data = {
                            'subdomain': name,
                            'detected_at': str(datetime.now()),
                            'registered_on': str(cert['not_before']),
                            'expires_on': str(cert['not_after']),
                            }
                    self.store_subdomains_data(db, data) 
                    
        return subdomains
    
    def recursive_search(self, db: Session, domain, current_depth=0):
        """Búsqueda recursiva de subdominios"""
        crtsh_client = CrtshClient()
        with self.lock:
            # Evitar procesar el mismo dominio múltiples veces
            if domain in self.processed_domains:
                return set()
            
            self.processed_domains.add(domain)
        
        app_logger.info(f"{'  ' * current_depth}Buscando: {domain} (profundidad: {current_depth})")
        
        # Buscar certificados para este dominio
        certificates = crtsh_client.search_domain(domain)
        
        if not certificates:
            return set()
            
        # Extraer subdominios de los certificados
        new_subdomains = self.extract_subdomains_data(certificates, domain, db)
        
        
        with self.lock:
            # Agregar nuevos subdominios encontrados
            before_count = len(self.found_subdomains)
            self.found_subdomains.update(new_subdomains)
            new_count = len(self.found_subdomains) - before_count
            
        app_logger.info(f"{'  ' * current_depth}Encontrados {len(new_subdomains)} subdominios para {domain} ({new_count} nuevos)")
        
        # Si hemos alcanzado la profundidad máxima, no continuar
        if current_depth >= self.max_depth:
            return new_subdomains
            
        # Buscar recursivamente en los nuevos subdominios encontrados
        domains_to_search = []
        for subdomain in new_subdomains:
            if subdomain not in self.processed_domains:
                domains_to_search.append(subdomain)
        
        # Usar threading para búsquedas paralelas
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_domain = {}
            
            if not domains_to_search:
                return
            
            for subdomain in domains_to_search:
                if not isinstance(subdomain, str):
                    app_logger.warning(f"incorrect value for subdomain: {subdomain}")
                    continue
                # Agregar delay para evitar rate limiting
                time.sleep(self.delay)
                future = executor.submit(self.recursive_search, db, subdomain, current_depth + 1)
                future_to_domain[future] = subdomain
            
            # Recopilar resultados
            for future in concurrent.futures.as_completed(future_to_domain):
                try:
                    future.result()
                except Exception as e:
                    app_logger.debug(f"error gathering results: {e}")
                    domain = future_to_domain[future]
        
        return new_subdomains

    def store_subdomains_data(self, db: Session, data: dict):
        """ Almacenar subdominios en la base de datos """
        new_subdomain = CrtshSubdomain(**data)
        try:
            # app_logger.debug(f"subdomain object: {new_subdomain}")
            db.add(new_subdomain)
            db.commit()
            db.refresh(new_subdomain)
        except IntegrityError as e:
            app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
        