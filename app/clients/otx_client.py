import requests
import json

from app.utils.log import app_logger
from app.config.settings import settings

#TODO: en algun momento tengo que agregar la consulta a https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list?limit=1000&page= porque quizas consiga mas info.

class OtxClient:
    def __init__(self, api_key):
        self.otx_base_url = f"https://otx.alienvault.com"
        self.api_key = api_key or settings.OTX_API_KEY
    
    def get_subdomains(self, target_domain):
        headers = {
            "X-OTX-API-KEY": self.api_key
        }
        
        try:
            
            response = requests.get(f"{self.otx_base_url}/api/v1/indicators/domain/{target_domain}/passive_dns", headers=headers)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                app_logger.debug(f"non json response for domain {target_domain}")
                return []
                
        except requests.exceptions.RequestException as e:
            app_logger.error(f"error requesting subdomain: {e}")
            return []
        
        except json.JSONDecodeError as e:
            app_logger.error(f"error decoding json: {e}")
            return []