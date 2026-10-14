import uuid
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import db_dep
from app.models.editorial import PublicacaoInstrumento
from app.models.instrumento import Instrumento
from app.services import publicacao_service as service
from pydantic import BaseModel, ConfigDict, Field


class BuscaPublicaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str = Field(default="", max_length=1000)
    filtros: dict = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

router = APIRouter(prefix="/publico")


@router.post("/instrumentos/{instrumento_id}/buscar")
def buscar_post(instrumento_id: uuid.UUID, payload: BuscaPublicaIn, db: Session = Depends(db_dep)):
    return service.buscar(db, instrumento_id, payload.q, payload.limit, payload.offset, filtros=payload.filtros)


@router.get("/instrumentos")
def instrumentos(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    query = select(PublicacaoInstrumento).join(Instrumento, Instrumento.publicacao_id == PublicacaoInstrumento.id).where(
        Instrumento.visibilidade == "PUBLICO", Instrumento.status != "ARQUIVADO")
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(PublicacaoInstrumento.criado_em.desc(), PublicacaoInstrumento.id).limit(limit).offset(offset))
    return {"items": [{"id": str(r.instrumento_id), "nome": r.schema_json["nome"],
                      "descricao": r.schema_json.get("descricao")} for r in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/instrumentos/{instrumento_id}")
def instrumento(instrumento_id: uuid.UUID, db: Session = Depends(db_dep)):
    i = service.publico(db, instrumento_id, lock=True)
    schema = db.get(PublicacaoInstrumento, i.publicacao_id).schema_json
    return {"id": str(i.id), "nome": schema["nome"], "descricao": schema.get("descricao"),
            "campos": service.campos_publicos(db, schema)}


@router.get("/instrumentos/{instrumento_id}/buscar")
def buscar(instrumento_id: uuid.UUID, q: str = "", limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
           filtros: str = Query("{}", max_length=10000), db: Session = Depends(db_dep)):
    try:
        parsed = json.loads(filtros)
        if not isinstance(parsed, dict):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "Filtros devem ser um objeto JSON.")
    return service.buscar(db, instrumento_id, q, limit, offset, filtros=parsed)


@router.get("/instrumentos/{instrumento_id}/facetas")
def facetas(instrumento_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.buscar(db, instrumento_id, "", 0, 0, facetas=True)["facetas"]


@router.get("/instrumentos/{instrumento_id}/registros/{registro_id}")
def registro(instrumento_id: uuid.UUID, registro_id: str, db: Session = Depends(db_dep)):
    return service.obter_registro(db, instrumento_id, registro_id)


@router.get("/instrumentos/{instrumento_id}/registros/{registro_id}/imagens")
def imagens(instrumento_id: uuid.UUID, registro_id: str, limit: int = Query(20, ge=1, le=100),
            offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    return service.galeria(db, instrumento_id, registro_id, limit, offset)
