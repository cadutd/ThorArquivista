from fastapi import HTTPException
from sqlalchemy import exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from app.models.editorial import AcessoInstrumento, Papel
from app.models.user import Usuario
from app.services.permissao_service import ROLE_PERMISSIONS, require

from app.core.permissions import PERMISSIONS
from app.services.permissao_service import validar_delegacao, bloquear_administracao, ha_administrador, preservar_administrador



def perfil_out(row):
    return {"id": row.nome, "codigo": row.nome, "nome": row.titulo or row.nome,
            "descricao": row.descricao, "ativo": row.ativo,
            "sistema": row.nome in ROLE_PERMISSIONS, "permissoes": row.permissoes}


def obter_perfil(db, codigo, acao="perfis_consultar"):
    require(db, acao)
    row = db.get(Papel, codigo)
    if not row:
        raise HTTPException(404, "Perfil nao encontrado.")
    return row


def listar_perfis(db, q, ativo, limit, offset):
    require(db, "perfis_consultar")
    query = select(Papel).where(or_(Papel.nome.ilike("%" + q + "%"), Papel.titulo.ilike("%" + q + "%")))
    if ativo is not None:
        query = query.where(Papel.ativo == ativo)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return {"items": [perfil_out(r) for r in db.scalars(query.order_by(Papel.nome).limit(limit).offset(offset))],
            "total": total, "limit": limit, "offset": offset}


def salvar_perfil(db, payload, codigo=None):
    bloquear_administracao(db)
    admin_antes = ha_administrador(db)
    require(db, "perfis_editar" if codigo else "perfis_incluir")
    if codigo == "ADMIN" or payload.codigo == "ADMIN":
        raise HTTPException(409, "O perfil ADMIN e protegido.")
    if codigo is not None and payload.codigo != codigo:
        raise HTTPException(409, "O codigo de um perfil existente nao pode ser alterado.")
    valid = {p["codigo"] for p in PERMISSIONS}
    if set(payload.permissoes) - valid:
        raise HTTPException(422, "Permissao desconhecida ou administrativa.")
    row = obter_perfil(db, codigo, "perfis_editar") if codigo else Papel(nome=payload.codigo)
    validar_delegacao(db, set(payload.permissoes) | set(row.permissoes or []))
    row.titulo = payload.nome
    row.descricao = payload.descricao or None
    row.ativo = payload.ativo
    row.permissoes = sorted(set(payload.permissoes))
    if not codigo:
        db.add(row)
    try:
        preservar_administrador(db, admin_antes)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Codigo de perfil ja cadastrado.")
    return perfil_out(row)


def excluir_perfil(db, codigo):
    bloquear_administracao(db)
    admin_antes = ha_administrador(db)
    row = obter_perfil(db, codigo, "perfis_excluir")
    validar_delegacao(db, row.permissoes)
    if codigo == "ADMIN":
        raise HTTPException(409, "O perfil ADMIN e protegido.")
    if codigo in ROLE_PERMISSIONS or db.scalar(select(AcessoInstrumento.id).where(AcessoInstrumento.papel == codigo).limit(1)):
        row.ativo = False
        preservar_administrador(db, admin_antes)
        db.commit()
        return {"status": "desativado"}
    db.delete(row)
    preservar_administrador(db, admin_antes)
    db.commit()
    return {"status": "excluido"}


def validar_perfil(db, codigo):
    row = db.get(Papel, codigo)
    if not row or not row.ativo:
        raise HTTPException(422, "Perfil inexistente ou inativo.")


def usuario_out(row):
    return {"id": str(row.id), "nome": row.nome, "username": row.username, "email": row.email,
            "ativo":row.ativo, "criado_em": row.criado_em}


def listar_usuarios(db, q, limit, offset, papel=None, ativo=None, nome="", username="", email="", cpf=""):
    require(db, "usuarios_consultar")
    query = select(Usuario).where(Usuario.excluido_em.is_(None), or_(
        Usuario.nome.ilike("%" + q + "%"), Usuario.email.ilike("%" + q + "%"),
        Usuario.username.ilike("%" + q + "%"), Usuario.cpf.ilike("%" + q.replace(".", "").replace("-", "") + "%")))
    if ativo is not None:
        query = query.where(Usuario.ativo == ativo)
    for column, value in [(Usuario.nome, nome), (Usuario.username, username), (Usuario.email, email),
                          (Usuario.cpf, cpf.replace(".", "").replace("-", ""))]:
        if value:
            query = query.where(column.ilike("%" + value + "%"))
    if papel:
        query = query.where(exists(select(AcessoInstrumento.id).where(
            AcessoInstrumento.usuario_id == Usuario.id, AcessoInstrumento.papel == papel)))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = list(db.scalars(query.order_by(Usuario.nome, Usuario.id).limit(limit).offset(offset)))
    from app.services.usuario_service import resumos_acessos
    access = resumos_acessos(db, [u.id for u in rows])
    return {"items": [{**usuario_out(u), **access[u.id],
                      "tem_acesso": bool(u.ativo and access[u.id]["tem_acesso"])} for u in rows],
            "total": total, "limit": limit, "offset": offset}
