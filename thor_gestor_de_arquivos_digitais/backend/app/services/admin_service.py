from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.configuracao import ParametroSistema
from app.schemas.admin import ConfiguracaoEnderecamento, ConfiguracaoInstituicao

CONFIG_ENDERECAMENTO_CHAVE = "enderecamento"
CONFIG_INSTITUICAO_CHAVE = "instituicao"


class AdminService:
    @staticmethod
    def obter_configuracao_enderecamento(db: Session) -> ConfiguracaoEnderecamento:
        parametro = db.get(ParametroSistema, CONFIG_ENDERECAMENTO_CHAVE)
        if not parametro:
            return ConfiguracaoEnderecamento()
        return ConfiguracaoEnderecamento.model_validate(parametro.valor)

    @staticmethod
    def salvar_configuracao_enderecamento(
        db: Session,
        dados: ConfiguracaoEnderecamento,
    ) -> ConfiguracaoEnderecamento:
        parametro = db.get(ParametroSistema, CONFIG_ENDERECAMENTO_CHAVE)
        valor = dados.model_dump()
        if parametro:
            parametro.valor = valor
        else:
            parametro = ParametroSistema(
                chave=CONFIG_ENDERECAMENTO_CHAVE,
                valor=valor,
                descricao="Parametrizações do módulo de endereçamento.",
            )
            db.add(parametro)
        db.commit()
        return dados

    @staticmethod
    def obter_configuracao_instituicao(db: Session) -> ConfiguracaoInstituicao:
        parametro = db.get(ParametroSistema, CONFIG_INSTITUICAO_CHAVE)
        if not parametro:
            return ConfiguracaoInstituicao()
        return ConfiguracaoInstituicao.model_validate(parametro.valor)

    @staticmethod
    def salvar_configuracao_instituicao(
        db: Session,
        dados: ConfiguracaoInstituicao,
    ) -> ConfiguracaoInstituicao:
        parametro = db.get(ParametroSistema, CONFIG_INSTITUICAO_CHAVE)
        valor = dados.model_dump()
        if parametro:
            parametro.valor = valor
        else:
            parametro = ParametroSistema(
                chave=CONFIG_INSTITUICAO_CHAVE,
                valor=valor,
                descricao="Dados institucionais usados em documentos gerados.",
            )
            db.add(parametro)
        db.commit()
        return dados
