from services.crtsh import PassiveScanner

print("Starting PassiveScanner...")
print(PassiveScanner("mundosteam.shop").get_subdomains_by_certificates()) 
print(PassiveScanner("mundosteam.shop").get_subdomains_by_wayback())
print(PassiveScanner("mundosteam.shop").get_subdomains_by_urlscan())
#print(PassiveScanner("mundosteam.shop").get_subdomains_by_virus_total()) # necesito api key
print(PassiveScanner("mundosteam.shop").get_subdomains_by_hackertarget())
print(PassiveScanner("mundosteam.shop").get_subdomains_by_otx())
print(PassiveScanner("mundosteam.shop").get_subdomains_by_shodan()) 
print("PassiveScanner finished.")