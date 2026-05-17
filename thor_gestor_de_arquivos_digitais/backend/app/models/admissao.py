from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import (
    Boolean,
    BigInteger,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoSuporte


class TipoProcessoAdmissao(str, Enum):
    FECHADO = "FECHADO"
    CONTINUO = "CONTINUO"


class TipoIngressoAdmissao(str, Enum):
    TRANSFERENCIA = "TRANSFERENCIA"
    RECOLHIMENTO = "RECOLHIMENTO"
    DOACAO = "DOACAO"
    AQUISICAO = "AQUISICAO"
    INCORPORACAO = "INCORPORACAO"
    REGULARIZACAO_LEGADO = "REGULARIZACAO_LEGADO"
    OUTRO = "OUTRO"


class StatusProcessoAdmissao(str, Enum):
    ABERTO = "ABERTO"
    EM_NEGOCIACAO = "EM_NEGOCIACAO"
    EM_RECEBIMENTO = "EM_RECEBIMENTO"
    EM_QUARENTENA = "EM_QUARENTENA"
    EM_VALIDACAO = "EM_VALIDACAO"
    PENDENTE_COMPLEMENTACAO = "PENDENTE_COMPLEMENTACAO"
    EM_GERACAO_AIP = "EM_GERACAO_AIP"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"
    REJEITADO = "REJEITADO"


class ResultadoFinalAdmissao(str, Enum):
    ADMITIDO = "ADMITIDO"
    ADMITIDO_COM_RESSALVA = "ADMITIDO_COM_RESSALVA"
    REJEITADO = "REJEITADO"
    CANCELADO = "CANCELADO"


class TipoReuniaoAdmissao(str, Enum):
    NEGOCIACAO_INICIAL = "NEGOCIACAO_INICIAL"
    ALINHAMENTO_TECNICO = "ALINHAMENTO_TECNICO"
    VALIDACAO_SIP = "VALIDACAO_SIP"
    REVISAO_ACORDO = "REVISAO_ACORDO"
    TRATAMENTO_DIVERGENCIA = "TRATAMENTO_DIVERGENCIA"
    HOMOLOGACAO = "HOMOLOGACAO"
    ENCERRAMENTO = "ENCERRAMENTO"
    OUTRO = "OUTRO"


class StatusAcordoAdmissao(str, Enum):
    RASCUNHO = "RASCUNHO"
    EM_ANALISE = "EM_ANALISE"
    ATIVO = "ATIVO"
    SUSPENSO = "SUSPENSO"
    ENCERRADO = "ENCERRADO"


class CanalSubmissao(str, Enum):
    UPLOAD = "UPLOAD"
    API = "API"
    REDE_INTERNA = "REDE_INTERNA"
    MIDIA_REMOVIVEL = "MIDIA_REMOVIVEL"
    ENTREGA_FISICA = "ENTREGA_FISICA"
    IMPORTACAO_SISTEMA = "IMPORTACAO_SISTEMA"
    OUTRO = "OUTRO"


class StatusSessaoSubmissao(str, Enum):
    INICIADA = "INICIADA"
    EM_TRANSFERENCIA = "EM_TRANSFERENCIA"
    RECEBIDA = "RECEBIDA"
    EM_QUARENTENA = "EM_QUARENTENA"
    EM_VALIDACAO = "EM_VALIDACAO"
    VALIDADA = "VALIDADA"
    REJEITADA = "REJEITADA"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


class StatusSipAdmissao(str, Enum):
    RECEBIDO = "RECEBIDO"
    EM_QUARENTENA = "EM_QUARENTENA"
    EM_VALIDACAO = "EM_VALIDACAO"
    VALIDADO = "VALIDADO"
    VALIDADO_COM_RESSALVA = "VALIDADO_COM_RESSALVA"
    REJEITADO = "REJEITADO"
    TRANSFORMADO_EM_AIP = "TRANSFORMADO_EM_AIP"


class TipoEventoAdmissao(str, Enum):
    CRIACAO_PROCESSO = "CRIACAO_PROCESSO"
    REUNIAO_ADMISSAO = "REUNIAO_ADMISSAO"
    CRIACAO_VERSAO_ACORDO = "CRIACAO_VERSAO_ACORDO"
    ATIVACAO_ACORDO = "ATIVACAO_ACORDO"
    INICIO_SESSAO = "INICIO_SESSAO"
    RECEBIMENTO_SIP = "RECEBIMENTO_SIP"
    APROVACAO = "APROVACAO"
    REJEICAO = "REJEICAO"
    GERACAO_AIP = "GERACAO_AIP"
    ENCERRAMENTO_PROCESSO = "ENCERRAMENTO_PROCESSO"
    CANCELAMENTO_PROCESSO = "CANCELAMENTO_PROCESSO"


class ResultadoEventoAdmissao(str, Enum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"
    ALERTA = "ALERTA"
    PENDENTE = "PENDENTE"
    INFORMATIVO = "INFORMATIVO"


class TipoRelacaoSipAip(str, Enum):
    ORIGEM_TOTAL = "ORIGEM_TOTAL"
    ORIGEM_PARCIAL = "ORIGEM_PARCIAL"
    COMPLEMENTACAO = "COMPLEMENTACAO"
    CORRECAO = "CORRECAO"
    REPROCESSAMENTO = "REPROCESSAMENTO"


class ProcessoAdmissao(Base):
    __tablename__ = "processos_admissao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_processo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    id_instituicao_arquivo: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instituicao_arquivo.id"), nullable=False, index=True)
    id_entidade_produtora: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades_produtoras.id"), nullable=False, index=True)
    tipo_processo_admissao: Mapped[TipoProcessoAdmissao] = mapped_column(SAEnum(TipoProcessoAdmissao), nullable=False, index=True)
    tipo_ingresso: Mapped[TipoIngressoAdmissao] = mapped_column(SAEnum(TipoIngressoAdmissao), nullable=False, index=True)
    tipo_suporte: Mapped[TipoSuporte] = mapped_column(SAEnum(TipoSuporte), nullable=False, index=True)
    data_inicio: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    data_fim_prevista: Mapped[Date | None] = mapped_column(Date)
    data_encerramento: Mapped[Date | None] = mapped_column(Date)
    processo_ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    admissoes_recorrentes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[StatusProcessoAdmissao] = mapped_column(SAEnum(StatusProcessoAdmissao), nullable=False, default=StatusProcessoAdmissao.ABERTO, index=True)
    resultado_final: Mapped[ResultadoFinalAdmissao | None] = mapped_column(SAEnum(ResultadoFinalAdmissao))
    id_descricao_arquivistica: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("registros_descritivos.id"), index=True)
    codigo_classificacao: Mapped[str | None] = mapped_column(String(100))
    codigo_classificacao_descricao: Mapped[str | None] = mapped_column(String(255))
    restricao_acesso: Mapped[str | None] = mapped_column(String(255))
    hipotese_legal_restricao: Mapped[str | None] = mapped_column(String(255))
    volume_estimado: Mapped[str | None] = mapped_column(String(100))
    volume_recebido: Mapped[str | None] = mapped_column(String(100))
    quantidade_unidades_estimadas: Mapped[int | None] = mapped_column(Integer)
    quantidade_unidades_recebidas: Mapped[int | None] = mapped_column(Integer)
    observacoes: Mapped[str | None] = mapped_column(Text)
    parecer_final: Mapped[str | None] = mapped_column(Text)
    criado_por: Mapped[str | None] = mapped_column(String(255))
    atualizado_por: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    instituicao_arquivo = relationship("InstituicaoArquivo")
    entidade_produtora = relationship("EntidadeProdutora")
    descricao_arquivistica = relationship("RegistroDescritivo")
    reunioes = relationship("ReuniaoAdmissao", back_populates="processo", cascade="all, delete-orphan")
    acordos = relationship("AcordoAdmissao", back_populates="processo", cascade="all, delete-orphan")
    sessoes = relationship("SessaoSubmissao", back_populates="processo", cascade="all, delete-orphan")
    sips = relationship("SipAdmissao", back_populates="processo", cascade="all, delete-orphan")
    eventos = relationship("EventoAdmissao", back_populates="processo", cascade="all, delete-orphan")


