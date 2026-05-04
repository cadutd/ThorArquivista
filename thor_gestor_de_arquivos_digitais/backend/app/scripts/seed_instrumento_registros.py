from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.db.mongo import get_instrumento_registros_collection
from app.db.session import SessionLocal
from app.models.enums import TipoCampoInstrumento
from app.models.instrumento_pesquisa import InstrumentoCampo, InstrumentoPesquisa

SEED_NAMESPACE = uuid.UUID("f0e4b5af-2c26-4fb7-923e-743693e3a96e")
REGISTROS_POR_INSTRUMENTO = 35


def seed_instrumento_registros() -> tuple[int, int, int]:
    collection = get_instrumento_registros_collection()
    created = 0
    updated = 0
    total = 0

    with SessionLocal() as db:
        instrumentos = (
            db.query(InstrumentoPesquisa)
            .order_by(InstrumentoPesquisa.nome.asc())
            .all()
        )

        for instrumento in instrumentos:
            campos = get_campos(db, instrumento.id)
            if not campos:
                continue

            for index in range(1, REGISTROS_POR_INSTRUMENTO + 1):
                registro_id = str(uuid.uuid5(SEED_NAMESPACE, f"{instrumento.id}:{index:03d}"))
                documento = build_documento(instrumento, campos, index, registro_id)
                result = collection.update_one(
                    {"_id": registro_id},
                    {"$set": documento},
                    upsert=True,
                )
                if result.upserted_id:
                    created += 1
                else:
                    updated += 1
                total += 1

    return created, updated, total


def get_campos(db: Session, instrumento_id: uuid.UUID) -> list[InstrumentoCampo]:
    return (
        db.query(InstrumentoCampo)
        .filter(InstrumentoCampo.instrumento_id == instrumento_id)
        .order_by(InstrumentoCampo.ordem.asc(), InstrumentoCampo.nome.asc())
        .all()
    )


def build_documento(
    instrumento: InstrumentoPesquisa,
    campos: list[InstrumentoCampo],
    index: int,
    registro_id: str,
) -> dict[str, Any]:
    created_at = datetime.now(UTC) - timedelta(
        days=index,
        minutes=stable_offset(str(instrumento.id)),
    )
    return {
        "_id": registro_id,
        "instrumento_id": str(instrumento.id),
        "schema_version": 1,
        "dados": {
            campo.chave: value_for_campo(instrumento, campo, index)
            for campo in campos
            if campo.aparece_cadastro or campo.aparece_listagem or campo.aparece_busca
        },
        "unidade_acondicionamento_ids": [],
        "registro_descritivo_ids": [],
        "status": "INATIVO" if index % 11 == 0 else "ATIVO",
        "criado_em": created_at,
        "atualizado_em": created_at + timedelta(hours=2),
    }


def value_for_campo(
    instrumento: InstrumentoPesquisa,
    campo: InstrumentoCampo,
    index: int,
) -> Any:
    tipo = campo.tipo
    opcoes = normalized_options(campo.opcoes)
    base = f"{instrumento.nome} {index:03d}"

    if tipo in {TipoCampoInstrumento.TEXTO_CURTO, TipoCampoInstrumento.VOCABULARIO}:
        return text_value(campo.chave, base, index)
    if tipo == TipoCampoInstrumento.TEXTO_LONGO:
        return f"Resumo de teste {index:03d} para {instrumento.nome}."
    if tipo == TipoCampoInstrumento.NUMERO:
        return 100 + index
    if tipo == TipoCampoInstrumento.DATA:
        return (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index)).date().isoformat()
    if tipo == TipoCampoInstrumento.PERIODO:
        return f"{2000 + (index % 20)}-{2001 + (index % 20)}"
    if tipo == TipoCampoInstrumento.BOOLEANO:
        return index % 2 == 0
    if tipo == TipoCampoInstrumento.LISTA_SIMPLES:
        return opcoes[(index - 1) % len(opcoes)] if opcoes else f"OPCAO_{index % 3}"
    if tipo == TipoCampoInstrumento.LISTA_MULTIPLA:
        return opcoes[:2] if len(opcoes) >= 2 else opcoes or ["A", "B"]
    if tipo == TipoCampoInstrumento.URL:
        return f"https://example.org/thor/{instrumento.id}/{campo.chave}/{index:03d}"
    if tipo == TipoCampoInstrumento.UNIDADE_ACONDICIONAMENTO:
        return f"TEST-FIS-{((index - 1) % 25) + 1:03d}"
    if tipo == TipoCampoInstrumento.REGISTRO_DESCRITIVO:
        return f"RD-TEST-{index:03d}"
    if tipo == TipoCampoInstrumento.ARQUIVO:
        return f"arquivo_teste_{index:03d}.pdf"
    if tipo == TipoCampoInstrumento.IMAGEM:
        return f"imagem_teste_{index:03d}.jpg"
    if tipo == TipoCampoInstrumento.CAMPO_CALCULADO:
        return f"calculado-{index:03d}"

    return text_value(campo.chave, base, index)


def text_value(chave: str, base: str, index: int) -> str:
    if "titulo" in chave:
        return f"Titulo dinamico {index:03d}"
    if "local" in chave:
        return f"Local de teste {((index - 1) % 5) + 1}"
    if "codigo" in chave or "identificador" in chave:
        return f"COD-{index:03d}"
    if "pais" in chave:
        return ["Brasil", "Portugal", "Italia", "Japao", "Angola"][(index - 1) % 5]
    if "entrevistado" in chave:
        return f"Entrevistado {index:03d}"
    if "termo" in chave:
        return f"Termo {index:03d}"
    if "categoria" in chave:
        return f"Categoria {((index - 1) % 4) + 1}"
    return base


def normalized_options(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    options: list[str] = []
    for item in value:
        if isinstance(item, str):
            options.append(item)
        elif isinstance(item, dict):
            option = item.get("valor") or item.get("value")
            if option:
                options.append(str(option))
    return options


def stable_offset(value: str) -> int:
    return sum(ord(char) for char in value) % 240


if __name__ == "__main__":
    created_count, updated_count, total_count = seed_instrumento_registros()
    print(
        "Massa de teste de registros dinamicos concluida: "
        f"{created_count} criados, {updated_count} atualizados, "
        f"{total_count} registros processados."
    )
