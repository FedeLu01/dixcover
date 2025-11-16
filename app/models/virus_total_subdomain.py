from sqlmodel import Field

from .base_model import BaseTable

class VirusTotalSubdomain(BaseTable, table=True):
    subdomain: str = Field(index=True)
    