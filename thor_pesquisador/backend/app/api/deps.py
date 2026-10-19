from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import Usuario
from app.services.auth_service import get_identidade_by_session


def db_dep() -> Session:
    yield from get_db()


def current_identity(
    db: Session = Depends(db_dep),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
):
    if settings.auth_disabled_for_tests:
        usuario = db.query(Usuario).filter(Usuario.ativo.is_(True), Usuario.excluido_em.is_(None)).first()
        if usuario:
            db.info["usuario"] = usuario
            return usuario
    usuario = get_identidade_by_session(db, session_token)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticacao requerida.")
    db.info["identidade"] = usuario
    if isinstance(usuario, Usuario):
        db.info["usuario"] = usuario
    return usuario


def current_user(identity=Depends(current_identity)) -> Usuario:
    if not isinstance(identity, Usuario):
        raise HTTPException(403, "Acesso interno requer usuario cadastrado e permissoes.")
    return identity
