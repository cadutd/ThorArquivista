import logging
import time
from app.core.config import settings
from app.db.session import SessionLocal
from app.services import auditoria_service
from app.services.importacao_async_worker import limpar_expirado, processar_pendente


def main():
    while True:
        try:
            with SessionLocal() as db:
                if limpar_expirado(db) or processar_pendente(db):
                    continue
        except Exception:
            logging.getLogger("thor.jobs").warning('{"evento":"import_worker_indisponivel"}')
        time.sleep(settings.jobs_poll_segundos)


if __name__ == "__main__":
    main()
