import requests
import json

from app.core.exceptions.exceptions import ExternalAPIError
from app.utils.log import app_logger
from app.clients.base_http_client import BaseHTTPClient



class CrtshClient(BaseHTTPClient):
    def __init__(self):
        super().__init__(
            base_url="https://crt.sh/",
            timeout=45,
            max_retries=3,
            retry_delay=1.5,
            ) 
    
    def search_domain(self, domain):
        """ Search certificates for a given domain """
        try:
            params = {
                'q': f'{domain}',
                'output': 'json'
            }
            
            response = self.get(endpoint="", params=params)
            
            return response
        
                
        except requests.exceptions.RequestException as e:
            app_logger.error(f"error requesting subdomain: {e}")
            return []
        
        except json.JSONDecodeError as e:
            app_logger.error(f"error decoding json: {e}")
            return []