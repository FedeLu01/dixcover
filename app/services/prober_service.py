import requests
import time
import random
import re
from datetime import datetime
from typing import Dict, List, Optional

from app.utils.log import app_logger
from app.config.settings import settings
from app.clients.base_http_client import BaseHTTPClient


class ProberService:
    """Simple HTTP prober for subdomains.

    - Tries an HTTP HEAD request first, then a GET if HEAD fails with a 405.
        - Treats any HTTP response (including 2xx/3xx/4xx/5xx) as a reachable host.
            Only network-level errors (connection refused, DNS failure, timeout, etc.)
            are considered "not alive".
        - Returns a dict with keys: subdomain, is_alive (bool - reachable), probed_at (datetime),
            status_code (int|None), error (str|None)
    """

    def __init__(
        self,
        timeout: float = 5.0,
        verify: bool = True,
        user_agent: Optional[str] = None,
        http_client: Optional[object] = None,
        ports: Optional[List[int]] = None,
    ):
        self.timeout = timeout
        self.verify = verify
        # Prefer client's session User-Agent when an http_client with session is provided.
        self.http_client = http_client
        if self.http_client and hasattr(self.http_client, "session") and self.http_client.session.headers.get("User-Agent"):
            # client already configures headers; do not override when making client requests
            self.headers = {}
        else:
            # pick a random user agent from BaseHTTPClient list when none provided
            ua = user_agent or random.choice(getattr(BaseHTTPClient, "USER_AGENTS", ["dixcover-prober/1.0"]))
            self.headers = {"User-Agent": ua}
        # optional HTTP client (should be instance of your BaseHTTPClient or similar)
        # ports to try (exclude default 443/80 since we probe default schemes first)
        # try secure ports first, then common HTTP developer ports
        self.ports = ports or [8443, 8080, 8000, 3000]

    def probe(self, subdomain: str) -> Dict:
        probed_at = datetime.now()

        # helper to perform a single request using provided http client if available
        def _single_request(method: str, url: str):
            # If an http_client with a requests-like session is provided, prefer it
            client = self.http_client
            max_retries = getattr(client, "max_retries", 2) if client else 2
            retry_delay = getattr(client, "retry_delay", 1.0) if client else 1.0

            for attempt in range(max_retries + 1):
                try:
                    if client and hasattr(client, "session"):
                        # Use client's session headers (do not override) so configured UA, auth, and other defaults are preserved
                        resp = client.session.request(
                            method=method,
                            url=url,
                            timeout=self.timeout,
                            allow_redirects=True,
                            verify=self.verify,
                        )
                    else:
                        resp = requests.request(
                            method=method,
                            url=url,
                            timeout=self.timeout,
                            allow_redirects=True,
                            headers=self.headers,
                            verify=self.verify,
                        )

                    # handle rate limit header
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        app_logger.warning("probe.rate_limited", subdomain=subdomain, url=url, wait=retry_after)
                        time.sleep(retry_after)
                        continue

                    return resp
                except requests.RequestException as e:
                    # sanitize exception message to avoid leaking memory addresses like <HTTPConnection(...) at 0x...>
                    raw_err = str(e)
                    sanitized = re.sub(r'0x[0-9a-fA-F]+', '<ptr>', raw_err)
                    app_logger.debug("probe.request_exception", subdomain=subdomain, url=url, error=sanitized, attempt=attempt)
                    if attempt == max_retries:
                        raise
                    time.sleep(retry_delay * (2 ** attempt))

        # Ordered probing logic:
        # 1) try default https (no explicit port)
        # 2) try default http (no explicit port)
        # 3) try additional ports with https then http
        last_error = None

        def _try_scheme_port(scheme: str, port: Optional[int] = None):
            url = f"{scheme}://{subdomain}/" if port is None else f"{scheme}://{subdomain}:{port}/"
            # HEAD first
            resp = _single_request("HEAD", url)
            status = getattr(resp, "status_code", None)
            # If HEAD not allowed or status missing, try GET
            if status == 405 or status is None:
                resp = _single_request("GET", url)
                status = getattr(resp, "status_code", None)
            is_alive = status is not None
            app_logger.debug("probe.result", subdomain=subdomain, url=url, is_alive=is_alive, status_code=status)
            return is_alive, status

        # 1) https default
        try:
            is_alive, status = _try_scheme_port("https", None)
            if is_alive:
                app_logger.debug("probe.success", subdomain=subdomain, url=f"https://{subdomain}/", status_code=status)
                return {"subdomain": subdomain, "is_alive": True, "probed_at": probed_at, "status_code": status, "error": None}
        except Exception as e:
            last_error = str(e)
            app_logger.debug("probe.try_failed", subdomain=subdomain, url=f"https://{subdomain}/", error=last_error)

        # 2) http default
        try:
            is_alive, status = _try_scheme_port("http", None)
            if is_alive:
                app_logger.debug("probe.success", subdomain=subdomain, url=f"http://{subdomain}/", status_code=status)
                return {"subdomain": subdomain, "is_alive": True, "probed_at": probed_at, "status_code": status, "error": None}
        except Exception as e:
            last_error = str(e)
            app_logger.debug("probe.try_failed", subdomain=subdomain, url=f"http://{subdomain}/", error=last_error)

        # 3) other ports (both https and http)
        for port in self.ports:
            for scheme in ("https", "http"):
                try:
                    is_alive, status = _try_scheme_port(scheme, port)
                    if is_alive:
                        app_logger.debug("probe.success", subdomain=subdomain, url=f"{scheme}://{subdomain}:{port}/", status_code=status)
                        return {"subdomain": subdomain, "is_alive": True, "probed_at": probed_at, "status_code": status, "error": None}
                except Exception as e:
                    last_error = str(e)
                    app_logger.debug("probe.try_failed", subdomain=subdomain, url=f"{scheme}://{subdomain}:{port}/", error=last_error)

        # all attempts failed (network errors)
        app_logger.debug("probe.error", subdomain=subdomain, error=last_error)
        return {"subdomain": subdomain, "is_alive": False, "probed_at": probed_at, "status_code": None, "error": last_error}
