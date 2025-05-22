import requests
import json
import time
import re

from app.utils.log import app_logger
from urllib.parse import urlparse
from typing import Set, List, Dict
import concurrent.futures
from threading import Lock

class CrtShSubdomainFinder:
    def __init__(self, max_depth=3, delay=1.0, max_workers=5):
        self.base_url = "https://crt.sh/"
        self.max_depth = max_depth
        self.delay = delay
        self.max_workers = max_workers
        self.found_subdomains = set()
        self.processed_domains = set()
        self.lock = Lock()
        
    def search_domain(self, domain):
        """Buscar certificados para un dominio específico"""
        try:
            params = {
                'q': f'%.{domain}',
                'output': 'json'
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # crt.sh a veces devuelve HTML en lugar de JSON en caso de error
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                print(f"Respuesta no JSON para {domain}")
                return []
                
        except requests.exceptions.RequestException as e:
            app_logger.error(f"error requesting subdomain: {e}")
            return []
        except json.JSONDecodeError as e:
            app_logger.error(f"error decoding json: {e}")
            return []

    def extract_subdomains(self, certificates, target_domain):
        """Extraer subdominios únicos de los certificados"""
        subdomains = set()
        
        for cert in certificates:
            # Extraer del campo 'name_value' que contiene los SANs
            if 'name_value' in cert:
                names = cert['name_value'].split('\n')
                for name in names:
                    name = name.strip().lower()
                    
                    # Filtrar solo subdominios válidos del dominio objetivo
                    if self.is_valid_subdomain(name, target_domain):
                        subdomains.add(name)
                        
            # También extraer del campo 'common_name' si existe
            if 'common_name' in cert:
                name = cert['common_name'].strip().lower()
                if self.is_valid_subdomain(name, target_domain):
                    subdomains.add(name)
                    
        return subdomains

    def is_valid_subdomain(self, name, target_domain):
        """Verificar si es un subdominio válido"""
        # Remover wildcards
        name = name.replace('*.', '')
        
        # Verificar que termine con el dominio objetivo
        if not name.endswith(f'.{target_domain}') and name != target_domain:
            return False
            
        # Verificar formato de dominio válido
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        
        return bool(domain_pattern.match(name))

    def recursive_search(self, domain, current_depth=0):
        """Búsqueda recursiva de subdominios"""
        with self.lock:
            # Evitar procesar el mismo dominio múltiples veces
            if domain in self.processed_domains:
                return set()
            self.processed_domains.add(domain)
        
        print(f"{'  ' * current_depth}Buscando: {domain} (profundidad: {current_depth})")
        
        # Buscar certificados para este dominio
        certificates = self.search_domain(domain)
        
        if not certificates:
            return set()
            
        # Extraer subdominios de los certificados
        new_subdomains = self.extract_subdomains(certificates, domain)
        
        with self.lock:
            # Agregar nuevos subdominios encontrados
            before_count = len(self.found_subdomains)
            self.found_subdomains.update(new_subdomains)
            new_count = len(self.found_subdomains) - before_count
            
        print(f"{'  ' * current_depth}Encontrados {len(new_subdomains)} subdominios para {domain} ({new_count} nuevos)")
        
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
            
            for subdomain in domains_to_search:
                # Agregar delay para evitar rate limiting
                time.sleep(self.delay)
                future = executor.submit(self.recursive_search, subdomain, current_depth + 1)
                future_to_domain[future] = subdomain
            
            # Recopilar resultados
            for future in concurrent.futures.as_completed(future_to_domain):
                try:
                    future.result()
                except Exception as e:
                    domain = future_to_domain[future]
                    print(f"Error procesando {domain}: {e}")
        
        return new_subdomains

    def search_all_subdomains(self, target_domain):
        """Iniciar búsqueda recursiva de subdominios"""
        print(f"Iniciando búsqueda recursiva para: {target_domain}")
        print(f"Profundidad máxima: {self.max_depth}")
        print(f"Delay entre requests: {self.delay}s")
        print("-" * 50)
        
        # Limpiar estado anterior
        self.found_subdomains.clear()
        self.processed_domains.clear()
        
        # Comenzar búsqueda recursiva
        start_time = time.time()
        self.recursive_search(target_domain)
        end_time = time.time()
        
        print("-" * 50)
        print(f"Búsqueda completada en {end_time - start_time:.2f} segundos")
        print(f"Total de subdominios encontrados: {len(self.found_subdomains)}")
        
        return sorted(list(self.found_subdomains))

    def save_results(self, subdomains, filename):
        """Guardar resultados en archivo"""
        try:
            with open(filename, 'w') as f:
                for subdomain in sorted(subdomains):
                    f.write(f"{subdomain}\n")
            print(f"Resultados guardados en: {filename}")
        except IOError as e:
            print(f"Error guardando archivo: {e}")

    def get_certificate_details(self, domain):
        """Obtener detalles de certificados para un dominio"""
        certificates = self.search_domain(domain)
        
        details = []
        for cert in certificates:
            details.append({
                'id': cert.get('id'),
                'issuer_name': cert.get('issuer_name'),
                'not_before': cert.get('not_before'),
                'not_after': cert.get('not_after'),
                'common_name': cert.get('common_name'),
                'name_value': cert.get('name_value')
            })
            
        return details


# Clase para análisis más detallado
class CrtShAnalyzer(CrtShSubdomainFinder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.certificate_stats = {}
    
    def analyze_certificates(self, domain):
        """Analizar certificados y generar estadísticas"""
        certificates = self.search_domain(domain)
        
        if not certificates:
            return {}
            
        stats = {
            'total_certificates': len(certificates),
            'unique_issuers': set(),
            'common_names': set(),
            'earliest_date': None,
            'latest_date': None,
            'subdomains_count': 0
        }
        
        for cert in certificates:
            # Recopilar emisores
            if cert.get('issuer_name'):
                issuer = cert['issuer_name'].split('=')[-1]  # Extraer nombre del emisor
                stats['unique_issuers'].add(issuer)
            
            # Recopilar common names
            if cert.get('common_name'):
                stats['common_names'].add(cert['common_name'])
                
            # Fechas
            if cert.get('not_before'):
                date = cert['not_before']
                if not stats['earliest_date'] or date < stats['earliest_date']:
                    stats['earliest_date'] = date
                    
            if cert.get('not_after'):
                date = cert['not_after']
                if not stats['latest_date'] or date > stats['latest_date']:
                    stats['latest_date'] = date
        
        # Convertir sets a lists para JSON serialization
        stats['unique_issuers'] = list(stats['unique_issuers'])
        stats['common_names'] = list(stats['common_names'])
        stats['unique_issuers_count'] = len(stats['unique_issuers'])
        
        return stats


# Ejemplo de uso
def main():
    # Crear instancia del buscador
    finder = CrtShSubdomainFinder(
        max_depth=5,  # Profundidad de recursión
        delay=3.5,    # Segundo entre requests
        max_workers=8  # Threads concurrentes
    )
    
    # Dominio objetivo
    target_domain = "compragamer.com"
    
    # Buscar subdominios recursivamente
    subdomains = finder.search_all_subdomains(target_domain)
    
    # Mostrar resultados
    print("\nSubdominios encontrados:")
    for subdomain in subdomains:
        print(f"  - {subdomain}")
    
    # Guardar en archivo
    finder.save_results(subdomains, f"{target_domain}_subdomains.txt")
    
    # Análisis detallado (opcional)
    analyzer = CrtShAnalyzer()
    stats = analyzer.analyze_certificates(target_domain)
    
    print(f"\nEstadísticas de certificados para {target_domain}:")
    print(f"  Total de certificados: {stats.get('total_certificates', 0)}")
    print(f"  Emisores únicos: {stats.get('unique_issuers_count', 0)}")
    print(f"  Primera fecha: {stats.get('earliest_date', 'N/A')}")
    print(f"  Última fecha: {stats.get('latest_date', 'N/A')}")


if __name__ == "__main__":
    main()