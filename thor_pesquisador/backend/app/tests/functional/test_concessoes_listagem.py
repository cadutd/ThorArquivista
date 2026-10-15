from app.tests.functional.test_editorial import ctx
from app.tests.functional.test_usuarios import payload, criar


def test_concessoes_listam_nomes_e_filtram_no_servidor(ctx):
    admin, instrument_id, _ = ctx
    user = criar(admin, payload())
    global_access = admin.post("/api/v1/acessos", json={"usuario_id": user["id"], "papel": "CONSULTA_INTERNA"}).json()["id"]
    scoped_access = admin.post("/api/v1/acessos", json={"usuario_id": user["id"], "papel": "EDITOR",
                                                       "instrumento_id": instrument_id}).json()["id"]
    instrument_name = admin.get("/api/v1/instrumentos/" + instrument_id).json()["nome"]
    params = {"usuario_id": user["id"], "q": user["username"]}
    page = admin.get("/api/v1/acessos", params=params).json()
    assert page["total"] == 2
    by_id = {row["id"]: row for row in page["items"]}
    assert by_id[global_access]["instrumento_nome"] == "Todos"
    assert by_id[scoped_access]["instrumento_nome"] == instrument_name
    assert all(row["perfil_nome"] and row["criado_em"] for row in page["items"])
    assert all(row["username"] == user["username"] for row in page["items"])
    scoped = admin.get("/api/v1/acessos", params={**params, "escopo": "INSTRUMENTO",
                                                 "instrumento": instrument_name, "papel": "EDITOR"}).json()
    assert scoped["total"] == 1 and scoped["items"][0]["id"] == scoped_access
    assert admin.get("/api/v1/acessos", params={**params, "escopo": "GLOBAL"}).json()["items"][0]["id"] == global_access
    assert admin.get("/api/v1/acessos", params={**params, "instrumento": "INEXISTENTE"}).json()["total"] == 0
    assert admin.get("/api/v1/acessos", params={**params, "limit": 1, "offset": 1}).json()["total"] == 2
    assert admin.get("/api/v1/acessos", params={**params, "limit": 1, "offset": 2}).json()["items"] == []
    assert admin.get("/api/v1/acessos", params={"escopo": "INVALIDO"}).status_code == 422
    detail = admin.get("/api/v1/acessos/" + scoped_access).json()
    assert detail["instrumento_nome"] == instrument_name and detail["perfil_nome"] == by_id[scoped_access]["perfil_nome"]
    assert detail["username"] == user["username"]
