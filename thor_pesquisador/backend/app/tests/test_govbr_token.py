from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
from fastapi import HTTPException
from jose import jwt, jwk
from app.core.config import settings
from app.services.auth_service import validate_jwt


@pytest.fixture
def signed():
    key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    private = key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption())
    public = key.public_key().public_bytes(Encoding.PEM,PublicFormat.SubjectPublicKeyInfo)
    jwks = {"keys":[{**jwk.construct(public,algorithm="RS256").to_dict(),"kid":"test-key"}]}
    origin = urlsplit(settings.govbr_authorize_url)
    claims = {"sub":"52998224725","aud":settings.govbr_client_id,
              "iss":f"{origin.scheme}://{origin.netloc}/",
              "exp":datetime.now(UTC) + timedelta(minutes=5),"nonce":"test-nonce"}
    def token(overrides=None,missing=None,kid="test-key"):
        data = {**claims,**(overrides or {})}
        if missing:
            del data[missing]
        return jwt.encode(data,private,algorithm="RS256",headers={"kid":kid})
    return token,jwks


def test_token_assinado_do_provedor(signed):
    token, jwks = signed
    assert validate_jwt(token(),jwks)["sub"] == "52998224725"


@pytest.mark.parametrize("missing",["sub","exp","aud","iss"])
def test_rejeita_claim_obrigatoria_ausente(signed,missing):
    token, jwks = signed
    with pytest.raises(HTTPException) as denied:
        validate_jwt(token(missing=missing),jwks)
    assert denied.value.status_code == 401


@pytest.mark.parametrize("overrides",[
    {"aud":"outro-client"},{"iss":"https://outro-provedor.example.org/"},
    {"iss":None},
    {"exp":datetime.now(UTC) - timedelta(minutes=10)},
])
def test_rejeita_audience_emissor_e_expiracao(signed,overrides):
    token, jwks = signed
    with pytest.raises(HTTPException) as denied:
        validate_jwt(token(overrides),jwks)
    assert denied.value.status_code == 401


def test_rejeita_chave_desconhecida(signed):
    token, jwks = signed
    with pytest.raises(HTTPException):
        validate_jwt(token(kid="outra"),jwks)
