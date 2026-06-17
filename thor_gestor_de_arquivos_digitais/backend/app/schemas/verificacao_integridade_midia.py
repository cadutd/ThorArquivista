from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ResultadoVerificacaoIntegridade
from app.schemas.evento_preservacao import EventoPreservacaoOut
from app.schemas.midia_armazenamento import MidiaArmazenamentoOut


class VerificacaoIntegridadeManualCreate(BaseModel):
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    resultado: ResultadoVerificacaoIntegridade
    software_utilizado: str | None = Field(default=None, max_length=255)
    versao_software: str | None = Field(default=None, max_length=100)
    arquivo_relatorio_id: uuid.UUID | None = None
    total_aips_verificados: int = Field(default=0, ge=0)
    total_sucesso: int = Field(default=0, ge=0)
    total_falha: int = Field(default=0, ge=0)
    total_alerta: int = Field(default=0, ge=0)
    relatorio_json: dict[str, Any] = Field(default_factory=dict)
    observacoes: str | None = None


class VerificacaoIntegridadeImportarRelatorio(BaseModel):
    ferramenta: str | None = Field(default=None, max_length=255)
    versao: str | None = Field(default=None, max_length=100)
    relatorio_json: dict[str, Any]
    arquivo_relatorio_id: uuid.UUID | None = None
    observacoes: str | None = None


class VerificacaoIntegridadeOut(BaseModel):
    id: uuid.UUID
    midia_id: int
    data_inicio: datetime
    data_fim: datetime | None = None
    usuario_id: str | None = None
    resultado: ResultadoVerificacaoIntegridade
    software_utilizado: str | None = None
    versao_software: str | None = None
    arquivo_relatorio_id: uuid.UUID | None = None
    total_aips_verificados: int
    total_sucesso: int
    total_falha: int
    total_alerta: int
    relatorio_json: dict[str, Any]
    observacoes: str | None = None
    evento_id: int | None = None
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}


class VerificacaoIntegridadePage(BaseModel):
    items: list[VerificacaoIntegridadeOut]
    total: int
    limit: int
    offset: int


class IntegridadePainelOut(BaseModel):
    validade_vencida: list[MidiaArmazenamentoOut]
    checagem_vencida: list[MidiaArmazenamentoOut]
    proximas_vencimento: list[MidiaArmazenamentoOut]
    falha_ultima_checagem: list[MidiaArmazenamentoOut]
    sem_checagem: list[MidiaArmazenamentoOut]
    com_alerta: list[MidiaArmazenamentoOut]


class IntegridadeResumoOut(BaseModel):
    validade_vencida: int
    checagem_vencida: int
    proximas_vencimento: int
    falha_ultima_checagem: int
    sem_checagem: int
    com_alerta: int


class VerificacaoIntegridadeDetalheOut(VerificacaoIntegridadeOut):
    eventos_unidades: list[EventoPreservacaoOut] = Field(default_factory=list)
