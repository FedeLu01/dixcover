from pydantic import BaseModel, Field


class ProbeResponse(BaseModel):
    """Response model for probe endpoint."""
    status: str = Field(..., description="Status of the probe request")
    message: str = Field(..., description="Human-readable message")
