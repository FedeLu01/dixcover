from datetime import datetime
import re

class Parser:
    def __init__(self, data):
        self.data = data

    def parse_crtsh(self):
        raw_subdomains = []
        parsed_data = []
        try:
            for data_block in self.data:
                raw_data = data_block["name_value"]
                subdomains = raw_data.strip().split("\n")
                if len(subdomains) > 0:
                    for subdomain in subdomains:
                        if not subdomain.strip().startswith("*."):
                            raw_subdomains.append(subdomain.strip())
            # Remove duplicates
            raw_subdomains = list(set(raw_subdomains))
            # Filter out subdomains that are not valid
            for subdomain in raw_subdomains:
                if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", subdomain):
                    parsed_data.append({
                        "subdomain": subdomain,
                        "registered_on": datetime.strptime(data_block["entry_timestamp"], "%Y-%m-%dT%H:%M:%S.%f" or "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d"),
                    })
        except Exception as e:
            print(f"Error parsing crt.sh data: {e}")
            return []
        
        return parsed_data