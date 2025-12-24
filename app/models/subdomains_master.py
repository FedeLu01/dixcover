from typing import Optional, List
from datetime import datetime

from sqlmodel import Field, Column, DateTime, SQLModel
from sqlalchemy import JSON


class MasterSubdomains(SQLModel, table=True):
    __tablename__ = "subdomains_master"

    id: Optional[int] = Field(default=None, primary_key=True)
    subdomain: str = Field(index=True, unique=True, nullable=False)
    # list of sources that detected this subdomain (keeps history)
    sources: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    # last time we observed it alive (kept for quick overview)
    last_alive: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    # when this master record was created in the system
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime, nullable=False))
