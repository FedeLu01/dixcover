
import json

from app.clients.base_http_client import BaseHTTPClient
from app.utils.log import app_logger
from app.config.settings import settings


class VirusTotalClient(BaseHTTPClient):
    def __init__(self):
        super().__init__(
            base_url="https://www.virustotal.com",
            api_key=settings.VIRUS_TOTAL_API_KEY
            )
        # headers used for VT requests (we still pass headers per-request)
        self.headers = {
            "x-apikey": self.api_key,
            "accept": "application/json"
        }

    def search_domain(self, domain: str, limit: int = 40, next_url: str = None) -> dict:
        """Request a single page of subdomains for `domain` from VirusTotal.

        Returns parsed JSON (dict). Caller should inspect `meta`/`links` to follow pagination.
        """
        # if a full next-url is provided by vt, request it directly
        try:
            if next_url:
                return self.get(next_url, headers=self.headers)

            params = {"limit": limit} if limit is not None else {}

            response = self.get(
                f"/api/v3/domains/{domain}/relationships/subdomains",
                headers=self.headers,
                params=params,
            )

            return response

        except json.JSONDecodeError as e:
            app_logger.error(f"error decoding json from VirusTotal for {domain}: {e}")
            return {}
        except Exception as e:
            app_logger.error(f"error requesting subdomain from VirusTotal: {e}")
            return {}