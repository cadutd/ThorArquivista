from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.armazenamento import (
    CompartimentoArmazenamento,
    EstruturaArmazenamento,
    LocalGuarda,
    MovimentacaoArmazenamento,
    PosicaoArmazenamento,
    ZonaGuarda,
)
from app.models.copia_unidade_acondicionamento_digital import (
    CopiaUnidadeAcondicionamentoDigital,
)
from app.models.enums import (
    TipoCompartimentoArmazenamento,
    TipoEstruturaArmazenamento,
    TipoPosicaoArmazenamento,
)
from app.models.midia_armazenamento import MidiaArmazenamento
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.schemas.armazenamento import (
    AtribuirPosicaoRequest,
    CompartimentoArmazenamentoCreate,
    CompartimentoArmazenamentoUpdate,
    EstruturaArmazenamentoCreate,
    EstruturaArmazenamentoUpdate,
    LocalGuardaCreate,
    LocalGuardaUpdate,
    PosicaoArmazenamentoCreate,
    PosicaoArmazenamentoUpdate,
    TopografiaGeradaRead,
    ZonaGuardaCreate,
    ZonaGuardaUpdate,
)
from app.services.admin_service import AdminService

ModelT = TypeVar("ModelT")


@dataclass(frozen=True)
class OcupacaoResumo:
    id: int
    nome: str
    total_posicoes: int
    posicoes_ocupadas: int
    capacidade_total: int
    ocupacao_total: int
    taxa_ocupacao: float


