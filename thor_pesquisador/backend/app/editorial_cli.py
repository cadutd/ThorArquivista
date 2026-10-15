"""Explicit administrator provisioning and resumable reconciliation, never implicit publication."""
import argparse
import uuid
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.mongo import registros_collection
from app.models.user import Usuario
from app.models.editorial import AcessoInstrumento, PublicacaoImagem
from app.models.instrumento import Instrumento, IndexacaoJob
from app.services.editorial_service import controle, invalidar_publicacao
from app.schemas.usuario import UsuarioIn
from app.models.editorial import Papel
from sqlalchemy.exc import IntegrityError
from app.services.permissao_service import bloquear_administracao, ha_administrador


def cadastrar_admin_inicial(db, payload):
    bloquear_administracao(db)
    existing = ha_administrador(db)
    if existing:
        raise ValueError("Ja existe administrador ativo. Utilize o CRUD de usuarios.")
    row = Usuario(**payload.model_dump())
    try:
        db.add(row)
        db.flush()
        db.add(AcessoInstrumento(usuario_id=row.id, papel="ADMIN", origem="MANUAL"))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("CPF ou usuario ja cadastrado; regularize o cadastro existente.") from exc
    return row


def backfill(db, after="", limit=100, instrumento_id=None):
    query = {"_id": {"$gt": after}}
    if instrumento_id is not None:
        query["instrumento_id"] = str(instrumento_id)
    docs = list(registros_collection().find(query).sort("_id", 1).limit(limit))
    for doc in docs:
        try:
            instrumento_id = uuid.UUID(doc["instrumento_id"])
        except (ValueError, KeyError):
            raise RuntimeError("Registro legado com instrumento invalido; corrija antes de continuar.")
        instrumento = db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
        if not instrumento:
            raise RuntimeError("Registro legado sem instrumento; corrija antes de continuar.")
        row = controle(db, instrumento_id, doc["_id"], doc)
        revision = doc.get("_revision", 1)
        if row.versao != revision or row.status_operacional != doc["status"]:
            row.versao = max(row.versao, revision)
            # A persisted revocation wins over a failed Mongo update.
            if row.status_operacional in {"INATIVO", "EXCLUIDO"}:
                registros_collection().update_one({"_id": doc["_id"]},
                    {"$set": {"status": row.status_operacional}})
            else:
                row.status_operacional = doc["status"]
            row.status_editorial = "RASCUNHO"
            invalidar_publicacao(db, instrumento)
        registros_collection().update_one({"_id": doc["_id"]},
                                         {"$set": {"_revision": row.versao}})
        db.commit()
    return docs[-1]["_id"] if docs else None


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    admin = sub.add_parser("grant-admin")
    admin.add_argument("--govbr-sub", required=True)
    initial = sub.add_parser("register-admin")
    for argument in ("nome", "username", "cpf", "email"):
        initial.add_argument("--" + argument, required=True)
    batch = sub.add_parser("backfill")
    batch.add_argument("--after", default="")
    batch.add_argument("--limit", type=int, default=100)
    batch.add_argument("--instrumento-id", type=uuid.UUID)
    sub.add_parser("retry-public-index")
    sub.add_parser("backfill-public-images")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == "register-admin":
            try:
                payload = UsuarioIn(nome=args.nome, username=args.username, cpf=args.cpf,
                                    email=args.email)
                cadastrar_admin_inicial(db, payload)
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
            print("Administrador cadastrado. O primeiro login gov.br sera vinculado pelo CPF.")
        elif args.command == "grant-admin":
            user = db.scalar(select(Usuario).where(Usuario.govbr_sub == args.govbr_sub))
            if not user:
                raise SystemExit("Usuario deve ser cadastrado antes do provisionamento.")
            if not user.ativo or user.excluido_em:
                raise SystemExit("Usuario deve estar ativo.")
            existing = db.scalar(select(AcessoInstrumento.id).where(AcessoInstrumento.usuario_id == user.id,
                AcessoInstrumento.papel == "ADMIN", AcessoInstrumento.instrumento_id.is_(None)))
            if not existing:
                db.add(AcessoInstrumento(usuario_id=user.id, papel="ADMIN"))
                db.commit()
            print("Administrador provisionado explicitamente.")
        elif args.command == "backfill":
            if not 1 <= args.limit <= 1000:
                raise SystemExit("Limite deve estar entre 1 e 1000.")
            print({"ultimo_cursor": backfill(db, args.after, args.limit, args.instrumento_id)})
        elif args.command == "backfill-public-images":
            from app.db.mongo import snapshots_collection
            rows = list(db.scalars(select(PublicacaoImagem).where(PublicacaoImagem.referencia == {}).limit(100)))
            snapshots = {s["_id"]: s for s in snapshots_collection().find({"_id": {"$in": [r.snapshot_id for r in rows]}},
                                                                          {"imagens": 1})}
            count = 0
            for row in rows:
                ref = next((v for v in snapshots.get(row.snapshot_id, {}).get("imagens", [])
                            if v["imagem_id"] == str(row.imagem_id)), None)
                if ref:
                    row.referencia = ref
                    count += 1
            db.commit()
            print({"referencias_recuperadas": count, "pendentes_no_lote": len(rows) - count})
        else:
            count = db.query(IndexacaoJob).filter(IndexacaoJob.tipo == "PUBLICACAO",
                IndexacaoJob.status == "FALHOU").update({"status": "PENDENTE", "erro": None})
            db.commit()
            print({"jobs_reagendados": count})


if __name__ == "__main__":
    main()
