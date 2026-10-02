from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection

from app.core.config import settings

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_url)
    return _client


def registros_collection() -> Collection:
    return get_mongo_client()[settings.mongodb_database]["instrumento_registros"]


def ensure_mongo_indexes() -> None:
    collection = registros_collection()
    collection.create_index(
        [("instrumento_id", ASCENDING), ("status", ASCENDING), ("criado_em", DESCENDING), ("_id", DESCENDING)],
        name="idx_registros_instrumento_status_criado",
    )
    collection.create_index(
        [("instrumento_id", ASCENDING), ("atualizado_em", DESCENDING), ("_id", DESCENDING)],
        name="idx_registros_instrumento_atualizado",
    )
    collection.create_index([("texto_busca_basico", "text")], name="idx_registros_texto_busca")
