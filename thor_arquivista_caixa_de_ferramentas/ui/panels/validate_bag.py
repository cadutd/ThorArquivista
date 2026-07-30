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

from pathlib import Path
from tkinter import StringVar, IntVar, filedialog, messagebox
from tkinter import X

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


ALGOS = ["todos", "sha256", "sha512", "md5", "sha1", "blake2b", "blake2s"]


def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page)
    topbar.pack(fill=X)
    ttk.Button(
        topbar,
        text="Fechar aba",
        bootstyle=DANGER,
        command=lambda: _close_tab(app, page),
    ).pack(side=RIGHT)

    bag = StringVar(value="")
    algo = StringVar(value="todos")
    show_progress = IntVar(value=1)

    r1 = ttk.Frame(page)
    r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Pasta do BagIt").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=bag).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r1, text="Procurar...", command=lambda: _ask_dir(bag)).pack(side=LEFT, padx=6)

    r2 = ttk.Frame(page)
    r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Algoritmo").pack(side=LEFT, padx=4)
    ttk.Combobox(r2, textvariable=algo, values=ALGOS, state="readonly", width=14).pack(side=LEFT)
    ttk.Checkbutton(
        r2,
        text="Mostrar progresso",
        variable=show_progress,
        bootstyle="round-toggle",
    ).pack(side=LEFT, padx=10)

    info = ttk.Labelframe(page, text="Validações executadas", padding=10)
    info.pack(fill=X, pady=(10, 8))
    for text in (
        "Estrutura básica: bagit.txt, bag-info.txt e data/",
        "Manifestos de payload: manifest-*.txt",
        "Fixidez dos arquivos em data/",
        "Arquivos extras em data/ ausentes nos manifestos",
        "Tagmanifests: tagmanifest-*.txt, quando existirem",
    ):
        ttk.Label(info, text=f"- {text}").pack(anchor="w", pady=1)

    def _exec():
        bag_path = bag.get().strip()
        if not bag_path:
            messagebox.showwarning("Campo obrigatório", "Informe a pasta raiz do pacote BagIt.", parent=page)
            return
        if not Path(bag_path).exists():
            messagebox.showerror("Pasta BagIt", f"A pasta informada não existe:\n{bag_path}", parent=page)
            return

        selected_algo = algo.get().strip()
        payload = {
            "bag": bag_path,
            "algo": None if selected_algo == "todos" else selected_algo,
            "progress": bool(show_progress.get()),
        }
        enqueue_cb("VALIDATE_BAG", payload)
        messagebox.showinfo(
            "Execução iniciada",
            "O job de validação do BagIt foi enviado para a fila.",
            parent=page,
        )

    ttk.Button(page, text="Executar", bootstyle=PRIMARY, command=_exec).pack(pady=10)
    return page


def _ask_dir(var):
    p = filedialog.askdirectory(title="Selecionar pasta raiz do pacote BagIt")
    if p:
        var.set(p)


def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
