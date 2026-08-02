# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
# Copyright (C) 2025  Carlos Eduardo Carvalho Amand
#
# Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral Affero GNU (GNU AGPL), conforme publicada
# pela Free Software Foundation, na versão 3 da Licença, ou (a seu critério)
# qualquer versão posterior.
#
# Este programa é distribuído na esperança de que seja útil,
# mas SEM QUALQUER GARANTIA; sem mesmo a garantia implícita de
# COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM PROPÓSITO PARTICULAR.
# Veja a Licença Pública Geral Affero GNU para mais detalhes.
#
# Você deve ter recebido uma cópia da GNU AGPL junto com este programa.
# Caso contrário, veja <https://www.gnu.org/licenses/>.

from __future__ import annotations

import json
import uuid
import threading
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


ISO = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_MAX_LOGS_PER_JOB = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO)


class JobStore:
    """
    JobStore em arquivo JSON (portável, thread-safe).

    Estrutura:
      {
        "jobs": [ { _id, job_type, status, params, created_at, updated_at, error_msg? }, ... ],
        "logs": { "<_id>": [ { ts, level, msg }, ... ] }
      }

    Status possíveis:
      - pending   : aguardando execução
      - running   : em execução (marcado por pop_next_pending)
      - done      : concluído com sucesso
      - error     : finalizado com erro
      - canceled  : cancelado pelo usuário (apenas se estava pending)
    """

    def __init__(self, path: str | Path = "./jobs_db.json", *, max_logs_per_job: int = DEFAULT_MAX_LOGS_PER_JOB):
        self.path = str(path)
        self.max_logs_per_job = max(100, int(max_logs_per_job))
        self._lock = self._get_path_lock(path)
        self._ensure_file()

    # ------------- API pública -------------
    def add_job(self, job_type: str, params: Dict[str, Any]) -> str:
        with self._locked_rw(self) as db:
            jid = str(uuid.uuid4())
            now = _now_iso()
            job = {
                "_id": jid,
                "job_type": job_type,
                "status": "pending",
                "params": params or {},
                "created_at": now,
                "updated_at": now,
                "error_msg": None,
            }
            db["jobs"].append(job)
            db["logs"].setdefault(jid, [])
            return jid

    def add_log(self, job_id: str, msg: str, level: str = "INFO") -> None:
        self.add_logs(job_id, [(msg, level)])

    def add_logs(self, job_id: str, entries: List[tuple[str, str]]) -> None:
        if not entries:
            return
        now = _now_iso()
        normalized = []
        for msg, level in entries:
            level = level.upper()
            if level not in ("INFO", "ERROR", "WARN", "WARNING", "DEBUG"):
                level = "INFO"
            normalized.append({"ts": now, "level": level, "msg": str(msg)})
        with self._locked_rw(self) as db:
            logs = db["logs"].setdefault(job_id, [])
            logs.extend(normalized)
            self._trim_logs(db)

    def get_logs(self, job_id: str) -> List[Dict[str, str]]:
        with self._locked_ro(self) as db:
            return list(db["logs"].get(job_id, []))

    def get_job_status(self, job_id: str) -> Optional[str]:
        with self._locked_ro(self) as db:
            job = self._find_job(db, job_id)
            return str(job.get("status")) if job else None

    def get_job_status_and_logs(self, job_id: str) -> tuple[Optional[str], List[Dict[str, str]]]:
        with self._locked_ro(self) as db:
            job = self._find_job(db, job_id)
            status = str(job.get("status")) if job else None
            logs = list(db["logs"].get(job_id, []))
            return status, logs

    def set_status(self, job_id: str, status: str, *, error_msg: Optional[str] = None) -> bool:
        if status not in ("pending", "running", "done", "error", "canceled"):
            raise ValueError(f"status inválido: {status}")
        with self._locked_rw(self) as db:
            job = self._find_job(db, job_id)
            if not job:
                return False
            job["status"] = status
            job["updated_at"] = _now_iso()
            job["error_msg"] = (error_msg or None)
            return True

    def pop_next_pending(self) -> Optional[Dict[str, Any]]:
        """
        Retorna e marca como 'running' o job 'pending' mais antigo.
        Se não houver pendentes, retorna None.
        """
        with self._locked_rw(self) as db:
            jobs = db["jobs"]
            pendentes = [j for j in jobs if j["status"] == "pending"]
            if not pendentes:
                return None
            pendentes.sort(key=lambda j: j.get("created_at", ""))
            job = pendentes[0]
            job["status"] = "running"
            job["updated_at"] = _now_iso()
            return dict(job)  # cópia para o worker

    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._locked_ro(self) as db:
            items = db["jobs"]
            if status:
                items = [j for j in items if j.get("status") == status]
            return sorted(items, key=lambda j: j.get("created_at", ""), reverse=True)

    def counts_by_status(self) -> Dict[str, int]:
        with self._locked_ro(self) as db:
            counts: Dict[str, int] = {"pending": 0, "running": 0, "done": 0, "error": 0, "canceled": 0}
            for j in db["jobs"]:
                st = j.get("status")
                if st in counts:
                    counts[st] += 1
            return counts

    def clear_by_status(self, status: str) -> int:
        """
        Remove permanentemente jobs com determinado status.
        Retorna a quantidade removida. Também remove os logs desses jobs.
        """
        if status not in ("pending", "running", "done", "error", "canceled"):
            raise ValueError(f"status inválido: {status}")
        with self._locked_rw(self) as db:
            before = len(db["jobs"])
            to_remove_ids = {j["_id"] for j in db["jobs"] if j.get("status") == status}
            db["jobs"] = [j for j in db["jobs"] if j["_id"] not in to_remove_ids]
            for jid in to_remove_ids:
                db["logs"].pop(jid, None)
            return before - len(db["jobs"])

    def requeue_from_status(self, status: str) -> int:
        """
        Move jobs de um status para 'pending'.
        Útil para reenfileirar 'error', 'done' ou 'canceled'.
        Retorna quantos foram alterados.
        """
        if status not in ("error", "done", "canceled", "running", "pending"):
            raise ValueError(f"status inválido para requeue: {status}")
        with self._locked_rw(self) as db:
            n = 0
            for j in db["jobs"]:
                if j.get("status") == status:
                    j["status"] = "pending"
                    j["updated_at"] = _now_iso()
                    j["error_msg"] = None
                    n += 1
            return n

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancela um job se estiver 'pending'.
        (Não cancela 'running' para evitar corrupção.)
        """
        with self._locked_rw(self) as db:
            job = self._find_job(db, job_id)
            if not job:
                return False
            if job["status"] != "pending":
                return False
            job["status"] = "canceled"
            job["updated_at"] = _now_iso()
            return True

    # ------------- Internos -------------
    _locks_guard = threading.Lock()
    _locks_by_path: Dict[str, threading.RLock] = {}

    @classmethod
    def _get_path_lock(cls, path: str | Path) -> threading.RLock:
        key = str(Path(path).resolve())
        with cls._locks_guard:
            lock = cls._locks_by_path.get(key)
            if lock is None:
                lock = threading.RLock()
                cls._locks_by_path[key] = lock
            return lock

    @staticmethod
    def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            for attempt in range(8):
                try:
                    tmp.replace(path)
                    return
                except PermissionError:
                    if attempt == 7:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except PermissionError:
                    pass

    def _trim_logs(self, db: Dict[str, Any]) -> None:
        logs_by_job = db.get("logs")
        if not isinstance(logs_by_job, dict):
            db["logs"] = {}
            return
        for logs in logs_by_job.values():
            if isinstance(logs, list) and len(logs) > self.max_logs_per_job:
                del logs[: len(logs) - self.max_logs_per_job]

    def _ensure_file(self) -> None:
        p = Path(self.path)
        with self._lock:
            if not p.exists():
                self._atomic_write_json(p, {"jobs": [], "logs": {}})

            # valida estrutura básica
            try:
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if "jobs" not in data or "logs" not in data:
                    raise ValueError("arquivo inválido")
            except Exception:
                self._atomic_write_json(p, {"jobs": [], "logs": {}})

    class _locked_ro:
        def __init__(self, outer: "JobStore"):
            self.outer = outer
            self._data = None

        def __enter__(self):
            self.outer._lock.acquire()
            try:
                with Path(self.outer.path).open("r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {"jobs": [], "logs": {}}
            return self._data

        def __exit__(self, exc_type, exc, tb):
            self.outer._lock.release()

    class _locked_rw:
        def __init__(self, outer: "JobStore"):
            self.outer = outer
            self._data = None

        def __enter__(self):
            self.outer._lock.acquire()
            try:
                with Path(self.outer.path).open("r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {"jobs": [], "logs": {}}
            return self._data

        def __exit__(self, exc_type, exc, tb):
            # gravação atômica
            p = Path(self.outer.path)
            try:
                self.outer._trim_logs(self._data)
                self.outer._atomic_write_json(p, self._data)
            finally:
                self.outer._lock.release()

    @staticmethod
    def _find_job(db: Dict[str, Any], job_id: str) -> Optional[Dict[str, Any]]:
        for j in db.get("jobs", []):
            if j.get("_id") == job_id:
                return j
        return None
