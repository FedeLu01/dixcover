# main.py o app/init_db.py
from sqlmodel import SQLModel
from app.services.database import engine

def init_db():
    SQLModel.metadata.create_all(engine)

# Llamá a esta función al iniciar tu app
if __name__ == "__main__":
    init_db()
