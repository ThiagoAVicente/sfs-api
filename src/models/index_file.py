from pydantic import BaseModel


class StatusResponse(BaseModel):
    """Job status response."""

    job_id: str
    status: str
