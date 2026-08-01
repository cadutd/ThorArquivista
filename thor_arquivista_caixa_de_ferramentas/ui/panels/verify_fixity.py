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
    report_extras = IntVar(value=1)
    show_progress = IntVar(value=1)
    max_list_items = StringVar(value="200")
    report_file = StringVar(value="")

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

    r4 = ttk.Frame(page); r4.pack(fill=X, pady=5)
    ttk.Label(r4, text="Itens por lista no log").pack(side=LEFT, padx=4)
    ttk.Spinbox(r4, from_=0, to=1000000, increment=50, textvariable=max_list_items, width=10).pack(side=LEFT)
    ttk.Label(r4, text="(0 lista tudo)", bootstyle=SECONDARY).pack(side=LEFT, padx=8)

    r5 = ttk.Frame(page); r5.pack(fill=X, pady=5)
    ttk.Label(r5, text="Relatório completo (.txt)").pack(side=LEFT, padx=4)
    ttk.Entry(r5, textvariable=report_file).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r5, text="Salvar como...", command=lambda: _ask_save_report(report_file)).pack(side=LEFT, padx=6)

    def _exec():
        try:
            max_items = int(max_list_items.get())
        except ValueError:
            messagebox.showwarning("Limite inválido", "Informe um número inteiro em 'Itens por lista no log'.", parent=page)
            return
        if max_items < 0:
            messagebox.showwarning("Limite inválido", "O limite de itens não pode ser negativo.", parent=page)
            return

        enqueue_cb("VERIFY_FIXITY", {
            "raiz": raiz.get(),
            "manifesto": manifesto.get(),
            "report_extras": bool(report_extras.get()),
            "progress": bool(show_progress.get()),
            "max_list_items": max_items,
            "report_file": report_file.get().strip() or None,
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

def _ask_save_report(var):
    p = filedialog.asksaveasfilename(
        title="Salvar relatório completo como",
        defaultextension=".txt",
        initialfile="verify_fixity_report.txt",
        filetypes=[("Arquivo de texto", "*.txt"), ("Todos", "*.*")]
    )
    if p: var.set(p)

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
