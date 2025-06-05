import httpx
import asyncio
import random
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from urllib.parse import urljoin
from app.utils.log import app_logger


class BaseAsyncHTTPClient(ABC):
    """Cliente HTTP base asíncrono con funcionalidades comunes"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (Android 14; Mobile; rv:123.0) Gecko/123.0 Firefox/123.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    ]

    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 timeout: int = 30, max_retries: int = 4,
                 retry_delay: float = 1.5):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.client = httpx.AsyncClient(timeout=self.timeout, headers=self._default_headers())

    def _default_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers.update(self._auth_header())
        return headers

    @abstractmethod
    def _auth_header(self) -> Dict[str, str]:
        """Debe ser implementado para añadir headers de autenticación si es necesario."""
        pass

    def _build_url(self, endpoint: str) -> str:
        return urljoin(f"{self.base_url}/", endpoint.lstrip('/'))

    async def _make_request(self, method: str, endpoint: str,
                            params: Optional[Dict] = None,
                            data: Optional[Dict] = None,
                            headers: Optional[Dict] = None) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        all_headers = self.client.headers.copy()
        if headers:
            all_headers.update(headers)

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=all_headers
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    app_logger.warning(f"Rate limited. Retrying after {retry_after}s.")
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()

                try:
                    return response.json()
                except ValueError:
                    return {"text": response.text}

            except httpx.RequestError as e:
                app_logger.error(f"Request error on attempt {attempt + 1}: {e}")
            except httpx.HTTPStatusError as e:
                app_logger.warning(f"HTTP status error on attempt {attempt + 1}: {e}")

            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

        raise Exception(f"Failed to complete request after {self.max_retries} attempts")

    async def get(self, endpoint: str, params: Optional[Dict] = None,
                  headers: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._make_request("GET", endpoint, params=params, headers=headers)

    async def post(self, endpoint: str, data: Optional[Dict] = None,
                   headers: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._make_request("POST", endpoint, data=data, headers=headers)

    async def close(self):
        await self.client.aclose()