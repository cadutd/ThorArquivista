from __future__ import annotations
from pydantic import BaseModel

class AIPCreate(BaseModel):
    identifier: str
    title: str | None = None
    storage_uri: str

class AIPOut(BaseModel):
    id: int
    identifier: str
    title: str | None
    storage_uri: str

    model_config = {"from_attributes": True}
