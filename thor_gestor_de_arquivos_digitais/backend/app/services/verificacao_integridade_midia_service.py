from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.copia_unidade_acondicionamento_digital import CopiaUnidadeAcondicionamentoDigital
from app.models.enums import (
    ResultadoEventoPreservacao,
    ResultadoVerificacaoIntegridade,
    StatusMidiaArmazenamento,
    TipoEventoMidiaArmazenamento,
    TipoEventoPreservacao,
)
from app.models.evento_preservacao import EventoPreservacao
from app.models.midia_armazenamento import MidiaArmazenamento, TipoMidiaArmazenamento
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.models.verificacao_integridade_midia import VerificacaoIntegridadeMidia
from app.schemas.evento_midia_armazenamento import EventoMidiaArmazenamentoCreate
from app.schemas.verificacao_integridade_midia import (
    IntegridadePainelOut,
    IntegridadeResumoOut,
    VerificacaoIntegridadeImportarRelatorio,
    VerificacaoIntegridadeManualCreate,
)
from app.services.evento_midia_armazenamento_service import EventoMidiaArmazenamentoService
from app.services.midia_armazenamento_service import _somar_meses


class VerificacaoIntegridadeMidiaService:
    CATEGORIAS_INTEGRIDADE = {
        "validade_vencida",
        "checagem_vencida",
        "proximas_vencimento",
        "falha_ultima_checagem",
        "sem_checagem",
        "com_alerta",
    }

    @staticmethod
    def listar_midias_com_checagem_vencida(db: Session, limite: int = 100) -> list[MidiaArmazenamento]:
        agora = datetime.now(timezone.utc)
        return (
            db.query(MidiaArmazenamento)
            .options(joinedload(MidiaArmazenamento.tipo_midia))
            .filter(
                MidiaArmazenamento.ativo.is_(True),
                MidiaArmazenamento.proxima_checagem_integridade.is_not(None),
                MidiaArmazenamento.proxima_checagem_integridade <= agora,
            )
            .order_by(MidiaArmazenamento.proxima_checagem_integridade.asc())
            .limit(max(1, min(limite, 500)))
            .all()
        )

    @staticmethod
    def listar_midias_com_validade_vencida(db: Session, limite: int = 100) -> list[MidiaArmazenamento]:
        hoje = date.today()
        return (
            db.query(MidiaArmazenamento)
            .options(joinedload(MidiaArmazenamento.tipo_midia))
            .filter(
                MidiaArmazenamento.ativo.is_(True),
                MidiaArmazenamento.data_validade.is_not(None),
                MidiaArmazenamento.data_validade <= hoje,
            )
            .order_by(MidiaArmazenamento.data_validade.asc())
            .limit(max(1, min(limite, 500)))
            .all()
        )

    @staticmethod
    def painel_integridade(db: Session) -> IntegridadePainelOut:
        hoje = date.today()
        agora = datetime.now(timezone.utc)
        limite_proximo = hoje + timedelta(days=90)
        base = db.query(MidiaArmazenamento).options(joinedload(MidiaArmazenamento.tipo_midia))
        return IntegridadePainelOut(
            validade_vencida=VerificacaoIntegridadeMidiaService.listar_midias_com_validade_vencida(db),
            checagem_vencida=VerificacaoIntegridadeMidiaService.listar_midias_com_checagem_vencida(db),
            proximas_vencimento=(
                base.filter(
                    MidiaArmazenamento.ativo.is_(True),
                    MidiaArmazenamento.data_validade.is_not(None),
                    MidiaArmazenamento.data_validade > hoje,
                    MidiaArmazenamento.data_validade <= limite_proximo,
                )
                .order_by(MidiaArmazenamento.data_validade.asc())
                .limit(100)
                .all()
            ),
            falha_ultima_checagem=(
                base.filter(MidiaArmazenamento.status == StatusMidiaArmazenamento.FALHA_INTEGRIDADE)
                .order_by(MidiaArmazenamento.atualizado_em.desc())
                .limit(100)
                .all()
            ),
            sem_checagem=(
                base.filter(
                    MidiaArmazenamento.ativo.is_(True),
                    or_(
                        MidiaArmazenamento.ultima_checagem_integridade.is_(None),
                        MidiaArmazenamento.proxima_checagem_integridade.is_(None),
                    ),
                )
                .order_by(MidiaArmazenamento.id.desc())
                .limit(100)
                .all()
            ),
            com_alerta=(
                base.filter(
                    or_(
                        MidiaArmazenamento.status == StatusMidiaArmazenamento.COM_ALERTA,
                        MidiaArmazenamento.status == StatusMidiaArmazenamento.EXPIRADA,
                    )
                )
                .order_by(MidiaArmazenamento.atualizado_em.desc())
                .limit(100)
                .all()
            ),
        )

    @staticmethod
    def resumo_integridade(db: Session) -> IntegridadeResumoOut:
        return IntegridadeResumoOut(
            validade_vencida=VerificacaoIntegridadeMidiaService._contar_categoria(db, "validade_vencida"),
            checagem_vencida=VerificacaoIntegridadeMidiaService._contar_categoria(db, "checagem_vencida"),
            proximas_vencimento=VerificacaoIntegridadeMidiaService._contar_categoria(db, "proximas_vencimento"),
            falha_ultima_checagem=VerificacaoIntegridadeMidiaService._contar_categoria(db, "falha_ultima_checagem"),
            sem_checagem=VerificacaoIntegridadeMidiaService._contar_categoria(db, "sem_checagem"),
            com_alerta=VerificacaoIntegridadeMidiaService._contar_categoria(db, "com_alerta"),
        )

    @staticmethod
    def listar_itens_integridade(
        db: Session,
        categoria: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MidiaArmazenamento], int]:
        query = VerificacaoIntegridadeMidiaService._query_categoria(db, categoria)
        total = query.count()
        items = (
            query.options(joinedload(MidiaArmazenamento.tipo_midia))
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def listar_por_midia(
        db: Session,
        midia_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[VerificacaoIntegridadeMidia], int]:
        VerificacaoIntegridadeMidiaService._obter_midia(db, midia_id)
        query = db.query(VerificacaoIntegridadeMidia).filter(VerificacaoIntegridadeMidia.midia_id == midia_id)
        total = query.count()
        items = (
            query.order_by(VerificacaoIntegridadeMidia.data_inicio.desc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def _contar_categoria(db: Session, categoria: str) -> int:
        query = VerificacaoIntegridadeMidiaService._query_categoria(db, categoria)
        return query.order_by(None).with_entities(func.count(MidiaArmazenamento.id)).scalar() or 0

    @staticmethod
    def _query_categoria(db: Session, categoria: str):
        if categoria not in VerificacaoIntegridadeMidiaService.CATEGORIAS_INTEGRIDADE:
            raise ValueError("Categoria de integridade invalida.")

        hoje = date.today()
        agora = datetime.now(timezone.utc)
        limite_proximo = hoje + timedelta(days=90)
        query = db.query(MidiaArmazenamento)

        if categoria == "validade_vencida":
            return (
                query.filter(
                    MidiaArmazenamento.ativo.is_(True),
                    MidiaArmazenamento.data_validade.is_not(None),
                    MidiaArmazenamento.data_validade <= hoje,
                )
                .order_by(MidiaArmazenamento.data_validade.asc(), MidiaArmazenamento.id.asc())
            )
        if categoria == "checagem_vencida":
            return (
                query.filter(
                    MidiaArmazenamento.ativo.is_(True),
                    MidiaArmazenamento.proxima_checagem_integridade.is_not(None),
                    MidiaArmazenamento.proxima_checagem_integridade <= agora,
                )
                .order_by(MidiaArmazenamento.proxima_checagem_integridade.asc(), MidiaArmazenamento.id.asc())
            )
        if categoria == "proximas_vencimento":
            return (
                query.filter(
                    MidiaArmazenamento.ativo.is_(True),
                    MidiaArmazenamento.data_validade.is_not(None),
                    MidiaArmazenamento.data_validade > hoje,
                    MidiaArmazenamento.data_validade <= limite_proximo,
                )
                .order_by(MidiaArmazenamento.data_validade.asc(), MidiaArmazenamento.id.asc())
            )
        if categoria == "falha_ultima_checagem":
            return (
                query.filter(MidiaArmazenamento.status == StatusMidiaArmazenamento.FALHA_INTEGRIDADE)
                .order_by(MidiaArmazenamento.atualizado_em.desc(), MidiaArmazenamento.id.desc())
            )
        if categoria == "sem_checagem":
            return (
                query.filter(
                    MidiaArmazenamento.ativo.is_(True),
                    or_(
                        MidiaArmazenamento.ultima_checagem_integridade.is_(None),
                        MidiaArmazenamento.proxima_checagem_integridade.is_(None),
                    ),
                )
                .order_by(MidiaArmazenamento.id.desc())
            )
        return (
            query.filter(
                or_(
                    MidiaArmazenamento.status == StatusMidiaArmazenamento.COM_ALERTA,
                    MidiaArmazenamento.status == StatusMidiaArmazenamento.EXPIRADA,
                )
            )
            .order_by(MidiaArmazenamento.atualizado_em.desc(), MidiaArmazenamento.id.desc())
        )

    @staticmethod
    def obter(db: Session, midia_id: int, verificacao_id: uuid.UUID) -> VerificacaoIntegridadeMidia | None:
        return (
            db.query(VerificacaoIntegridadeMidia)
            .filter(
                VerificacaoIntegridadeMidia.id == verificacao_id,
                VerificacaoIntegridadeMidia.midia_id == midia_id,
            )
            .one_or_none()
        )

    @staticmethod
    def listar_eventos_unidades(db: Session, verificacao_id: uuid.UUID) -> list[EventoPreservacao]:
        return (
            db.query(EventoPreservacao)
            .filter(EventoPreservacao.correlacao == f"verificacao_integridade:{verificacao_id}")
            .order_by(EventoPreservacao.id.desc())
            .all()
        )

    @staticmethod
    def registrar_checagem_manual(
        db: Session,
        midia_id: int,
        dados: VerificacaoIntegridadeManualCreate,
        usuario_id: str | None,
    ) -> VerificacaoIntegridadeMidia:
        relatorio = {
            **dados.relatorio_json,
            "origem_registro": "manual",
            "resultado_midia": dados.resultado.value,
        }
        return VerificacaoIntegridadeMidiaService._registrar_verificacao(
            db,
            midia_id=midia_id,
            data_inicio=dados.data_inicio or datetime.now(timezone.utc),
            data_fim=dados.data_fim or datetime.now(timezone.utc),
            usuario_id=usuario_id,
            resultado=dados.resultado,
            software_utilizado=dados.software_utilizado,
            versao_software=dados.versao_software,
            arquivo_relatorio_id=dados.arquivo_relatorio_id,
            total_aips_verificados=dados.total_aips_verificados,
            total_sucesso=dados.total_sucesso,
            total_falha=dados.total_falha,
            total_alerta=dados.total_alerta,
            relatorio_json=relatorio,
            observacoes=dados.observacoes,
        )

    @staticmethod
    def importar_relatorio_verificacao(
        db: Session,
        midia_id: int,
        dados: VerificacaoIntegridadeImportarRelatorio,
        usuario_id: str | None,
    ) -> VerificacaoIntegridadeMidia:
        relatorio = dados.relatorio_json
        VerificacaoIntegridadeMidiaService._validar_relatorio(relatorio)
        return VerificacaoIntegridadeMidiaService.processar_relatorio_thor_caixa_ferramentas(
            db,
            midia_id=midia_id,
            relatorio=relatorio,
            usuario_id=usuario_id,
            ferramenta=dados.ferramenta,
            versao=dados.versao,
            arquivo_relatorio_id=dados.arquivo_relatorio_id,
            observacoes=dados.observacoes,
        )

    @staticmethod
    def processar_relatorio_thor_caixa_ferramentas(
        db: Session,
        *,
        midia_id: int,
        relatorio: dict[str, Any],
        usuario_id: str | None,
        ferramenta: str | None = None,
        versao: str | None = None,
        arquivo_relatorio_id: uuid.UUID | None = None,
        observacoes: str | None = None,
    ) -> VerificacaoIntegridadeMidia:
        midia_relatorio = relatorio.get("midia_id") or relatorio.get("id_midia_armazenamento")
        if midia_relatorio is not None and str(midia_relatorio) != str(midia_id):
            raise ValueError("Relatorio pertence a outra midia de armazenamento.")

        totais = VerificacaoIntegridadeMidiaService._extrair_totais(relatorio)
        resultado = VerificacaoIntegridadeMidiaService._normalizar_resultado(
            relatorio.get("resultado_midia") or relatorio.get("resultado")
        )
        relatorio_normalizado = {
            **relatorio,
            "midia_id": midia_id,
            "software": ferramenta or relatorio.get("software") or relatorio.get("ferramenta") or "Thor Caixa de Ferramentas",
            "versao": versao or relatorio.get("versao") or relatorio.get("versao_software"),
        }
        return VerificacaoIntegridadeMidiaService._registrar_verificacao(
            db,
            midia_id=midia_id,
            data_inicio=VerificacaoIntegridadeMidiaService._parse_datetime(relatorio.get("data_inicio")) or datetime.now(timezone.utc),
            data_fim=VerificacaoIntegridadeMidiaService._parse_datetime(relatorio.get("data_fim")) or datetime.now(timezone.utc),
            usuario_id=usuario_id,
            resultado=resultado,
            software_utilizado=relatorio_normalizado["software"],
            versao_software=relatorio_normalizado["versao"],
            arquivo_relatorio_id=arquivo_relatorio_id,
            total_aips_verificados=totais["total_aips_verificados"],
            total_sucesso=totais["total_sucesso"],
            total_falha=totais["total_falha"],
            total_alerta=totais["total_alerta"],
            relatorio_json=relatorio_normalizado,
            observacoes=observacoes or relatorio.get("observacoes"),
        )

    @staticmethod
    def _registrar_verificacao(
        db: Session,
        *,
        midia_id: int,
        data_inicio: datetime,
        data_fim: datetime | None,
        usuario_id: str | None,
        resultado: ResultadoVerificacaoIntegridade,
        software_utilizado: str | None,
        versao_software: str | None,
        arquivo_relatorio_id: uuid.UUID | None,
        total_aips_verificados: int,
        total_sucesso: int,
        total_falha: int,
        total_alerta: int,
        relatorio_json: dict[str, Any],
        observacoes: str | None,
    ) -> VerificacaoIntegridadeMidia:
        midia = VerificacaoIntegridadeMidiaService._obter_midia(db, midia_id)
        verificacao = VerificacaoIntegridadeMidia(
            midia_id=midia_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            usuario_id=usuario_id,
            resultado=resultado,
            software_utilizado=software_utilizado,
            versao_software=versao_software,
            arquivo_relatorio_id=arquivo_relatorio_id,
            total_aips_verificados=total_aips_verificados,
            total_sucesso=total_sucesso,
            total_falha=total_falha,
            total_alerta=total_alerta,
            relatorio_json=relatorio_json,
            observacoes=observacoes,
        )
        db.add(verificacao)
        db.flush()

        evento = EventoMidiaArmazenamentoService.registrar(
            db,
            midia_id,
            EventoMidiaArmazenamentoCreate(
                tipo_evento=TipoEventoMidiaArmazenamento.CHECAGEM_MIDIA,
                resultado=VerificacaoIntegridadeMidiaService._resultado_evento(resultado),
                data_evento=data_fim or data_inicio,
                detalhe=VerificacaoIntegridadeMidiaService._detalhe_verificacao(resultado, verificacao),
                agente=usuario_id,
                premis_json=VerificacaoIntegridadeMidiaService._premis_verificacao(midia_id, verificacao, usuario_id),
            ),
            commit=False,
        )
        db.flush()
        verificacao.evento_id = evento.id

        VerificacaoIntegridadeMidiaService._atualizar_midia_apos_verificacao(db, midia, verificacao)
        VerificacaoIntegridadeMidiaService._registrar_eventos_unidades(db, midia_id, verificacao)

        db.commit()
        db.refresh(verificacao)
        return verificacao

    @staticmethod
    def _obter_midia(db: Session, midia_id: int) -> MidiaArmazenamento:
        midia = db.get(MidiaArmazenamento, midia_id)
        if not midia:
            raise LookupError("Midia de armazenamento nao encontrada.")
        return midia

    @staticmethod
    def _validar_relatorio(relatorio: dict[str, Any]) -> None:
        if not isinstance(relatorio, dict) or not relatorio:
            raise ValueError("Relatorio de verificacao deve ser um objeto JSON.")
        if not any(campo in relatorio for campo in ("resultado_midia", "resultado", "aips", "falhas", "alertas")):
            raise ValueError("Relatorio nao possui campos reconhecidos para verificacao de integridade.")

    @staticmethod
    def _extrair_totais(relatorio: dict[str, Any]) -> dict[str, int]:
        falhas = VerificacaoIntegridadeMidiaService._lista(relatorio.get("falhas"))
        alertas = VerificacaoIntegridadeMidiaService._lista(relatorio.get("alertas"))
        aips = VerificacaoIntegridadeMidiaService._lista(relatorio.get("aips") or relatorio.get("aips_verificados"))
        total = int(relatorio.get("total_aips_verificados") or len(aips) or (len(falhas) + len(alertas)))
        total_falha = int(relatorio.get("total_falha") or len(falhas))
        total_alerta = int(relatorio.get("total_alerta") or len(alertas))
        total_sucesso = int(relatorio.get("total_sucesso") or max(total - total_falha - total_alerta, 0))
        return {
            "total_aips_verificados": total,
            "total_sucesso": total_sucesso,
            "total_falha": total_falha,
            "total_alerta": total_alerta,
        }

    @staticmethod
    def _normalizar_resultado(valor: Any) -> ResultadoVerificacaoIntegridade:
        texto = str(valor or "").upper()
        if texto in ResultadoVerificacaoIntegridade.__members__:
            return ResultadoVerificacaoIntegridade[texto]
        if texto == "INDETERMINADO":
            return ResultadoVerificacaoIntegridade.INCONCLUSIVO
        return ResultadoVerificacaoIntegridade.SUCESSO

    @staticmethod
    def _resultado_evento(resultado: ResultadoVerificacaoIntegridade) -> ResultadoEventoPreservacao:
        mapa = {
            ResultadoVerificacaoIntegridade.SUCESSO: ResultadoEventoPreservacao.SUCESSO,
            ResultadoVerificacaoIntegridade.FALHA: ResultadoEventoPreservacao.FALHA,
            ResultadoVerificacaoIntegridade.ALERTA: ResultadoEventoPreservacao.ALERTA,
            ResultadoVerificacaoIntegridade.INCONCLUSIVO: ResultadoEventoPreservacao.INDETERMINADO,
        }
        return mapa[resultado]

    @staticmethod
    def _atualizar_midia_apos_verificacao(
        db: Session,
        midia: MidiaArmazenamento,
        verificacao: VerificacaoIntegridadeMidia,
    ) -> None:
        data_base = verificacao.data_fim or verificacao.data_inicio
        midia.ultima_checagem_integridade = data_base
        tipo = db.get(TipoMidiaArmazenamento, midia.tipo_midia_id)
        if tipo:
            midia.proxima_checagem_integridade = _somar_meses(data_base, tipo.periodicidade_checagem_meses)
        if verificacao.resultado == ResultadoVerificacaoIntegridade.FALHA:
            midia.status = StatusMidiaArmazenamento.FALHA_INTEGRIDADE
        elif verificacao.resultado == ResultadoVerificacaoIntegridade.ALERTA:
            midia.status = StatusMidiaArmazenamento.COM_ALERTA
        elif midia.data_validade and midia.data_validade <= date.today():
            midia.status = StatusMidiaArmazenamento.EXPIRADA
        else:
            midia.status = StatusMidiaArmazenamento.ATIVA

    @staticmethod
    def _registrar_eventos_unidades(
        db: Session,
        midia_id: int,
        verificacao: VerificacaoIntegridadeMidia,
    ) -> None:
        relatorio = verificacao.relatorio_json or {}
        entradas = [
            (entrada, ResultadoVerificacaoIntegridade.SUCESSO)
            for entrada in (
                VerificacaoIntegridadeMidiaService._lista(relatorio.get("aips"))
                + VerificacaoIntegridadeMidiaService._lista(relatorio.get("aips_verificados"))
            )
        ]
        entradas += [
            (entrada, ResultadoVerificacaoIntegridade.FALHA)
            for entrada in VerificacaoIntegridadeMidiaService._lista(relatorio.get("falhas"))
        ]
        entradas += [
            (entrada, ResultadoVerificacaoIntegridade.ALERTA)
            for entrada in VerificacaoIntegridadeMidiaService._lista(relatorio.get("alertas"))
        ]
        vistos: set[tuple[int, str]] = set()
        for entrada, resultado_padrao in entradas:
            if not isinstance(entrada, dict):
                continue
            unidade = VerificacaoIntegridadeMidiaService._identificar_unidade(db, midia_id, entrada)
            if not unidade:
                continue
            resultado = VerificacaoIntegridadeMidiaService._resultado_evento(
                VerificacaoIntegridadeMidiaService._normalizar_resultado(entrada.get("resultado") or resultado_padrao.value)
            )
            detalhe = entrada.get("detalhe") or entrada.get("tipo_falha") or entrada.get("mensagem") or "Validacao de AIP registrada por relatorio externo."
            chave = (unidade.id, f"{resultado.value}:{detalhe}")
            if chave in vistos:
                continue
            vistos.add(chave)
            db.add(
                EventoPreservacao(
                    id_unidade_acondicionamento=unidade.id,
                    tipo_evento=TipoEventoPreservacao.FIXIDEZ,
                    resultado=resultado,
                    detalhe=f"Verificacao de integridade da midia {midia_id}: {detalhe}",
                    agente=verificacao.usuario_id,
                    correlacao=f"verificacao_integridade:{verificacao.id}",
                )
            )

    @staticmethod
    def _identificar_unidade(
        db: Session,
        midia_id: int,
        entrada: dict[str, Any],
    ) -> UnidadeAcondicionamento | None:
        unidade_id = entrada.get("unidade_id") or entrada.get("id_unidade_acondicionamento")
        if unidade_id:
            try:
                return db.get(UnidadeAcondicionamento, int(unidade_id))
            except (TypeError, ValueError):
                pass
        aip_id = entrada.get("aip_id") or entrada.get("id_aip")
        if aip_id:
            try:
                unidade = db.get(UnidadeAcondicionamento, int(aip_id))
                if unidade:
                    return unidade
            except (TypeError, ValueError):
                pass
        identificador = entrada.get("identificador") or entrada.get("codigo_aip") or entrada.get("aip")
        if identificador:
            unidade = (
                db.query(UnidadeAcondicionamento)
                .filter(UnidadeAcondicionamento.identificador == str(identificador))
                .one_or_none()
            )
            if unidade:
                return unidade
            copia = (
                db.query(CopiaUnidadeAcondicionamentoDigital)
                .filter(
                    CopiaUnidadeAcondicionamentoDigital.id_midia_armazenamento == midia_id,
                    CopiaUnidadeAcondicionamentoDigital.uri_copia.ilike(f"%{identificador}%"),
                )
                .first()
            )
            if copia:
                return db.get(UnidadeAcondicionamento, copia.id_unidade_acondicionamento)
        return None

    @staticmethod
    def _premis_verificacao(
        midia_id: int,
        verificacao: VerificacaoIntegridadeMidia,
        agente: str | None,
    ) -> dict[str, Any]:
        return {
            "eventType": TipoEventoMidiaArmazenamento.CHECAGEM_MIDIA.value,
            "eventDateTime": (verificacao.data_fim or verificacao.data_inicio).isoformat(),
            "eventDetail": VerificacaoIntegridadeMidiaService._detalhe_verificacao(verificacao.resultado, verificacao),
            "eventOutcomeInformation": {
                "eventOutcome": VerificacaoIntegridadeMidiaService._resultado_evento(verificacao.resultado).value,
                "eventOutcomeDetail": verificacao.observacoes or verificacao.resultado.value,
            },
            "linkingAgentIdentifier": {
                "linkingAgentIdentifierType": "usuario",
                "linkingAgentIdentifierValue": agente,
            },
            "linkingObjectIdentifier": {
                "linkingObjectIdentifierType": "midia_armazenamento",
                "linkingObjectIdentifierValue": str(midia_id),
            },
            "verificationSummary": {
                "totalAipsVerified": verificacao.total_aips_verificados,
                "totalSuccess": verificacao.total_sucesso,
                "totalFailure": verificacao.total_falha,
                "totalWarning": verificacao.total_alerta,
                "software": verificacao.software_utilizado,
                "softwareVersion": verificacao.versao_software,
            },
        }

    @staticmethod
    def _detalhe_verificacao(
        resultado: ResultadoVerificacaoIntegridade,
        verificacao: VerificacaoIntegridadeMidia,
    ) -> str:
        return (
            f"Verificacao de integridade de midia concluida com resultado {resultado.value}. "
            f"AIPs verificados: {verificacao.total_aips_verificados}; "
            f"sucesso: {verificacao.total_sucesso}; falha: {verificacao.total_falha}; alerta: {verificacao.total_alerta}."
        )

    @staticmethod
    def _parse_datetime(valor: Any) -> datetime | None:
        if isinstance(valor, datetime):
            return valor
        if isinstance(valor, str) and valor.strip():
            try:
                return datetime.fromisoformat(valor.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def _lista(valor: Any) -> list[Any]:
        return valor if isinstance(valor, list) else []
