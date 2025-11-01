# ui/panels/duplicate_treatment.py
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
from ttkbootstrap.constants import *

# -----------------------------------------------------------------------------
# Painel: Tratamento de Duplicatas
# Seções (cada uma com seu botão de execução):
#   1) Gerar script de tratamento (Linux/Windows; quarentena/remover)
#   2) Dashboard — Potencial (Duplicatas)
#   3) Dashboard — Planejado (Decisões)
#
# Integra com job_type "DUPLICATE_FINDER" (core/scripts_map.py).
# Padrão do projeto: create_panel(parent, enqueue_cb, close_cb=None)
# -----------------------------------------------------------------------------

def create_panel(parent, enqueue_cb, close_cb=None):
    page = ttk.Frame(parent)

    # ----------------- Vars (Script de tratamento) -----------------
    decisoes_st = tk.StringVar()
    script_out = tk.StringVar()
    sistema = tk.StringVar(value="linux")           # linux | windows
    acao = tk.StringVar(value="quarentena")         # quarentena | remover
    prefixo_quarentena = tk.StringVar(value="quarentena")
    script_log_nome = tk.StringVar()

    # ----------------- Vars (Dashboard Duplicatas) -----------------
    inventario_dd = tk.StringVar()
    duplicatas_dd = tk.StringVar()
    dash_dup_csv = tk.StringVar()
    dash_dup_xlsx = tk.StringVar()

    # ----------------- Vars (Dashboard Decisões) -------------------
    inventario_dm = tk.StringVar()
    decisoes_dm = tk.StringVar()
    dash_dec_csv = tk.StringVar()
    dash_dec_xlsx = tk.StringVar()

    # ----------------- Seção 1: Script de tratamento ----------------
    grp_st = ttk.LabelFrame(page, text="Gerar script de tratamento")
    grp_st.pack(fill="x", padx=2, pady=(8, 6))

    _grid_pair_btn(grp_st, 0, "Decisões CSV:", decisoes_st, pick_file=True, csv_only=True)
    _grid_pair_btn(grp_st, 0, "Script de saída (.sh/.cmd):", script_out, col=3, pick_file=True, save_as=True, script_ft=True)

    ttk.Label(grp_st, text="Sistema:").grid(row=1, column=0, sticky="e", padx=(6, 4), pady=(6, 0))
    ttk.Combobox(grp_st, textvariable=sistema, state="readonly", values=["linux", "windows"], width=12)\
        .grid(row=1, column=1, sticky="w", padx=(0, 6), pady=(6, 0))

    ttk.Label(grp_st, text="Ação:").grid(row=1, column=2, sticky="e", padx=(6, 4), pady=(6, 0))
    ttk.Combobox(grp_st, textvariable=acao, state="readonly", values=["quarentena", "remover"], width=14)\
        .grid(row=1, column=3, sticky="w", padx=(0, 6), pady=(6, 0))

    _grid_pair(grp_st, 2, "Prefixo quarentena:", prefixo_quarentena, width=22, col=0)
    _grid_pair(grp_st, 2, "Nome do log (opcional):", script_log_nome, width=40, col=2)

    ttk.Button(
        grp_st,
        text="Gerar script",
        bootstyle=PRIMARY,
        command=lambda: _exec_script_tratamento(page, enqueue_cb, decisoes_st, script_out, sistema, acao, prefixo_quarentena, script_log_nome),
    ).grid(row=3, column=0, sticky="w", padx=6, pady=(8, 6))

    grp_st.grid_columnconfigure(1, weight=1)
    grp_st.grid_columnconfigure(4, weight=1)

    # ----------------- Seção 2: Dashboard — Potencial (Duplicatas) --
    grp_dd = ttk.LabelFrame(page, text="Dashboard — Potencial (Duplicatas)")
    grp_dd.pack(fill="x", padx=2, pady=(6, 6))

    _grid_pair_btn(grp_dd, 0, "Inventário CSV:", inventario_dd, pick_file=True, csv_only=True)
    _grid_pair_btn(grp_dd, 0, "Duplicatas CSV:", duplicatas_dd, col=3, pick_file=True, csv_only=True)

    _grid_pair_btn(grp_dd, 1, "Dashboard CSV (saída):", dash_dup_csv, pick_file=True, save_as=True, csv_only=True)
    _grid_pair_btn(grp_dd, 1, "Dashboard XLSX (opcional):", dash_dup_xlsx, col=3, pick_file=True, save_as=True, xlsx_only=True)

    ttk.Button(
        grp_dd,
        text="Gerar dashboard (duplicatas)",
        bootstyle=PRIMARY,
        command=lambda: _exec_dashboard_duplicatas(page, enqueue_cb, inventario_dd, duplicatas_dd, dash_dup_csv, dash_dup_xlsx),
    ).grid(row=2, column=0, sticky="w", padx=6, pady=(8, 6))

    grp_dd.grid_columnconfigure(1, weight=1)
    grp_dd.grid_columnconfigure(4, weight=1)

    # ----------------- Seção 3: Dashboard — Planejado (Decisões) ----
    grp_dm = ttk.LabelFrame(page, text="Dashboard — Planejado (Decisões)")
    grp_dm.pack(fill="x", padx=2, pady=(6, 8))

    _grid_pair_btn(grp_dm, 0, "Inventário CSV:", inventario_dm, pick_file=True, csv_only=True)
    _grid_pair_btn(grp_dm, 0, "Decisões CSV:", decisoes_dm, col=3, pick_file=True, csv_only=True)

    _grid_pair_btn(grp_dm, 1, "Dashboard CSV (saída):", dash_dec_csv, pick_file=True, save_as=True, csv_only=True)
    _grid_pair_btn(grp_dm, 1, "Dashboard XLSX (opcional):", dash_dec_xlsx, col=3, pick_file=True, save_as=True, xlsx_only=True)

    ttk.Button(
        grp_dm,
        text="Gerar dashboard (decisões)",
        bootstyle=PRIMARY,
        command=lambda: _exec_dashboard_decisoes(page, enqueue_cb, inventario_dm, decisoes_dm, dash_dec_csv, dash_dec_xlsx),
    ).grid(row=2, column=0, sticky="w", padx=6, pady=(8, 8))

    grp_dm.grid_columnconfigure(1, weight=1)
    grp_dm.grid_columnconfigure(4, weight=1)

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

