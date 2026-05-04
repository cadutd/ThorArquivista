from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import (
    StatusInstrumentoPesquisa,
    TipoInstrumentoPesquisa,
    VisibilidadeInstrumentoPesquisa,
)

SEED_NAMESPACE = uuid.UUID("f4fc7d66-6b6b-4d9a-9d4c-f76adfe9b0a0")


@dataclass(frozen=True)
class InstrumentoPesquisaSeed:
    codigo: str
    nome: str
    tipo: TipoInstrumentoPesquisa
    descricao: str
    status: StatusInstrumentoPesquisa
    visibilidade: VisibilidadeInstrumentoPesquisa
    responsavel: str

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(SEED_NAMESPACE, self.codigo)


def build_seed_data() -> list[InstrumentoPesquisaSeed]:
    return [
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-GUIA-ACERVO-GERAL",
            nome="Guia do Acervo Institucional",
            tipo=TipoInstrumentoPesquisa.GUIA,
            descricao="Guia de teste para consulta geral aos fundos e coleções institucionais.",
            status=StatusInstrumentoPesquisa.PUBLICADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.PUBLICO,
            responsavel="Equipe de Referência",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-INVENTARIO-FUNDO-ADM",
            nome="Inventário do Fundo Administração Central",
            tipo=TipoInstrumentoPesquisa.INVENTARIO,
            descricao="Inventário de teste com séries administrativas, dossiês e unidades documentais.",
            status=StatusInstrumentoPesquisa.PUBLICADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.INTERNO,
            responsavel="Arquivo Permanente",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-CATALOGO-FOTOGRAFICO",
            nome="Catálogo Fotográfico Histórico",
            tipo=TipoInstrumentoPesquisa.CATALOGO,
            descricao="Catálogo de teste para fotografias digitalizadas, negativos e ampliações.",
            status=StatusInstrumentoPesquisa.RASCUNHO,
            visibilidade=VisibilidadeInstrumentoPesquisa.RESTRITO,
            responsavel="Núcleo Iconográfico",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-INDICE-NOMINAL",
            nome="Índice Nominal de Correspondências",
            tipo=TipoInstrumentoPesquisa.INDICE,
            descricao="Índice de teste para nomes de pessoas citadas em correspondências.",
            status=StatusInstrumentoPesquisa.PUBLICADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.INTERNO,
            responsavel="Equipe de Descrição",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-BASE-MIGRACAO",
            nome="Base Temática Migrações",
            tipo=TipoInstrumentoPesquisa.BASE_TEMATICA,
            descricao="Base temática de teste reunindo documentos relacionados a fluxos migratórios.",
            status=StatusInstrumentoPesquisa.RASCUNHO,
            visibilidade=VisibilidadeInstrumentoPesquisa.INTERNO,
            responsavel="Pesquisa Histórica",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-EXPOSICAO-MEMORIA",
            nome="Exposição Memória Institucional",
            tipo=TipoInstrumentoPesquisa.EXPOSICAO,
            descricao="Instrumento de teste para seleção curatorial de itens de exposição.",
            status=StatusInstrumentoPesquisa.PUBLICADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.PUBLICO,
            responsavel="Ação Cultural",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-OUTRO-COLECAO-ORAL",
            nome="Roteiro de Consulta de História Oral",
            tipo=TipoInstrumentoPesquisa.OUTRO,
            descricao="Instrumento de teste para entrevistas, transcrições e termos de autorização.",
            status=StatusInstrumentoPesquisa.ARQUIVADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.RESTRITO,
            responsavel="Programa de História Oral",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-GUIA-ACESSO-DIGITAL",
            nome="Guia de Acesso ao Acervo Digital",
            tipo=TipoInstrumentoPesquisa.GUIA,
            descricao="Guia de teste para orientar consulta a pacotes digitais e cópias de acesso.",
            status=StatusInstrumentoPesquisa.RASCUNHO,
            visibilidade=VisibilidadeInstrumentoPesquisa.INTERNO,
            responsavel="Preservação Digital",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-INVENTARIO-AUDIOVISUAL",
            nome="Inventário Audiovisual",
            tipo=TipoInstrumentoPesquisa.INVENTARIO,
            descricao="Inventário de teste para fitas, matrizes digitais e cópias de preservação.",
            status=StatusInstrumentoPesquisa.PUBLICADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.RESTRITO,
            responsavel="Núcleo Audiovisual",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-CATALOGO-MAPAS",
            nome="Catálogo de Mapas e Plantas",
            tipo=TipoInstrumentoPesquisa.CATALOGO,
            descricao="Catálogo de teste para documentos cartográficos e plantas arquitetônicas.",
            status=StatusInstrumentoPesquisa.ARQUIVADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.INTERNO,
            responsavel="Mapoteca",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-INDICE-ASSUNTOS",
            nome="Índice de Assuntos",
            tipo=TipoInstrumentoPesquisa.INDICE,
            descricao="Índice de teste para termos controlados, assuntos e descritores.",
            status=StatusInstrumentoPesquisa.PUBLICADO,
            visibilidade=VisibilidadeInstrumentoPesquisa.PUBLICO,
            responsavel="Controle de Vocabulário",
        ),
        InstrumentoPesquisaSeed(
            codigo="TEST-INST-BASE-DIREITOS-HUMANOS",
            nome="Base Temática Direitos Humanos",
            tipo=TipoInstrumentoPesquisa.BASE_TEMATICA,
            descricao="Base temática de teste com documentos sensíveis e regras de acesso restrito.",
            status=StatusInstrumentoPesquisa.RASCUNHO,
            visibilidade=VisibilidadeInstrumentoPesquisa.RESTRITO,
            responsavel="Comissão de Acesso",
        ),
    ]


