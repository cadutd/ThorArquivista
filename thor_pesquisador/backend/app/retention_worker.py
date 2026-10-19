"""Run bounded retention work once (CronJob); never create destructive policies implicitly."""
import argparse
import json
import logging
import time
from app.db.session import SessionLocal, engine
from sqlalchemy import text
from app.services import auditoria_service
from app.services.retencao_service import expirar_exportacoes, limpar_artefatos, processar_pendente


def rodada(max_lotes=100):
    # Dedicated connection: session commits must not return a session lock to the pool.
    with engine.connect() as lock:
        if not lock.scalar(text("SELECT pg_try_advisory_lock(5832184)")):
            return
        try:
            with SessionLocal() as db:
                expirar_exportacoes(db)
                limpar_artefatos(db)
                from app.services.portal_service import limpar_acessos
                limpar_acessos(db)
                for _ in range(max_lotes):
                    if not processar_pendente(db):
                        break
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(5832184)"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-lotes", type=int, default=100)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--intervalo-segundos", type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.max_lotes <= 10000 or not 1 <= args.intervalo_segundos <= 3600:
        parser.error("Limites: max-lotes 1..10000 e intervalo-segundos 1..3600")
    while True:
        try:
            rodada(args.max_lotes)
        except Exception as exc:
            logging.getLogger("thor.jobs").warning(json.dumps({"evento": "RETENCAO_INDISPONIVEL",
                                                             "erro_tipo": type(exc).__name__}))
            if not args.loop:
                raise SystemExit(1) from None
        if not args.loop:
            return
        time.sleep(args.intervalo_segundos)


if __name__ == "__main__":
    main()
