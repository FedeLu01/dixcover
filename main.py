from app.services.passive_scanner import PassiveScanner
from app.controllers.passive_scanner import PassiveScannerController 
from app.jobs.dixcover import store_subdomains
from app.jobs.init_db import init_db

print("Starting PassiveScanner...")
#test = PassiveScannerController(PassiveScanner("example.com")).handle_get_subdomains_from_certificates()
#init_db()
used = store_subdomains("example.com")
print(used)
print("PassiveScanner finished.")

# TODO: revisar que viene en el common_name de crt.sh con el dominio bWVsaQo=
# TODO: revisar el parsing del timeformat de crt.sh (a veces viene si float.)