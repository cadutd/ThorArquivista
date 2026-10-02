from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.registro_service import _texto_busca, _validar


def campo(chave: str, tipo: str, obrigatorio: bool = False, aparece_busca: bool = True):
    return SimpleNamespace(
        chave=chave,
        tipo=tipo,
        obrigatorio=obrigatorio,
        aparece_busca=aparece_busca,
        nome=chave,
    )


def test_validar_aceita_dados_compativeis():
    campos = [campo("titulo", "TEXTO_CURTO", True), campo("ano", "NUMERO")]
    _validar(campos, {"titulo": "Mapa", "ano": 1932})


def test_validar_rejeita_obrigatorio_ausente():
    campos = [campo("titulo", "TEXTO_CURTO", True)]
    with pytest.raises(HTTPException) as exc:
        _validar(campos, {})
    assert exc.value.status_code == 422


def test_validar_rejeita_campo_desconhecido():
    campos = [campo("titulo", "TEXTO_CURTO")]
    with pytest.raises(HTTPException) as exc:
        _validar(campos, {"titulo": "A", "extra": "B"})
    assert exc.value.status_code == 422


def test_validar_rejeita_tipo_incorreto():
    campos = [campo("ano", "NUMERO")]
    with pytest.raises(HTTPException) as exc:
        _validar(campos, {"ano": "1932"})
    assert exc.value.status_code == 422


def test_texto_busca_usa_apenas_campos_marcados():
    campos = [campo("titulo", "TEXTO_CURTO", aparece_busca=True), campo("interno", "TEXTO_CURTO", aparece_busca=False)]
    assert _texto_busca(campos, {"titulo": "Mapa", "interno": "sigilo"}) == "Mapa"
