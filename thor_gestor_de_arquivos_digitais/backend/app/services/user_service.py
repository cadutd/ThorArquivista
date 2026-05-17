from __future__ import annotations

import uuid

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserRole, UserUpdate


class UserService:
    @staticmethod
    def criar(db: Session, dados: UserCreate) -> User:
        payload = UserService._normalizar_payload(dados.model_dump())
        UserService._validar_unicidade(db, payload)

        usuario = User(**payload)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        username: str | None = None,
        nome: str | None = None,
        email: str | None = None,
        papel: UserRole | None = None,
        ativo: bool | None = None,
    ) -> tuple[list[User], int]:
        query = db.query(User)

        if q:
            termo = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    User.username.ilike(termo),
                    User.nome.ilike(termo),
                    User.email.ilike(termo),
                    User.keycloak_sub.ilike(termo),
                )
            )
        if username:
            query = query.filter(User.username.ilike(f"%{username.strip()}%"))
        if nome:
            query = query.filter(User.nome.ilike(f"%{nome.strip()}%"))
        if email:
            query = query.filter(User.email.ilike(f"%{email.strip()}%"))
        if papel:
            query = query.filter(User.papel == papel)
        if ativo is not None:
            query = query.filter(User.ativo == ativo)

        total = query.count()
        items = (
            query.order_by(User.nome.asc(), User.id.asc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def obter_por_id(db: Session, id: uuid.UUID) -> User | None:
        return db.get(User, id)

    @staticmethod
    def atualizar(db: Session, id: uuid.UUID, dados: UserUpdate) -> User | None:
        usuario = db.get(User, id)
        if not usuario:
            return None

        payload = UserService._normalizar_payload(dados.model_dump(exclude_unset=True))
        UserService._validar_unicidade(db, payload, usuario_id=id)

        for campo, valor in payload.items():
            setattr(usuario, campo, valor)

        db.commit()
        db.refresh(usuario)
        return usuario

    @staticmethod
    def excluir(db: Session, id: uuid.UUID) -> bool:
        usuario = db.get(User, id)
        if not usuario:
            return False

        db.delete(usuario)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Não foi possível excluir o usuário porque ele está vinculado a outros registros.")
        return True

    @staticmethod
    def _normalizar_payload(payload: dict) -> dict:
        normalized = dict(payload)
        for campo in ("keycloak_sub", "username", "nome", "email", "observacoes"):
            if campo in normalized and isinstance(normalized[campo], str):
                normalized[campo] = normalized[campo].strip() or None
        if "username" in normalized and normalized["username"]:
            normalized["username"] = normalized["username"].lower()
        if "email" in normalized and normalized["email"]:
            normalized["email"] = normalized["email"].lower()
        return normalized

    @staticmethod
    def _validar_unicidade(
        db: Session,
        valores: dict,
        usuario_id: uuid.UUID | None = None,
    ) -> None:
        filtros = []
        if valores.get("username"):
            filtros.append(User.username == valores["username"])
        if valores.get("email"):
            filtros.append(User.email == valores["email"])
        if valores.get("keycloak_sub"):
            filtros.append(User.keycloak_sub == valores["keycloak_sub"])
        if not filtros:
            return

        query = db.query(User).filter(or_(*filtros))
        if usuario_id:
            query = query.filter(User.id != usuario_id)
        existente = query.first()
        if not existente:
            return

        if valores.get("username") and existente.username == valores["username"]:
            raise ValueError("Nome de usuário já cadastrado.")
        if valores.get("email") and existente.email == valores["email"]:
            raise ValueError("E-mail já cadastrado.")
        if valores.get("keycloak_sub") and existente.keycloak_sub == valores["keycloak_sub"]:
            raise ValueError("Identificador Keycloak já cadastrado.")
