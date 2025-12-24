from sqlmodel import Field, Column, JSON

from .base_model import BaseTable

class ShodanSubdomain(BaseTable, table=True):
    __tablename__ = "shodan_subdomain"

    subdomain: str = Field(unique=True, nullable=False)
    #ports: dict = Field(sa_column=Column(JSON))
    #ip: dict = Field(sa_column=Column(JSON))
    