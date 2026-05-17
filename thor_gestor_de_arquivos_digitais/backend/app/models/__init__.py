from __future__ import annotations

# Importa os models para que o SQLAlchemy/Alembic carregue o metadata completo

from app.models.unidade_acondicionamento import UnidadeAcondicionamento  # noqa: F401
from app.models.unidade_acondicionamento_digital import (  # noqa: F401
    UnidadeAcondicionamentoDigital,
)
from app.models.midia_armazenamento import MidiaArmazenamento  # noqa: F401
from app.models.copia_unidade_acondicionamento_digital import (  # noqa: F401
    CopiaUnidadeAcondicionamentoDigital,
)
from app.models.evento_preservacao import EventoPreservacao  # noqa: F401
from app.models.armazenamento import (  # noqa: F401
    CompartimentoArmazenamento,
    EstruturaArmazenamento,
    LocalGuarda,
    MovimentacaoArmazenamento,
    PosicaoArmazenamento,
    ZonaGuarda,
)
from app.models.configuracao import ParametroSistema  # noqa: F401
from app.models.descricao_arquivistica import RegistroDescritivo  # noqa: F401
from app.models.ficha_espelho import ModeloFichaEspelho  # noqa: F401
from app.models.instrumento_pesquisa import InstrumentoCampo, InstrumentoPesquisa  # noqa: F401
from app.models.entidade_produtora import EntidadeProdutora  # noqa: F401
from app.models.instituicao_arquivo import InstituicaoArquivo  # noqa: F401
from app.models.user import User  # noqa: F401
