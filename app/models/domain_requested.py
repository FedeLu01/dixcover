from sqlmodel import Field

from app.models.base_model import BaseTable

class DomainRequested(BaseTable, table=True):
    domain: str = Field(index=True)
    requested_at: str = Field()
    client_ip: str = Field()
    