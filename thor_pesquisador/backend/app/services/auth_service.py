from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urlsplit

import httpx
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import Sessao, Usuario
from app.services.cpf import normalizar_cpf


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_authorization_url(state: str, nonce: str, code_challenge: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.govbr_client_id,
            "scope": "openid email profile",
            "redirect_uri": settings.govbr_redirect_uri,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{settings.govbr_authorize_url}?{query}"


def random_urlsafe(size: int = 32) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(size)).decode("ascii").rstrip("=")


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


async def exchange_code_for_claims(code: str, code_verifier: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            settings.govbr_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.govbr_redirect_uri,
                "code_verifier": code_verifier,
            },
            auth=(settings.govbr_client_id, settings.govbr_client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_response.raise_for_status()
        payload = token_response.json()
        id_token = payload.get("id_token")
        token = id_token
        if not token:
            raise HTTPException(status_code=400, detail="gov.br nao retornou token.")

        jwks_response = await client.get(settings.govbr_jwks_url)
        jwks_response.raise_for_status()

    return validate_jwt(token, jwks_response.json())


def validate_jwt(token: str, jwks: dict) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key = next((item for item in jwks.get("keys", []) if item.get("kid") == kid), None)
        if not key:
            raise JWTError("kid nao encontrado no JWK.")
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.govbr_client_id,
            options={"verify_at_hash": False, "require_exp": True, "require_aud": True,
                     "require_sub": True, "require_iss": True},
        )
        provider = urlsplit(settings.govbr_authorize_url)
        if not isinstance(claims["iss"], str) or claims["iss"].rstrip("/") != f"{provider.scheme}://{provider.netloc}":
            raise JWTError("Emissor invalido.")
        return claims
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token gov.br invalido: {exc}") from exc


def usuario_from_claims(db: Session, claims: dict) -> Usuario:
    try:
        sub = normalizar_cpf(str(claims.get("sub") or ""))
        cpf = normalizar_cpf(str(claims.get("preferred_username") or sub))
        if sub != cpf:
            raise ValueError("Identidade inconsistente.")
    except ValueError as exc:
        raise HTTPException(401, "Identidade gov.br invalida.") from exc
    usuario = db.scalar(select(Usuario).where(Usuario.cpf == cpf).with_for_update())
    if not usuario or not usuario.ativo or usuario.excluido_em:
        raise HTTPException(403, "Usuario nao cadastrado ou inativo. Solicite acesso ao administrador.")
    if usuario.govbr_sub:
        try:
            if normalizar_cpf(usuario.govbr_sub) != cpf:
                raise ValueError("Vinculo inconsistente.")
        except ValueError as exc:
            raise HTTPException(403, "Vinculo gov.br inconsistente.") from exc
    usuario.govbr_sub = cpf
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(403, "Vinculo gov.br inconsistente.") from exc
    db.refresh(usuario)
    return usuario


def create_session(db: Session, usuario: Usuario) -> str:
    usuario = db.scalar(select(Usuario).where(Usuario.id == usuario.id).with_for_update()
                        .execution_options(populate_existing=True))
    if not usuario:
        raise HTTPException(403, "Usuario nao cadastrado.")
    if not usuario.ativo or usuario.excluido_em:
        raise HTTPException(403, "Usuario inativo.")
    raw_token = random_urlsafe(48)
    sessao = Sessao(
        id=uuid.uuid4(),
        usuario_id=usuario.id,
        token_hash=token_hash(raw_token),
        expira_em=datetime.now(UTC) + timedelta(hours=8),
    )
    db.add(sessao)
    db.commit()
    return raw_token


def get_usuario_by_session(db: Session, raw_token: str | None) -> Usuario | None:
    if not raw_token:
        return None
    sessao = db.scalar(select(Sessao).where(Sessao.token_hash == token_hash(raw_token)))
    if not sessao or sessao.expira_em < datetime.now(UTC):
        return None
    usuario = db.get(Usuario, sessao.usuario_id)
    return usuario if usuario and usuario.ativo and not usuario.excluido_em else None


def delete_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    sessao = db.scalar(select(Sessao).where(Sessao.token_hash == token_hash(raw_token)))
    if sessao:
        db.delete(sessao)
        db.commit()


def create_dev_user_session(db: Session) -> str:
    if not settings.govbr_dev_login or settings.app_env not in {"dev", "test"}:
        raise HTTPException(404, "Login de desenvolvimento desabilitado.")
    usuario = db.scalar(select(Usuario).where(Usuario.govbr_sub == "00000000000"))
    if not usuario:
        usuario = Usuario(govbr_sub="00000000000", cpf="00000000000",
                          username="desenvolvimento", nome="Usuario Desenvolvimento", email="dev@example.local")
        db.add(usuario)
        db.commit()
    if not usuario.ativo or usuario.excluido_em:
        raise HTTPException(403, "Usuario inativo.")
    if settings.dev_admin_enabled and settings.app_env in {"dev", "test"}:
        from app.models.editorial import AcessoInstrumento
        if not db.scalar(select(AcessoInstrumento).where(AcessoInstrumento.usuario_id == usuario.id,
                            AcessoInstrumento.papel == "ADMIN", AcessoInstrumento.instrumento_id.is_(None))):
            db.add(AcessoInstrumento(usuario_id=usuario.id, papel="ADMIN"))
            db.commit()
    return create_session(db, usuario)
