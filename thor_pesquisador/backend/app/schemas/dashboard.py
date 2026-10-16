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
    indexacao_jobs_recentes: list[dict[str, str | int | None]] = []
    indexacao_jobs_falhos: int = 0
    pendencias_editoriais: int = 0
    publicacoes_recentes: list[dict] = []
    jobs_conformidade: dict = {}
