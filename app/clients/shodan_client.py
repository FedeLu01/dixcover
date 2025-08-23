import requests
import json

from tenacity import retry, stop_after_attempt, wait_exponential
from app.utils.log import app_logger
from app.config.settings import settings


class ShodanClient:
    def __init__(self):
        self.base_url = "https://api.shodan.io"


    def search_domain(self, domain):
        """ Buscar certificados para un dominio específico """
        try:
            
            response = requests.get(f"{self.base_url}/dns/domain/{domain}?key={settings.SHODAN_API_KEY}")
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