from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.armazenamento import (
    AtribuirPosicaoRequest,
    CompartimentoArmazenamentoCreate,
    CompartimentoArmazenamentoRead,
    CompartimentoArmazenamentoUpdate,
    EstruturaArmazenamentoCreate,
    EstruturaArmazenamentoRead,
    EstruturaArmazenamentoUpdate,
    LocalGuardaCreate,
    LocalGuardaRead,
    LocalGuardaUpdate,
    MovimentacaoArmazenamentoRead,
    OcupacaoRead,
    PosicaoArmazenamentoCreate,
    PosicaoArmazenamentoRead,
    PosicaoArmazenamentoUpdate,
    TopografiaGeradaRead,
    ZonaGuardaCreate,
    ZonaGuardaRead,
    ZonaGuardaUpdate,
)
from app.schemas.copia_unidade_acondicionamento_digital import (
    CopiaUnidadeAcondicionamentoDigitalOut,
)
from app.schemas.midia_armazenamento import MidiaArmazenamentoOut
from app.schemas.unidade_acondicionamento import UnidadeAcondicionamentoOut
from app.services.armazenamento_service import ArmazenamentoService

router = APIRouter()


@router.get("/locais-guarda", response_model=list[LocalGuardaRead])
def listar_locais_guarda(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_locais(db, limit, offset)


@router.post(
    "/locais-guarda",
    response_model=LocalGuardaRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_local_guarda(dados: LocalGuardaCreate, db: Session = Depends(db_dep)):
    try:
        return ArmazenamentoService.criar_local(db, dados)
    except ValueError as e:
        raise _http_conflict(e)


@router.get("/locais-guarda/{id}", response_model=LocalGuardaRead)
def obter_local_guarda(id: int, db: Session = Depends(db_dep)):
    local = ArmazenamentoService.obter_local(db, id)
    if not local:
        raise _http_not_found("Local de guarda não encontrado.")
    return local


@router.put("/locais-guarda/{id}", response_model=LocalGuardaRead)
def atualizar_local_guarda(
    id: int,
    dados: LocalGuardaUpdate,
    db: Session = Depends(db_dep),
):
    try:
        local = ArmazenamentoService.atualizar_local(db, id, dados)
    except ValueError as e:
        raise _http_conflict(e)
    if not local:
        raise _http_not_found("Local de guarda não encontrado.")
    return local


@router.delete("/locais-guarda/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_local_guarda(id: int, db: Session = Depends(db_dep)):
    if not ArmazenamentoService.excluir_local(db, id):
        raise _http_not_found("Local de guarda não encontrado.")


@router.get("/locais-guarda/{id}/posicoes-ocupadas", response_model=list[PosicaoArmazenamentoRead])
def listar_posicoes_ocupadas_por_local(
    id: int,
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_posicoes(
        db,
        ocupada=True,
        id_local_guarda=id,
        limit=limit,
        offset=offset,
    )


@router.get("/locais-guarda/{id}/ocupacao", response_model=OcupacaoRead)
def obter_ocupacao_local(id: int, db: Session = Depends(db_dep)):
    try:
        return ArmazenamentoService.ocupacao_local(db, id)
    except LookupError as e:
        raise _http_not_found(str(e))


@router.get("/zonas-guarda", response_model=list[ZonaGuardaRead])
def listar_zonas_guarda(
    db: Session = Depends(db_dep),
    id_local_guarda: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_zonas(db, id_local_guarda, limit, offset)


@router.post(
    "/zonas-guarda",
    response_model=ZonaGuardaRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_zona_guarda(dados: ZonaGuardaCreate, db: Session = Depends(db_dep)):
    try:
        return ArmazenamentoService.criar_zona(db, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)


@router.get("/zonas-guarda/{id}", response_model=ZonaGuardaRead)
def obter_zona_guarda(id: int, db: Session = Depends(db_dep)):
    zona = ArmazenamentoService.obter_zona(db, id)
    if not zona:
        raise _http_not_found("Zona de guarda não encontrada.")
    return zona


@router.put("/zonas-guarda/{id}", response_model=ZonaGuardaRead)
def atualizar_zona_guarda(id: int, dados: ZonaGuardaUpdate, db: Session = Depends(db_dep)):
    try:
        zona = ArmazenamentoService.atualizar_zona(db, id, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)
    if not zona:
        raise _http_not_found("Zona de guarda não encontrada.")
    return zona


@router.delete("/zonas-guarda/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_zona_guarda(id: int, db: Session = Depends(db_dep)):
    if not ArmazenamentoService.excluir_zona(db, id):
        raise _http_not_found("Zona de guarda não encontrada.")


@router.post("/zonas-guarda/{id}/gerar-topografia", response_model=TopografiaGeradaRead)
def gerar_topografia(id: int, db: Session = Depends(db_dep)):
    try:
        return ArmazenamentoService.gerar_topografia(db, id)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)


@router.get("/zonas-guarda/{id}/posicoes-livres", response_model=list[PosicaoArmazenamentoRead])
def listar_posicoes_livres_por_zona(
    id: int,
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_posicoes(
        db,
        ocupada=False,
        id_zona_guarda=id,
        limit=limit,
        offset=offset,
    )


@router.get("/zonas-guarda/{id}/ocupacao", response_model=OcupacaoRead)
def obter_ocupacao_zona(id: int, db: Session = Depends(db_dep)):
    try:
        return ArmazenamentoService.ocupacao_zona(db, id)
    except LookupError as e:
        raise _http_not_found(str(e))


@router.get("/estruturas-armazenamento", response_model=list[EstruturaArmazenamentoRead])
def listar_estruturas_armazenamento(
    db: Session = Depends(db_dep),
    id_zona_guarda: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_estruturas(db, id_zona_guarda, limit, offset)


@router.post(
    "/estruturas-armazenamento",
    response_model=EstruturaArmazenamentoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_estrutura_armazenamento(
    dados: EstruturaArmazenamentoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return ArmazenamentoService.criar_estrutura(db, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)


@router.get("/estruturas-armazenamento/{id}", response_model=EstruturaArmazenamentoRead)
def obter_estrutura_armazenamento(id: int, db: Session = Depends(db_dep)):
    estrutura = ArmazenamentoService.obter_estrutura(db, id)
    if not estrutura:
        raise _http_not_found("Estrutura de armazenamento não encontrada.")
    return estrutura


@router.put("/estruturas-armazenamento/{id}", response_model=EstruturaArmazenamentoRead)
def atualizar_estrutura_armazenamento(
    id: int,
    dados: EstruturaArmazenamentoUpdate,
    db: Session = Depends(db_dep),
):
    try:
        estrutura = ArmazenamentoService.atualizar_estrutura(db, id, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)
    if not estrutura:
        raise _http_not_found("Estrutura de armazenamento não encontrada.")
    return estrutura


@router.delete("/estruturas-armazenamento/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_estrutura_armazenamento(id: int, db: Session = Depends(db_dep)):
    if not ArmazenamentoService.excluir_estrutura(db, id):
        raise _http_not_found("Estrutura de armazenamento não encontrada.")


@router.get("/compartimentos-armazenamento", response_model=list[CompartimentoArmazenamentoRead])
def listar_compartimentos_armazenamento(
    db: Session = Depends(db_dep),
    id_estrutura_armazenamento: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_compartimentos(
        db,
        id_estrutura_armazenamento,
        limit,
        offset,
    )


@router.post(
    "/compartimentos-armazenamento",
    response_model=CompartimentoArmazenamentoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_compartimento_armazenamento(
    dados: CompartimentoArmazenamentoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return ArmazenamentoService.criar_compartimento(db, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)


@router.get("/compartimentos-armazenamento/{id}", response_model=CompartimentoArmazenamentoRead)
def obter_compartimento_armazenamento(id: int, db: Session = Depends(db_dep)):
    compartimento = ArmazenamentoService.obter_compartimento(db, id)
    if not compartimento:
        raise _http_not_found("Compartimento de armazenamento não encontrado.")
    return compartimento


@router.put("/compartimentos-armazenamento/{id}", response_model=CompartimentoArmazenamentoRead)
def atualizar_compartimento_armazenamento(
    id: int,
    dados: CompartimentoArmazenamentoUpdate,
    db: Session = Depends(db_dep),
):
    try:
        compartimento = ArmazenamentoService.atualizar_compartimento(db, id, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)
    if not compartimento:
        raise _http_not_found("Compartimento de armazenamento não encontrado.")
    return compartimento


@router.delete("/compartimentos-armazenamento/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_compartimento_armazenamento(id: int, db: Session = Depends(db_dep)):
    if not ArmazenamentoService.excluir_compartimento(db, id):
        raise _http_not_found("Compartimento de armazenamento não encontrado.")


@router.get("/posicoes-armazenamento", response_model=list[PosicaoArmazenamentoRead])
def listar_posicoes_armazenamento(
    db: Session = Depends(db_dep),
    id_zona_guarda: int | None = Query(default=None, ge=1),
    id_local_guarda: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_posicoes(
        db,
        id_zona_guarda=id_zona_guarda,
        id_local_guarda=id_local_guarda,
        limit=limit,
        offset=offset,
    )


@router.get("/posicoes-armazenamento/livres", response_model=list[PosicaoArmazenamentoRead])
def listar_posicoes_livres(
    db: Session = Depends(db_dep),
    id_zona_guarda: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_posicoes(
        db,
        ocupada=False,
        id_zona_guarda=id_zona_guarda,
        limit=limit,
        offset=offset,
    )


@router.get("/posicoes-armazenamento/ocupadas", response_model=list[PosicaoArmazenamentoRead])
def listar_posicoes_ocupadas(
    db: Session = Depends(db_dep),
    id_local_guarda: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_posicoes(
        db,
        ocupada=True,
        id_local_guarda=id_local_guarda,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/posicoes-armazenamento",
    response_model=PosicaoArmazenamentoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_posicao_armazenamento(dados: PosicaoArmazenamentoCreate, db: Session = Depends(db_dep)):
    try:
        return ArmazenamentoService.criar_posicao(db, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)


@router.get("/posicoes-armazenamento/{id}", response_model=PosicaoArmazenamentoRead)
def obter_posicao_armazenamento(id: int, db: Session = Depends(db_dep)):
    posicao = ArmazenamentoService.obter_posicao(db, id)
    if not posicao:
        raise _http_not_found("Posição de armazenamento não encontrada.")
    return posicao


@router.put("/posicoes-armazenamento/{id}", response_model=PosicaoArmazenamentoRead)
def atualizar_posicao_armazenamento(
    id: int,
    dados: PosicaoArmazenamentoUpdate,
    db: Session = Depends(db_dep),
):
    try:
        posicao = ArmazenamentoService.atualizar_posicao(db, id, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_conflict(e)
    if not posicao:
        raise _http_not_found("Posição de armazenamento não encontrada.")
    return posicao


@router.delete("/posicoes-armazenamento/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_posicao_armazenamento(id: int, db: Session = Depends(db_dep)):
    try:
        if not ArmazenamentoService.excluir_posicao(db, id):
            raise _http_not_found("Posição de armazenamento não encontrada.")
    except ValueError as e:
        raise _http_conflict(e)


@router.post(
    "/unidades-acondicionamento/{id}/atribuir-posicao",
    response_model=UnidadeAcondicionamentoOut,
)
def atribuir_posicao_unidade(
    id: int,
    dados: AtribuirPosicaoRequest,
    db: Session = Depends(db_dep),
):
    try:
        return ArmazenamentoService.atribuir_posicao_unidade(db, id, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_bad_request(e)


@router.get(
    "/unidades-acondicionamento/{id}/localizacao",
    response_model=PosicaoArmazenamentoRead | None,
)
def obter_localizacao_unidade(id: int, db: Session = Depends(db_dep)):
    try:
        return ArmazenamentoService.localizacao_unidade(db, id)
    except LookupError as e:
        raise _http_not_found(str(e))


@router.post(
    "/midias-armazenamento/{id}/atribuir-posicao",
    response_model=MidiaArmazenamentoOut,
)
def atribuir_posicao_midia(
    id: int,
    dados: AtribuirPosicaoRequest,
    db: Session = Depends(db_dep),
):
    try:
        return ArmazenamentoService.atribuir_posicao_midia(db, id, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_bad_request(e)


@router.post(
    "/copias-unidades-acondicionamento-digitais/{id}/atribuir-posicao",
    response_model=CopiaUnidadeAcondicionamentoDigitalOut,
)
def atribuir_posicao_copia(
    id: int,
    dados: AtribuirPosicaoRequest,
    db: Session = Depends(db_dep),
):
    try:
        return ArmazenamentoService.atribuir_posicao_copia(db, id, dados)
    except LookupError as e:
        raise _http_not_found(str(e))
    except ValueError as e:
        raise _http_bad_request(e)


@router.get("/movimentacoes-armazenamento", response_model=list[MovimentacaoArmazenamentoRead])
def listar_movimentacoes_armazenamento(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return ArmazenamentoService.listar_movimentacoes(db, limit, offset)


@router.get(
    "/movimentacoes-armazenamento/unidade/{id}",
    response_model=list[MovimentacaoArmazenamentoRead],
)
def listar_movimentacoes_unidade(id: int, db: Session = Depends(db_dep)):
    return ArmazenamentoService.listar_movimentacoes_unidade(db, id)


@router.get(
    "/movimentacoes-armazenamento/midia/{id}",
    response_model=list[MovimentacaoArmazenamentoRead],
)
def listar_movimentacoes_midia(id: int, db: Session = Depends(db_dep)):
    return ArmazenamentoService.listar_movimentacoes_midia(db, id)


@router.get(
    "/movimentacoes-armazenamento/copia/{id}",
    response_model=list[MovimentacaoArmazenamentoRead],
)
def listar_movimentacoes_copia(id: int, db: Session = Depends(db_dep)):
    return ArmazenamentoService.listar_movimentacoes_copia(db, id)


def _http_not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def _http_conflict(error: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


def _http_bad_request(error: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
