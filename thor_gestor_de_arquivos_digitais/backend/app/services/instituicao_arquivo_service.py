from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.instituicao_arquivo import InstituicaoArquivo
from app.schemas.instituicao_arquivo import InstituicaoArquivoCreate, InstituicaoArquivoUpdate


class InstituicaoArquivoService:
    @staticmethod
    def obter(db: Session) -> InstituicaoArquivo | None:
        return db.query(InstituicaoArquivo).order_by(InstituicaoArquivo.criada_em.asc()).first()

    @staticmethod
    def criar(db: Session, dados: InstituicaoArquivoCreate) -> InstituicaoArquivo:
        if InstituicaoArquivoService.obter(db):
            raise ValueError("Já existe uma Instituição de Arquivo cadastrada.")

        instituicao = InstituicaoArquivo(**dados.model_dump(), singleton_key=True)
        db.add(instituicao)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Já existe uma Instituição de Arquivo cadastrada.")
        db.refresh(instituicao)
        return instituicao

    @staticmethod
    def atualizar(db: Session, dados: InstituicaoArquivoUpdate) -> InstituicaoArquivo | None:
        instituicao = InstituicaoArquivoService.obter(db)
        if not instituicao:
            return None

        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(instituicao, campo, valor)

        db.commit()
        db.refresh(instituicao)
        return instituicao

    @staticmethod
    def excluir(db: Session) -> bool:
        instituicao = InstituicaoArquivoService.obter(db)
        if not instituicao:
            return False

        db.delete(instituicao)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "A instituição não pode ser removida porque está vinculada a outros registros."
            )
        return True
