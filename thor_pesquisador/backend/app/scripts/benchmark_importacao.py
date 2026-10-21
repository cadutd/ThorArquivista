"""Synthetic end-to-end volume rehearsal in disposable PostgreSQL/Mongo databases."""
import argparse
import json
import os
import resource
import tempfile
import time
import uuid
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.mongo import get_mongo_client, registros_collection
from app.models.editorial import AcessoInstrumento
from app.models.instrumento import Instrumento
from app.models.user import Usuario
from app.schemas.instrumento import InstrumentoCreate
from app.schemas.instrumento_campo import InstrumentoCampoCreate
from app.schemas.importacao import ConfiguracaoImportacao
from app.services import auditoria_service, instrumento_service
from app.services import importacao_async_service as service, importacao_async_worker as worker
from app.services.armazenamento_service import armazenamento


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quantidades", nargs="+", type=int, default=[200000, 500000])
    args = parser.parse_args()
    assert settings.app_env == "test" and make_url(settings.database_url).database.endswith("_test"), "Use somente compose de testes."
    assert settings.mongodb_database.endswith("_test")
    assert all(1 <= value <= 1000000 for value in args.quantidades)
    original_url, original_mongo = settings.database_url, settings.mongodb_database
    name = "thor_import_volume_" + uuid.uuid4().hex + "_test"
    assert name.startswith("thor_import_volume_") and name.endswith("_test")
    url = make_url(original_url)
    control = create_engine(url, isolation_level="AUTOCOMMIT")
    engine = None
    prefixes = []
    with control.connect() as conn:
        conn.execute(text('CREATE DATABASE "' + name + '"'))
    try:
        settings.database_url = url.set(database=name).render_as_string(hide_password=False)
        settings.mongodb_database = name
        command.upgrade(Config("alembic.ini"), "head")
        engine = create_engine(settings.database_url)
        factory = sessionmaker(engine, expire_on_commit=False)
        # Indexing is derived and deliberately outside the measured canonical import.
        worker.enqueue_indexacao = lambda *args, **kwargs: None
        with factory() as db:
            user = Usuario(nome="Benchmark sintetico")
            db.add(user); db.flush()
            db.add(AcessoInstrumento(usuario_id=user.id, papel="ADMIN"))
            db.commit()
            uid = user.id
        reports = []
        for quantity in args.quantidades:
            with factory() as db, tempfile.NamedTemporaryFile(mode="w+b", suffix=".csv") as source:
                db.info["usuario"] = db.get(Usuario, uid)
                instrument = instrumento_service.criar_instrumento(db, InstrumentoCreate(nome="Volume sintetico " + str(quantity), tipo="CATALOGO"), uid)
                iid = instrument.id
                instrumento_service.criar_campo(db, iid, InstrumentoCampoCreate(nome="Nome", chave="nome", tipo="TEXTO_CURTO", obrigatorio=True))
                source.write(b"Nome\n")
                for number in range(quantity):
                    source.write(("Pessoa sintetica " + str(number) + "\n").encode())
                source.flush()
                size = source.tell()
                source.seek(0)
                started = time.monotonic()
                jid = uuid.uuid4()
                service.criar(db, iid, jid, "sintetico.csv", size)
                prefixes.append("importacoes-assincronas/" + str(jid) + "/")
                number = 1
                while data := source.read(settings.importacao_chunk_bytes):
                    service.parte(db, iid, jid, number, data)
                    number += 1
                service.finalizar(db, iid, jid)
                upload_end = time.monotonic()
                assert worker.processar_pendente(db, job_id=jid)
                from app.models.importacao_async import ImportacaoAsync as Job
                job = db.get(Job, jid)
                assert job.status == "AGUARDANDO_MAPA", job.erro
                analyzed = time.monotonic()
                config = ConfiguracaoImportacao(operacao_id=jid, schema_version=job.schema_version,
                    mapeamentos=[{"origem":"Nome", "destino":"nome"}])
                service.validar(db, iid, jid, config)
                assert worker.processar_pendente(db, job_id=jid)
                assert db.get(Job, jid).status == "AGUARDANDO_CONFIRMACAO"
                validated = time.monotonic()
                service.confirmar(db, iid, jid)
                assert worker.processar_pendente(db, job_id=jid)
                job = db.get(Job, jid)
                assert job.status == "CONCLUIDA", job.erro
                assert job.processados == quantity
                assert registros_collection().count_documents({"_importacao_id": str(jid)}) == quantity
                finished = time.monotonic()
                reports.append({"registros":quantity, "bytes":size, "upload_s":round(upload_end-started,2),
                    "analise_s":round(analyzed-upload_end,2), "validacao_s":round(validated-analyzed,2),
                    "importacao_s":round(finished-validated,2), "total_s":round(finished-started,2),
                    "rss_pico_mib":round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2),
                    "registros_por_segundo":round(quantity/(finished-validated),2)})
                print(json.dumps(reports[-1]), flush=True)
        print(json.dumps({"resultado":"APROVADO", "banco_isolado":name, "ensaios":reports}), flush=True)
    finally:
        for prefix in prefixes:
            armazenamento.limpar_prefixo(prefix)
        if engine:
            engine.dispose()
        assert name.startswith("thor_import_volume_") and name != original_mongo
        get_mongo_client().drop_database(name)
        settings.database_url, settings.mongodb_database = original_url, original_mongo
        with control.connect() as conn:
            conn.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))
        control.dispose()


if __name__ == "__main__":
    main()
