from __future__ import annotations

import uuid

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.permissao import Perfil, Permissao
from app.schemas.permissao import AcaoPermissao, PerfilCreate, PerfilUpdate, PermissaoCreate, PermissaoUpdate


class PermissaoService:
    @staticmethod
    def criar(db: Session, dados: PermissaoCreate) -> Permissao:
        payload = PermissaoService._normalizar_payload(dados.model_dump())
        PermissaoService._validar_unicidade(db, payload)
        permissao = Permissao(**payload)
        db.add(permissao)
        db.commit()
        db.refresh(permissao)
        return permissao

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        codigo: str | None = None,
        nome: str | None = None,
        modulo: str | None = None,
        funcao: str | None = None,
        acao: AcaoPermissao | None = None,
        ativo: bool | None = None,
    ) -> tuple[list[Permissao], int]:
        query = db.query(Permissao)
        if q:
            termo = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    Permissao.codigo.ilike(termo),
                    Permissao.nome.ilike(termo),
                    Permissao.descricao.ilike(termo),
                    Permissao.modulo.ilike(termo),
                    Permissao.funcao.ilike(termo),
                )
            )
        if codigo:
            query = query.filter(Permissao.codigo.ilike(f"%{codigo.strip()}%"))
        if nome:
            query = query.filter(Permissao.nome.ilike(f"%{nome.strip()}%"))
        if modulo:
            query = query.filter(Permissao.modulo == modulo)
        if funcao:
            query = query.filter(Permissao.funcao == funcao)
        if acao:
            query = query.filter(Permissao.acao == acao)
        if ativo is not None:
            query = query.filter(Permissao.ativo == ativo)

        total = query.count()
        items = (
            query.order_by(Permissao.modulo.asc(), Permissao.funcao.asc(), Permissao.acao.asc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def obter_por_id(db: Session, id: uuid.UUID) -> Permissao | None:
        return db.get(Permissao, id)

    @staticmethod
    def atualizar(db: Session, id: uuid.UUID, dados: PermissaoUpdate) -> Permissao | None:
        permissao = db.get(Permissao, id)
        if not permissao:
            return None
        payload = PermissaoService._normalizar_payload(dados.model_dump(exclude_unset=True))
        PermissaoService._validar_unicidade(db, payload, permissao_id=id)
        for campo, valor in payload.items():
            setattr(permissao, campo, valor)
        db.commit()
        db.refresh(permissao)
        return permissao

    @staticmethod
    def excluir(db: Session, id: uuid.UUID) -> bool:
        permissao = db.get(Permissao, id)
        if not permissao:
            return False
        db.delete(permissao)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Não foi possível excluir a permissão porque ela está vinculada a outros registros.")
        return True

    @staticmethod
    def _normalizar_payload(payload: dict) -> dict:
        normalized = dict(payload)
        for campo in ("codigo", "nome", "descricao", "modulo", "funcao", "acao"):
            if campo in normalized and isinstance(normalized[campo], str):
                normalized[campo] = normalized[campo].strip()
        if "codigo" in normalized and normalized["codigo"]:
            normalized["codigo"] = normalized["codigo"].lower()
        if "funcao" in normalized and normalized["funcao"]:
            normalized["funcao"] = normalized["funcao"].lower()
        if "modulo" in normalized and normalized["modulo"]:
            normalized["modulo"] = normalized["modulo"].lower()
        return normalized

    @staticmethod
    def _validar_unicidade(db: Session, valores: dict, permissao_id: uuid.UUID | None = None) -> None:
        filtros = []
        if valores.get("codigo"):
            filtros.append(Permissao.codigo == valores["codigo"])
        if valores.get("funcao") and valores.get("acao"):
            filtros.append((Permissao.funcao == valores["funcao"]) & (Permissao.acao == valores["acao"]))
        if not filtros:
            return
        query = db.query(Permissao).filter(or_(*filtros))
        if permissao_id:
            query = query.filter(Permissao.id != permissao_id)
        existente = query.first()
        if not existente:
            return
        if valores.get("codigo") and existente.codigo == valores["codigo"]:
            raise ValueError("Código da permissão já cadastrado.")
        if valores.get("funcao") and valores.get("acao") and existente.funcao == valores["funcao"] and existente.acao == valores["acao"]:
            raise ValueError("Já existe permissão para esta função e ação.")


class PerfilService:
    @staticmethod
    def criar(db: Session, dados: PerfilCreate) -> Perfil:
        payload = dados.model_dump()
        permissao_ids = payload.pop("permissao_ids", [])
        payload = PerfilService._normalizar_payload(payload)
        PerfilService._validar_unicidade(db, payload)
        perfil = Perfil(**payload)
        perfil.permissoes = PerfilService._buscar_permissoes(db, permissao_ids)
        db.add(perfil)
        db.commit()
        db.refresh(perfil)
        return PerfilService.obter_por_id(db, perfil.id) or perfil

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        codigo: str | None = None,
        nome: str | None = None,
        ativo: bool | None = None,
        sistema: bool | None = None,
    ) -> tuple[list[Perfil], int]:
        query = db.query(Perfil).options(selectinload(Perfil.permissoes))
        if q:
            termo = f"%{q.strip()}%"
            query = query.filter(or_(Perfil.codigo.ilike(termo), Perfil.nome.ilike(termo), Perfil.descricao.ilike(termo)))
        if codigo:
            query = query.filter(Perfil.codigo.ilike(f"%{codigo.strip()}%"))
        if nome:
            query = query.filter(Perfil.nome.ilike(f"%{nome.strip()}%"))
        if ativo is not None:
            query = query.filter(Perfil.ativo == ativo)
        if sistema is not None:
            query = query.filter(Perfil.sistema == sistema)

        total = query.count()
        items = query.order_by(Perfil.nome.asc(), Perfil.id.asc()).offset(max(offset, 0)).limit(min(max(limit, 1), 100)).all()
        return items, total

    @staticmethod
    def obter_por_id(db: Session, id: uuid.UUID) -> Perfil | None:
        return db.query(Perfil).options(selectinload(Perfil.permissoes)).filter(Perfil.id == id).first()

    @staticmethod
    def atualizar(db: Session, id: uuid.UUID, dados: PerfilUpdate) -> Perfil | None:
        perfil = db.query(Perfil).options(selectinload(Perfil.permissoes)).filter(Perfil.id == id).first()
        if not perfil:
            return None
        payload = dados.model_dump(exclude_unset=True)
        permissao_ids = payload.pop("permissao_ids", None)
        payload = PerfilService._normalizar_payload(payload)
        PerfilService._validar_unicidade(db, payload, perfil_id=id)
        for campo, valor in payload.items():
            setattr(perfil, campo, valor)
        if permissao_ids is not None:
            perfil.permissoes = PerfilService._buscar_permissoes(db, permissao_ids)
        db.commit()
        return PerfilService.obter_por_id(db, id) or perfil

    @staticmethod
    def excluir(db: Session, id: uuid.UUID) -> bool:
        perfil = db.get(Perfil, id)
        if not perfil:
            return False
        db.delete(perfil)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Não foi possível excluir o perfil porque ele está vinculado a usuários.")
        return True

    @staticmethod
    def _buscar_permissoes(db: Session, ids: list[uuid.UUID]) -> list[Permissao]:
        if not ids:
            return []
        permissoes = db.query(Permissao).filter(Permissao.id.in_(ids)).all()
        if len(permissoes) != len(set(ids)):
            raise ValueError("Uma ou mais permissões informadas não foram encontradas.")
        return permissoes

    @staticmethod
    def _normalizar_payload(payload: dict) -> dict:
        normalized = dict(payload)
        for campo in ("codigo", "nome", "descricao"):
            if campo in normalized and isinstance(normalized[campo], str):
                normalized[campo] = normalized[campo].strip()
        if "codigo" in normalized and normalized["codigo"]:
            normalized["codigo"] = normalized["codigo"].upper()
        return normalized

    @staticmethod
    def _validar_unicidade(db: Session, valores: dict, perfil_id: uuid.UUID | None = None) -> None:
        filtros = []
        if valores.get("codigo"):
            filtros.append(Perfil.codigo == valores["codigo"])
        if valores.get("nome"):
            filtros.append(Perfil.nome == valores["nome"])
        if not filtros:
            return
        query = db.query(Perfil).filter(or_(*filtros))
        if perfil_id:
            query = query.filter(Perfil.id != perfil_id)
        existente = query.first()
        if not existente:
            return
        if valores.get("codigo") and existente.codigo == valores["codigo"]:
            raise ValueError("Código do perfil já cadastrado.")
        if valores.get("nome") and existente.nome == valores["nome"]:
            raise ValueError("Nome do perfil já cadastrado.")
