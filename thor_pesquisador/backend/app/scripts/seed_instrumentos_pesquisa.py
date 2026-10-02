from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import StatusInstrumento, TipoInstrumento, VisibilidadeInstrumento
from app.models.instrumento import Instrumento

SEED_NAMESPACE = uuid.UUID("86fb3ebf-b79d-4df6-9920-27e6ee4d4c49")


@dataclass(frozen=True)
class InstrumentoPesquisaSeed:
    codigo: str
    nome: str
    tipo: TipoInstrumento
    descricao: str
    status: StatusInstrumento
    visibilidade: VisibilidadeInstrumento

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(SEED_NAMESPACE, self.codigo)


def build_seed_data() -> list[InstrumentoPesquisaSeed]:
    return [
        InstrumentoPesquisaSeed(
            codigo="TEST-PESQ-GUIA-ACERVO-GERAL",
            nome="Guia do Acervo Institucional",
            tipo=TipoInstrumento.GUIA,
            descricao="Guia de teste para consulta geral aos fundos e colecoes institucionais.",
            status=StatusInstrumento.PUBLICADO,
            visibilidade=VisibilidadeInstrumento.PUBLICO,
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-PESQ-INVENTARIO-FUNDO-ADM",
            nome="Inventario do Fundo Administracao Central",
            tipo=TipoInstrumento.INVENTARIO,
            descricao="Inventario de teste com series administrativas, dossies e unidades documentais.",
            status=StatusInstrumento.PUBLICADO,
            visibilidade=VisibilidadeInstrumento.INTERNO,
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-PESQ-CATALOGO-FOTOGRAFICO",
            nome="Catalogo Fotografico Historico",
            tipo=TipoInstrumento.CATALOGO,
            descricao="Catalogo de teste para fotografias digitalizadas, negativos e ampliacoes.",
            status=StatusInstrumento.RASCUNHO,
            visibilidade=VisibilidadeInstrumento.RESTRITO,
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-PESQ-INDICE-NOMINAL",
            nome="Indice Nominal de Correspondencias",
            tipo=TipoInstrumento.INDICE,
            descricao="Indice de teste para nomes de pessoas citadas em correspondencias.",
            status=StatusInstrumento.PUBLICADO,
            visibilidade=VisibilidadeInstrumento.INTERNO,
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-PESQ-BASE-MIGRACAO",
            nome="Base Tematica Migracoes",
            tipo=TipoInstrumento.BASE_TEMATICA,
            descricao="Base tematica de teste reunindo documentos relacionados a fluxos migratorios.",
            status=StatusInstrumento.RASCUNHO,
            visibilidade=VisibilidadeInstrumento.INTERNO,
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-PESQ-INDICE-ASSUNTOS",
            nome="Indice de Assuntos",
            tipo=TipoInstrumento.INDICE,
            descricao="Indice de teste para termos controlados, assuntos e descritores.",
            status=StatusInstrumento.PUBLICADO,
            visibilidade=VisibilidadeInstrumento.PUBLICO,
        ),
    ]


def upsert_instrumento(db: Session, seed: InstrumentoPesquisaSeed) -> bool:
    instrumento = db.get(Instrumento, seed.id)
    created = instrumento is None
    if instrumento is None:
        instrumento = Instrumento(id=seed.id)
        db.add(instrumento)

    instrumento.nome = seed.nome
    instrumento.tipo = seed.tipo.value
    instrumento.descricao = seed.descricao
    instrumento.status = seed.status.value
    instrumento.visibilidade = seed.visibilidade.value
    return created


def seed_instrumentos_pesquisa() -> tuple[int, int, int]:
    seeds = build_seed_data()
    created = 0
    updated = 0

    with SessionLocal() as db:
        for seed in seeds:
            if upsert_instrumento(db, seed):
                created += 1
            else:
                updated += 1
        db.commit()

        total = sum(1 for seed in seeds if db.get(Instrumento, seed.id) is not None)
        if total != len(seeds):
            raise RuntimeError(
                "Contagem inesperada apos seed de instrumentos de pesquisa: "
                f"{total} de {len(seeds)} registros encontrados."
            )

    return created, updated, total


if __name__ == "__main__":
    created_count, updated_count, total_count = seed_instrumentos_pesquisa()
    print(
        "Massa de teste de instrumentos de pesquisa concluida: "
        f"{created_count} criados, {updated_count} atualizados, "
        f"{total_count} registros no total."
    )
