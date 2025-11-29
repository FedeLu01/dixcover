from app.api.crtsh_controller import handle_recursive_search
from sqlmodel import SQLModel
from app.services.database import engine

def init_db():
    SQLModel.metadata.create_all(engine)

print("Starting PassiveScanner...")
#test = PassiveScannerController(PassiveScanner("example.com")).handle_get_subdomains_from_certificates()
#init_db()
init_db()
domain = 'galicia.ar'
handle_recursive_search(domain)
print("PassiveScanner finished.")