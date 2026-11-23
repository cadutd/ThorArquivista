# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
from __future__ import annotations

import json
from pathlib import Path
from tkinter import END, StringVar, Text, filedialog, messagebox
from tkinter import BOTH, LEFT, RIGHT, X, Y

import ttkbootstrap as ttk
from ttkbootstrap.constants import DANGER, INFO, PRIMARY, SECONDARY, SUCCESS, WARNING

from scripts.backup_common import normalize_sources, validate_source_paths


def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page)
    topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    plan_path = StringVar(value="")
    dest_path = StringVar(value="")
    backup_name = StringVar(value="")
    status = StringVar(value="Selecione um plano JSON.")

    r1 = ttk.Frame(page)
    r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Plano JSON").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=plan_path).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r1, text="Abrir...", command=lambda: _ask_plan(plan_path, dest_path, backup_name, status)).pack(side=LEFT, padx=6)

    r2 = ttk.Frame(page)
    r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Destino do backup").pack(side=LEFT, padx=4)
    ttk.Entry(r2, textvariable=dest_path).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r2, text="Selecionar...", command=lambda: _ask_dir(dest_path)).pack(side=LEFT, padx=6)

    r3 = ttk.Frame(page)
    r3.pack(fill=X, pady=5)
    ttk.Label(r3, text="Backup").pack(side=LEFT, padx=4)
    ttk.Entry(r3, textvariable=backup_name, width=30).pack(side=LEFT)
    ttk.Label(r3, textvariable=status, bootstyle=SECONDARY).pack(side=LEFT, padx=12)

    ttk.Label(page, text="Arquivos: <destino>/<origem>/ | Manifestos: thor-backup/manifests/<origem>/manifest-<algoritmo>.txt").pack(fill=X, pady=4)

    actions = ttk.Frame(page)
    actions.pack(fill=X, pady=8)
    ttk.Button(actions, text="Validar plano", bootstyle=INFO, command=lambda: _validate(plan_path, dest_path, backup_name, status, output)).pack(side=LEFT, padx=4)
    ttk.Button(actions, text="Executar", bootstyle=PRIMARY, command=lambda: _enqueue_plan(enqueue_cb, plan_path, False, page)).pack(side=LEFT, padx=4)
    ttk.Button(actions, text="Retomar", bootstyle=SUCCESS, command=lambda: _enqueue_plan(enqueue_cb, plan_path, True, page, dest_path)).pack(side=LEFT, padx=4)
    ttk.Button(actions, text="Pausar com STOP", bootstyle=WARNING, command=lambda: _write_stop(dest_path, page)).pack(side=LEFT, padx=4)
    ttk.Button(actions, text="Verificar integridade", bootstyle=INFO, command=lambda: _enqueue_verify(enqueue_cb, dest_path, page)).pack(side=LEFT, padx=4)
    ttk.Button(actions, text="Histórico", bootstyle=SECONDARY, command=lambda: _show_history(dest_path, backup_name, output)).pack(side=LEFT, padx=4)

    body = ttk.Frame(page)
    body.pack(fill=BOTH, expand=True, pady=(8, 0))
    output = Text(body, height=18, wrap="none")
    output.pack(side=LEFT, fill=BOTH, expand=True)
    scroll = ttk.Scrollbar(body, orient="vertical", command=output.yview)
    scroll.pack(side=RIGHT, fill=Y)
    output.configure(yscrollcommand=scroll.set)

    return page


