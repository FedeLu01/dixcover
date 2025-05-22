import requests
import json

url = "https://www.virustotal.com/vtapi/v2/domain/report"

headers = {
    "accept": "application/json",
    "x-apikey": "536b3d108d956b9bd4ae18766495cae83fc9c303dd98fe4fa79da49ac1079e3e"
}

params = {
    "domain": "compragamer.com",
    "apikey": "536b3d108d956b9bd4ae18766495cae83fc9c303dd98fe4fa79da49ac1079e3e"
}
response = requests.get(url, headers=headers, params=params)

with open("virustotal_subdomains.json", "w") as f:
    json.dump(response.json(), f, indent=4)
    print("Data saved to virustotal_subdomains.json")