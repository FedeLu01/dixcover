from sqlmodel import Field

from .base_model import BaseTable

class VirusTotalSubdomain(BaseTable, table=True):
    __tablename__ = "virus_total_subdomain"

    subdomain: str = Field(index=True, unique=True)
    