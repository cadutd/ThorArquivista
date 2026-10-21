import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy import event, func, select, update

from app.core.observability import request_id_context
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.models.conformidade import AuditoriaGeral
from app.models.editorial import EditorialRegistro
from app.models.instrumento import IndexacaoJob, Instrumento, InstrumentoCampo
from app.models.user import Usuario
from app.services import importacao_bulk, registro_service
from app.tests.functional.test_editorial import ctx  # noqa: F401


@pytest.fixture
def lote_ctx(ctx):
    client, iid, _ = ctx
    uid = uuid.UUID(client.get('/api/v1/auth/me').json()['id'])
    with SessionLocal() as db:
        instrumento = db.get(Instrumento, uuid.UUID(iid))
        job = SimpleNamespace(id=uuid.uuid4(), instrumento_id=instrumento.id,
                              usuario_id=uid, schema_version=instrumento.schema_version)
        db.execute(update(InstrumentoCampo.__table__).where(
            InstrumentoCampo.instrumento_id == instrumento.id, InstrumentoCampo.chave == 'segredo')
            .values(aparece_busca=False))
        db.commit()
    return client, job


def _preparar(db, job):
    db.info['usuario'] = db.get(Usuario, job.usuario_id)
    return db.scalar(select(Instrumento).where(Instrumento.id == job.instrumento_id)
                     .with_for_update().execution_options(populate_existing=True))


def _registros(quantidade=3, inicio=1):
    return [{'linha': linha, 'dados': {'titulo': f'Titulo {linha}', 'segredo': 'reservado'}}
            for linha in range(inicio, inicio + quantidade)]


def _ids(job, registros):
    return [str(uuid.uuid5(job.id, str(r['linha'] - 1))) for r in registros]


def _controles(db, job):
    return list(db.scalars(select(EditorialRegistro).where(
        EditorialRegistro.instrumento_id == job.instrumento_id).order_by(EditorialRegistro.registro_id)))


def _eventos(db, job):
    return list(db.scalars(select(AuditoriaGeral).where(
        AuditoriaGeral.operacao_id == job.id, AuditoriaGeral.acao == 'CRIAR_REGISTRO_CONCLUIDO')
        .order_by(AuditoriaGeral.registro_id)))


