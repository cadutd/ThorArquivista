import uuid
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import db_dep, current_identity, current_user
from app.services import portal_service
from app.schemas.portal import ConfiguracaoPortalIn
from app.services.permissao_service import require
from app.models.editorial import PublicacaoInstrumento
from app.services import publicacao_service as service
from pydantic import BaseModel, ConfigDict, Field


class BuscaPublicaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str = Field(default="", max_length=1000)
    filtros: dict = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

router = APIRouter(prefix="/publico")


@router.get("/configuracao")
def configuracao(db: Session = Depends(db_dep)):
    return portal_service.configuracao(db)


@router.get("/destaques")
def destaques(limit: int = Query(6, ge=1, le=12), db: Session = Depends(db_dep)):
    return portal_service.destaques(db, limit)


@router.get("/configuracao/administracao", dependencies=[Depends(current_user)])
def configuracao_admin(db: Session = Depends(db_dep)):
    require(db, "portal_configuracao_consultar")
    return portal_service.configuracao(db)


@router.put("/configuracao/administracao", dependencies=[Depends(current_user)])
def configurar(payload: ConfiguracaoPortalIn, db: Session = Depends(db_dep)):
    return portal_service.salvar(db, payload)


@router.post("/instrumentos/{instrumento_id}/buscar", dependencies=[Depends(current_identity)])
def buscar_post(instrumento_id: uuid.UUID, payload: BuscaPublicaIn, db: Session = Depends(db_dep)):
    return service.buscar(db, instrumento_id, payload.q, payload.limit, payload.offset, filtros=payload.filtros)


@router.get("/instrumentos")
def instrumentos(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                 q: str = Query("", max_length=150), tipo: str = Query("", max_length=30),
                 nome: str = Query("", max_length=255), descricao: str = Query("", max_length=1000), db: Session = Depends(db_dep)):
    return portal_service.catalogo(db, limit, offset, q, tipo, nome, descricao)


@router.get("/instrumentos/{instrumento_id}/imagem-card/{capa_id}")
def imagem_card(instrumento_id: uuid.UUID, capa_id: uuid.UUID, db: Session = Depends(db_dep)):
    from app.services.capa_instrumento_service import publica
    return publica(db, instrumento_id, capa_id)

@router.post("/instrumentos/{instrumento_id}/acessos", status_code=204, dependencies=[Depends(current_identity)])
def acesso(instrumento_id: uuid.UUID, db: Session = Depends(db_dep)):
    portal_service.registrar_acesso(db, instrumento_id)


@router.get("/instrumentos/{instrumento_id}", dependencies=[Depends(current_identity)])
def instrumento(instrumento_id: uuid.UUID, db: Session = Depends(db_dep)):
    i = service.publico(db, instrumento_id, lock=True)
    schema = db.get(PublicacaoInstrumento, i.publicacao_id).schema_json
    return {"id": str(i.id), "nome": schema["nome"], "descricao": schema.get("descricao"),
            "campos": service.campos_publicos(db, schema)}


@router.get("/instrumentos/{instrumento_id}/buscar", dependencies=[Depends(current_identity)])
def buscar(instrumento_id: uuid.UUID, q: str = Query("", max_length=1000), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
           filtros: str = Query("{}", max_length=10000), db: Session = Depends(db_dep)):
    try:
        parsed = json.loads(filtros)
        if not isinstance(parsed, dict):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "Filtros devem ser um objeto JSON.")
    return service.buscar(db, instrumento_id, q, limit, offset, filtros=parsed)


@router.get("/instrumentos/{instrumento_id}/facetas", dependencies=[Depends(current_identity)])
def facetas(instrumento_id: uuid.UUID, db: Session = Depends(db_dep)):
    return service.buscar(db, instrumento_id, "", 0, 0, facetas=True)["facetas"]


@router.get("/instrumentos/{instrumento_id}/registros/{registro_id}", dependencies=[Depends(current_identity)])
def registro(instrumento_id: uuid.UUID, registro_id: str, db: Session = Depends(db_dep)):
    return service.obter_registro(db, instrumento_id, registro_id)


@router.get("/instrumentos/{instrumento_id}/registros/{registro_id}/imagens", dependencies=[Depends(current_identity)])
def imagens(instrumento_id: uuid.UUID, registro_id: str, limit: int = Query(20, ge=1, le=100),
            offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    return service.galeria(db, instrumento_id, registro_id, limit, offset)
