from __future__ import annotations

import uuid
from sqlalchemy import delete, func, or_, select, update
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.imagem import AuditoriaImagem, ImagemDocumento, RegistroImagem
from app.models.instrumento import Instrumento
from app.schemas.imagem import ImagemCreate, ImagemOut, TipoReferencia
from app.services.armazenamento_service import armazenamento, validar_imagem
from app.services.indexacao_service import enqueue_registro
from app.services.registro_service import obter_registro


def visiveis(usuario):
    return or_(ImagemDocumento.direitos_acesso != "RESTRITO", ImagemDocumento.criado_por == usuario.id)


def obter(db, imagem_id, usuario, editar=False, lock=False):
    query = select(ImagemDocumento).where(ImagemDocumento.id == imagem_id)
    if lock:
        query = query.with_for_update()
    imagem = db.scalar(query)
    if not imagem:
        raise HTTPException(404, "Imagem nao encontrada.")
    if (editar or imagem.direitos_acesso != "PUBLICO") and not usuario:
        raise HTTPException(401, "Autenticacao requerida.")
    if usuario and ((imagem.direitos_acesso == "RESTRITO" or editar) and imagem.criado_por != usuario.id):
        raise HTTPException(403, "Sem permissao para esta imagem.")
    return imagem


def saida(imagem):
    result = ImagemOut.model_validate(imagem)
    if imagem.object_key:
        result = result.model_copy(update={
            "uri": f"/api/v1/imagens/{imagem.id}/conteudo",
            "thumbnail_uri": f"/api/v1/imagens/{imagem.id}/conteudo?thumbnail=true",
        })
    return result


def listar(db, usuario, limit, offset, q=None, tipo=None, direitos=None):
    query = select(ImagemDocumento).where(visiveis(usuario))
    if q:
        query = query.where(or_(ImagemDocumento.titulo.ilike(f"%{q.strip()}%"), ImagemDocumento.descricao.ilike(f"%{q.strip()}%")))
    if tipo:
        query = query.where(ImagemDocumento.tipo_referencia == tipo)
    if direitos:
        query = query.where(ImagemDocumento.direitos_acesso == direitos)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(ImagemDocumento.criado_em.desc(), ImagemDocumento.id.desc()).limit(limit).offset(offset))
    return {"items": [saida(i) for i in items], "total": total, "limit": limit, "offset": offset}


def auditar(db, acao, usuario_id, imagem_id=None, instrumento_id=None, registro_id=None, **detalhe):
    db.add(AuditoriaImagem(acao=acao, usuario_id=usuario_id, imagem_id=imagem_id,
                           instrumento_id=instrumento_id, registro_id=registro_id, detalhe=detalhe))


def criar(db, payload, usuario):
    imagem = ImagemDocumento(**payload.model_dump(mode="json"), criado_por=usuario.id)
    db.add(imagem)
    db.flush()
    auditar(db, "CRIACAO", usuario.id, imagem.id, tipo=imagem.tipo_referencia)
    db.commit()
    db.refresh(imagem)
    return saida(imagem)


def upload(db, titulo, direitos, descricao, conteudo, mime_type, usuario, metadados=None):
    largura, altura, thumbnail = validar_imagem(conteudo, mime_type)
    imagem_id = uuid.uuid4()
    key, thumb_key = f"imagens/{imagem_id}/original", f"imagens/{imagem_id}/thumbnail.jpg"
    saved = []
    try:
        armazenamento.salvar_upload(key, conteudo, mime_type)
        saved.append(key)
        armazenamento.salvar_upload(thumb_key, thumbnail, "image/jpeg")
        saved.append(thumb_key)
        imagem = ImagemDocumento(
            id=imagem_id, titulo=titulo, descricao=descricao, tipo_referencia="UPLOAD",
            uri=f"s3://{key}", object_key=key, thumbnail_key=thumb_key,
            direitos_acesso=direitos, mime_type=mime_type, tamanho_bytes=len(conteudo),
            largura=largura, altura=altura, checksum_sha256=armazenamento.calcular_checksum(conteudo),
            criado_por=usuario.id, metadados_json=metadados or {},
        )
        db.add(imagem)
        auditar(db, "UPLOAD", usuario.id, imagem_id, checksum=imagem.checksum_sha256, tamanho=len(conteudo))
        db.commit()
    except Exception:
        db.rollback()
        for saved_key in saved:
            try:
                armazenamento.remover_objeto(saved_key)
            except HTTPException:
                pass
        raise
    # A failed read after commit must not remove objects of a persisted image.
    db.refresh(imagem)
    return saida(imagem)


