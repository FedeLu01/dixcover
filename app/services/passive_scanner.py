import requests
from app.utils.utils import Parser
from app.config.config import Config

class PassiveScanner:
    def __init__(self, domain: str, shodan_api_key: str = None, vt_api_key: str = None):
        self.domain = domain
        self.shodan_api_key = shodan_api_key or Config.SHODAN_API_KEY
        self.vt_api_key = vt_api_key or Config.VIRUSTOTAL_API_KEY

    def get_subdomains_from_certificates(self):
        try:
            response = requests.get(f"https://crt.sh/?q={self.domain}&output=json")
            data = Parser(response.json()).parse_crtsh()
            return data
        except requests.RequestException as e:
            print(f"Error fetching data from crt.sh: {e}")
            return []
        
    def get_subdomains_from_wayback(self):
        try:
            resp = requests.get(f"https://web.archive.org/cdx/search/cdx?url=*.{self.domain}&output=json&fl=original&limit=1000000")
            return resp.json()
        except requests.RequestException as e:
            print(f"Error fetching data from Wayback Machine: {e}")
            return []
        
    def get_subdomains_from_urlscan(self):
        try:
            resp = requests.get(f"https://urlscan.io/api/v1/search/?q={self.domain}")
            return resp.json()
        except requests.RequestException as e:
            print(f"Error fetching data from urlscan: {e}")
            return []
    
    def get_subdomains_from_virus_total(self):
        try:
            auth_header = {
                "X-Apikey": f"{self.vt_api_key}"
            }
            resp = requests.get(f"https://www.virustotal.com/api/v3/domains/{self.domain}/subdomains", headers=auth_header)
            return resp.json()
        except requests.RequestException as e:
            print(f"Error fetching data from VirusTotal: {e}")
            return []
        
    def get_subdomains_from_hackertarget(self):
        try:
            resp = requests.get(f"https://api.hackertarget.com/hostsearch/?q={self.domain}")
            return resp.json()
        except requests.RequestException as e:
            print(f"Error fetching data from HackerTarget: {e}")
            return []
    
    def get_subdomains_from_otx(self):
        try:
            resp = requests.get(f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns")
            return resp.json()
        except requests.RequestException as e:
            print(f"Error fetching data from OTX: {e}")
            return []        
    
    def get_subdomains_from_shodan(self):
        try:
            resp = requests.get(f"https://api.shodan.io/dns/domain/{self.domain}?key={self.api_key}")
            return resp.json()
        except requests.RequestException as e:
            print(f"Error fetching data from Shodan: {e}")
            return []