from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.models.admissao import (
    CanalSubmissao,
    StatusProcessoAdmissao,
    StatusSessaoSubmissao,
    StatusSipAdmissao,
    TipoIngressoAdmissao,
    TipoProcessoAdmissao,
)
from app.models.enums import TipoSuporte
from app.schemas.admissao import (
    AcordoAdmissaoCreate,
    AcordoAdmissaoRead,
    AcordoAdmissaoUpdate,
    EventoAdmissaoCreate,
    EventoAdmissaoRead,
    ProcessoAdmissaoCreate,
    ProcessoAdmissaoList,
    ProcessoAdmissaoRead,
    ProcessoAdmissaoUpdate,
    RelacaoSipAipCreate,
    RelacaoSipAipRead,
    ReuniaoAdmissaoCreate,
    ReuniaoAdmissaoRead,
    ReuniaoAdmissaoUpdate,
    SessaoSubmissaoCreate,
    SessaoSubmissaoRead,
    SessaoSubmissaoUpdate,
    SipAdmissaoCreate,
    SipAdmissaoRead,
    SipAdmissaoUpdate,
)
from app.services.admissao_service import AdmissaoService

router = APIRouter()


@router.get("/processos", response_model=ProcessoAdmissaoList)
def listar_processos(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = None,
    numero_processo: str | None = None,
    titulo: str | None = None,
    id_entidade_produtora: uuid.UUID | None = None,
    tipo_processo_admissao: TipoProcessoAdmissao | None = None,
    tipo_ingresso: TipoIngressoAdmissao | None = None,
    tipo_suporte: TipoSuporte | None = None,
    status: StatusProcessoAdmissao | None = None,
    processo_ativo: bool | None = None,
    data_inicio_de: date | None = None,
    data_inicio_ate: date | None = None,
):
    items, total = AdmissaoService.listar_processos(
        db,
        limit=limit,
        offset=offset,
        q=q,
        numero_processo=numero_processo,
        titulo=titulo,
        id_entidade_produtora=id_entidade_produtora,
        tipo_processo_admissao=tipo_processo_admissao,
        tipo_ingresso=tipo_ingresso,
        tipo_suporte=tipo_suporte,
        status=status,
        processo_ativo=processo_ativo,
        data_inicio_de=data_inicio_de,
        data_inicio_ate=data_inicio_ate,
    )
    return ProcessoAdmissaoList(items=items, total=total, limit=limit, offset=offset)


