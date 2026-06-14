from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import TipoMidiaArmazenamento
from app.models.midia_armazenamento import MidiaArmazenamento
from app.schemas.midia_armazenamento import MidiaArmazenamentoCreate


class MidiaArmazenamentoService:
    @staticmethod
    def obter(db: Session, midia_id: int) -> MidiaArmazenamento | None:
        return db.get(MidiaArmazenamento, midia_id)

    @staticmethod
    def criar(
        db: Session,
        dados: MidiaArmazenamentoCreate,
    ) -> MidiaArmazenamento:
        midia = MidiaArmazenamento(**dados.model_dump())
        db.add(midia)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Já existe uma mídia de armazenamento com o mesmo nome."
            )
        db.refresh(midia)
        return midia

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        tipo: TipoMidiaArmazenamento | None = None,
        ativo: bool | None = None,
    ) -> tuple[list[MidiaArmazenamento], int]:
        query = db.query(MidiaArmazenamento)

        if q:
            termo = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    MidiaArmazenamento.nome.ilike(termo),
                    MidiaArmazenamento.descricao.ilike(termo),
                )
            )
        if tipo:
            query = query.filter(MidiaArmazenamento.tipo == tipo)
        if ativo is not None:
            query = query.filter(MidiaArmazenamento.ativo.is_(ativo))

        total = query.count()
        items = (
            query.order_by(MidiaArmazenamento.id.desc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total
