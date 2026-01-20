from enum import Enum


class TipoSuporte(str, Enum):
    FISICO = "FISICO"
    DIGITAL = "DIGITAL"
    HIBRIDO = "HIBRIDO"


class TipoUnidade(str, Enum):
    CAIXA = "CAIXA"
    PASTA = "PASTA"
    VOLUME = "VOLUME"
    AIP = "AIP"
    SIP = "SIP"
    DIP = "DIP"


class NivelAcesso(str, Enum):
    PUBLICO = "PUBLICO"
    RESTRITO = "RESTRITO"
    CONFIDENCIAL = "CONFIDENCIAL"


class StatusUnidade(str, Enum):
    ATIVA = "ATIVA"
    INATIVA = "INATIVA"
    TRANSFERIDA = "TRANSFERIDA"
    ELIMINADA = "ELIMINADA"


class TipoMidiaArmazenamento(str, Enum):
    FILESYSTEM = "FILESYSTEM"
    NAS = "NAS"
    NFS = "NFS"
    LTO = "LTO"
    S3 = "S3"
    CLOUD = "CLOUD"


class FuncaoCopia(str, Enum):
    PRESERVACAO = "PRESERVACAO"
    BACKUP = "BACKUP"
    ACESSO = "ACESSO"
    QUARENTENA = "QUARENTENA"


class StatusCopia(str, Enum):
    ATIVA = "ATIVA"
    INDISPONIVEL = "INDISPONIVEL"
    CORROMPIDA = "CORROMPIDA"
    EM_VERIFICACAO = "EM_VERIFICACAO"


class TipoEventoPreservacao(str, Enum):
    INGESTAO = "INGESTAO"
    VALIDACAO = "VALIDACAO"
    FIXIDEZ = "FIXIDEZ"
    REPLICACAO = "REPLICACAO"
    MIGRACAO = "MIGRACAO"
    ACESSO = "ACESSO"
    MOVIMENTACAO = "MOVIMENTACAO"
    OUTRO = "OUTRO"


class ResultadoEventoPreservacao(str, Enum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"
    ALERTA = "ALERTA"
    INDETERMINADO = "INDETERMINADO"
