from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.admissao import (
    CanalSubmissao,
    ResultadoEventoAdmissao,
    ResultadoFinalAdmissao,
    StatusAcordoAdmissao,
    StatusProcessoAdmissao,
    StatusSessaoSubmissao,
    StatusSipAdmissao,
    TipoEventoAdmissao,
    TipoIngressoAdmissao,
    TipoProcessoAdmissao,
    TipoRelacaoSipAip,
    TipoReuniaoAdmissao,
)
from app.models.enums import TipoSuporte


class ProcessoAdmissaoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    numero_processo: str = Field(..., min_length=1, max_length=100)
    titulo: str = Field(..., min_length=1, max_length=255)
    descricao: str | None = None
    id_instituicao_arquivo: uuid.UUID
    id_entidade_produtora: uuid.UUID
    nome_usuario_responsavel: str | None = Field(default=None, max_length=255)
    tipo_processo_admissao: TipoProcessoAdmissao
    tipo_ingresso: TipoIngressoAdmissao
    tipo_suporte: TipoSuporte
    data_inicio: date
    data_fim_prevista: date | None = None
    data_encerramento: date | None = None
    processo_ativo: bool = True
    admissoes_recorrentes: bool = False
    status: StatusProcessoAdmissao = StatusProcessoAdmissao.ABERTO
    resultado_final: ResultadoFinalAdmissao | None = None
    id_descricao_arquivistica: uuid.UUID | None = None
    codigo_classificacao: str | None = Field(default=None, max_length=100)
    codigo_classificacao_descricao: str | None = Field(default=None, max_length=255)
    restricao_acesso: str | None = Field(default=None, max_length=255)
    hipotese_legal_restricao: str | None = Field(default=None, max_length=255)
    volume_estimado: str | None = Field(default=None, max_length=100)
    volume_recebido: str | None = Field(default=None, max_length=100)
    quantidade_unidades_estimadas: int | None = Field(default=None, ge=0)
    quantidade_unidades_recebidas: int | None = Field(default=None, ge=0)
    observacoes: str | None = None
    parecer_final: str | None = None
    criado_por: str | None = Field(default=None, max_length=255)
    atualizado_por: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validar_datas(self):
        if self.data_fim_prevista and self.data_fim_prevista < self.data_inicio:
            raise ValueError("data_fim_prevista não pode ser anterior a data_inicio.")
        if self.data_encerramento and self.data_encerramento < self.data_inicio:
            raise ValueError("data_encerramento não pode ser anterior a data_inicio.")
        return self


class ProcessoAdmissaoCreate(ProcessoAdmissaoBase):
    pass


class ProcessoAdmissaoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    numero_processo: str | None = Field(default=None, min_length=1, max_length=100)
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descricao: str | None = None
    id_instituicao_arquivo: uuid.UUID | None = None
    id_entidade_produtora: uuid.UUID | None = None
    nome_usuario_responsavel: str | None = Field(default=None, max_length=255)
    tipo_processo_admissao: TipoProcessoAdmissao | None = None
    tipo_ingresso: TipoIngressoAdmissao | None = None
    tipo_suporte: TipoSuporte | None = None
    data_inicio: date | None = None
    data_fim_prevista: date | None = None
    data_encerramento: date | None = None
    processo_ativo: bool | None = None
    admissoes_recorrentes: bool | None = None
    status: StatusProcessoAdmissao | None = None
    resultado_final: ResultadoFinalAdmissao | None = None
    id_descricao_arquivistica: uuid.UUID | None = None
    codigo_classificacao: str | None = Field(default=None, max_length=100)
    codigo_classificacao_descricao: str | None = Field(default=None, max_length=255)
    restricao_acesso: str | None = Field(default=None, max_length=255)
    hipotese_legal_restricao: str | None = Field(default=None, max_length=255)
    volume_estimado: str | None = Field(default=None, max_length=100)
    volume_recebido: str | None = Field(default=None, max_length=100)
    quantidade_unidades_estimadas: int | None = Field(default=None, ge=0)
    quantidade_unidades_recebidas: int | None = Field(default=None, ge=0)
    observacoes: str | None = None
    parecer_final: str | None = None
    atualizado_por: str | None = Field(default=None, max_length=255)


