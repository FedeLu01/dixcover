from sqlmodel import Field

from app.models.base_model import BaseTable

class CrtshSubdomain(BaseTable, table=True):
    __tablename__ = "crtsh_subdomain"

    subdomain: str = Field(index=True, unique=True)
    registered_on: str = Field()
    expires_on: str = Field()
    