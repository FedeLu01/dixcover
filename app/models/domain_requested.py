from sqlmodel import Field
from datetime import datetime, timedelta

from app.models.base_model import BaseTable

class DomainRequested(BaseTable, table=True):
    domain: str = Field(default= None, index=True)
    time_to_zero: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(minutes=15)
        )
    