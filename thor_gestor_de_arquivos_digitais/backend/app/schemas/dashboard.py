from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DashboardSupportCount(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tipo_suporte: str
    total: int


class DashboardAddressingStats(BaseModel):
    locais: int
    zonas: int
    estruturas: int
    compartimentos: int
    posicoes: int
    posicoes_livres: int
    posicoes_ocupadas: int
    posicoes_inativas: int
    taxa_ocupacao: float


class DashboardStats(BaseModel):
    total_unidades: int
    aips_digitais: int
    midias_ativas: int
    alertas: int
    unidades_por_suporte: list[DashboardSupportCount]
    enderecamento: DashboardAddressingStats