class ReuniaoAdmissao(Base):
    __tablename__ = "reunioes_admissao"
    __table_args__ = (UniqueConstraint("id_processo_admissao", "numero_reuniao", name="uq_reuniao_admissao_numero"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_processo_admissao: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("processos_admissao.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_reuniao: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo_reuniao: Mapped[TipoReuniaoAdmissao] = mapped_column(SAEnum(TipoReuniaoAdmissao), nullable=False, index=True)
    data_reuniao: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    participantes: Mapped[str | None] = mapped_column(Text)
    deliberacoes: Mapped[str | None] = mapped_column(Text)
    pendencias: Mapped[str | None] = mapped_column(Text)
    proximos_passos: Mapped[str | None] = mapped_column(Text)
    ata_documento: Mapped[str | None] = mapped_column(String(500))
    criado_por: Mapped[str | None] = mapped_column(String(255))
    atualizado_por: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    processo = relationship("ProcessoAdmissao", back_populates="reunioes")


class AcordoAdmissao(Base):
    __tablename__ = "acordos_admissao"
    __table_args__ = (UniqueConstraint("id_processo_admissao", "numero_versao", name="uq_acordo_admissao_versao"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_processo_admissao: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("processos_admissao.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_versao: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusAcordoAdmissao] = mapped_column(SAEnum(StatusAcordoAdmissao), nullable=False, default=StatusAcordoAdmissao.RASCUNHO, index=True)
    data_inicio_vigencia: Mapped[Date | None] = mapped_column(Date)
    data_fim_vigencia: Mapped[Date | None] = mapped_column(Date)
    motivo_revisao: Mapped[str | None] = mapped_column(Text)
    regras_empacotamento: Mapped[str | None] = mapped_column(Text)
    regras_nomenclatura: Mapped[str | None] = mapped_column(Text)
    formatos_aceitos: Mapped[str | None] = mapped_column(Text)
    metadados_obrigatorios: Mapped[str | None] = mapped_column(Text)
    requisitos_fixidez: Mapped[str | None] = mapped_column(Text)
    requisitos_representacao: Mapped[str | None] = mapped_column(Text)
    politica_validacao: Mapped[str | None] = mapped_column(Text)
    politica_rejeicao: Mapped[str | None] = mapped_column(Text)
    politica_normalizacao: Mapped[str | None] = mapped_column(Text)
    politica_sigilo: Mapped[str | None] = mapped_column(Text)
    periodicidade_submissao: Mapped[str | None] = mapped_column(String(100))
    observacoes: Mapped[str | None] = mapped_column(Text)
    documento_acordo: Mapped[str | None] = mapped_column(String(500))
    criado_por: Mapped[str | None] = mapped_column(String(255))
    atualizado_por: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    processo = relationship("ProcessoAdmissao", back_populates="acordos")
    sessoes = relationship("SessaoSubmissao", back_populates="acordo")


class SessaoSubmissao(Base):
    __tablename__ = "sessoes_submissao"
    __table_args__ = (UniqueConstraint("id_processo_admissao", "numero_sessao", name="uq_sessao_submissao_numero"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_processo_admissao: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("processos_admissao.id", ondelete="CASCADE"), nullable=False, index=True)
    id_acordo_utilizado: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("acordos_admissao.id"), nullable=False, index=True)
    numero_sessao: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    data_inicio: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_fim: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    canal_submissao: Mapped[CanalSubmissao] = mapped_column(SAEnum(CanalSubmissao), nullable=False, index=True)
    protocolo_transferencia: Mapped[str | None] = mapped_column(String(255))
    responsavel_envio: Mapped[str | None] = mapped_column(String(255))
    responsavel_recebimento: Mapped[str | None] = mapped_column(String(255))
    tipo_suporte: Mapped[TipoSuporte] = mapped_column(SAEnum(TipoSuporte), nullable=False, index=True)
    volume_informado: Mapped[str | None] = mapped_column(String(100))
    volume_recebido: Mapped[str | None] = mapped_column(String(100))
    quantidade_itens_informada: Mapped[int | None] = mapped_column(Integer)
    quantidade_itens_recebida: Mapped[int | None] = mapped_column(Integer)
    caminho_origem: Mapped[str | None] = mapped_column(String(500))
    caminho_destino_quarentena: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[StatusSessaoSubmissao] = mapped_column(SAEnum(StatusSessaoSubmissao), nullable=False, default=StatusSessaoSubmissao.INICIADA, index=True)
    resultado_validacao: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_por: Mapped[str | None] = mapped_column(String(255))
    atualizado_por: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    processo = relationship("ProcessoAdmissao", back_populates="sessoes")
    acordo = relationship("AcordoAdmissao", back_populates="sessoes")
    sips = relationship("SipAdmissao", back_populates="sessao", cascade="all, delete-orphan")


class SipAdmissao(Base):
    __tablename__ = "sips_admissao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_processo_admissao: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("processos_admissao.id", ondelete="CASCADE"), nullable=False, index=True)
    id_sessao_submissao: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessoes_submissao.id", ondelete="CASCADE"), nullable=False, index=True)
    codigo_sip: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo_sip: Mapped[TipoSuporte] = mapped_column(SAEnum(TipoSuporte), nullable=False, index=True)
    status: Mapped[StatusSipAdmissao] = mapped_column(SAEnum(StatusSipAdmissao), nullable=False, default=StatusSipAdmissao.RECEBIDO, index=True)
    data_recebimento: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    estrutura_original: Mapped[str | None] = mapped_column(Text)
    caminho_armazenamento_temporario: Mapped[str | None] = mapped_column(String(500))
    manifesto_arquivos: Mapped[str | None] = mapped_column(Text)
    algoritmo_hash: Mapped[str | None] = mapped_column(String(50))
    hash_global: Mapped[str | None] = mapped_column(String(255))
    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)
    quantidade_arquivos: Mapped[int | None] = mapped_column(Integer)
    quantidade_unidades_fisicas: Mapped[int | None] = mapped_column(Integer)
    resultado_validacao: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_por: Mapped[str | None] = mapped_column(String(255))
    atualizado_por: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    processo = relationship("ProcessoAdmissao", back_populates="sips")
    sessao = relationship("SessaoSubmissao", back_populates="sips")


class RelacaoSipAip(Base):
    __tablename__ = "relacoes_sip_aip"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_sip: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sips_admissao.id", ondelete="CASCADE"), nullable=False, index=True)
    id_unidade_acondicionamento: Mapped[int] = mapped_column(ForeignKey("unidades_acondicionamento.id"), nullable=False, index=True)
    tipo_relacao: Mapped[TipoRelacaoSipAip] = mapped_column(SAEnum(TipoRelacaoSipAip), nullable=False, default=TipoRelacaoSipAip.ORIGEM_TOTAL)
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_por: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    sip = relationship("SipAdmissao")
    unidade_acondicionamento = relationship("UnidadeAcondicionamento")


class EventoAdmissao(Base):
    __tablename__ = "eventos_admissao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_processo_admissao: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("processos_admissao.id", ondelete="CASCADE"), nullable=False, index=True)
    id_sessao_submissao: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sessoes_submissao.id", ondelete="SET NULL"), index=True)
    id_sip: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sips_admissao.id", ondelete="SET NULL"), index=True)
    id_unidade_acondicionamento: Mapped[int | None] = mapped_column(ForeignKey("unidades_acondicionamento.id", ondelete="SET NULL"), index=True)
    tipo_evento: Mapped[TipoEventoAdmissao] = mapped_column(SAEnum(TipoEventoAdmissao), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[ResultadoEventoAdmissao] = mapped_column(SAEnum(ResultadoEventoAdmissao), nullable=False, default=ResultadoEventoAdmissao.INFORMATIVO, index=True)
    agente: Mapped[str | None] = mapped_column(String(255))
    data_evento: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    detalhe_tecnico: Mapped[str | None] = mapped_column(Text)
    evidencia: Mapped[str | None] = mapped_column(String(500))
    criado_por: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    processo = relationship("ProcessoAdmissao", back_populates="eventos")
