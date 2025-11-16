from pydantic import BaseModel

class DomainInput(BaseModel):
    domain: str 
    