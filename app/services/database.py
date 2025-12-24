from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session, Session
from app.config.settings import settings

# create engine for postgresql database
engine = create_engine(
    f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST_IP}:5432/{settings.DB_NAME}",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False
)

# session factory (scoped session if multithreaded or async)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# declarative base for orm models
Base = declarative_base()


def get_db():
    """
    generates a new database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()