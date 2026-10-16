import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class ExportacaoIn(BaseModel):
    operacao_id: uuid.UUID
    formato: Literal["CSV", "JSON", "PACOTE"] = "JSON"
    escopo: Literal["ADMINISTRATIVO", "PUBLICADO"] = "ADMINISTRATIVO"


class PoliticaIn(BaseModel):
    nome: str = Field(min_length=3, max_length=150)
    categoria: Literal["LOG_TECNICO", "ACESSO_CONSULTIVO", "EXPORTACAO", "SESSAO", "REGISTRO_EXCLUIDO"]
    dias: int = Field(ge=1, le=36500)
    instrumento_id: uuid.UUID | None = None
    ativo: bool = True
    permitir_expurgo: bool = False
    bloqueada: bool = False

    @model_validator(mode="after")
    def scope(self):
        self.nome = self.nome.strip()
        if len(self.nome) < 3:
            raise ValueError("Nome obrigatorio.")
        if (self.categoria == "REGISTRO_EXCLUIDO") != bool(self.instrumento_id):
            raise ValueError("Selecione um instrumento somente para registros excluidos.")
        return self


class RetencaoIn(BaseModel):
    operacao_id: uuid.UUID
    simulacao: bool = True


class ImpedimentoIn(BaseModel):
    bloqueado: bool = False
    reter_ate: datetime | None = None
