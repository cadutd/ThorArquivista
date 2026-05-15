from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import TipoSuporte, TipoUnidade, NivelAcesso, StatusUnidade

# Se você já tiver schemas próprios para digital e cópia, importe aqui.
# Se ainda não tiver, pode comentar essas linhas e manter digital/copias_digitais fora do Out.
from app.schemas.unidade_acondicionamento_digital import UnidadeAcondicionamentoDigitalOut
from app.schemas.copia_unidade_acondicionamento_digital import CopiaUnidadeAcondicionamentoDigitalOut


class UnidadeAcondicionamentoBase(BaseModel):
    """
    Campos alinhados ao model UnidadeAcondicionamento.
    """
    model_config = ConfigDict(use_enum_values=True)

    identificador: str = Field(..., max_length=255)
    titulo: str = Field(..., max_length=500)
    descricao: str | None = Field(default=None, max_length=2000)
    produtor: str | None = Field(default=None, max_length=255)
    unidade: str | None = Field(default=None, max_length=255)
    data_limite: str | None = Field(default=None, max_length=255)
    codigo_classificacao: str | None = Field(default=None, max_length=255)
    assunto: str | None = Field(default=None, max_length=500)
    codigo_barra: str | None = Field(default=None, max_length=128)
    informacoes_pacote: str | None = None

    tipo_suporte: TipoSuporte
    tipo_unidade: TipoUnidade

    nivel_acesso: NivelAcesso = NivelAcesso.RESTRITO
    status: StatusUnidade = StatusUnidade.ATIVA

    id_unidade_pai: int | None = None
    id_representa: int | None = None


class UnidadeAcondicionamentoCreate(UnidadeAcondicionamentoBase):
    """
    Create é igual ao Base.
    Se futuramente você permitir criar também a extensão digital no mesmo POST,
    você pode adicionar aqui:
      digital: UnidadeAcondicionamentoDigitalCreate | None = None
    """
    pass


class UnidadeAcondicionamentoUpdate(BaseModel):
    """
    Update parcial.
    Mantém apenas campos que existem no model e que fazem sentido atualizar via PATCH/PUT.
    """
    model_config = ConfigDict(use_enum_values=True)

    identificador: str | None = Field(default=None, max_length=255)
    titulo: str | None = Field(default=None, max_length=500)
    descricao: str | None = Field(default=None, max_length=2000)
    produtor: str | None = Field(default=None, max_length=255)
    unidade: str | None = Field(default=None, max_length=255)
    data_limite: str | None = Field(default=None, max_length=255)
    codigo_classificacao: str | None = Field(default=None, max_length=255)
    assunto: str | None = Field(default=None, max_length=500)
    codigo_barra: str | None = Field(default=None, max_length=128)
    informacoes_pacote: str | None = None

    tipo_suporte: TipoSuporte | None = None
    tipo_unidade: TipoUnidade | None = None

    nivel_acesso: NivelAcesso | None = None
    status: StatusUnidade | None = None

    id_unidade_pai: int | None = None
    id_representa: int | None = None


class UnidadeAcondicionamentoOut(UnidadeAcondicionamentoBase):
    """
    Saída (read).
    Inclui auditoria e permite (opcionalmente) expor relações definidas no model:
      - digital (1:1)
      - copias_digitais (1:N)
    """
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    id_posicao_armazenamento: int | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    # Relacionamentos do model (opcionais na resposta)
    digital: UnidadeAcondicionamentoDigitalOut | None = None
    copias_digitais: list[CopiaUnidadeAcondicionamentoDigitalOut] = Field(default_factory=list)


class UnidadeAcondicionamentoPage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[UnidadeAcondicionamentoOut]
    total: int
    limit: int
    offset: int
