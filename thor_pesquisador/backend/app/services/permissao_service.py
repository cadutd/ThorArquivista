from fastapi import HTTPException
from sqlalchemy import exists, or_, select
from app.core.permissions import expand_legacy
from app.models.editorial import AcessoInstrumento, Papel

ROLE_PERMISSIONS = {
    "ADMIN": ["*"],
    "GESTOR_INSTRUMENTOS": ["consultar", "criar_instrumento", "gerenciar", "editar_registro", "enviar_revisao", "publicar", "arquivar", "reindexar", "gerenciar_imagens"],
    "EDITOR": ["consultar", "editar_registro", "enviar_revisao", "gerenciar_imagens"],
    "REVISOR": ["consultar", "revisar"],
    "CONSULTA_INTERNA": ["consultar"],
    "PUBLICO_AUTENTICADO": ["consulta_publicada"],
}
ROLE_PERMISSIONS = {name: expand_legacy(values) for name, values in ROLE_PERMISSIONS.items()}


def permissoes(db, instrumento_id=None, usuario=None):
    usuario = usuario or db.info.get("usuario")
    if not usuario:
        return set()
    rows = db.execute(select(Papel.permissoes).join(AcessoInstrumento, AcessoInstrumento.papel == Papel.nome).where(
        AcessoInstrumento.usuario_id == usuario.id,
        Papel.ativo.is_(True),
        or_(AcessoInstrumento.instrumento_id.is_(None), AcessoInstrumento.instrumento_id == instrumento_id)
        if instrumento_id else AcessoInstrumento.instrumento_id.is_(None)))
    return {p for row in rows for p in row[0]}


def require(db, acao, instrumento_id=None):
    permissions = permissoes(db, instrumento_id)
    if "*" not in permissions and acao not in permissions:
        raise HTTPException(403, "Sem permissao para esta acao ou instrumento.")
    return db.info["usuario"]


def filtro_escopo(db, coluna, acao="instrumentos_consultar"):
    usuario = db.info.get("usuario")
    global_permissions = permissoes(db)
    if "*" in global_permissions or acao in global_permissions:
        return True
    if not usuario:
        return False
    return exists(select(AcessoInstrumento.id).join(Papel).where(
        AcessoInstrumento.usuario_id == usuario.id,
        AcessoInstrumento.instrumento_id == coluna,
        Papel.ativo.is_(True),
        Papel.permissoes.contains([acao])))


def require_imagens(db, usuario, acao="imagens_consultar"):
    permissions = permissoes(db, usuario=usuario)
    scoped = db.scalar(select(AcessoInstrumento.id).join(Papel).where(
        AcessoInstrumento.usuario_id == usuario.id,
        Papel.ativo.is_(True),
        Papel.permissoes.contains([acao])).limit(1))
    if "*" not in permissions and acao not in permissions and not scoped:
        raise HTTPException(403, "Sem permissao para esta operacao de imagens.")


def validar_delegacao(db, permissions, instrumento_id=None):
    """Delegation never creates privileges the acting user does not hold."""
    own = permissoes(db, instrumento_id)
    if "*" not in own and not set(permissions).issubset(own):
        raise HTTPException(403, "Nao e permitido administrar permissoes superiores as suas.")


def validar_concessao(db, papel, instrumento_id=None):
    profile = db.get(Papel, papel)
    if not profile:
        raise HTTPException(422, "Perfil inexistente.")
    validar_delegacao(db, profile.permissoes, instrumento_id)


def validar_usuario_delegado(db, usuario_id):
    grants = db.scalars(select(AcessoInstrumento).where(AcessoInstrumento.usuario_id == usuario_id))
    for grant in grants:
        validar_concessao(db, grant.papel, grant.instrumento_id)


def require_any_scope(db, acao):
    usuario = db.info.get("usuario")
    if not usuario:
        raise HTTPException(403, "Sem permissao para esta operacao.")
    require_imagens(db, usuario, acao)
