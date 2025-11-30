import json

from app.utils.log import app_logger
from app.clients.base_http_client import BaseHTTPClient

#TODO: en algun momento tengo que agregar la consulta a https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list?limit=1000&page= porque quizas consiga mas info.

class OtxClient(BaseHTTPClient):
    def __init__(self, api_key):
        super().__init__(
            base_url="https://otx.alienvault.com",
            timeout=45,
            max_retries=3,
            retry_delay=1.5,
            api_key=api_key
        )
    
    def get_subdomains(self, target_domain):
        headers = {
            "X-OTX-API-KEY": self.api_key
        }
        
        try:
            
            response = self.get(endpoint=f"/api/v1/indicators/domain/{target_domain}/passive_dns", headers=headers)
            
            return response.get('passive_dns', [])
                
        except Exception as e:
            app_logger.error(f"error requesting subdomain: {e}")
            return []
        
        except json.JSONDecodeError as e:
            app_logger.error(f"error decoding json: {e}")
            return []