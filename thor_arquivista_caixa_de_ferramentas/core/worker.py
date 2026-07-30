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
import time
from collections import deque
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional, Deque

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
      - clear_running()
      - requeue_errors()
      - requeue_all()
      - cancel_job(job_id)
      - list_jobs(status=None)
      - counts_by_status()

    E com 'streaming' de saída:
      - stdout/stderr são lidos linha a linha e gravados em JobStore.add_log()
        durante a execução do job.
    """

    def __init__(self, cfg: AppConfig, jobstore: JobStore):
        self.cfg = cfg
        self.jobstore = jobstore
        self._stop_event = threading.Event()
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

    def clear_running(self) -> int:
        """Remove todos os jobs 'running'. Retorna quantos removeu."""
        return self.jobstore.clear_by_status('running')

    def clear_done(self) -> int:
        """Remove todos os jobs 'done'. Retorna quantos removeu."""
        return self.jobstore.clear_by_status('done')

    def clear_error(self) -> int:
        """Remove todos os jobs 'error'. Retorna quantos removeu."""
        return self.jobstore.clear_by_status('error')

    def clear_canceled(self) -> int:
        """Remove todos os jobs 'canceled'. Retorna quantos removeu."""
        return self.jobstore.clear_by_status('canceled')

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
                # _execute agora recebe o ID do job para poder logar em tempo real
                rc, out, err = self._execute(jid, jtype, params)

                # logs resumidos finais (últimas linhas). Registra stderr antes de
                # stdout para o relatório final do script ficar mais visível no tail.
                if err:
                    self.jobstore.add_log(
                        jid,
                        f"[stderr] (últimas linhas)\n{err[-4000:]}",
                        level="ERROR" if rc else "INFO",
                    )
                if out:
                    self.jobstore.add_log(
                        jid,
                        f"[stdout] (relatório final)\n{out[-4000:]}",
                    )

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
                    # usa stderr resumido como mensagem de erro, se houver
                    err_msg = (err or out or "")[:500]
                    self.jobstore.set_status(jid, "error", error_msg=err_msg)

            except Exception as e:
                traceback.print_exc()
                self.jobstore.add_log(jid, f"Falha inesperada: {e}", level="ERROR")
                self.jobstore.set_status(jid, "error", error_msg=str(e)[:500])

    def _execute(self, job_id: str, job_type: str, params: Dict[str, Any]) -> tuple[int, str, str]:
        """
        Executa o script correspondente ao job_type, fazendo streaming de stdout/stderr
        para o JobStore em tempo real.

        Retorna:
          (exit_code, stdout_resumido, stderr_resumido)
        """
        if job_type not in self._scripts:
            msg = f"Job não suportado: {job_type}"
            self.jobstore.add_log(job_id, msg, level="ERROR")
            return 1, "", msg

        script_name, arg_builder = self._scripts[job_type]
        args = arg_builder(params, self.cfg)  # builder recebe (params, cfg)
        cmd = [sys.executable, str(Path(self.cfg.scripts_dir) / script_name)] + args

        # registra o comando completo no log
        self.jobstore.add_log(job_id, f"Comando: {' '.join(cmd)}")

        # buffers para manter uma cópia resumida sem crescer com jobs grandes
        full_out: Deque[str] = deque(maxlen=1000)
        full_err: Deque[str] = deque(maxlen=1000)
        pending_logs: List[tuple[str, str]] = []
        pending_lock = threading.Lock()
        last_flush = time.monotonic()

        def _flush_logs(*, force: bool = False) -> None:
            nonlocal last_flush
            with pending_lock:
                if not pending_logs:
                    return
                now = time.monotonic()
                if not force and len(pending_logs) < 100 and (now - last_flush) < 1.0:
                    return
                batch = list(pending_logs)
                pending_logs.clear()
                last_flush = now
            self.jobstore.add_logs(job_id, batch)

        def _queue_log(msg: str, level: str = "INFO") -> None:
            with pending_lock:
                pending_logs.append((msg, level))
            _flush_logs()

        try:
            proc = subprocess.Popen(  # noqa: S603
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # line-buffered
            )
        except FileNotFoundError as e:
            msg = f"Falha ao iniciar processo: {e}"
            self.jobstore.add_log(job_id, msg, level="ERROR")
            return 127, "", msg
        except Exception as e:  # noqa: BLE001
            msg = f"Erro ao iniciar processo: {e}"
            self.jobstore.add_log(job_id, msg, level="ERROR")
            return 1, "", msg

        def _reader(stream, is_err: bool) -> None:
            if stream is None:
                return
            for line in stream:
                line = line.rstrip("\n")
                if not line:
                    continue
                if is_err:
                    full_err.append(line + "\n")
                    _queue_log(line, level="ERROR")
                else:
                    full_out.append(line + "\n")
                    _queue_log(line)

        # threads para ler stdout e stderr em paralelo
        t_out = threading.Thread(target=_reader, args=(proc.stdout, False), daemon=True)
        t_err = threading.Thread(target=_reader, args=(proc.stderr, True), daemon=True)
        t_out.start()
        t_err.start()

        # aguarda fim do processo
        proc.wait()
        t_out.join()
        t_err.join()
        _flush_logs(force=True)

        rc = proc.returncode

        # Mantém apenas o "rabo" de stdout/stderr para guardar
        out_tail = "".join(full_out)[-4000:]
        err_tail = "".join(full_err)[-4000:]

        return rc, out_tail, err_tail
