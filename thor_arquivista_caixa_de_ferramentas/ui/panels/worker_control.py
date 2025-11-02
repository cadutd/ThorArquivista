# ui/panels/worker_control.py
from __future__ import annotations

from pathlib import Path
import json
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import BOTH, X, YES, StringVar, END, Toplevel, Text

REFRESH_MS = 1000  # 1 segundo
ROW_HEIGHT = 12

def create_panel(app, enqueue_cb):
    """
    Painel de controle do Worker com gestão de fila:
      - Estado do worker (Executando / Pausado / Parado)
      - Iniciar, Parar, Pausar, Retomar, Reiniciar
      - Contagem por status
      - Lista de jobs (filtro por status)
      - Ações de fila: Reenfileirar erros, Reenfileirar todos, Limpar pendentes, Cancelar selecionado
      - Ver logs do job selecionado (modal)
    """
    page = ttk.Frame(app._main_nb, padding=10)

    # Estado + botões
    state_row = ttk.Frame(page); state_row.pack(fill=X)
    ttk.Label(state_row, text="Estado:").pack(side=LEFT, padx=(2, 8))
    state_lbl = ttk.Label(state_row, text="—", bootstyle=SECONDARY)
    state_lbl.pack(side=LEFT)

    btn_row = ttk.Frame(page); btn_row.pack(fill=X, pady=8)
    start_btn = ttk.Button(btn_row, text="Iniciar", bootstyle=SUCCESS, command=lambda: _start_worker(app))
    stop_btn = ttk.Button(btn_row, text="Parar", bootstyle=DANGER, command=lambda: _stop_worker(app))
    pause_btn = ttk.Button(btn_row, text="Pausar", bootstyle=WARNING, command=lambda: _pause_worker(app))
    resume_btn = ttk.Button(btn_row, text="Retomar", bootstyle=INFO, command=lambda: _resume_worker(app))
    restart_btn = ttk.Button(btn_row, text="Reiniciar", bootstyle=PRIMARY, command=lambda: _restart_worker(app))

    start_btn.pack(side=LEFT, padx=4)
    stop_btn.pack(side=LEFT, padx=4)
    pause_btn.pack(side=LEFT, padx=4)
    resume_btn.pack(side=LEFT, padx=4)
    restart_btn.pack(side=LEFT, padx=4)

    # Informações rápidas
    info = ttk.Labelframe(page, text="Ambiente", padding=10)
    info.pack(fill=X, pady=(10, 8))
    _add_info(info, "JobStore", Path(app.jobstore.path).resolve())
    _add_info(info, "Scripts", Path(app.cfg.scripts_dir).resolve())
    _add_info(info, "PREMIS log", Path(app.cfg.premis_log).resolve())

    # Contadores por status
    counts_frame = ttk.Labelframe(page, text="Contagem por status", padding=10)
    counts_frame.pack(fill=X)
    counts_vars = {
        "pending": StringVar(value="0"),
        "running": StringVar(value="0"),
        "done": StringVar(value="0"),
        "error": StringVar(value="0"),
        "canceled": StringVar(value="0"),
    }

    # Adiciona os contadores lado a lado
    for col, (name, var) in enumerate(counts_vars.items()):
        _add_count_cell(counts_frame, 0, col, name, var)


