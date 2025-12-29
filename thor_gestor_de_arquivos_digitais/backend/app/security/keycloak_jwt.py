from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings


@dataclass
class JWKSCache:
    jwks: dict | None = None
    fetched_at: float = 0.0
    ttl_seconds: int = 300  # 5 min


_JWKS_CACHE = JWKSCache()


def _realm_base_url(internal: bool = True) -> str:
    base = settings.keycloak_internal_url if internal else settings.keycloak_url
    return f"{base}/realms/{settings.keycloak_realm}"


def oauth_authorize_url() -> str:
    return f"{_realm_base_url(internal=False)}/protocol/openid-connect/auth"


def oauth_token_url() -> str:
    return f"{_realm_base_url(internal=False)}/protocol/openid-connect/token"


def _jwks_url() -> str:
    return f"{_realm_base_url(internal=True)}/protocol/openid-connect/certs"


async def get_jwks() -> dict:
    now = time.time()
    if _JWKS_CACHE.jwks and (now - _JWKS_CACHE.fetched_at) < _JWKS_CACHE.ttl_seconds:
        return _JWKS_CACHE.jwks

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(_jwks_url())
        r.raise_for_status()
        jwks = r.json()

    _JWKS_CACHE.jwks = jwks
    _JWKS_CACHE.fetched_at = now
    return jwks


def _pick_key(jwks: dict, kid: str) -> dict:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise JWTError("Chave pública (kid) não encontrada no JWKS.")


def _audience_ok(claims: dict) -> bool:
    """
    Keycloak pode colocar audience em 'aud' (string/list) ou usar 'azp' (authorized party).
    """
    client_id = settings.keycloak_client_id

    aud = claims.get("aud")
    azp = claims.get("azp")

    if isinstance(aud, str):
        aud_ok = aud == client_id
    elif isinstance(aud, list):
        aud_ok = client_id in aud
    else:
        aud_ok = False

    azp_ok = (azp == client_id) if isinstance(azp, str) else False

    # Em muitos cenários o token vem com aud="account" e azp=<client_id>
    return aud_ok or azp_ok


async def validar_token_e_obter_claims(token: str) -> dict:
    """
    Valida assinatura e claims básicas:
      - assinatura via JWKS
      - exp/iat (já é feito pelo jose)
      - issuer
      - audience/azp (opcional)
    """
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise JWTError("Token sem 'kid' no header.")

        jwks = await get_jwks()
        key = _pick_key(jwks, kid)

        issuer = _realm_base_url(internal=False)

        # decode valida exp/nbf automaticamente
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=issuer,
            options={
                "verify_aud": False,  # fazemos manualmente (por causa do azp)
            },
        )

        if settings.keycloak_verify_audience and not _audience_ok(claims):
            raise JWTError("Token com audience/azp incompatível com o client_id.")

        return claims

    except JWTError as e:
        raise JWTError(f"Token inválido: {e}") from e
