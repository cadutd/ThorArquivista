from __future__ import annotations

from fastapi import APIRouter, Depends

from app.security.deps import get_current_user_claims

router = APIRouter()


@router.get("/me")
async def me(claims: dict = Depends(get_current_user_claims)):
    """
    Retorna claims básicas do token. Útil para validar que o Keycloak está integrado.
    """
    return {
        "sub": claims.get("sub"),
        "preferred_username": claims.get("preferred_username"),
        "email": claims.get("email"),
        "name": claims.get("name"),
        "realm_access": claims.get("realm_access"),
        "resource_access": claims.get("resource_access"),
        "iss": claims.get("iss"),
        "aud": claims.get("aud"),
        "azp": claims.get("azp"),
    }
