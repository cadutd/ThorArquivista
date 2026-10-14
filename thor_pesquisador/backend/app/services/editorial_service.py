"""SQL is authoritative for publication pointers; orphan Mongo snapshots are private."""
import uuid
import hashlib
import json
from fastapi import HTTPException
from sqlalchemy import select
from app.db.mongo import registros_collection, snapshots_collection
from app.models.editorial import EditorialRegistro, EventoEditorial, PublicacaoInstrumento, PublicacaoImagem
from app.models.instrumento import Instrumento, IndexacaoJob
from app.models.imagem import RegistroImagem, ImagemDocumento
from app.schemas.instrumento import InstrumentoSchema
from app.services.permissao_service import require

TRANSICOES = {
    "enviar-revisao": ({"RASCUNHO"}, "EM_REVISAO", "enviar_revisao"),
    "aprovar": ({"EM_REVISAO"}, "APROVADO", "revisar"),
    "devolver": ({"EM_REVISAO", "APROVADO"}, "RASCUNHO", "revisar"),
    "publicar": ({"APROVADO"}, "PUBLICADO", "publicar"),
    "arquivar": ({"RASCUNHO", "EM_REVISAO", "APROVADO", "PUBLICADO"}, "ARQUIVADO", "arquivar"),
    "reabrir": ({"ARQUIVADO"}, "RASCUNHO", "registros_editar"),
}


def assinatura(db, instrumento, doc, links):
    schema = InstrumentoSchema.model_validate(instrumento).model_dump(mode="json")
    content = {"dados": doc.get("dados", {}), "schema_version": instrumento.schema_version,
        "campos": schema["campos"], "imagens": links}
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def referencias(db, instrumento_id, registro_id):
    from app.services.imagem_service import saida
    links = db.execute(select(RegistroImagem, ImagemDocumento).join(ImagemDocumento).where(
        RegistroImagem.instrumento_id == instrumento_id, RegistroImagem.registro_id == registro_id)
        .order_by(RegistroImagem.ordem, RegistroImagem.imagem_id)).all()
    result = []
    for v, image in links:
        presentation = saida(image).model_dump(mode="json")
        presentation["metadados_json"], presentation["criado_por"] = {}, None
        result.append({"imagem_id": str(v.imagem_id), "ordem": v.ordem,
            "principal": v.principal, "legenda": v.legenda, "imagem": presentation})
    return result


def validar_transicao(acao, estado, justificativa=None):
    rule = TRANSICOES.get(acao)
    if not rule or estado not in rule[0]:
        raise HTTPException(409, "Transicao editorial invalida.")
    if acao in {"devolver", "arquivar"} and not (justificativa or "").strip():
        raise HTTPException(422, "Informe a justificativa.")
    return rule


def invalidar_publicacao(db, instrumento):
    instrumento.geracao_publica += 1
    db.add(IndexacaoJob(instrumento_id=instrumento.id, tipo="PUBLICACAO",
                       geracao_publica=instrumento.geracao_publica, status="PENDENTE"))


def auditar_edicao(db, instrumento_id, registro_id, acao, anterior, novo, versao, detalhe=None):
    actor = db.info["usuario"]
    operation = uuid.uuid4()
    db.add(EventoEditorial(id=operation, instrumento_id=instrumento_id, registro_id=registro_id,
        usuario_id=actor.id, agente=actor.nome, acao=acao, estado_anterior=anterior, estado_novo=novo,
        versao=versao, resultado=detalhe or {"versao": versao}))
    return operation


def controle(db, instrumento_id, registro_id, doc):
    row = db.scalar(select(EditorialRegistro).where(
        EditorialRegistro.instrumento_id == instrumento_id,
        EditorialRegistro.registro_id == registro_id).with_for_update())
    if not row:
        row = EditorialRegistro(instrumento_id=instrumento_id, registro_id=registro_id,
            status_editorial="RASCUNHO", status_operacional=doc["status"],
            versao=doc.get("_revision", 1))
        db.add(row)
        db.flush()
    return row


