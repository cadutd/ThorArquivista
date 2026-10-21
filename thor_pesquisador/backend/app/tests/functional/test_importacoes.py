import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.core.config import settings
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.main import create_app
from app.models.editorial import AcessoInstrumento, Papel
from app.models.importacao import ImportacaoRegistros
from app.models.user import Usuario
from app.services import importacao_service, registro_service
from app.services.auth_service import create_session
from app.tests.functional.test_editorial import ctx


def config(client, iid, mappings=None):
    return {"operacao_id": str(uuid.uuid4()), "schema_version": client.get("/api/v1/instrumentos/" + iid).json()["schema_version"],
            "mapeamentos": mappings or [{"origem": "Nome", "destino": "titulo"}]}


def send(client, iid, action, content, cfg=None, filename="a.csv"):
    return client.post("/api/v1/instrumentos/" + iid + "/registros/importacoes" + ("/" + action if action else ""),
        files={"arquivo": (filename, content, "text/csv" if filename.endswith(".csv") else "application/json")},
        data={"configuracao": json.dumps(cfg)} if cfg else {})


def count(iid):
    return registros_collection().count_documents({"instrumento_id": iid})


def test_importar_csv_preview_idempotencia_e_historico(ctx):
    client, iid, _ = ctx
    content = "Nome;Ignorada\nAna;PRIVADO\nMaria;OUTRO".encode()
    cfg = config(client, iid)
    before = count(iid)
    analyzed = send(client, iid, "analisar", content)
    assert analyzed.status_code == 200, analyzed.text
    assert analyzed.json()["total"] == 2
    preview = send(client, iid, "validar", content, cfg)
    assert preview.json()["validos"] == 2 and preview.json()["invalidos"] == 0
    assert count(iid) == before
    created = send(client, iid, "", content, cfg)
    assert created.status_code == 200, created.text
    assert created.json()["status"] == "CONCLUIDA" and created.json()["processados"] == 2
    assert count(iid) == before + 2
    docs = list(registros_collection().find({"instrumento_id": iid, "_id": {"$ne": ctx[2]}}))
    assert all(set(doc["dados"]) == {"titulo"} for doc in docs)
    for doc in docs:
        out = client.get("/api/v1/instrumentos/" + iid + "/registros/" + doc["_id"]).json()
        assert out["status_editorial"] == "RASCUNHO"
    assert send(client, iid, "", content, cfg).json()["processados"] == 2
    assert count(iid) == before + 2
    assert send(client, iid, "", b"Nome\nOutro", cfg).status_code == 409
    history = client.get("/api/v1/instrumentos/" + iid + "/registros/importacoes").json()
    assert history[0]["id"] == cfg["operacao_id"]
    assert client.delete("/api/v1/instrumentos/" + iid).status_code == 409


def test_criar_campos_json_sem_publicar(ctx):
    client, iid, _ = ctx
    content = b'[{"Nome":"Ana","Idade":0,"Ativo":false,"Chegada":"31/12/1900"}]'
    cfg = config(client, iid, [
        {"origem": "Nome", "destino": "titulo"},
        {"origem": "Idade", "novo": {"nome": "Idade", "chave": "idade", "tipo": "NUMERO"}},
        {"origem": "Ativo", "novo": {"nome": "Ativo", "chave": "ativo", "tipo": "BOOLEANO"}},
        {"origem": "Chegada", "novo": {"nome": "Chegada", "chave": "chegada", "tipo": "DATA"}},
    ])
    preview = send(client, iid, "validar", content, cfg, "a.json")
    assert preview.status_code == 200, preview.text
    assert preview.json()["previa"][0]["dados"] == {"titulo": "Ana", "idade": 0, "ativo": False, "chegada": "1900-12-31"}
    before_schema = client.get("/api/v1/instrumentos/" + iid + "/schema").json()
    assert "idade" not in {f["chave"] for f in before_schema["campos"]}
    response = send(client, iid, "", content, cfg, "a.json")
    assert response.json()["status"] == "CONCLUIDA", response.text
    schema = client.get("/api/v1/instrumentos/" + iid + "/schema").json()
    assert schema["schema_version"] == before_schema["schema_version"] + 1
    assert all(not field["exibir_publico"] for field in schema["campos"] if field["chave"] in {"idade", "ativo", "chegada"})
    assert send(client, iid, "", content, cfg, "a.json").json()["status"] == "CONCLUIDA"
    assert count(iid) == 2


def test_dados_invalidos_nao_criam_campos_nem_linhas(ctx):
    client, iid, _ = ctx
    cfg = config(client, iid, [{"origem": "Nome", "novo": {"nome": "Numero", "chave": "numero", "tipo": "NUMERO", "obrigatorio": True}}])
    content = b"Nome\n12\ninvalido"
    preview = send(client, iid, "validar", content, cfg).json()
    assert preview["invalidos"] == 1 and preview["erros"][0]["linha"] == 2
    response = send(client, iid, "", content, cfg)
    assert response.status_code == 422 and count(iid) == 1
    assert not any(f["chave"] == "numero" for f in client.get("/api/v1/instrumentos/" + iid + "/schema").json()["campos"])
    with SessionLocal() as db:
        assert db.get(ImportacaoRegistros, uuid.UUID(cfg["operacao_id"])) is None


@pytest.mark.parametrize("mappings", [
    [{"origem": "Inexistente", "destino": "titulo"}],
    [{"origem": "Nome", "destino": "inexistente"}],
    [{"origem": "Nome", "destino": "titulo"}, {"origem": "Outro", "destino": "titulo"}],
    [{"origem": "Nome", "destino": "titulo", "novo": {"nome": "X", "chave": "x", "tipo": "NUMERO"}}],
    [],
])
def test_mapeamentos_invalidos(ctx, mappings):
    client, iid, _ = ctx
    cfg = config(client, iid)
    cfg["mapeamentos"] = mappings
    assert send(client, iid, "", b"Nome,Outro\nAna,A", cfg).status_code == 422
    assert count(iid) == 1


