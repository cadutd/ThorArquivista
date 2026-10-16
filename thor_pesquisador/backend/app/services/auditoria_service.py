"""Unified read projection: existing image/editorial events are NOT copied."""
import uuid
from sqlalchemy import String, case, cast, event, func, inspect, literal, or_, select, union_all, update
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from app.core.observability import request_id_context
from app.models.conformidade import AuditoriaGeral
from app.models.editorial import AcessoInstrumento, EditorialRegistro, EventoEditorial, Papel, PublicacaoImagem
from app.models.imagem import AuditoriaImagem, ImagemDocumento, RegistroImagem
from app.models.instrumento import Instrumento, InstrumentoCampo, IndexacaoJob
from app.models.user import Usuario
from app.services.permissao_service import filtro_escopo, permissoes, require_any_scope

# General audit records changed field names and bounded operational facts, not payloads.
SAFE_KEYS = {"status", "estado_anterior", "estado_novo", "etapa", "versao", "quantidade", "processados",
             "elegiveis", "bloqueados", "removidos", "simulacao", "executor", "tentativa", "categoria",
             "campos_alterados", "antes", "depois", "ativo", "papel", "origem", "usuario_id",
             "escopo", "formato", "operacao_relacionada_id", "snapshot_id", "resultado"}
SAFE_KEYS |= {"permissoes", "instrumento_id", "dias", "permitir_expurgo", "bloqueada"}


def sanitizar(value, depth=0):
    if depth > 3:
        return None
    if isinstance(value, dict):
        return {str(k): sanitizar(v, depth + 1) for k, v in list(value.items())[:40] if k in SAFE_KEYS}
    if isinstance(value, list):
        return [sanitizar(v, depth + 1) for v in value[:100]]
    if isinstance(value, str):
        return value[:255]
    return value if value is None or isinstance(value, (bool, int, float)) else str(value)[:64]


def registrar(db, acao, entidade, entidade_id=None, instrumento_id=None, registro_id=None, detalhe=None,
              usuario=None, operacao_id=None):
    usuario = usuario or db.info.get("usuario")
    row = AuditoriaGeral(id=uuid.uuid4(), usuario_id=usuario.id if usuario else None,
        agente=usuario.nome if usuario else "nao autenticado", acao=acao[:60], entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id else None, instrumento_id=instrumento_id,
        registro_id=registro_id, detalhe=sanitizar(detalhe or {}),
        request_id=request_id_context.get(), operacao_id=operacao_id)
    db.add(row)
    return row


@event.listens_for(Session, "before_flush")
def auditar_transacao(db, _context, _instances):
    from app.models.conformidade import PoliticaRetencao
    mapped = {Instrumento: "instrumento", InstrumentoCampo: "campo", Usuario: "usuario",
              Papel: "perfil", AcessoInstrumento: "acesso", PoliticaRetencao: "politica_retencao",
              IndexacaoJob: "indexacao"}
    revisions = set()
    usuario = db.info.get("usuario")
    editorial_instruments = {e.instrumento_id for e in db.new if isinstance(e, EventoEditorial) and not e.registro_id}
    for row in list(db.new) + list(db.dirty) + list(db.deleted):
        is_new, is_deleted = row in db.new, row in db.deleted
        if not is_new and not is_deleted and not db.is_modified(row, include_collections=False):
            continue
        if isinstance(row, (AuditoriaImagem, EventoEditorial)) and is_new:
            row.request_id = row.request_id or request_id_context.get()
            if isinstance(row, AuditoriaImagem) and usuario:
                row.agente = usuario.nome
        if isinstance(row, (Instrumento, InstrumentoCampo, EditorialRegistro, EventoEditorial, RegistroImagem, AuditoriaImagem)):
            iid = row.id if isinstance(row, Instrumento) else row.instrumento_id
            if iid and not (is_new and isinstance(row, Instrumento)):
                revisions.add(iid)
        if isinstance(row, ImagemDocumento) and not is_new:
            revisions.update(db.scalars(select(RegistroImagem.instrumento_id).where(RegistroImagem.imagem_id == row.id)))
            revisions.update(db.scalars(select(PublicacaoImagem.instrumento_id).where(PublicacaoImagem.imagem_id == row.id)))
        entity = mapped.get(type(row))
        if isinstance(row, Instrumento) and not is_new and not is_deleted and row.id in editorial_instruments:
            entity = None
        if not entity or not usuario:
            continue
        if is_new and hasattr(row, "id") and row.id is None:
            row.id = uuid.uuid4()
        changes = [a.key for a in inspect(row).attrs if a.history.has_changes()]
        facts = {"campos_alterados": changes}
        # Only non-personal operational values may enter before/after.
        for label, attr in (("antes", "deleted"), ("depois", "added")):
            facts[label] = {key: getattr(inspect(row).attrs[key].history, attr)[0]
                for key in changes if key in {"ativo", "status", "papel", "origem", "usuario_id",
                    "instrumento_id", "permissoes", "dias", "categoria", "permitir_expurgo", "bloqueada"}
                and getattr(inspect(row).attrs[key].history, attr)}
        registrar(db, ("INCLUIR_" if is_new else "EXCLUIR_" if is_deleted else "EDITAR_") + entity.upper(),
            entity, getattr(row, "id", None) or getattr(row, "nome", None),
            row.id if isinstance(row, Instrumento) else getattr(row, "instrumento_id", None),
            detalhe=facts, operacao_id=db.info.get("operacao_id"))
    # SQL-side increment avoids lost updates by independent sessions and does not audit itself.
    if revisions:
        db.execute(update(Instrumento).where(Instrumento.id.in_(revisions))
                   .values(revisao_dados=Instrumento.revisao_dados + 1).execution_options(synchronize_session=False))


