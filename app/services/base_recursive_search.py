import re
import time
import concurrent.futures
from threading import Lock
from app.utils.log import app_logger
import datetime

class BaseSubdomainService:
    def __init__(self, max_depth=5, delay=5, max_workers=5):
        self.max_depth = max_depth
        self.delay = delay
        self.max_workers = max_workers
        self.found_subdomains = set()
        self.processed_domains = set()
        self.lock = Lock()

    def _is_valid_subdomain(self, name, target_domain):
        name = name.replace('*.', '')
        if not name.endswith(f'{target_domain}') and name != target_domain:
            return False
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        if not bool(domain_pattern.match(name)):
            app_logger.debug(f'invalid domain: {name}')
        return bool(domain_pattern.match(name))

    def recursive_search(self, db, domain, current_depth=0):
        raise NotImplementedError("Implement in subclass")

    def store_subdomains_data(self, db, data):
        raise NotImplementedError("Implement in subclass")