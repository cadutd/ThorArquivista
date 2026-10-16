from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import exists, func, select
from app.models.conformidade import AuditoriaGeral, Exportacao
from app.models.editorial import EditorialRegistro, EventoEditorial, PublicacaoImagem
from app.models.imagem import ImagemDocumento, RegistroImagem
from app.models.instrumento import IndexacaoJob, Instrumento
from app.services.permissao_service import filtro_escopo, permissoes, require_any_scope


def resumo(db, inicio=None, fim=None, instrumento_id=None):
    require_any_scope(db, "relatorios_consultar")
    inicio, fim = periodo(inicio, fim)

    def scoped(column):
        result = filtro_escopo(db, column, "relatorios_consultar")
        return (result, column == instrumento_id) if instrumento_id else (result,)

    def groups(model, key, column, extra=()):
        return [{"nome": str(name), "total": count} for name, count in db.execute(
            select(key, func.count()).where(*scoped(column), *extra).group_by(key).order_by(key))]

    dates = []
    if inicio:
        dates.append(EventoEditorial.criado_em >= inicio)
    if fim:
        dates.append(EventoEditorial.criado_em <= fim)
    result = {
        "instrumentos": groups(Instrumento, Instrumento.status, Instrumento.id),
        "registros": groups(EditorialRegistro, EditorialRegistro.status_operacional, EditorialRegistro.instrumento_id,
                            (EditorialRegistro.expurgado_em.is_(None),)),
        "publicacoes": groups(EventoEditorial, func.date_trunc("day", EventoEditorial.criado_em),
                              EventoEditorial.instrumento_id, (EventoEditorial.acao == "publicar", *dates)),
        "indexacao": groups(IndexacaoJob, IndexacaoJob.status, IndexacaoJob.instrumento_id),
        "exportacoes": groups(Exportacao, Exportacao.status, Exportacao.instrumento_id,
             () if "*" in permissoes(db) else (Exportacao.usuario_id == db.info["usuario"].id,)),
    }
    # Only global report permission plus image consultation can enumerate unlinked images.
    allowed = permissoes(db)
    from app.services.imagem_service import visiveis
    result["imagens_orfas"] = db.scalar(select(func.count()).select_from(ImagemDocumento).where(
        visiveis(db.info["usuario"], db),
        ~exists(select(RegistroImagem.imagem_id).where(RegistroImagem.imagem_id == ImagemDocumento.id)),
        ~exists(select(PublicacaoImagem.imagem_id).where(PublicacaoImagem.imagem_id == ImagemDocumento.id)))) if (
        "*" in allowed or {"relatorios_consultar", "imagens_consultar"}.issubset(allowed)) else None
    return result


def periodo(inicio=None, fim=None):
    fim = (fim.replace(tzinfo=UTC) if fim and not fim.tzinfo else fim) or datetime.now(UTC)
    inicio = (inicio.replace(tzinfo=UTC) if inicio and not inicio.tzinfo else inicio) or fim - timedelta(days=30)
    if inicio > fim or fim - inicio > timedelta(days=366):
        raise HTTPException(422, "Informe periodo valido de ate 366 dias.")
    return inicio, fim


def registros_por_instrumento(db, limit, offset, instrumento_id=None, q=""):
    require_any_scope(db, "relatorios_consultar")
    filters = [filtro_escopo(db, Instrumento.id, "relatorios_consultar")]
    if instrumento_id:
        filters.append(Instrumento.id == instrumento_id)
    if q:
        filters.append(Instrumento.nome.ilike("%" + q[:100] + "%"))
    counts = select(EditorialRegistro.instrumento_id, func.count().label("total")).where(
        EditorialRegistro.expurgado_em.is_(None)).group_by(EditorialRegistro.instrumento_id).subquery()
    query = select(Instrumento.id, Instrumento.nome, func.coalesce(counts.c.total, 0).label("total")).outerjoin(
        counts, counts.c.instrumento_id == Instrumento.id).where(*filters)
    return {"items": [dict(r) for r in db.execute(query.order_by(Instrumento.nome, Instrumento.id)
        .limit(limit).offset(offset)).mappings()], "total": db.scalar(select(func.count()).select_from(query.subquery()))}


def alteracoes_usuarios(db, limit, offset, inicio=None, fim=None):
    from app.services.permissao_service import require
    require(db, "relatorios_consultar")
    require(db, "usuarios_consultar")
    require(db, "auditoria_consultar")
    inicio, fim = periodo(inicio, fim)
    filters = [AuditoriaGeral.entidade == "usuario", AuditoriaGeral.criado_em >= inicio, AuditoriaGeral.criado_em <= fim]
    query = select(AuditoriaGeral.id, AuditoriaGeral.acao, AuditoriaGeral.entidade_id, AuditoriaGeral.agente,
                   AuditoriaGeral.criado_em).where(*filters)
    return {"items": [dict(r) for r in db.execute(query.order_by(AuditoriaGeral.criado_em.desc(), AuditoriaGeral.id)
        .limit(limit).offset(offset)).mappings()], "total": db.scalar(select(func.count()).select_from(query.subquery()))}


def jobs_dashboard(db):
    # Counts only; no Mongo scan and no per-job / per-instrument fetch.
    result = {"exportacoes": {}, "retencao_pendente": 0}
    user = db.info["usuario"]
    scope = [filtro_escopo(db, Exportacao.instrumento_id, "exportacoes_consultar")]
    if "*" not in permissoes(db):
        scope.append(Exportacao.usuario_id == user.id)
    result["exportacoes"] = dict(db.execute(select(Exportacao.status, func.count()).where(*scope).group_by(Exportacao.status)).all())
    from app.models.conformidade import ExecucaoRetencao, PoliticaRetencao
    scope = [filtro_escopo(db, PoliticaRetencao.instrumento_id, "retencao_consultar"),
             ExecucaoRetencao.status.in_(["PENDENTE", "PROCESSANDO", "FALHOU"])]
    if "*" not in permissoes(db):
        scope.append(ExecucaoRetencao.usuario_id == user.id)
    result["retencao_pendente"] = db.scalar(select(func.count()).select_from(ExecucaoRetencao).join(
        PoliticaRetencao, PoliticaRetencao.id == ExecucaoRetencao.politica_id).where(*scope))
    return result