#    _add_count_row(counts_frame, "pending", counts_vars["pending"])
#    _add_count_row(counts_frame, "running", counts_vars["running"])
#    _add_count_row(counts_frame, "done", counts_vars["done"])
#    _add_count_row(counts_frame, "error", counts_vars["error"])
#    _add_count_row(counts_frame, "canceled", counts_vars["canceled"])

    # Filtro e ações de fila
    actions = ttk.Frame(page); actions.pack(fill=X, pady=(10, 6))
    ttk.Label(actions, text="Filtrar:").pack(side=LEFT, padx=(2, 6))
    filt = StringVar(value="pending")
    ttk.Combobox(actions, textvariable=filt, state="readonly",
                 values=["pending", "error", "done", "canceled", "running", "todos"], width=12).pack(side=LEFT)

    ttk.Button(actions, text="Atualizar", bootstyle=SECONDARY,
               command=lambda: _refresh_jobs(app, jobs_tree, filt.get())).pack(side=LEFT, padx=6)

    ttk.Button(actions, text="Reenfileirar erros", bootstyle=WARNING,
               command=lambda: _do_requeue_errors(app, jobs_tree, filt)).pack(side=LEFT, padx=6)
    ttk.Button(actions, text="Reenfileirar todos", bootstyle=WARNING,
               command=lambda: _do_requeue_all(app, jobs_tree, filt)).pack(side=LEFT, padx=6)
    ttk.Button(actions, text="Limpar pendentes", bootstyle=DANGER,
               command=lambda: _do_clear_pending(app, jobs_tree, filt)).pack(side=LEFT, padx=6)
    ttk.Button(actions, text="Limpar executados", bootstyle=DANGER,
               command=lambda: _do_clear_done(app, jobs_tree, filt)).pack(side=LEFT, padx=6)
    ttk.Button(actions, text="Limpar com erro", bootstyle=DANGER,
               command=lambda: _do_clear_error(app, jobs_tree, filt)).pack(side=LEFT, padx=6)
    ttk.Button(actions, text="Cancelar selecionado", bootstyle=DANGER,
               command=lambda: _do_cancel_selected(app, jobs_tree, filt)).pack(side=LEFT, padx=6)
    ttk.Button(actions, text="Ver logs", bootstyle=INFO,
               command=lambda: _show_logs_modal(app, jobs_tree)).pack(side=LEFT, padx=6)

    # Tabela de jobs
    cols = ("id", "tipo", "status", "criado", "params")
    jobs_tree = ttk.Treeview(page, columns=cols, show="headings", height=ROW_HEIGHT, bootstyle=INFO)
    for c, t, w in (
        ("id", "ID", 180),
        ("tipo", "Tipo", 150),
        ("status", "Status", 100),
        ("criado", "Criado em", 160),
        ("params", "Parâmetros", 600),
    ):
        jobs_tree.heading(c, text=t)
        jobs_tree.column(c, width=w, anchor="w")
    jobs_tree.pack(fill=BOTH, expand=YES, pady=(8, 0))

    # Mensagens
    msg = ttk.Label(page, text="", bootstyle=INFO)
    msg.pack(fill=X, pady=(6, 0))

    # Atualização periódica de estado/contagens
    def _tick():
        if not page.winfo_exists():
            return
        alive = app.worker.is_alive() if app.worker else False
        paused = app.worker.is_paused() if app.worker else False
        if alive and not paused:
            state_lbl.configure(text="Em execução", bootstyle=SUCCESS)
            start_btn.configure(state=DISABLED); stop_btn.configure(state=NORMAL)
            pause_btn.configure(state=NORMAL);   resume_btn.configure(state=DISABLED)
        elif alive and paused:
            state_lbl.configure(text="Pausado", bootstyle=WARNING)
            start_btn.configure(state=DISABLED); stop_btn.configure(state=NORMAL)
            pause_btn.configure(state=DISABLED); resume_btn.configure(state=NORMAL)
        else:
            state_lbl.configure(text="Parado", bootstyle=DANGER)
            start_btn.configure(state=NORMAL);   stop_btn.configure(state=DISABLED)
            pause_btn.configure(state=DISABLED); resume_btn.configure(state=DISABLED)

        # contagens
        counts = app.worker.counts_by_status()
        for k, var in counts_vars.items():
            var.set(str(counts.get(k, 0)))

        page.after(REFRESH_MS, _tick)


    # rodape com "Fechar aba"
    rodape = ttk.Frame(page); rodape.pack(fill=X)
    ttk.Button(rodape, text="Fechar", bootstyle=DANGER,
               command=lambda: _close_tab(app, page)).pack(side=LEFT)


    # primeira carga da lista
    _refresh_jobs(app, jobs_tree, filt.get())
    _tick()
    return page


# ---------------- helpers UI ----------------

def _add_info(parent, label, value):
    row = ttk.Frame(parent); row.pack(fill=X, pady=2)
    ttk.Label(row, text=f"{label}:", width=14, anchor="e").pack(side=LEFT, padx=(0, 8))
    ttk.Label(row, text=str(value), anchor="w").pack(side=LEFT)

def _add_count_row(parent, name, var):
    row = ttk.Frame(parent); row.pack(fill=X, pady=2)
    ttk.Label(row, text=f"{name}:", width=12, anchor="e").pack(side=LEFT, padx=(0, 8))
    ttk.Entry(row, textvariable=var, width=8, state="readonly").pack(side=LEFT)

def _add_count_cell(parent, row, col, name, var):
    """Adiciona um contador (label + valor) em uma célula da grid."""
    ttk.Label(parent, text=f"{name}:", width=10, anchor="e").grid(row=row*2, column=col, padx=4, pady=(0, 2))
    ttk.Entry(parent, textvariable=var, width=6, state="readonly", justify="center").grid(row=row*2+1, column=col, padx=4)
    parent.grid_columnconfigure(col, weight=1)


def _refresh_jobs(app, tree, status_filter):
    tree.delete(*tree.get_children())
    status = None if status_filter == "todos" else status_filter
    jobs = app.worker.list_jobs(status=status)
    for j in jobs:
        jid = j.get("_id", "")
        jtype = j.get("job_type", "")
        st = j.get("status", "")
        created = j.get("created_at", "")
        params = j.get("params", {})
        tree.insert("", "end", iid=jid, values=(jid, jtype, st, created, _pretty_params(params)))

def _pretty_params(params: dict) -> str:
    try:
        # string curta, mas legível
        s = json.dumps(params, ensure_ascii=False)
        if len(s) > 120:
            s = s[:117] + "..."
        return s
    except Exception:
        return str(params)

def _start_worker(app):
    try:
        if not app.worker or not app.worker.is_alive():
            app.worker.start()
            app._status.configure(text="Worker iniciado.")
        else:
            app._status.configure(text="Worker já está em execução.")
    except Exception as e:
        app._status.configure(text=f"Falha ao iniciar worker: {e}")

