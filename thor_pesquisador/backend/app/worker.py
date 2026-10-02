from __future__ import annotations

import logging

from app.services.indexacao_service import run_worker_once

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("thor_pesquisador.index_worker")


def main() -> None:
    logger.info("Index worker iniciado.")
    while True:
        try:
            processed = run_worker_once(timeout=5)
            if processed:
                logger.info("Mensagem de indexacao processada.")
        except Exception:
            logger.exception("Falha ao processar mensagem de indexacao.")


if __name__ == "__main__":
    main()
