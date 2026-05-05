from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.enums import TipoMidiaArmazenamento
from app.models.midia_armazenamento import MidiaArmazenamento

MIDIAS_TOTAL = 72


def seed_midias_armazenamento() -> tuple[int, int, int]:
    tipos = list(TipoMidiaArmazenamento)
    created = 0
    updated = 0

    with SessionLocal() as db:
        for index in range(1, MIDIAS_TOTAL + 1):
            tipo = tipos[(index - 1) % len(tipos)]
            nome = f"MIDIA-TESTE-{tipo.value}-{index:03d}"
            midia = db.scalar(
                select(MidiaArmazenamento).where(MidiaArmazenamento.nome == nome)
            )
            payload = {
                "nome": nome,
                "tipo": tipo,
                "descricao": (
                    f"Massa de teste para pesquisa de midias de armazenamento "
                    f"{tipo.value} lote {((index - 1) // len(tipos)) + 1}."
                ),
                "ativo": index % 9 != 0,
            }
            if midia:
                for campo, valor in payload.items():
                    setattr(midia, campo, valor)
                updated += 1
            else:
                db.add(MidiaArmazenamento(**payload))
                created += 1

        db.commit()

    return created, updated, MIDIAS_TOTAL


if __name__ == "__main__":
    created_count, updated_count, total_count = seed_midias_armazenamento()
    print(
        "Massa de teste de midias de armazenamento concluida: "
        f"{created_count} criadas, {updated_count} atualizadas, "
        f"{total_count} registros processados."
    )
