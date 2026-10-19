from __future__ import annotations

from pydantic import BaseModel


class UsuarioOut(BaseModel):
    id: str | None
    nome: str
    email: str | None = None
    cpf: str | None = None
    visitante: bool = False


class AuthStartOut(BaseModel):
    authorization_url: str
