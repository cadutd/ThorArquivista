from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.models.enums import StatusInstrumentoPesquisa, TipoInstrumentoPesquisa, VisibilidadeInstrumentoPesquisa
from app.schemas.instrumento_campo import (
    InstrumentoCampoCreate,
    InstrumentoCampoOut,
    InstrumentoCampoReordenar,
    InstrumentoCampoUpdate,
)
from app.schemas.instrumento_pesquisa import (
    InstrumentoPesquisaCreate,
    InstrumentoPesquisaOut,
    InstrumentoPesquisaPage,
    InstrumentoPesquisaSchema,
    InstrumentoPesquisaUpdate,
)
from app.schemas.instrumento_registro import (
    InstrumentoRegistroCreate,
    InstrumentoRegistroAdvancedSearch,
    InstrumentoRegistroFacets,
    InstrumentoRegistroOut,
    InstrumentoRegistroPage,
    InstrumentoRegistroSearch,
    InstrumentoRegistroUpdate,
    StatusInstrumentoRegistro,
)
from app.services.instrumento_campo_service import InstrumentoCampoService
from app.services.instrumento_pesquisa_service import InstrumentoPesquisaService
from app.services.instrumento_registro_service import InstrumentoRegistroService

router = APIRouter()


@router.post(
    "",
    response_model=InstrumentoPesquisaOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_instrumento_pesquisa(
    dados: InstrumentoPesquisaCreate,
    db: Session = Depends(db_dep),
):
    return InstrumentoPesquisaService.criar(db, dados)


@router.get("", response_model=InstrumentoPesquisaPage)
def listar_instrumentos_pesquisa(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    tipo: TipoInstrumentoPesquisa | None = None,
    status_instrumento: StatusInstrumentoPesquisa | None = Query(default=None, alias="status"),
    visibilidade: VisibilidadeInstrumentoPesquisa | None = None,
):
    items, total = InstrumentoPesquisaService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        tipo=tipo,
        status=status_instrumento,
        visibilidade=visibilidade,
    )
    return InstrumentoPesquisaPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{instrumento_id}/schema", response_model=InstrumentoPesquisaSchema)
