import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse
from app.api.deps import current_user, db_dep
from app.core.config import settings
from app.schemas.importacao import ConfiguracaoImportacao
from app.services import importacao_async_service as service

router = APIRouter(prefix="/instrumentos/{instrumento_id}/registros/importacoes/assincronas",
                   dependencies=[Depends(current_user)])


class SolicitarImportacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operacao_id: uuid.UUID
    nome_arquivo: str = Field(min_length=1, max_length=255)
    tamanho_bytes: int = Field(ge=1)


@router.get("/limites")
def limites(instrumento_id: uuid.UUID, db: Session = Depends(db_dep)):
    service.instrumento(db, instrumento_id)
    return service.limites()


@router.get("")
def listar(instrumento_id: uuid.UUID, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
           q: str = Query("", max_length=150), status: str = Query("", max_length=32), db: Session = Depends(db_dep)):
    return service.listar(db, instrumento_id, limit, offset, q, status)


@router.post("", status_code=201)
def solicitar(instrumento_id: uuid.UUID, payload: SolicitarImportacao, db: Session = Depends(db_dep)):
    return service.criar(db, instrumento_id, payload.operacao_id, payload.nome_arquivo, payload.tamanho_bytes)


@router.get("/{job_id}")
def obter(instrumento_id: uuid.UUID, job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.saida(service.obter(db, instrumento_id, job_id, exigir_arquivo=False))


@router.post("/{job_id}/partes")
async def partes(instrumento_id: uuid.UUID, job_id: uuid.UUID, numero: int = Query(..., ge=1),
                 arquivo: UploadFile = File(...), db: Session = Depends(db_dep)):
    try:
        data = await arquivo.read(settings.importacao_chunk_bytes + 1)
        if len(data) > settings.importacao_chunk_bytes:
            raise HTTPException(413, "Parte excede o limite configurado.")
        return await run_in_threadpool(service.parte, db, instrumento_id, job_id, numero, data)
    finally:
        await arquivo.close()


@router.post("/{job_id}/finalizar", status_code=202)
def finalizar(instrumento_id: uuid.UUID, job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.finalizar(db, instrumento_id, job_id)


@router.post("/{job_id}/validar", status_code=202)
def validar(instrumento_id: uuid.UUID, job_id: uuid.UUID, payload: ConfiguracaoImportacao, db: Session = Depends(db_dep)):
    return service.validar(db, instrumento_id, job_id, payload)


@router.post("/{job_id}/confirmar", status_code=202)
def confirmar(instrumento_id: uuid.UUID, job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.confirmar(db, instrumento_id, job_id)


@router.post("/{job_id}/cancelar")
def cancelar(instrumento_id: uuid.UUID, job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.cancelar(db, instrumento_id, job_id)


@router.post("/{job_id}/retomar", status_code=202)
def retomar(instrumento_id: uuid.UUID, job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.retomar(db, instrumento_id, job_id)


@router.get("/{job_id}/erros")
def erros(instrumento_id: uuid.UUID, job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return StreamingResponse(service.erros_csv(db, instrumento_id, job_id), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="erros-importacao-{job_id}.csv"'})
