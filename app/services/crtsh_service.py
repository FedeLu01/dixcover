from app.clients.crtsh_client import CrtshClient
from datetime import datetime
from urllib.parse import urlparse
from typing import Set, List, Dict
from threading import Lock
from app.models.crtsh_subdomain import CrtshSubdomain
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger

import json
import time
import re
import concurrent.futures


class CrtshService:
    def __init__(self, max_depth=5, delay=5, max_workers=5):
        self.max_depth = max_depth
        self.delay = delay
        self.max_workers = max_workers
        self.found_subdomains = set()
        self.processed_domains = set()
        self.lock = Lock()
        
    def _is_valid_subdomain(self, name, target_domain):
        """ Verificar si es un subdominio válido """
        # Remover wildcards
        name = name.replace('*.', '')
        
        # Verificar que termine con el dominio objetivo
        if not name.endswith(f'{target_domain}') and name != target_domain:
            return False
            
        # Verificar formato de dominio válido
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        
        if not bool(domain_pattern.match(name)):
            app_logger.debug(f'invalid domain: {name}')
            
        
        return bool(domain_pattern.match(name))
    
    def extract_subdomains_data(self, certificates, target_domain, db: Session):
        """ Extraer subdominios unicos de los certificados """
        subdomains = set()
        
        for cert in certificates:
            # Extraer del campo 'name_value' que contiene los SANs
            if 'name_value' in cert:
                names = cert['name_value'].split('\n')
                for name in names:
                    name = name.strip().lower()
                    
                    # Filtrar solo subdominios válidos del dominio objetivo
                    if self._is_valid_subdomain(name, target_domain):
                        subdomains.add(name)
                        data = {
                            'subdomain': name,
                            'detected_at': str(datetime.now()),
                            'registered_on': str(cert['not_before']),
                            'expires_on': str(cert['not_after']),
                            }
                        self.store_subdomains_data(db, data)
                        
            # También extraer del campo 'common_name' si existe
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
            # app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
        