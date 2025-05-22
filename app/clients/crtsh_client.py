import requests
import json

from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.exceptions.exceptions import ExternalAPIError
from app.utils.log import app_logger



class CrtshClient:
    def __init__(self):
        self.base_url = "https://crt.sh/"

    
    @retry(
    stop=stop_after_attempt(4), # max number of retries
    wait=wait_exponential(multiplier=5, min=4, max=5) # exponential backoff
    )
    def search_domain(self, domain):
        """ Buscar certificados para un dominio específico """
        try:
            params = {
                'q': f'{domain}',
                'output': 'json'
            }
            
            response = requests.get(self.base_url, params=params, timeout=45)
            print(response.url)
            print(response.json())
            response.raise_for_status()
            
            # crt.sh a veces devuelve HTML en lugar de JSON en caso de error
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