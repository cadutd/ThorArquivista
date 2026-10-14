from __future__ import annotations

import uuid
import json
from fastapi import APIRouter, Cookie, Depends, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import current_user, db_dep
from app.core.config import settings
from app.models.user import Usuario
from app.schemas.imagem import DireitosAcesso, ImagemCreate, ImagemOut, ImagemPage, ImagemUpdate, ReordenarIn, TipoReferencia, VinculoCreate, VinculoOut, VinculoPage, VinculoUpdate
from app.services import imagem_service as service
from app.services.armazenamento_service import armazenamento
from app.services.permissao_service import require_imagens
from app.services.auth_service import get_usuario_by_session

router = APIRouter()


@router.get("/imagens", response_model=ImagemPage)
def listar(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), q: str | None = None,
           tipo: TipoReferencia | None = None, direitos: DireitosAcesso | None = None,
           db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return service.listar(db, usuario, limit, offset, q, tipo, direitos)


@router.post("/imagens", response_model=ImagemOut, status_code=201)
def criar(payload: ImagemCreate, db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return service.criar(db, payload, usuario)


@router.post("/imagens/upload", response_model=ImagemOut, status_code=201)
async def upload(arquivo: UploadFile = File(...), titulo: str = Form(..., min_length=1, max_length=255),
                 direitos_acesso: DireitosAcesso = Form(DireitosAcesso.INTERNO), descricao: str | None = Form(None),
                 metadados_json: str = Form("{}", max_length=10000),
                 db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    titulo = titulo.strip()
    if not titulo:
        raise HTTPException(422, "Titulo obrigatorio.")
    try:
        metadata = json.loads(metadados_json)
        if not isinstance(metadata, dict):
            raise ValueError()
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, "Metadados devem ser um objeto JSON.") from exc
    try:
        conteudo = await arquivo.read(settings.upload_max_bytes + 1)
        return await run_in_threadpool(service.upload, db, titulo, direitos_acesso.value, descricao, conteudo, arquivo.content_type or "", usuario, metadata)
    finally:
        await arquivo.close()


@router.get("/imagens/{imagem_id}", response_model=ImagemOut)
def obter(imagem_id: uuid.UUID, db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    require_imagens(db, usuario, "imagens_consultar")
    return service.saida(service.obter(db, imagem_id, usuario))


@router.put("/imagens/{imagem_id}", response_model=ImagemOut)
def atualizar(imagem_id: uuid.UUID, payload: ImagemUpdate, db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return service.atualizar(db, imagem_id, payload, usuario)


@router.delete("/imagens/{imagem_id}", status_code=204)
def excluir(imagem_id: uuid.UUID, db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    service.excluir(db, imagem_id, usuario)
    return Response(status_code=204)


@router.get("/imagens/{imagem_id}/conteudo")
def conteudo(imagem_id: uuid.UUID, thumbnail: bool = False, db: Session = Depends(db_dep),
             token: str | None = Cookie(None, alias=settings.session_cookie_name)):
    usuario = get_usuario_by_session(db, token)
    imagem = service.obter(db, imagem_id, usuario)
    if not imagem.object_key:
        if imagem.tipo_referencia == "IIIF" and not thumbnail:
            raise HTTPException(422, "Esta referencia e um manifest IIIF, nao um arquivo.")
        uri = imagem.thumbnail_uri if thumbnail else imagem.uri
        if not uri:
            raise HTTPException(404, "Miniatura nao disponivel.")
        return RedirectResponse(uri, status_code=307, headers={"Cache-Control": "private, no-store"})
    key = imagem.thumbnail_key if thumbnail else imagem.object_key
    if not key:
        raise HTTPException(404, "Miniatura nao disponivel.")
    obj = armazenamento.obter_objeto(key)
    body = obj["Body"]

    def chunks():
        try:
            yield from body.iter_chunks(chunk_size=65536)
        finally:
            body.close()

    return StreamingResponse(chunks(), media_type="image/jpeg" if thumbnail else imagem.mime_type,
                             headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "Content-Disposition": "inline"})


PREFIX = "/instrumentos/{instrumento_id}/registros/{registro_id}/imagens"


@router.get(PREFIX, response_model=VinculoPage)
def listar_vinculos(instrumento_id: uuid.UUID, registro_id: str, limit: int = Query(20, ge=1, le=100),
                    offset: int = Query(0, ge=0), db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return service.listar_vinculos(db, instrumento_id, registro_id, usuario, limit, offset)


@router.post(PREFIX, response_model=VinculoOut, status_code=201)
def vincular(instrumento_id: uuid.UUID, registro_id: str, payload: VinculoCreate,
             db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return service.vincular(db, instrumento_id, registro_id, payload, usuario)


@router.patch(PREFIX + "/reordenar", status_code=204)
def reordenar(instrumento_id: uuid.UUID, registro_id: str, payload: ReordenarIn,
              db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    service.reordenar(db, instrumento_id, registro_id, payload, usuario)
    return Response(status_code=204)


@router.patch(PREFIX + "/{imagem_id}", response_model=VinculoOut)
def editar_vinculo(instrumento_id: uuid.UUID, registro_id: str, imagem_id: uuid.UUID, payload: VinculoUpdate,
                   db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return service.editar_vinculo(db, instrumento_id, registro_id, imagem_id, payload, usuario)


@router.delete(PREFIX + "/{imagem_id}", status_code=204)
def desvincular(instrumento_id: uuid.UUID, registro_id: str, imagem_id: uuid.UUID,
                db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    service.desvincular(db, instrumento_id, registro_id, imagem_id, usuario)
    return Response(status_code=204)
