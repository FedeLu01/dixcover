from sqlmodel import Field

from app.models.base_model import BaseTable

class OtxSubdomain(BaseTable, table=True):
    __tablename__ = "otx_subdomains"

    address: str = Field()
    subdomain: str = Field(index=True, unique=True)
    