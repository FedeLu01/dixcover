from typing import Optional
from datetime import datetime

from sqlmodel import Field, Column, DateTime

from app.models.base_model import BaseTable


class MasterSubdomains(BaseTable, table=True):
    __tablename__ = "subdomains_master"

    subdomain: str = Field(index=True, unique=True, nullable=False)
    source: str = Field(index=True)
    first_seen: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    last_seen: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    