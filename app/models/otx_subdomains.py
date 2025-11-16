from sqlmodel import Field

from app.models.base_model import BaseTable

class OtxSubdomain(BaseTable, table=True):
    address: str = Field()
    subdomain: str = Field(index=True, unique=True)
    