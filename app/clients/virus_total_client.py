import requests
import json

from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.exceptions.exceptions import ExternalAPIError
from app.utils.log import app_logger
from app.config.settings import settings


class VirusTotalClient:
    def __init__(self):
        self.base_url = "https://www.virustotal.com"
        self.api_key = settings.VIRUS_TOTAL_API_KEY
        self.headers = {
            "x-apikey": self.api_key,
            "accept": "application/json"
            }

    
    @retry(
    stop=stop_after_attempt(4), # max number of retries
    wait=wait_exponential(multiplier=4, min=4, max=5) # exponential backoff
    )
    def search_domain(self, domain):
        """ Buscar certificados para un dominio específico """
        try:
            
            response = requests.get(f"{self.base_url}/api/v3/domains/{domain}/relationships/subdomains", headers=self.headers)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                app_logger.debug(f"non json response for domain {domain}")
                return []
                
        except requests.exceptions.RequestException as e:
            app_logger.error(f"error requesting subdomain: {e}")
            return []
        
        except json.JSONDecodeError as e:
            app_logger.error(f"error decoding json: {e}")
            return []