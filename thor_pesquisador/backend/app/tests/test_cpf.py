import pytest
from app.services.cpf import normalizar_cpf
from app.schemas.usuario import UsuarioIn


@pytest.mark.parametrize("value", ["52998224725", "529.982.247-25", "529982247-25", " 52998224725 "])
def test_normaliza_cpf(value):
    assert normalizar_cpf(value) == "52998224725"


@pytest.mark.parametrize("value", ["", "00000000000", "11111111111", "52998224724", "5299822472",
                                  "529a98224725", "529 982 24725", "５２９９８２２４７２５"])
def test_rejeita_cpf_invalido(value):
    with pytest.raises(ValueError):
        normalizar_cpf(value)


def test_schema_normaliza_username_e_rejeita_campos_extras():
    data = dict(nome=" Nome ",username="Meu.Usuario",cpf="529.982.247-25",
                email="user@example.org")
    row = UsuarioIn(**data)
    assert row.username == "meu.usuario" and row.nome == "Nome"
    with pytest.raises(ValueError):
        UsuarioIn(**data, govbr_sub="52998224725")