def test_schema_alterado_obrigatorios_e_colisao(ctx):
    client, iid, _ = ctx
    cfg = config(client, iid)
    created = client.post("/api/v1/instrumentos/" + iid + "/campos",
                         json={"nome": "Codigo", "chave": "codigo", "tipo": "TEXTO_CURTO", "obrigatorio": True})
    assert created.status_code == 201
    assert send(client, iid, "", b"Nome\nAna", cfg).status_code == 409
    cfg["schema_version"] += 1
    assert send(client, iid, "validar", b"Nome\nAna", cfg).json()["invalidos"] == 1
    cfg["mapeamentos"] = [{"origem": "Nome", "novo": {"nome": "Titulo", "chave": "titulo", "tipo": "TEXTO_CURTO"}}]
    assert send(client, iid, "", b"Nome\nAna", cfg).status_code == 409


def test_retomada_de_falha_apos_mongo_sem_duplicar(ctx, monkeypatch):
    client, iid, _ = ctx
    cfg = config(client, iid, [{"origem": "Nome", "novo": {"nome": "Importado", "chave": "importado", "tipo": "TEXTO_CURTO"}}])
    content = b"Nome\nAna\nMaria"
    original = registro_service.criar_registro
    calls = []
    def failed(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(result.id)
        raise RuntimeError("Falha simulada apos persistir Mongo/SQL")
    monkeypatch.setattr(registro_service, "criar_registro", failed)
    result = send(client, iid, "", content, cfg).json()
    assert result["status"] == "INTERROMPIDA" and count(iid) == 2
    # Preserve an edit made after the interrupted attempt.
    registros_collection().update_one({"_id": calls[0]}, {"$set": {"dados.importado": "Edicao posterior"}})
    monkeypatch.setattr(registro_service, "criar_registro", original)
    resumed = send(client, iid, "", content, cfg)
    assert resumed.json()["status"] == "CONCLUIDA" and resumed.json()["processados"] == 2, resumed.text
    assert count(iid) == 3
    assert registros_collection().find_one({"_id": calls[0]})["dados"]["importado"] == "Edicao posterior"


def test_retomada_nao_recria_registro_expurgado(ctx, monkeypatch):
    client, iid, _ = ctx
    cfg = config(client, iid)
    content = b"Nome\nAna"
    original = registro_service.criar_registro
    def failed(*args, **kwargs):
        result = original(*args, **kwargs)
        registros_collection().delete_one({"_id": result.id})
        raise RuntimeError("Remocao simulada apos a persistencia")
    monkeypatch.setattr(registro_service, "criar_registro", failed)
    assert send(client, iid, "", content, cfg).json()["status"] == "INTERROMPIDA"
    monkeypatch.setattr(registro_service, "criar_registro", original)
    assert send(client, iid, "", content, cfg).json()["status"] == "INTERROMPIDA"
    assert count(iid) == 1


def user_client(iid, permissions):
    with SessionLocal() as db:
        user = Usuario(nome="Importador " + uuid.uuid4().hex)
        role = Papel(nome="IMP_" + uuid.uuid4().hex, permissoes=permissions)
        db.add_all([user, role]); db.flush()
        grant = AcessoInstrumento(usuario_id=user.id, papel=role.nome, instrumento_id=uuid.UUID(iid))
        db.add(grant); db.commit()
        token, grant_id = create_session(db, user), grant.id
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    return client, grant_id


def test_permissoes_escopo_propriedade_e_revogacao(ctx):
    admin, iid, _ = ctx
    cfg = config(admin, iid)
    anonymous = TestClient(create_app())
    assert send(anonymous, iid, "analisar", b"Nome\nAna").status_code == 401
    denied, _ = user_client(iid, ["instrumentos_consultar"])
    assert send(denied, iid, "analisar", b"Nome\nAna").status_code == 403
    client, gid = user_client(iid, ["instrumentos_consultar", "registros_incluir"])
    new_config = config(admin, iid, [{"origem": "Nome", "novo": {"nome": "Novo", "chave": "novo", "tipo": "TEXTO_CURTO"}}])
    assert send(client, iid, "", b"Nome\nAna", new_config).status_code == 403
    assert send(client, str(uuid.uuid4()), "analisar", b"Nome\nAna").status_code == 403
    assert send(client, iid, "", b"Nome\nAna", cfg).json()["status"] == "CONCLUIDA"
    assert send(admin, iid, "", b"Nome\nAna", cfg).status_code == 409
    assert admin.get("/api/v1/instrumentos/" + iid + "/registros/importacoes").json() == []
    with SessionLocal() as db:
        db.delete(db.get(AcessoInstrumento, gid)); db.commit()
    assert send(client, iid, "", b"Nome\nAna", cfg).status_code == 403


def test_bloqueio_concorrente(ctx):
    client, iid, _ = ctx
    import hashlib
    lock = int.from_bytes(hashlib.sha256(("importacao:" + iid).encode()).digest()[:8], "big", signed=True)
    with SessionLocal().get_bind().connect() as guard:
        guard.execute(select(func.pg_advisory_lock(lock))); guard.commit()
        try:
            assert send(client, iid, "", b"Nome\nAna", config(client, iid)).status_code == 409
        finally:
            guard.execute(select(func.pg_advisory_unlock(lock))); guard.commit()