def _exec_script_tratamento(page, enqueue_cb, decisoes_var, script_out_var, sistema_var, acao_var, prefixo_var, log_var):
    dec = (decisoes_var.get() or "").strip()
    out = (script_out_var.get() or "").strip()
    if not dec or not out:
        messagebox.showwarning("Campos obrigatórios", "Informe Decisões CSV e o arquivo do Script de saída.", parent=page.winfo_toplevel())
        return
    payload = {
        "modo": "script_tratamento",
        "decisoes": dec,
        "gerar_script_remocao": out,
        "sistema": (sistema_var.get() or "linux").strip(),
        "acao": (acao_var.get() or "quarentena").strip(),
        "prefixo_quarentena": (prefixo_var.get() or "quarentena").strip(),
    }
    logname = (log_var.get() or "").strip()
    if logname:
        payload["script_log_nome"] = logname
    enqueue_cb("DUPLICATE_FINDER", payload)
    messagebox.showinfo("Execução iniciada", "Geração de script enviada para a fila de execução.", parent=page.winfo_toplevel())


def _exec_dashboard_duplicatas(page, enqueue_cb, inventario_var, duplicatas_var, dash_csv_var, dash_xlsx_var):
    inv = (inventario_var.get() or "").strip()
    dup = (duplicatas_var.get() or "").strip()
    dcsv = (dash_csv_var.get() or "").strip()
    dxlsx = (dash_xlsx_var.get() or "").strip()
    if not inv or not dup or not dcsv:
        messagebox.showwarning("Campos obrigatórios", "Informe Inventário CSV, Duplicatas CSV e o caminho do Dashboard CSV.", parent=page.winfo_toplevel())
        return
    payload = {
        "modo": "dashboard_duplicatas",
        "inventario": inv,
        "duplicatas": dup,
        "dashboard_duplicatas_csv": dcsv,
    }
    if dxlsx:
        payload["dashboard_duplicatas_xlsx"] = dxlsx
    enqueue_cb("DUPLICATE_FINDER", payload)
    messagebox.showinfo("Execução iniciada", "Dashboard de duplicatas enviado para a fila de execução.", parent=page.winfo_toplevel())


