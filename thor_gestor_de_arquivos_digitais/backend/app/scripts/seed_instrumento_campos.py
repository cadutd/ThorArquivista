from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import TipoCampoInstrumento
from app.scripts.seed_instrumentos_pesquisa import (
    SEED_NAMESPACE as INSTRUMENTO_NAMESPACE,
    build_seed_data as build_instrumento_seed_data,
    upsert_instrumento,
)

CAMPO_NAMESPACE = uuid.UUID("ca40b39f-52bc-4fc1-9d67-0c05be3b3d16")


@dataclass(frozen=True)
class InstrumentoCampoSeed:
    instrumento_codigo: str
    nome: str
    chave: str
    tipo: TipoCampoInstrumento
    ordem: int
    obrigatorio: bool = False
    multiplo: bool = False
    valor_padrao: str | None = None
    placeholder: str | None = None
    ajuda: str | None = None
    aparece_cadastro: bool = True
    aparece_listagem: bool = True
    aparece_busca: bool = True
    filtro_avancado: bool = False
    facetavel: bool = False
    ordenavel: bool = False
    opcoes: dict[str, Any] | list[Any] | None = None
    validacoes: dict[str, Any] | list[Any] | None = None

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(CAMPO_NAMESPACE, f"{self.instrumento_codigo}:{self.chave}")

    @property
    def instrumento_id(self) -> uuid.UUID:
        return uuid.uuid5(INSTRUMENTO_NAMESPACE, self.instrumento_codigo)


