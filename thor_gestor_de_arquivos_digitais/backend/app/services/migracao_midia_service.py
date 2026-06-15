from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.enums import (
    ResultadoEventoPreservacao,
    StatusMigracaoMidia,
    StatusMidiaArmazenamento,
    TipoEventoMidiaArmazenamento,
)
from app.models.midia_armazenamento import MidiaArmazenamento, TipoMidiaArmazenamento
from app.models.migracao_midia import MigracaoMidia
from app.schemas.evento_midia_armazenamento import EventoMidiaArmazenamentoCreate
from app.schemas.migracao_midia import (
    MigracaoMidiaConclusao,
    MigracaoMidiaEtapaCreate,
    MigracaoMidiaIniciar,
    MigracaoMidiaRelatorioCreate,
    MigracaoMidiaUpdate,
)
from app.services.evento_midia_armazenamento_service import EventoMidiaArmazenamentoService
from app.services.midia_armazenamento_service import MidiaArmazenamentoService


class MigracaoMidiaService:
    @staticmethod
    def iniciar_migracao(
        db: Session,
        midia_origem_id: int,
        dados: MigracaoMidiaIniciar,
        usuario_id: str | None,
    ) -> MigracaoMidia:
        origem = db.get(MidiaArmazenamento, midia_origem_id)
        if not origem:
            raise LookupError("Midia de origem nao encontrada.")
        if origem.status in {
            StatusMidiaArmazenamento.EM_MIGRACAO,
            StatusMidiaArmazenamento.MIGRADA,
            StatusMidiaArmazenamento.DESATIVADA,
            StatusMidiaArmazenamento.PERDIDA,
        }:
            raise ValueError("Midia de origem nao pode ser migrada neste status.")

        payload = dados.nova_midia.model_dump()
        tipo = db.get(TipoMidiaArmazenamento, payload["tipo_midia_id"])
        if not tipo or not tipo.ativo:
            raise LookupError("Tipo de midia de destino nao encontrado ou inativo.")

        payload["midia_origem_id"] = origem.id
        payload["status"] = StatusMidiaArmazenamento.EM_MIGRACAO
        payload["ativo"] = True
        destino = MidiaArmazenamento(**payload)
        MidiaArmazenamentoService._aplicar_calculos(destino, tipo)
        origem.status = StatusMidiaArmazenamento.EM_MIGRACAO
        db.add(destino)
        try:
            db.flush()
            evento_origem = EventoMidiaArmazenamentoService.registrar(
                db,
                origem.id,
                EventoMidiaArmazenamentoCreate(
                    tipo_evento=TipoEventoMidiaArmazenamento.MIGRACAO_MIDIA,
                    resultado=ResultadoEventoPreservacao.ALERTA,
                    detalhe=f"Migracao iniciada para a midia {destino.id}.",
                    agente=usuario_id,
                ),
                commit=False,
            )
            EventoMidiaArmazenamentoService.registrar(
                db,
                destino.id,
                EventoMidiaArmazenamentoCreate(
                    tipo_evento=TipoEventoMidiaArmazenamento.MIGRACAO_MIDIA,
                    resultado=ResultadoEventoPreservacao.ALERTA,
                    detalhe=f"Midia criada como destino da migracao da midia {origem.id}.",
                    agente=usuario_id,
                ),
                commit=False,
            )
            db.flush()
            migracao = MigracaoMidia(
                midia_origem_id=origem.id,
                midia_destino_id=destino.id,
                usuario_responsavel_id=usuario_id,
                status=StatusMigracaoMidia.EM_EXECUCAO,
                motivo_migracao=dados.motivo_migracao,
                procedimento_utilizado=dados.procedimento_utilizado,
                software_utilizado=dados.software_utilizado,
                versao_software=dados.versao_software,
                observacoes=dados.observacoes,
                evento_id=evento_origem.id,
                etapas=[],
                relatorios=[],
            )
            db.add(migracao)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Nao foi possivel iniciar a migracao. Verifique dados da nova midia.")
        db.refresh(migracao)
        return MigracaoMidiaService.obter(db, migracao.id) or migracao

    @staticmethod
    def listar(db: Session, limit: int = 50, offset: int = 0) -> tuple[list[MigracaoMidia], int]:
        query = db.query(MigracaoMidia).options(
            joinedload(MigracaoMidia.midia_origem),
            joinedload(MigracaoMidia.midia_destino),
        )
        total = query.count()
        items = query.order_by(MigracaoMidia.data_inicio.desc()).offset(max(offset, 0)).limit(min(max(limit, 1), 100)).all()
        return items, total

    @staticmethod
    def obter(db: Session, migracao_id: uuid.UUID) -> MigracaoMidia | None:
        return (
            db.query(MigracaoMidia)
            .options(joinedload(MigracaoMidia.midia_origem), joinedload(MigracaoMidia.midia_destino))
            .filter(MigracaoMidia.id == migracao_id)
            .one_or_none()
        )

    @staticmethod
    def atualizar(db: Session, migracao_id: uuid.UUID, dados: MigracaoMidiaUpdate) -> MigracaoMidia | None:
        migracao = db.get(MigracaoMidia, migracao_id)
        if not migracao:
            return None
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(migracao, campo, valor)
        db.commit()
        return MigracaoMidiaService.obter(db, migracao_id)

    @staticmethod
    def registrar_etapa(db: Session, migracao_id: uuid.UUID, dados: MigracaoMidiaEtapaCreate, usuario_id: str | None) -> MigracaoMidia:
        migracao = db.get(MigracaoMidia, migracao_id)
        if not migracao:
            raise LookupError("Migracao de midia nao encontrada.")
        etapas = list(migracao.etapas or [])
        etapas.append({
            "data": (dados.data or datetime.now(timezone.utc)).isoformat(),
            "descricao": dados.descricao,
            "resultado": dados.resultado,
            "evidencias": dados.evidencias or {},
            "usuario": usuario_id,
        })
        migracao.etapas = etapas
        db.commit()
        return MigracaoMidiaService.obter(db, migracao_id) or migracao

    @staticmethod
    def anexar_relatorio(db: Session, migracao_id: uuid.UUID, dados: MigracaoMidiaRelatorioCreate, usuario_id: str | None) -> MigracaoMidia:
        migracao = db.get(MigracaoMidia, migracao_id)
        if not migracao:
            raise LookupError("Migracao de midia nao encontrada.")
        relatorios = list(migracao.relatorios or [])
        relatorios.append({
            "data": datetime.now(timezone.utc).isoformat(),
            "tipo": dados.tipo,
            "referencia": dados.referencia,
            "descricao": dados.descricao,
            "usuario": usuario_id,
        })
        migracao.relatorios = relatorios
        db.commit()
        return MigracaoMidiaService.obter(db, migracao_id) or migracao

    @staticmethod
    def concluir_migracao(db: Session, migracao_id: uuid.UUID, dados: MigracaoMidiaConclusao, usuario_id: str | None) -> MigracaoMidia:
        migracao = db.get(MigracaoMidia, migracao_id)
        if not migracao:
            raise LookupError("Migracao de midia nao encontrada.")
        if dados.resultado != StatusMigracaoMidia.CONCLUIDA:
            migracao.status = dados.resultado
            migracao.observacoes = dados.observacoes or migracao.observacoes
            db.commit()
            return MigracaoMidiaService.obter(db, migracao_id) or migracao

        origem = db.get(MidiaArmazenamento, migracao.midia_origem_id)
        destino = db.get(MidiaArmazenamento, migracao.midia_destino_id)
        if not origem or not destino:
            raise LookupError("Midia de origem ou destino nao encontrada.")

        migracao.status = StatusMigracaoMidia.CONCLUIDA
        migracao.data_conclusao = datetime.now(timezone.utc)
        migracao.observacoes = dados.observacoes or migracao.observacoes
        migracao.relatorio_integridade_origem = dados.relatorio_integridade_origem or migracao.relatorio_integridade_origem
        migracao.relatorio_integridade_destino = dados.relatorio_integridade_destino or migracao.relatorio_integridade_destino
        origem.status = StatusMidiaArmazenamento.MIGRADA
        origem.ativo = False
        origem.data_desativacao = migracao.data_conclusao
        origem.motivo_desativacao = dados.observacoes or migracao.motivo_migracao
        destino.status = StatusMidiaArmazenamento.ATIVA
        destino.ativo = True

        EventoMidiaArmazenamentoService.registrar(
            db,
            origem.id,
            EventoMidiaArmazenamentoCreate(
                tipo_evento=TipoEventoMidiaArmazenamento.MIGRACAO_MIDIA,
                resultado=ResultadoEventoPreservacao.SUCESSO,
                detalhe=f"Migracao concluida para a midia {destino.id}.",
                agente=usuario_id,
            ),
            commit=False,
        )
        EventoMidiaArmazenamentoService.registrar(
            db,
            destino.id,
            EventoMidiaArmazenamentoCreate(
                tipo_evento=TipoEventoMidiaArmazenamento.MIGRACAO_MIDIA,
                resultado=ResultadoEventoPreservacao.SUCESSO,
                detalhe=f"Midia ativada como destino da migracao da midia {origem.id}.",
                agente=usuario_id,
            ),
            commit=False,
        )
        db.commit()
        return MigracaoMidiaService.obter(db, migracao_id) or migracao
