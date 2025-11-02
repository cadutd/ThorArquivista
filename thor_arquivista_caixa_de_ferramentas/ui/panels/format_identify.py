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

# ui/panels/format_identify.py
from __future__ import annotations
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, filedialog
from tkinter import X

def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page); topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    raiz = StringVar(value="")
    saida = StringVar(value="")

    r1 = ttk.Frame(page); r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Pasta Raiz").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=raiz).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r1, text="Procurar…", command=lambda: _ask_dir(raiz)).pack(side=LEFT, padx=6)

    r2 = ttk.Frame(page); r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Relatório de Saída (.csv)").pack(side=LEFT, padx=4)
    ttk.Entry(r2, textvariable=saida).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r2, text="Salvar como…", command=lambda: _ask_save_csv(saida)).pack(side=LEFT, padx=6)

    ttk.Button(page, text="Executar",
               bootstyle=PRIMARY,
               command=lambda: enqueue_cb("FORMAT_IDENTIFY", {
                   "raiz": raiz.get(), "saida": saida.get()
               })).pack(pady=10)
    return page

def _ask_dir(var):
    p = filedialog.askdirectory(title="Selecionar pasta raiz")
    if p: var.set(p)

def _ask_save_csv(var):
    p = filedialog.asksaveasfilename(title="Salvar relatório como",
                                     defaultextension=".csv",
                                     filetypes=[("CSV", "*.csv")])
    if p: var.set(p)

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
