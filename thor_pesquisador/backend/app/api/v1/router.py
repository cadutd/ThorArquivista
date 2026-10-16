from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, health, instrumentos
from app.api.v1 import imagens, editorial, publico, administracao
from app.api.v1 import conformidade

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(conformidade.router, tags=["conformidade"])
api_router.include_router(publico.router, tags=["publico"])
api_router.include_router(editorial.router, tags=["editorial"])
api_router.include_router(administracao.router, tags=["administracao"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(imagens.router, tags=["imagens"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(instrumentos.router, prefix="/instrumentos", tags=["instrumentos"])
