from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from app.config.settings import settings

# Crea el engine con pool de conexiones.
engine = create_engine(
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST_IP}:3306/{settings.DB_NAME}",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False
)

# Fabrica de sesiones (scoped session si es multithreaded o async)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Declarative base para modelos orm
Base = declarative_base()


def get_db():
    """
    Genera una nueva sesión de base de datos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()