import uuid
import pytest
from sqlalchemy import select
from app.core.permissions import CRUD_MODULES, OPERATIONS, PERMISSIONS, expand_legacy
from app.db.session import SessionLocal
from app.models.editorial import AcessoInstrumento, Papel
from app.models.imagem import ImagemDocumento
from app.tests.functional.test_editorial import ctx
from app.tests.functional.test_administracao import user_client


def grant(admin, user, permissions, instrument=None):
    code = "CRUD_" + uuid.uuid4().hex.upper()
    response = admin.post("/api/v1/perfis", json={"codigo": code, "nome": "Perfil granular",
                                               "permissoes": permissions})
    assert response.status_code == 201, response.text
    response = admin.post("/api/v1/acessos", json={"usuario_id": user["id"], "papel": code,
                                                  "instrumento_id": instrument})
    assert response.status_code == 201, response.text
    return code, response.json()["id"]


def cpf():
    digits = [int(d) for d in str(uuid.uuid4().int % 1000000000).zfill(9)]
    for weights in (range(10, 1, -1), range(11, 1, -1)):
        remainder = sum(d * w for d, w in zip(digits, weights)) % 11
        digits.append(0 if remainder < 2 else 11 - remainder)
    return "".join(map(str, digits))


def requests_for(admin, actor, user, instrument, record, module):
    base = "/api/v1/instrumentos/" + instrument
    profile, _ = grant(admin, user_client()[1], [])
    _, target = user_client()
    if module == "instrumentos":
        return [("GET", base, None),
                ("POST", "/api/v1/instrumentos", {"nome": "Granular", "tipo": "CATALOGO"}),
                ("PUT", base, {"nome": "Atualizado"}),
                ("DELETE", base, None)]
    if module == "campos":
        field = admin.get(base + "/campos").json()[0]["id"]
        return [("GET", base + "/campos", None),
                ("POST", base + "/campos", {"nome": "Novo", "chave": "novo", "tipo": "TEXTO_CURTO"}),
                ("PUT", base + "/campos/" + field, {"nome": "Atualizado"}),
                ("DELETE", base + "/campos/" + field, None)]
    if module == "registros":
        return [("GET", base + "/registros/" + record, None),
                ("POST", base + "/registros", {"dados": {"titulo": "Novo"}}),
                ("PUT", base + "/registros/" + record, {"dados": {"titulo": "Atualizado"}}),
                ("DELETE", base + "/registros/" + record, None)]
    if module in {"imagens", "galerias"}:
        image = admin.post("/api/v1/imagens", json={"titulo": "Imagem",
            "uri": "https://example.org/granular.jpg", "direitos_acesso": "PUBLICO"}).json()["id"]
        with SessionLocal() as db:
            db.get(ImagemDocumento, uuid.UUID(image)).criado_por = uuid.UUID(user["id"])
            db.commit()
        if module == "imagens":
            return [("GET", "/api/v1/imagens/" + image, None),
                    ("POST", "/api/v1/imagens", {"titulo": "Nova", "uri": "https://example.org/nova.jpg"}),
                    ("PUT", "/api/v1/imagens/" + image, {"titulo": "Atualizada", "uri": "https://example.org/granular.jpg", "direitos_acesso": "PUBLICO"}),
                    ("DELETE", "/api/v1/imagens/" + image, None)]
        path = base + "/registros/" + record + "/imagens"
        linked = admin.post("/api/v1/imagens", json={"titulo": "Vinculada",
            "uri": "https://example.org/linked.jpg", "direitos_acesso": "PUBLICO"}).json()["id"]
        assert admin.post(path, json={"imagem_id": linked}).status_code == 201
        return [("GET", path, None), ("POST", path, {"imagem_id": image}),
                ("PATCH", path + "/" + linked, {"legenda": "Atualizada"}),
                ("DELETE", path + "/" + linked, None)]
    if module == "usuarios":
        with SessionLocal() as db:
            from app.models.user import Usuario
            db.get(Usuario, uuid.UUID(target["id"])).govbr_sub = None
            db.commit()
        data = {"nome": "Usuario granular", "username": "u_" + uuid.uuid4().hex,
                "cpf": cpf(), "email": "granular@example.org"}
        return [("GET", "/api/v1/usuarios/" + target["id"], None),
                ("POST", "/api/v1/usuarios", data),
                ("PUT", "/api/v1/usuarios/" + target["id"], data),
                ("DELETE", "/api/v1/usuarios/" + target["id"], None)]
    if module == "perfis":
        payload = {"codigo": profile, "nome": "Perfil atualizado", "permissoes": []}
        return [("GET", "/api/v1/perfis/" + profile, None),
                ("POST", "/api/v1/perfis", {**payload, "codigo": "NOVO_" + uuid.uuid4().hex.upper()}),
                ("PUT", "/api/v1/perfis/" + profile, payload),
                ("DELETE", "/api/v1/perfis/" + profile, None)]
    if module == "retencao":
        payload = {"nome": "Politica " + uuid.uuid4().hex, "categoria": "LOG_TECNICO", "dias": 30}
        pid = admin.post("/api/v1/retencao/politicas", json=payload).json()["id"]
        return [("GET", "/api/v1/retencao/politicas/" + pid, None),
                ("POST", "/api/v1/retencao/politicas", {**payload, "nome": "Nova " + uuid.uuid4().hex}),
                ("PUT", "/api/v1/retencao/politicas/" + pid, payload),
                ("DELETE", "/api/v1/retencao/politicas/" + pid, None)]
    access = admin.post("/api/v1/acessos", json={"usuario_id": target["id"], "papel": profile}).json()["id"]
    return [("GET", "/api/v1/acessos/" + access, None),
            ("POST", "/api/v1/acessos", {"usuario_id": target["id"], "papel": profile, "instrumento_id": instrument}),
            ("PUT", "/api/v1/acessos/" + access, {"usuario_id": target["id"], "papel": profile}),
            ("DELETE", "/api/v1/acessos/" + access, None)]


