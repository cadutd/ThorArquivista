from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services import exportacao_service as exports, retencao_service as retention


@pytest.mark.parametrize("before", exports.TRANSITIONS)
@pytest.mark.parametrize("after", exports.TRANSITIONS)
def test_maquina_exportacao_todas_transicoes(before, after):
    row = SimpleNamespace(status=before)
    if before == after or after in exports.TRANSITIONS[before]:
        exports.transicionar(row, after)
        assert row.status == after
    else:
        with pytest.raises(HTTPException) as error:
            exports.transicionar(row, after)
        assert error.value.status_code == 409 and row.status == before


@pytest.mark.parametrize("before", retention.TRANSITIONS)
@pytest.mark.parametrize("after", retention.TRANSITIONS)
def test_maquina_retencao_todas_transicoes(before, after):
    row = SimpleNamespace(status=before)
    if before == after or after in retention.TRANSITIONS[before]:
        retention.transicionar(row, after)
        assert row.status == after
    else:
        with pytest.raises(HTTPException):
            retention.transicionar(row, after)
        assert row.status == before


@pytest.mark.parametrize("text", ["=1+1", "+cmd", "-cmd", "@SUM(A1)", "  =cmd", "\tcmd", "\ncmd", "\rcmd"])
def test_csv_neutraliza_formulas(text):
    assert exports.csv_value(text) == "'" + text


@pytest.mark.parametrize("value", [-10, 0, 1.5, None, "texto", "com,virgula", 'com"aspas'])
def test_csv_preserva_valores(value):
    assert exports.csv_value(value) == value


def test_excecao_http_nao_registra_bindings_sensiveis():
    import logging
    from app.core.observability import SanitizedExceptionFilter
    error = RuntimeError("token=SEGREDO cpf=00000000000")
    record = logging.LogRecord("uvicorn.error", logging.ERROR, "", 0, "Exception in ASGI application",
                               (), (RuntimeError, error, None))
    assert SanitizedExceptionFilter().filter(record)
    assert "SEGREDO" not in record.getMessage() and "00000000000" not in record.getMessage()
    assert record.exc_info is None and "RuntimeError" in record.getMessage()


def test_pacote_nao_trunca_referencias_silenciosamente(monkeypatch):
    import uuid
    from app.core.config import settings
    monkeypatch.setattr(settings, "exportacao_max_referencias_lote", 1)
    row = ("snap", uuid.uuid4(), "Imagem", "image/jpeg", "checksum")
    db = SimpleNamespace(execute=lambda q: [row, row])
    with pytest.raises(HTTPException) as error:
        exports._referencias(db, SimpleNamespace(formato="PACOTE"), [{"snapshot_id": "snap"}])
    assert error.value.status_code == 422


def test_retencao_cli_execucao_unica(monkeypatch):
    import sys
    from app import retention_worker
    calls = []
    monkeypatch.setattr(sys, "argv", ["retention_worker", "--max-lotes", "2"])
    monkeypatch.setattr(retention_worker, "rodada", calls.append)
    retention_worker.main()
    assert calls == [2]


def test_retencao_agendada_usa_intervalo_e_rodadas_limitadas(monkeypatch):
    import sys
    from app import retention_worker
    calls = []
    monkeypatch.setattr(sys, "argv", ["retention_worker", "--loop", "--intervalo-segundos", "2"])
    monkeypatch.setattr(retention_worker, "rodada", calls.append)
    def stop(seconds):
        assert seconds == 2
        raise KeyboardInterrupt
    monkeypatch.setattr(retention_worker.time, "sleep", stop)
    with pytest.raises(KeyboardInterrupt):
        retention_worker.main()
    assert calls == [100]