class ArmazenamentoService:
    @staticmethod
    def listar_locais(db: Session, limit: int = 50, offset: int = 0) -> list[LocalGuarda]:
        return (
            db.query(LocalGuarda)
            .order_by(LocalGuarda.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def criar_local(db: Session, dados: LocalGuardaCreate) -> LocalGuarda:
        local = LocalGuarda(**dados.model_dump())
        db.add(local)
        return ArmazenamentoService._commit_refresh(db, local, "Código de local já cadastrado.")

    @staticmethod
    def obter_local(db: Session, id: int) -> LocalGuarda | None:
        return db.get(LocalGuarda, id)

    @staticmethod
    def atualizar_local(db: Session, id: int, dados: LocalGuardaUpdate) -> LocalGuarda | None:
        local = db.get(LocalGuarda, id)
        if not local:
            return None
        ArmazenamentoService._apply(local, dados.model_dump(exclude_unset=True))
        return ArmazenamentoService._commit_refresh(db, local, "Código de local já cadastrado.")

    @staticmethod
    def excluir_local(db: Session, id: int) -> bool:
        local = db.get(LocalGuarda, id)
        if not local:
            return False
        db.delete(local)
        db.commit()
        return True

    @staticmethod
    def listar_zonas(
        db: Session,
        id_local_guarda: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ZonaGuarda]:
        query = db.query(ZonaGuarda)
        if id_local_guarda:
            query = query.filter(ZonaGuarda.id_local_guarda == id_local_guarda)
        return query.order_by(ZonaGuarda.id.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def criar_zona(db: Session, dados: ZonaGuardaCreate) -> ZonaGuarda:
        if not db.get(LocalGuarda, dados.id_local_guarda):
            raise LookupError("Local de guarda não encontrado.")
        zona = ZonaGuarda(**dados.model_dump())
        db.add(zona)
        return ArmazenamentoService._commit_refresh(db, zona, "Código de zona já cadastrado neste local.")

    @staticmethod
    def obter_zona(db: Session, id: int) -> ZonaGuarda | None:
        return db.get(ZonaGuarda, id)

    @staticmethod
    def atualizar_zona(db: Session, id: int, dados: ZonaGuardaUpdate) -> ZonaGuarda | None:
        zona = db.get(ZonaGuarda, id)
        if not zona:
            return None
        payload = dados.model_dump(exclude_unset=True)
        if "id_local_guarda" in payload and not db.get(LocalGuarda, payload["id_local_guarda"]):
            raise LookupError("Local de guarda não encontrado.")
        ArmazenamentoService._apply(zona, payload)
        return ArmazenamentoService._commit_refresh(
            db,
            zona,
            "Código de zona já cadastrado neste local.",
        )

    @staticmethod
    def excluir_zona(db: Session, id: int) -> bool:
        zona = db.get(ZonaGuarda, id)
        if not zona:
            return False
        zona.ativo = False
        db.commit()
        return True

    @staticmethod
    def listar_estruturas(
        db: Session,
        id_zona_guarda: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EstruturaArmazenamento]:
        query = db.query(EstruturaArmazenamento)
        if id_zona_guarda:
            query = query.filter(EstruturaArmazenamento.id_zona_guarda == id_zona_guarda)
        return query.order_by(EstruturaArmazenamento.id.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def criar_estrutura(db: Session, dados: EstruturaArmazenamentoCreate) -> EstruturaArmazenamento:
        if not db.get(ZonaGuarda, dados.id_zona_guarda):
            raise LookupError("Zona de guarda não encontrada.")
        estrutura = EstruturaArmazenamento(**dados.model_dump())
        db.add(estrutura)
        return ArmazenamentoService._commit_refresh(
            db,
            estrutura,
            "Código de estrutura já cadastrado nesta zona.",
        )

    @staticmethod
    def obter_estrutura(db: Session, id: int) -> EstruturaArmazenamento | None:
        return db.get(EstruturaArmazenamento, id)

    @staticmethod
    def atualizar_estrutura(
        db: Session,
        id: int,
        dados: EstruturaArmazenamentoUpdate,
    ) -> EstruturaArmazenamento | None:
        estrutura = db.get(EstruturaArmazenamento, id)
        if not estrutura:
            return None
        payload = dados.model_dump(exclude_unset=True)
        if "id_zona_guarda" in payload and not db.get(ZonaGuarda, payload["id_zona_guarda"]):
            raise LookupError("Zona de guarda não encontrada.")
        ArmazenamentoService._apply(estrutura, payload)
        return ArmazenamentoService._commit_refresh(
            db,
            estrutura,
            "Código de estrutura já cadastrado nesta zona.",
        )

    @staticmethod
    def excluir_estrutura(db: Session, id: int) -> bool:
        estrutura = db.get(EstruturaArmazenamento, id)
        if not estrutura:
            return False
        estrutura.ativo = False
        db.commit()
        return True

    @staticmethod
    def listar_compartimentos(
        db: Session,
        id_estrutura_armazenamento: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CompartimentoArmazenamento]:
        query = db.query(CompartimentoArmazenamento)
        if id_estrutura_armazenamento:
            query = query.filter(
                CompartimentoArmazenamento.id_estrutura_armazenamento
                == id_estrutura_armazenamento
            )
        return query.order_by(CompartimentoArmazenamento.id.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def criar_compartimento(
        db: Session,
        dados: CompartimentoArmazenamentoCreate,
    ) -> CompartimentoArmazenamento:
        if not db.get(EstruturaArmazenamento, dados.id_estrutura_armazenamento):
            raise LookupError("Estrutura de armazenamento não encontrada.")
        compartimento = CompartimentoArmazenamento(**dados.model_dump())
        db.add(compartimento)
        return ArmazenamentoService._commit_refresh(
            db,
            compartimento,
            "Código de compartimento já cadastrado nesta estrutura.",
        )

    @staticmethod
    def obter_compartimento(db: Session, id: int) -> CompartimentoArmazenamento | None:
        return db.get(CompartimentoArmazenamento, id)

    @staticmethod
    def atualizar_compartimento(
        db: Session,
        id: int,
        dados: CompartimentoArmazenamentoUpdate,
    ) -> CompartimentoArmazenamento | None:
        compartimento = db.get(CompartimentoArmazenamento, id)
        if not compartimento:
            return None
        payload = dados.model_dump(exclude_unset=True)
        if "id_estrutura_armazenamento" in payload and not db.get(
            EstruturaArmazenamento,
            payload["id_estrutura_armazenamento"],
        ):
            raise LookupError("Estrutura de armazenamento não encontrada.")
        ArmazenamentoService._apply(compartimento, payload)
        return ArmazenamentoService._commit_refresh(
            db,
            compartimento,
            "Código de compartimento já cadastrado nesta estrutura.",
        )

    @staticmethod
    def excluir_compartimento(db: Session, id: int) -> bool:
        compartimento = db.get(CompartimentoArmazenamento, id)
        if not compartimento:
            return False
        compartimento.ativo = False
        db.commit()
        return True

    @staticmethod
    def listar_posicoes(
        db: Session,
        ocupada: bool | None = None,
        id_zona_guarda: int | None = None,
        id_local_guarda: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PosicaoArmazenamento]:
        query = ArmazenamentoService._posicoes_query(db)
        if ocupada is not None:
            query = query.filter(PosicaoArmazenamento.ocupada.is_(ocupada))
        if id_zona_guarda:
            query = query.filter(EstruturaArmazenamento.id_zona_guarda == id_zona_guarda)
        if id_local_guarda:
            query = query.filter(ZonaGuarda.id_local_guarda == id_local_guarda)
        return query.order_by(PosicaoArmazenamento.codigo_completo).offset(offset).limit(limit).all()

    @staticmethod
    def criar_posicao(db: Session, dados: PosicaoArmazenamentoCreate) -> PosicaoArmazenamento:
        if not db.get(CompartimentoArmazenamento, dados.id_compartimento_armazenamento):
            raise LookupError("Compartimento de armazenamento não encontrado.")
        posicao = PosicaoArmazenamento(**dados.model_dump())
        db.add(posicao)
        return ArmazenamentoService._commit_refresh(db, posicao, "Posição já cadastrada.")

    @staticmethod
    def obter_posicao(db: Session, id: int) -> PosicaoArmazenamento | None:
        return (
            ArmazenamentoService._posicoes_query(db)
            .filter(PosicaoArmazenamento.id == id)
            .first()
        )

    @staticmethod
    def atualizar_posicao(
        db: Session,
        id: int,
        dados: PosicaoArmazenamentoUpdate,
    ) -> PosicaoArmazenamento | None:
        posicao = db.get(PosicaoArmazenamento, id)
        if not posicao:
            return None
        payload = dados.model_dump(exclude_unset=True)
        if "id_compartimento_armazenamento" in payload and not db.get(
            CompartimentoArmazenamento,
            payload["id_compartimento_armazenamento"],
        ):
            raise LookupError("Compartimento de armazenamento não encontrado.")
        ArmazenamentoService._apply(posicao, payload)
        return ArmazenamentoService._commit_refresh(db, posicao, "Posição já cadastrada.")

    @staticmethod
    def excluir_posicao(db: Session, id: int) -> bool:
        posicao = db.get(PosicaoArmazenamento, id)
        if not posicao:
            return False
        if ArmazenamentoService._ocupacao_posicao(db, id) > 0:
            raise ValueError("Não é possível inativar posição ocupada.")
        posicao.ativo = False
        db.commit()
        return True

    @staticmethod
    def gerar_topografia(db: Session, id_zona_guarda: int) -> TopografiaGeradaRead:
        zona = (
            db.query(ZonaGuarda)
            .options(joinedload(ZonaGuarda.local_guarda))
            .filter(ZonaGuarda.id == id_zona_guarda)
            .first()
        )
        if not zona:
            raise LookupError("Zona de guarda não encontrada.")

        params = [
            zona.quantidade_corredores,
            zona.quantidade_modulos_por_corredor,
            zona.quantidade_estantes_por_modulo,
            zona.quantidade_prateleiras_por_estante,
            zona.capacidade_caixas_por_prateleira,
        ]
        if any(value is None or value <= 0 for value in params):
            raise ValueError("Parâmetros de geração topográfica incompletos ou inválidos.")

        if (
            db.query(EstruturaArmazenamento)
            .filter(EstruturaArmazenamento.id_zona_guarda == zona.id)
            .first()
        ):
            raise ValueError("A zona já possui topografia gerada.")

        estruturas_criadas = 0
        compartimentos_criados = 0
        posicoes_criadas = 0
        digitos = AdminService.obter_configuracao_enderecamento(db).digitos_codigo_estrutura

        try:
            for corredor in range(1, zona.quantidade_corredores + 1):
                for modulo in range(1, zona.quantidade_modulos_por_corredor + 1):
                    for estante in range(1, zona.quantidade_estantes_por_modulo + 1):
                        estrutura_codigo = (
                            f"C{corredor:0{digitos.corredor}d}-"
                            f"M{modulo:0{digitos.modulo}d}-"
                            f"E{estante:0{digitos.estante}d}"
                        )
                        estrutura = EstruturaArmazenamento(
                            id_zona_guarda=zona.id,
                            codigo=estrutura_codigo,
                            nome=f"Estante {estrutura_codigo}",
                            tipo_estrutura=TipoEstruturaArmazenamento.ESTANTE,
                            ordem=estruturas_criadas + 1,
                            capacidade_total=(
                                zona.quantidade_prateleiras_por_estante
                                * zona.capacidade_caixas_por_prateleira
                            ),
                        )
                        db.add(estrutura)
                        db.flush()
                        estruturas_criadas += 1

                        for prateleira in range(1, zona.quantidade_prateleiras_por_estante + 1):
                            compartimento_codigo = f"P{prateleira:02d}"
                            compartimento = CompartimentoArmazenamento(
                                id_estrutura_armazenamento=estrutura.id,
                                codigo=compartimento_codigo,
                                nome=f"Prateleira {prateleira:02d}",
                                tipo_compartimento=TipoCompartimentoArmazenamento.PRATELEIRA,
                                ordem=prateleira,
                                capacidade_posicoes=zona.capacidade_caixas_por_prateleira,
                            )
                            db.add(compartimento)
                            db.flush()
                            compartimentos_criados += 1

                            for caixa in range(1, zona.capacidade_caixas_por_prateleira + 1):
                                posicao_codigo = f"CX{caixa:03d}"
                                codigo_completo = (
                                    f"{zona.local_guarda.codigo}-{zona.codigo}-"
                                    f"{estrutura_codigo}-{compartimento_codigo}-{posicao_codigo}"
                                )
                                db.add(
                                    PosicaoArmazenamento(
                                        id_compartimento_armazenamento=compartimento.id,
                                        codigo=posicao_codigo,
                                        codigo_completo=codigo_completo,
                                        tipo_posicao=TipoPosicaoArmazenamento.POSICAO_CAIXA,
                                        ordem=caixa,
                                        capacidade_unidades=1,
                                    )
                                )
                                posicoes_criadas += 1

            db.commit()
        except Exception:
            db.rollback()
            raise

        return TopografiaGeradaRead(
            id_zona_guarda=zona.id,
            estruturas_criadas=estruturas_criadas,
            compartimentos_criados=compartimentos_criados,
            posicoes_criadas=posicoes_criadas,
        )

    @staticmethod
    def atribuir_posicao_unidade(
        db: Session,
        id_unidade: int,
        dados: AtribuirPosicaoRequest,
    ) -> UnidadeAcondicionamento:
        unidade = db.get(UnidadeAcondicionamento, id_unidade)
        if not unidade:
            raise LookupError("Unidade de acondicionamento não encontrada.")
        ArmazenamentoService._atribuir_posicao(
            db,
            unidade,
            dados,
            "id_unidade_acondicionamento",
        )
        return unidade

    @staticmethod
    def atribuir_posicao_midia(
        db: Session,
        id_midia: int,
        dados: AtribuirPosicaoRequest,
    ) -> MidiaArmazenamento:
        midia = db.get(MidiaArmazenamento, id_midia)
        if not midia:
            raise LookupError("Mídia de armazenamento não encontrada.")
        ArmazenamentoService._atribuir_posicao(db, midia, dados, "id_midia_armazenamento")
        return midia

    @staticmethod
    def atribuir_posicao_copia(
        db: Session,
        id_copia: int,
        dados: AtribuirPosicaoRequest,
    ) -> CopiaUnidadeAcondicionamentoDigital:
        copia = db.get(CopiaUnidadeAcondicionamentoDigital, id_copia)
        if not copia:
            raise LookupError("Cópia digital não encontrada.")
        ArmazenamentoService._atribuir_posicao(
            db,
            copia,
            dados,
            "id_copia_unidade_acondicionamento_digital",
        )
        return copia

    @staticmethod
    def listar_movimentacoes(
        db: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovimentacaoArmazenamento]:
        return (
            db.query(MovimentacaoArmazenamento)
            .order_by(MovimentacaoArmazenamento.data_movimentacao.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def listar_movimentacoes_unidade(db: Session, id: int) -> list[MovimentacaoArmazenamento]:
        return ArmazenamentoService._listar_movimentacoes_por(
            db,
            MovimentacaoArmazenamento.id_unidade_acondicionamento,
            id,
        )

    @staticmethod
    def listar_movimentacoes_midia(db: Session, id: int) -> list[MovimentacaoArmazenamento]:
        return ArmazenamentoService._listar_movimentacoes_por(
            db,
            MovimentacaoArmazenamento.id_midia_armazenamento,
            id,
        )

    @staticmethod
    def listar_movimentacoes_copia(db: Session, id: int) -> list[MovimentacaoArmazenamento]:
        return ArmazenamentoService._listar_movimentacoes_por(
            db,
            MovimentacaoArmazenamento.id_copia_unidade_acondicionamento_digital,
            id,
        )

    @staticmethod
    def localizacao_unidade(db: Session, id_unidade: int) -> PosicaoArmazenamento | None:
        unidade = db.get(UnidadeAcondicionamento, id_unidade)
        if not unidade:
            raise LookupError("Unidade de acondicionamento não encontrada.")
        if not unidade.id_posicao_armazenamento:
            return None
        return ArmazenamentoService.obter_posicao(db, unidade.id_posicao_armazenamento)

    @staticmethod
    def ocupacao_zona(db: Session, id_zona: int) -> OcupacaoResumo:
        zona = db.get(ZonaGuarda, id_zona)
        if not zona:
            raise LookupError("Zona de guarda não encontrada.")
        return ArmazenamentoService._ocupacao_por_escopo(db, zona.id, zona.nome, id_zona_guarda=id_zona)

    @staticmethod
    def ocupacao_local(db: Session, id_local: int) -> OcupacaoResumo:
        local = db.get(LocalGuarda, id_local)
        if not local:
            raise LookupError("Local de guarda não encontrado.")
        return ArmazenamentoService._ocupacao_por_escopo(
            db,
            local.id,
            local.nome,
            id_local_guarda=id_local,
        )

    @staticmethod
    def _atribuir_posicao(
        db: Session,
        objeto: Any,
        dados: AtribuirPosicaoRequest,
        movimento_field: str,
    ) -> None:
        posicao = db.get(PosicaoArmazenamento, dados.id_posicao)
        if not posicao:
            raise LookupError("Posição de armazenamento não encontrada.")
        if not posicao.ativo:
            raise ValueError("Não é possível atribuir uma posição inativa.")

        origem_id = objeto.id_posicao_armazenamento
        if origem_id == posicao.id:
            raise ValueError("Objeto já está atribuído a esta posição.")

        if ArmazenamentoService._ocupacao_posicao(db, posicao.id) >= posicao.capacidade_unidades:
            raise ValueError("A posição não possui capacidade disponível.")

        try:
            objeto.id_posicao_armazenamento = posicao.id
            posicao.ocupada = True
            if origem_id:
                ArmazenamentoService._atualizar_ocupacao_posicao(db, origem_id)
            db.add(
                MovimentacaoArmazenamento(
                    **{
                        movimento_field: objeto.id,
                        "id_posicao_origem": origem_id,
                        "id_posicao_destino": posicao.id,
                        "responsavel": dados.responsavel,
                        "motivo": dados.motivo,
                        "observacoes": dados.observacoes,
                    }
                )
            )
            db.commit()
            db.refresh(objeto)
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _ocupacao_posicao(db: Session, id_posicao: int) -> int:
        unidade_count = (
            db.query(func.count(UnidadeAcondicionamento.id))
            .filter(UnidadeAcondicionamento.id_posicao_armazenamento == id_posicao)
            .scalar()
            or 0
        )
        midia_count = (
            db.query(func.count(MidiaArmazenamento.id))
            .filter(MidiaArmazenamento.id_posicao_armazenamento == id_posicao)
            .scalar()
            or 0
        )
        copia_count = (
            db.query(func.count(CopiaUnidadeAcondicionamentoDigital.id))
            .filter(CopiaUnidadeAcondicionamentoDigital.id_posicao_armazenamento == id_posicao)
            .scalar()
            or 0
        )
        return unidade_count + midia_count + copia_count

    @staticmethod
    def _atualizar_ocupacao_posicao(db: Session, id_posicao: int) -> None:
        posicao = db.get(PosicaoArmazenamento, id_posicao)
        if posicao:
            posicao.ocupada = ArmazenamentoService._ocupacao_posicao(db, id_posicao) > 0

    @staticmethod
    def _ocupacao_por_escopo(
        db: Session,
        id: int,
        nome: str,
        id_zona_guarda: int | None = None,
        id_local_guarda: int | None = None,
    ) -> OcupacaoResumo:
        posicoes = ArmazenamentoService.listar_posicoes(
            db,
            id_zona_guarda=id_zona_guarda,
            id_local_guarda=id_local_guarda,
            limit=100000,
        )
        capacidade_total = sum(posicao.capacidade_unidades for posicao in posicoes)
        ocupacao_total = sum(ArmazenamentoService._ocupacao_posicao(db, posicao.id) for posicao in posicoes)
        total_posicoes = len(posicoes)
        posicoes_ocupadas = sum(1 for posicao in posicoes if posicao.ocupada)
        return OcupacaoResumo(
            id=id,
            nome=nome,
            total_posicoes=total_posicoes,
            posicoes_ocupadas=posicoes_ocupadas,
            capacidade_total=capacidade_total,
            ocupacao_total=ocupacao_total,
            taxa_ocupacao=round((ocupacao_total / capacidade_total) * 100, 2)
            if capacidade_total
            else 0,
        )

    @staticmethod
    def _posicoes_query(db: Session):
        return (
            db.query(PosicaoArmazenamento)
            .join(PosicaoArmazenamento.compartimento_armazenamento)
            .join(CompartimentoArmazenamento.estrutura_armazenamento)
            .join(EstruturaArmazenamento.zona_guarda)
            .join(ZonaGuarda.local_guarda)
            .options(
                joinedload(PosicaoArmazenamento.compartimento_armazenamento)
                .joinedload(CompartimentoArmazenamento.estrutura_armazenamento)
                .joinedload(EstruturaArmazenamento.zona_guarda)
                .joinedload(ZonaGuarda.local_guarda)
            )
        )

    @staticmethod
    def _listar_movimentacoes_por(db: Session, column: Any, id: int) -> list[MovimentacaoArmazenamento]:
        return (
            db.query(MovimentacaoArmazenamento)
            .filter(column == id)
            .order_by(MovimentacaoArmazenamento.data_movimentacao.desc())
            .all()
        )

    @staticmethod
    def _apply(model: Any, payload: dict[str, Any]) -> None:
        for field, value in payload.items():
            setattr(model, field, value)

    @staticmethod
    def _commit_refresh(db: Session, model: ModelT, conflict_message: str) -> ModelT:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(conflict_message)
        db.refresh(model)
        return model