def vinculados(db, imagem_id):
    return list(db.scalars(select(RegistroImagem).where(RegistroImagem.imagem_id == imagem_id)))


def notificar(vinculos):
    for vinculo in vinculos:
        enqueue_registro(vinculo.instrumento_id, vinculo.registro_id)


def atualizar(db, imagem_id, payload, usuario):
    imagem = obter(db, imagem_id, usuario, editar=True, lock=True)
    data = payload.model_dump(mode="json")
    if not imagem.object_key:
        try:
            validated = ImagemCreate(tipo_referencia=imagem.tipo_referencia, **data)
        except ValidationError as exc:
            raise HTTPException(422, "Referencia de imagem invalida.") from exc
        data = validated.model_dump(mode="json")
    else:
        for field in ("uri", "thumbnail_uri", "manifest_iiif_uri"):
            data.pop(field, None)
    for field, value in data.items():
        setattr(imagem, field, value)
    links = vinculados(db, imagem_id)
    auditar(db, "ATUALIZACAO", usuario.id, imagem_id, direitos=imagem.direitos_acesso)
    db.commit()
    db.refresh(imagem)
    notificar(links)
    return saida(imagem)


def excluir(db, imagem_id, usuario):
    imagem = obter(db, imagem_id, usuario, editar=True, lock=True)
    if vinculados(db, imagem_id):
        raise HTTPException(409, "Imagem vinculada a registros. Remova os vinculos antes de excluir.")
    if imagem.object_key:
        armazenamento.remover_objeto(imagem.object_key)
        if imagem.thumbnail_key:
            armazenamento.remover_objeto(imagem.thumbnail_key)
    auditar(db, "EXCLUSAO", usuario.id, imagem_id, titulo=imagem.titulo)
    db.delete(imagem)
    db.commit()


def registro(db, instrumento_id, registro_id, lock=False):
    if lock:
        db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
    result = obter_registro(db, instrumento_id, registro_id)
    if result.status == "EXCLUIDO":
        raise HTTPException(404, "Registro excluido.")
    return result


def listar_vinculos(db, instrumento_id, registro_id, usuario, limit, offset):
    registro(db, instrumento_id, registro_id)
    query = select(RegistroImagem, ImagemDocumento).join(ImagemDocumento).where(
        RegistroImagem.instrumento_id == instrumento_id, RegistroImagem.registro_id == registro_id, visiveis(usuario))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(RegistroImagem.ordem, RegistroImagem.imagem_id).limit(limit).offset(offset))
    return {"items": [vinculo_saida(v, i) for v, i in rows], "total": total, "limit": limit, "offset": offset}


def vinculo_saida(v, imagem):
    return {"instrumento_id": v.instrumento_id, "registro_id": v.registro_id, "imagem_id": v.imagem_id,
            "ordem": v.ordem, "principal": v.principal, "legenda": v.legenda, "imagem": saida(imagem)}


def vincular(db, instrumento_id, registro_id, payload, usuario):
    registro(db, instrumento_id, registro_id, lock=True)
    imagem = obter(db, payload.imagem_id, usuario, lock=True)
    key = (instrumento_id, registro_id, payload.imagem_id)
    if db.get(RegistroImagem, key):
        raise HTTPException(409, "Imagem ja vinculada.")
    ordem = db.scalar(select(func.max(RegistroImagem.ordem)).where(RegistroImagem.instrumento_id == instrumento_id, RegistroImagem.registro_id == registro_id))
    if payload.principal:
        limpar_principal(db, instrumento_id, registro_id)
    vinculo = RegistroImagem(instrumento_id=instrumento_id, registro_id=registro_id, imagem_id=payload.imagem_id,
                             ordem=(ordem + 1 if ordem is not None else 0), principal=payload.principal, legenda=payload.legenda)
    db.add(vinculo)
    auditar(db, "VINCULO", usuario.id, imagem.id, instrumento_id, registro_id)
    db.commit()
    db.refresh(vinculo)
    enqueue_registro(instrumento_id, registro_id)
    return vinculo_saida(vinculo, imagem)


