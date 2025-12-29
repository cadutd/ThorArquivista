from __future__ import annotations
from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import get_db

def db_dep() -> Generator[Session, None, None]:
    yield from get_db()
