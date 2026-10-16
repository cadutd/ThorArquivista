"""Dedicated SQL queue: independent of Redis and the indexing worker."""
import logging
import time
from app.core.config import settings
from app.db.session import SessionLocal
from app.services import auditoria_service
from app.services.exportacao_service import processar_pendente


def main():
    while True:
        try:
            with SessionLocal() as db:
                if processar_pendente(db):
                    continue
        except Exception:
            logging.getLogger(__name__).warning('{"evento":"export_worker_indisponivel"}')
        time.sleep(settings.jobs_poll_segundos)


if __name__ == "__main__":
    main()
