from __future__ import annotations
from pydantic import BaseModel

class EventOut(BaseModel):
    id: int
    aip_id: int | None
    event_type: str
    outcome: str | None
    detail: str | None

    model_config = {"from_attributes": True}
