from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


LOCAL_CODE = "TEST-DEP-01"
ZONES = [
    ("ZT01", "Zona de Teste 01"),
    ("ZT02", "Zona de Teste 02"),
]
SHELVES_PER_ZONE = 20
COMPARTMENTS_PER_SHELF = 5
POSITIONS_PER_COMPARTMENT = 10


@dataclass(frozen=True)
class SeedSummary:
    local_id: int
    zones: int
    structures: int
    compartments: int
    positions: int


def upsert_local(db: Session) -> int:
    return int(
        db.execute(
            text(
                """
                INSERT INTO locais_guarda (
                    codigo,
                    nome,
                    tipo_local,
                    descricao,
                    logradouro,
                    numero,
                    bairro,
                    municipio,
                    uf,
                    cep,
                    pais,
                    observacoes,
                    ativo
                )
                VALUES (
                    :codigo,
                    :nome,
                    CAST(:tipo_local AS tipo_local_guarda),
                    :descricao,
                    :logradouro,
                    :numero,
                    :bairro,
                    :municipio,
                    :uf,
                    :cep,
                    :pais,
                    :observacoes,
                    true
                )
                ON CONFLICT (codigo)
                DO UPDATE SET
                    nome = EXCLUDED.nome,
                    tipo_local = EXCLUDED.tipo_local,
                    descricao = EXCLUDED.descricao,
                    logradouro = EXCLUDED.logradouro,
                    numero = EXCLUDED.numero,
                    bairro = EXCLUDED.bairro,
                    municipio = EXCLUDED.municipio,
                    uf = EXCLUDED.uf,
                    cep = EXCLUDED.cep,
                    pais = EXCLUDED.pais,
                    observacoes = EXCLUDED.observacoes,
                    ativo = true,
                    atualizado_em = now()
                RETURNING id
                """
            ),
            {
                "codigo": LOCAL_CODE,
                "nome": "Depósito de Testes",
                "tipo_local": "DEPOSITO",
                "descricao": "Local de guarda criado para testes de endereçamento.",
                "logradouro": "Rua de Testes",
                "numero": "100",
                "bairro": "Centro",
                "municipio": "São Paulo",
                "uf": "SP",
                "cep": "00000-000",
                "pais": "Brasil",
                "observacoes": "Massa idempotente de endereçamento.",
            },
        ).scalar_one()
    )


def upsert_zone(db: Session, local_id: int, code: str, name: str) -> int:
    return int(
        db.execute(
            text(
                """
                INSERT INTO zonas_guarda (
                    id_local_guarda,
                    codigo,
                    nome,
                    tipo_zona,
                    descricao,
                    quantidade_corredores,
                    quantidade_modulos_por_corredor,
                    quantidade_estantes_por_modulo,
                    quantidade_prateleiras_por_estante,
                    capacidade_caixas_por_prateleira,
                    observacoes,
                    ativo
                )
                VALUES (
                    :local_id,
                    :codigo,
                    :nome,
                    CAST(:tipo_zona AS tipo_zona_guarda),
                    :descricao,
                    1,
                    1,
                    :estantes,
                    :prateleiras,
                    :posicoes,
                    :observacoes,
                    true
                )
                ON CONFLICT (id_local_guarda, codigo)
                DO UPDATE SET
                    nome = EXCLUDED.nome,
                    tipo_zona = EXCLUDED.tipo_zona,
                    descricao = EXCLUDED.descricao,
                    quantidade_corredores = EXCLUDED.quantidade_corredores,
                    quantidade_modulos_por_corredor = EXCLUDED.quantidade_modulos_por_corredor,
                    quantidade_estantes_por_modulo = EXCLUDED.quantidade_estantes_por_modulo,
                    quantidade_prateleiras_por_estante = EXCLUDED.quantidade_prateleiras_por_estante,
                    capacidade_caixas_por_prateleira = EXCLUDED.capacidade_caixas_por_prateleira,
                    observacoes = EXCLUDED.observacoes,
                    ativo = true,
                    atualizado_em = now()
                RETURNING id
                """
            ),
            {
                "local_id": local_id,
                "codigo": code,
                "nome": name,
                "tipo_zona": "ACERVO_TEXTUAL",
                "descricao": (
                    "Zona de teste com 20 estantes, 5 prateleiras por estante "
                    "e 10 posições por prateleira."
                ),
                "estantes": SHELVES_PER_ZONE,
                "prateleiras": COMPARTMENTS_PER_SHELF,
                "posicoes": POSITIONS_PER_COMPARTMENT,
                "observacoes": "Criada pelo seed de endereçamento.",
            },
        ).scalar_one()
    )


