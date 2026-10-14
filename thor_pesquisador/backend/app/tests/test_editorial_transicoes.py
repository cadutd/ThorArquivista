import pytest
from fastapi import HTTPException
from app.services.editorial_service import TRANSICOES, validar_transicao


@pytest.mark.parametrize("acao", list(TRANSICOES))
@pytest.mark.parametrize("estado", ["RASCUNHO", "EM_REVISAO", "APROVADO", "PUBLICADO", "ARQUIVADO"])
def test_todas_transicoes(acao, estado):
    if estado in TRANSICOES[acao][0]:
        assert validar_transicao(acao, estado, "Justificativa")[1] == TRANSICOES[acao][1]
    else:
        with pytest.raises(HTTPException) as error:
            validar_transicao(acao, estado, "Justificativa")
        assert error.value.status_code == 409


@pytest.mark.parametrize("acao,estado", [("devolver", "EM_REVISAO"), ("arquivar", "PUBLICADO")])
def test_justificativa_obrigatoria(acao, estado):
    with pytest.raises(HTTPException) as error:
        validar_transicao(acao, estado, " ")
    assert error.value.status_code == 422
