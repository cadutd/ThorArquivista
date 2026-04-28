from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.descricao_arquivistica import (
    RegistroDescritivoBatchCreate,
    RegistroDescritivoCreate,
    RegistroDescritivoDuplicate,
    EAD2002ImportResult,
    RegistroDescritivoMove,
    RegistroDescritivoRead,
    RegistroDescritivoTreeNode,
    RegistroDescritivoUpdate,
    RegistroUnidadesAssociadasRead,
    RegistroUnidadesAssociadasUpdate,
)
from app.services.descricao_arquivistica_service import DescricaoArquivisticaService
from app.services.ead2002_service import EAD2002Service
from app.models.descricao_arquivistica import RegistroDescritivo

router = APIRouter()


@router.get("/registros", response_model=list[RegistroDescritivoRead])
def listar_registros(
    db: Session = Depends(db_dep),
    q: str | None = Query(default=None),
    nivel: str | None = Query(default=None),
):
    return [
        _with_children_flag(db, registro)
        for registro in DescricaoArquivisticaService.listar(db, q=q, nivel=nivel)
    ]


@router.get("/registros/arvore", response_model=list[RegistroDescritivoTreeNode])
def obter_arvore(
    db: Session = Depends(db_dep),
    q: str | None = Query(default=None),
    nivel: str | None = Query(default=None),
):
    return DescricaoArquivisticaService.arvore(db, q=q, nivel=nivel)


@router.post("/registros", response_model=RegistroDescritivoRead, status_code=status.HTTP_201_CREATED)
def criar_registro(dados: RegistroDescritivoCreate, db: Session = Depends(db_dep)):
    try:
        return _with_children_flag(db, DescricaoArquivisticaService.criar(db, dados))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/registros/lote", response_model=list[RegistroDescritivoRead], status_code=status.HTTP_201_CREATED)
def criar_lote(dados: RegistroDescritivoBatchCreate, db: Session = Depends(db_dep)):
    try:
        return [_with_children_flag(db, registro) for registro in DescricaoArquivisticaService.criar_lote(db, dados)]
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/registros/{id}", response_model=RegistroDescritivoRead)
def obter_registro(id: uuid.UUID, db: Session = Depends(db_dep)):
    registro = DescricaoArquivisticaService.obter(db, id)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return _with_children_flag(db, registro)


@router.get("/registros/{id}/unidades", response_model=RegistroUnidadesAssociadasRead)
def listar_unidades_associadas(id: uuid.UUID, db: Session = Depends(db_dep)):
    unidades = DescricaoArquivisticaService.listar_unidades_associadas(db, id)
    if unidades is None:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return {"id_registro_descritivo": id, "unidades": unidades}


@router.put("/registros/{id}/unidades", response_model=RegistroUnidadesAssociadasRead)
def atualizar_unidades_associadas(
    id: uuid.UUID,
    dados: RegistroUnidadesAssociadasUpdate,
    db: Session = Depends(db_dep),
):
    try:
        unidades = DescricaoArquivisticaService.substituir_unidades_associadas(
            db,
            id,
            dados.unidades_ids,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if unidades is None:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return {"id_registro_descritivo": id, "unidades": unidades}


@router.get("/registros/{id}/exportar/ead2002")
def exportar_registro_ead2002(id: uuid.UUID, db: Session = Depends(db_dep)):
    content = EAD2002Service.exportar(db, id)
    if content is None:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return Response(
        content=content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="ead2002-{id}.xml"'},
    )


@router.post("/importar/ead2002", response_model=EAD2002ImportResult, status_code=status.HTTP_201_CREATED)
def importar_ead2002(
    content: bytes = Body(..., media_type="application/xml"),
    db: Session = Depends(db_dep),
):
    try:
        return EAD2002Service.importar(db, content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/registros/{id}", response_model=RegistroDescritivoRead)
def atualizar_registro(id: uuid.UUID, dados: RegistroDescritivoUpdate, db: Session = Depends(db_dep)):
    try:
        registro = DescricaoArquivisticaService.atualizar(db, id, dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not registro:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return _with_children_flag(db, registro)


@router.delete("/registros/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_registro(
    id: uuid.UUID,
    db: Session = Depends(db_dep),
    cascade: bool = Query(default=False),
):
    try:
        deleted = DescricaoArquivisticaService.excluir(db, id, cascade=cascade)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/registros/{id}/duplicar", response_model=RegistroDescritivoRead, status_code=status.HTTP_201_CREATED)
def duplicar_registro(id: uuid.UUID, dados: RegistroDescritivoDuplicate, db: Session = Depends(db_dep)):
    try:
        registro = DescricaoArquivisticaService.duplicar(db, id, dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not registro:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return _with_children_flag(db, registro)


@router.post("/registros/{id}/mover", response_model=RegistroDescritivoRead)
def mover_registro(id: uuid.UUID, dados: RegistroDescritivoMove, db: Session = Depends(db_dep)):
    try:
        registro = DescricaoArquivisticaService.mover(db, id, dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not registro:
        raise HTTPException(status_code=404, detail="Registro descritivo não encontrado.")
    return _with_children_flag(db, registro)


def _with_children_flag(db: Session, registro):
    registro.has_children = bool(
        db.query(RegistroDescritivo.id)
        .filter(RegistroDescritivo.parent_id == registro.id)
        .first()
    )
    return registro
