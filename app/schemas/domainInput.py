from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DomainInput(BaseModel):
    domain: str 
    