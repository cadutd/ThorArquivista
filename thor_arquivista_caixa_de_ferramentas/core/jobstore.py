from __future__ import annotations

import json
import uuid
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


ISO = "%Y-%m-%dT%H:%M:%S.%fZ"


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

    def __init__(self, path: str | Path = "./jobs_db.json"):
        self.path = str(path)
        self._lock = threading.Lock()
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
        level = level.upper()
        if level not in ("INFO", "ERROR", "WARN", "WARNING", "DEBUG"):
            level = "INFO"
        with self._locked_rw(self) as db:
            logs = db["logs"].setdefault(job_id, [])
            logs.append({"ts": _now_iso(), "level": level, "msg": str(msg)})

    def get_logs(self, job_id: str) -> List[Dict[str, str]]:
        with self._locked_ro(self) as db:
            return list(db["logs"].get(job_id, []))

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
    def _ensure_file(self) -> None:
        p = Path(self.path)
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            data = {"jobs": [], "logs": {}}
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(p)

        # valida estrutura básica
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if "jobs" not in data or "logs" not in data:
                raise ValueError("arquivo inválido")
        except Exception:
            data = {"jobs": [], "logs": {}}
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(p)

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
            tmp = p.with_suffix(p.suffix + ".tmp")
            try:
                tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(p)
            finally:
                self.outer._lock.release()

    @staticmethod
    def _find_job(db: Dict[str, Any], job_id: str) -> Optional[Dict[str, Any]]:
        for j in db.get("jobs", []):
            if j.get("_id") == job_id:
                return j
        return None
