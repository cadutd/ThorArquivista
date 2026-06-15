from __future__ import annotations

from typing import Any
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ResultadoEventoPreservacao, TipoEventoMidiaArmazenamento


class EventoMidiaArmazenamentoBase(BaseModel):
    tipo_evento: TipoEventoMidiaArmazenamento
    resultado: ResultadoEventoPreservacao = ResultadoEventoPreservacao.SUCESSO
    data_evento: datetime | None = None
    detalhe: str | None = None
    agente: str | None = Field(default=None, max_length=255)
    correlacao: str | None = Field(default=None, max_length=255)
    premis_json: dict[str, Any] | None = None
    evento_relacionado_id: int | None = None


class EventoMidiaArmazenamentoCreate(EventoMidiaArmazenamentoBase):
    pass


class EventoMidiaArmazenamentoOut(EventoMidiaArmazenamentoBase):
    id: int
    id_midia_armazenamento: int
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}
