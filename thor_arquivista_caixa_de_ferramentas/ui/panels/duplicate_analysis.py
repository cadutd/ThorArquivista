# ui/panels/duplicate_analysis.py
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
from ttkbootstrap.constants import *

# -----------------------------------------------------------------------------
# Painel: Análise de Duplicatas
# Funcionalidades (cada uma com sua seção e botão):
#   1) Inventariar (SHA-256)
#   2) Detectar duplicatas
#   3) Gerar modelo de decisão
#
# Integra com job_type "DUPLICATE_FINDER" (core/scripts_map.py).
# Padrão do projeto: create_panel(parent, enqueue_cb, close_cb=None)
# -----------------------------------------------------------------------------

def create_panel(parent, enqueue_cb, close_cb=None):
    page = ttk.Frame(parent)

    # ----------------- Vars (Inventário) -----------------
    raiz_inv = tk.StringVar()
    inventario_inv = tk.StringVar()
    mostrar_progresso = tk.BooleanVar(value=True)

    # ----------------- Vars (Duplicatas) -----------------
    inventario_dup = tk.StringVar()
    duplicatas_dup = tk.StringVar()

    # ----------------- Vars (Modelo de decisões) ---------
    duplicatas_mod = tk.StringVar()
    decisoes_mod = tk.StringVar()

    # ----------------- Seção 1: Inventariar --------------
    grp_inv = ttk.LabelFrame(page, text="Inventariar (SHA-256)")
    grp_inv.pack(fill="x", padx=2, pady=(8, 6))

    _grid_pair_btn(grp_inv, 0, "Pasta raiz:", raiz_inv, pick_dir=True)
    _grid_pair_btn(grp_inv, 0, "Inventário CSV:", inventario_inv, col=3, pick_file=True, save_as=True)
    ttk.Checkbutton(grp_inv, text="Mostrar progresso", variable=mostrar_progresso).grid(row=1, column=0, sticky="w", padx=6, pady=(4, 2))

    ttk.Button(
        grp_inv,
        text="Executar inventário",
        bootstyle=PRIMARY,
        command=lambda: _exec_inventario(page, enqueue_cb, raiz_inv, inventario_inv, mostrar_progresso),
    ).grid(row=2, column=0, sticky="w", padx=6, pady=(8, 6))

    grp_inv.grid_columnconfigure(1, weight=1)
    grp_inv.grid_columnconfigure(4, weight=1)

    # ----------------- Seção 2: Detectar duplicatas ------
    grp_dup = ttk.LabelFrame(page, text="Detectar duplicatas")
    grp_dup.pack(fill="x", padx=2, pady=(6, 6))

    _grid_pair_btn(grp_dup, 0, "Inventário CSV:", inventario_dup, pick_file=True)
    _grid_pair_btn(grp_dup, 0, "Duplicatas CSV:", duplicatas_dup, col=3, pick_file=True, save_as=True)

    ttk.Button(
        grp_dup,
        text="Detectar duplicatas",
        bootstyle=PRIMARY,
        command=lambda: _exec_duplicatas(page, enqueue_cb, inventario_dup, duplicatas_dup),
    ).grid(row=1, column=0, sticky="w", padx=6, pady=(8, 6))

    grp_dup.grid_columnconfigure(1, weight=1)
    grp_dup.grid_columnconfigure(4, weight=1)

    # -------------- Seção 3: Gerar modelo de decisão -----
    grp_mod = ttk.LabelFrame(page, text="Gerar modelo de decisão")
    grp_mod.pack(fill="x", padx=2, pady=(6, 8))

    _grid_pair_btn(grp_mod, 0, "Duplicatas CSV:", duplicatas_mod, pick_file=True)
    _grid_pair_btn(grp_mod, 0, "Decisões CSV:", decisoes_mod, col=3, pick_file=True, save_as=True)

    ttk.Button(
        grp_mod,
        text="Gerar modelo de decisão",
        bootstyle=PRIMARY,
        command=lambda: _exec_modelo(page, enqueue_cb, duplicatas_mod, decisoes_mod),
    ).grid(row=1, column=0, sticky="w", padx=6, pady=(8, 8))

    grp_mod.grid_columnconfigure(1, weight=1)
    grp_mod.grid_columnconfigure(4, weight=1)

    # ----------------- Rodapé -----------------
    fr_btns = ttk.Frame(page)
    fr_btns.pack(fill="x", pady=8)
    ttk.Button(fr_btns, text="Fechar", bootstyle=DANGER, command=lambda: _close()).pack(side="left", padx=6)

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