def transicionar(db, instrumento_id, acao, payload, registro_id=None):
    if acao not in TRANSICOES:
        raise HTTPException(404, "Acao nao encontrada.")
    permission = "instrumentos_editar" if acao == "reabrir" and registro_id is None else TRANSICOES[acao][2]
    usuario = require(db, permission, instrumento_id)
    instrumento = db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
    if not instrumento:
        raise HTTPException(404, "Instrumento nao encontrado.")
    anterior = db.get(EventoEditorial, payload.operacao_id)
    if anterior:
        if (anterior.instrumento_id != instrumento_id or anterior.registro_id != registro_id
                or anterior.usuario_id != usuario.id or anterior.acao != acao
                or anterior.versao != payload.versao or anterior.justificativa != payload.justificativa):
            raise HTTPException(409, "Identificador de operacao reutilizado com outro comando.")
        return anterior.resultado
    doc = None
    row = instrumento
    if registro_id:
        doc = registros_collection().find_one({"_id": registro_id, "instrumento_id": str(instrumento_id)})
        if not doc:
            raise HTTPException(404, "Registro nao encontrado.")
        row = controle(db, instrumento_id, registro_id, doc)
        if row.versao != doc.get("_revision", 1):
            raise HTTPException(409, "Registro necessita reconciliacao antes de revisar ou publicar.")
        estado, versao = row.status_editorial, row.versao
    else:
        estado, versao = instrumento.status, instrumento.versao_editorial
    if versao != payload.versao:
        raise HTTPException(409, "Versao alterada. Recarregue o registro.")
    _, destino, _ = validar_transicao(acao, estado, payload.justificativa)
    if registro_id and row.status_operacional == "EXCLUIDO" and acao != "arquivar":
        raise HTTPException(409, "Registro excluido nao pode ser reaberto ou publicado.")
    if registro_id and acao in {"enviar-revisao", "aprovar", "publicar"} and row.status_operacional != "ATIVO":
        raise HTTPException(409, "Registro inativo ou excluido nao pode seguir o fluxo editorial.")
    refs = referencias(db, instrumento_id, registro_id) if registro_id and acao in {"aprovar", "publicar"} else []
    if registro_id and acao == "aprovar":
        row.aprovacao_hash = assinatura(db, instrumento, doc, refs)
    if acao == "publicar":
        if registro_id:
            if not instrumento.publicacao_id:
                raise HTTPException(409, "Publique o schema do instrumento antes do registro.")
            if row.aprovacao_hash != assinatura(db, instrumento, doc, refs):
                raise HTTPException(409, "Conteudo ou schema alterado apos aprovacao. Devolva para nova revisao.")
            from app.services.registro_service import _validar
            _validar(instrumento.campos, doc.get("dados", {}))
            snapshot = {"_id": str(payload.operacao_id), "instrumento_id": str(instrumento_id),
                "registro_id": registro_id, "versao": versao, "schema_id": str(instrumento.publicacao_id),
                "dados": doc.get("dados", {}), "schema_version": doc.get("schema_version", 1)}
            snapshot["imagens"] = refs
            for reference in refs:
                db.add(PublicacaoImagem(snapshot_id=snapshot["_id"], imagem_id=uuid.UUID(reference["imagem_id"]), instrumento_id=instrumento_id,
                                       referencia=reference))
            # An insert-only snapshot can survive a failed SQL commit, but is never visible without its pointer.
            snapshots_collection().update_one({"_id": snapshot["_id"]}, {"$setOnInsert": snapshot}, upsert=True)
            persisted = snapshots_collection().find_one({"_id": snapshot["_id"]})
            if persisted != snapshot:
                raise HTTPException(409, "Snapshot da operacao diverge da versao atual.")
            row.snapshot_id, row.versao_publicada = snapshot["_id"], versao
        else:
            publication = PublicacaoInstrumento(id=payload.operacao_id, instrumento_id=instrumento_id,
                versao=versao, usuario_id=usuario.id,
                schema_json=InstrumentoSchema.model_validate(instrumento).model_dump(mode="json"))
            db.add(publication)
            instrumento.publicacao_id = publication.id
    if registro_id:
        row.status_editorial = destino
        if acao == "arquivar":
            row.snapshot_id = None
        if acao == "reabrir":
            row.versao += 1
            registros_collection().update_one({"_id": registro_id, "instrumento_id": str(instrumento_id)},
                                               {"$set": {"_revision": row.versao}})
    else:
        instrumento.status = destino
        if acao == "arquivar":
            instrumento.publicacao_id = None
        if acao == "reabrir":
            instrumento.versao_editorial += 1
    if acao in {"publicar", "arquivar", "reabrir"}:
        invalidar_publicacao(db, instrumento)
    resultado = {"status_editorial": destino, "versao": row.versao if registro_id else instrumento.versao_editorial,
                 "operacao_id": str(payload.operacao_id)}
    db.add(EventoEditorial(id=payload.operacao_id, instrumento_id=instrumento_id, registro_id=registro_id,
        usuario_id=usuario.id, agente=usuario.nome, acao=acao, estado_anterior=estado, estado_novo=destino,
        versao=payload.versao, justificativa=payload.justificativa, resultado=resultado))
    db.commit()
    return resultado


def historico(db, instrumento_id, registro_id=None, limit=20, offset=0):
    require(db, "editorial_consultar", instrumento_id)
    query = select(EventoEditorial).where(EventoEditorial.instrumento_id == instrumento_id,
                                         EventoEditorial.registro_id == registro_id)
    rows = db.scalars(query.order_by(EventoEditorial.criado_em.desc(), EventoEditorial.id.desc()).limit(limit + 1).offset(offset)).all()
    return {"items": [{"id": str(e.id), "acao": e.acao, "data": e.criado_em, "agente": e.agente,
                      "estado_anterior": e.estado_anterior, "estado_novo": e.estado_novo,
                      "versao": e.versao, "justificativa": e.justificativa} for e in rows[:limit]],
            "has_more": len(rows) > limit}
