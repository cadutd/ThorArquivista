from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import Sessao, Usuario


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
        access_token = payload.get("access_token")
        token = id_token or access_token
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
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.govbr_client_id,
            options={"verify_at_hash": False},
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token gov.br invalido: {exc}") from exc


def upsert_usuario_from_claims(db: Session, claims: dict) -> Usuario:
    sub = str(claims.get("sub") or claims.get("preferred_username") or "")
    if not sub:
        raise HTTPException(status_code=400, detail="Token gov.br sem identificador.")
    usuario = db.scalar(select(Usuario).where(Usuario.govbr_sub == sub))
    if not usuario:
        usuario = Usuario(id=uuid.uuid4(), govbr_sub=sub, nome=claims.get("name") or sub)
        db.add(usuario)
    usuario.cpf = claims.get("preferred_username") or claims.get("sub")
    usuario.nome = claims.get("name") or usuario.nome
    usuario.email = claims.get("email")
    db.commit()
    db.refresh(usuario)
    return usuario


def create_session(db: Session, usuario: Usuario) -> str:
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
    return db.get(Usuario, sessao.usuario_id)


def delete_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    sessao = db.scalar(select(Sessao).where(Sessao.token_hash == token_hash(raw_token)))
    if sessao:
        db.delete(sessao)
        db.commit()


def create_dev_user_session(db: Session) -> str:
    usuario = upsert_usuario_from_claims(
        db,
        {
            "sub": "00000000000",
            "preferred_username": "00000000000",
            "name": "Usuario Desenvolvimento",
            "email": "dev@example.local",
        },
    )
    return create_session(db, usuario)
