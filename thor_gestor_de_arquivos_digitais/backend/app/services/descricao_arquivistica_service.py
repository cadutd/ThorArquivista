from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.descricao_arquivistica import RegistroDescritivo
from app.schemas.descricao_arquivistica import (
    RegistroDescritivoBatchCreate,
    RegistroDescritivoCreate,
    RegistroDescritivoDuplicate,
    RegistroDescritivoMove,
    RegistroDescritivoTreeNode,
    RegistroDescritivoUpdate,
)

ALLOWED_CHILDREN = {
    "1": {"2"},
    "2": {"2.5", "3"},
    "2.5": {"3"},
    "3": {"3.5", "4"},
    "3.5": {"4"},
    "4": {"5"},
    "5": set(),
}
INHERITED_FIELDS = ("produtor", "condicoes_acesso", "idioma", "regras_convencoes")


class DescricaoArquivisticaService:
    @staticmethod
    def listar(db: Session, q: str | None = None, nivel: str | None = None) -> list[RegistroDescritivo]:
        query = db.query(RegistroDescritivo)
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    RegistroDescritivo.titulo.ilike(like),
                    RegistroDescritivo.codigo_referencia.ilike(like),
                    RegistroDescritivo.produtor.ilike(like),
                )
            )
        if nivel:
            query = query.filter(RegistroDescritivo.nivel == nivel)
        return query.order_by(RegistroDescritivo.codigo_referencia, RegistroDescritivo.titulo).all()

    @staticmethod
    def arvore(db: Session, q: str | None = None, nivel: str | None = None) -> list[RegistroDescritivoTreeNode]:
        registros = DescricaoArquivisticaService.listar(db, q=q, nivel=nivel)
        if q or nivel:
            return [DescricaoArquivisticaService._node(registro, []) for registro in registros]

        children_by_parent: dict[uuid.UUID | None, list[RegistroDescritivo]] = {}
        for registro in registros:
            children_by_parent.setdefault(registro.parent_id, []).append(registro)

        def build(parent_id: uuid.UUID | None) -> list[RegistroDescritivoTreeNode]:
            return [
                DescricaoArquivisticaService._node(registro, build(registro.id))
                for registro in children_by_parent.get(parent_id, [])
            ]

        return build(None)

    @staticmethod
    def obter(db: Session, id: uuid.UUID) -> RegistroDescritivo | None:
        return db.get(RegistroDescritivo, id)

    @staticmethod
    def criar(db: Session, dados: RegistroDescritivoCreate) -> RegistroDescritivo:
        payload = dados.model_dump()
        DescricaoArquivisticaService._validate_parent(db, payload.get("parent_id"), payload["nivel"])
        DescricaoArquivisticaService._inherit_context(db, payload)
        registro = RegistroDescritivo(**payload)
        db.add(registro)
        db.commit()
        db.refresh(registro)
        return registro

    @staticmethod
    def atualizar(db: Session, id: uuid.UUID, dados: RegistroDescritivoUpdate) -> RegistroDescritivo | None:
        registro = db.get(RegistroDescritivo, id)
        if not registro:
            return None
        payload = dados.model_dump(exclude_unset=True)
        parent_id = payload.get("parent_id", registro.parent_id)
        nivel = payload.get("nivel", registro.nivel)
        DescricaoArquivisticaService._validate_parent(db, parent_id, nivel, current_id=id)
        for key, value in payload.items():
            setattr(registro, key, value)
        db.commit()
        db.refresh(registro)
        return registro

    @staticmethod
    def excluir(db: Session, id: uuid.UUID, cascade: bool = False) -> bool:
        registro = db.get(RegistroDescritivo, id)
        if not registro:
            return False
        has_children = db.query(RegistroDescritivo.id).filter(RegistroDescritivo.parent_id == id).first()
        if has_children and not cascade:
            raise ValueError("Registro possui filhos. Confirme exclusão em cascata.")
        db.delete(registro)
        db.commit()
        return True

    @staticmethod
    def mover(db: Session, id: uuid.UUID, dados: RegistroDescritivoMove) -> RegistroDescritivo | None:
        registro = db.get(RegistroDescritivo, id)
        if not registro:
            return None
        DescricaoArquivisticaService._validate_parent(db, dados.parent_id, registro.nivel, current_id=id)
        registro.parent_id = dados.parent_id
        db.commit()
        db.refresh(registro)
        return registro

    @staticmethod
    def duplicar(db: Session, id: uuid.UUID, dados: RegistroDescritivoDuplicate) -> RegistroDescritivo | None:
        original = db.get(RegistroDescritivo, id)
        if not original:
            return None
        payload = DescricaoArquivisticaService._copy_payload(original)
        payload["parent_id"] = dados.parent_id if dados.parent_id is not None else original.parent_id
        payload["titulo"] = dados.titulo or f"Cópia de {original.titulo}"
        payload["codigo_referencia"] = dados.codigo_referencia or f"{original.codigo_referencia}-COPIA"
        DescricaoArquivisticaService._validate_parent(db, payload["parent_id"], payload["nivel"])
        registro = RegistroDescritivo(**payload)
        db.add(registro)
        db.commit()
        db.refresh(registro)
        return registro

    @staticmethod
    def criar_lote(db: Session, dados: RegistroDescritivoBatchCreate) -> list[RegistroDescritivo]:
        registros = [DescricaoArquivisticaService.criar(db, item) for item in dados.registros]
        return registros

    @staticmethod
    def _validate_parent(
        db: Session,
        parent_id: uuid.UUID | None,
        nivel: str,
        current_id: uuid.UUID | None = None,
    ) -> None:
        if nivel == "1":
            if parent_id is not None:
                raise ValueError("Registros de nível 1 não podem possuir pai.")
            return
        if parent_id is None:
            raise ValueError("Registros abaixo do nível 1 devem possuir pai.")
        if parent_id == current_id:
            raise ValueError("Registro não pode ser pai de si mesmo.")
        parent = db.get(RegistroDescritivo, parent_id)
        if not parent:
            raise LookupError("Registro pai não encontrado.")
        if nivel not in ALLOWED_CHILDREN[parent.nivel]:
            raise ValueError(f"Nível {nivel} não é filho compatível do nível {parent.nivel}.")

    @staticmethod
    def _inherit_context(db: Session, payload: dict[str, Any]) -> None:
        parent_id = payload.get("parent_id")
        if not parent_id:
            return
        parent = db.get(RegistroDescritivo, parent_id)
        if not parent:
            return
        for field in INHERITED_FIELDS:
            if payload.get(field) in (None, ""):
                payload[field] = getattr(parent, field)

    @staticmethod
    def _node(registro: RegistroDescritivo, children: list[RegistroDescritivoTreeNode]) -> RegistroDescritivoTreeNode:
        return RegistroDescritivoTreeNode(
            id=registro.id,
            parent_id=registro.parent_id,
            nivel=registro.nivel,
            norma=registro.norma,
            codigo_referencia=registro.codigo_referencia,
            titulo=registro.titulo,
            children=children,
        )

    @staticmethod
    def _copy_payload(registro: RegistroDescritivo) -> dict[str, Any]:
        ignored = {"id", "children", "parent", "created_at", "updated_at"}
        return {
            column.name: getattr(registro, column.name)
            for column in RegistroDescritivo.__table__.columns
            if column.name not in ignored
        }
