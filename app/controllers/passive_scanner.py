from app.services.passive_scanner import PassiveScanner
from typing import Dict, List

class PassiveScannerController:
    def __init__(self, scanner: PassiveScanner):
        self.scanner = scanner
        
    def handle_get_subdomains_from_certificates(self) -> List[Dict]:
        crtsh_subdomains = self.scanner.get_subdomains_from_certificates()
        print(crtsh_subdomains)
        return crtsh_subdomains
        