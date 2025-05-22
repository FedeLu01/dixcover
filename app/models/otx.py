from sqlmodel import Field

from app.models.base_model import BaseModel

class Otx(BaseModel, table=True):
    subdomain: str = Field(unique=True, index=True)
    uri: str = Field(unique=True, nullable=False)
