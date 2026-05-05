from __future__ import annotations

import uuid

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import StatusInstrumentoPesquisa, TipoInstrumentoPesquisa, VisibilidadeInstrumentoPesquisa
from app.models.instrumento_pesquisa import InstrumentoCampo, InstrumentoPesquisa
from app.schemas.instrumento_pesquisa import (
    InstrumentoPesquisaCreate,
    InstrumentoPesquisaSchema,
    InstrumentoPesquisaSchemaResumo,
    InstrumentoPesquisaUpdate,
)


class InstrumentoPesquisaService:
    @staticmethod
    def criar(
        db: Session,
        dados: InstrumentoPesquisaCreate,
    ) -> InstrumentoPesquisa:
        instrumento = InstrumentoPesquisa(**dados.model_dump())
        db.add(instrumento)
        db.commit()
        db.refresh(instrumento)
        return instrumento

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        tipo: TipoInstrumentoPesquisa | None = None,
        status: StatusInstrumentoPesquisa | None = None,
        visibilidade: VisibilidadeInstrumentoPesquisa | None = None,
    ) -> tuple[list[InstrumentoPesquisa], int]:
        query = db.query(InstrumentoPesquisa)

        if q:
            termo = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    InstrumentoPesquisa.nome.ilike(termo),
                    InstrumentoPesquisa.descricao.ilike(termo),
                    InstrumentoPesquisa.responsavel.ilike(termo),
                )
            )
        if tipo:
            query = query.filter(InstrumentoPesquisa.tipo == tipo)
        if status:
            query = query.filter(InstrumentoPesquisa.status == status)
        if visibilidade:
            query = query.filter(InstrumentoPesquisa.visibilidade == visibilidade)

        total = query.count()
        items = (
            query.order_by(InstrumentoPesquisa.atualizado_em.desc(), InstrumentoPesquisa.nome.asc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def obter_por_id(
        db: Session,
        id: uuid.UUID,
    ) -> InstrumentoPesquisa | None:
        return db.get(InstrumentoPesquisa, id)

    @staticmethod
    def atualizar(
        db: Session,
        id: uuid.UUID,
        dados: InstrumentoPesquisaUpdate,
    ) -> InstrumentoPesquisa | None:
        instrumento = db.get(InstrumentoPesquisa, id)
        if not instrumento:
            return None

        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(instrumento, campo, valor)

        db.commit()
        db.refresh(instrumento)
        return instrumento

    @staticmethod
    def excluir(db: Session, id: uuid.UUID) -> bool:
        instrumento = db.get(InstrumentoPesquisa, id)
        if not instrumento:
            return False

        db.delete(instrumento)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Não foi possível excluir o instrumento porque ele está vinculado a outros registros."
            )

        return True

    @staticmethod
    def obter_schema(
        db: Session,
        id: uuid.UUID,
    ) -> InstrumentoPesquisaSchema | None:
        instrumento = db.get(InstrumentoPesquisa, id)
        if not instrumento:
            return None

        campos = (
            db.query(InstrumentoCampo)
            .filter(InstrumentoCampo.instrumento_id == id)
            .order_by(InstrumentoCampo.ordem.asc(), InstrumentoCampo.nome.asc())
            .all()
        )

        return InstrumentoPesquisaSchema(
            instrumento=InstrumentoPesquisaSchemaResumo(
                id=instrumento.id,
                nome=instrumento.nome,
                tipo=instrumento.tipo,
                status=instrumento.status,
            ),
            campos=campos,
        )
