from __future__ import annotations
from pydantic import BaseModel

class JobOut(BaseModel):
    id: int
    job_type: str
    status: str

    model_config = {"from_attributes": True}