def obter_schema_instrumento(
    instrumento_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    schema = InstrumentoPesquisaService.obter_schema(db, instrumento_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instrumento de pesquisa não encontrado.",
        )
    return schema


@router.post(
    "/{instrumento_id}/registros",
    response_model=InstrumentoRegistroOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_registro_instrumento(
    instrumento_id: uuid.UUID,
    dados: InstrumentoRegistroCreate,
    db: Session = Depends(db_dep),
):
    try:
        return InstrumentoRegistroService.criar(db, instrumento_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{instrumento_id}/registros",
    response_model=InstrumentoRegistroPage,
)
def listar_registros_instrumento(
    instrumento_id: uuid.UUID,
    db: Session = Depends(db_dep),
    page_size: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    status_registro: StatusInstrumentoRegistro | None = Query(default=None, alias="status"),
):
    try:
        return InstrumentoRegistroService.listar(
            db,
            instrumento_id,
            status=status_registro,
            page_size=page_size,
            cursor=cursor,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{instrumento_id}/buscar",
    response_model=InstrumentoRegistroPage,
)
def buscar_registros_instrumento(
    instrumento_id: uuid.UUID,
    dados: InstrumentoRegistroSearch,
    db: Session = Depends(db_dep),
):
    try:
        return InstrumentoRegistroService.buscar(
            db,
            instrumento_id,
            q=dados.q,
            page_size=dados.page_size,
            cursor=dados.cursor,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{instrumento_id}/buscar-avancado",
    response_model=InstrumentoRegistroPage,
)
def buscar_registros_instrumento_avancado(
    instrumento_id: uuid.UUID,
    dados: InstrumentoRegistroAdvancedSearch,
    db: Session = Depends(db_dep),
):
    try:
        return InstrumentoRegistroService.buscar_avancado(
            db,
            instrumento_id,
            q=dados.q,
            filters=dados.filters,
            sort=dados.sort,
            page_size=dados.page_size,
            cursor=dados.cursor,
            offset=dados.offset,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{instrumento_id}/facetas",
    response_model=InstrumentoRegistroFacets,
)
def listar_facetas_instrumento(
    instrumento_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    try:
        return {"facets": InstrumentoRegistroService.listar_facetas(db, instrumento_id)}
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{instrumento_id}/registros/{registro_id}",
    response_model=InstrumentoRegistroOut,
)
def obter_registro_instrumento(
    instrumento_id: uuid.UUID,
    registro_id: str,
    db: Session = Depends(db_dep),
):
    try:
        registro = InstrumentoRegistroService.obter(db, instrumento_id, registro_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not registro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro do instrumento não encontrado.")
    return registro


@router.put(
    "/{instrumento_id}/registros/{registro_id}",
    response_model=InstrumentoRegistroOut,
)
def atualizar_registro_instrumento(
    instrumento_id: uuid.UUID,
    registro_id: str,
    dados: InstrumentoRegistroUpdate,
    db: Session = Depends(db_dep),
):
    try:
        registro = InstrumentoRegistroService.atualizar(db, instrumento_id, registro_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not registro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro do instrumento não encontrado.")
    return registro


@router.delete(
    "/{instrumento_id}/registros/{registro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_registro_instrumento(
    instrumento_id: uuid.UUID,
    registro_id: str,
    db: Session = Depends(db_dep),
):
    try:
        excluido = InstrumentoRegistroService.excluir(db, instrumento_id, registro_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not excluido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro do instrumento não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{instrumento_id}/campos",
    response_model=InstrumentoCampoOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_campo_instrumento(
    instrumento_id: uuid.UUID,
    dados: InstrumentoCampoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return InstrumentoCampoService.criar(db, instrumento_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{instrumento_id}/campos",
    response_model=list[InstrumentoCampoOut],
)
def listar_campos_instrumento(
    instrumento_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    try:
        return InstrumentoCampoService.listar(db, instrumento_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{instrumento_id}/campos/reordenar",
    response_model=list[InstrumentoCampoOut],
)
def reordenar_campos_instrumento(
    instrumento_id: uuid.UUID,
    dados: InstrumentoCampoReordenar,
    db: Session = Depends(db_dep),
):
    try:
        return InstrumentoCampoService.reordenar(db, instrumento_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{instrumento_id}/campos/{campo_id}",
    response_model=InstrumentoCampoOut,
)
def obter_campo_instrumento(
    instrumento_id: uuid.UUID,
    campo_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    campo = InstrumentoCampoService.obter(db, instrumento_id, campo_id)
    if not campo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo do instrumento não encontrado.",
        )
    return campo


@router.put(
    "/{instrumento_id}/campos/{campo_id}",
    response_model=InstrumentoCampoOut,
)
def atualizar_campo_instrumento(
    instrumento_id: uuid.UUID,
    campo_id: uuid.UUID,
    dados: InstrumentoCampoUpdate,
    db: Session = Depends(db_dep),
):
    try:
        campo = InstrumentoCampoService.atualizar(db, instrumento_id, campo_id, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if not campo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo do instrumento não encontrado.",
        )
    return campo


@router.delete(
    "/{instrumento_id}/campos/{campo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_campo_instrumento(
    instrumento_id: uuid.UUID,
    campo_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    excluido = InstrumentoCampoService.excluir(db, instrumento_id, campo_id)
    if not excluido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo do instrumento não encontrado.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}", response_model=InstrumentoPesquisaOut)
def obter_instrumento_pesquisa(
    id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    instrumento = InstrumentoPesquisaService.obter_por_id(db, id)
    if not instrumento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instrumento de pesquisa não encontrado.",
        )
    return instrumento


@router.put("/{id}", response_model=InstrumentoPesquisaOut)
def atualizar_instrumento_pesquisa(
    id: uuid.UUID,
    dados: InstrumentoPesquisaUpdate,
    db: Session = Depends(db_dep),
):
    instrumento = InstrumentoPesquisaService.atualizar(db, id, dados)
    if not instrumento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instrumento de pesquisa não encontrado.",
        )
    return instrumento


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_instrumento_pesquisa(
    id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    try:
        excluido = InstrumentoPesquisaService.excluir(db, id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if not excluido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instrumento de pesquisa não encontrado.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
