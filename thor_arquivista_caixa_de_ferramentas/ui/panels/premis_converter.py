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

# ui/panels/premis_converter.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# -----------------------------------------------------------------------------
# Painel: PREMIS — Conversor/Validador (XML ⇄ CSV ⇄ JSON)
#
# Integra com job_type "PREMIS_CONVERTER" (core/scripts_map.py).
# Padrão do projeto: create_panel(parent, enqueue_cb, close_cb=None)
#
# Campos:
#   - Entrada (XML/CSV/JSON)
#   - Saída   (XML/CSV/JSON) [opcional, deduzível]
#   - Validar XML contra XSD (checkbox)
#   - XSD do PREMIS (opcional)
# Ações:
#   - Converter / Validar
#   - Gerar exemplos (./examples)
# -----------------------------------------------------------------------------

def create_panel(parent, enqueue_cb, close_cb=None):
    page = tb.Frame(parent)

    # ----------------- Vars -----------------
    var_in = tk.StringVar()
    var_out = tk.StringVar()
    var_validate = tk.BooleanVar(value=False)
    var_schema = tk.StringVar(value=_default_schema_guess(parent))

    # ----------------- Seção principal -----------------
    grp = ttk.LabelFrame(page, text="PREMIS — Conversor/Validador")
    grp.pack(fill="x", padx=2, pady=(8, 6))

    _grid_pair_btn_any(grp, 0, "Arquivo de entrada:", var_in, filetypes=_FILE_FT, pick_file=True, on_change=lambda: _auto_suggest_out(var_in, var_out))
    _grid_pair_btn_any(grp, 0, "Arquivo de saída:", var_out, col=3, filetypes=_FILE_FT, pick_file=True, save_as=True)

    tb.Checkbutton(grp, text="Validar XML contra XSD", variable=var_validate).grid(row=1, column=0, sticky="w", padx=6, pady=(4, 2))
    _grid_pair_btn_any(grp, 2, "XSD (opcional):", var_schema, filetypes=_XSD_FT, pick_file=True)

    tb.Button(
        grp,
        text="Converter / Validar",
        bootstyle=PRIMARY,
        command=lambda: _exec_convert(page, enqueue_cb, var_in, var_out, var_validate, var_schema),
    ).grid(row=3, column=0, sticky="w", padx=6, pady=(8, 6))

    tb.Button(
        grp,
        text="Gerar exemplos (./examples)",
        bootstyle=INFO,
        command=lambda: _exec_examples(page, enqueue_cb, var_schema),
    ).grid(row=3, column=1, sticky="w", padx=6, pady=(8, 6))

    grp.grid_columnconfigure(1, weight=1)
    grp.grid_columnconfigure(4, weight=1)

    # ----------------- Rodapé -----------------
    fr_btns = tb.Frame(page)
    fr_btns.pack(fill="x", pady=8)
    tb.Button(fr_btns, text="Fechar", bootstyle=DANGER, command=lambda: _close())\
      .pack(side="left", padx=6)

    # ----------------- Funções locais -----------------
    def _close():
        """Fecha o painel, chamando callback externo se fornecido."""
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


# -------------------------
# Exec handlers
# -------------------------

def _exec_convert(page, enqueue_cb, in_var, out_var, validate_var, schema_var):
    in_path = (in_var.get() or "").strip()
    out_path = (out_var.get() or "").strip()
    if not in_path:
        messagebox.showwarning("Campos obrigatórios", "Informe o caminho do arquivo de entrada.", parent=page.winfo_toplevel())
        return

    payload = {
        # aceita PT/EN no scripts_map (_args_premis_converter)
        "entrada": in_path,
        "saida": out_path if out_path else None,
        "validar": bool(validate_var.get()),
        "schema": (schema_var.get() or "").strip() or None,
    }
    # remove None para payload mais limpo
    payload = {k: v for k, v in payload.items() if v is not None}

    enqueue_cb("PREMIS_CONVERTER", payload)
    messagebox.showinfo("Execução iniciada", "Conversão/validação enviada para a fila de execução.", parent=page.winfo_toplevel())


