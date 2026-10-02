from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_dep
from app.models.user import Usuario
from app.schemas.busca import BuscaAvancadaIn, BuscaAvancadaOut, FacetasOut, ReindexacaoOut
from app.schemas.instrumento import InstrumentoCreate, InstrumentoOut, InstrumentoPage, InstrumentoSchema, InstrumentoUpdate
from app.schemas.instrumento_campo import InstrumentoCampoCreate, InstrumentoCampoOut, InstrumentoCampoUpdate
from app.schemas.registro import RegistroCreate, RegistroOut, RegistroPage, RegistroSearch, RegistroUpdate
from app.services import indexacao_service
from app.services import instrumento_service, registro_service

router = APIRouter()


@router.get("", response_model=InstrumentoPage)
def listar_instrumentos(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = None,
    db: Session = Depends(db_dep),
    _usuario: Usuario = Depends(current_user),
) -> InstrumentoPage:
    items, total = instrumento_service.listar_instrumentos(db, limit, offset, q)
    return InstrumentoPage(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=InstrumentoOut, status_code=status.HTTP_201_CREATED)
def criar_instrumento(payload: InstrumentoCreate, db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return instrumento_service.criar_instrumento(db, payload, usuario.id)


@router.get("/{instrumento_id}", response_model=InstrumentoOut)
def obter_instrumento(instrumento_id: uuid.UUID, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    instrumento = instrumento_service.obter_instrumento(db, instrumento_id)
    if not instrumento:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    return instrumento


@router.get("/{instrumento_id}/schema", response_model=InstrumentoSchema)
def obter_schema(instrumento_id: uuid.UUID, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    instrumento = instrumento_service.obter_instrumento(db, instrumento_id)
    if not instrumento:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    return instrumento


@router.put("/{instrumento_id}", response_model=InstrumentoOut)
def atualizar_instrumento(instrumento_id: uuid.UUID, payload: InstrumentoUpdate, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return instrumento_service.atualizar_instrumento(db, instrumento_id, payload)


@router.delete("/{instrumento_id}")
def excluir_instrumento(instrumento_id: uuid.UUID, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    instrumento_service.excluir_instrumento(db, instrumento_id)
    return {"status": "ok"}


@router.get("/{instrumento_id}/campos", response_model=list[InstrumentoCampoOut])
def listar_campos(instrumento_id: uuid.UUID, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return instrumento_service.listar_campos(db, instrumento_id)


@router.post("/{instrumento_id}/campos", response_model=InstrumentoCampoOut, status_code=status.HTTP_201_CREATED)
def criar_campo(instrumento_id: uuid.UUID, payload: InstrumentoCampoCreate, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return instrumento_service.criar_campo(db, instrumento_id, payload)


@router.put("/{instrumento_id}/campos/{campo_id}", response_model=InstrumentoCampoOut)
def atualizar_campo(instrumento_id: uuid.UUID, campo_id: uuid.UUID, payload: InstrumentoCampoUpdate, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return instrumento_service.atualizar_campo(db, instrumento_id, campo_id, payload)


@router.delete("/{instrumento_id}/campos/{campo_id}")
def excluir_campo(instrumento_id: uuid.UUID, campo_id: uuid.UUID, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    instrumento_service.excluir_campo(db, instrumento_id, campo_id)
    return {"status": "ok"}


@router.post("/{instrumento_id}/registros", response_model=RegistroOut, status_code=status.HTTP_201_CREATED)
def criar_registro(instrumento_id: uuid.UUID, payload: RegistroCreate, db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return registro_service.criar_registro(db, instrumento_id, payload, usuario.id)


@router.get("/{instrumento_id}/registros", response_model=RegistroPage)
def listar_registros(
    instrumento_id: uuid.UUID,
    page_size: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    db: Session = Depends(db_dep),
    _usuario: Usuario = Depends(current_user),
):
    return registro_service.listar_registros(db, instrumento_id, page_size, cursor)


@router.post("/{instrumento_id}/buscar", response_model=RegistroPage)
def buscar_registros(instrumento_id: uuid.UUID, payload: RegistroSearch, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return registro_service.buscar_registros(db, instrumento_id, payload.q, payload.page_size, payload.cursor)


@router.post("/{instrumento_id}/buscar-avancado", response_model=BuscaAvancadaOut)
def buscar_registros_avancado(instrumento_id: uuid.UUID, payload: BuscaAvancadaIn, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return indexacao_service.buscar_avancado(db, instrumento_id, payload)


@router.get("/{instrumento_id}/facetas", response_model=FacetasOut)
def obter_facetas(instrumento_id: uuid.UUID, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return indexacao_service.facetas(db, instrumento_id)


@router.post("/{instrumento_id}/reindexar", response_model=ReindexacaoOut, status_code=status.HTTP_202_ACCEPTED)
def reindexar_instrumento(instrumento_id: uuid.UUID, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return indexacao_service.criar_job_reindexacao(db, instrumento_id)


@router.get("/{instrumento_id}/registros/{registro_id}", response_model=RegistroOut)
def obter_registro(instrumento_id: uuid.UUID, registro_id: str, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    return registro_service.obter_registro(db, instrumento_id, registro_id)


@router.put("/{instrumento_id}/registros/{registro_id}", response_model=RegistroOut)
def atualizar_registro(instrumento_id: uuid.UUID, registro_id: str, payload: RegistroUpdate, db: Session = Depends(db_dep), usuario: Usuario = Depends(current_user)):
    return registro_service.atualizar_registro(db, instrumento_id, registro_id, payload, usuario.id)


@router.delete("/{instrumento_id}/registros/{registro_id}")
def excluir_registro(instrumento_id: uuid.UUID, registro_id: str, db: Session = Depends(db_dep), _usuario: Usuario = Depends(current_user)):
    registro_service.excluir_registro(db, instrumento_id, registro_id)
    return {"status": "ok"}