class ProcessoAdmissaoRead(ProcessoAdmissaoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    criado_em: datetime
    atualizado_em: datetime
    nome_instituicao_arquivo: str | None = None
    nome_entidade_produtora: str | None = None
    titulo_descricao_arquivistica: str | None = None


class ProcessoAdmissaoList(BaseModel):
    items: list[ProcessoAdmissaoRead]
    total: int
    limit: int
    offset: int


class ReuniaoAdmissaoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    numero_reuniao: int | None = Field(default=None, ge=1)
    titulo: str = Field(..., min_length=1, max_length=255)
    descricao: str | None = None
    tipo_reuniao: TipoReuniaoAdmissao
    data_reuniao: datetime
    participantes: str | None = None
    deliberacoes: str | None = None
    pendencias: str | None = None
    proximos_passos: str | None = None
    criado_por: str | None = Field(default=None, max_length=255)
    atualizado_por: str | None = Field(default=None, max_length=255)


class ReuniaoAdmissaoCreate(ReuniaoAdmissaoBase):
    pass


class ReuniaoAdmissaoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descricao: str | None = None
    tipo_reuniao: TipoReuniaoAdmissao | None = None
    data_reuniao: datetime | None = None
    participantes: str | None = None
    deliberacoes: str | None = None
    pendencias: str | None = None
    proximos_passos: str | None = None
    atualizado_por: str | None = Field(default=None, max_length=255)


class ReuniaoAdmissaoRead(ReuniaoAdmissaoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    id_processo_admissao: uuid.UUID
    numero_reuniao: int
    criado_em: datetime
    atualizado_em: datetime


class AcordoAdmissaoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    numero_versao: int | None = Field(default=None, ge=1)
    titulo: str = Field(..., min_length=1, max_length=255)
    descricao: str | None = None
    status: StatusAcordoAdmissao = StatusAcordoAdmissao.RASCUNHO
    data_inicio_vigencia: date | None = None
    data_fim_vigencia: date | None = None
    motivo_revisao: str | None = None
    regras_empacotamento: str | None = None
    regras_nomenclatura: str | None = None
    formatos_aceitos: str | None = None
    metadados_obrigatorios: str | None = None
    requisitos_fixidez: str | None = None
    requisitos_representacao: str | None = None
    politica_validacao: str | None = None
    politica_rejeicao: str | None = None
    politica_normalizacao: str | None = None
    politica_sigilo: str | None = None
    periodicidade_submissao: str | None = Field(default=None, max_length=100)
    observacoes: str | None = None
    documento_acordo: str | None = Field(default=None, max_length=500)
    criado_por: str | None = Field(default=None, max_length=255)
    atualizado_por: str | None = Field(default=None, max_length=255)


class AcordoAdmissaoCreate(AcordoAdmissaoBase):
    pass


class AcordoAdmissaoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descricao: str | None = None
    status: StatusAcordoAdmissao | None = None
    data_inicio_vigencia: date | None = None
    data_fim_vigencia: date | None = None
    motivo_revisao: str | None = None
    regras_empacotamento: str | None = None
    regras_nomenclatura: str | None = None
    formatos_aceitos: str | None = None
    metadados_obrigatorios: str | None = None
    requisitos_fixidez: str | None = None
    requisitos_representacao: str | None = None
    politica_validacao: str | None = None
    politica_rejeicao: str | None = None
    politica_normalizacao: str | None = None
    politica_sigilo: str | None = None
    periodicidade_submissao: str | None = Field(default=None, max_length=100)
    observacoes: str | None = None
    documento_acordo: str | None = Field(default=None, max_length=500)
    atualizado_por: str | None = Field(default=None, max_length=255)


class AcordoAdmissaoRead(AcordoAdmissaoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    id_processo_admissao: uuid.UUID
    numero_versao: int
    criado_em: datetime
    atualizado_em: datetime


class SessaoSubmissaoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_acordo_utilizado: uuid.UUID
    numero_sessao: int | None = Field(default=None, ge=1)
    titulo: str = Field(..., min_length=1, max_length=255)
    descricao: str | None = None
    data_inicio: datetime
    data_fim: datetime | None = None
    canal_submissao: CanalSubmissao
    protocolo_transferencia: str | None = Field(default=None, max_length=255)
    responsavel_envio: str | None = Field(default=None, max_length=255)
    responsavel_recebimento: str | None = Field(default=None, max_length=255)
    tipo_suporte: TipoSuporte
    volume_informado: str | None = Field(default=None, max_length=100)
    volume_recebido: str | None = Field(default=None, max_length=100)
    quantidade_itens_informada: int | None = Field(default=None, ge=0)
    quantidade_itens_recebida: int | None = Field(default=None, ge=0)
    caminho_origem: str | None = Field(default=None, max_length=500)
    caminho_destino_quarentena: str | None = Field(default=None, max_length=500)
    status: StatusSessaoSubmissao = StatusSessaoSubmissao.INICIADA
    resultado_validacao: str | None = None
    observacoes: str | None = None
    criado_por: str | None = Field(default=None, max_length=255)
    atualizado_por: str | None = Field(default=None, max_length=255)


class SessaoSubmissaoCreate(SessaoSubmissaoBase):
    pass


class SessaoSubmissaoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_acordo_utilizado: uuid.UUID | None = None
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descricao: str | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    canal_submissao: CanalSubmissao | None = None
    protocolo_transferencia: str | None = Field(default=None, max_length=255)
    responsavel_envio: str | None = Field(default=None, max_length=255)
    responsavel_recebimento: str | None = Field(default=None, max_length=255)
    tipo_suporte: TipoSuporte | None = None
    volume_informado: str | None = Field(default=None, max_length=100)
    volume_recebido: str | None = Field(default=None, max_length=100)
    quantidade_itens_informada: int | None = Field(default=None, ge=0)
    quantidade_itens_recebida: int | None = Field(default=None, ge=0)
    caminho_origem: str | None = Field(default=None, max_length=500)
    caminho_destino_quarentena: str | None = Field(default=None, max_length=500)
    status: StatusSessaoSubmissao | None = None
    resultado_validacao: str | None = None
    observacoes: str | None = None
    atualizado_por: str | None = Field(default=None, max_length=255)


class SessaoSubmissaoRead(SessaoSubmissaoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    id_processo_admissao: uuid.UUID
    numero_sessao: int
    criado_em: datetime
    atualizado_em: datetime


class SipAdmissaoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    codigo_sip: str = Field(..., min_length=1, max_length=100)
    titulo: str = Field(..., min_length=1, max_length=255)
    descricao: str | None = None
    tipo_sip: TipoSuporte
    status: StatusSipAdmissao = StatusSipAdmissao.RECEBIDO
    data_recebimento: datetime
    estrutura_original: str | None = None
    caminho_armazenamento_temporario: str | None = Field(default=None, max_length=500)
    manifesto_arquivos: str | None = None
    algoritmo_hash: str | None = Field(default=None, max_length=50)
    hash_global: str | None = Field(default=None, max_length=255)
    tamanho_bytes: int | None = Field(default=None, ge=0)
    quantidade_arquivos: int | None = Field(default=None, ge=0)
    quantidade_unidades_fisicas: int | None = Field(default=None, ge=0)
    resultado_validacao: str | None = None
    observacoes: str | None = None
    criado_por: str | None = Field(default=None, max_length=255)
    atualizado_por: str | None = Field(default=None, max_length=255)


class SipAdmissaoCreate(SipAdmissaoBase):
    pass


class SipAdmissaoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    codigo_sip: str | None = Field(default=None, min_length=1, max_length=100)
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descricao: str | None = None
    tipo_sip: TipoSuporte | None = None
    status: StatusSipAdmissao | None = None
    data_recebimento: datetime | None = None
    estrutura_original: str | None = None
    caminho_armazenamento_temporario: str | None = Field(default=None, max_length=500)
    manifesto_arquivos: str | None = None
    algoritmo_hash: str | None = Field(default=None, max_length=50)
    hash_global: str | None = Field(default=None, max_length=255)
    tamanho_bytes: int | None = Field(default=None, ge=0)
    quantidade_arquivos: int | None = Field(default=None, ge=0)
    quantidade_unidades_fisicas: int | None = Field(default=None, ge=0)
    resultado_validacao: str | None = None
    observacoes: str | None = None
    atualizado_por: str | None = Field(default=None, max_length=255)


class SipAdmissaoRead(SipAdmissaoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    id_processo_admissao: uuid.UUID
    id_sessao_submissao: uuid.UUID
    criado_em: datetime
    atualizado_em: datetime


class EventoAdmissaoCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_sessao_submissao: uuid.UUID | None = None
    id_sip: uuid.UUID | None = None
    id_unidade_acondicionamento: int | None = None
    tipo_evento: TipoEventoAdmissao
    descricao: str = Field(..., min_length=1)
    resultado: ResultadoEventoAdmissao = ResultadoEventoAdmissao.INFORMATIVO
    agente: str | None = Field(default=None, max_length=255)
    data_evento: datetime | None = None
    detalhe_tecnico: str | None = None
    evidencia: str | None = Field(default=None, max_length=500)
    criado_por: str | None = Field(default=None, max_length=255)


class EventoAdmissaoRead(EventoAdmissaoCreate):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    id_processo_admissao: uuid.UUID
    data_evento: datetime
    criado_em: datetime


class RelacaoSipAipCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_unidade_acondicionamento: int
    tipo_relacao: TipoRelacaoSipAip = TipoRelacaoSipAip.ORIGEM_TOTAL
    observacoes: str | None = None
    criado_por: str | None = Field(default=None, max_length=255)


class RelacaoSipAipRead(RelacaoSipAipCreate):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    id_sip: uuid.UUID
    criado_em: datetime
