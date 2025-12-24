# clients/base_client.py
import requests
import time
import random
import re

from typing import Dict, Any, Optional
from urllib.parse import urljoin
from abc import ABC
from app.utils.log import app_logger

class BaseHTTPClient(ABC):
    """Base HTTP client with common functionalities like GET, POST, retries, and error handling"""
    
    def __init__(self,
                 base_url: str,
                 api_key: Optional[str] = None, 
                 timeout: int = 30, max_retries: int = 3, 
                 retry_delay: float = 1.5,
                 content_type: Optional[str] = 'application/json',
                 accept: Optional[str] = 'application/json'
                 ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.content_type = content_type
        self.accept = accept
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        # setup default headers
        self._setup_default_headers()
    
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
    
    def _setup_default_headers(self):
        """setup default headers for the client"""
        self.session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': self.accept,
            'Content-Type': self.content_type,
        })
        
        # add authentication header if api_key is provided
        if self.api_key:
            self._setup_authentication()
            
    def _setup_authentication(self):
        """setup authentication with API key (can be overridden)"""
        pass
    
    def _build_url(self, endpoint: str) -> str:
        """build full URL"""
        return urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> Dict[str, Any]:
        """do HTTP request with retries"""
        url = self._build_url(endpoint)
        request_headers = headers or {}
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=self.timeout
                )

                # check rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    app_logger.warning("request.rate_limited", url=url, attempt=attempt + 1, wait=retry_after)
                    time.sleep(retry_after)
                    continue

                # debug log for non-success status codes (we'll still raise below)
                if response.status_code >= 400:
                    app_logger.debug("request.status", method=method, url=url, status_code=response.status_code)

                response.raise_for_status()

                # try to parse json response
                try:
                    return response.json()
                except ValueError:
                    app_logger.debug("request.parse_text", url=url, length=len(response.text))
                    return {'text': response.text}

            except requests.exceptions.RequestException as e:
                # sanitize message to remove memory addresses like <HTTPSConnection(...) at 0x...>
                raw = str(e)
                sanitized = re.sub(r'0x[0-9a-fA-F]+', '<ptr>', raw)
                exc_type = type(e).__name__
                app_logger.error("request.failed", method=method, url=url, attempt=attempt + 1, exc_type=exc_type, error=sanitized)

                if attempt == self.max_retries:
                    raise

                # exponential backoff
                wait_time = self.retry_delay * (2 ** attempt)
                time.sleep(wait_time)
        
        raise Exception(f"Failed to make request after {self.max_retries} attempts")
    
    def get(self, endpoint: str, params: Optional[Dict] = None, 
            headers: Optional[Dict] = None) -> Dict[str, Any]:
        """do GET request"""
        return self._make_request('GET', endpoint, params=params, headers=headers)
    
    def post(self, endpoint: str, data: Optional[Dict] = None,
             headers: Optional[Dict] = None) -> Dict[str, Any]:
        """do POST request"""
        return self._make_request('POST', endpoint, data=data, headers=headers)
    
    def close(self):
        """close HTTP session"""
        self.session.close()