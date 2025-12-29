# app/models/enums.py
from enum import Enum


class TipoSuporte(str, Enum):
    FISICO = "fisico"
    DIGITAL = "digital"
    HIBRIDO = "hibrido"


class TipoUnidade(str, Enum):
    CAIXA = "caixa"
    PASTA = "pasta"
    VOLUME = "volume"
    AIP = "aip"
    SIP = "sip"
    DIP = "dip"


class NivelAcesso(str, Enum):
    PUBLICO = "publico"
    RESTRITO = "restrito"
    CONFIDENCIAL = "confidencial"


class StatusUnidade(str, Enum):
    ATIVA = "ativa"
    INATIVA = "inativa"
    TRANSFERIDA = "transferida"
    ELIMINADA = "eliminada"


class TipoMidiaArmazenamento(str, Enum):
    FILESYSTEM = "filesystem"
    NAS = "nas"
    NFS = "nfs"
    LTO = "lto"
    S3 = "s3"
    CLOUD = "cloud"

class FuncaoCopia(str, Enum):
    PRESERVACAO = "preservacao"
    BACKUP = "backup"
    ACESSO = "acesso"
    QUARENTENA = "quarentena"

class StatusCopia(str, Enum):
    ATIVA = "ativa"
    INDISPONIVEL = "indisponivel"
    CORROMPIDA = "corrompida"
    EM_VERIFICACAO = "em_verificacao"

class TipoEventoPreservacao(str, Enum):
    INGESTAO = "ingestao"
    VALIDACAO = "validacao"
    FIXIDEZ = "fixidez"
    REPLICACAO = "replicacao"
    MIGRACAO = "migracao"
    ACESSO = "acesso"
    MOVIMENTACAO = "movimentacao"
    OUTRO = "outro"

class ResultadoEventoPreservacao(str, Enum):
    SUCESSO = "sucesso"
    FALHA = "falha"
    ALERTA = "alerta"
    INDETERMINADO = "indeterminado"
