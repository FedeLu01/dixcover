from sqlmodel import SQLModel
import logging

from app.services.database import engine

# Import all model modules so their tables are registered on SQLModel.metadata
# If a model module is not imported, SQLModel.metadata.create_all won't see it.
from app.models import (
    crtsh_subdomain,
    domain_requested,
    otx_subdomains,
    shodan_subdomain,
    subdomains_master,
    virus_total_subdomain,
)

logger = logging.getLogger(__name__)


def init_db():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info('Database tables created or already exist')
    except Exception as e:
        logger.exception('Failed to create database tables: %s', e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
