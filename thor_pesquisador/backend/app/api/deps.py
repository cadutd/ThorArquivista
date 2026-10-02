from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import Usuario
from app.services.auth_service import get_usuario_by_session


def db_dep() -> Session:
    yield from get_db()


def current_user(
    db: Session = Depends(db_dep),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> Usuario:
    if settings.auth_disabled_for_tests:
        usuario = db.query(Usuario).first()
        if usuario:
            return usuario
    usuario = get_usuario_by_session(db, session_token)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticacao requerida.")
    return usuario
