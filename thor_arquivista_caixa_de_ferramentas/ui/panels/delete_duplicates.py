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

# ui/panels/delete_duplicates.py
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *


DEFAULT_MANIFEST_DIR_NAME = "manifesto_origem"
DEFAULT_REPORT_DIR_NAME = "relatorio_exclusao"


def create_panel(parent, enqueue_cb, close_cb=None):
    page = tb.Frame(parent)

    origem = tk.StringVar()
    duplicatas = tk.StringVar()
    manifesto_dir = tk.StringVar()
    relatorio_dir = tk.StringVar()
    progress = tk.BooleanVar(value=True)

    grp = ttk.LabelFrame(page, text="Excluir duplicatas por manifesto")
    grp.pack(fill="x", padx=2, pady=(8, 6))

    _grid_pair_btn(grp, 0, "Pasta origem:", origem, pick_dir=True)
    _grid_pair_btn(grp, 1, "Pasta com possíveis duplicatas:", duplicatas, pick_dir=True, on_change=lambda: _suggest_outputs(duplicatas, manifesto_dir, relatorio_dir))
    _grid_pair_btn(grp, 2, "Pasta do manifesto:", manifesto_dir, pick_dir=True)
    _grid_pair_btn(grp, 3, "Pasta do relatório:", relatorio_dir, pick_dir=True)

    tb.Checkbutton(grp, text="Mostrar progresso", variable=progress).grid(row=4, column=0, sticky="w", padx=6, pady=(4, 2))

    tb.Button(
        grp,
        text="Executar exclusão",
        bootstyle=PRIMARY,
        command=lambda: _exec(page, enqueue_cb, origem, duplicatas, manifesto_dir, relatorio_dir, progress),
    ).grid(row=5, column=0, sticky="w", padx=6, pady=(8, 6))

    grp.grid_columnconfigure(1, weight=1)

    fr_btns = tb.Frame(page)
    fr_btns.pack(fill="x", pady=8)
    tb.Button(fr_btns, text="Fechar", bootstyle=DANGER, command=lambda: _close()).pack(side="left", padx=6)

    def _close():
        if callable(close_cb):
            try:
                close_cb(page)
                return
            except Exception:
                pass
        try:
            page.destroy()
        except Exception:
            pass

    return page


def _exec(page, enqueue_cb, origem_var, duplicatas_var, manifesto_dir_var, relatorio_dir_var, progress_var):
    origem = (origem_var.get() or "").strip()
    duplicatas = (duplicatas_var.get() or "").strip()
    manifesto_dir = (manifesto_dir_var.get() or "").strip()
    relatorio_dir = (relatorio_dir_var.get() or "").strip()

    if not origem or not duplicatas:
        messagebox.showwarning("Campos obrigatórios", "Informe a pasta origem e a pasta com possíveis duplicatas.", parent=page.winfo_toplevel())
        return

    ok = messagebox.askyesno(
        "Confirmar exclusão",
        "Esta tarefa apaga arquivos da pasta de possíveis duplicatas quando o hash existir no manifesto da origem. Deseja enfileirar a execução?",
        parent=page.winfo_toplevel(),
    )
    if not ok:
        return

    payload = {
        "origem": origem,
        "duplicatas": duplicatas,
        "progress": bool(progress_var.get()),
    }
    if manifesto_dir:
        payload["manifesto"] = manifesto_dir
    if relatorio_dir:
        payload["relatorio"] = relatorio_dir

    enqueue_cb("DELETE_DUPLICATES", payload)
    messagebox.showinfo("Execução iniciada", "Exclusão de duplicatas enviada para a fila de execução.", parent=page.winfo_toplevel())


def _pick_dir(var: tk.StringVar):
    d = filedialog.askdirectory(title="Selecionar pasta")
    if d:
        var.set(d)


def _grid_pair_btn(parent, row, label, var, *, pick_dir=False, on_change=None):
    tb.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=(6, 4), pady=2)
    entry = tb.Entry(parent, textvariable=var)
    entry.grid(row=row, column=1, sticky="we", pady=2)
    if on_change:
        var.trace_add("write", lambda *_: on_change())

    if pick_dir:
        tb.Button(parent, text="📂", width=3, command=lambda: _pick_dir(var)).grid(row=row, column=2, sticky="w", padx=(6, 0), pady=2)


def _suggest_outputs(duplicatas_var, manifesto_dir_var, relatorio_dir_var):
    base = (duplicatas_var.get() or "").strip()
    if not base:
        return
    root = Path(base)
    if not (manifesto_dir_var.get() or "").strip():
        manifesto_dir_var.set(str(root / DEFAULT_MANIFEST_DIR_NAME))
    if not (relatorio_dir_var.get() or "").strip():
        relatorio_dir_var.set(str(root / DEFAULT_REPORT_DIR_NAME))
