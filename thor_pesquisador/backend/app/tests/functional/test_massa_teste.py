from __future__ import annotations

from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.scripts.seed_instrumento_campos import build_seed_data as build_campos
from app.scripts.seed_instrumento_campos import seed_instrumento_campos
from app.scripts.seed_instrumento_registros import build_seed_data as build_registros
from app.scripts.seed_instrumento_registros import seed_instrumento_registros
from app.scripts.seed_instrumentos_pesquisa import build_seed_data as build_instrumentos
from app.scripts.seed_instrumentos_pesquisa import seed_instrumentos_pesquisa


def test_massa_de_instrumentos_campos_e_registros_e_idempotente():
    instrumentos_first = seed_instrumentos_pesquisa()
    campos_first = seed_instrumento_campos()
    registros_first = seed_instrumento_registros()

    instrumentos_second = seed_instrumentos_pesquisa()
    campos_second = seed_instrumento_campos()
    registros_second = seed_instrumento_registros()

    assert instrumentos_first[2] == len(build_instrumentos())
    assert campos_first[2] == len(build_campos())
    assert registros_first[2] == len(build_registros())
    assert instrumentos_second[0] == 0
    assert campos_second[0] == 0
    assert registros_second[0] == 0

    with SessionLocal() as db:
        assert db.query(Instrumento).count() >= len(build_instrumentos())
        assert db.query(InstrumentoCampo).count() >= len(build_campos())

    ids = [seed.id for seed in build_registros()]
    assert registros_collection().count_documents({"_id": {"$in": ids}}) == len(ids)
