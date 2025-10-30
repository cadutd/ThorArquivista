# ui/panels/build_bag.py
from __future__ import annotations
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, filedialog
from tkinter import X

def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page); topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    fonte = StringVar(value="")
    destino = StringVar(value="")
    bag_name = StringVar(value="")
    org = StringVar(value="APESP")

    r1 = ttk.Frame(page); r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Fonte (pasta)").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=fonte).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r1, text="Procurar…", command=lambda: _ask_dir(fonte)).pack(side=LEFT, padx=6)

    r2 = ttk.Frame(page); r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Destino (pasta)").pack(side=LEFT, padx=4)
    ttk.Entry(r2, textvariable=destino).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r2, text="Procurar…", command=lambda: _ask_dir(destino)).pack(side=LEFT, padx=6)

    r3 = ttk.Frame(page); r3.pack(fill=X, pady=5)
    ttk.Label(r3, text="Nome da Bag").pack(side=LEFT, padx=4)
    ttk.Entry(r3, textvariable=bag_name, width=40).pack(side=LEFT, padx=4)
    ttk.Label(r3, text="Organização").pack(side=LEFT, padx=8)
    ttk.Entry(r3, textvariable=org, width=24).pack(side=LEFT)

    ttk.Button(page, text="Executar",
               bootstyle=PRIMARY,
               command=lambda: enqueue_cb("BUILD_BAG", {
                   "fonte": fonte.get(),
                   "destino": destino.get(),
                   "bag_name": bag_name.get(),
                   "org": org.get() or "APESP",
               })).pack(pady=10)
    return page

def _ask_dir(var):
    p = filedialog.askdirectory(title="Selecionar pasta")
    if p: var.set(p)

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
