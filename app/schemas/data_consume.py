from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class SourceEnum(str, Enum):
    ALL_SUBDOMAINS = "all_subdomains"
    ALIVE_SUBDOMAINS = "alive_subdomains"


class DataConsumeRequest(BaseModel):
    domain: str
    source: SourceEnum  # 'all_subdomains' or 'alive_subdomains'


class SubdomainOut(BaseModel):
    subdomain: str
    sources: List[str]
    created_at: Optional[str]


class AliveOut(BaseModel):
    subdomain: str
    probed_at: Optional[str]
    status_code: Optional[int]
