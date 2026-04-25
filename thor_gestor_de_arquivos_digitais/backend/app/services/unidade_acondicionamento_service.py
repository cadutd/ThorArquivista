from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import NivelAcesso, StatusUnidade, TipoSuporte, TipoUnidade
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.schemas.unidade_acondicionamento import (
    UnidadeAcondicionamentoCreate,
    UnidadeAcondicionamentoUpdate,
)


class UnidadeAcondicionamentoService:

    @staticmethod
    def criar(
        db: Session,
        dados: UnidadeAcondicionamentoCreate,
    ) -> UnidadeAcondicionamento:
        ua = UnidadeAcondicionamento(**dados.model_dump())
        db.add(ua)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Já existe uma unidade de acondicionamento com o mesmo identificador."
            )
        db.refresh(ua)
        return ua

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        identificador: str | None = None,
        titulo: str | None = None,
        descricao: str | None = None,
        tipo_suporte: TipoSuporte | None = None,
        tipo_unidade: TipoUnidade | None = None,
        nivel_acesso: NivelAcesso | None = None,
        status: StatusUnidade | None = None,
        criado_em_de=None,
        criado_em_ate=None,
        atualizado_em_de=None,
        atualizado_em_ate=None,
    ) -> tuple[list[UnidadeAcondicionamento], int]:
        query = db.query(UnidadeAcondicionamento)

        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    UnidadeAcondicionamento.identificador.ilike(like),
                    UnidadeAcondicionamento.titulo.ilike(like),
                    UnidadeAcondicionamento.descricao.ilike(like),
                )
            )
        if identificador:
            query = query.filter(
                UnidadeAcondicionamento.identificador.ilike(f"%{identificador}%")
            )
        if titulo:
            query = query.filter(UnidadeAcondicionamento.titulo.ilike(f"%{titulo}%"))
        if descricao:
            query = query.filter(
                UnidadeAcondicionamento.descricao.ilike(f"%{descricao}%")
            )
        if tipo_suporte:
            query = query.filter(UnidadeAcondicionamento.tipo_suporte == tipo_suporte)
        if tipo_unidade:
            query = query.filter(UnidadeAcondicionamento.tipo_unidade == tipo_unidade)
        if nivel_acesso:
            query = query.filter(UnidadeAcondicionamento.nivel_acesso == nivel_acesso)
        if status:
            query = query.filter(UnidadeAcondicionamento.status == status)
        if criado_em_de:
            query = query.filter(UnidadeAcondicionamento.criado_em >= criado_em_de)
        if criado_em_ate:
            query = query.filter(UnidadeAcondicionamento.criado_em <= criado_em_ate)
        if atualizado_em_de:
            query = query.filter(
                UnidadeAcondicionamento.atualizado_em >= atualizado_em_de
            )
        if atualizado_em_ate:
            query = query.filter(
                UnidadeAcondicionamento.atualizado_em <= atualizado_em_ate
            )

        total = query.count()
        items = (
            query.order_by(UnidadeAcondicionamento.id.desc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def obter_por_id(
        db: Session,
        id: int,
    ) -> UnidadeAcondicionamento | None:
        return db.get(UnidadeAcondicionamento, id)

    @staticmethod
    def atualizar(
        db: Session,
        id: int,
        dados: UnidadeAcondicionamentoUpdate,
    ) -> UnidadeAcondicionamento | None:
        ua = db.get(UnidadeAcondicionamento, id)
        if not ua:
            return None

        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(ua, campo, valor)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Já existe uma unidade de acondicionamento com o mesmo identificador."
            )

        db.refresh(ua)
        return ua

    @staticmethod
    def excluir(db: Session, id: int) -> bool:
        ua = db.get(UnidadeAcondicionamento, id)
        if not ua:
            return False

        db.delete(ua)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Não foi possível excluir a unidade porque ela está vinculada a outros registros."
            )

        return True
