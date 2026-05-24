from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router

from app.api.v1.admin import router as admin_router
from app.api.v1.aips import router as aips_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.armazenamento import router as armazenamento_router
from app.api.v1.descricao_arquivistica import router as descricao_arquivistica_router
from app.api.v1.unidades_acondicionamento import router as unidades_router
from app.api.v1.midias_armazenamento import router as midias_router
from app.api.v1.copias_unidades_acondicionamento_digitais import router as copias_router
from app.api.v1.eventos_preservacao import router as eventos_router
from app.api.v1.fichas_espelho import router as fichas_espelho_router
from app.api.v1.instrumentos_pesquisa import router as instrumentos_pesquisa_router
from app.api.v1.entidades_produtoras import router as entidades_produtoras_router
from app.api.v1.permissoes import router as permissoes_router
from app.api.v1.usuarios import router as usuarios_router
from app.api.v1.admissao import router as admissao_router

from app.security.deps import get_current_user_claims

api_router = APIRouter()


# Público
api_router.include_router(health_router, tags=["health"])

# Protegido (auth)
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(get_current_user_claims)],
)

# Protegidos (domínio)
protecoes = [Depends(get_current_user_claims)]

api_router.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=protecoes,
)

api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"],
    dependencies=protecoes,
)

api_router.include_router(
    armazenamento_router,
    tags=["armazenamento"],
    dependencies=protecoes,
)

api_router.include_router(
    descricao_arquivistica_router,
    prefix="/descricao-arquivistica",
    tags=["descricao-arquivistica"],
    dependencies=protecoes,
)

api_router.include_router(
    unidades_router,
    prefix="/unidades-acondicionamento",
    tags=["unidades-acondicionamento"],
    dependencies=protecoes,
)

api_router.include_router(
    midias_router,
    prefix="/midias-armazenamento",
    tags=["midias-armazenamento"],
    dependencies=protecoes,
)

api_router.include_router(
    copias_router,
    tags=["copias-unidade-acondicionamento-digital"],
    dependencies=protecoes,
)

api_router.include_router(
    eventos_router,
    tags=["eventos-preservacao"],
    dependencies=protecoes,
)

api_router.include_router(
    fichas_espelho_router,
    prefix="/fichas-espelho",
    tags=["fichas-espelho"],
    dependencies=protecoes,
)

api_router.include_router(
    instrumentos_pesquisa_router,
    prefix="/instrumentos-pesquisa",
    tags=["instrumentos-pesquisa"],
    dependencies=protecoes,
)

api_router.include_router(
    entidades_produtoras_router,
    prefix="/entidades-produtoras",
    tags=["entidades-produtoras"],
    dependencies=protecoes,
)

api_router.include_router(
    permissoes_router,
    tags=["perfis-permissoes"],
    dependencies=protecoes,
)

api_router.include_router(
    usuarios_router,
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=protecoes,
)

api_router.include_router(
    admissao_router,
    prefix="/admissao",
    tags=["admissao"],
    dependencies=protecoes,
)


#api_router.include_router(health_router, tags=["health"])
#api_router.include_router(unidades_router, prefix="/unidades-acondicionamento", tags=["unidades-acondicionamento"])
#api_router.include_router(midias_router, prefix="/midias-armazenamento", tags=["midias-armazenamento"])
#api_router.include_router(copias_router, tags=["copias-unidade-acondicionamento-digital"])
#api_router.include_router(eventos_router, tags=["eventos-preservacao"])
#api_router.include_router(aips_router, prefix="/aips", tags=["aips"])