def upsert_instrumento(db: Session, seed: InstrumentoPesquisaSeed) -> bool:
    existing_id = db.execute(
        text(
            """
            SELECT id
            FROM instrumentos_pesquisa
            WHERE id = :id
            """
        ),
        {"id": seed.id},
    ).scalar_one_or_none()
    created = existing_id is None

    db.execute(
        text(
            """
            INSERT INTO instrumentos_pesquisa (
                id,
                nome,
                tipo,
                descricao,
                status,
                visibilidade,
                responsavel
            )
            VALUES (
                :id,
                :nome,
                :tipo,
                :descricao,
                :status,
                :visibilidade,
                :responsavel
            )
            ON CONFLICT (id)
            DO UPDATE SET
                nome = EXCLUDED.nome,
                tipo = EXCLUDED.tipo,
                descricao = EXCLUDED.descricao,
                status = EXCLUDED.status,
                visibilidade = EXCLUDED.visibilidade,
                responsavel = EXCLUDED.responsavel,
                atualizado_em = now()
            """
        ),
        {
            "id": seed.id,
            "nome": seed.nome,
            "tipo": seed.tipo.value,
            "descricao": seed.descricao,
            "status": seed.status.value,
            "visibilidade": seed.visibilidade.value,
            "responsavel": seed.responsavel,
        },
    )

    return created


def count_seeded_instrumentos(db: Session, seeds: list[InstrumentoPesquisaSeed]) -> int:
    ids = [str(seed.id) for seed in seeds]
    return int(
        db.execute(
            text(
                """
                SELECT count(*)
                FROM instrumentos_pesquisa
                WHERE id = ANY(:ids)
                """
            ),
            {"ids": ids},
        ).scalar_one()
    )


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

        total = count_seeded_instrumentos(db, seeds)
        if total != len(seeds):
            raise RuntimeError(
                "Contagem inesperada apos seed de instrumentos de pesquisa: "
                f"{total} de {len(seeds)} registros encontrados."
            )

        db.commit()

    return created, updated, total


if __name__ == "__main__":
    created_count, updated_count, total_count = seed_instrumentos_pesquisa()
    print(
        "Massa de teste de instrumentos de pesquisa concluida: "
        f"{created_count} criados, {updated_count} atualizados, "
        f"{total_count} registros no total."
    )
