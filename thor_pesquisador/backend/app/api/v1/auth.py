from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_dep
from app.core.config import settings
from app.models.user import Usuario
from app.schemas.auth import AuthStartOut, UsuarioOut
from app.services.auth_service import (
    build_authorization_url,
    code_challenge,
    create_dev_user_session,
    create_session,
    delete_session,
    exchange_code_for_claims,
    random_urlsafe,
    upsert_usuario_from_claims,
)

router = APIRouter()


@router.get("/govbr/start", response_model=AuthStartOut)
def govbr_start(response: Response) -> AuthStartOut:
    state = random_urlsafe()
    nonce = random_urlsafe()
    verifier = random_urlsafe(48)
    response.set_cookie("thor_auth_state", state, httponly=True, secure=settings.session_cookie_secure, samesite="lax")
    response.set_cookie("thor_auth_nonce", nonce, httponly=True, secure=settings.session_cookie_secure, samesite="lax")
    response.set_cookie("thor_auth_verifier", verifier, httponly=True, secure=settings.session_cookie_secure, samesite="lax")
    return AuthStartOut(authorization_url=build_authorization_url(state, nonce, code_challenge(verifier)))


@router.get("/govbr/callback")
async def govbr_callback(
    request: Request,
    code: str = Query(default=""),
    state: str = Query(default=""),
    db: Session = Depends(db_dep),
) -> RedirectResponse:
    expected_state = request.cookies.get("thor_auth_state")
    verifier = request.cookies.get("thor_auth_verifier")
    if not expected_state or expected_state != state or not verifier:
        raise HTTPException(status_code=400, detail="Estado de autenticacao invalido.")
    claims = await exchange_code_for_claims(code, verifier)
    usuario = upsert_usuario_from_claims(db, claims)
    raw_session = create_session(db, usuario)
    response = RedirectResponse(f"{settings.public_app_url}/instrumentos")
    _set_session_cookie(response, raw_session)
    response.delete_cookie("thor_auth_state")
    response.delete_cookie("thor_auth_nonce")
    response.delete_cookie("thor_auth_verifier")
    return response


@router.post("/dev-login", response_model=UsuarioOut)
def dev_login(response: Response, db: Session = Depends(db_dep)) -> UsuarioOut:
    if not settings.govbr_dev_login:
        raise HTTPException(status_code=404, detail="Login de desenvolvimento desabilitado.")
    raw_session = create_dev_user_session(db)
    _set_session_cookie(response, raw_session)
    usuario = current_user(db, raw_session)
    return _usuario_out(usuario)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(db_dep)) -> dict[str, str]:
    delete_session(db, request.cookies.get(settings.session_cookie_name))
    response.delete_cookie(settings.session_cookie_name, domain=settings.session_cookie_domain)
    return {"status": "ok"}


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(current_user)) -> UsuarioOut:
    return _usuario_out(usuario)


def _set_session_cookie(response: Response, raw_session: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        raw_session,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        domain=settings.session_cookie_domain,
        max_age=8 * 60 * 60,
    )


def _usuario_out(usuario: Usuario) -> UsuarioOut:
    return UsuarioOut(id=str(usuario.id), nome=usuario.nome, email=usuario.email, cpf=usuario.cpf)