def _exec_inventario(page, enqueue_cb, raiz_var, inventario_var, progresso_var):
    raiz = (raiz_var.get() or "").strip()
    inv = (inventario_var.get() or "").strip()
    if not raiz or not inv:
        messagebox.showwarning("Campos obrigatórios", "Informe a Pasta raiz e o caminho do Inventário CSV.", parent=page.winfo_toplevel())
        return
    payload = {
        "modo": "inventario",
        "raiz": raiz,
        "inventario": inv,
        "mostrar_progresso": bool(progresso_var.get()),
    }
    enqueue_cb("DUPLICATE_FINDER", payload)
    messagebox.showinfo("Execução iniciada", "Inventário enviado para a fila de execução.", parent=page.winfo_toplevel())


def _exec_duplicatas(page, enqueue_cb, inventario_var, duplicatas_var):
    inv = (inventario_var.get() or "").strip()
    dup = (duplicatas_var.get() or "").strip()
    if not inv or not dup:
        messagebox.showwarning("Campos obrigatórios", "Informe Inventário CSV e o caminho do Duplicatas CSV.", parent=page.winfo_toplevel())
        return
    payload = {
        "modo": "duplicatas",
        "inventario": inv,
        "duplicatas": dup,
    }
    enqueue_cb("DUPLICATE_FINDER", payload)
    messagebox.showinfo("Execução iniciada", "Detecção de duplicatas enviada para a fila de execução.", parent=page.winfo_toplevel())


def _exec_modelo(page, enqueue_cb, duplicatas_var, decisoes_var):
    dup = (duplicatas_var.get() or "").strip()
    dec = (decisoes_var.get() or "").strip()
    if not dup or not dec:
        messagebox.showwarning("Campos obrigatórios", "Informe Duplicatas CSV e o caminho do Decisões CSV.", parent=page.winfo_toplevel())
        return
    payload = {
        "modo": "modelo_decisoes",
        "duplicatas": dup,
        "decisoes": dec,
    }
    enqueue_cb("DUPLICATE_FINDER", payload)
    messagebox.showinfo("Execução iniciada", "Modelo de decisões enviado para a fila de execução.", parent=page.winfo_toplevel())


# -------------------------
# Helpers de layout
# -------------------------

_CSV_FT = [("Arquivos CSV", "*.csv")]

def _pick_dir(var: tk.StringVar):
    d = filedialog.askdirectory(title="Selecionar pasta")
    if d:
        var.set(d)


def _pick_file(var: tk.StringVar, save_as: bool = False):
    if save_as:
        p = filedialog.asksaveasfilename(title="Salvar como", defaultextension=".csv", filetypes=_CSV_FT)
    else:
        p = filedialog.askopenfilename(title="Selecionar arquivo CSV", filetypes=_CSV_FT)
    if p:
        var.set(p)


def _grid_pair(parent, row, label, var, width=None, *, col=0, colspan=1):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    entry = ttk.Entry(parent, textvariable=var, width=width or 40)
    entry.grid(row=row, column=col + 1, columnspan=colspan, sticky="we", pady=2)
    parent.grid_columnconfigure(col + 1, weight=1)


def _grid_pair_btn(parent, row, label, var, *, col=0, pick_dir=False, pick_file=False, save_as=False):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    entry = ttk.Entry(parent, textvariable=var)
    entry.grid(row=row, column=col + 1, sticky="we", pady=2)

    # Botão com ícone unicode para ação
    if pick_dir:
        ttk.Button(parent, text="📂", width=3, command=lambda: _pick_dir(var))\
           .grid(row=row, column=col + 2, sticky="w", padx=(6, 0), pady=2)
    elif pick_file:
        ttk.Button(parent, text="📄", width=3, command=lambda: _pick_file(var, save_as=save_as))\
           .grid(row=row, column=col + 2, sticky="w", padx=(6, 0), pady=2)

    parent.grid_columnconfigure(col + 1, weight=1)