def limpar_principal(db, instrumento_id, registro_id):
    db.execute(update(RegistroImagem).where(RegistroImagem.instrumento_id == instrumento_id, RegistroImagem.registro_id == registro_id).values(principal=False))
    db.flush()


def editar_vinculo(db, instrumento_id, registro_id, imagem_id, payload, usuario):
    registro(db, instrumento_id, registro_id, lock=True)
    imagem = obter(db, imagem_id, usuario)
    v = db.get(RegistroImagem, (instrumento_id, registro_id, imagem_id))
    if not v:
        raise HTTPException(404, "Vinculo nao encontrado.")
    if payload.principal:
        limpar_principal(db, instrumento_id, registro_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "principal" and value is None:
            raise HTTPException(422, "Principal nao pode ser nulo.")
        setattr(v, field, value)
    auditar(db, "ATUALIZACAO_VINCULO", usuario.id, imagem_id, instrumento_id, registro_id)
    db.commit()
    enqueue_registro(instrumento_id, registro_id)
    return vinculo_saida(v, imagem)


def reordenar(db, instrumento_id, registro_id, payload, usuario):
    registro(db, instrumento_id, registro_id, lock=True)
    ids = [i.imagem_id for i in payload.items]
    ordens = [i.ordem for i in payload.items]
    if len(set(ids)) != len(ids) or len(set(ordens)) != len(ordens):
        raise HTTPException(422, "Imagens e ordens devem ser unicas.")
    links = list(db.scalars(select(RegistroImagem).where(RegistroImagem.instrumento_id == instrumento_id, RegistroImagem.registro_id == registro_id)))
    by_id = {v.imagem_id: v for v in links}
    if any(i not in by_id for i in ids):
        raise HTTPException(404, "Vinculo nao encontrado.")
    final = {v.imagem_id: v.ordem for v in links}
    for item in payload.items:
        obter(db, item.imagem_id, usuario)
        final[item.imagem_id] = item.ordem
    if len(set(final.values())) != len(final):
        raise HTTPException(409, "Ordem ja utilizada por outro vinculo.")
    for item in payload.items:
        by_id[item.imagem_id].ordem = item.ordem
    auditar(db, "REORDENACAO", usuario.id, instrumento_id=instrumento_id, registro_id=registro_id, items=payload.model_dump(mode="json")["items"])
    db.commit()
    enqueue_registro(instrumento_id, registro_id)


def desvincular(db, instrumento_id, registro_id, imagem_id, usuario):
    registro(db, instrumento_id, registro_id, lock=True)
    obter(db, imagem_id, usuario)
    v = db.get(RegistroImagem, (instrumento_id, registro_id, imagem_id))
    if not v:
        raise HTTPException(404, "Vinculo nao encontrado.")
    auditar(db, "DESVINCULO", usuario.id, imagem_id, instrumento_id, registro_id)
    db.delete(v)
    db.commit()
    enqueue_registro(instrumento_id, registro_id)


def limpar_vinculos(db, instrumento_id, registro_id=None, usuario_id=None):
    query = select(RegistroImagem).where(RegistroImagem.instrumento_id == instrumento_id)
    if registro_id is not None:
        query = query.where(RegistroImagem.registro_id == registro_id)
    for v in db.scalars(query):
        auditar(db, "DESVINCULO_EXCLUSAO", usuario_id, v.imagem_id, v.instrumento_id, v.registro_id)
        db.delete(v)
    db.flush()


def resumos(db, instrumento_id, registro_ids, usuario=None):
    # One SQL query per MongoDB batch; restricted images never enter the search projection.
    query = select(RegistroImagem, ImagemDocumento).join(ImagemDocumento).where(
        RegistroImagem.instrumento_id == instrumento_id, RegistroImagem.registro_id.in_(registro_ids),
        visiveis(usuario) if usuario else ImagemDocumento.direitos_acesso == "PUBLICO").order_by(RegistroImagem.principal.desc(), RegistroImagem.ordem, RegistroImagem.imagem_id)
    result = {}
    for v, i in db.execute(query):
        resumo = result.setdefault(v.registro_id, {"possui_imagens": True, "total_imagens": 0, "imagem_principal_thumbnail":
            f"/api/v1/imagens/{i.id}/conteudo?thumbnail=true" if i.object_key else i.thumbnail_uri})
        resumo["total_imagens"] += 1
    return result
