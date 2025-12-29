from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.aips import router as aips_router
from app.api.v1.unidades_acondicionamento import router as unidades_router
from app.api.v1.midias_armazenamento import router as midias_router
from app.api.v1.copias_unidades_acondicionamento_digitais import router as copias_router
from app.api.v1.eventos_preservacao import router as eventos_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(unidades_router, prefix="/unidades-acondicionamento", tags=["unidades-acondicionamento"])
api_router.include_router(midias_router, prefix="/midias-armazenamento", tags=["midias-armazenamento"])
api_router.include_router(copias_router, tags=["copias-unidade-acondicionamento-digital"])
api_router.include_router(eventos_router, tags=["eventos-preservacao"])
api_router.include_router(aips_router, prefix="/aips", tags=["aips"])
