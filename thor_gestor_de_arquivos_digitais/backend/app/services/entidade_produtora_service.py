from __future__ import annotations

import re
import unicodedata
import uuid

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entidade_produtora import EntidadeProdutora
from app.models.enums import TipoEntidadeProdutora
from app.schemas.entidade_produtora import (
    EntidadeProdutoraCreate,
    EntidadeProdutoraUpdate,
)


def normalizar_nome(nome: str) -> str:
    sem_acentos = "".join(
        char
        for char in unicodedata.normalize("NFKD", nome)
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", sem_acentos).strip().lower()


class EntidadeProdutoraService:
    @staticmethod
    def criar(db: Session, dados: EntidadeProdutoraCreate) -> EntidadeProdutora:
        payload = dados.model_dump()
        payload["nome_normalizado"] = normalizar_nome(dados.nome)
        avisos = EntidadeProdutoraService._avisos_duplicidade(db, payload)
        EntidadeProdutoraService._validar_regras(db, payload)

        entidade = EntidadeProdutora(**payload)
        db.add(entidade)
        db.commit()
        db.refresh(entidade)
        EntidadeProdutoraService._hidratar_campos_resposta(entidade, avisos)
        return entidade

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        nome: str | None = None,
        sigla: str | None = None,
        tipo_entidade: TipoEntidadeProdutora | None = None,
        entidade_ativa: bool | None = None,
        id_entidade_superior: uuid.UUID | None = None,
    ) -> tuple[list[EntidadeProdutora], int]:
        query = db.query(EntidadeProdutora)

        if q:
            termo = f"%{q.strip()}%"
            termo_normalizado = f"%{normalizar_nome(q)}%"
            query = query.filter(
                or_(
                    EntidadeProdutora.nome.ilike(termo),
                    EntidadeProdutora.nome_normalizado.ilike(termo_normalizado),
                    EntidadeProdutora.sigla.ilike(termo),
                    EntidadeProdutora.codigo_referencia.ilike(termo),
                )
            )
        if nome:
            query = query.filter(
                EntidadeProdutora.nome_normalizado.ilike(f"%{normalizar_nome(nome)}%")
            )
        if sigla:
            query = query.filter(EntidadeProdutora.sigla.ilike(f"%{sigla.strip()}%"))
        if tipo_entidade:
            query = query.filter(EntidadeProdutora.tipo_entidade == tipo_entidade)
        if entidade_ativa is not None:
            query = query.filter(EntidadeProdutora.entidade_ativa == entidade_ativa)
        if id_entidade_superior is not None:
            query = query.filter(
                EntidadeProdutora.id_entidade_superior == id_entidade_superior
            )

        total = query.count()
        items = (
            query.order_by(EntidadeProdutora.nome.asc(), EntidadeProdutora.id.asc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        for item in items:
            EntidadeProdutoraService._hidratar_campos_resposta(item)
        return items, total

    @staticmethod
    def obter_por_id(db: Session, id: uuid.UUID) -> EntidadeProdutora | None:
        entidade = db.get(EntidadeProdutora, id)
        if entidade:
            EntidadeProdutoraService._hidratar_campos_resposta(entidade)
        return entidade

    @staticmethod
    def atualizar(
        db: Session,
        id: uuid.UUID,
        dados: EntidadeProdutoraUpdate,
    ) -> EntidadeProdutora | None:
        entidade = db.get(EntidadeProdutora, id)
        if not entidade:
            return None

        payload = dados.model_dump(exclude_unset=True)
        if "nome" in payload and payload["nome"] is not None:
            payload["nome_normalizado"] = normalizar_nome(payload["nome"])

        valores = {
            campo.name: getattr(entidade, campo.name)
            for campo in EntidadeProdutora.__table__.columns
        }
        valores.update(payload)
        EntidadeProdutoraService._validar_regras(db, valores, entidade_id=id)
        avisos = EntidadeProdutoraService._avisos_duplicidade(db, valores, entidade_id=id)

        for campo, valor in payload.items():
            setattr(entidade, campo, valor)

        db.commit()
        db.refresh(entidade)
        EntidadeProdutoraService._hidratar_campos_resposta(entidade, avisos)
        return entidade

    @staticmethod
    def excluir(db: Session, id: uuid.UUID) -> bool:
        entidade = db.get(EntidadeProdutora, id)
        if not entidade:
            return False

        db.delete(entidade)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Não foi possível excluir a entidade produtora porque ela está vinculada a outros registros."
            )
        return True

    @staticmethod
    def arvore(db: Session) -> list[EntidadeProdutora]:
        return EntidadeProdutoraService.listar_arvore(
            db,
            parent_id=None,
            apenas_raizes=True,
        )

    @staticmethod
    def listar_arvore(
        db: Session,
        q: str | None = None,
        tipo_entidade: TipoEntidadeProdutora | None = None,
        entidade_ativa: bool | None = None,
        parent_id: uuid.UUID | None = None,
        apenas_raizes: bool = False,
    ) -> list[EntidadeProdutora]:
        query = db.query(EntidadeProdutora)
        tem_filtro = bool(q or tipo_entidade or entidade_ativa is not None)

        if parent_id is not None:
            query = query.filter(EntidadeProdutora.id_entidade_superior == parent_id)
        elif apenas_raizes and not tem_filtro:
            query = query.filter(EntidadeProdutora.id_entidade_superior.is_(None))

        if q:
            termo = f"%{q.strip()}%"
            termo_normalizado = f"%{normalizar_nome(q)}%"
            query = query.filter(
                or_(
                    EntidadeProdutora.nome.ilike(termo),
                    EntidadeProdutora.nome_normalizado.ilike(termo_normalizado),
                    EntidadeProdutora.sigla.ilike(termo),
                    EntidadeProdutora.codigo_referencia.ilike(termo),
                )
            )
        if tipo_entidade:
            query = query.filter(EntidadeProdutora.tipo_entidade == tipo_entidade)
        if entidade_ativa is not None:
            query = query.filter(EntidadeProdutora.entidade_ativa == entidade_ativa)

        entidades = query.order_by(EntidadeProdutora.nome.asc(), EntidadeProdutora.id.asc()).all()
        for entidade in entidades:
            entidade.filhos = []
            entidade.has_children = bool(
                db.query(EntidadeProdutora.id)
                .filter(EntidadeProdutora.id_entidade_superior == entidade.id)
                .first()
            )
        return entidades

    @staticmethod
    def _validar_regras(
        db: Session,
        valores: dict,
        entidade_id: uuid.UUID | None = None,
    ) -> None:
        data_inicio = valores.get("data_inicio")
        data_fim = valores.get("data_fim")
        if data_inicio and data_fim and data_fim < data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio.")

        if data_fim and valores.get("entidade_ativa") and not (valores.get("observacoes") or "").strip():
            raise ValueError(
                "Informe observacoes para manter a entidade ativa com data_fim preenchida."
            )

        superior_id = valores.get("id_entidade_superior")
        if superior_id is None:
            return
        if entidade_id and superior_id == entidade_id:
            raise ValueError("A entidade não pode ser superior de si mesma.")
        if not db.get(EntidadeProdutora, superior_id):
            raise LookupError("Entidade superior não encontrada.")

        visitados = {entidade_id} if entidade_id else set()
        atual_id = superior_id
        while atual_id:
            if atual_id in visitados:
                raise ValueError("A hierarquia informada cria um ciclo.")
            visitados.add(atual_id)
            atual = db.get(EntidadeProdutora, atual_id)
            atual_id = atual.id_entidade_superior if atual else None

    @staticmethod
    def _avisos_duplicidade(
        db: Session,
        valores: dict,
        entidade_id: uuid.UUID | None = None,
    ) -> list[str]:
        avisos: list[str] = []
        filtros = []
        if valores.get("nome_normalizado"):
            filtros.append(EntidadeProdutora.nome_normalizado == valores["nome_normalizado"])
        if valores.get("sigla"):
            filtros.append(EntidadeProdutora.sigla == valores["sigla"])
        if valores.get("codigo_referencia"):
            filtros.append(
                EntidadeProdutora.codigo_referencia == valores["codigo_referencia"]
            )
        if not filtros:
            return avisos

        query = db.query(EntidadeProdutora).filter(or_(*filtros))
        if entidade_id:
            query = query.filter(EntidadeProdutora.id != entidade_id)

        for entidade in query.limit(10).all():
            if valores.get("nome_normalizado") and entidade.nome_normalizado == valores["nome_normalizado"]:
                avisos.append(f"Possível duplicidade por nome: {entidade.nome}.")
            if valores.get("sigla") and entidade.sigla == valores["sigla"]:
                avisos.append(f"Possível duplicidade por sigla: {entidade.nome}.")
            if (
                valores.get("codigo_referencia")
                and entidade.codigo_referencia == valores["codigo_referencia"]
            ):
                avisos.append(
                    f"Possível duplicidade por código de referência: {entidade.nome}."
                )
        return avisos

    @staticmethod
    def _hidratar_campos_resposta(
        entidade: EntidadeProdutora,
        avisos: list[str] | None = None,
    ) -> None:
        entidade.nome_entidade_superior = (
            entidade.entidade_superior.nome if entidade.entidade_superior else None
        )
        entidade.avisos_duplicidade = avisos or []
