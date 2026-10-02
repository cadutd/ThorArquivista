from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.models.enums import StatusRegistro
from app.models.instrumento import InstrumentoCampo
from app.scripts.seed_instrumento_campos import seed_instrumento_campos
from app.scripts.seed_instrumentos_pesquisa import SEED_NAMESPACE as INSTRUMENTO_NAMESPACE
from app.services.registro_service import _texto_busca

REGISTRO_NAMESPACE = uuid.UUID("0951e6f5-7a1b-421d-a13e-1b7c6c8bcae2")


@dataclass(frozen=True)
class InstrumentoRegistroSeed:
    instrumento_codigo: str
    codigo: str
    dados: dict[str, Any]
    status: StatusRegistro = StatusRegistro.ATIVO

    @property
    def id(self) -> str:
        return str(uuid.uuid5(REGISTRO_NAMESPACE, f"{self.instrumento_codigo}:{self.codigo}"))

    @property
    def instrumento_id(self) -> uuid.UUID:
        return uuid.uuid5(INSTRUMENTO_NAMESPACE, self.instrumento_codigo)


def build_seed_data() -> list[InstrumentoRegistroSeed]:
    return [
        InstrumentoRegistroSeed(
            "TEST-PESQ-GUIA-ACERVO-GERAL",
            "fundo-administracao",
            {
                "codigo_referencia": "BR THOR FND ADM",
                "titulo": "Fundo Administracao Central",
                "resumo": "Documentos produzidos pela administracao central entre 1930 e 1985.",
                "disponivel_publico": True,
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-GUIA-ACERVO-GERAL",
            "colecao-mapas",
            {
                "codigo_referencia": "BR THOR COL MAP",
                "titulo": "Colecao de Mapas e Plantas",
                "resumo": "Mapas urbanos, plantas arquitetonicas e levantamentos cartograficos.",
                "disponivel_publico": True,
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-INVENTARIO-FUNDO-ADM",
            "atas-1934",
            {
                "serie_documental": "ATAS",
                "numero_folhas": 128,
                "data_limite": "1934-12-31",
                "observacoes_internas": "Massa de teste para validacao de inventario.",
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-INVENTARIO-FUNDO-ADM",
            "relatorios-1950",
            {
                "serie_documental": "RELATORIOS",
                "numero_folhas": 82,
                "data_limite": "1950-06-30",
                "observacoes_internas": "Registro com busca restrita aos campos publicos.",
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-CATALOGO-FOTOGRAFICO",
            "evento-1972",
            {
                "autor_fotografia": "Laboratorio Fotografico Institucional",
                "data_captura": "1972-05-10",
                "palavras_chave": ["EVENTOS", "RETRATOS"],
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-INDICE-NOMINAL",
            "maria-oliveira",
            {
                "nome_citado": "Oliveira, Maria",
                "variacoes_nome": ["Maria de Oliveira", "M. Oliveira"],
                "url_documento": "https://example.org/documentos/maria-oliveira",
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-BASE-MIGRACAO",
            "italia-1908",
            {
                "pais_origem": "Italia",
                "ano_chegada": 1908,
                "fonte_externa": "https://example.org/migracoes/italia-1908",
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-INDICE-ASSUNTOS",
            "cartografia",
            {
                "termo_principal": "Cartografia",
                "categoria": "ASSUNTO",
                "nota_escopo": "Usar para documentos cartograficos, mapas e plantas.",
            },
        ),
        InstrumentoRegistroSeed(
            "TEST-PESQ-INDICE-ASSUNTOS",
            "acesso-restrito",
            {
                "termo_principal": "Acesso restrito",
                "categoria": "ASSUNTO",
                "nota_escopo": "Termo usado para registros com restricao administrativa.",
            },
            status=StatusRegistro.INATIVO,
        ),
    ]


def seed_instrumento_registros() -> tuple[int, int, int]:
    seed_instrumento_campos()
    seeds = build_seed_data()
    collection = registros_collection()
    created = 0
    updated = 0
    base_time = datetime(2026, 1, 1, tzinfo=UTC)

    with SessionLocal() as db:
        campos_por_instrumento = {
            str(seed.instrumento_id): list(
                db.scalars(
                    select(InstrumentoCampo)
                    .where(InstrumentoCampo.instrumento_id == seed.instrumento_id)
                    .order_by(InstrumentoCampo.ordem.asc())
                )
            )
            for seed in seeds
        }

    for index, seed in enumerate(seeds):
        campos = campos_por_instrumento[str(seed.instrumento_id)]
        now = base_time + timedelta(minutes=index)
        documento = {
            "_id": seed.id,
            "instrumento_id": str(seed.instrumento_id),
            "schema_version": 1,
            "dados": seed.dados,
            "status": seed.status.value,
            "criado_por": "seed_instrumento_registros",
            "atualizado_por": "seed_instrumento_registros",
            "criado_em": now,
            "atualizado_em": now,
            "texto_busca_basico": _texto_busca(campos, seed.dados),
        }
        result = collection.update_one({"_id": seed.id}, {"$set": documento}, upsert=True)
        if result.upserted_id is not None:
            created += 1
        else:
            updated += 1

    total = collection.count_documents({"_id": {"$in": [seed.id for seed in seeds]}})
    if total != len(seeds):
        raise RuntimeError(
            "Contagem inesperada apos seed de registros dos instrumentos: "
            f"{total} de {len(seeds)} registros encontrados."
        )

    return created, updated, total


if __name__ == "__main__":
    created_count, updated_count, total_count = seed_instrumento_registros()
    print(
        "Massa de teste de registros dos instrumentos concluida: "
        f"{created_count} criados, {updated_count} atualizados, "
        f"{total_count} registros no total."
    )
