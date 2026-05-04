from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection

from app.core.config import settings

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    return _client


def get_instrumento_registros_collection() -> Collection:
    client = get_mongo_client()
    database = client.get_default_database()
    collection = database["instrumento_registros"]
    ensure_instrumento_registros_indexes(collection)
    return collection


def ensure_instrumento_registros_indexes(collection: Collection) -> None:
    collection.create_index([("instrumento_id", ASCENDING)])
    collection.create_index([("instrumento_id", ASCENDING), ("status", ASCENDING)])
    collection.create_index([("instrumento_id", ASCENDING), ("criado_em", DESCENDING)])
    collection.create_index([("instrumento_id", ASCENDING), ("status", ASCENDING), ("criado_em", DESCENDING), ("_id", DESCENDING)])
    collection.create_index([("unidade_acondicionamento_ids", ASCENDING)])
    collection.create_index([("registro_descritivo_ids", ASCENDING)])
