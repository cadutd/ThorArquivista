from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ResultadoEventoPreservacao, TipoEventoPreservacao


class EventoMidiaArmazenamentoBase(BaseModel):
    tipo_evento: TipoEventoPreservacao
    resultado: ResultadoEventoPreservacao = ResultadoEventoPreservacao.SUCESSO
    detalhe: str | None = None
    agente: str | None = Field(default=None, max_length=255)
    correlacao: str | None = Field(default=None, max_length=255)


class EventoMidiaArmazenamentoCreate(EventoMidiaArmazenamentoBase):
    pass


class EventoMidiaArmazenamentoOut(EventoMidiaArmazenamentoBase):
    id: int
    id_midia_armazenamento: int
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}