def consulta():
    a, e, i = AuditoriaGeral, EventoEditorial, AuditoriaImagem
    return union_all(
        select(literal("geral").label("fonte"), a.id, a.usuario_id, a.agente, a.acao, a.entidade,
               a.entidade_id, a.instrumento_id, a.registro_id, a.request_id, a.operacao_id,
               a.detalhe, a.criado_em),
        select(literal("editorial"), e.id, e.usuario_id, e.agente, e.acao,
               case((e.registro_id.is_not(None), "registro"), else_="instrumento"),
               func.coalesce(e.registro_id, cast(e.instrumento_id, String)),
               e.instrumento_id, e.registro_id, e.request_id, e.id,
               func.jsonb_build_object("estado_anterior", e.estado_anterior, "estado_novo", e.estado_novo,
                                       "versao", e.versao, "resultado", e.resultado), e.criado_em),
        select(literal("imagem"), i.id, i.usuario_id, func.coalesce(i.agente, literal("agente legado")),
               i.acao, literal("imagem"), cast(i.imagem_id, String), i.instrumento_id, i.registro_id,
               i.request_id, cast(literal(None), UUID),
               i.detalhe, i.criado_em)).subquery()


def listar(db, limit=20, offset=0, q="", acao=None, usuario_id=None, entidade=None,
           instrumento_id=None, inicio=None, fim=None, fonte=None, evento_id=None):
    require_any_scope(db, "auditoria_consultar")
    source = consulta()
    c = source.c
    filters = [filtro_escopo(db, c.instrumento_id, "auditoria_consultar")]
    allowed = permissoes(db)
    if "*" not in allowed:
        for entity, permission in (("usuario", "usuarios_consultar"), ("perfil", "perfis_consultar"), ("acesso", "acessos_consultar")):
            if permission not in allowed:
                filters.append(c.entidade != entity)
        if "usuarios_consultar" not in allowed:
            filters.append(or_(c.entidade != "sessao", c.usuario_id == db.info["usuario"].id))
    if q:
        pattern = "%" + q.strip()[:100] + "%"
        filters.append(or_(c.acao.ilike(pattern), c.agente.ilike(pattern), c.entidade.ilike(pattern)))
    for key, value in ((c.acao, acao), (c.usuario_id, usuario_id), (c.entidade, entidade),
                       (c.instrumento_id, instrumento_id), (c.fonte, fonte), (c.id, evento_id)):
        if value is not None:
            filters.append(key == value)
    if inicio:
        filters.append(c.criado_em >= inicio)
    if fim:
        filters.append(c.criado_em <= fim)
    rows = db.execute(select(*c).where(*filters).order_by(c.criado_em.desc(), c.id.desc(), c.fonte)
                      .limit(limit).offset(offset)).mappings()
    return {"items": [dict(row, detalhe=sanitizar(row["detalhe"])) for row in rows],
            "total": db.scalar(select(func.count()).select_from(source).where(*filters))}
