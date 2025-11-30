from app.clients.base_http_client import BaseHTTPClient
from app.utils.log import app_logger
from app.config.settings import settings

import json

class ShodanClient(BaseHTTPClient):
    def __init__(self):
        super().__init__(base_url="https://api.shodan.io")


    def search_domain(self, domain):
        """ search subdomains for a given domain """
        try:
            
            response = self.get(f"/dns/domain/{domain}?key={settings.SHODAN_API_KEY}")
            
            return response.get('subdomains', [])    
        
        except Exception as e:
            app_logger.error(f"error requesting subdomain: {e}")
            return []
        
        except json.JSONDecodeError as e:
            app_logger.error(f"error decoding json: {e}")
            return []