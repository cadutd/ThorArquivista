from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TipoReferencia(StrEnum):
    UPLOAD = "UPLOAD"
    URL = "URL"
    IIIF = "IIIF"
    REPOSITORIO_EXTERNO = "REPOSITORIO_EXTERNO"


class DireitosAcesso(StrEnum):
    PUBLICO = "PUBLICO"
    INTERNO = "INTERNO"
    RESTRITO = "RESTRITO"


class ImagemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=255)
    descricao: str | None = None
    tipo_referencia: TipoReferencia = TipoReferencia.URL
    uri: str | None = Field(default=None, max_length=4000)
    thumbnail_uri: str | None = Field(default=None, max_length=4000)
    manifest_iiif_uri: str | None = Field(default=None, max_length=4000)
    direitos_acesso: DireitosAcesso = DireitosAcesso.INTERNO
    metadados_json: dict = Field(default_factory=dict)

    @field_validator("uri", "thumbnail_uri", "manifest_iiif_uri")
    @classmethod
    def validar_url(cls, value):
        if value is None:
            return None
        url = urlsplit(value)
        if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
            raise ValueError("Informe uma URL HTTP/HTTPS sem credenciais.")
        return value

    @model_validator(mode="after")
    def referencia(self):
        if self.tipo_referencia == TipoReferencia.UPLOAD:
            raise ValueError("Use o endpoint de upload para arquivos.")
        if self.tipo_referencia == TipoReferencia.IIIF:
            if not self.manifest_iiif_uri:
                raise ValueError("Manifest IIIF obrigatorio.")
            self.uri = self.manifest_iiif_uri
        elif not self.uri:
            raise ValueError("URL obrigatoria.")
        return self


class ImagemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=255)
    descricao: str | None = None
    uri: str | None = Field(default=None, max_length=4000)
    thumbnail_uri: str | None = Field(default=None, max_length=4000)
    manifest_iiif_uri: str | None = Field(default=None, max_length=4000)
    direitos_acesso: DireitosAcesso = DireitosAcesso.INTERNO
    metadados_json: dict = Field(default_factory=dict)

    validar_url = field_validator("uri", "thumbnail_uri", "manifest_iiif_uri")(ImagemCreate.validar_url.__func__)


class ImagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    titulo: str
    descricao: str | None
    tipo_referencia: TipoReferencia
    uri: str
    thumbnail_uri: str | None
    manifest_iiif_uri: str | None
    mime_type: str | None
    tamanho_bytes: int | None
    largura: int | None
    altura: int | None
    checksum_sha256: str | None
    direitos_acesso: DireitosAcesso
    metadados_json: dict
    criado_por: uuid.UUID | None
    criado_em: datetime
    atualizado_em: datetime


class ImagemPage(BaseModel):
    items: list[ImagemOut]
    total: int
    limit: int
    offset: int


class VinculoCreate(BaseModel):
    imagem_id: uuid.UUID
    principal: bool = False
    legenda: str | None = Field(default=None, max_length=4000)


class VinculoUpdate(BaseModel):
    principal: bool | None = None
    legenda: str | None = Field(default=None, max_length=4000)


class VinculoOut(BaseModel):
    instrumento_id: uuid.UUID
    registro_id: str
    imagem_id: uuid.UUID
    ordem: int
    principal: bool
    legenda: str | None
    imagem: ImagemOut


class VinculoPage(BaseModel):
    items: list[VinculoOut]
    total: int
    limit: int
    offset: int


class ReordenarItem(BaseModel):
    imagem_id: uuid.UUID
    ordem: int = Field(ge=0)


class ReordenarIn(BaseModel):
    items: list[ReordenarItem] = Field(min_length=1, max_length=100)
