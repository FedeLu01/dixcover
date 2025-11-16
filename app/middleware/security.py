from urllib.parse import urlparse

class Security:
    def __init__(self):
        pass
    
    def is_valid_domain(self, domain):
        hostname = urlparse(domain)
        return hostname.netloc 