@pytest.mark.parametrize("module", CRUD_MODULES)
@pytest.mark.parametrize("operation", OPERATIONS)
def test_operacao_independente_na_api(ctx, module, operation):
    admin, instrument, record = ctx
    actor, user = user_client()
    dependencies = []
    grant(admin, user, [module + "_" + operation, *dependencies])
    cases = requests_for(admin, actor, user, instrument, record, module)
    allowed_index = OPERATIONS.index(operation)
    # Denied operations cannot mutate fixtures before the permitted request.
    for index, (method, path, payload) in enumerate(cases):
        if index != allowed_index:
            response = actor.request(method, path, json=payload)
            assert response.status_code == 403, (module, operation, method, response.text)
    method, path, payload = cases[allowed_index]
    response = actor.request(method, path, json=payload)
    assert 200 <= response.status_code < 300, (module, operation, response.text)


def test_editar_nao_exclui_registro_por_put(ctx):
    admin, instrument, record = ctx
    actor, user = user_client()
    grant(admin, user, ["registros_editar"])
    response = actor.put("/api/v1/instrumentos/" + instrument + "/registros/" + record,
                         json={"dados": {"titulo": "Tentativa"}, "status": "EXCLUIDO"})
    assert response.status_code == 403
    assert admin.get("/api/v1/instrumentos/" + instrument + "/registros/" + record).json()["status"] == "ATIVO"


def test_escopo_nao_concede_acesso_global_ou_outro_instrumento(ctx):
    admin, instrument, _ = ctx
    actor, user = user_client()
    grant(admin, user, ["instrumentos_consultar", "instrumentos_editar", "usuarios_consultar"], instrument)
    assert actor.get("/api/v1/instrumentos/" + instrument).status_code == 200
    assert actor.put("/api/v1/instrumentos/" + instrument, json={"nome": "Permitido"}).status_code == 200
    other = admin.post("/api/v1/instrumentos", json={"nome": "Outro", "tipo": "CATALOGO"}).json()["id"]
    assert actor.get("/api/v1/instrumentos/" + other).status_code == 403
    assert actor.put("/api/v1/instrumentos/" + other, json={"nome": "Negado"}).status_code == 403
    assert actor.get("/api/v1/usuarios").status_code == 403
    assert actor.post("/api/v1/instrumentos", json={"nome": "Negado", "tipo": "CATALOGO"}).status_code == 403
    assert actor.get("/api/v1/instrumentos").json()["total"] == 1


def test_administracao_delegada_nao_eleva_privilegios(ctx):
    admin, _, _ = ctx
    actor, user = user_client()
    permissions = [m + "_" + op for m in ("usuarios", "perfis", "acessos") for op in OPERATIONS]
    permissions += ["permissoes_consultar"]
    own_profile, own_access = grant(admin, user, permissions)
    _, target = user_client()
    assert actor.post("/api/v1/acessos", json={"usuario_id": target["id"], "papel": "ADMIN"}).status_code == 403
    assert actor.put("/api/v1/acessos/" + own_access, json={"usuario_id": user["id"], "papel": "ADMIN"}).status_code == 403
    assert actor.post("/api/v1/perfis", json={"codigo": "ESCALADA", "nome": "Escalada",
                                            "permissoes": ["publicar"]}).status_code == 403
    assert actor.put("/api/v1/perfis/" + own_profile, json={"codigo": own_profile, "nome": "Escalada",
                                                         "permissoes": ["publicar"]}).status_code == 403
    assert actor.delete("/api/v1/perfis/GESTOR_INSTRUMENTOS").status_code == 403
    # Mutating a privileged user's identity or grants would bypass profile delegation.
    admin_users = admin.get("/api/v1/usuarios", params={"papel": "ADMIN"}).json()["items"]
    admin_id = admin_users[0]["id"]
    assert actor.delete("/api/v1/usuarios/" + admin_id).status_code == 403
    assert actor.post("/api/v1/usuarios", json={"nome": "Escalada", "username": "e_" + uuid.uuid4().hex,
        "cpf": cpf(), "email": "esc@example.org", "perfil_codigo": "ADMIN"}).status_code == 422
    assert actor.get("/api/v1/permissoes").status_code == 200


def test_catalogo_operacoes_e_legados(ctx):
    admin, _, _ = ctx
    rows = admin.get("/api/v1/permissoes?limit=100").json()["items"]
    assert len({p["codigo"] for p in rows}) == len(rows)
    for module in CRUD_MODULES:
        assert {p["acao"] for p in rows if p["codigo"].startswith(module + "_")} == {op.upper() for op in OPERATIONS}
    assert {p["acao"] for p in rows if p["modulo"] == "Permissoes"} == {"CONSULTAR"}
    assert not {"gerenciar", "consultar", "editar_registro", "gerenciar_imagens"} & {p["codigo"] for p in rows}
    assert expand_legacy(["registros_editar"]) == ["registros_editar"]
    assert set(expand_legacy(["editar_registro"])) == {"registros_incluir", "registros_editar", "registros_excluir"}
