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

# ui/panels/verify_fixity.py
from __future__ import annotations
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, IntVar, filedialog, messagebox
from tkinter import X

def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    # Topbar com botão de fechar
    topbar = ttk.Frame(page); topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER,
               command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    raiz = StringVar(value="")
    manifesto = StringVar(value="")
    report_extras = IntVar(value=0)
    show_progress = IntVar(value=0)

    r1 = ttk.Frame(page); r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Pasta Raiz").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=raiz).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r1, text="Procurar…", command=lambda: _ask_dir(raiz)).pack(side=LEFT, padx=6)

    r2 = ttk.Frame(page); r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Manifesto (.txt)").pack(side=LEFT, padx=4)
    ttk.Entry(r2, textvariable=manifesto).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r2, text="Abrir…", command=lambda: _ask_open_manifest(manifesto)).pack(side=LEFT, padx=6)

    r3 = ttk.Frame(page); r3.pack(fill=X, pady=5)
    ttk.Checkbutton(r3, text="Reportar extras", variable=report_extras, bootstyle="round-toggle").pack(side=LEFT, padx=4)
    ttk.Checkbutton(r3, text="Mostrar progresso", variable=show_progress, bootstyle="round-toggle").pack(side=LEFT, padx=10)

    def _exec():
        enqueue_cb("VERIFY_FIXITY", {
            "raiz": raiz.get(),
            "manifesto": manifesto.get(),
            "report_extras": bool(report_extras.get()),
            "progress": bool(show_progress.get()),
        })

        # feedback modal ao usuário
        parent = page.winfo_toplevel() if hasattr(page, "winfo_toplevel") else page
        messagebox.showinfo(
            "Execução iniciada",
            "O script foi enviado para a fila de execução e será processado em segundo plano.",
            parent=parent,
        )



    ttk.Button(page, text="Executar", bootstyle=PRIMARY, command=_exec).pack(pady=10)
    return page

def _ask_dir(var):
    p = filedialog.askdirectory(title="Selecionar pasta raiz")
    if p: var.set(p)

def _ask_open_manifest(var):
    p = filedialog.askopenfilename(
        title="Selecionar manifesto BagIt",
        filetypes=[("Manifesto BagIt", "manifest-*.txt"), ("TXT", "*.txt"), ("Todos", "*.*")]
    )
    if p: var.set(p)

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
