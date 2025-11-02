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
from typing import Dict, Any, Optional
import threading, queue, subprocess, sys, shlex
from pathlib import Path
from .db import DbCtx, insert_job, update_job, append_log
from datetime import datetime, timezone

JOB_TYPES = [
    "HASH_MANIFEST",
    "VERIFY_FIXITY",
    "BUILD_BAG",
    "BUILD_SIP",
    "FORMAT_IDENTIFY",
    "REPLICATE",
    "PREMIS_EVENT",
]

@dataclass
class Job:
    type: str
    params: Dict[str, Any]
    _id: Optional[Any] = None

class JobRunner:
    def __init__(self, ctx: DbCtx, scripts_dir: Path, premis_log: Optional[Path] = None, premis_agent: str = "Orquestração"):
        self.ctx = ctx
        self.scripts = scripts_dir
        self.premis_log = premis_log
        self.premis_agent = premis_agent
        self.q: "queue.Queue[Job]" = queue.Queue()
        self._stop = threading.Event()
        self.worker = threading.Thread(target=self._loop, daemon=True)
        self.worker.start()

    def enqueue(self, job: Job) -> Any:
        jid = insert_job(self.ctx, {"type": job.type, "params": job.params})
        job._id = jid
        self.q.put(job)
        return jid

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            try:
                job: Job = self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            self._process(job)

    def _log(self, job: Job, line: str):
        try:
            append_log(self.ctx, job._id, line)
        except Exception:
            pass

    def _set_status(self, job: Job, status: str, extra: Optional[Dict[str, Any]] = None):
        patch = {"status": status}
        if extra:
            patch.update(extra)
        try:
            self.ctx.db.jobs.update_one({"_id": job._id}, {"$set": patch})
        except Exception:
            pass

    def _proc(self, cmd: str, cwd: Optional[Path] = None, job: Optional[Job] = None) -> int:
        p = subprocess.Popen(shlex.split(cmd), cwd=str(cwd) if cwd else None,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            sys.stdout.write(line)
            if job:
                self._log(job, line.rstrip())
        return p.wait()

    def _emit_premis(self, job: Job, outcome: str, detail: str = ""):
        if not self.premis_log:
            return
        # Map job type -> eventType + obj-id heuristic
        mapping = {
            "HASH_MANIFEST": ("message digest calculation", job.params.get("saida", job.params.get("raiz",""))),
            "VERIFY_FIXITY": ("fixity check", job.params.get("manifesto","")),
            "BUILD_BAG": ("packaging", job.params.get("bag_name", job.params.get("destino",""))),
            "BUILD_SIP": ("ingestion preparation", job.params.get("sip_id", job.params.get("saida",""))),
            "FORMAT_IDENTIFY": ("format identification", job.params.get("raiz","")),
            "REPLICATE": ("replication", job.params.get("fonte","")),
            # PREMIS_EVENT is user-driven, we don't re-emit
        }
        evt_type, obj_id = mapping.get(job.type, ("processing", ""))
        cmd = f"python {self.scripts.as_posix()}/premis_log.py --arquivo-log {shlex.quote(str(self.premis_log))} --tipo {shlex.quote(evt_type)} --obj-id {shlex.quote(str(obj_id))} --detalhe {shlex.quote(detail)} --resultado {shlex.quote(outcome)} --agente {shlex.quote(self.premis_agent)}"
        try:
            self._proc(cmd, job=job)
        except Exception as e:
            self._log(job, f"[PREMIS-ERROR] {e}")

    def _process(self, job: Job):
        self._set_status(job, "running", {"started_at": datetime.now(timezone.utc).isoformat()})
        try:
            code = self._dispatch(job)
            status = "success" if code == 0 else "failure"
            self._set_status(job, status, {"finished_at": datetime.now(timezone.utc).isoformat(), "exit_code": code})
            self._emit_premis(job, outcome=status, detail=f"Exit code {code}")
        except Exception as e:
            self._log(job, f"[EXCEPTION] {e}")
            self._set_status(job, "failure", {"finished_at": datetime.now(timezone.utc).isoformat(), "error": str(e)})
            self._emit_premis(job, outcome="failure", detail=str(e))

    # --- Dispatch to scripts ---
    def _dispatch(self, job: Job) -> int:
        sdir = self.scripts.as_posix()
        t = job.type
        p = job.params
        if t == "HASH_MANIFEST":
            cmd = f"python {sdir}/hash_files.py --raiz {shlex.quote(p['raiz'])} --saida {shlex.quote(p['saida'])}"
            return self._proc(cmd, job=job)
        if t == "VERIFY_FIXITY":
            cmd = f"python {sdir}/verify_fixity.py --raiz {shlex.quote(p['raiz'])} --manifesto {shlex.quote(p['manifesto'])}"
            return self._proc(cmd, job=job)
        if t == "BUILD_BAG":
            org = shlex.quote(p.get('org','APESP'))
            cmd = f"python {sdir}/build_bag.py --fonte {shlex.quote(p['fonte'])} --destino {shlex.quote(p['destino'])} --bag-name {shlex.quote(p['bag_name'])} --org {org}"
            return self._proc(cmd, job=job)
        if t == "BUILD_SIP":
            zipflag = "--zip" if p.get("zip_out") else "--no-zip"
            cmd = f"python {sdir}/build_sip.py --fonte {shlex.quote(p['fonte'])} --saida {shlex.quote(p['saida'])} --sip-id {shlex.quote(p['sip_id'])} {zipflag}"
            return self._proc(cmd, job=job)
        if t == "FORMAT_IDENTIFY":
            out = f"--saida {shlex.quote(p['saida'])}" if p.get("saida") else ""
            cmd = f"python {sdir}/format_identify.py --raiz {shlex.quote(p['raiz'])} {out}"
            return self._proc(cmd, job=job)
        if t == "REPLICATE":
            cmd = f"python {sdir}/replicate_storage.py --fonte {shlex.quote(p['fonte'])} " + " ".join([f"--destino {shlex.quote(d)}" for d in p['destinos']])
            if p.get("verificar_hash"):
                cmd += " --verificar-hash"
            return self._proc(cmd, job=job)
        if t == "PREMIS_EVENT":
            cmd = f"python {sdir}/premis_log.py --arquivo-log {shlex.quote(p['arquivo_log'])} --tipo {shlex.quote(p['tipo'])} --obj-id {shlex.quote(p['obj_id'])} --detalhe {shlex.quote(p.get('detalhe',''))} --resultado {shlex.quote(p.get('resultado','success'))} --agente {shlex.quote(p.get('agente','Sistema'))}"
            return self._proc(cmd, job=job)
        raise ValueError(f"Tipo de job não suportado: {t}")
