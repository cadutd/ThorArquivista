from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, health, instrumentos

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(instrumentos.router, prefix="/instrumentos", tags=["instrumentos"])
