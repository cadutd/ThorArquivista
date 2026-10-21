import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from app.api.deps import current_user, db_dep
from app.schemas.importacao import ConfiguracaoImportacao
from app.services import importacao_service as service
from app.services.importacao_arquivo import MAX_BYTES

router = APIRouter(prefix="/instrumentos/{instrumento_id}/registros/importacoes",
                   dependencies=[Depends(current_user)])


async def conteudo(arquivo):
    try:
        data = await arquivo.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "Arquivo excede 5 MiB.")
        return data
    finally:
        await arquivo.close()


def config(raw):
    try:
        return ConfiguracaoImportacao.model_validate_json(raw)
    except ValidationError:
        raise HTTPException(422, "Configuracao invalida. Confira o mapeamento, tipos, chaves e campos obrigatorios.")


@router.get("")
def listar(instrumento_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.listar(db, instrumento_id)


@router.post("/analisar")
async def analisar(instrumento_id: uuid.UUID, arquivo: UploadFile = File(...), db: Session = Depends(db_dep)):
    return await run_in_threadpool(service.analisar, db, instrumento_id, await conteudo(arquivo), arquivo.filename)


@router.post("/validar")
async def validar(instrumento_id: uuid.UUID, arquivo: UploadFile = File(...), configuracao: str = Form(..., max_length=100000),
                  db: Session = Depends(db_dep)):
    return await run_in_threadpool(service.validar, db, instrumento_id, await conteudo(arquivo), arquivo.filename, config(configuracao))


@router.post("")
async def executar(instrumento_id: uuid.UUID, arquivo: UploadFile = File(...), configuracao: str = Form(..., max_length=100000),
                   db: Session = Depends(db_dep)):
    return await run_in_threadpool(service.executar, db, instrumento_id, await conteudo(arquivo), arquivo.filename, config(configuracao))
