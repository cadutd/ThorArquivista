from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.midia_armazenamento import MidiaArmazenamento, TipoMidiaArmazenamento

MIDIAS_TOTAL = 72
TIPOS_INICIAIS = [
    ("FILESYSTEM", "Sistema de arquivos", 5, 6),
    ("NAS", "Network attached storage", 5, 6),
    ("NFS", "Network file system", 5, 6),
    ("LTO", "Fita LTO", 10, 12),
    ("S3", "Armazenamento S3", 10, 12),
    ("CLOUD", "Armazenamento em nuvem", 10, 12),
]


def seed_midias_armazenamento() -> tuple[int, int, int]:
    created = 0
    updated = 0

    with SessionLocal() as db:
        tipos = []
        for nome, descricao, duracao, periodicidade in TIPOS_INICIAIS:
            tipo = db.scalar(
                select(TipoMidiaArmazenamento).where(TipoMidiaArmazenamento.nome == nome)
            )
            if not tipo:
                tipo = TipoMidiaArmazenamento(
                    nome=nome,
                    descricao=descricao,
                    tempo_duracao_anos=duracao,
                    periodicidade_checagem_meses=periodicidade,
                    ativo=True,
                )
                db.add(tipo)
                db.flush()
            tipos.append(tipo)

        for index in range(1, MIDIAS_TOTAL + 1):
            tipo = tipos[(index - 1) % len(tipos)]
            nome = f"MIDIA-TESTE-{tipo.nome}-{index:03d}"
            midia = db.scalar(
                select(MidiaArmazenamento).where(MidiaArmazenamento.nome == nome)
            )
            payload = {
                "nome": nome,
                "tipo_midia_id": tipo.id,
                "descricao": (
                    f"Massa de teste para pesquisa de midias de armazenamento "
                    f"{tipo.nome} lote {((index - 1) // len(tipos)) + 1}."
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
