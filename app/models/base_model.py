from datetime import datetime
from typing import Optional
from sqlmodel import Column, DateTime, Field, SQLModel, func


class BaseTable(SQLModel):
    id: Optional[int] = Field(default=None, unique=True, nullable=False, primary_key=True, index=True)
    detected_at: datetime = Field(
        default_factory=datetime.now
        )