def _exec_dashboard_decisoes(page, enqueue_cb, inventario_var, decisoes_var, dash_csv_var, dash_xlsx_var):
    inv = (inventario_var.get() or "").strip()
    dec = (decisoes_var.get() or "").strip()
    dcsv = (dash_csv_var.get() or "").strip()
    dxlsx = (dash_xlsx_var.get() or "").strip()
    if not inv or not dec or not dcsv:
        messagebox.showwarning("Campos obrigatórios", "Informe Inventário CSV, Decisões CSV e o caminho do Dashboard CSV.", parent=page.winfo_toplevel())
        return
    payload = {
        "modo": "dashboard_decisoes",
        "inventario": inv,
        "decisoes": dec,
        "dashboard_decisoes_csv": dcsv,
    }
    if dxlsx:
        payload["dashboard_decisoes_xlsx"] = dxlsx
    enqueue_cb("DUPLICATE_FINDER", payload)
    messagebox.showinfo("Execução iniciada", "Dashboard de decisões enviado para a fila de execução.", parent=page.winfo_toplevel())


# -------------------------
# Helpers de layout
# -------------------------

_CSV_FT = [("Arquivos CSV", "*.csv")]
_XLSX_FT = [("Planilha Excel", "*.xlsx")]
_SCRIPT_FT = [("Script Linux (.sh)", "*.sh"), ("Script Windows (.cmd)", "*.cmd"), ("Todos os arquivos", "*.*")]

def _pick_dir(var: tk.StringVar):
    d = filedialog.askdirectory(title="Selecionar pasta")
    if d:
        var.set(d)


def _pick_file(var: tk.StringVar, save_as: bool = False, *, csv_only=False, xlsx_only=False, script_ft=False):
    # Decide filtros conforme contexto
    if script_ft:
        ftypes = _SCRIPT_FT
        default_ext = ".sh"
    elif xlsx_only:
        ftypes = _XLSX_FT
        default_ext = ".xlsx"
    elif csv_only:
        ftypes = _CSV_FT
        default_ext = ".csv"
    else:
        # fallback genérico
        ftypes = [("Todos os arquivos", "*.*")]
        default_ext = ""

    if save_as:
        p = filedialog.asksaveasfilename(title="Salvar como", defaultextension=default_ext, filetypes=ftypes)
    else:
        p = filedialog.askopenfilename(title="Selecionar arquivo", filetypes=ftypes)
    if p:
        var.set(p)


def _grid_pair(parent, row, label, var, width=None, *, col=0, colspan=1):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    entry = ttk.Entry(parent, textvariable=var, width=width or 40)
    entry.grid(row=row, column=col + 1, columnspan=colspan, sticky="we", pady=2)
    parent.grid_columnconfigure(col + 1, weight=1)


def _grid_pair_btn(parent, row, label, var, *, col=0, pick_dir=False, pick_file=False, save_as=False, csv_only=False, xlsx_only=False, script_ft=False):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    entry = ttk.Entry(parent, textvariable=var)
    entry.grid(row=row, column=col + 1, sticky="we", pady=2)

    if pick_dir:
        ttk.Button(parent, text="📂", width=3, command=lambda: _pick_dir(var))\
           .grid(row=row, column=col + 2, sticky="w", padx=(6, 0), pady=2)
    elif pick_file:
        ttk.Button(parent, text="📄", width=3, command=lambda: _pick_file(var, save_as=save_as, csv_only=csv_only, xlsx_only=xlsx_only, script_ft=script_ft))\
           .grid(row=row, column=col + 2, sticky="w", padx=(6, 0), pady=2)

    parent.grid_columnconfigure(col + 1, weight=1)