def _estado(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


@pytest.mark.parametrize('quantidade', [1, 1000])
def test_lote_bulk_consultas_constantes_sem_commit(lote_ctx, monkeypatch, quantidade):
    _, job = lote_ctx
    registros = _registros(quantidade, inicio=11)
    ids = _ids(job, registros)
    collection = registros_collection()
    proxy = SimpleNamespace(find=Mock(wraps=collection.find), bulk_write=Mock(wraps=collection.bulk_write))
    monkeypatch.setattr(importacao_bulk, 'registros_collection', lambda: proxy)
    monkeypatch.setattr(registro_service, 'enqueue_registro', Mock(side_effect=AssertionError('enqueue individual')))
    request_id = str(uuid.uuid4())
    token = request_id_context.set(request_id)
    statements = []

    def contar(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    try:
        with SessionLocal() as db:
            before = _preparar(db, job).revisao_dados
            indexacoes = db.scalar(select(func.count()).select_from(IndexacaoJob).where(
                IndexacaoJob.instrumento_id == job.instrumento_id))
            engine = db.get_bind()
            event.listen(engine, 'before_cursor_execute', contar)
            try:
                with monkeypatch.context() as patch:
                    patch.setattr(db, 'commit', Mock(side_effect=AssertionError('commit do helper')))
                    assert importacao_bulk.gravar_lote(db, job, registros) == quantidade
            finally:
                event.remove(engine, 'before_cursor_execute', contar)
            assert len(statements) == 6, statements
            with SessionLocal() as other:
                assert not _eventos(other, job)
                assert not any(row.registro_id in ids for row in _controles(other, job))
            db.commit()
            db.expire_all()
            assert db.get(Instrumento, job.instrumento_id).revisao_dados == before + 1
            rows = [r for r in _controles(db, job) if r.registro_id in ids]
            assert len(rows) == quantidade
            assert all(r.versao == 1 and r.status_operacional == 'ATIVO' and r.status_editorial == 'RASCUNHO'
                       for r in rows)
            eventos = _eventos(db, job)
            assert len(eventos) == quantidade
            assert {a.registro_id for a in eventos} == set(ids)
            actor = db.get(Usuario, job.usuario_id)
            assert all(a.usuario_id == actor.id and a.agente == actor.nome and a.request_id == request_id
                       and a.entidade == 'registro' and a.entidade_id == a.registro_id
                       and a.instrumento_id == job.instrumento_id and a.detalhe == {'etapa': 'CONCLUIDA'}
                       for a in eventos)
            assert db.scalar(select(func.count()).select_from(IndexacaoJob).where(
                IndexacaoJob.instrumento_id == job.instrumento_id)) == indexacoes
    finally:
        request_id_context.reset(token)
    assert proxy.find.call_count == proxy.bulk_write.call_count == 1
    projection = proxy.find.call_args.args[1]
    assert 'dados' not in projection and projection['_revision'] == projection['status'] == 1
    operations = proxy.bulk_write.call_args.args[0]
    assert len(operations) == quantidade
    assert all(set(op._doc) == {'$setOnInsert'} and op._upsert for op in operations)
    docs = {doc['_id']: doc for doc in collection.find({'_id': {'$in': ids}})}
    for registro, rid in zip(registros, ids):
        doc = docs[rid]
        assert doc['_importacao_id'] == str(job.id) and doc['_importacao_linha'] == registro['linha']
        assert doc['instrumento_id'] == str(job.instrumento_id) and doc['schema_version'] == job.schema_version
        assert doc['_revision'] == 1 and doc['status'] == 'ATIVO' and doc['dados'] == registro['dados']
        assert doc['criado_por'] == doc['atualizado_por'] == str(job.usuario_id)
        assert doc['criado_em'] == doc['atualizado_em']
        assert doc['texto_busca_basico'] == registro['dados']['titulo']


@pytest.mark.parametrize('status', ['INATIVO', 'EXCLUIDO'])
def test_retry_preserva_edicoes_status_e_auditoria(lote_ctx, status):
    client, job = lote_ctx
    registros = _registros(2)
    ids = _ids(job, registros)
    with SessionLocal() as db:
        _preparar(db, job)
        importacao_bulk.gravar_lote(db, job, registros)
        db.commit()
    path = f'/api/v1/instrumentos/{job.instrumento_id}/registros/{ids[0]}'
    assert client.put(path, json={'dados': {'titulo': 'Edicao do usuario'}, 'status': 'INATIVO'}).status_code == 200
    if status == 'EXCLUIDO':
        assert client.delete(path).status_code == 200
    collection = registros_collection()
    docs = list(collection.find({'_id': {'$in': ids}}).sort('_id'))
    with SessionLocal() as db:
        before = _preparar(db, job).revisao_dados
        controles = [_estado(r) for r in _controles(db, job)]
        eventos = [_estado(r) for r in _eventos(db, job)]
        assert importacao_bulk.gravar_lote(db, job, registros) == 2
        db.commit()
        db.expire_all()
        assert db.get(Instrumento, job.instrumento_id).revisao_dados == before + 1
        assert [_estado(r) for r in _controles(db, job)] == controles
        assert [_estado(r) for r in _eventos(db, job)] == eventos
        assert len(eventos) == 2
    assert list(collection.find({'_id': {'$in': ids}}).sort('_id')) == docs
    assert collection.find_one({'_id': ids[0]})['status'] == status


@pytest.mark.parametrize('tabela', ['editorial_registros', 'auditoria_geral'])
def test_mongo_gravado_sql_falha_replay_recupera_controles(lote_ctx, tabela):
    _, job = lote_ctx
    registros = _registros()
    ids = _ids(job, registros)
    collection = registros_collection()

    def falhar(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.startswith('INSERT INTO ' + tabela):
            raise RuntimeError('Falha SQL depois do Mongo')

    with SessionLocal() as db:
        before = _preparar(db, job).revisao_dados
        engine = db.get_bind()
        event.listen(engine, 'before_cursor_execute', falhar)
        try:
            with pytest.raises(RuntimeError, match='Falha SQL'):
                importacao_bulk.gravar_lote(db, job, registros)
        finally:
            event.remove(engine, 'before_cursor_execute', falhar)
        db.rollback()
        assert collection.count_documents({'_id': {'$in': ids}}) == 3
        assert not _eventos(db, job)
        assert not any(r.registro_id in ids for r in _controles(db, job))
        assert db.get(Instrumento, job.instrumento_id).revisao_dados == before
        collection.update_one({'_id': ids[0]}, {'$set': {
            'dados': {'titulo': 'Orfao editado'}, '_revision': 7, 'status': 'INATIVO',
            'texto_busca_basico': 'Orfao editado'}})
        documentos = list(collection.find({'_id': {'$in': ids}}).sort('_id'))
        _preparar(db, job)
        assert importacao_bulk.gravar_lote(db, job, registros) == 3
        db.commit()
        rows = {r.registro_id: r for r in _controles(db, job)}
        assert rows[ids[0]].versao == 7 and rows[ids[0]].status_operacional == 'INATIVO'
        assert len(_eventos(db, job)) == 3
        db.expire_all()
        assert db.get(Instrumento, job.instrumento_id).revisao_dados == before + 1
    assert list(collection.find({'_id': {'$in': ids}}).sort('_id')) == documentos


def test_bulk_mongo_parcial_replay(lote_ctx, monkeypatch):
    _, job = lote_ctx
    registros = _registros()
    ids = _ids(job, registros)
    collection = registros_collection()

    def parcial(operations, **kwargs):
        collection.bulk_write(operations[:1], **kwargs)
        raise RuntimeError('Mongo parcial')

    with SessionLocal() as db:
        _preparar(db, job)
        with monkeypatch.context() as patch:
            patch.setattr(importacao_bulk, 'registros_collection', lambda: SimpleNamespace(
                find=collection.find, bulk_write=parcial))
            with pytest.raises(RuntimeError, match='Mongo parcial'):
                importacao_bulk.gravar_lote(db, job, registros)
        db.rollback()
        assert collection.count_documents({'_id': {'$in': ids}}) == 1
        assert not _eventos(db, job)
        _preparar(db, job)
        assert importacao_bulk.gravar_lote(db, job, registros) == 3
        db.commit()
        assert len(_eventos(db, job)) == 3
        assert sum(r.registro_id in ids for r in _controles(db, job)) == 3
    assert collection.count_documents({'_id': {'$in': ids}}) == 3


def test_controle_criado_por_api_apos_orfao_recebe_primeira_auditoria(lote_ctx):
    client, job = lote_ctx
    registros = _registros(1)
    rid = _ids(job, registros)[0]
    with SessionLocal() as db:
        _preparar(db, job)
        importacao_bulk.gravar_lote(db, job, registros)
        db.rollback()
    path = f'/api/v1/instrumentos/{job.instrumento_id}/registros/{rid}'
    assert client.put(path, json={'dados': {'titulo': 'Editado antes do replay'}, 'status': 'INATIVO'}).status_code == 200
    doc = registros_collection().find_one({'_id': rid})
    with SessionLocal() as db:
        _preparar(db, job)
        row = next(r for r in _controles(db, job) if r.registro_id == rid)
        estado = _estado(row)
        assert not _eventos(db, job)
        for _ in range(2):
            importacao_bulk.gravar_lote(db, job, registros)
            db.commit()
            _preparar(db, job)
        db.refresh(row)
        assert _estado(row) == estado
        assert len(_eventos(db, job)) == 1
    assert registros_collection().find_one({'_id': rid}) == doc


@pytest.mark.parametrize('colisao', ['sem_marcador', 'job', 'linha', 'instrumento'])
def test_colisao_rejeitada_antes_de_qualquer_escrita(lote_ctx, colisao):
    _, job = lote_ctx
    registros = _registros(2)
    ids = _ids(job, registros)
    doc = {'_id': ids[1], '_importacao_id': str(job.id), '_importacao_linha': 2,
           'instrumento_id': str(job.instrumento_id), 'status': 'ATIVO', '_revision': 9}
    if colisao == 'sem_marcador':
        del doc['_importacao_id']
    elif colisao == 'job':
        doc['_importacao_id'] = str(uuid.uuid4())
    elif colisao == 'linha':
        doc['_importacao_linha'] = 3
    else:
        doc['instrumento_id'] = str(uuid.uuid4())
    collection = registros_collection()
    collection.insert_one(doc)
    with SessionLocal() as db:
        before = _preparar(db, job).revisao_dados
        with pytest.raises(HTTPException) as exc:
            importacao_bulk.gravar_lote(db, job, registros)
        assert exc.value.status_code == 409
        db.rollback()
        assert not _eventos(db, job)
        assert not any(r.registro_id in ids for r in _controles(db, job))
        assert db.get(Instrumento, job.instrumento_id).revisao_dados == before
    assert collection.find_one({'_id': ids[0]}) is None
    assert collection.find_one({'_id': ids[1]}) == doc


def test_registro_expurgado_nao_e_recriado(lote_ctx):
    _, job = lote_ctx
    registros = _registros(1)
    rid = _ids(job, registros)[0]
    with SessionLocal() as db:
        _preparar(db, job)
        importacao_bulk.gravar_lote(db, job, registros)
        db.commit()
    collection = registros_collection()
    collection.delete_one({'_id': rid})
    # Include a new row first to prove the guard rejects the entire batch.
    registros = _registros(1, inicio=2) + registros
    with SessionLocal() as db:
        before = _preparar(db, job).revisao_dados
        with pytest.raises(HTTPException) as exc:
            importacao_bulk.gravar_lote(db, job, registros)
        assert exc.value.status_code == 409
        db.rollback()
        assert len(_eventos(db, job)) == 1
        assert db.get(Instrumento, job.instrumento_id).revisao_dados == before
    assert collection.count_documents({'_id': {'$in': _ids(job, registros)}}) == 0


def test_validacao_corrente_antes_de_escrever_lote(lote_ctx):
    _, job = lote_ctx
    registros = _registros(2)
    registros[-1]['dados']['titulo'] = 123
    with SessionLocal() as db:
        _preparar(db, job)
        with pytest.raises(HTTPException) as exc:
            importacao_bulk.gravar_lote(db, job, registros)
        assert exc.value.status_code == 422
        db.rollback()
        assert not _eventos(db, job)
    assert registros_collection().count_documents({'_id': {'$in': _ids(job, registros)}}) == 0


def test_lote_vazio_nao_acessa_bancos():
    assert importacao_bulk.gravar_lote(None, None, []) == 0


@pytest.mark.parametrize('linhas', [[1, 1], [0], [-1], [True], ['1'], list(range(1, 1002))])
def test_limites_e_linhas_invalidas_sem_acesso_a_bancos(linhas):
    with pytest.raises(HTTPException) as exc:
        importacao_bulk.gravar_lote(None, None, [{'linha': linha, 'dados': {}} for linha in linhas])
    assert exc.value.status_code == 422
