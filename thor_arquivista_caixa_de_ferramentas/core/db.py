# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
# Copyright (C) 2025  Carlos Eduardo Carvalho Amand
#
# Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU GPL), conforme publicada
# pela Free Software Foundation, na versão 3 da Licença, ou (a seu critério)
# qualquer versão posterior.
#
# Este programa é distribuído na esperança de que seja útil,
# mas SEM QUALQUER GARANTIA; sem mesmo a garantia implícita de
# COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM PROPÓSITO PARTICULAR.
# Veja a Licença Pública Geral GNU para mais detalhes.
#
# Você deve ter recebido uma cópia da GNU GPL junto com este programa.
# Caso contrário, veja <https://www.gnu.org/licenses/>.

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
from pymongo import MongoClient
from datetime import datetime, timezone

@dataclass
class DbCtx:
    client: MongoClient
    dbname: str

    @property
    def db(self):
        return self.client[self.dbname]

def connect(uri: str, dbname: str) -> DbCtx:
    client = MongoClient(uri)
    return DbCtx(client=client, dbname=dbname)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def insert_job(ctx: DbCtx, job: Dict[str, Any]) -> str:
    job["created_at"] = now_iso()
    job["status"] = job.get("status","queued")
    r = ctx.db.jobs.insert_one(job)
    return str(r.inserted_id)

def update_job(ctx: DbCtx, job_id: Any, patch: Dict[str, Any]) -> None:
    ctx.db.jobs.update_one({"_id": job_id}, {"$set": patch})

def append_log(ctx: DbCtx, job_id: Any, line: str) -> None:
    ctx.db.job_logs.insert_one({"job_id": job_id, "at": now_iso(), "line": line})

def list_jobs(ctx: DbCtx, limit: int = 50):
    return list(ctx.db.jobs.find().sort("created_at", -1).limit(limit))

def list_job_logs(ctx: DbCtx, job_id: Any, limit: int = 500):
    return list(ctx.db.job_logs.find({"job_id": job_id}).sort("at", 1).limit(limit))
