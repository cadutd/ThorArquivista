"""Recover a record creation whose Mongo write succeeded before SQL finalization."""
import argparse
import uuid
from datetime import UTC, datetime, timedelta
from sqlalchemy import select
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.models.conformidade import AuditoriaGeral
from app.models.instrumento import Instrumento
from app.models.user import Usuario
from app.services.auditoria_service import registrar
from app.services.editorial_service import controle


def reconciliar(db, operacao_id):
    intent = db.scalar(select(AuditoriaGeral).where(AuditoriaGeral.operacao_id == operacao_id,
                        AuditoriaGeral.acao == "CRIAR_REGISTRO_INTENCAO"))
    if not intent or intent.criado_em > datetime.now(UTC) - timedelta(minutes=10):
        raise ValueError("Intencao ausente ou recente (aguarde 10 minutos).")
    db.scalar(select(Instrumento).where(Instrumento.id == intent.instrumento_id).with_for_update())
    if db.scalar(select(AuditoriaGeral.id).where(AuditoriaGeral.operacao_id == operacao_id,
        AuditoriaGeral.acao.in_(["CRIAR_REGISTRO_CONCLUIDO", "CANCELAR_CRIACAO_REGISTRO"])).limit(1)):
        return
    doc = registros_collection().find_one({"_id": intent.registro_id, "instrumento_id": str(intent.instrumento_id)})
    user = db.get(Usuario, intent.usuario_id)
    db.info["usuario"] = user
    if doc:
        controle(db, intent.instrumento_id, intent.registro_id, doc)
    registrar(db, "CRIAR_REGISTRO_CONCLUIDO" if doc else "CANCELAR_CRIACAO_REGISTRO", "registro",
        intent.registro_id, intent.instrumento_id, intent.registro_id,
        {"etapa": "RECONCILIADA", "executor": "conformidade_cli"}, operacao_id=operacao_id)
    db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operacao_id", type=uuid.UUID)
    args = parser.parse_args()
    with SessionLocal() as db:
        reconciliar(db, args.operacao_id)
