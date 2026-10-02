from __future__ import annotations

from enum import StrEnum


class TipoInstrumento(StrEnum):
    GUIA = "GUIA"
    INVENTARIO = "INVENTARIO"
    CATALOGO = "CATALOGO"
    INDICE = "INDICE"
    BASE_TEMATICA = "BASE_TEMATICA"
    OUTRO = "OUTRO"


class StatusInstrumento(StrEnum):
    RASCUNHO = "RASCUNHO"
    PUBLICADO = "PUBLICADO"
    ARQUIVADO = "ARQUIVADO"


class VisibilidadeInstrumento(StrEnum):
    INTERNO = "INTERNO"
    PUBLICO = "PUBLICO"
    RESTRITO = "RESTRITO"


class TipoCampo(StrEnum):
    TEXTO_CURTO = "TEXTO_CURTO"
    TEXTO_LONGO = "TEXTO_LONGO"
    NUMERO = "NUMERO"
    DATA = "DATA"
    BOOLEANO = "BOOLEANO"
    LISTA_SIMPLES = "LISTA_SIMPLES"
    LISTA_MULTIPLA = "LISTA_MULTIPLA"
    URL = "URL"


class StatusRegistro(StrEnum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    EXCLUIDO = "EXCLUIDO"


class TipoIndexacaoJob(StrEnum):
    REGISTRO = "REGISTRO"
    REINDEXACAO = "REINDEXACAO"
    SCHEMA = "SCHEMA"


class StatusIndexacaoJob(StrEnum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    FALHOU = "FALHOU"
