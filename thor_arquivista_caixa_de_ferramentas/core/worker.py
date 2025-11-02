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

# core/worker.py
from __future__ import annotations

import sys
import subprocess
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple,  List, Optional

from core.config import AppConfig
from core.jobstore import JobStore
from core.scripts_map import get_scripts_map
from negocio.premis import append_event, event_type_for_job, guess_object_id


class Worker:
    """
    Worker de fila local (JobStore JSON), que:
      - consome jobs 'pending'
      - executa scripts via subprocess
      - registra logs no JobStore e eventos PREMIS no JSONL

    Agora com APIs de gestão de fila:
      - pause()/resume()/is_paused()
      - clear_pending()
      - requeue_errors()
      - requeue_all()
      - cancel_job(job_id)
      - list_jobs(status=None)
      - counts_by_status()
    """

    def __init__(self, cfg: AppConfig, jobstore: JobStore):
        self.cfg = cfg
        self.jobstore = jobstore
        self._stop_event = threading.Event()
#        self._thread: threading.Thread | None = None
        self._pause_event = threading.Event()
        self._pause_event.clear()  # não pausado por padrão
        self._thread: Optional[threading.Thread] = None

        # Carrega o mapeamento de scripts de um módulo separado
        self._scripts = get_scripts_map()

    # ---------------- Lifecycle ----------------
    def start(self, *, daemon: bool = True) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=daemon)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def join(self, timeout: float | None = None) -> None:
        if self._thread:
            self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    # ---------------- Pause/Resume ----------------
    def pause(self) -> None:
        self._pause_event.set()

    def resume(self) -> None:
        self._pause_event.clear()

    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    # ---------------- Queue management ----------------
    def list_jobs(self, status: str | None = None) -> List[Dict[str, Any]]:
        """Lista jobs; se status for informado, filtra por ele."""
        return self.jobstore.list_jobs(status=status)

    def counts_by_status(self) -> Dict[str, int]:
        return self.jobstore.counts_by_status()

    def clear_pending(self) -> int:
        """Remove todos os jobs 'pending'. Retorna quantos removeu."""
        return self.jobstore.clear_by_status('pending')

    def clear_done(self) -> int:
        """Remove todos os jobs 'done'. Retorna quantos removeu."""
        return self.jobstore.clear_by_status('done')

    def clear_error(self) -> int:
        """Remove todos os jobs 'error'. Retorna quantos removeu."""
        return self.jobstore.clear_by_status('error')

    def requeue_errors(self) -> int:
        """Muda jobs 'error' para 'pending'. Retorna quantos alterou."""
        return self.jobstore.requeue_from_status('error')

    def requeue_all(self) -> int:
        """Reenfileira jobs com status em ['error','done','canceled'] para 'pending'."""
        n = 0
        for st in ('error', 'done', 'canceled'):
            n += self.jobstore.requeue_from_status(st)
        return n

    def cancel_job(self, job_id: str) -> bool:
        """Cancela um job (se estiver pending, marca como canceled)."""
        return self.jobstore.cancel_job(job_id)

    # ---------------- Internals ----------------
    def _loop(self) -> None:
        while not self._stop_event.is_set():
            # respeita pausa
            if self._pause_event.is_set():
                self._stop_event.wait(0.3)
                continue

            job = self.jobstore.pop_next_pending()
            if not job:
                self._stop_event.wait(0.5)
                continue

            jid = job["_id"]
            jtype = job["job_type"]
            params = job.get("params", {})
            self.jobstore.add_log(jid, f"Iniciando job {jtype}")

            try:
                rc, out, err = self._execute(jtype, params)

                if out:
                    self.jobstore.add_log(jid, out[:2000])
                if err:
                    self.jobstore.add_log(jid, err[:2000], level="ERROR" if rc else "INFO")

                if jtype != "PREMIS_EVENT":
                    append_event(
                        Path(self.cfg.premis_log),
                        {
                            "eventIdentifier": f"local-{jtype}-{datetime.utcnow().isoformat()}",
                            "eventType": event_type_for_job(jtype),
                            "eventDateTime": datetime.utcnow().isoformat() + "Z",
                            "eventDetail": f"Exit code {rc}",
                            "eventOutcome": "success" if rc == 0 else "failure",
                            "linkingObjectIdentifier": guess_object_id(jtype, params),
                            "linkingAgentName": self.cfg.premis_agent or "Gerenciador",
                        },
                    )

                if rc == 0:
                    self.jobstore.add_log(jid, "Concluído com sucesso")
                    self.jobstore.set_status(jid, "done")
                else:
                    self.jobstore.add_log(jid, f"Erro (rc={rc})", level="ERROR")
                    self.jobstore.set_status(jid, "error", error_msg=(err or "")[:500])

            except Exception as e:
                traceback.print_exc()
                self.jobstore.add_log(jid, f"Falha inesperada: {e}", level="ERROR")
                self.jobstore.set_status(jid, "error", error_msg=str(e)[:500])

    def _execute(self, job_type: str, params: Dict[str, Any]) -> tuple[int, str, str]:
        if job_type not in self._scripts:
            return 1, "", f"Job não suportado: {job_type}"

        script_name, arg_builder = self._scripts[job_type]
        args = arg_builder(params, self.cfg)  # builder recebe (params, cfg)
        cmd = [sys.executable, str(Path(self.cfg.scripts_dir) / script_name)] + args
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr