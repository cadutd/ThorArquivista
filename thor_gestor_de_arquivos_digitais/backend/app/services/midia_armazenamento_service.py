from __future__ import annotations

import calendar
import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.enums import ResultadoEventoPreservacao, TipoEventoPreservacao
from app.models.evento_midia_armazenamento import EventoMidiaArmazenamento
from app.models.midia_armazenamento import MidiaArmazenamento, TipoMidiaArmazenamento
from app.schemas.midia_armazenamento import (
    MidiaArmazenamentoCreate,
    MidiaArmazenamentoUpdate,
    TipoMidiaArmazenamentoCreate,
    TipoMidiaArmazenamentoUpdate,
)


def _somar_anos(valor: date, anos: int) -> date:
    try:
        return valor.replace(year=valor.year + anos)
    except ValueError:
        return valor.replace(year=valor.year + anos, day=28)


def _somar_meses(valor: datetime, meses: int) -> datetime:
    mes_total = valor.month - 1 + meses
    ano = valor.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(valor.day, calendar.monthrange(ano, mes)[1])
    return valor.replace(year=ano, month=mes, day=dia)


def _data_para_datetime(valor: date | None) -> datetime | None:
    if not valor:
        return None
    return datetime.combine(valor, time.min, tzinfo=timezone.utc)


class TipoMidiaArmazenamentoService:
    @staticmethod
    def obter(db: Session, tipo_id: uuid.UUID) -> TipoMidiaArmazenamento | None:
        return db.get(TipoMidiaArmazenamento, tipo_id)

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        ativo: bool | None = None,
    ) -> tuple[list[TipoMidiaArmazenamento], int]:
        query = db.query(TipoMidiaArmazenamento)
        if q:
            termo = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    TipoMidiaArmazenamento.nome.ilike(termo),
                    TipoMidiaArmazenamento.descricao.ilike(termo),
                )
            )
        if ativo is not None:
            query = query.filter(TipoMidiaArmazenamento.ativo.is_(ativo))

        total = query.count()
        items = (
            query.order_by(TipoMidiaArmazenamento.nome.asc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def criar(db: Session, dados: TipoMidiaArmazenamentoCreate) -> TipoMidiaArmazenamento:
        tipo = TipoMidiaArmazenamento(**dados.model_dump())
        db.add(tipo)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Ja existe um tipo de midia de armazenamento com o mesmo nome.")
        db.refresh(tipo)
        return tipo

    @staticmethod
    def atualizar(
        db: Session,
        tipo_id: uuid.UUID,
        dados: TipoMidiaArmazenamentoUpdate,
    ) -> TipoMidiaArmazenamento | None:
        tipo = db.get(TipoMidiaArmazenamento, tipo_id)
        if not tipo:
            return None
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(tipo, campo, valor)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Ja existe um tipo de midia de armazenamento com o mesmo nome.")
        db.refresh(tipo)
        return tipo

    @staticmethod
    def excluir(db: Session, tipo_id: uuid.UUID) -> bool:
        tipo = db.get(TipoMidiaArmazenamento, tipo_id)
        if not tipo:
            return False
        tem_midia = (
            db.query(MidiaArmazenamento.id)
            .filter(MidiaArmazenamento.tipo_midia_id == tipo_id)
            .first()
            is not None
        )
        if tem_midia:
            tipo.ativo = False
        else:
            db.delete(tipo)
        db.commit()
        return True


class MidiaArmazenamentoService:
    @staticmethod
    def obter(db: Session, midia_id: int) -> MidiaArmazenamento | None:
        return (
            db.query(MidiaArmazenamento)
            .options(joinedload(MidiaArmazenamento.tipo_midia))
            .filter(MidiaArmazenamento.id == midia_id)
            .first()
        )

    @staticmethod
    def _tipo_ativo(db: Session, tipo_id: uuid.UUID) -> TipoMidiaArmazenamento:
        tipo = db.get(TipoMidiaArmazenamento, tipo_id)
        if not tipo:
            raise LookupError("Tipo de midia de armazenamento nao encontrado.")
        if not tipo.ativo:
            raise ValueError("Tipo de midia de armazenamento inativo.")
        return tipo

    @staticmethod
    def _aplicar_calculos(midia: MidiaArmazenamento, tipo: TipoMidiaArmazenamento) -> None:
        base_validade = midia.data_inicio_uso or midia.data_aquisicao
        if not midia.data_validade and base_validade:
            midia.data_validade = _somar_anos(base_validade, tipo.tempo_duracao_anos)

        base_checagem = (
            midia.ultima_checagem_integridade
            or _data_para_datetime(midia.data_inicio_uso)
            or _data_para_datetime(midia.data_aquisicao)
        )
        if not midia.proxima_checagem_integridade and base_checagem:
            midia.proxima_checagem_integridade = _somar_meses(
                base_checagem,
                tipo.periodicidade_checagem_meses,
            )

    @staticmethod
    def _adicionar_evento(
        db: Session,
        midia_id: int,
        detalhe: str,
        agente: str | None,
        tipo_evento: TipoEventoPreservacao = TipoEventoPreservacao.OUTRO,
    ) -> None:
        db.add(
            EventoMidiaArmazenamento(
                id_midia_armazenamento=midia_id,
                tipo_evento=tipo_evento,
                resultado=ResultadoEventoPreservacao.SUCESSO,
                detalhe=detalhe,
                agente=agente,
            )
        )

    @staticmethod
    def criar(
        db: Session,
        dados: MidiaArmazenamentoCreate,
        agente: str | None = None,
    ) -> MidiaArmazenamento:
        payload = dados.model_dump()
        tipo = MidiaArmazenamentoService._tipo_ativo(db, payload["tipo_midia_id"])
        midia = MidiaArmazenamento(**payload)
        MidiaArmazenamentoService._aplicar_calculos(midia, tipo)
        db.add(midia)
        try:
            db.flush()
            MidiaArmazenamentoService._adicionar_evento(
                db,
                midia.id,
                "Midia de armazenamento cadastrada.",
                agente,
            )
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Ja existe uma midia de armazenamento com o mesmo nome.")
        db.refresh(midia)
        return MidiaArmazenamentoService.obter(db, midia.id) or midia

    @staticmethod
    def atualizar(
        db: Session,
        midia_id: int,
        dados: MidiaArmazenamentoUpdate,
        agente: str | None = None,
    ) -> MidiaArmazenamento | None:
        midia = db.get(MidiaArmazenamento, midia_id)
        if not midia:
            return None
        payload = dados.model_dump(exclude_unset=True)
        tipo = None
        if "tipo_midia_id" in payload:
            tipo = MidiaArmazenamentoService._tipo_ativo(db, payload["tipo_midia_id"])
        for campo, valor in payload.items():
            setattr(midia, campo, valor)
        if tipo is None:
            tipo = db.get(TipoMidiaArmazenamento, midia.tipo_midia_id)
        if tipo:
            MidiaArmazenamentoService._aplicar_calculos(midia, tipo)
        try:
            if payload:
                campos = ", ".join(sorted(payload.keys()))
                MidiaArmazenamentoService._adicionar_evento(
                    db,
                    midia.id,
                    f"Midia de armazenamento atualizada. Campos alterados: {campos}.",
                    agente,
                )
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Ja existe uma midia de armazenamento com o mesmo nome.")
        return MidiaArmazenamentoService.obter(db, midia_id)

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        tipo_midia_id: uuid.UUID | None = None,
        ativo: bool | None = None,
    ) -> tuple[list[MidiaArmazenamento], int]:
        query = db.query(MidiaArmazenamento).options(joinedload(MidiaArmazenamento.tipo_midia))

        if q:
            termo = f"%{q.strip()}%"
            query = query.outerjoin(TipoMidiaArmazenamento).filter(
                or_(
                    MidiaArmazenamento.nome.ilike(termo),
                    MidiaArmazenamento.descricao.ilike(termo),
                    MidiaArmazenamento.identificador_fisico.ilike(termo),
                    TipoMidiaArmazenamento.nome.ilike(termo),
                )
            )
        if tipo_midia_id:
            query = query.filter(MidiaArmazenamento.tipo_midia_id == tipo_midia_id)
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
