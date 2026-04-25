from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DashboardSupportCount(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tipo_suporte: str
    total: int


class DashboardStats(BaseModel):
    total_unidades: int
    aips_digitais: int
    midias_ativas: int
    alertas: int
    unidades_por_suporte: list[DashboardSupportCount]