@router.post("/processos", response_model=ProcessoAdmissaoRead, status_code=status.HTTP_201_CREATED)
def criar_processo(dados: ProcessoAdmissaoCreate, db: Session = Depends(db_dep)):
    try:
        return AdmissaoService.criar_processo(db, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/processos/{id}", response_model=ProcessoAdmissaoRead)
def obter_processo(id: uuid.UUID, db: Session = Depends(db_dep)):
    processo = AdmissaoService.obter_processo(db, id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo de admissão não encontrado.")
    return processo


@router.put("/processos/{id}", response_model=ProcessoAdmissaoRead)
def atualizar_processo(id: uuid.UUID, dados: ProcessoAdmissaoUpdate, db: Session = Depends(db_dep)):
    try:
        processo = AdmissaoService.atualizar_processo(db, id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo de admissão não encontrado.")
    return processo


@router.delete("/processos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_processo(id: uuid.UUID, db: Session = Depends(db_dep)):
    if not AdmissaoService.excluir_processo(db, id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo de admissão não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/processos/{processo_id}/reunioes", response_model=list[ReuniaoAdmissaoRead])
def listar_reunioes(processo_id: uuid.UUID, db: Session = Depends(db_dep)):
    return AdmissaoService.listar_reunioes(db, processo_id)


@router.post("/processos/{processo_id}/reunioes", response_model=ReuniaoAdmissaoRead, status_code=status.HTTP_201_CREATED)
def criar_reuniao(processo_id: uuid.UUID, dados: ReuniaoAdmissaoCreate, db: Session = Depends(db_dep)):
    try:
        return AdmissaoService.criar_reuniao(db, processo_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/reunioes/{id}", response_model=ReuniaoAdmissaoRead)
def obter_reuniao(id: uuid.UUID, db: Session = Depends(db_dep)):
    reuniao = AdmissaoService.obter_reuniao(db, id)
    if not reuniao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunião de admissão não encontrada.")
    return reuniao


@router.put("/reunioes/{id}", response_model=ReuniaoAdmissaoRead)
def atualizar_reuniao(id: uuid.UUID, dados: ReuniaoAdmissaoUpdate, db: Session = Depends(db_dep)):
    reuniao = AdmissaoService.atualizar_reuniao(db, id, dados)
    if not reuniao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunião de admissão não encontrada.")
    return reuniao


@router.get("/processos/{processo_id}/acordos", response_model=list[AcordoAdmissaoRead])
def listar_acordos(processo_id: uuid.UUID, db: Session = Depends(db_dep)):
    return AdmissaoService.listar_acordos(db, processo_id)


@router.post("/processos/{processo_id}/acordos", response_model=AcordoAdmissaoRead, status_code=status.HTTP_201_CREATED)
def criar_acordo(processo_id: uuid.UUID, dados: AcordoAdmissaoCreate, db: Session = Depends(db_dep)):
    try:
        return AdmissaoService.criar_acordo(db, processo_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/acordos/{id}", response_model=AcordoAdmissaoRead)
def obter_acordo(id: uuid.UUID, db: Session = Depends(db_dep)):
    acordo = AdmissaoService.obter_acordo(db, id)
    if not acordo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acordo de admissão não encontrado.")
    return acordo


@router.put("/acordos/{id}", response_model=AcordoAdmissaoRead)
def atualizar_acordo(id: uuid.UUID, dados: AcordoAdmissaoUpdate, db: Session = Depends(db_dep)):
    acordo = AdmissaoService.atualizar_acordo(db, id, dados)
    if not acordo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acordo de admissão não encontrado.")
    return acordo


@router.post("/acordos/{id}/ativar", response_model=AcordoAdmissaoRead)
def ativar_acordo(id: uuid.UUID, db: Session = Depends(db_dep)):
    acordo = AdmissaoService.ativar_acordo(db, id)
    if not acordo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acordo de admissão não encontrado.")
    return acordo


@router.post("/acordos/{id}/nova-versao", response_model=AcordoAdmissaoRead, status_code=status.HTTP_201_CREATED)
def nova_versao_acordo(id: uuid.UUID, db: Session = Depends(db_dep)):
    acordo = AdmissaoService.nova_versao_acordo(db, id)
    if not acordo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acordo de admissão não encontrado.")
    return acordo


@router.get("/processos/{processo_id}/sessoes", response_model=list[SessaoSubmissaoRead])
def listar_sessoes(processo_id: uuid.UUID, db: Session = Depends(db_dep)):
    return AdmissaoService.listar_sessoes(db, processo_id)


@router.post("/processos/{processo_id}/sessoes", response_model=SessaoSubmissaoRead, status_code=status.HTTP_201_CREATED)
def criar_sessao(processo_id: uuid.UUID, dados: SessaoSubmissaoCreate, db: Session = Depends(db_dep)):
    try:
        return AdmissaoService.criar_sessao(db, processo_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/sessoes/{id}", response_model=SessaoSubmissaoRead)
def obter_sessao(id: uuid.UUID, db: Session = Depends(db_dep)):
    sessao = AdmissaoService.obter_sessao(db, id)
    if not sessao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão de submissão não encontrada.")
    return sessao


@router.put("/sessoes/{id}", response_model=SessaoSubmissaoRead)
def atualizar_sessao(id: uuid.UUID, dados: SessaoSubmissaoUpdate, db: Session = Depends(db_dep)):
    sessao = AdmissaoService.atualizar_sessao(db, id, dados)
    if not sessao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão de submissão não encontrada.")
    return sessao


@router.post("/sessoes/{id}/finalizar", response_model=SessaoSubmissaoRead)
def finalizar_sessao(id: uuid.UUID, db: Session = Depends(db_dep)):
    try:
        sessao = AdmissaoService.finalizar_sessao(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if not sessao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão de submissão não encontrada.")
    return sessao


@router.get("/sessoes/{sessao_id}/sips", response_model=list[SipAdmissaoRead])
def listar_sips(sessao_id: uuid.UUID, db: Session = Depends(db_dep)):
    return AdmissaoService.listar_sips_por_sessao(db, sessao_id)


@router.get("/processos/{processo_id}/sips", response_model=list[SipAdmissaoRead])
def listar_sips_processo(processo_id: uuid.UUID, db: Session = Depends(db_dep)):
    return AdmissaoService.listar_sips_por_processo(db, processo_id)


@router.post("/sessoes/{sessao_id}/sips", response_model=SipAdmissaoRead, status_code=status.HTTP_201_CREATED)
def criar_sip(sessao_id: uuid.UUID, dados: SipAdmissaoCreate, db: Session = Depends(db_dep)):
    try:
        return AdmissaoService.criar_sip(db, sessao_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/sips/{id}", response_model=SipAdmissaoRead)
def obter_sip(id: uuid.UUID, db: Session = Depends(db_dep)):
    sip = AdmissaoService.obter_sip(db, id)
    if not sip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SIP não encontrado.")
    return sip


@router.put("/sips/{id}", response_model=SipAdmissaoRead)
def atualizar_sip(id: uuid.UUID, dados: SipAdmissaoUpdate, db: Session = Depends(db_dep)):
    try:
        sip = AdmissaoService.atualizar_sip(db, id, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if not sip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SIP não encontrado.")
    return sip


@router.post("/sips/{id}/validar", response_model=SipAdmissaoRead)
def validar_sip(id: uuid.UUID, db: Session = Depends(db_dep)):
    sip = AdmissaoService.alterar_status_sip(db, id, StatusSipAdmissao.VALIDADO)
    if not sip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SIP não encontrado.")
    return sip


@router.post("/sips/{id}/rejeitar", response_model=SipAdmissaoRead)
def rejeitar_sip(id: uuid.UUID, db: Session = Depends(db_dep)):
    sip = AdmissaoService.alterar_status_sip(db, id, StatusSipAdmissao.REJEITADO)
    if not sip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SIP não encontrado.")
    return sip


@router.post("/sips/{id}/transformar-em-aip", response_model=RelacaoSipAipRead, status_code=status.HTTP_201_CREATED)
def transformar_sip_em_aip(id: uuid.UUID, dados: RelacaoSipAipCreate, db: Session = Depends(db_dep)):
    try:
        return AdmissaoService.vincular_sip_aip(db, id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/processos/{processo_id}/eventos", response_model=list[EventoAdmissaoRead])
def listar_eventos(processo_id: uuid.UUID, db: Session = Depends(db_dep)):
    return AdmissaoService.listar_eventos(db, processo_id)


@router.post("/processos/{processo_id}/eventos", response_model=EventoAdmissaoRead, status_code=status.HTTP_201_CREATED)
def criar_evento(processo_id: uuid.UUID, dados: EventoAdmissaoCreate, db: Session = Depends(db_dep)):
    try:
        return AdmissaoService.criar_evento(db, processo_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