def upsert_structure(db: Session, zone_id: int, shelf_index: int) -> int:
    code = f"E{shelf_index:02d}"
    return int(
        db.execute(
            text(
                """
                INSERT INTO estruturas_armazenamento (
                    id_zona_guarda,
                    codigo,
                    nome,
                    tipo_estrutura,
                    descricao,
                    ordem,
                    capacidade_total,
                    observacoes,
                    ativo
                )
                VALUES (
                    :zone_id,
                    :codigo,
                    :nome,
                    CAST(:tipo_estrutura AS tipo_estrutura_armazenamento),
                    :descricao,
                    :ordem,
                    :capacidade_total,
                    :observacoes,
                    true
                )
                ON CONFLICT (id_zona_guarda, codigo)
                DO UPDATE SET
                    nome = EXCLUDED.nome,
                    tipo_estrutura = EXCLUDED.tipo_estrutura,
                    descricao = EXCLUDED.descricao,
                    ordem = EXCLUDED.ordem,
                    capacidade_total = EXCLUDED.capacidade_total,
                    observacoes = EXCLUDED.observacoes,
                    ativo = true,
                    atualizado_em = now()
                RETURNING id
                """
            ),
            {
                "zone_id": zone_id,
                "codigo": code,
                "nome": f"Estante {shelf_index:02d}",
                "tipo_estrutura": "ESTANTE",
                "descricao": "Estante gerada para massa de testes.",
                "ordem": shelf_index,
                "capacidade_total": COMPARTMENTS_PER_SHELF * POSITIONS_PER_COMPARTMENT,
                "observacoes": "Criada pelo seed de endereçamento.",
            },
        ).scalar_one()
    )


def upsert_compartment(db: Session, structure_id: int, shelf_index: int) -> int:
    code = f"P{shelf_index:02d}"
    return int(
        db.execute(
            text(
                """
                INSERT INTO compartimentos_armazenamento (
                    id_estrutura_armazenamento,
                    codigo,
                    nome,
                    tipo_compartimento,
                    descricao,
                    ordem,
                    capacidade_posicoes,
                    observacoes,
                    ativo
                )
                VALUES (
                    :structure_id,
                    :codigo,
                    :nome,
                    CAST(:tipo_compartimento AS tipo_compartimento_armazenamento),
                    :descricao,
                    :ordem,
                    :capacidade_posicoes,
                    :observacoes,
                    true
                )
                ON CONFLICT (id_estrutura_armazenamento, codigo)
                DO UPDATE SET
                    nome = EXCLUDED.nome,
                    tipo_compartimento = EXCLUDED.tipo_compartimento,
                    descricao = EXCLUDED.descricao,
                    ordem = EXCLUDED.ordem,
                    capacidade_posicoes = EXCLUDED.capacidade_posicoes,
                    observacoes = EXCLUDED.observacoes,
                    ativo = true,
                    atualizado_em = now()
                RETURNING id
                """
            ),
            {
                "structure_id": structure_id,
                "codigo": code,
                "nome": f"Prateleira {shelf_index:02d}",
                "tipo_compartimento": "PRATELEIRA",
                "descricao": "Prateleira gerada para massa de testes.",
                "ordem": shelf_index,
                "capacidade_posicoes": POSITIONS_PER_COMPARTMENT,
                "observacoes": "Criada pelo seed de endereçamento.",
            },
        ).scalar_one()
    )


