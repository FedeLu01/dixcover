# clients/base_client.py
import requests
import time
import json
import random

from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
from abc import ABC, abstractmethod
from app.utils.log import app_logger

class BaseHTTPClient(ABC):
    """Cliente HTTP base con funcionalidades comunes"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 timeout: int = 30, max_retries: int = 3, 
                 retry_delay: float = 1.5):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        # Configurar headers por defecto
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
        "Python-urllib/3.10",
        "Python-requests/2.31.0",
        "Scrapy/2.11.0 (+https://scrapy.org)",
        "python-httpx/0.27.0",
        "aiohttp/3.9.1",
        "Wget/1.21.3",
        "curl/8.4.0",
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    ]
    
    def _setup_default_headers(self):
        """Configurar headers por defecto del cliente"""
        self.session.headers.update({
            'User-Agent': f"{random.choice(self.USER_AGENTS)}",
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Agregar autenticación si está disponible
        if self.api_key:
            self._setup_authentication()
    
    @abstractmethod
    def _setup_authentication(self):
        """Configurar autenticación específica del cliente"""
        pass
    
    def _build_url(self, endpoint: str) -> str:
        """Construir URL completa"""
        return urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Realizar request HTTP con reintentos"""
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
                
                # Verificar rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    app_logger.warning(f"Rate limited. Waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                
                # Intentar parsear JSON, si falla devolver texto
                try:
                    return response.json()
                except ValueError:
                    return {'text': response.text}
                    
            except requests.exceptions.RequestException as e:
                app_logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                
                if attempt == self.max_retries:
                    raise
                
                # Backoff exponencial
                wait_time = self.retry_delay * (2 ** attempt)
                time.sleep(wait_time)
        
        raise Exception(f"Failed to make request after {self.max_retries} attempts")
    
    def get(self, endpoint: str, params: Optional[Dict] = None, 
            headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Realizar GET request"""
        return self._make_request('GET', endpoint, params=params, headers=headers)
    
    def post(self, endpoint: str, data: Optional[Dict] = None,
             headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Realizar POST request"""
        return self._make_request('POST', endpoint, data=data, headers=headers)
    
    def close(self):
        """Cerrar sesión HTTP"""
        self.session.close()