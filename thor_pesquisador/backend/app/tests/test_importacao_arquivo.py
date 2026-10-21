import json
import pytest
from fastapi import HTTPException
from app.services.importacao_arquivo import ler_arquivo, converter, sugerir_tipo


@pytest.mark.parametrize("content,name,expected", [
    (b"Nome,Idade\nAna,20\n", "a.csv", [{"Nome": "Ana", "Idade": "20"}]),
    ("\ufeffNome;Porto\n\"Ana; Maria\";Santos\n".encode(), "a.csv", [{"Nome": "Ana; Maria", "Porto": "Santos"}]),
    ("Nome;Cidade\nJoão;Belém\n".encode("cp1252"), "a.csv", [{"Nome": "João", "Cidade": "Belém"}]),
    (b'[{"nome":"Ana"},{"porto":"Santos"}]', "a.json", [{"nome": "Ana"}, {"porto": "Santos"}]),
    (b'{"registros":[{"nome":"Ana"}]}', "a.json", [{"nome": "Ana"}]),
    (b'{"items":[{"nome":"Ana"}]}', "a.json", [{"nome": "Ana"}]),
    (b'Nome\n"Ana\nMaria"\n', "a.csv", [{"Nome": "Ana\nMaria"}]),
])
def test_leitura(content, name, expected):
    columns, rows, info = ler_arquivo(content, name)
    assert rows == expected and columns
    assert info["formato"] in {"csv", "json"}


@pytest.mark.parametrize("content,name", [
    (b"", "a.csv"), (b"nome,nome\na,b", "a.csv"), (b"a,b\nx", "a.csv"),
    (b"a,b\nx,y,z", "a.csv"), (b",b\nx,y", "a.csv"), (b"nome\n", "a.csv"),
    (b'[{"nome":1,"nome":2}]', "a.json"), (b"[NaN]", "a.json"),
    (b'[{"nome":NaN}]', "a.json"), (b"{}", "a.json"), (b"[1]", "a.json"),
    (b"[", "a.json"), (b"nome\x00\na", "a.csv"), (b"a", "a.exe"),
    (json.dumps([{"a": n} for n in range(1001)]).encode(), "a.json"),
    (("a\n" + "x\n" * 1001).encode(), "a.csv"),
    (json.dumps([{str(n): n for n in range(101)}]).encode(), "a.json"),
])
def test_rejeita_arquivo(content, name):
    with pytest.raises(HTTPException) as exc:
        ler_arquivo(content, name)
    assert exc.value.status_code == 422


@pytest.mark.parametrize("value,tipo,expected", [
    ("não", "BOOLEANO", False), ("Sim", "BOOLEANO", True), (0, "BOOLEANO", False),
    ("2,50", "NUMERO", 2.5), ("0", "NUMERO", 0), ("0012", "TEXTO_CURTO", "0012"),
    ("31/12/1900", "DATA", "1900-12-31"), ("1900-01-02", "DATA", "1900-01-02"),
    ("a|b", "LISTA_MULTIPLA", ["a", "b"]), ('["a","b"]', "LISTA_MULTIPLA", ["a", "b"]),
    (False, "BOOLEANO", False), ("", "NUMERO", None),
])
def test_conversao(value, tipo, expected):
    assert converter(value, tipo) == expected


@pytest.mark.parametrize("value,tipo", [
    ("talvez", "BOOLEANO"), ("nan", "NUMERO"), ("inf", "NUMERO"), (True, "NUMERO"),
    ("31/02/1900", "DATA"), ([1], "LISTA_MULTIPLA"),
])
def test_conversao_invalida(value, tipo):
    with pytest.raises((ValueError, TypeError)):
        converter(value, tipo)


def test_sugestoes_conservadoras():
    assert sugerir_tipo(["001", "002"]) == "TEXTO_CURTO"
    assert sugerir_tipo([0, 2.5]) == "NUMERO"
    assert sugerir_tipo([False, True]) == "BOOLEANO"
    assert sugerir_tipo(["1900-01-02"]) == "DATA"
    assert sugerir_tipo([["a"], ["b"]]) == "LISTA_MULTIPLA"
    assert converter("9007199254740993", "NUMERO") == 9007199254740993
    assert converter("1e100", "NUMERO") == 1e100
    with pytest.raises(ValueError):
        converter("9223372036854775808", "NUMERO")
