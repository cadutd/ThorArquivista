# ui/panels/duplicate_finder.py
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Icon

# ---------------------------------------------------------------------------------
# Painel: Localizar Duplicidades (integra com job_type "DUPLICATE_FINDER")
# Segue o mesmo padrão do projeto: create_panel(parent, enqueue_cb, close_cb=None)
# ---------------------------------------------------------------------------------

def create_panel(parent, enqueue_cb, close_cb=None):
    """
    Mantém o padrão dos demais painéis:
    - cria 'page' (Frame)
    - define handler local _exec()
    - retorna 'page'
    """
    page = ttk.Frame(parent)

    # ----------------- Vars principais -----------------
    modo = tk.StringVar(value="inventario")  # inventario | duplicatas | modelo_decisoes | script_tratamento | dashboard_duplicatas | dashboard_decisoes

    # Comuns
    raiz = tk.StringVar()              # para inventário
    inventario = tk.StringVar()        # caminho CSV
    duplicatas = tk.StringVar()        # caminho CSV
    decisoes = tk.StringVar()          # caminho CSV
    mostrar_progresso = tk.BooleanVar(value=True)

    # Script de tratamento
    script_saida = tk.StringVar()      # .sh ou .cmd
    sistema = tk.StringVar(value="linux")  # linux | windows
    acao = tk.StringVar(value="quarentena")  # quarentena | remover
    prefixo_quarentena = tk.StringVar(value="quarentena")
    script_log_nome = tk.StringVar()   # opcional

    # Dashboards
    dash_dup_csv = tk.StringVar()
    dash_dup_xlsx = tk.StringVar()
    dash_dec_csv = tk.StringVar()
    dash_dec_xlsx = tk.StringVar()

    # ----------------- Layout -----------------
    # Modo de execução (linha superior)
    grp_modo = ttk.LabelFrame(page, text="Modo de execução")
    grp_modo.pack(fill="x", pady=6)

    modos = [
        ("Inventariar (SHA-256)", "inventario"),
        ("Detectar duplicatas", "duplicatas"),
        ("Gerar modelo de decisões", "modelo_decisoes"),
        ("Gerar script de tratamento", "script_tratamento"),
        ("Dashboard — Potencial (Duplicatas)", "dashboard_duplicatas"),
        ("Dashboard — Planejado (Decisões)", "dashboard_decisoes"),
    ]
    r = 0
    for label, val in modos:
        ttk.Radiobutton(grp_modo, text=label, value=val, variable=modo).grid(row=0, column=r, sticky="w", padx=(6 if r == 0 else 12, 0), pady=6)
        r += 1

    # Seções de parâmetros
    grp_paths = ttk.LabelFrame(page, text="Parâmetros principais")
    grp_paths.pack(fill="x", pady=6)

    # Linha 1
    _grid_pair_btn(grp_paths, 0, "Pasta raiz (inventário):", raiz, pick_dir=True)
    _grid_pair_btn(grp_paths, 0, "Inventário CSV:", inventario, col=3, pick_file=True, save_as=True)

    # Linha 2
    _grid_pair_btn(grp_paths, 1, "Duplicatas CSV:", duplicatas, pick_file=True, save_as=True)
    _grid_pair_btn(grp_paths, 1, "Decisões CSV:", decisoes, col=3, pick_file=True, save_as=True)

    # Linha 3
    ttk.Checkbutton(grp_paths, text="Mostrar progresso (inventário)", variable=mostrar_progresso).grid(row=2, column=0, sticky="w", padx=6, pady=(4, 2))

    grp_paths.grid_columnconfigure(1, weight=1)
    grp_paths.grid_columnconfigure(4, weight=1)

    # Script de tratamento
    grp_script = ttk.LabelFrame(page, text="Script de tratamento (quarentena/remover)")
    grp_script.pack(fill="x", pady=4)

    _grid_pair_btn(grp_script, 0, "Script de saída (.sh/.cmd):", script_saida, pick_file=True, save_as=True)
    ttk.Label(grp_script, text="Sistema:").grid(row=0, column=3, sticky="e", padx=(6, 4))
    ttk.Combobox(grp_script, textvariable=sistema, state="readonly", values=["linux", "windows"], width=10).grid(row=0, column=4, sticky="w", padx=(0, 6) )

    ttk.Label(grp_script, text="Ação:").grid(row=1, column=0, sticky="e", padx=(6, 4), pady=(6, 0))
    ttk.Combobox(grp_script, textvariable=acao, state="readonly", values=["quarentena", "remover"], width=14).grid(row=1, column=1, sticky="w", padx=(0, 6), pady=(6, 0))

    _grid_pair(grp_script, 1, "Prefixo quarentena:", prefixo_quarentena, width=22, col=2)
    _grid_pair(grp_script, 2, "Nome do log (opcional):", script_log_nome, width=42, col=0, colspan=3)

    grp_script.grid_columnconfigure(1, weight=1)
    grp_script.grid_columnconfigure(4, weight=1)

    # Dashboards
    grp_dash = ttk.LabelFrame(page, text="Dashboards")
    grp_dash.pack(fill="x", pady=6)

    _grid_pair_btn(grp_dash, 0, "Dash (Duplicatas) CSV:", dash_dup_csv, pick_file=True, save_as=True)
    _grid_pair_btn(grp_dash, 0, "Dash (Duplicatas) XLSX:", dash_dup_xlsx, col=3, pick_file=True, save_as=True)
    _grid_pair_btn(grp_dash, 1, "Dash (Decisões) CSV:", dash_dec_csv, pick_file=True, save_as=True)
    _grid_pair_btn(grp_dash, 1, "Dash (Decisões) XLSX:", dash_dec_xlsx, col=3, pick_file=True, save_as=True)

    grp_dash.grid_columnconfigure(1, weight=1)
    grp_dash.grid_columnconfigure(4, weight=1)

    # Rodapé botões
    fr_btns = ttk.Frame(page)
    fr_btns.pack(fill="x", pady=8)
    ttk.Button(fr_btns, text="Executar", bootstyle=PRIMARY, command=lambda: _exec()).pack(side="left")
    ttk.Button(fr_btns, text="Fechar", bootstyle=DANGER, command=lambda: _close()).pack(side="left", padx=6)

    # ----------------- Funções locais -----------------

    def _pick_dir(var: tk.StringVar):
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    def _pick_file(var: tk.StringVar, save_as=False):
        if save_as:
            p = filedialog.asksaveasfilename()
        else:
            p = filedialog.askopenfilename()
        if p:
            var.set(p)

    def _close():
        # Padrão: permitir fechar o painel
        if callable(close_cb):
            try:
                close_cb(page)
                return
            except Exception:
                pass
        # fallback
        try:
            page.destroy()
        except Exception:
            pass

    def _exec():
        # Monta payload conforme "modo", alinhado ao core/scripts_map.py
        m = modo.get().strip()
        if m == "inventario":
            if not raiz.get().strip() or not inventario.get().strip():
                messagebox.showwarning("Campos obrigatórios", "Informe a Pasta raiz e o caminho do Inventário CSV.")
                return
            payload = {
                "modo": "inventario",
                "raiz": raiz.get().strip(),
                "inventario": inventario.get().strip(),
                "mostrar_progresso": bool(mostrar_progresso.get()),
            }

        elif m == "duplicatas":
            if not inventario.get().strip() or not duplicatas.get().strip():
                messagebox.showwarning("Campos obrigatórios", "Informe Inventário CSV e o caminho do Duplicatas CSV.")
                return
            payload = {
                "modo": "duplicatas",
                "inventario": inventario.get().strip(),
                "duplicatas": duplicatas.get().strip(),
            }

        elif m == "modelo_decisoes":
            if not duplicatas.get().strip() or not decisoes.get().strip():
                messagebox.showwarning("Campos obrigatórios", "Informe Duplicatas CSV e Decisões CSV.")
                return
            payload = {
                "modo": "modelo_decisoes",
                "duplicatas": duplicatas.get().strip(),
                "decisoes": decisoes.get().strip(),
            }

        elif m == "script_tratamento":
            if not decisoes.get().strip() or not script_saida.get().strip():
                messagebox.showwarning("Campos obrigatórios", "Informe Decisões CSV e o arquivo do Script de saída.")
                return
            payload = {
                "modo": "script_tratamento",
                "decisoes": decisoes.get().strip(),
                "gerar_script_remocao": script_saida.get().strip(),
                "sistema": sistema.get().strip() or "linux",
                "acao": acao.get().strip() or "quarentena",
                "prefixo_quarentena": prefixo_quarentena.get().strip() or "quarentena",
            }
            if script_log_nome.get().strip():
                payload["script_log_nome"] = script_log_nome.get().strip()

        elif m == "dashboard_duplicatas":
            if not inventario.get().strip() or not duplicatas.get().strip() or not dash_dup_csv.get().strip():
                messagebox.showwarning("Campos obrigatórios", "Informe Inventário CSV, Duplicatas CSV e o caminho do Dashboard CSV.")
                return
            payload = {
                "modo": "dashboard_duplicatas",
                "inventario": inventario.get().strip(),
                "duplicatas": duplicatas.get().strip(),
                "dashboard_duplicatas_csv": dash_dup_csv.get().strip(),
            }
            if dash_dup_xlsx.get().strip():
                payload["dashboard_duplicatas_xlsx"] = dash_dup_xlsx.get().strip()

        elif m == "dashboard_decisoes":
            if not inventario.get().strip() or not decisoes.get().strip() or not dash_dec_csv.get().strip():
                messagebox.showwarning("Campos obrigatórios", "Informe Inventário CSV, Decisões CSV e o caminho do Dashboard CSV.")
                return
            payload = {
                "modo": "dashboard_decisoes",
                "inventario": inventario.get().strip(),
                "decisoes": decisoes.get().strip(),
                "dashboard_decisoes_csv": dash_dec_csv.get().strip(),
            }
            if dash_dec_xlsx.get().strip():
                payload["dashboard_decisoes_xlsx"] = dash_dec_xlsx.get().strip()
        else:
            messagebox.showwarning("Modo inválido", f"Modo não reconhecido: {m}")
            return

        # Enfileira o job
        enqueue_cb("DUPLICATE_FINDER", payload)

        # Feedback
        parent_win = page.winfo_toplevel() if hasattr(page, "winfo_toplevel") else page
        messagebox.showinfo("Execução iniciada", "O job foi enviado para a fila de execução.", parent=parent_win)

    return page

# -------------------------
# Helpers de layout
# -------------------------

    return page


# -------------------------
# Helpers de layout
# -------------------------

def _pick_dir(var: tk.StringVar):
    """Abre seletor de diretório e define o valor no campo."""
    d = filedialog.askdirectory(title="Selecionar pasta raiz")    
    if d:
        var.set(d)


def _pick_file(var: tk.StringVar, save_as=False):
    """Abre seletor de arquivo (open/save) e define o valor no campo."""
    if save_as:
        p = filedialog.asksaveasfilename()
    else:
        p = filedialog.askopenfilename()
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

    if pick_dir:
        ttk.Button(parent, text="📂", command=lambda: _pick_dir(var)).grid(row=row, column=col + 2, padx=(6, 0), pady=2)
    elif pick_file:
        ttk.Button(parent, text="📄", command=lambda: _pick_file(var, save_as=save_as)).grid(row=row, column=col + 2, padx=(6, 0), pady=2)
    parent.grid_columnconfigure(col + 1, weight=1)
