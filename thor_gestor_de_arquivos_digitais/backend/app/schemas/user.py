from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.permissao import PerfilRead


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    ARQUIVISTA = "ARQUIVISTA"
    ADMISSAO = "ADMISSAO"
    GESTOR_ARMAZENAMENTO = "GESTOR_ARMAZENAMENTO"
    CONSULTA = "CONSULTA"


class UserBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    keycloak_sub: str | None = Field(default=None, max_length=255)
    username: str = Field(..., min_length=3, max_length=150)
    nome: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    papel: UserRole = UserRole.ARQUIVISTA
    id_perfil: uuid.UUID | None = None
    ativo: bool = True
    observacoes: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    keycloak_sub: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=150)
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    papel: UserRole | None = None
    id_perfil: uuid.UUID | None = None
    ativo: bool | None = None
    observacoes: str | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    perfil: PerfilRead | None = None
    criado_em: datetime
    atualizado_em: datetime


class UserList(BaseModel):
    items: list[UserRead]
    total: int
    limit: int
    offset: int


class IdentityProviderName(StrEnum):
    KEYCLOAK = "KEYCLOAK"


class IdentityAccountCreate(BaseModel):
    provider: IdentityProviderName = IdentityProviderName.KEYCLOAK


class IdentityAccountRead(BaseModel):
    provider: IdentityProviderName
    provider_user_id: str
    temporary_password: str
    username: str
    email: str
