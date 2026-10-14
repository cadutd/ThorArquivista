import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import current_user, db_dep
from app.schemas.administracao import PerfilIn
from app.schemas.usuario import UsuarioIn
from app.services import usuario_service
from app.services import administracao_service as service
from app.services.permissao_service import require

router = APIRouter(dependencies=[Depends(current_user)])


@router.get("/perfis")
def perfis(q: str = "", ativo: bool | None = None, limit: int = Query(20, ge=1, le=100),
           offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    return service.listar_perfis(db, q, ativo, limit, offset)


@router.post("/perfis", status_code=201)
def criar(payload: PerfilIn, db: Session = Depends(db_dep)):
    return service.salvar_perfil(db, payload)


@router.get("/perfis/{codigo}")
def perfil(codigo: str, db: Session = Depends(db_dep)):
    return service.perfil_out(service.obter_perfil(db, codigo))


@router.put("/perfis/{codigo}")
def editar(codigo: str, payload: PerfilIn, db: Session = Depends(db_dep)):
    return service.salvar_perfil(db, payload, codigo)


@router.delete("/perfis/{codigo}")
def excluir(codigo: str, db: Session = Depends(db_dep)):
    return service.excluir_perfil(db, codigo)


@router.get("/usuarios/{usuario_id}")
def usuario(usuario_id: uuid.UUID, db: Session = Depends(db_dep)):
    return usuario_service.dados(db, usuario_service.obter(db, usuario_id))


@router.post("/usuarios", status_code=201)
def criar_usuario(payload: UsuarioIn, db: Session = Depends(db_dep)):
    return usuario_service.salvar(db, payload)


@router.put("/usuarios/{usuario_id}")
def editar_usuario(usuario_id: uuid.UUID, payload: UsuarioIn, db: Session = Depends(db_dep)):
    return usuario_service.salvar(db, payload, usuario_id)


@router.delete("/usuarios/{usuario_id}")
def excluir_usuario(usuario_id: uuid.UUID, db: Session = Depends(db_dep)):
    return usuario_service.excluir(db, usuario_id)


@router.get("/permissoes")
def permissoes(q: str = "", modulo: str = "", funcao: str = "", acao: str = "",
               limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
               db: Session = Depends(db_dep)):
    require(db, "permissoes_consultar")
    rows = [p for p in service.PERMISSIONS if
            q.casefold() in (p["codigo"] + " " + p["nome"]).casefold() and
            modulo.casefold() in p["modulo"].casefold() and funcao.casefold() in p["funcao"].casefold() and
            (not acao or p["acao"] == acao)]
    return {"items": rows[offset:offset + limit], "total": len(rows), "limit": limit, "offset": offset}
