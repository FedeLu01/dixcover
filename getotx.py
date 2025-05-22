import requests
import json

url = "https://otx.alienvault.com/api/v1/indicators/domain/mercadolibre.com.ar/url_list?limit=1000&page="
headers = {
    "X-OTX-API-KEY": "ef971c4000cc85666ab685452c355ecb08f10890fec5faaea43e9b4fc81f8b92"
}

response = requests.get(url, headers=headers)
with open("otx_subdomains.json", "w") as f:
    json.dump(response.json(), f, indent=4)
    print("Data saved to otx_subdomains.json")