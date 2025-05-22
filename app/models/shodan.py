from sqlmodel import Field, Column, JSON

from app.models.base_model import BaseModel

class Shodan(BaseModel, table=True):
    subdomain: str = Field(unique=True, nullable=False)
    ports: dict = Field(sa_column=Column(JSON))
    ip: dict = Field(sa_column=Column(JSON))
    