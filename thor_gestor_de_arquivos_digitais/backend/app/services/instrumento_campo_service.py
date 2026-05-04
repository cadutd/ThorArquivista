from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.instrumento_pesquisa import InstrumentoCampo, InstrumentoPesquisa
from app.schemas.instrumento_campo import (
    InstrumentoCampoCreate,
    InstrumentoCampoReordenar,
    InstrumentoCampoUpdate,
)


class InstrumentoCampoService:
    @staticmethod
    def instrumento_existe(db: Session, instrumento_id: uuid.UUID) -> bool:
        return db.get(InstrumentoPesquisa, instrumento_id) is not None

    @staticmethod
    def criar(
        db: Session,
        instrumento_id: uuid.UUID,
        dados: InstrumentoCampoCreate,
    ) -> InstrumentoCampo:
        if not InstrumentoCampoService.instrumento_existe(db, instrumento_id):
            raise LookupError("Instrumento de pesquisa não encontrado.")

        campo = InstrumentoCampo(
            instrumento_id=instrumento_id,
            **dados.model_dump(),
        )
        db.add(campo)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Já existe um campo com a mesma chave neste instrumento.")
        db.refresh(campo)
        return campo

    @staticmethod
    def listar(
        db: Session,
        instrumento_id: uuid.UUID,
    ) -> list[InstrumentoCampo]:
        if not InstrumentoCampoService.instrumento_existe(db, instrumento_id):
            raise LookupError("Instrumento de pesquisa não encontrado.")

        return (
            db.query(InstrumentoCampo)
            .filter(InstrumentoCampo.instrumento_id == instrumento_id)
            .order_by(InstrumentoCampo.ordem.asc(), InstrumentoCampo.nome.asc())
            .all()
        )

    @staticmethod
    def obter(
        db: Session,
        instrumento_id: uuid.UUID,
        campo_id: uuid.UUID,
    ) -> InstrumentoCampo | None:
        return (
            db.query(InstrumentoCampo)
            .filter(
                InstrumentoCampo.instrumento_id == instrumento_id,
                InstrumentoCampo.id == campo_id,
            )
            .first()
        )

    @staticmethod
    def atualizar(
        db: Session,
        instrumento_id: uuid.UUID,
        campo_id: uuid.UUID,
        dados: InstrumentoCampoUpdate,
    ) -> InstrumentoCampo | None:
        campo = InstrumentoCampoService.obter(db, instrumento_id, campo_id)
        if not campo:
            return None

        for item_campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(campo, item_campo, valor)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Já existe um campo com a mesma chave neste instrumento.")

        db.refresh(campo)
        return campo

    @staticmethod
    def excluir(
        db: Session,
        instrumento_id: uuid.UUID,
        campo_id: uuid.UUID,
    ) -> bool:
        campo = InstrumentoCampoService.obter(db, instrumento_id, campo_id)
        if not campo:
            return False

        db.delete(campo)
        db.commit()
        return True

    @staticmethod
    def reordenar(
        db: Session,
        instrumento_id: uuid.UUID,
        dados: InstrumentoCampoReordenar,
    ) -> list[InstrumentoCampo]:
        campos = (
            db.query(InstrumentoCampo)
            .filter(InstrumentoCampo.instrumento_id == instrumento_id)
            .all()
        )
        if not campos and not InstrumentoCampoService.instrumento_existe(db, instrumento_id):
            raise LookupError("Instrumento de pesquisa não encontrado.")

        por_id = {campo.id: campo for campo in campos}
        missing = [item.id for item in dados.campos if item.id not in por_id]
        if missing:
            raise LookupError("Um ou mais campos não pertencem ao instrumento informado.")

        for item in dados.campos:
            por_id[item.id].ordem = item.ordem

        db.commit()
        return InstrumentoCampoService.listar(db, instrumento_id)
