from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from app.models.portal import ConfiguracaoPortal, AcessoPortal, ContagemPortal
from app.models.instrumento import Instrumento
from app.models.editorial import PublicacaoInstrumento
from app.schemas.portal import DEFAULT_COLORS
from app.services.auditoria_service import registrar
from app.services.auth_service import token_hash
from app.services.permissao_service import require
from app.services.publicacao_service import publico


def configuracao(db):
    row = db.get(ConfiguracaoPortal, 1)
    return {"nome_instituicao": row.nome_instituicao if row else "Thor Pesquisador",
            "cores": row.cores if row else DEFAULT_COLORS, "versao": row.versao if row else 1}


def salvar(db, payload):
    require(db, "portal_configuracao_editar")
    row = db.scalar(select(ConfiguracaoPortal).where(ConfiguracaoPortal.id == 1).with_for_update())
    if not row or row.versao != payload.versao:
        raise HTTPException(409, "Configuracao alterada por outro usuario. Recarregue antes de salvar.")
    changed = [key for key in ("nome_instituicao", "cores")
               if getattr(row, key) != (payload.cores.model_dump() if key == "cores" else payload.nome_instituicao)]
    row.nome_instituicao, row.cores = payload.nome_instituicao, payload.cores.model_dump()
    row.versao += 1
    row.atualizado_em = datetime.now(UTC)
    registrar(db, "EDITAR_CONFIGURACAO_PORTAL", "configuracao_portal", 1, detalhe={"campos_alterados": changed, "versao": row.versao})
    db.commit()
    return configuracao(db)


def elegiveis():
    return select(PublicacaoInstrumento).join(Instrumento, Instrumento.publicacao_id == PublicacaoInstrumento.id).where(
        Instrumento.visibilidade == "PUBLICO", Instrumento.status != "ARQUIVADO")


def resumo(row):
    capa_id = row.schema_json.get("imagem_card_id")
    return {"id": str(row.instrumento_id), "nome": row.schema_json["nome"],
            "tipo": row.schema_json.get("tipo", "OUTRO"), "descricao": row.schema_json.get("descricao"),
            "imagem_card_url": f"/publico/instrumentos/{row.instrumento_id}/imagem-card/{capa_id}" if capa_id else None}


def catalogo(db, limit, offset, q="", tipo="", nome="", descricao=""):
    query = elegiveis()
    if q.strip():
        escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = "%" + escaped + "%"
        from sqlalchemy import or_
        query = query.where(or_(PublicacaoInstrumento.schema_json["nome"].astext.ilike(pattern, escape="\\"),
                               PublicacaoInstrumento.schema_json["descricao"].astext.ilike(pattern, escape="\\")))
    if tipo:
        query = query.where(PublicacaoInstrumento.schema_json["tipo"].astext == tipo)
    for key, value in (("nome", nome), ("descricao", descricao)):
        if value.strip():
            escaped = value.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.where(PublicacaoInstrumento.schema_json[key].astext.ilike("%" + escaped + "%", escape="\\"))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    page = db.scalars(query.order_by(PublicacaoInstrumento.schema_json["nome"].astext, PublicacaoInstrumento.id).limit(limit).offset(offset))
    return {"items": [resumo(row) for row in page], "total": total, "limit": limit, "offset": offset}


def destaques(db, limit):
    since = datetime.now(UTC).date() - timedelta(days=29)
    counts = select(ContagemPortal.instrumento_id, func.sum(ContagemPortal.quantidade).label("total")).where(
        ContagemPortal.dia >= since).group_by(ContagemPortal.instrumento_id).subquery()
    query = elegiveis().outerjoin(counts, counts.c.instrumento_id == PublicacaoInstrumento.instrumento_id)
    rows = list(db.execute(query.add_columns(func.coalesce(counts.c.total, 0)).order_by(
        func.coalesce(counts.c.total, 0).desc(), PublicacaoInstrumento.criado_em.desc(), PublicacaoInstrumento.id).limit(limit)))
    return {"items": [resumo(row) for row, _ in rows], "com_acessos": any(count for _, count in rows), "janela_dias": 30}


def registrar_acesso(db, instrumento_id):
    publico(db, instrumento_id, lock=True)
    sid = db.info.get("sessao_id")
    if not sid:
        raise HTTPException(401, "Sessao requerida.")
    day = datetime.now(UTC).date()
    inserted = db.scalar(insert(AcessoPortal).values(sessao_chave=token_hash(str(sid)), instrumento_id=instrumento_id,
        dia=day).on_conflict_do_nothing().returning(AcessoPortal.sessao_chave))
    if inserted:
        db.execute(insert(ContagemPortal).values(instrumento_id=instrumento_id, dia=day, quantidade=1)
            .on_conflict_do_update(index_elements=["instrumento_id", "dia"],
                set_={"quantidade": ContagemPortal.quantidade + 1}))
    db.commit()


def limpar_acessos(db):
    cutoff = datetime.now(UTC).date() - timedelta(days=30)
    from sqlalchemy import tuple_
    for model, columns in ((AcessoPortal, (AcessoPortal.sessao_chave, AcessoPortal.instrumento_id, AcessoPortal.dia)),
                           (ContagemPortal, (ContagemPortal.instrumento_id, ContagemPortal.dia))):
        for _ in range(100):
            ids = select(*columns).where(model.dia < cutoff).order_by(model.dia).limit(1000)
            result = db.execute(delete(model).where(tuple_(*columns).in_(ids)))
            db.commit()
            if result.rowcount < 1000:
                break
