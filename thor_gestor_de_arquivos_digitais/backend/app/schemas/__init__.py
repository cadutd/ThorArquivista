# Schemas pt_BR (Unidade de Acondicionamento)
from app.schemas.unidade_acondicionamento import (  # noqa: F401
    UnidadeAcondicionamentoCreate,
    UnidadeAcondicionamentoUpdate,
    UnidadeAcondicionamentoOut,
)

from app.schemas.unidade_acondicionamento_digital import (  # noqa: F401
    UnidadeAcondicionamentoDigitalCreate,
    UnidadeAcondicionamentoDigitalOut,
)

from app.schemas.midia_armazenamento import (  # noqa: F401
    MidiaArmazenamentoCreate,
    MidiaArmazenamentoUpdate,
    MidiaArmazenamentoOut,
)

from app.schemas.copia_unidade_acondicionamento_digital import (  # noqa: F401
    CopiaUnidadeAcondicionamentoDigitalCreate,
    CopiaUnidadeAcondicionamentoDigitalUpdate,
    CopiaUnidadeAcondicionamentoDigitalOut,
)

from app.schemas.evento_preservacao import (  # noqa: F401
    EventoPreservacaoCreate,
    EventoPreservacaoOut,
)

from app.schemas.evento_midia_armazenamento import (  # noqa: F401
    EventoMidiaArmazenamentoCreate,
    EventoMidiaArmazenamentoOut,
)

from app.schemas.migracao_midia import (  # noqa: F401
    MigracaoMidiaConclusao,
    MigracaoMidiaEtapaCreate,
    MigracaoMidiaIniciar,
    MigracaoMidiaOut,
    MigracaoMidiaPage,
    MigracaoMidiaRelatorioCreate,
    MigracaoMidiaUpdate,
)