def _stop_worker(app):
    try:
        if app.worker and app.worker.is_alive():
            app.worker.stop()
            app.worker.join(timeout=2.0)
            app._status.configure(text="Worker parado.")
        else:
            app._status.configure(text="Worker já está parado.")
    except Exception as e:
        app._status.configure(text=f"Falha ao parar worker: {e}")

def _pause_worker(app):
    try:
        if app.worker and app.worker.is_alive() and not app.worker.is_paused():
            app.worker.pause()
            app._status.configure(text="Worker pausado.")
        else:
            app._status.configure(text="Worker não está ativo ou já pausado.")
    except Exception as e:
        app._status.configure(text=f"Falha ao pausar worker: {e}")

def _resume_worker(app):
    try:
        if app.worker and app.worker.is_alive() and app.worker.is_paused():
            app.worker.resume()
            app._status.configure(text="Worker retomado.")
        else:
            app._status.configure(text="Worker não está pausado.")
    except Exception as e:
        app._status.configure(text=f"Falha ao retomar worker: {e}")

def _restart_worker(app):
    try:
        if app.worker and app.worker.is_alive():
            app.worker.stop()
            app.worker.join(timeout=2.0)
        app.worker.start()
        app._status.configure(text="Worker reiniciado.")
    except Exception as e:
        app._status.configure(text=f"Falha ao reiniciar worker: {e}")

def _do_requeue_errors(app, tree, filt_var):
    n = app.worker.requeue_errors()
    app._status.configure(text=f"Reenfileirados {n} job(s) com erro.")
    _refresh_jobs(app, tree, filt_var.get())

def _do_requeue_all(app, tree, filt_var):
    n = app.worker.requeue_all()
    app._status.configure(text=f"Reenfileirados {n} job(s).")
    _refresh_jobs(app, tree, filt_var.get())

def _do_clear_pending(app, tree, filt_var):
    n = app.worker.clear_pending()
    app._status.configure(text=f"Removidos {n} job(s) pendentes.")
    _refresh_jobs(app, tree, filt_var.get())

def _do_clear_done(app, tree, filt_var):
    n = app.worker.clear_done()
    app._status.configure(text=f"Removidos {n} job(s) executados.")
    _refresh_jobs(app, tree, filt_var.get())

def _do_clear_error(app, tree, filt_var):
    n = app.worker.clear_error()
    app._status.configure(text=f"Removidos {n} job(s) com erro.")
    _refresh_jobs(app, tree, filt_var.get())


def _do_cancel_selected(app, tree, filt_var):
    sel = tree.selection()
    if not sel:
        app._status.configure(text="Nenhum job selecionado para cancelar.")
        return
    jid = sel[0]
    ok = app.worker.cancel_job(jid)
    app._status.configure(text=f"Job {jid} {'cancelado' if ok else 'não pôde ser cancelado'}.")
    _refresh_jobs(app, tree, filt_var.get())

def _show_logs_modal(app, tree):
    sel = tree.selection()
    if not sel:
        app._status.configure(text="Nenhum job selecionado para visualizar logs.")
        return
    jid = sel[0]
    logs = app.worker.jobstore.get_logs(jid)

    # janela modal
    win = Toplevel(app)
    win.title(f"Logs do Job {jid}")
    win.geometry("900x500")
    win.transient(app)
    win.grab_set()

    top = ttk.Frame(win, padding=6); top.pack(fill=X)
    ttk.Label(top, text=f"Job: {jid}", bootstyle=PRIMARY).pack(side=LEFT)
    ttk.Button(top, text="Atualizar", bootstyle=SECONDARY,
               command=lambda: _populate_logs_text(txt, app, jid)).pack(side=RIGHT, padx=4)
    ttk.Button(top, text="Copiar", bootstyle=INFO,
               command=lambda: _copy_logs_to_clipboard(app, txt)).pack(side=RIGHT, padx=4)
    ttk.Button(top, text="Fechar", bootstyle=DANGER,
               command=win.destroy).pack(side=RIGHT, padx=4)

    txt = Text(win, wrap="word")
    txt.pack(fill=BOTH, expand=YES, padx=6, pady=6)

    _populate_logs_text(txt, app, jid)

def _populate_logs_text(txt: Text, app, job_id: str):
    txt.configure(state="normal")
    txt.delete("1.0", END)
    logs = app.worker.jobstore.get_logs(job_id)
    # ordena por timestamp
    def _ts(l): return l.get("ts", "")
    logs = sorted(logs, key=_ts)
    for entry in logs:
        line = f"[{entry.get('ts','')}] {entry.get('level','INFO')}: {entry.get('msg','')}\n"
        txt.insert(END, line)
    if not logs:
        txt.insert(END, "Sem logs para este job.")
    txt.see(END)
    txt.configure(state="disabled")

def _copy_logs_to_clipboard(app, txt: Text):
    content = txt.get("1.0", END)
    app.clipboard_clear()
    app.clipboard_append(content.strip())
    app._status.configure(text="Logs copiados para a área de transferência.")

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
