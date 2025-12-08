from sqlmodel import Field
from datetime import datetime, timedelta

from app.models.base_model import BaseTable
from sqlalchemy import Column, Boolean

class DomainRequested(BaseTable, table=True):
    domain: str = Field(default= None, index=True)
    time_to_zero: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(minutes=15)
        )
    scheduled: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False))