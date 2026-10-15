import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.main import create_app
from app.models.editorial import AcessoInstrumento
from app.tests.functional.test_editorial import ctx
from app.tests.functional.test_usuarios import criar, payload, autenticado


def create_access(admin, user, instrument=None, role="EDITOR"):
    response = admin.post("/api/v1/acessos", json={"usuario_id":user["id"], "papel":role, "instrumento_id":instrument})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def plan(user, instrument=None, **overrides):
    return {"usuario_id":user["id"], "perfis":["EDITOR"], "escopo":"INSTRUMENTO" if instrument else "GLOBAL",
            "instrumento_ids":[instrument] if instrument else [], **overrides}


def grants(admin, user):
    return admin.get("/api/v1/acessos", params={"usuario_id":user["id"],"limit":100}).json()


def test_edicao_lote_preserva_id_e_outros_acessos(ctx):
    admin, instrument, _ = ctx
    user = criar(admin,payload())
    original = create_access(admin,user,instrument)
    unrelated = create_access(admin,user,role="PUBLICO_AUTENTICADO")
    before = admin.get("/api/v1/acessos/" + unrelated).json()
    path = "/api/v1/acessos/" + original + "/lote"
    assert admin.put(path,json=plan(user,instrument)).status_code == 200
    other = admin.post("/api/v1/instrumentos",json={"nome":"Edicao " + uuid.uuid4().hex,"tipo":"GUIA"}).json()["id"]
    response = admin.put(path,json=plan(user,instrument,perfis=["EDITOR","REVISOR"],instrumento_ids=[instrument,other]))
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 4 and response.json()["items"][0]["id"] == original
    assert grants(admin,user)["total"] == 5
    assert admin.get("/api/v1/acessos/" + unrelated).json() == before
    assert admin.get("/api/v1/acessos/" + original).json()["instrumento_id"] == instrument


def test_edicao_lote_transfere_so_a_concessao_selecionada(ctx):
    admin, instrument, _ = ctx
    first, second = criar(admin,payload()), criar(admin,payload())
    original = create_access(admin,first,instrument)
    unrelated = create_access(admin,first,role="REVISOR")
    response = admin.put("/api/v1/acessos/" + original + "/lote",json=plan(second,perfis=["CONSULTA_INTERNA"]))
    assert response.status_code == 200, response.text
    assert grants(admin,first)["items"][0]["id"] == unrelated
    assert grants(admin,second)["items"][0]["id"] == original


@pytest.mark.parametrize("case", ["conflito","perfil_invalido","instrumento_ausente","escopo_invalido","usuario_ausente"])
def test_edicao_lote_rejeita_sem_modificar_original(ctx,case):
    admin, instrument, _ = ctx
    user = criar(admin,payload())
    original = create_access(admin,user,instrument)
    create_access(admin,user,role="CONSULTA_INTERNA")
    before = grants(admin,user)
    data = plan(user,instrument)
    expected = 422
    if case == "conflito":
        data["perfis"].append("CONSULTA_INTERNA"); expected = 409
    elif case == "perfil_invalido":
        data["perfis"].append("INEXISTENTE")
    elif case == "instrumento_ausente":
        data["instrumento_ids"].append(str(uuid.uuid4())); expected = 404
    elif case == "escopo_invalido":
        data["escopo"] = "GLOBAL"
    else:
        data["usuario_id"] = str(uuid.uuid4()); expected = 404
    response = admin.put("/api/v1/acessos/" + original + "/lote",json=data)
    assert response.status_code == expected, response.text
    assert grants(admin,user) == before


def test_edicao_lote_permissoes_distintas_para_editar_e_expandir(ctx):
    admin, instrument, _ = ctx
    actor, target = criar(admin,payload()), criar(admin,payload())
    read = admin.post("/api/v1/perfis",json={"codigo":"EDIT_" + uuid.uuid4().hex.upper(),
        "nome":"Edicao limitada","permissoes":["acessos_editar","instrumentos_consultar"]}).json()
    create_access(admin,actor,role=read["codigo"])
    client = autenticado(actor["id"])
    original = create_access(admin,target,instrument,"CONSULTA_INTERNA")
    # A lean profile whose privileges can be delegated by this actor.
    lean = admin.post("/api/v1/perfis",json={"codigo":"LEAN_" + uuid.uuid4().hex.upper(),
        "nome":"Consulta limitada","permissoes":["instrumentos_consultar"]}).json()
    simple = create_access(admin,target,instrument,lean["codigo"])
    path = "/api/v1/acessos/" + simple + "/lote"
    assert client.put(path,json=plan(target,instrument,perfis=[lean["codigo"]])).status_code == 200
    assert client.put(path,json=plan(target,instrument,perfis=[lean["codigo"],read["codigo"]])).status_code == 403
    assert client.put("/api/v1/acessos/" + original + "/lote",json=plan(target,instrument,perfis=[lean["codigo"]])).status_code == 403
    assert TestClient(create_app()).put(path,json=plan(target)).status_code == 401
    assert admin.put("/api/v1/acessos/" + str(uuid.uuid4()) + "/lote",json=plan(target)).status_code == 404


def test_edicao_lote_protege_admin_e_preserva_id_quando_nao_primeiro(ctx):
    admin, _, _ = ctx
    self_id = admin.get("/api/v1/auth/me").json()["id"]
    own = next(a for a in admin.get("/api/v1/acessos",params={"usuario_id":self_id}).json()["items"] if a["papel"] == "ADMIN")
    data = {"usuario_id":self_id,"perfis":["EDITOR"],"escopo":"GLOBAL","instrumento_ids":[]}
    assert admin.put("/api/v1/acessos/" + own["id"] + "/lote",json=data).status_code == 409
    user = criar(admin,payload())
    original = create_access(admin,user,role="REVISOR")
    response = admin.put("/api/v1/acessos/" + original + "/lote",json=plan(user,perfis=["EDITOR","REVISOR"]))
    assert response.status_code == 200
    assert admin.get("/api/v1/acessos/" + original).json()["papel"] == "REVISOR"


def test_edicao_lote_falha_sql_reverte_atualizacao_e_inclusoes(ctx,monkeypatch):
    admin, instrument, _ = ctx
    user = criar(admin,payload())
    original = create_access(admin,user,instrument)
    before = grants(admin,user)
    flush = Session.flush
    def fail(db,*args,**kwargs):
        inserts = any(isinstance(row,AcessoInstrumento) for row in db.new)
        result = flush(db,*args,**kwargs)
        if inserts:
            raise IntegrityError("falha simulada",{},Exception("rollback"))
        return result
    with monkeypatch.context() as m:
        m.setattr(Session,"flush",fail)
        response = admin.put("/api/v1/acessos/" + original + "/lote",json=plan(user,perfis=["EDITOR","REVISOR"]))
        assert response.status_code == 409
    assert grants(admin,user) == before
