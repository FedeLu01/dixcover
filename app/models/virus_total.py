from sqlmodel import Field, Column, JSON

from app.models.base_model import BaseModel

class VirusTotal(BaseModel, table=True):
    subdomain: str = Field(unique=True)
    ip: dict = Field(sa_column=Column(JSON))
    uri: str = Field(unique=True)
    