def _exec_examples(page, enqueue_cb, schema_var):
    payload = {
        "exemplo": True,
    }
    schema = (schema_var.get() or "").strip()
    if schema:
        payload["schema"] = schema

    enqueue_cb("PREMIS_CONVERTER", payload)
    messagebox.showinfo("Execução iniciada", "Geração de exemplos enviada para a fila de execução.", parent=page.winfo_toplevel())


# -------------------------
# Helpers de layout / pickers
# -------------------------

_FILE_FT = [("Todos", "*.*"), ("XML", "*.xml"), ("CSV", "*.csv"), ("JSON", "*.json")]
_XSD_FT  = [("XSD", "*.xsd"), ("Todos", "*.*")]

def _pick_file_any(var: tk.StringVar, *, save_as: bool = False, filetypes=None):
    filetypes = filetypes or _FILE_FT
    if save_as:
        p = filedialog.asksaveasfilename(title="Salvar como", filetypes=filetypes)
    else:
        p = filedialog.askopenfilename(title="Selecionar arquivo", filetypes=filetypes)
    if p:
        var.set(p)

def _grid_pair(parent, row, label, var, width=None, *, col=0, colspan=1):
    tb.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    entry = tb.Entry(parent, textvariable=var, width=width or 40)
    entry.grid(row=row, column=col + 1, columnspan=colspan, sticky="we", pady=2)
    parent.grid_columnconfigure(col + 1, weight=1)

def _grid_pair_btn_any(parent, row, label, var, *, col=0, filetypes=None, pick_file=False, save_as=False, on_change=None):
    tb.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    entry = tb.Entry(parent, textvariable=var)
    entry.grid(row=row, column=col + 1, sticky="we", pady=2)
    if on_change:
        var.trace_add("write", lambda *_: on_change())

    if pick_file:
        tb.Button(parent, text="📄", width=3, command=lambda: _pick_file_any(var, save_as=save_as, filetypes=filetypes))\
           .grid(row=row, column=col + 2, sticky="w", padx=(6, 0), pady=2)

    parent.grid_columnconfigure(col + 1, weight=1)


# -------------------------
# Outras utilidades
# -------------------------

def _default_schema_guess(widget) -> str:
    """
    Tenta adivinhar o caminho do XSD no layout do projeto:
      <repo>/thor_arquivista_caixa_de_ferramentas/schemas/premis-v3-0.xsd
    Caso não exista, retorna string vazia.
    """
    try:
        here = Path(widget.winfo_toplevel().winfo_pathname(widget.winfo_id())).resolve()
    except Exception:
        here = None

    # Sobe na árvore para encontrar a pasta 'thor_arquivista_caixa_de_ferramentas'
    try:
        from pathlib import Path
        cwd = Path.cwd()
        # heurística simples: procurar a pasta alvo subindo até 5 níveis
        cur = cwd
        for _ in range(5):
            candidate = cur / "thor_arquivista_caixa_de_ferramentas" / "schemas" / "premis-v3-0.xsd"
            if candidate.exists():
                return candidate.as_posix()
            cur = cur.parent
    except Exception:
        pass
    return ""  # fallback

def _auto_suggest_out(var_in: tk.StringVar, var_out: tk.StringVar):
    """Sugere saída a partir da extensão da entrada quando saída estiver vazia."""
    if (var_out.get() or "").strip():
        return
    in_path = (var_in.get() or "").strip()
    if not in_path:
        return
    import os
    root, ext = os.path.splitext(in_path.lower())
    if ext == ".xml":
        var_out.set(root + ".csv")
    elif ext == ".csv":
        var_out.set(root + ".xml")
    elif ext == ".json":
        var_out.set(root + ".xml")
    else:
        var_out.set(in_path + ".out")
