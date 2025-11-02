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

# ui/panels/premis_event.py
from __future__ import annotations
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, filedialog
from tkinter import X

def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page); topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    arquivo_log = StringVar(value=str(app.cfg.premis_log))
    tipo = StringVar(value="other")
    obj_id = StringVar(value="")
    detalhe = StringVar(value="")
    resultado = StringVar(value="success")
    agente = StringVar(value=app.cfg.premis_agent or "Gerenciador")

    r0 = ttk.Frame(page); r0.pack(fill=X, pady=5)
    ttk.Label(r0, text="Arquivo de Log (JSONL)").pack(side=LEFT, padx=4)
    ttk.Entry(r0, textvariable=arquivo_log).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r0, text="Escolher…", command=lambda: _ask_open_jsonl(arquivo_log)).pack(side=LEFT, padx=6)

    r1 = ttk.Frame(page); r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Tipo").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=tipo, width=24).pack(side=LEFT, padx=4)
    ttk.Label(r1, text="Resultado").pack(side=LEFT, padx=10)
    ttk.Combobox(r1, values=["success", "failure", "neutral"], textvariable=resultado, state="readonly", width=12).pack(side=LEFT)

    r2 = ttk.Frame(page); r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Objeto (ID)").pack(side=LEFT, padx=4)
    ttk.Entry(r2, textvariable=obj_id).pack(side=LEFT, fill=X, expand=True)

    r3 = ttk.Frame(page); r3.pack(fill=X, pady=5)
    ttk.Label(r3, text="Detalhe").pack(side=LEFT, padx=4)
    ttk.Entry(r3, textvariable=detalhe).pack(side=LEFT, fill=X, expand=True)

    r4 = ttk.Frame(page); r4.pack(fill=X, pady=5)
    ttk.Label(r4, text="Agente").pack(side=LEFT, padx=4)
    ttk.Entry(r4, textvariable=agente, width=40).pack(side=LEFT, padx=4)

    def _exec():
        enqueue_cb("PREMIS_EVENT", {
            "arquivo_log": arquivo_log.get(),
            "tipo": tipo.get(),
            "obj_id": obj_id.get(),
            "detalhe": detalhe.get(),
            "resultado": resultado.get(),
            "agente": agente.get(),
        })

    ttk.Button(page, text="Registrar Evento", bootstyle=PRIMARY, command=_exec).pack(pady=10)
    return page

def _ask_open_jsonl(var):
    p = filedialog.askopenfilename(title="Selecionar arquivo JSONL",
                                   filetypes=[("JSONL", "*.jsonl"), ("Todos", "*.*")])
    if p: var.set(p)

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
