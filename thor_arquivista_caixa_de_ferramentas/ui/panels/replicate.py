# ui/panels/replicate.py
from __future__ import annotations
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, Text, IntVar, filedialog, END
from tkinter import X

def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page); topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    fonte = StringVar(value="")
    destinos_text = None
    verificar = IntVar(value=0)

    r1 = ttk.Frame(page); r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Fonte (pasta)").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=fonte).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r1, text="Procurar…", command=lambda: _ask_dir(fonte)).pack(side=LEFT, padx=6)

    r2 = ttk.Frame(page); r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Destinos (um por linha)").pack(side=LEFT, padx=4)

    destinos_text = Text(r2, height=6)
    destinos_text.pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r2, text="Adicionar…", command=lambda: _add_dest(destinos_text)).pack(side=LEFT, padx=6)

    r3 = ttk.Frame(page); r3.pack(fill=X, pady=5)
    ttk.Checkbutton(r3, text="Verificar hash após copiar", variable=verificar, bootstyle="round-toggle").pack(side=LEFT, padx=4)

    def _exec():
        destinos = [ln.strip() for ln in destinos_text.get("1.0", END).splitlines() if ln.strip()]
        enqueue_cb("REPLICATE", {
            "fonte": fonte.get(),
            "destinos": destinos,
            "verificar_hash": bool(verificar.get()),
        })

    ttk.Button(page, text="Executar", bootstyle=PRIMARY, command=_exec).pack(pady=10)
    return page

def _ask_dir(var):
    p = filedialog.askdirectory(title="Selecionar pasta")
    if p: var.set(p)

def _add_dest(txt: Text):
    p = filedialog.askdirectory(title="Selecionar destino")
    if p:
        current = txt.get("1.0", END).strip()
        txt.insert(END, ("\n" if current else "") + p)

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