def build_seed_data() -> list[InstrumentoCampoSeed]:
    return [
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-GUIA-ACERVO-GERAL",
            nome="Código de referência",
            chave="codigo_referencia",
            tipo=TipoCampoInstrumento.TEXTO_CURTO,
            ordem=0,
            obrigatorio=True,
            placeholder="BR THOR FND 001",
            ajuda="Código usado para identificar o conjunto descrito.",
            aparece_listagem=True,
            aparece_busca=True,
            filtro_avancado=True,
            ordenavel=True,
            validacoes={"max_length": 120},
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-GUIA-ACERVO-GERAL",
            nome="Título",
            chave="titulo",
            tipo=TipoCampoInstrumento.TEXTO_CURTO,
            ordem=1,
            obrigatorio=True,
            placeholder="Nome do fundo ou coleção",
            ajuda="Informe o título principal apresentado ao público.",
            ordenavel=True,
            validacoes={"max_length": 255},
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-GUIA-ACERVO-GERAL",
            nome="Resumo",
            chave="resumo",
            tipo=TipoCampoInstrumento.TEXTO_LONGO,
            ordem=2,
            ajuda="Síntese do conteúdo e abrangência do acervo.",
            aparece_listagem=False,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-GUIA-ACERVO-GERAL",
            nome="Período de abrangência",
            chave="periodo_abrangencia",
            tipo=TipoCampoInstrumento.PERIODO,
            ordem=3,
            aparece_listagem=False,
            filtro_avancado=True,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-GUIA-ACERVO-GERAL",
            nome="Disponível ao público",
            chave="disponivel_publico",
            tipo=TipoCampoInstrumento.BOOLEANO,
            ordem=4,
            valor_padrao="true",
            facetavel=True,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-INVENTARIO-FUNDO-ADM",
            nome="Série documental",
            chave="serie_documental",
            tipo=TipoCampoInstrumento.LISTA_SIMPLES,
            ordem=0,
            obrigatorio=True,
            filtro_avancado=True,
            facetavel=True,
            opcoes=[
                {"valor": "ATAS", "rotulo": "Atas"},
                {"valor": "CORRESPONDENCIA", "rotulo": "Correspondência"},
                {"valor": "PROCESSOS", "rotulo": "Processos"},
                {"valor": "RELATORIOS", "rotulo": "Relatórios"},
            ],
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-INVENTARIO-FUNDO-ADM",
            nome="Número de folhas",
            chave="numero_folhas",
            tipo=TipoCampoInstrumento.NUMERO,
            ordem=1,
            placeholder="0",
            ajuda="Quantidade estimada de folhas no dossiê.",
            aparece_busca=False,
            ordenavel=True,
            validacoes={"min": 0},
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-INVENTARIO-FUNDO-ADM",
            nome="Unidade vinculada",
            chave="unidade_vinculada",
            tipo=TipoCampoInstrumento.UNIDADE_ACONDICIONAMENTO,
            ordem=2,
            obrigatorio=True,
            aparece_listagem=False,
            ajuda="Associe a unidade de acondicionamento que guarda o item.",
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-INVENTARIO-FUNDO-ADM",
            nome="Observações internas",
            chave="observacoes_internas",
            tipo=TipoCampoInstrumento.TEXTO_LONGO,
            ordem=3,
            aparece_listagem=False,
            aparece_busca=False,
            filtro_avancado=False,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-CATALOGO-FOTOGRAFICO",
            nome="Imagem principal",
            chave="imagem_principal",
            tipo=TipoCampoInstrumento.IMAGEM,
            ordem=0,
            ajuda="Arquivo de imagem usado como miniatura do registro.",
            aparece_busca=False,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-CATALOGO-FOTOGRAFICO",
            nome="Autor da fotografia",
            chave="autor_fotografia",
            tipo=TipoCampoInstrumento.VOCABULARIO,
            ordem=1,
            placeholder="Nome normalizado do fotógrafo",
            filtro_avancado=True,
            facetavel=True,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-CATALOGO-FOTOGRAFICO",
            nome="Data da captura",
            chave="data_captura",
            tipo=TipoCampoInstrumento.DATA,
            ordem=2,
            filtro_avancado=True,
            ordenavel=True,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-CATALOGO-FOTOGRAFICO",
            nome="Palavras-chave",
            chave="palavras_chave",
            tipo=TipoCampoInstrumento.LISTA_MULTIPLA,
            ordem=3,
            multiplo=True,
            facetavel=True,
            opcoes=[
                {"valor": "EDIFICIOS", "rotulo": "Edifícios"},
                {"valor": "EVENTOS", "rotulo": "Eventos"},
                {"valor": "RETRATOS", "rotulo": "Retratos"},
                {"valor": "PAISAGENS", "rotulo": "Paisagens"},
            ],
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-INDICE-NOMINAL",
            nome="Nome citado",
            chave="nome_citado",
            tipo=TipoCampoInstrumento.TEXTO_CURTO,
            ordem=0,
            obrigatorio=True,
            placeholder="Sobrenome, Nome",
            filtro_avancado=True,
            ordenavel=True,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-INDICE-NOMINAL",
            nome="Variações do nome",
            chave="variacoes_nome",
            tipo=TipoCampoInstrumento.LISTA_MULTIPLA,
            ordem=1,
            multiplo=True,
            aparece_listagem=False,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-INDICE-NOMINAL",
            nome="Registro descritivo relacionado",
            chave="registro_relacionado",
            tipo=TipoCampoInstrumento.REGISTRO_DESCRITIVO,
            ordem=2,
            obrigatorio=True,
            aparece_busca=False,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-BASE-MIGRACAO",
            nome="País de origem",
            chave="pais_origem",
            tipo=TipoCampoInstrumento.VOCABULARIO,
            ordem=0,
            obrigatorio=True,
            filtro_avancado=True,
            facetavel=True,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-BASE-MIGRACAO",
            nome="Ano de chegada",
            chave="ano_chegada",
            tipo=TipoCampoInstrumento.NUMERO,
            ordem=1,
            filtro_avancado=True,
            ordenavel=True,
            validacoes={"min": 1800, "max": 2100},
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-BASE-MIGRACAO",
            nome="Link externo",
            chave="link_externo",
            tipo=TipoCampoInstrumento.URL,
            ordem=2,
            placeholder="https://",
            aparece_listagem=False,
            validacoes={"format": "url"},
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-EXPOSICAO-MEMORIA",
            nome="Legenda curatorial",
            chave="legenda_curatorial",
            tipo=TipoCampoInstrumento.TEXTO_LONGO,
            ordem=0,
            obrigatorio=True,
            ajuda="Texto curto exibido na exposição.",
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-EXPOSICAO-MEMORIA",
            nome="Ordem expositiva",
            chave="ordem_expositiva",
            tipo=TipoCampoInstrumento.NUMERO,
            ordem=1,
            ordenavel=True,
            validacoes={"min": 1},
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-EXPOSICAO-MEMORIA",
            nome="Arquivo de apoio",
            chave="arquivo_apoio",
            tipo=TipoCampoInstrumento.ARQUIVO,
            ordem=2,
            aparece_busca=False,
            aparece_listagem=False,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-OUTRO-COLECAO-ORAL",
            nome="Entrevistado",
            chave="entrevistado",
            tipo=TipoCampoInstrumento.TEXTO_CURTO,
            ordem=0,
            obrigatorio=True,
            filtro_avancado=True,
            ordenavel=True,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-OUTRO-COLECAO-ORAL",
            nome="Termo de autorização",
            chave="termo_autorizacao",
            tipo=TipoCampoInstrumento.ARQUIVO,
            ordem=1,
            obrigatorio=True,
            aparece_listagem=False,
            aparece_busca=False,
        ),
        InstrumentoCampoSeed(
            instrumento_codigo="TEST-INST-OUTRO-COLECAO-ORAL",
            nome="Duração calculada",
            chave="duracao_calculada",
            tipo=TipoCampoInstrumento.CAMPO_CALCULADO,
            ordem=2,
            ajuda="Campo calculado a partir dos metadados técnicos da mídia.",
            aparece_cadastro=False,
            validacoes={"formula": "fim - inicio"},
        ),
    ]


