"""Bounded local benchmark. Never seeds or runs against operational databases."""
import json
import resource
import statistics
import time
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.core.config import settings
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.main import create_app
from app.models.instrumento import Instrumento
from app.models.portal import AcessoPortal, ContagemPortal
from app.services.portal_service import elegiveis


def main():
    if settings.app_env != "test" or not settings.database_url.rsplit("/", 1)[-1].endswith("_test") or not settings.mongodb_database.endswith("_test"):
        raise SystemExit("Benchmark permitido somente em bancos isolados de teste.")
    with SessionLocal() as db:
        size = {
            "instrumentos": db.scalar(select(func.count()).select_from(Instrumento)),
            "publicacoes_elegiveis": db.scalar(select(func.count()).select_from(elegiveis().subquery())),
            "acessos_deduplicados": db.scalar(select(func.count()).select_from(AcessoPortal)),
            "contagens_diarias": db.scalar(select(func.count()).select_from(ContagemPortal)),
            "registros_mongo": registros_collection().count_documents({}),
        }
    result = {"ambiente": "Docker isolado, TestClient, sem rede externa", "volume": size, "rotas": {}}
    with TestClient(create_app()) as client:
        for path in ("/api/v1/publico/instrumentos?limit=20", "/api/v1/publico/destaques?limit=6"):
            assert client.get(path).status_code == 200
            samples = []
            for _ in range(50):
                start = time.perf_counter()
                response = client.get(path)
                samples.append((time.perf_counter() - start) * 1000)
                assert response.status_code == 200, response.status_code
            result["rotas"][path] = {
                "amostras": len(samples), "p50_ms": round(statistics.median(samples), 2),
                "p95_ms": round(sorted(samples)[47], 2), "max_ms": round(max(samples), 2),
            }
    result["rss_max_mib"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)
    result["limite"] = "Sem carga concorrente, rede, ingress ou escala institucional; nao e teste de capacidade."
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
