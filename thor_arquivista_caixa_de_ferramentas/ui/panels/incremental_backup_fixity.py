# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
# Copyright (C) 2025  Carlos Eduardo Carvalho Amand
#
# Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU GPL), conforme publicada
# pela Free Software Foundation, na versão 3 da Licença, ou (a seu critério)
# qualquer versão posterior.

from __future__ import annotations

from pathlib import Path
from tkinter import StringVar, IntVar, filedialog, messagebox
from tkinter import X

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page)
    topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    relatorio_fixidez = StringVar(value="")
    origem = StringVar(value="")
    destino = StringVar(value="")
    saida_relatorio = StringVar(value="")
    dry_run = IntVar(value=0)
    show_progress = IntVar(value=1)

    _file_row(page, "Relatório de fixidez (.txt)", relatorio_fixidez, _ask_open_txt)
    _dir_row(page, "Pasta origem do backup", origem)
    _dir_row(page, "Pasta destino", destino)
    _file_row(page, "Relatório da aplicação (.txt)", saida_relatorio, _ask_save_txt)

    opts = ttk.Frame(page)
    opts.pack(fill=X, pady=5)
    ttk.Checkbutton(opts, text="Simular sem copiar", variable=dry_run, bootstyle="round-toggle").pack(side=LEFT, padx=4)
    ttk.Checkbutton(opts, text="Mostrar progresso", variable=show_progress, bootstyle="round-toggle").pack(side=LEFT, padx=10)

    info = ttk.Labelframe(page, text="Critério de aplicação", padding=10)
    info.pack(fill=X, pady=(10, 8))
    for text in (
        "Copia da origem para o destino os registros MISSING, CORRUPT e ERROR do relatório de fixidez.",
        "Registros OK são ignorados.",
        "Registros EXTRA são reportados, mas não são excluídos automaticamente.",
        "Se o caminho do relatório começar com data/, a origem também é testada sem esse prefixo.",
    ):
        ttk.Label(info, text=f"- {text}").pack(anchor="w", pady=1)

    def _exec():
        required = [
            ("Relatório de fixidez", relatorio_fixidez.get().strip(), "file"),
            ("Pasta origem do backup", origem.get().strip(), "dir"),
            ("Pasta destino", destino.get().strip(), "dir"),
        ]
        for label, value, kind in required:
            if not value:
                messagebox.showwarning("Campo obrigatório", f"Informe: {label}.", parent=page)
                return
            path = Path(value)
            if kind == "file" and not path.is_file():
                messagebox.showerror(label, f"Arquivo inválido:\n{value}", parent=page)
                return
            if kind == "dir" and not path.is_dir():
                messagebox.showerror(label, f"Pasta inválida:\n{value}", parent=page)
                return

        enqueue_cb(
            "INCREMENTAL_BACKUP_FIXITY",
            {
                "relatorio_fixidez": relatorio_fixidez.get().strip(),
                "origem": origem.get().strip(),
                "destino": destino.get().strip(),
                "saida_relatorio": saida_relatorio.get().strip() or None,
                "dry_run": bool(dry_run.get()),
                "progress": bool(show_progress.get()),
            },
        )
        messagebox.showinfo(
            "Execução iniciada",
            "O backup incremental por relatório de fixidez foi enviado para a fila.",
            parent=page,
        )

    ttk.Button(page, text="Executar", bootstyle=PRIMARY, command=_exec).pack(pady=10)
    return page


def _dir_row(parent, label, var):
    row = ttk.Frame(parent)
    row.pack(fill=X, pady=5)
    ttk.Label(row, text=label).pack(side=LEFT, padx=4)
    ttk.Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(row, text="Procurar...", command=lambda: _ask_dir(var)).pack(side=LEFT, padx=6)


def _file_row(parent, label, var, picker):
    row = ttk.Frame(parent)
    row.pack(fill=X, pady=5)
    ttk.Label(row, text=label).pack(side=LEFT, padx=4)
    ttk.Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(row, text="Selecionar...", command=lambda: picker(var)).pack(side=LEFT, padx=6)


def _ask_dir(var):
    path = filedialog.askdirectory(title="Selecionar pasta")
    if path:
        var.set(path)


def _ask_open_txt(var):
    path = filedialog.askopenfilename(
        title="Selecionar relatório de fixidez",
        filetypes=[("Relatório TXT", "*.txt"), ("Todos", "*.*")],
    )
    if path:
        var.set(path)


def _ask_save_txt(var):
    path = filedialog.asksaveasfilename(
        title="Salvar relatório da aplicação",
        defaultextension=".txt",
        initialfile="incremental_backup_report.txt",
        filetypes=[("Relatório TXT", "*.txt"), ("Todos", "*.*")],
    )
    if path:
        var.set(path)


def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
