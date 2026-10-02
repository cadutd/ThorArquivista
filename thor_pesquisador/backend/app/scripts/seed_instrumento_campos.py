from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import TipoCampo
from app.models.instrumento import InstrumentoCampo
from app.scripts.seed_instrumentos_pesquisa import (
    SEED_NAMESPACE as INSTRUMENTO_NAMESPACE,
    build_seed_data as build_instrumento_seed_data,
    upsert_instrumento,
)

CAMPO_NAMESPACE = uuid.UUID("e948f7a7-c770-41ee-88bf-1d4c04ef3a65")


@dataclass(frozen=True)
class InstrumentoCampoSeed:
    instrumento_codigo: str
    nome: str
    chave: str
    tipo: TipoCampo
    ordem: int
    obrigatorio: bool = False
    multiplo: bool = False
    opcoes: dict[str, Any] | list[Any] | None = None
    validacoes: dict[str, Any] | list[Any] | None = None
    aparece_cadastro: bool = True
    aparece_listagem: bool = True
    aparece_busca: bool = True

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(CAMPO_NAMESPACE, f"{self.instrumento_codigo}:{self.chave}")

    @property
    def instrumento_id(self) -> uuid.UUID:
        return uuid.uuid5(INSTRUMENTO_NAMESPACE, self.instrumento_codigo)


def build_seed_data() -> list[InstrumentoCampoSeed]:
    return [
        InstrumentoCampoSeed("TEST-PESQ-GUIA-ACERVO-GERAL", "Codigo de referencia", "codigo_referencia", TipoCampo.TEXTO_CURTO, 0, True),
        InstrumentoCampoSeed("TEST-PESQ-GUIA-ACERVO-GERAL", "Titulo", "titulo", TipoCampo.TEXTO_CURTO, 1, True),
        InstrumentoCampoSeed("TEST-PESQ-GUIA-ACERVO-GERAL", "Resumo", "resumo", TipoCampo.TEXTO_LONGO, 2, aparece_listagem=False),
        InstrumentoCampoSeed("TEST-PESQ-GUIA-ACERVO-GERAL", "Disponivel ao publico", "disponivel_publico", TipoCampo.BOOLEANO, 3),
        InstrumentoCampoSeed(
            "TEST-PESQ-INVENTARIO-FUNDO-ADM",
            "Serie documental",
            "serie_documental",
            TipoCampo.LISTA_SIMPLES,
            0,
            True,
            opcoes=["ATAS", "CORRESPONDENCIA", "PROCESSOS", "RELATORIOS"],
        ),
        InstrumentoCampoSeed("TEST-PESQ-INVENTARIO-FUNDO-ADM", "Numero de folhas", "numero_folhas", TipoCampo.NUMERO, 1, aparece_busca=False),
        InstrumentoCampoSeed("TEST-PESQ-INVENTARIO-FUNDO-ADM", "Data limite", "data_limite", TipoCampo.DATA, 2),
        InstrumentoCampoSeed("TEST-PESQ-INVENTARIO-FUNDO-ADM", "Observacoes internas", "observacoes_internas", TipoCampo.TEXTO_LONGO, 3, aparece_listagem=False, aparece_busca=False),
        InstrumentoCampoSeed("TEST-PESQ-CATALOGO-FOTOGRAFICO", "Autor da fotografia", "autor_fotografia", TipoCampo.TEXTO_CURTO, 0, True),
        InstrumentoCampoSeed("TEST-PESQ-CATALOGO-FOTOGRAFICO", "Data da captura", "data_captura", TipoCampo.DATA, 1),
        InstrumentoCampoSeed(
            "TEST-PESQ-CATALOGO-FOTOGRAFICO",
            "Palavras-chave",
            "palavras_chave",
            TipoCampo.LISTA_MULTIPLA,
            2,
            multiplo=True,
            opcoes=["EDIFICIOS", "EVENTOS", "RETRATOS", "PAISAGENS"],
        ),
        InstrumentoCampoSeed("TEST-PESQ-INDICE-NOMINAL", "Nome citado", "nome_citado", TipoCampo.TEXTO_CURTO, 0, True),
        InstrumentoCampoSeed("TEST-PESQ-INDICE-NOMINAL", "Variacoes do nome", "variacoes_nome", TipoCampo.LISTA_MULTIPLA, 1, multiplo=True),
        InstrumentoCampoSeed("TEST-PESQ-INDICE-NOMINAL", "URL do documento", "url_documento", TipoCampo.URL, 2, aparece_listagem=False),
        InstrumentoCampoSeed("TEST-PESQ-BASE-MIGRACAO", "Pais de origem", "pais_origem", TipoCampo.TEXTO_CURTO, 0, True),
        InstrumentoCampoSeed("TEST-PESQ-BASE-MIGRACAO", "Ano de chegada", "ano_chegada", TipoCampo.NUMERO, 1),
        InstrumentoCampoSeed("TEST-PESQ-BASE-MIGRACAO", "Fonte externa", "fonte_externa", TipoCampo.URL, 2, aparece_listagem=False),
        InstrumentoCampoSeed("TEST-PESQ-INDICE-ASSUNTOS", "Termo principal", "termo_principal", TipoCampo.TEXTO_CURTO, 0, True),
        InstrumentoCampoSeed("TEST-PESQ-INDICE-ASSUNTOS", "Categoria", "categoria", TipoCampo.LISTA_SIMPLES, 1, opcoes=["PESSOA", "LOCAL", "ASSUNTO"]),
        InstrumentoCampoSeed("TEST-PESQ-INDICE-ASSUNTOS", "Nota de escopo", "nota_escopo", TipoCampo.TEXTO_LONGO, 2, aparece_listagem=False),
    ]


def ensure_instrumentos(db: Session) -> None:
    for seed in build_instrumento_seed_data():
        upsert_instrumento(db, seed)


def upsert_campo(db: Session, seed: InstrumentoCampoSeed) -> bool:
    campo = db.scalar(
        select(InstrumentoCampo).where(
            InstrumentoCampo.instrumento_id == seed.instrumento_id,
            InstrumentoCampo.chave == seed.chave,
        )
    )
    created = campo is None
    if campo is None:
        campo = InstrumentoCampo(id=seed.id, instrumento_id=seed.instrumento_id)
        db.add(campo)

    campo.nome = seed.nome
    campo.chave = seed.chave
    campo.tipo = seed.tipo.value
    campo.ordem = seed.ordem
    campo.obrigatorio = seed.obrigatorio
    campo.multiplo = seed.multiplo
    campo.opcoes = seed.opcoes
    campo.validacoes = seed.validacoes
    campo.aparece_cadastro = seed.aparece_cadastro
    campo.aparece_listagem = seed.aparece_listagem
    campo.aparece_busca = seed.aparece_busca
    return created


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
        db.commit()

        total = sum(1 for seed in seeds if db.get(InstrumentoCampo, seed.id) is not None)
        if total != len(seeds):
            raise RuntimeError(
                "Contagem inesperada apos seed de campos dos instrumentos: "
                f"{total} de {len(seeds)} registros encontrados."
            )

    return created, updated, total


if __name__ == "__main__":
    created_count, updated_count, total_count = seed_instrumento_campos()
    print(
        "Massa de teste de campos dos instrumentos concluida: "
        f"{created_count} criados, {updated_count} atualizados, "
        f"{total_count} registros no total."
    )
