from typing import Optional
from datetime import datetime

from sqlmodel import Field, Column, DateTime, SQLModel
from sqlalchemy import Integer


class AliveSubdomain(SQLModel, table=True):
    __tablename__ = "alive_subdomains"

    id: Optional[int] = Field(default=None, primary_key=True)
    subdomain: str = Field(index=True, unique=True, nullable=False)
    # when this probe occurred (primary timestamp)
    probed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    # last time the host was observed alive
    last_alive: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    status_code: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    notes: Optional[str] = Field(default=None)
