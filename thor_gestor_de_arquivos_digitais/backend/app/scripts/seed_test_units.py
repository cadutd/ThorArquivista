from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import NivelAcesso, StatusUnidade, TipoSuporte, TipoUnidade


@dataclass(frozen=True)
class UnitSeed:
    identificador: str
    titulo: str
    descricao: str
    tipo_suporte: TipoSuporte
    tipo_unidade: TipoUnidade
    nivel_acesso: NivelAcesso
    status: StatusUnidade
    tamanho_bytes: int | None = None
    status_fixidez: str | None = None


PHYSICAL_UNIT_TYPES = [TipoUnidade.CAIXA, TipoUnidade.PASTA, TipoUnidade.VOLUME]
DIGITAL_UNIT_TYPES = [TipoUnidade.AIP, TipoUnidade.SIP, TipoUnidade.DIP]
ACCESS_LEVELS = [NivelAcesso.PUBLICO, NivelAcesso.RESTRITO, NivelAcesso.CONFIDENCIAL]


def build_seed_data() -> list[UnitSeed]:
    physical_units = [
        UnitSeed(
            identificador=f"TEST-FIS-{index:03d}",
            titulo=f"Unidade fisica de teste {index:02d}",
            descricao=(
                "Massa de teste para unidade de acondicionamento fisica, "
                "representando caixas, pastas e volumes de acervo institucional."
            ),
            tipo_suporte=TipoSuporte.FISICO,
            tipo_unidade=PHYSICAL_UNIT_TYPES[(index - 1) % len(PHYSICAL_UNIT_TYPES)],
            nivel_acesso=ACCESS_LEVELS[(index - 1) % len(ACCESS_LEVELS)],
            status=StatusUnidade.ATIVA,
        )
        for index in range(1, 26)
    ]

    digital_units = [
        UnitSeed(
            identificador=f"TEST-DIG-{index:03d}",
            titulo=f"Unidade digital de teste {index:02d}",
            descricao=(
                "Massa de teste para unidade de acondicionamento digital, "
                "representando pacotes SIP, AIP e DIP em repositorio digital."
            ),
            tipo_suporte=TipoSuporte.DIGITAL,
            tipo_unidade=DIGITAL_UNIT_TYPES[(index - 1) % len(DIGITAL_UNIT_TYPES)],
            nivel_acesso=ACCESS_LEVELS[(index - 1) % len(ACCESS_LEVELS)],
            status=StatusUnidade.ATIVA,
            tamanho_bytes=250_000_000 + (index * 37_500_000),
            status_fixidez="VALIDADA" if index % 5 else "PENDENTE",
        )
        for index in range(1, 26)
    ]

    return physical_units + digital_units


def upsert_unit(db: Session, seed: UnitSeed) -> bool:
    existing_id = db.execute(
        text(
            """
            SELECT id
            FROM unidades_acondicionamento
            WHERE identificador = :identificador
            """
        ),
        {"identificador": seed.identificador},
    ).scalar_one_or_none()
    created = existing_id is None

    unit_id = db.execute(
        text(
            """
            INSERT INTO unidades_acondicionamento (
                identificador,
                titulo,
                descricao,
                tipo_suporte,
                tipo_unidade,
                nivel_acesso,
                status
            )
            VALUES (
                :identificador,
                :titulo,
                :descricao,
                CAST(:tipo_suporte AS tipo_suporte),
                CAST(:tipo_unidade AS tipo_unidade),
                CAST(:nivel_acesso AS nivel_acesso),
                CAST(:status AS status_unidade)
            )
            ON CONFLICT (identificador)
            DO UPDATE SET
                titulo = EXCLUDED.titulo,
                descricao = EXCLUDED.descricao,
                tipo_suporte = EXCLUDED.tipo_suporte,
                tipo_unidade = EXCLUDED.tipo_unidade,
                nivel_acesso = EXCLUDED.nivel_acesso,
                status = EXCLUDED.status,
                atualizado_em = now()
            RETURNING id
            """
        ),
        {
            "identificador": seed.identificador,
            "titulo": seed.titulo,
            "descricao": seed.descricao,
            "tipo_suporte": seed.tipo_suporte.value,
            "tipo_unidade": seed.tipo_unidade.value,
            "nivel_acesso": seed.nivel_acesso.value,
            "status": seed.status.value,
        },
    ).scalar_one()

    if seed.tipo_suporte == TipoSuporte.DIGITAL:
        db.execute(
            text(
                """
                INSERT INTO unidades_acondicionamento_digitais (
                    id_unidade_acondicionamento,
                    tamanho_bytes,
                    status_fixidez
                )
                VALUES (
                    :unit_id,
                    :tamanho_bytes,
                    :status_fixidez
                )
                ON CONFLICT (id_unidade_acondicionamento)
                DO UPDATE SET
                    tamanho_bytes = EXCLUDED.tamanho_bytes,
                    status_fixidez = EXCLUDED.status_fixidez
                """
            ),
            {
                "unit_id": unit_id,
                "tamanho_bytes": seed.tamanho_bytes,
                "status_fixidez": seed.status_fixidez,
            },
        )

    return created


def count_seeded_units(db: Session) -> tuple[int, int, int]:
    physical = db.execute(
        text(
            """
            SELECT count(*)
            FROM unidades_acondicionamento
            WHERE identificador LIKE 'TEST-FIS-%'
              AND tipo_suporte = 'FISICO'
            """
        )
    ).scalar_one()
    digital = db.execute(
        text(
            """
            SELECT count(*)
            FROM unidades_acondicionamento
            WHERE identificador LIKE 'TEST-DIG-%'
              AND tipo_suporte = 'DIGITAL'
            """
        )
    ).scalar_one()
    digital_extensions = db.execute(
        text(
            """
            SELECT count(*)
            FROM unidades_acondicionamento ua
            JOIN unidades_acondicionamento_digitais uad
              ON uad.id_unidade_acondicionamento = ua.id
            WHERE ua.identificador LIKE 'TEST-DIG-%'
              AND ua.tipo_suporte = 'DIGITAL'
            """
        )
    ).scalar_one()

    return int(physical), int(digital), int(digital_extensions)


def seed_test_units() -> tuple[int, int, int, int, int]:
    created = 0
    updated = 0

    with SessionLocal() as db:
        for seed in build_seed_data():
            if upsert_unit(db, seed):
                created += 1
            else:
                updated += 1

        physical, digital, digital_extensions = count_seeded_units(db)
        if physical != 25 or digital != 25 or digital_extensions != 25:
            raise RuntimeError(
                "Contagem inesperada apos seed: "
                f"{physical} fisicas, {digital} digitais, "
                f"{digital_extensions} extensoes digitais."
            )

        db.commit()

    return created, updated, physical, digital, digital_extensions


if __name__ == "__main__":
    created_count, updated_count, physical_count, digital_count, extension_count = (
        seed_test_units()
    )
    print(
        "Massa de teste de unidades concluida: "
        f"{created_count} criadas, {updated_count} atualizadas, "
        f"{physical_count} fisicas, {digital_count} digitais, "
        f"{extension_count} extensoes digitais."
    )
