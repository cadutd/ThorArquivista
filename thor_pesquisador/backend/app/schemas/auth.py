from __future__ import annotations

from pydantic import BaseModel


class UsuarioOut(BaseModel):
    id: str
    nome: str
    email: str | None = None
    cpf: str | None = None


class AuthStartOut(BaseModel):
    authorization_url: str