def _load_plan(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise ValueError(f"Plano não encontrado: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("O plano JSON deve conter um objeto.")
    return data


def _plan_dest(data: dict) -> str:
    return str(data.get("destination") or data.get("destino") or "")


def _plan_name(data: dict, plan_path: str) -> str:
    return str(data.get("name") or data.get("nome") or Path(plan_path).stem)


def _plan_sources(data: dict) -> list:
    return data.get("sources") or data.get("pastas") or data.get("folders") or []


def _ask_plan(plan_path, dest_path, backup_name, status):
    p = filedialog.askopenfilename(title="Selecionar plano de backup", filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
    if not p:
        return
    plan_path.set(p)
    try:
        data = _load_plan(p)
        dest_path.set(_plan_dest(data))
        backup_name.set(_plan_name(data, p))
        status.set("Plano carregado.")
    except Exception as e:
        status.set(f"Plano inválido: {e}")


def _ask_dir(var):
    p = filedialog.askdirectory(title="Selecionar destino do backup")
    if p:
        var.set(p)


def _validate(plan_path, dest_path, backup_name, status, output):
    output.delete("1.0", END)
    try:
        data = _load_plan(plan_path.get())
        sources = _plan_sources(data)
        dest = _plan_dest(data)
        if not dest:
            raise ValueError("Campo 'destination'/'destino' ausente.")
        if not isinstance(sources, list) or not sources:
            raise ValueError("Lista 'sources'/'pastas' ausente.")
        normalized = normalize_sources(data)
        validate_source_paths(Path(dest).resolve(), normalized)
        missing = []
        for item in sources:
            p = item if isinstance(item, str) else item.get("path") or item.get("raiz") or item.get("source")
            if not p or not Path(p).exists():
                missing.append(str(p))
        dest_path.set(dest)
        backup_name.set(_plan_name(data, plan_path.get()))
        output.insert(END, json.dumps(data, ensure_ascii=False, indent=2))
        output.insert(END, "\n\nOrganização no destino:\n")
        opts = data.get("options") or data.get("opcoes") or {}
        algo = opts.get("algo") or opts.get("algorithm") or "sha256"
        for source in normalized:
            output.insert(END, f"  {source['name']}/\n  thor-backup/manifests/{source['name']}/manifest-{algo}.txt\n")
        if missing:
            status.set(f"Plano válido com {len(missing)} origem(ns) não encontrada(s).")
            output.insert(END, "\n\nOrigens não encontradas:\n" + "\n".join(missing))
        else:
            status.set("Plano válido.")
    except Exception as e:
        status.set(f"Plano inválido: {e}")
        output.insert(END, str(e))


def _enqueue_plan(enqueue_cb, plan_path, resume: bool, page, dest_path=None):
    if not plan_path.get().strip():
        messagebox.showwarning("Plano JSON", "Selecione um plano JSON.", parent=page)
        return
    if resume:
        try:
            dest = _plan_dest(_load_plan(plan_path.get().strip()))
        except Exception as exc:
            messagebox.showerror("Plano inválido", str(exc), parent=page)
            return
        if dest_path is not None:
            dest_path.set(dest)
        if dest:
            stop = Path(dest) / "thor-backup" / "checkpoints" / "STOP"
            if stop.exists():
                stop.unlink()
    enqueue_cb("BACKUP_PLAN", {"config": plan_path.get().strip(), "resume": resume, "progress": True})
    messagebox.showinfo("Backup preservacional", "Job enviado para a fila do Worker.", parent=page)


def _enqueue_verify(enqueue_cb, dest_path, page):
    if not dest_path.get().strip():
        messagebox.showwarning("Destino", "Informe o destino do backup.", parent=page)
        return
    enqueue_cb("BACKUP_VERIFY", {"destino": dest_path.get().strip(), "progress": True})
    messagebox.showinfo("Verificação", "Job de verificação enviado para a fila.", parent=page)


def _write_stop(dest_path, page):
    if not dest_path.get().strip():
        messagebox.showwarning("Destino", "Informe o destino do backup.", parent=page)
        return
    stop = Path(dest_path.get().strip()) / "thor-backup" / "checkpoints" / "STOP"
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text("STOP\n", encoding="utf-8")
    messagebox.showinfo("Parada segura", f"Arquivo STOP criado:\n{stop}", parent=page)


def _show_history(dest_path, backup_name, output):
    output.delete("1.0", END)
    if not dest_path.get().strip():
        output.insert(END, "Informe o destino do backup.")
        return
    tb = Path(dest_path.get().strip()) / "thor-backup"
    if not tb.exists():
        output.insert(END, f"Estrutura não encontrada: {tb}")
        return
    checkpoint = tb / "checkpoints" / f"{backup_name.get().strip()}.state.json"
    sections = [
        ("Checkpoint", [checkpoint] if checkpoint.exists() else sorted((tb / "checkpoints").glob("*.state.json"))),
        ("Relatórios", sorted(p for p in (tb / "relatorios").rglob("*") if p.is_file())),
        ("Manifestos atuais", sorted((tb / "manifests").glob("*/manifest-*.txt"))),
        ("Manifestos históricos", sorted((tb / "historico").glob("*/*/manifest-*.txt"))),
    ]
    for title, paths in sections:
        output.insert(END, f"{title}\n")
        if not paths:
            output.insert(END, "  Nenhum item.\n")
        for p in paths[-50:]:
            output.insert(END, f"  {p}\n")
        output.insert(END, "\n")


def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
