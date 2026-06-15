from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import StatusMigracaoMidia
from app.schemas.midia_armazenamento import MidiaArmazenamentoCreate, MidiaArmazenamentoOut


class MigracaoMidiaIniciar(BaseModel):
    nova_midia: MidiaArmazenamentoCreate
    motivo_migracao: str = Field(..., min_length=3)
    procedimento_utilizado: str = Field(..., min_length=3)
    software_utilizado: str | None = None
    versao_software: str | None = None
    observacoes: str | None = None


class MigracaoMidiaUpdate(BaseModel):
    status: StatusMigracaoMidia | None = None
    motivo_migracao: str | None = None
    procedimento_utilizado: str | None = None
    software_utilizado: str | None = None
    versao_software: str | None = None
    observacoes: str | None = None
    relatorio_integridade_origem: str | None = None
    relatorio_integridade_destino: str | None = None


class MigracaoMidiaEtapaCreate(BaseModel):
    descricao: str = Field(..., min_length=3)
    resultado: str | None = None
    data: datetime | None = None
    evidencias: dict[str, Any] | None = None


class MigracaoMidiaRelatorioCreate(BaseModel):
    tipo: str = Field(..., min_length=2)
    referencia: str = Field(..., min_length=2)
    descricao: str | None = None


class MigracaoMidiaConclusao(BaseModel):
    resultado: StatusMigracaoMidia = StatusMigracaoMidia.CONCLUIDA
    observacoes: str | None = None
    relatorio_integridade_origem: str | None = None
    relatorio_integridade_destino: str | None = None


class MigracaoMidiaOut(BaseModel):
    id: uuid.UUID
    midia_origem_id: int
    midia_destino_id: int
    data_inicio: datetime
    data_conclusao: datetime | None = None
    usuario_responsavel_id: str | None = None
    status: StatusMigracaoMidia
    motivo_migracao: str
    procedimento_utilizado: str
    software_utilizado: str | None = None
    versao_software: str | None = None
    observacoes: str | None = None
    relatorio_integridade_origem: str | None = None
    relatorio_integridade_destino: str | None = None
    evento_id: int | None = None
    etapas: list[dict[str, Any]] = Field(default_factory=list)
    relatorios: list[dict[str, Any]] = Field(default_factory=list)
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None
    midia_origem: MidiaArmazenamentoOut | None = None
    midia_destino: MidiaArmazenamentoOut | None = None

    model_config = {"from_attributes": True}


class MigracaoMidiaPage(BaseModel):
    items: list[MigracaoMidiaOut]
    total: int
    limit: int
    offset: int
