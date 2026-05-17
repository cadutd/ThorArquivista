from __future__ import annotations

import secrets
import string
from enum import StrEnum

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.user import User


class IdentityProvider(StrEnum):
    KEYCLOAK = "KEYCLOAK"


class IdentityAccountResult(dict):
    provider: str
    provider_user_id: str
    temporary_password: str
    username: str
    email: str


async def create_identity_account(
    usuario: User,
    provider: IdentityProvider,
) -> IdentityAccountResult:
    if provider == IdentityProvider.KEYCLOAK:
        return await _create_keycloak_user(usuario)

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Provedor de identidade não suportado.",
    )


async def _create_keycloak_user(usuario: User) -> IdentityAccountResult:
    if usuario.keycloak_sub:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário já está vinculado a uma conta de identidade.",
        )

    temporary_password = _generate_temporary_password()
    first_name, last_name = _split_display_name(usuario.nome)
    token = await _get_keycloak_admin_token()
    realm_admin_url = f"{settings.keycloak_internal_url}/admin/realms/{settings.keycloak_realm}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "username": usuario.username,
        "email": usuario.email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": usuario.ativo,
        "emailVerified": True,
        "requiredActions": ["UPDATE_PASSWORD"],
        "credentials": [
            {
                "type": "password",
                "value": temporary_password,
                "temporary": True,
            }
        ],
        "attributes": {
            "thor_usuario_id": [str(usuario.id)],
            "thor_papel": [usuario.papel],
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        created = await client.post(f"{realm_admin_url}/users", headers=headers, json=payload)
        if created.status_code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma conta no provedor de identidade para este usuário ou e-mail.",
            )
        if created.status_code not in (201, 204):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Falha ao criar usuário no provedor de identidade: {created.text}",
            )

        provider_user_id = _provider_id_from_location(created.headers.get("location"))
        if not provider_user_id:
            provider_user_id = await _find_keycloak_user_id(client, realm_admin_url, headers, usuario.username)

    if not provider_user_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Conta criada, mas o provedor não retornou o identificador do usuário.",
        )

    return IdentityAccountResult(
        provider=IdentityProvider.KEYCLOAK.value,
        provider_user_id=provider_user_id,
        temporary_password=temporary_password,
        username=usuario.username,
        email=usuario.email,
    )


async def _get_keycloak_admin_token() -> str:
    token_url = (
        f"{settings.keycloak_internal_url}/realms/{settings.keycloak_admin_realm}"
        "/protocol/openid-connect/token"
    )
    data = {
        "grant_type": "password",
        "client_id": settings.keycloak_admin_client_id,
        "username": settings.keycloak_admin_user,
        "password": settings.keycloak_admin_password,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(token_url, data=data)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao autenticar no provedor de identidade.",
        )
    return str(response.json()["access_token"])


async def _find_keycloak_user_id(
    client: httpx.AsyncClient,
    realm_admin_url: str,
    headers: dict[str, str],
    username: str,
) -> str | None:
    response = await client.get(
        f"{realm_admin_url}/users",
        headers=headers,
        params={"username": username, "exact": "true"},
    )
    if response.status_code != 200:
        return None
    users = response.json()
    if not users:
        return None
    return users[0].get("id")


def _provider_id_from_location(location: str | None) -> str | None:
    if not location:
        return None
    return location.rstrip("/").split("/")[-1] or None


def _split_display_name(nome: str) -> tuple[str, str]:
    parts = [part for part in nome.strip().split(" ") if part]
    if not parts:
        return "Usuário", "Thor"
    if len(parts) == 1:
        return parts[0], "Thor"
    return " ".join(parts[:-1]), parts[-1]


def _generate_temporary_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(length - 3))
    return f"{password}A1!"
