from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.admissao import (
    AcordoAdmissao,
    EventoAdmissao,
    ProcessoAdmissao,
    RelacaoSipAip,
    ReuniaoAdmissao,
    ResultadoEventoAdmissao,
    StatusAcordoAdmissao,
    StatusProcessoAdmissao,
    StatusSessaoSubmissao,
    StatusSipAdmissao,
    SessaoSubmissao,
    SipAdmissao,
    TipoEventoAdmissao,
)
from app.models.descricao_arquivistica import RegistroDescritivo
from app.models.entidade_produtora import EntidadeProdutora
from app.models.instituicao_arquivo import InstituicaoArquivo
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.schemas.admissao import (
    AcordoAdmissaoCreate,
    AcordoAdmissaoUpdate,
    EventoAdmissaoCreate,
    ProcessoAdmissaoCreate,
    ProcessoAdmissaoUpdate,
    RelacaoSipAipCreate,
    ReuniaoAdmissaoCreate,
    ReuniaoAdmissaoUpdate,
    SessaoSubmissaoCreate,
    SessaoSubmissaoUpdate,
    SipAdmissaoCreate,
    SipAdmissaoUpdate,
)


class AdmissaoService:
    @staticmethod
    def listar_processos(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        numero_processo: str | None = None,
        titulo: str | None = None,
        id_entidade_produtora: uuid.UUID | None = None,
        tipo_processo_admissao: str | None = None,
        tipo_ingresso: str | None = None,
        tipo_suporte: str | None = None,
        status: str | None = None,
        processo_ativo: bool | None = None,
        data_inicio_de=None,
        data_inicio_ate=None,
    ) -> tuple[list[ProcessoAdmissao], int]:
        query = db.query(ProcessoAdmissao)
        if q:
            termo = f"%{q.strip()}%"
            query = query.filter(or_(ProcessoAdmissao.numero_processo.ilike(termo), ProcessoAdmissao.titulo.ilike(termo)))
        if numero_processo:
            query = query.filter(ProcessoAdmissao.numero_processo.ilike(f"%{numero_processo.strip()}%"))
        if titulo:
            query = query.filter(ProcessoAdmissao.titulo.ilike(f"%{titulo.strip()}%"))
        if id_entidade_produtora:
            query = query.filter(ProcessoAdmissao.id_entidade_produtora == id_entidade_produtora)
        if tipo_processo_admissao:
            query = query.filter(ProcessoAdmissao.tipo_processo_admissao == tipo_processo_admissao)
        if tipo_ingresso:
            query = query.filter(ProcessoAdmissao.tipo_ingresso == tipo_ingresso)
        if tipo_suporte:
            query = query.filter(ProcessoAdmissao.tipo_suporte == tipo_suporte)
        if status:
            query = query.filter(ProcessoAdmissao.status == status)
        if processo_ativo is not None:
            query = query.filter(ProcessoAdmissao.processo_ativo == processo_ativo)
        if data_inicio_de:
            query = query.filter(ProcessoAdmissao.data_inicio >= data_inicio_de)
        if data_inicio_ate:
            query = query.filter(ProcessoAdmissao.data_inicio <= data_inicio_ate)

        total = query.count()
        items = (
            query.order_by(ProcessoAdmissao.criado_em.desc(), ProcessoAdmissao.numero_processo.asc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        for item in items:
            AdmissaoService._hidratar_processo(item)
        return items, total

    @staticmethod
    def obter_processo(db: Session, id: uuid.UUID) -> ProcessoAdmissao | None:
        processo = db.get(ProcessoAdmissao, id)
        if processo:
            AdmissaoService._hidratar_processo(processo)
        return processo

    @staticmethod
    def criar_processo(db: Session, dados: ProcessoAdmissaoCreate) -> ProcessoAdmissao:
        AdmissaoService._validar_referencias_processo(db, dados.model_dump())
        if db.query(ProcessoAdmissao.id).filter(ProcessoAdmissao.numero_processo == dados.numero_processo).first():
            raise ValueError("Número de processo já cadastrado.")
        processo = ProcessoAdmissao(**dados.model_dump())
        db.add(processo)
        db.flush()
        AdmissaoService._registrar_evento(
            db,
            processo.id,
            TipoEventoAdmissao.CRIACAO_PROCESSO,
            f"Processo de admissão {processo.numero_processo} criado.",
            agente=dados.criado_por,
        )
        db.commit()
        db.refresh(processo)
        AdmissaoService._hidratar_processo(processo)
        return processo

    @staticmethod
    def atualizar_processo(db: Session, id: uuid.UUID, dados: ProcessoAdmissaoUpdate) -> ProcessoAdmissao | None:
        processo = db.get(ProcessoAdmissao, id)
        if not processo:
            return None
        payload = dados.model_dump(exclude_unset=True)
        valores = {col.name: getattr(processo, col.name) for col in ProcessoAdmissao.__table__.columns}
        valores.update(payload)
        AdmissaoService._validar_referencias_processo(db, valores)
        numero = payload.get("numero_processo")
        if numero and numero != processo.numero_processo and db.query(ProcessoAdmissao.id).filter(ProcessoAdmissao.numero_processo == numero).first():
            raise ValueError("Número de processo já cadastrado.")
        status_anterior = processo.status
        for campo, valor in payload.items():
            setattr(processo, campo, valor)
        status_atual = AdmissaoService._enum_value(processo.status)
        if status_atual in {"CONCLUIDO", "CANCELADO", "REJEITADO"}:
            processo.processo_ativo = False
        if status_anterior != processo.status and status_atual in {"CONCLUIDO", "CANCELADO"}:
            AdmissaoService._registrar_evento(
                db,
                processo.id,
                TipoEventoAdmissao.ENCERRAMENTO_PROCESSO if status_atual == "CONCLUIDO" else TipoEventoAdmissao.CANCELAMENTO_PROCESSO,
                f"Status do processo alterado para {status_atual}.",
                agente=payload.get("atualizado_por"),
            )
        db.commit()
        db.refresh(processo)
        AdmissaoService._hidratar_processo(processo)
        return processo

    @staticmethod
    def excluir_processo(db: Session, id: uuid.UUID) -> bool:
        processo = db.get(ProcessoAdmissao, id)
        if not processo:
            return False
        processo.processo_ativo = False
        processo.status = StatusProcessoAdmissao.CANCELADO
        AdmissaoService._registrar_evento(db, processo.id, TipoEventoAdmissao.CANCELAMENTO_PROCESSO, "Processo cancelado por exclusão lógica.")
        db.commit()
        return True

    @staticmethod
    def criar_reuniao(db: Session, processo_id: uuid.UUID, dados: ReuniaoAdmissaoCreate) -> ReuniaoAdmissao:
        processo = AdmissaoService._obter_processo_ou_erro(db, processo_id)
        payload = dados.model_dump(exclude={"numero_reuniao"})
        numero = dados.numero_reuniao or AdmissaoService._proximo_numero(db, ReuniaoAdmissao, processo_id, "numero_reuniao")
        reuniao = ReuniaoAdmissao(id_processo_admissao=processo.id, numero_reuniao=numero, **payload)
        db.add(reuniao)
        db.flush()
        AdmissaoService._registrar_evento(db, processo.id, TipoEventoAdmissao.REUNIAO_ADMISSAO, f"Reunião {numero} registrada.", agente=dados.criado_por)
        db.commit()
        db.refresh(reuniao)
        return reuniao

    @staticmethod
    def listar_reunioes(db: Session, processo_id: uuid.UUID) -> list[ReuniaoAdmissao]:
        return db.query(ReuniaoAdmissao).filter(ReuniaoAdmissao.id_processo_admissao == processo_id).order_by(ReuniaoAdmissao.numero_reuniao.asc()).all()

    @staticmethod
    def obter_reuniao(db: Session, id: uuid.UUID) -> ReuniaoAdmissao | None:
        return db.get(ReuniaoAdmissao, id)

    @staticmethod
    def atualizar_reuniao(db: Session, id: uuid.UUID, dados: ReuniaoAdmissaoUpdate) -> ReuniaoAdmissao | None:
        reuniao = db.get(ReuniaoAdmissao, id)
        if not reuniao:
            return None
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(reuniao, campo, valor)
        db.commit()
        db.refresh(reuniao)
        return reuniao

    @staticmethod
    def excluir_reuniao(db: Session, id: uuid.UUID) -> bool:
        reuniao = db.get(ReuniaoAdmissao, id)
        if not reuniao:
            return False
        db.delete(reuniao)
        db.commit()
        return True

    @staticmethod
    def criar_acordo(db: Session, processo_id: uuid.UUID, dados: AcordoAdmissaoCreate) -> AcordoAdmissao:
        processo = AdmissaoService._obter_processo_ou_erro(db, processo_id)
        if AdmissaoService._enum_value(dados.status) == "ATIVO":
            AdmissaoService._desativar_acordos_ativos(db, processo.id)
        payload = dados.model_dump(exclude={"numero_versao"})
        numero = dados.numero_versao or AdmissaoService._proximo_numero(db, AcordoAdmissao, processo_id, "numero_versao")
        acordo = AcordoAdmissao(id_processo_admissao=processo.id, numero_versao=numero, **payload)
        db.add(acordo)
        db.flush()
        AdmissaoService._registrar_evento(db, processo.id, TipoEventoAdmissao.CRIACAO_VERSAO_ACORDO, f"Versão {numero} do acordo criada.", agente=dados.criado_por)
        if AdmissaoService._enum_value(acordo.status) == "ATIVO":
            AdmissaoService._registrar_evento(db, processo.id, TipoEventoAdmissao.ATIVACAO_ACORDO, f"Versão {numero} do acordo ativada.", agente=dados.criado_por)
        db.commit()
        db.refresh(acordo)
        return acordo

    @staticmethod
    def listar_acordos(db: Session, processo_id: uuid.UUID) -> list[AcordoAdmissao]:
        return db.query(AcordoAdmissao).filter(AcordoAdmissao.id_processo_admissao == processo_id).order_by(AcordoAdmissao.numero_versao.desc()).all()

    @staticmethod
    def obter_acordo(db: Session, id: uuid.UUID) -> AcordoAdmissao | None:
        return db.get(AcordoAdmissao, id)

    @staticmethod
    def atualizar_acordo(db: Session, id: uuid.UUID, dados: AcordoAdmissaoUpdate) -> AcordoAdmissao | None:
        acordo = db.get(AcordoAdmissao, id)
        if not acordo:
            return None
        payload = dados.model_dump(exclude_unset=True)
        if AdmissaoService._enum_value(payload.get("status")) == "ATIVO":
            AdmissaoService._desativar_acordos_ativos(db, acordo.id_processo_admissao, exceto_id=acordo.id)
        for campo, valor in payload.items():
            setattr(acordo, campo, valor)
        if AdmissaoService._enum_value(payload.get("status")) == "ATIVO":
            AdmissaoService._registrar_evento(db, acordo.id_processo_admissao, TipoEventoAdmissao.ATIVACAO_ACORDO, f"Versão {acordo.numero_versao} do acordo ativada.", agente=payload.get("atualizado_por"))
        db.commit()
        db.refresh(acordo)
        return acordo

    @staticmethod
    def ativar_acordo(db: Session, id: uuid.UUID) -> AcordoAdmissao | None:
        acordo = db.get(AcordoAdmissao, id)
        if not acordo:
            return None
        AdmissaoService._desativar_acordos_ativos(db, acordo.id_processo_admissao, exceto_id=acordo.id)
        acordo.status = StatusAcordoAdmissao.ATIVO
        acordo.data_inicio_vigencia = acordo.data_inicio_vigencia or datetime.now(timezone.utc).date()
        AdmissaoService._registrar_evento(db, acordo.id_processo_admissao, TipoEventoAdmissao.ATIVACAO_ACORDO, f"Versão {acordo.numero_versao} do acordo ativada.")
        db.commit()
        db.refresh(acordo)
        return acordo

    @staticmethod
    def nova_versao_acordo(db: Session, id: uuid.UUID) -> AcordoAdmissao | None:
        origem = db.get(AcordoAdmissao, id)
        if not origem:
            return None
        campos = [
            "titulo", "descricao", "regras_empacotamento", "regras_nomenclatura", "formatos_aceitos",
            "metadados_obrigatorios", "requisitos_fixidez", "requisitos_representacao", "politica_validacao",
            "politica_rejeicao", "politica_normalizacao", "politica_sigilo", "periodicidade_submissao", "observacoes",
        ]
        acordo = AcordoAdmissao(
            id_processo_admissao=origem.id_processo_admissao,
            numero_versao=AdmissaoService._proximo_numero(db, AcordoAdmissao, origem.id_processo_admissao, "numero_versao"),
            status=StatusAcordoAdmissao.RASCUNHO,
            motivo_revisao=f"Nova versão baseada na versão {origem.numero_versao}.",
            **{campo: getattr(origem, campo) for campo in campos},
        )
        db.add(acordo)
        db.flush()
        AdmissaoService._registrar_evento(db, origem.id_processo_admissao, TipoEventoAdmissao.CRIACAO_VERSAO_ACORDO, f"Versão {acordo.numero_versao} do acordo criada a partir da versão {origem.numero_versao}.")
        db.commit()
        db.refresh(acordo)
        return acordo

    @staticmethod
    def criar_sessao(db: Session, processo_id: uuid.UUID, dados: SessaoSubmissaoCreate) -> SessaoSubmissao:
        processo = AdmissaoService._obter_processo_ou_erro(db, processo_id)
        if not processo.processo_ativo:
            raise ValueError("Sessões só podem ser criadas para processos ativos.")
        acordo = db.get(AcordoAdmissao, dados.id_acordo_utilizado)
        if not acordo or acordo.id_processo_admissao != processo.id:
            raise LookupError("Acordo de admissão não encontrado para o processo.")
        payload = dados.model_dump(exclude={"numero_sessao"})
        numero = dados.numero_sessao or AdmissaoService._proximo_numero(db, SessaoSubmissao, processo_id, "numero_sessao")
        sessao = SessaoSubmissao(id_processo_admissao=processo.id, numero_sessao=numero, **payload)
        db.add(sessao)
        db.flush()
        AdmissaoService._registrar_evento(db, processo.id, TipoEventoAdmissao.INICIO_SESSAO, f"Sessão de submissão {numero} iniciada.", id_sessao_submissao=sessao.id, agente=dados.criado_por)
        db.commit()
        db.refresh(sessao)
        return sessao

    @staticmethod
    def listar_sessoes(db: Session, processo_id: uuid.UUID) -> list[SessaoSubmissao]:
        return db.query(SessaoSubmissao).filter(SessaoSubmissao.id_processo_admissao == processo_id).order_by(SessaoSubmissao.numero_sessao.desc()).all()

    @staticmethod
    def obter_sessao(db: Session, id: uuid.UUID) -> SessaoSubmissao | None:
        return db.get(SessaoSubmissao, id)

    @staticmethod
    def atualizar_sessao(db: Session, id: uuid.UUID, dados: SessaoSubmissaoUpdate) -> SessaoSubmissao | None:
        sessao = db.get(SessaoSubmissao, id)
        if not sessao:
            return None
        payload = dados.model_dump(exclude_unset=True)
        for campo, valor in payload.items():
            setattr(sessao, campo, valor)
        db.commit()
        db.refresh(sessao)
        return sessao

    @staticmethod
    def finalizar_sessao(db: Session, id: uuid.UUID) -> SessaoSubmissao | None:
        sessao = db.get(SessaoSubmissao, id)
        if not sessao:
            return None
        pendentes = db.query(SipAdmissao.id).filter(SipAdmissao.id_sessao_submissao == id, SipAdmissao.status.in_([StatusSipAdmissao.RECEBIDO, StatusSipAdmissao.EM_QUARENTENA, StatusSipAdmissao.EM_VALIDACAO])).first()
        if pendentes:
            raise ValueError("Não é possível finalizar sessão com SIPs pendentes de validação.")
        sessao.status = StatusSessaoSubmissao.FINALIZADA
        sessao.data_fim = sessao.data_fim or datetime.now(timezone.utc)
        db.commit()
        db.refresh(sessao)
        return sessao

    @staticmethod
    def criar_sip(db: Session, sessao_id: uuid.UUID, dados: SipAdmissaoCreate) -> SipAdmissao:
        sessao = db.get(SessaoSubmissao, sessao_id)
        if not sessao:
            raise LookupError("Sessão de submissão não encontrada.")
        if db.query(SipAdmissao.id).filter(SipAdmissao.codigo_sip == dados.codigo_sip).first():
            raise ValueError("Código SIP já cadastrado.")
        sip = SipAdmissao(id_processo_admissao=sessao.id_processo_admissao, id_sessao_submissao=sessao.id, **dados.model_dump())
        db.add(sip)
        db.flush()
        AdmissaoService._registrar_evento(db, sessao.id_processo_admissao, TipoEventoAdmissao.RECEBIMENTO_SIP, f"SIP {sip.codigo_sip} recebido.", id_sessao_submissao=sessao.id, id_sip=sip.id, agente=dados.criado_por)
        db.commit()
        db.refresh(sip)
        return sip

    @staticmethod
    def listar_sips_por_sessao(db: Session, sessao_id: uuid.UUID) -> list[SipAdmissao]:
        return db.query(SipAdmissao).filter(SipAdmissao.id_sessao_submissao == sessao_id).order_by(SipAdmissao.criado_em.desc()).all()

    @staticmethod
    def listar_sips_por_processo(db: Session, processo_id: uuid.UUID) -> list[SipAdmissao]:
        return db.query(SipAdmissao).filter(SipAdmissao.id_processo_admissao == processo_id).order_by(SipAdmissao.criado_em.desc()).all()

    @staticmethod
    def obter_sip(db: Session, id: uuid.UUID) -> SipAdmissao | None:
        return db.get(SipAdmissao, id)

    @staticmethod
    def atualizar_sip(db: Session, id: uuid.UUID, dados: SipAdmissaoUpdate) -> SipAdmissao | None:
        sip = db.get(SipAdmissao, id)
        if not sip:
            return None
        payload = dados.model_dump(exclude_unset=True)
        status_anterior = sip.status
        codigo = payload.get("codigo_sip")
        if codigo and codigo != sip.codigo_sip and db.query(SipAdmissao.id).filter(SipAdmissao.codigo_sip == codigo).first():
            raise ValueError("Código SIP já cadastrado.")
        for campo, valor in payload.items():
            setattr(sip, campo, valor)
        if "status" in payload and sip.status != status_anterior:
            status_atual = AdmissaoService._enum_value(sip.status)
            AdmissaoService._registrar_evento(
                db,
                sip.id_processo_admissao,
                TipoEventoAdmissao.APROVACAO if status_atual in {"VALIDADO", "VALIDADO_COM_RESSALVA"} else TipoEventoAdmissao.REJEICAO if status_atual == "REJEITADO" else TipoEventoAdmissao.RECEBIMENTO_SIP,
                f"Status do SIP {sip.codigo_sip} alterado para {status_atual}.",
                id_sessao_submissao=sip.id_sessao_submissao,
                id_sip=sip.id,
                agente=payload.get("atualizado_por"),
            )
        db.commit()
        db.refresh(sip)
        return sip

    @staticmethod
    def alterar_status_sip(db: Session, id: uuid.UUID, status: StatusSipAdmissao) -> SipAdmissao | None:
        return AdmissaoService.atualizar_sip(db, id, SipAdmissaoUpdate(status=status))

    @staticmethod
    def vincular_sip_aip(db: Session, id: uuid.UUID, dados: RelacaoSipAipCreate) -> RelacaoSipAip:
        sip = db.get(SipAdmissao, id)
        if not sip:
            raise LookupError("SIP não encontrado.")
        unidade = db.get(UnidadeAcondicionamento, dados.id_unidade_acondicionamento)
        if not unidade:
            raise LookupError("Unidade de acondicionamento não encontrada.")
        if AdmissaoService._enum_value(sip.status) == "REJEITADO":
            raise ValueError("SIP rejeitado não pode ser transformado em AIP.")
        relacao = RelacaoSipAip(id_sip=sip.id, **dados.model_dump())
        sip.status = StatusSipAdmissao.TRANSFORMADO_EM_AIP
        db.add(relacao)
        db.flush()
        AdmissaoService._registrar_evento(db, sip.id_processo_admissao, TipoEventoAdmissao.GERACAO_AIP, f"SIP {sip.codigo_sip} vinculado à unidade {unidade.identificador} como AIP.", id_sessao_submissao=sip.id_sessao_submissao, id_sip=sip.id, id_unidade_acondicionamento=unidade.id, agente=dados.criado_por)
        db.commit()
        db.refresh(relacao)
        return relacao

    @staticmethod
    def listar_eventos(db: Session, processo_id: uuid.UUID) -> list[EventoAdmissao]:
        return db.query(EventoAdmissao).filter(EventoAdmissao.id_processo_admissao == processo_id).order_by(EventoAdmissao.data_evento.desc(), EventoAdmissao.criado_em.desc()).all()

    @staticmethod
    def criar_evento(db: Session, processo_id: uuid.UUID, dados: EventoAdmissaoCreate) -> EventoAdmissao:
        AdmissaoService._obter_processo_ou_erro(db, processo_id)
        evento = EventoAdmissao(id_processo_admissao=processo_id, data_evento=dados.data_evento or datetime.now(timezone.utc), **dados.model_dump(exclude={"data_evento"}))
        db.add(evento)
        db.commit()
        db.refresh(evento)
        return evento

    @staticmethod
    def _registrar_evento(db: Session, processo_id: uuid.UUID, tipo_evento: TipoEventoAdmissao, descricao: str, resultado: ResultadoEventoAdmissao = ResultadoEventoAdmissao.SUCESSO, agente: str | None = None, id_sessao_submissao: uuid.UUID | None = None, id_sip: uuid.UUID | None = None, id_unidade_acondicionamento: int | None = None) -> EventoAdmissao:
        evento = EventoAdmissao(id_processo_admissao=processo_id, id_sessao_submissao=id_sessao_submissao, id_sip=id_sip, id_unidade_acondicionamento=id_unidade_acondicionamento, tipo_evento=tipo_evento, descricao=descricao, resultado=resultado, agente=agente, criado_por=agente)
        db.add(evento)
        return evento

    @staticmethod
    def _obter_processo_ou_erro(db: Session, processo_id: uuid.UUID) -> ProcessoAdmissao:
        processo = db.get(ProcessoAdmissao, processo_id)
        if not processo:
            raise LookupError("Processo de admissão não encontrado.")
        return processo

    @staticmethod
    def _proximo_numero(db: Session, model, processo_id: uuid.UUID, campo: str) -> int:
        maior = db.query(model).filter(model.id_processo_admissao == processo_id).order_by(getattr(model, campo).desc()).first()
        return (getattr(maior, campo) if maior else 0) + 1

    @staticmethod
    def _desativar_acordos_ativos(db: Session, processo_id: uuid.UUID, exceto_id: uuid.UUID | None = None) -> None:
        query = db.query(AcordoAdmissao).filter(AcordoAdmissao.id_processo_admissao == processo_id, AcordoAdmissao.status == StatusAcordoAdmissao.ATIVO)
        if exceto_id:
            query = query.filter(AcordoAdmissao.id != exceto_id)
        for acordo in query.all():
            acordo.status = StatusAcordoAdmissao.ENCERRADO

    @staticmethod
    def _validar_referencias_processo(db: Session, valores: dict) -> None:
        if not db.get(InstituicaoArquivo, valores.get("id_instituicao_arquivo")):
            raise LookupError("Instituição de arquivo não encontrada.")
        if not db.get(EntidadeProdutora, valores.get("id_entidade_produtora")):
            raise LookupError("Entidade produtora não encontrada.")
        descricao_id = valores.get("id_descricao_arquivistica")
        if descricao_id and not db.get(RegistroDescritivo, descricao_id):
            raise LookupError("Descrição arquivística não encontrada.")
        data_inicio = valores.get("data_inicio")
        data_fim_prevista = valores.get("data_fim_prevista")
        data_encerramento = valores.get("data_encerramento")
        if data_inicio and data_fim_prevista and data_fim_prevista < data_inicio:
            raise ValueError("data_fim_prevista não pode ser anterior a data_inicio.")
        if data_inicio and data_encerramento and data_encerramento < data_inicio:
            raise ValueError("data_encerramento não pode ser anterior a data_inicio.")

    @staticmethod
    def _hidratar_processo(processo: ProcessoAdmissao) -> None:
        processo.nome_instituicao_arquivo = processo.instituicao_arquivo.nome if processo.instituicao_arquivo else None
        processo.nome_entidade_produtora = processo.entidade_produtora.nome if processo.entidade_produtora else None
        processo.titulo_descricao_arquivistica = processo.descricao_arquivistica.titulo if processo.descricao_arquivistica else None

    @staticmethod
    def _enum_value(value) -> str | None:
        return value.value if hasattr(value, "value") else value