def ensure_instrumentos(db: Session) -> None:
    for seed in build_instrumento_seed_data():
        upsert_instrumento(db, seed)


def upsert_campo(db: Session, seed: InstrumentoCampoSeed) -> bool:
    existing_id = db.execute(
        text(
            """
            SELECT id
            FROM instrumento_campos
            WHERE id = :id
            """
        ),
        {"id": seed.id},
    ).scalar_one_or_none()
    created = existing_id is None

    db.execute(
        text(
            """
            INSERT INTO instrumento_campos (
                id,
                instrumento_id,
                nome,
                chave,
                tipo,
                ordem,
                obrigatorio,
                multiplo,
                valor_padrao,
                placeholder,
                ajuda,
                aparece_cadastro,
                aparece_listagem,
                aparece_busca,
                filtro_avancado,
                facetavel,
                ordenavel,
                opcoes,
                validacoes
            )
            VALUES (
                :id,
                :instrumento_id,
                :nome,
                :chave,
                :tipo,
                :ordem,
                :obrigatorio,
                :multiplo,
                :valor_padrao,
                :placeholder,
                :ajuda,
                :aparece_cadastro,
                :aparece_listagem,
                :aparece_busca,
                :filtro_avancado,
                :facetavel,
                :ordenavel,
                CAST(:opcoes AS jsonb),
                CAST(:validacoes AS jsonb)
            )
            ON CONFLICT (instrumento_id, chave)
            DO UPDATE SET
                nome = EXCLUDED.nome,
                tipo = EXCLUDED.tipo,
                ordem = EXCLUDED.ordem,
                obrigatorio = EXCLUDED.obrigatorio,
                multiplo = EXCLUDED.multiplo,
                valor_padrao = EXCLUDED.valor_padrao,
                placeholder = EXCLUDED.placeholder,
                ajuda = EXCLUDED.ajuda,
                aparece_cadastro = EXCLUDED.aparece_cadastro,
                aparece_listagem = EXCLUDED.aparece_listagem,
                aparece_busca = EXCLUDED.aparece_busca,
                filtro_avancado = EXCLUDED.filtro_avancado,
                facetavel = EXCLUDED.facetavel,
                ordenavel = EXCLUDED.ordenavel,
                opcoes = EXCLUDED.opcoes,
                validacoes = EXCLUDED.validacoes,
                atualizado_em = now()
            """
        ),
        {
            "id": seed.id,
            "instrumento_id": seed.instrumento_id,
            "nome": seed.nome,
            "chave": seed.chave,
            "tipo": seed.tipo.value,
            "ordem": seed.ordem,
            "obrigatorio": seed.obrigatorio,
            "multiplo": seed.multiplo,
            "valor_padrao": seed.valor_padrao,
            "placeholder": seed.placeholder,
            "ajuda": seed.ajuda,
            "aparece_cadastro": seed.aparece_cadastro,
            "aparece_listagem": seed.aparece_listagem,
            "aparece_busca": seed.aparece_busca,
            "filtro_avancado": seed.filtro_avancado,
            "facetavel": seed.facetavel,
            "ordenavel": seed.ordenavel,
            "opcoes": json_dump(seed.opcoes),
            "validacoes": json_dump(seed.validacoes),
        },
    )

    return created


def json_dump(value: dict[str, Any] | list[Any] | None) -> str | None:
    if value is None:
        return None

    import json

    return json.dumps(value, ensure_ascii=False)


def count_seeded_campos(db: Session, seeds: list[InstrumentoCampoSeed]) -> int:
    ids = [str(seed.id) for seed in seeds]
    return int(
        db.execute(
            text(
                """
                SELECT count(*)
                FROM instrumento_campos
                WHERE id = ANY(:ids)
                """
            ),
            {"ids": ids},
        ).scalar_one()
    )


def seed_instrumento_campos() -> tuple[int, int, int]:
    seeds = build_seed_data()
    created = 0
    updated = 0

    with SessionLocal() as db:
        ensure_instrumentos(db)

        for seed in seeds:
            if upsert_campo(db, seed):
                created += 1
            else:
                updated += 1

        total = count_seeded_campos(db, seeds)
        if total != len(seeds):
            raise RuntimeError(
                "Contagem inesperada apos seed de campos dos instrumentos: "
                f"{total} de {len(seeds)} registros encontrados."
            )

        db.commit()

    return created, updated, total


if __name__ == "__main__":
    created_count, updated_count, total_count = seed_instrumento_campos()
    print(
        "Massa de teste de campos dos instrumentos concluida: "
        f"{created_count} criados, {updated_count} atualizados, "
        f"{total_count} registros no total."
    )
