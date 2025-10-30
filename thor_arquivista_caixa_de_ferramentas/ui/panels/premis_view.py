# ui/panels/premis_view.py
from __future__ import annotations

from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, BOTH, X, YES
from tkinter import filedialog

from negocio.premis import (
    read_events,
    unique_sorted,
    in_range,
    event_row,
    export_csv,
    sort_key,
)

def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    # Topbar com "Fechar aba"
    topbar = ttk.Frame(page); topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    # Estado da UI (sem type annotations locais)
    app._premis_sort_by = None
    app._premis_sort_reverse = False
    app._premis_filtered_rows = []
    app._premis_rows_filtered_cache = []
    app._premis_rows_cache = []

    bar = ttk.Frame(page); bar.pack(fill=X)
    app._premis_tipo = StringVar(value="")
    app._premis_outcome = StringVar(value="")
    app._premis_agent = StringVar(value="")
    app._premis_object = StringVar(value="")
    app._premis_from = StringVar(value="")
    app._premis_to = StringVar(value="")
    app._premis_query = StringVar(value="")

    ttk.Label(bar, text="Tipo").pack(side=LEFT, padx=4)
    app._premis_tipo_cb = ttk.Combobox(bar, textvariable=app._premis_tipo, values=[], width=18, state="readonly")
    app._premis_tipo_cb.pack(side=LEFT)

    ttk.Label(bar, text="Outcome").pack(side=LEFT, padx=4)
    app._premis_outcome_cb = ttk.Combobox(bar, textvariable=app._premis_outcome, values=[], width=12, state="readonly")
    app._premis_outcome_cb.pack(side=LEFT)

    ttk.Label(bar, text="Agente").pack(side=LEFT, padx=4)
    app._premis_agent_cb = ttk.Combobox(bar, textvariable=app._premis_agent, values=[], width=20, state="readonly")
    app._premis_agent_cb.pack(side=LEFT)

    ttk.Label(bar, text="Objeto").pack(side=LEFT, padx=4)
    app._premis_object_cb = ttk.Combobox(bar, textvariable=app._premis_object, values=[], width=24, state="readonly")
    app._premis_object_cb.pack(side=LEFT)

    row2 = ttk.Frame(page); row2.pack(fill=X, pady=4)
    ttk.Label(row2, text="De").pack(side=LEFT, padx=4)
    ttk.Entry(row2, textvariable=app._premis_from, width=12).pack(side=LEFT)
    ttk.Label(row2, text="Até").pack(side=LEFT, padx=4)
    ttk.Entry(row2, textvariable=app._premis_to, width=12).pack(side=LEFT)

    ttk.Label(row2, text="Buscar").pack(side=LEFT, padx=4)
    ttk.Entry(row2, textvariable=app._premis_query, width=36).pack(side=LEFT)

    ttk.Button(row2, text="Abrir log…", bootstyle=SECONDARY, command=lambda: _premis_open_log(app)).pack(side=LEFT, padx=6)
    ttk.Button(row2, text="Atualizar", bootstyle=PRIMARY, command=lambda: _premis_reload(app)).pack(side=LEFT, padx=4)
    ttk.Button(row2, text="Exportar CSV", bootstyle=SECONDARY, command=lambda: _premis_export_csv(app)).pack(side=LEFT, padx=4)

    cols = ("data", "tipo", "resultado", "objeto", "detalhe", "agente", "id")
    titles = ["Data/Hora", "Tipo", "Resultado", "Objeto", "Detalhe", "Agente", "ID"]
    app._premis_col_titles = {c: t for c, t in zip(cols, titles)}
    app._premis_tree = ttk.Treeview(page, columns=cols, show="headings", height=18, bootstyle=INFO)
    for c, t in zip(cols, titles):
        app._premis_tree.heading(c, text=t, command=lambda cn=c: _premis_set_sort(app, cn))
        app._premis_tree.column(
            c,
            width=150 if c not in ("detalhe", "objeto") else (420 if c == "detalhe" else 240),
            anchor="w"
        )
    app._premis_tree.pack(fill=BOTH, expand=YES, pady=(8, 0))

    pbar = ttk.Frame(page); pbar.pack(fill=X, pady=6)
    ttk.Label(pbar, text="Itens/página").pack(side=LEFT, padx=4)
    app._premis_page_size = StringVar(value="200")
    app._premis_page = 0
    ttk.Combobox(pbar, textvariable=app._premis_page_size,
                 values=["50", "100", "200", "500", "1000"], width=6, state="readonly").pack(side=LEFT)
    ttk.Button(pbar, text="⟨ Anterior", command=lambda: _premis_change_page(app, -1)).pack(side=LEFT, padx=6)
    ttk.Button(pbar, text="Próxima ⟩", command=lambda: _premis_change_page(app, 1)).pack(side=LEFT)
    app._premis_page_lbl = ttk.Label(pbar, text="Página 1"); app._premis_page_lbl.pack(side=LEFT, padx=10)

    _premis_reload(app)
    return page


