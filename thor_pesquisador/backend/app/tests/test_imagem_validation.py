from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from PIL import Image
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.imagem import ImagemCreate, ImagemUpdate
from app.services.armazenamento_service import ArmazenamentoS3, validar_imagem


def png():
    data = BytesIO()
    Image.new("RGB", (32, 24), "white").save(data, format="PNG")
    return data.getvalue()


@pytest.mark.parametrize("uri", ["javascript:alert(1)", "file:///etc/passwd", "https://user:pass@example.org/x", ""])
def test_url_invalida(uri):
    with pytest.raises(ValidationError):
        ImagemCreate(titulo="Imagem", uri=uri)


def test_manifest_obrigatorio_e_upload_nao_pode_ser_falsificado():
    for payload in [{"tipo_referencia": "IIIF"}, {"tipo_referencia": "UPLOAD", "uri": "https://example.org/a.png"}]:
        with pytest.raises(ValidationError):
            ImagemCreate(titulo="Imagem", **payload)
    with pytest.raises(ValidationError):
        ImagemUpdate(titulo=" ", object_key="arbitrario")


def test_valida_dimensoes_miniatura_e_checksum():
    data = png()
    width, height, thumbnail = validar_imagem(data, "image/png")
    assert (width, height) == (32, 24)
    assert Image.open(BytesIO(thumbnail)).format == "JPEG"
    assert len(ArmazenamentoS3.calcular_checksum(data)) == 64


@pytest.mark.parametrize("data,mime,status", [
    (b"", "image/png", 413), (b"not-an-image", "image/png", 422),
    (b"<svg/>", "image/svg+xml", 422),
])
def test_upload_invalido(data, mime, status):
    with pytest.raises(HTTPException) as exc:
        validar_imagem(data, mime)
    assert exc.value.status_code == status


def test_limite_e_mime_spoofing(monkeypatch):
    with pytest.raises(HTTPException):
        validar_imagem(png(), "image/jpeg")
    monkeypatch.setattr(settings, "upload_max_bytes", 5)
    with pytest.raises(HTTPException) as exc:
        validar_imagem(png(), "image/png")
    assert exc.value.status_code == 413


def test_url_assinada_expira(monkeypatch):
    params = {}
    def generate(method, **kwargs):
        params.update(kwargs)
        assert method == "get_object"
        return "https://example.org/signed"
    storage = ArmazenamentoS3()
    monkeypatch.setattr(storage, "client", lambda: SimpleNamespace(generate_presigned_url=generate))
    assert storage.obter_url_acesso("original") == "https://example.org/signed"
    assert params["ExpiresIn"] == settings.s3_url_expiration
