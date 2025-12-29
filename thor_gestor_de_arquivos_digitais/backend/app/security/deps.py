from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.security.keycloak_jwt import (
    oauth_authorize_url,
    oauth_token_url,
    validar_token_e_obter_claims,
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=oauth_authorize_url(),
    tokenUrl=oauth_token_url(),
)


async def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return await validar_token_e_obter_claims(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
