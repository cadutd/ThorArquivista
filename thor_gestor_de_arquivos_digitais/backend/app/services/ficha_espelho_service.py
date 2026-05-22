from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.configuracao import ParametroSistema
from app.models.descricao_arquivistica import RegistroDescritivo
from app.models.enums import TipoSuporte
from app.models.ficha_espelho import ModeloFichaEspelho
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.schemas.ficha_espelho import (
    CAMPOS_PADRAO_FICHA_ESPELHO,
    FichaEspelhoDados,
    FichaEspelhoGerada,
    FichaEspelhoInstituicao,
    FichaEspelhoGerarRequest,
    ModeloFichaEspelhoCreate,
    ModeloFichaEspelhoUpdate,
    validar_dimensoes_modelo,
)
from app.services.admin_service import CONFIG_INSTITUICAO_CHAVE


class FichaEspelhoService:
    @staticmethod
    def listar_modelos(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        ativo: bool | None = None,
    ) -> tuple[list[ModeloFichaEspelho], int]:
        query = db.query(ModeloFichaEspelho)
        if q:
            like = f"%{q.strip()}%"
            query = query.filter(or_(ModeloFichaEspelho.nome.ilike(like), ModeloFichaEspelho.descricao.ilike(like)))
        if ativo is not None:
            query = query.filter(ModeloFichaEspelho.ativo == ativo)

        total = query.count()
        items = (
            query.order_by(ModeloFichaEspelho.nome.asc(), ModeloFichaEspelho.id.asc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100))
            .all()
        )
        return items, total

    @staticmethod
    def obter_modelo(db: Session, modelo_id: int) -> ModeloFichaEspelho | None:
        return db.get(ModeloFichaEspelho, modelo_id)

    @staticmethod
    def criar_modelo(db: Session, dados: ModeloFichaEspelhoCreate) -> ModeloFichaEspelho:
        modelo = ModeloFichaEspelho(**dados.model_dump())
        db.add(modelo)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Já existe um modelo de ficha espelho com este nome.")
        db.refresh(modelo)
        return modelo

    @staticmethod
    def atualizar_modelo(db: Session, modelo_id: int, dados: ModeloFichaEspelhoUpdate) -> ModeloFichaEspelho | None:
        modelo = db.get(ModeloFichaEspelho, modelo_id)
        if not modelo:
            return None

        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(modelo, campo, valor)

        validar_dimensoes_modelo(
            modelo.tamanho_papel,
            modelo.orientacao,
            modelo.colunas,
            modelo.largura_cm,
            modelo.altura_cm,
        )

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Já existe um modelo de ficha espelho com este nome.")
        db.refresh(modelo)
        return modelo

    @staticmethod
    def excluir_modelo(db: Session, modelo_id: int) -> bool:
        modelo = db.get(ModeloFichaEspelho, modelo_id)
        if not modelo:
            return False
        db.delete(modelo)
        db.commit()
        return True

    @staticmethod
    def obter_ou_criar_modelo_padrao(db: Session) -> ModeloFichaEspelho:
        modelo = db.query(ModeloFichaEspelho).order_by(ModeloFichaEspelho.id.asc()).first()
        if modelo:
            return modelo

        modelo = ModeloFichaEspelho(
            nome="Ficha espelho padrão",
            descricao="Modelo padrão com os metadados essenciais da caixa.",
            campos=list(CAMPOS_PADRAO_FICHA_ESPELHO),
            tamanho_papel="A4",
            orientacao="RETRATO",
            colunas=1,
            largura_cm=18.6,
            altura_cm=27.3,
            ativo=True,
        )
        db.add(modelo)
        db.commit()
        db.refresh(modelo)
        return modelo

    @staticmethod
    def gerar(db: Session, dados: FichaEspelhoGerarRequest) -> FichaEspelhoGerada:
        modelo = db.get(ModeloFichaEspelho, dados.modelo_id)
        if not modelo:
            raise LookupError("Modelo de ficha espelho não encontrado.")

        unidades = (
            db.query(UnidadeAcondicionamento)
            .options(selectinload(UnidadeAcondicionamento.registros_descritivos))
            .filter(UnidadeAcondicionamento.id.in_(dados.unidade_ids))
            .order_by(UnidadeAcondicionamento.identificador.asc(), UnidadeAcondicionamento.id.asc())
            .all()
        )
        encontrados = {unidade.id for unidade in unidades}
        faltantes = [unidade_id for unidade_id in dados.unidade_ids if unidade_id not in encontrados]
        if faltantes:
            raise LookupError(f"Unidades não encontradas: {', '.join(str(item) for item in faltantes)}.")

        unidades_digitais = [unidade.identificador for unidade in unidades if unidade.tipo_suporte == TipoSuporte.DIGITAL]
        if unidades_digitais:
            raise ValueError(
                "Apenas unidades que não são digitais podem ter ficha espelho impressa: "
                f"{', '.join(unidades_digitais)}."
            )

        instituicao = FichaEspelhoService._instituicao(db)
        fichas = [FichaEspelhoService._dados_unidade(unidade) for unidade in unidades]
        return FichaEspelhoGerada(modelo=modelo, instituicao=instituicao, fichas=fichas)

    @staticmethod
    def _instituicao(db: Session) -> FichaEspelhoInstituicao:
        parametro = db.get(ParametroSistema, CONFIG_INSTITUICAO_CHAVE)
        valor = parametro.valor if parametro else {}
        return FichaEspelhoInstituicao(
            nome=valor.get("nome"),
            logotipo_data_url=valor.get("logotipo_data_url"),
        )

    @staticmethod
    def _dados_unidade(unidade: UnidadeAcondicionamento) -> FichaEspelhoDados:
        registro = FichaEspelhoService._registro_representativo(unidade.registros_descritivos)
        ancestrais = FichaEspelhoService._ancestrais(registro)
        fundo = FichaEspelhoService._primeiro_titulo_por_nivel(ancestrais, {"1"})
        classe = FichaEspelhoService._primeiro_titulo_por_nivel(ancestrais, {"2", "3"})
        subclasse = FichaEspelhoService._primeiro_titulo_por_nivel(ancestrais, {"2.5", "3.5"})

        return FichaEspelhoDados(
            unidade_id=unidade.id,
            unidade_produtora=unidade.unidade or unidade.produtor or (registro.produtor if registro else None),
            fundo=fundo,
            classe=classe,
            subclasse=subclasse,
            descricao_conteudo=unidade.descricao or (registro.ambito_conteudo if registro else None) or unidade.titulo,
            data_limite=unidade.data_limite or FichaEspelhoService._data_limite_registro(registro),
            identificador_caixa=unidade.identificador,
            codigo_barras=unidade.codigo_barra or unidade.identificador,
        )

    @staticmethod
    def _registro_representativo(registros: list[RegistroDescritivo]) -> RegistroDescritivo | None:
        if not registros:
            return None
        return sorted(registros, key=lambda item: FichaEspelhoService._nivel_numero(item.nivel), reverse=True)[0]

    @staticmethod
    def _ancestrais(registro: RegistroDescritivo | None) -> list[RegistroDescritivo]:
        if not registro:
            return []
        items: list[RegistroDescritivo] = []
        atual: RegistroDescritivo | None = registro
        while atual:
            items.append(atual)
            atual = atual.parent
        return list(reversed(items))

    @staticmethod
    def _primeiro_titulo_por_nivel(registros: list[RegistroDescritivo], niveis: set[str]) -> str | None:
        for registro in registros:
            if registro.nivel in niveis:
                return registro.titulo
        return None

    @staticmethod
    def _data_limite_registro(registro: RegistroDescritivo | None) -> str | None:
        if not registro:
            return None
        if registro.data_inicial and registro.data_final:
            return f"{registro.data_inicial.isoformat()} a {registro.data_final.isoformat()}"
        if registro.data_inicial:
            return registro.data_inicial.isoformat()
        if registro.data_final:
            return registro.data_final.isoformat()
        return None

    @staticmethod
    def _nivel_numero(nivel: str) -> float:
        try:
            return float(nivel)
        except ValueError:
            return 0
