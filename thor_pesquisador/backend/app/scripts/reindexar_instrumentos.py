from __future__ import annotations

import argparse
import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.enums import StatusInstrumento
from app.models.instrumento import Instrumento
from app.services.indexacao_service import criar_job_reindexacao


def main() -> None:
    parser = argparse.ArgumentParser(description="Enfileira reindexacao de instrumentos no Meilisearch.")
    parser.add_argument("--instrumento-id", help="UUID de um instrumento especifico.")
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.instrumento_id:
            ids = [uuid.UUID(args.instrumento_id)]
        else:
            ids = list(
                db.scalars(
                    select(Instrumento.id)
                    .where(Instrumento.status == StatusInstrumento.PUBLICADO.value)
                    .order_by(Instrumento.nome.asc())
                )
            )

        for instrumento_id in ids:
            job = criar_job_reindexacao(db, instrumento_id)
            print(f"Reindexacao enfileirada: instrumento={instrumento_id} job={job.id} total_estimado={job.total_estimado}")


if __name__ == "__main__":
    main()
