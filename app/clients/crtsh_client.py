import json
import time

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
        """ Search certificates for a given domain.

        This method retries up to `max_retries` when receiving HTTP 502 responses.
        Returns parsed JSON on success or an empty list on failure.
        """
        params = {
            'q': f'{domain}',
            'output': 'json'
        }

        attempts = getattr(self, 'max_retries', 3)
        delay = getattr(self, 'retry_delay', 1.5)

        for attempt in range(1, attempts + 1):
            try:
                # Use session.request so we get the full response object
                resp = self.session.request('GET', self._build_url(''), params=params, timeout=self.timeout)

                if resp.status_code == 502:
                    app_logger.warning(f"crtsh returning 502 (attempt {attempt}/{attempts}); retrying after {delay}s")
                    if attempt < attempts:
                        time.sleep(delay)
                        continue
                    else:
                        app_logger.error(f"crtsh: exhausted retries after receiving 502")
                        return []

                # If other non-2xx statuses, log and return empty
                if resp.status_code >= 400:
                    app_logger.error(f"crtsh returned status {resp.status_code} for domain {domain}")
                    return []

                # attempt JSON parse
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    app_logger.error(f"crtsh: failed to decode JSON for domain {domain}")
                    return []

            except Exception as e:
                app_logger.error(f"error requesting subdomain: {e}")
                # if it's the last attempt, return empty
                if attempt >= attempts:
                    return []
                time.sleep(delay)