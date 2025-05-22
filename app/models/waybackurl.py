from sqlmodel import Field

from app.models.base_model import BaseModel

class WaybackUrls(BaseModel, table=True):
    uri: str = Field(index=True, unique=True)
    source: str = Field(nullable=False)