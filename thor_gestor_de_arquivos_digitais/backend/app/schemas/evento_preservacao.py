from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import TipoEventoPreservacao, ResultadoEventoPreservacao


class EventoPreservacaoBase(BaseModel):
    tipo_evento: TipoEventoPreservacao
    resultado: ResultadoEventoPreservacao = ResultadoEventoPreservacao.SUCESSO
    detalhe: str | None = None
    agente: str | None = Field(default=None, max_length=255)
    correlacao: str | None = Field(default=None, max_length=255)


class EventoPreservacaoCreate(EventoPreservacaoBase):
    pass


class EventoPreservacaoOut(EventoPreservacaoBase):
    id: int
    id_unidade_acondicionamento: int
    criado_em: str | None = None

    model_config = {"from_attributes": True}