def upsert_position(
    db: Session,
    compartment_id: int,
    zone_code: str,
    shelf_index: int,
    compartment_index: int,
    position_index: int,
) -> int:
    code = f"CX{position_index:03d}"
    full_code = (
        f"{LOCAL_CODE}-{zone_code}-E{shelf_index:02d}-"
        f"P{compartment_index:02d}-{code}"
    )
    return int(
        db.execute(
            text(
                """
                INSERT INTO posicoes_armazenamento (
                    id_compartimento_armazenamento,
                    codigo,
                    codigo_completo,
                    tipo_posicao,
                    ordem,
                    capacidade_unidades,
                    ocupada,
                    ativo,
                    observacoes
                )
                VALUES (
                    :compartment_id,
                    :codigo,
                    :codigo_completo,
                    CAST(:tipo_posicao AS tipo_posicao_armazenamento),
                    :ordem,
                    1,
                    false,
                    true,
                    :observacoes
                )
                ON CONFLICT (id_compartimento_armazenamento, codigo)
                DO UPDATE SET
                    codigo_completo = EXCLUDED.codigo_completo,
                    tipo_posicao = EXCLUDED.tipo_posicao,
                    ordem = EXCLUDED.ordem,
                    capacidade_unidades = EXCLUDED.capacidade_unidades,
                    ativo = true,
                    observacoes = EXCLUDED.observacoes,
                    atualizado_em = now()
                RETURNING id
                """
            ),
            {
                "compartment_id": compartment_id,
                "codigo": code,
                "codigo_completo": full_code,
                "tipo_posicao": "POSICAO_CAIXA",
                "ordem": position_index,
                "observacoes": "Posição criada pelo seed de endereçamento.",
            },
        ).scalar_one()
    )


def seed_storage_addressing() -> SeedSummary:
    with SessionLocal() as db:
        local_id = upsert_local(db)
        zone_ids = [upsert_zone(db, local_id, code, name) for code, name in ZONES]

        for zone_id, (zone_code, _) in zip(zone_ids, ZONES, strict=True):
            for shelf_index in range(1, SHELVES_PER_ZONE + 1):
                structure_id = upsert_structure(db, zone_id, shelf_index)
                for compartment_index in range(1, COMPARTMENTS_PER_SHELF + 1):
                    compartment_id = upsert_compartment(
                        db,
                        structure_id,
                        compartment_index,
                    )
                    for position_index in range(1, POSITIONS_PER_COMPARTMENT + 1):
                        upsert_position(
                            db,
                            compartment_id,
                            zone_code,
                            shelf_index,
                            compartment_index,
                            position_index,
                        )

        db.commit()

        counts = db.execute(
            text(
                """
                SELECT
                    (SELECT count(*)
                       FROM zonas_guarda
                      WHERE id_local_guarda = :local_id) AS zones,
                    (SELECT count(*)
                       FROM estruturas_armazenamento ea
                       JOIN zonas_guarda zg ON zg.id = ea.id_zona_guarda
                      WHERE zg.id_local_guarda = :local_id) AS structures,
                    (SELECT count(*)
                       FROM compartimentos_armazenamento ca
                       JOIN estruturas_armazenamento ea
                         ON ea.id = ca.id_estrutura_armazenamento
                       JOIN zonas_guarda zg ON zg.id = ea.id_zona_guarda
                      WHERE zg.id_local_guarda = :local_id) AS compartments,
                    (SELECT count(*)
                       FROM posicoes_armazenamento pa
                       JOIN compartimentos_armazenamento ca
                         ON ca.id = pa.id_compartimento_armazenamento
                       JOIN estruturas_armazenamento ea
                         ON ea.id = ca.id_estrutura_armazenamento
                       JOIN zonas_guarda zg ON zg.id = ea.id_zona_guarda
                      WHERE zg.id_local_guarda = :local_id) AS positions
                """
            ),
            {"local_id": local_id},
        ).one()

    return SeedSummary(
        local_id=local_id,
        zones=int(counts.zones),
        structures=int(counts.structures),
        compartments=int(counts.compartments),
        positions=int(counts.positions),
    )


if __name__ == "__main__":
    summary = seed_storage_addressing()
    print(
        "Massa de teste de endereçamento concluida: "
        f"local #{summary.local_id}, "
        f"{summary.zones} zonas, "
        f"{summary.structures} estruturas, "
        f"{summary.compartments} compartimentos, "
        f"{summary.positions} posições."
    )