# ----- helpers do painel -----

def _premis_set_sort(app, col_name: str):
    cols = ("data", "tipo", "resultado", "objeto", "detalhe", "agente", "id")
    try:
        idx = cols.index(col_name)
    except ValueError:
        return
    if getattr(app, "_premis_sort_by", None) == idx:
        app._premis_sort_reverse = not getattr(app, "_premis_sort_reverse", False)
    else:
        app._premis_sort_by = idx
        app._premis_sort_reverse = False
    _premis_render_page(app)

def _premis_reload(app):
    path = Path(app.cfg.premis_log)
    events = read_events(path)

    app._premis_tipo_cb.configure(values=[""] + unique_sorted([e.get("eventType") for e in events]))
    app._premis_outcome_cb.configure(values=[""] + unique_sorted([e.get("eventOutcome") for e in events]))
    app._premis_agent_cb.configure(values=[""] + unique_sorted([e.get("linkingAgentName") for e in events]))
    app._premis_object_cb.configure(values=[""] + unique_sorted([e.get("linkingObjectIdentifier") for e in events]))

    tipo = app._premis_tipo.get().strip()
    outcome = app._premis_outcome.get().strip()
    agent = app._premis_agent.get().strip()
    obj = app._premis_object.get().strip()
    query = app._premis_query.get().strip().lower()
    date_from = app._premis_from.get().strip()
    date_to = app._premis_to.get().strip()

    filtered = []
    for e in events:
        if tipo and e.get("eventType") != tipo: continue
        if outcome and e.get("eventOutcome") != outcome: continue
        if agent and e.get("linkingAgentName") != agent: continue
        if obj and e.get("linkingObjectIdentifier") != obj: continue
        if not in_range(e.get("eventDateTime", ""), date_from, date_to): continue
        if query:
            hay = " ".join([
                str(e.get("linkingObjectIdentifier", "")),
                str(e.get("eventDetail", "")),
                str(e.get("linkingAgentName", "")),
                str(e.get("eventIdentifier", "")),
            ]).lower()
            if query not in hay:
                continue
        filtered.append(event_row(e))

    app._premis_filtered_rows = filtered
    ps = max(1, int(app._premis_page_size.get() or "200"))
    app._premis_page = max(0, min(app._premis_page, (len(filtered) - 1) // ps))
    _premis_render_page(app)

def _premis_render_page(app):
    rows = list(getattr(app, "_premis_filtered_rows", []))
    sort_idx = getattr(app, "_premis_sort_by", None)
    sort_rev = getattr(app, "_premis_sort_reverse", False)
    if sort_idx is not None:
        rows = sorted(rows, key=lambda r: sort_key(sort_idx, r), reverse=sort_rev)

    cols = ("data", "tipo", "resultado", "objeto", "detalhe", "agente", "id")
    for i, c in enumerate(cols):
        base = getattr(app, "_premis_col_titles", {}).get(c, c)
        if sort_idx == i:
            arrow = "▼" if sort_rev else "▲"
            app._premis_tree.heading(c, text=f"{base} {arrow}")
        else:
            app._premis_tree.heading(c, text=base)

    page_size = max(1, int(app._premis_page_size.get() or "200"))
    start = app._premis_page * page_size
    end = start + page_size
    page_rows = rows[start:end]

    app._premis_tree.delete(*app._premis_tree.get_children())
    for r in page_rows:
        app._premis_tree.insert("", "end", values=r)

    app._premis_rows_cache = page_rows
    app._premis_rows_filtered_cache = rows

    total_pages = max(1, (len(rows) + page_size - 1) // page_size)
    app._premis_page_lbl.config(text=f"Página {app._premis_page + 1} de {total_pages} — {len(rows)} eventos")

def _premis_change_page(app, delta: int):
    rows = getattr(app, "_premis_filtered_rows", [])
    if not rows:
        return
    page_size = max(1, int(app._premis_page_size.get() or "200"))
    total_pages = max(1, (len(rows) + page_size - 1) // page_size)
    app._premis_page = max(0, min(app._premis_page + delta, total_pages - 1))
    _premis_render_page(app)

def _premis_open_log(app):
    p = filedialog.askopenfilename(
        title="Abrir eventos PREMIS (JSONL)",
        filetypes=[("JSONL", "*.jsonl"), ("Todos", "*.*")]
    )
    if not p:
        return
    app.cfg.premis_log = p
    app._premis_page = 0
    _premis_reload(app)

def _premis_export_csv(app):
    p = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv")],
        title="Exportar eventos PREMIS (todos filtrados)"
    )
    if not p:
        return
    rows = getattr(app, "_premis_rows_filtered_cache", getattr(app, "_premis_filtered_rows", []))
    export_csv(Path(p), rows)

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
