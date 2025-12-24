from sqlmodel import Field, SQLModel
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, Boolean


class DomainRequested(SQLModel, table=True):
    __tablename__ = "domain_requested"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(default=None, index=True, nullable=False)
    requested_at: datetime = Field(default_factory=datetime.now)
    # when can the user run another scan for the same domain
    time_to_zero: datetime = Field(default_factory=lambda: datetime.now() + timedelta(minutes=15))
    scheduled: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False))
    requested_by: Optional[str] = Field(default=None)