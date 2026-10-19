import uuid
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import Usuario
from app.models.editorial import Papel, AcessoInstrumento
from app.services.auth_service import create_session
from app.tests.functional.test_editorial import ctx, publish


def photo():
    buffer = BytesIO()
    Image.new("RGB", (320, 600), "green").save(buffer, format="PNG")
    return ("capa.png", buffer.getvalue(), "image/png")


def test_capa_upload_padrao_publicacao_e_revogacao(ctx):
    admin, iid, _ = ctx
    path = "/api/v1/instrumentos/" + iid
    original = admin.get(path).json()
    upload = admin.post("/api/v1/instrumentos/imagens-card", files={"arquivo":photo()})
    assert upload.status_code == 201, upload.text
    data = upload.json()
    assert (data["largura"], data["altura"]) == (960, 540)
    assert admin.get(path).json() == original
    preview = admin.get("/api/v1/instrumentos/imagens-card/" + data["id"])
    assert preview.status_code == 200
    assert Image.open(BytesIO(preview.content)).size == (960, 540)
    public_url = "/api/v1/publico/instrumentos/" + iid + "/imagem-card/" + data["id"]
    anonymous = TestClient(create_app())
    assert anonymous.get(public_url).status_code == 404
    assert admin.put(path, json={"imagem_card_id":data["id"],"versao_editorial":original["versao_editorial"]}).status_code == 200
    publish(admin, path)
    response = anonymous.get(public_url)
    assert response.status_code == 200 and response.headers["content-type"] == "image/jpeg"
    catalog = anonymous.get("/api/v1/publico/instrumentos", params={"nome":original["nome"]}).json()
    assert catalog["items"][0]["imagem_card_url"] == public_url.removeprefix("/api/v1")
    new = admin.post("/api/v1/instrumentos/imagens-card", data={"instrumento_id":iid}, files={"arquivo":photo()}).json()
    current = admin.get(path).json()
    assert admin.put(path, json={"imagem_card_id":new["id"],"versao_editorial":current["versao_editorial"]}).status_code == 200
    assert anonymous.get(public_url).status_code == 404
    publish(admin, path)
    new_url = "/api/v1/publico/instrumentos/" + iid + "/imagem-card/" + new["id"]
    assert anonymous.get(new_url).status_code == 200
    current = admin.get(path).json()
    assert admin.put(path, json={"imagem_card_id":None,"versao_editorial":current["versao_editorial"]}).status_code == 200
    assert anonymous.get(new_url).status_code == 404
    publish(admin, path)
    assert anonymous.get("/api/v1/publico/instrumentos", params={"nome":original["nome"]}).json()["items"][0]["imagem_card_url"] is None
    assert anonymous.get("/api/v1/imagens/" + str(uuid.uuid4()) + "/conteudo").status_code == 401


def test_capa_validacao_e_permissoes(ctx):
    admin, iid, _ = ctx
    anonymous = TestClient(create_app())
    url = "/api/v1/instrumentos/imagens-card"
    assert anonymous.post(url, files={"arquivo":photo()}).status_code == 401
    assert admin.post(url, files={"arquivo":("a.svg", b"<svg/>", "image/svg+xml")}).status_code == 422
    assert admin.post(url, files={"arquivo":("a.png", b"not-png", "image/png")}).status_code == 422
    large = BytesIO()
    Image.new("1", (5000, 4000)).save(large, format="PNG")
    assert admin.post(url, files={"arquivo":("grande.png", large.getvalue(), "image/png")}).status_code == 422
    capa = admin.post(url, files={"arquivo":photo()}).json()["id"]
    with SessionLocal() as db:
        user = Usuario(nome="Sem privilegios de capa"); db.add(user); db.commit()
        token = create_session(db, user)
        user_id = user.id
    client = TestClient(create_app()); client.cookies.set(settings.session_cookie_name, token)
    assert client.post(url, files={"arquivo":photo()}).status_code == 403
    assert client.get(url + "/" + capa).status_code == 404
    with SessionLocal() as db:
        profile = Papel(nome="CAPA_" + uuid.uuid4().hex, permissoes=["instrumentos_incluir"])
        db.add(profile); db.flush()
        grant = AcessoInstrumento(usuario_id=user_id, papel=profile.nome)
        db.add(grant); db.commit()
        grant_id = grant.id
    owned = client.post(url, files={"arquivo":photo()})
    assert owned.status_code == 201
    preview_path = url + "/" + owned.json()["id"]
    assert client.get(preview_path).status_code == 200
    with SessionLocal() as db:
        db.delete(db.get(AcessoInstrumento, grant_id)); db.commit()
    assert client.get(preview_path).status_code == 404
    current = admin.get("/api/v1/instrumentos/" + iid).json()
    assert admin.put("/api/v1/instrumentos/" + iid, json={"imagem_card_id":str(uuid.uuid4()),
        "versao_editorial":current["versao_editorial"]}).status_code == 404


def test_filtros_internos_e_catalogo_snapshot(ctx):
    admin, iid, _ = ctx
    path = "/api/v1/instrumentos/" + iid
    current = admin.get(path).json()
    name = "Catalogo " + uuid.uuid4().hex
    description = "Descricao institucional para combinar filtros"
    assert admin.put(path, json={"nome":name,"descricao":description,"versao_editorial":current["versao_editorial"]}).status_code == 200
    filters = {"nome":name,"tipo":"CATALOGO","status":"RASCUNHO","visibilidade":"PUBLICO","descricao":"combinar filtros"}
    response = admin.get("/api/v1/instrumentos", params=filters).json()
    assert response["total"] == 1 and response["items"][0]["id"] == iid
    for key, value in (("visibilidade","INTERNO"),("descricao","inexistente"),("status","PUBLICADO"),("tipo","GUIA")):
        assert admin.get("/api/v1/instrumentos", params={**filters,key:value}).json()["total"] == 0
    publish(admin, path)
    anonymous = TestClient(create_app())
    filters = {"nome":name,"tipo":"CATALOGO","descricao":"combinar filtros"}
    assert anonymous.get("/api/v1/publico/instrumentos", params=filters).json()["total"] == 1
    assert anonymous.get("/api/v1/publico/instrumentos", params={**filters,"descricao":"inexistente"}).json()["total"] == 0
    current = admin.get(path).json()
    assert admin.put(path, json={"descricao":"Descricao privada nova","versao_editorial":current["versao_editorial"]}).status_code == 200
    assert anonymous.get("/api/v1/publico/instrumentos", params=filters).json()["total"] == 1
    assert anonymous.get("/api/v1/publico/instrumentos", params={**filters,"descricao":"privada nova"}).json()["total"] == 0
