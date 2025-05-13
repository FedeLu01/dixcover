from datetime import datetime

class Parser:
    def __init__(self, data):
        self.data = data

    def parse_crtsh(self):
        parsed_data = []
        try:
            for data_block in self.data:
                if "*" in data_block["common_name"]:
                    continue
                
                parsed_data.append({
                    "subdomain": data_block["common_name"], 
                    "registered_on": datetime.strptime(data_block["entry_timestamp"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d"),
                    },
                )
            # Remove duplicates
            parsed_data = list({v['subdomain']:v for v in parsed_data}.values())
        except Exception as e:
            print(f"Error parsing crt.sh data: {e}")
            return []
        
        return parsed_data