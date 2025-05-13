from app.services.database import DatabaseManager
from app.models.schema import ALL_TABLES

def init_db():
    db = DatabaseManager()
    for query in ALL_TABLES:
        db.execute_query(query)
    print("Todas las tablas fueron creadas correctamente.")
