from __future__ import annotations

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_instrumentos: int
    instrumentos_publicados: int
    instrumentos_rascunho: int
    total_campos: int
    total_registros: int
    registros_ativos: int
    registros_inativos: int
    instrumentos_por_tipo: list[dict[str, int | str]]
