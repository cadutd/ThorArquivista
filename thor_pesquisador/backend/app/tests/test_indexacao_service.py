from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx

from app.schemas.busca import BuscaAvancadaIn
from app.services import indexacao_service
from app.services.indexacao_service import _build_filter, _build_sort, documento_indexavel


def campo(chave: str, tipo: str, **kwargs):
    defaults = {
        "chave": chave,
        "tipo": tipo,
        "aparece_busca": True,
        "filtro_avancado": False,
        "facetavel": False,
        "ordenavel": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_documento_indexavel_gera_titulo_e_texto_geral():
    campos = [
        campo("titulo", "TEXTO_CURTO"),
        campo("resumo", "TEXTO_LONGO"),
        campo("interno", "TEXTO_CURTO", aparece_busca=False),
    ]
    doc = {
        "_id": "registro-1",
        "instrumento_id": "instrumento-1",
        "schema_version": 2,
        "dados": {"titulo": "Mapa historico", "resumo": "Cartografia urbana", "interno": "sigilo"},
        "status": "ATIVO",
        "criado_em": datetime(2026, 1, 1, tzinfo=UTC),
        "atualizado_em": datetime(2026, 1, 2, tzinfo=UTC),
    }

    result = documento_indexavel(campos, doc)

    assert result["id"] == "registro-1"
    assert result["titulo"] == "Mapa historico"
    assert "Cartografia urbana" in result["texto_geral"]
    assert "sigilo" not in result["texto_geral"]


def test_build_filter_usa_apenas_campos_marcados():
    campos = [
        campo("serie", "LISTA_SIMPLES", filtro_avancado=True),
        campo("ano", "NUMERO", filtro_avancado=True),
        campo("interno", "TEXTO_CURTO", filtro_avancado=False),
    ]

    result = _build_filter(campos, {"serie": "ATAS", "ano": {"gte": 1930, "lte": 1950}, "interno": "nao"})

    assert 'status != "EXCLUIDO"' in result
    assert 'dados.serie = "ATAS"' in result
    assert "dados.ano >= 1930" in result
    assert "dados.ano <= 1950" in result
    assert not any("interno" in item for item in result)


def test_build_sort_usa_apenas_campos_ordenaveis():
    campos = [campo("titulo", "TEXTO_CURTO", ordenavel=True), campo("interno", "TEXTO_CURTO")]

    result = _build_sort(campos, ["titulo:asc", "interno:desc", "criado_em:desc"])

    assert result == ["dados.titulo:asc", "criado_em:desc"]


def test_busca_avancada_retorna_vazio_quando_indice_nao_existe(monkeypatch):
    instrumento_id = uuid.uuid4()
    monkeypatch.setattr(indexacao_service, "_campos", lambda _db, _instrumento_id: [campo("titulo", "TEXTO_CURTO")])
    monkeypatch.setattr(indexacao_service, "_meili_request", _raise_meili_not_found)

    result = indexacao_service.buscar_avancado(SimpleNamespace(), instrumento_id, BuscaAvancadaIn())

    assert result["items"] == []
    assert result["total"] == 0
    assert result["indice_defasado"] is True


def test_facetas_retorna_vazio_quando_indice_nao_existe(monkeypatch):
    instrumento_id = uuid.uuid4()
    monkeypatch.setattr(indexacao_service, "_campos", lambda _db, _instrumento_id: [campo("serie", "LISTA_SIMPLES", facetavel=True)])
    monkeypatch.setattr(indexacao_service, "_meili_request", _raise_meili_not_found)

    result = indexacao_service.facetas(SimpleNamespace(), instrumento_id)

    assert result == {"instrumento_id": instrumento_id, "facetas": {}}


def _raise_meili_not_found(*_args, **_kwargs):
    request = httpx.Request("POST", "http://meilisearch:7700/indexes/inexistente/search")
    response = httpx.Response(404, request=request)
    raise httpx.HTTPStatusError("Indice inexistente.", request=request, response=response)
