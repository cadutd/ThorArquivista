# ui/panels/hash_manifest.py
from __future__ import annotations
from pathlib import Path
import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, IntVar, filedialog
from tkinter import X

ALGOS = ["sha256", "sha512", "md5", "sha1", "blake2b", "blake2s"]
_MANIFEST_RE = re.compile(r"manifest-[A-Za-z0-9_]+\.txt$", re.IGNORECASE)

def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    # Barra superior com botão de fechar
    topbar = ttk.Frame(page); topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER,
               command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    # Variáveis de controle
    raiz = StringVar(value="")
    saida = StringVar(value="")
    algo = StringVar(value="sha256")
    show_progress = IntVar(value=0)
    ignore_hidden = IntVar(value=1)

    # Pasta raiz
    r1 = ttk.Frame(page); r1.pack(fill=X, pady=5)
    ttk.Label(r1, text="Pasta Raiz").pack(side=LEFT, padx=4)
    ttk.Entry(r1, textvariable=raiz).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r1, text="Procurar…", command=lambda: _ask_dir(raiz, saida, algo)).pack(side=LEFT, padx=6)

    # Arquivo de saída
    r2 = ttk.Frame(page); r2.pack(fill=X, pady=5)
    ttk.Label(r2, text="Arquivo de saída").pack(side=LEFT, padx=4)
    ttk.Entry(r2, textvariable=saida).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(r2, text="Salvar como…", command=lambda: _ask_save(saida, raiz, algo)).pack(side=LEFT, padx=6)

    # Algoritmo
    r_alg = ttk.Frame(page); r_alg.pack(fill=X, pady=5)
    ttk.Label(r_alg, text="Algoritmo").pack(side=LEFT, padx=4)
    cb_algo = ttk.Combobox(r_alg, textvariable=algo, values=ALGOS, state="readonly", width=14)
    cb_algo.pack(side=LEFT)

    # Atualiza sugestão ao trocar algoritmo
    cb_algo.bind("<<ComboboxSelected>>", lambda e: _suggest_output_filename(raiz, saida, algo))

    # Opções
    r3 = ttk.Frame(page); r3.pack(fill=X, pady=5)
    ttk.Checkbutton(r3, text="Mostrar progresso", variable=show_progress,
                    bootstyle="round-toggle").pack(side=LEFT, padx=4)
    ttk.Checkbutton(r3, text="Ignorar arquivos ocultos", variable=ignore_hidden,
                    bootstyle="round-toggle").pack(side=LEFT, padx=10)

    # Botão Executar
    def _exec():
        enqueue_cb("HASH_MANIFEST", {
            "raiz": raiz.get(),
            "saida": saida.get(),
            "algo": algo.get().strip() or "sha256",
            "progress": bool(show_progress.get()),
            "ignore_hidden": bool(ignore_hidden.get()),
        })

    ttk.Button(page, text="Executar", bootstyle=PRIMARY, command=_exec).pack(pady=10)
    return page

# --------- helpers ---------
def _suggest_output_filename(raiz_var: StringVar, saida_var: StringVar, algo_var: StringVar):
    raiz_path = Path(raiz_var.get().strip()) if raiz_var.get().strip() else None
    saida_txt = saida_var.get().strip()
    algo = (algo_var.get() or "sha256").strip().lower()
    new_name = f"manifest-{algo}.txt"

    # regra 1 — se saída estiver vazia → sugere baseada na raiz
    if not saida_txt:
        suggested = raiz_path / new_name if raiz_path else Path(new_name)
        saida_var.set(str(suggested))
        return

    saida_path = Path(saida_txt)
    if _MANIFEST_RE.match(saida_path.name):
        # substitui o nome mantendo o diretório existente
        dirn = saida_path.parent if saida_path.parent != Path("") else (raiz_path or Path.cwd())
        saida_var.set(str(dirn / new_name))
    # caso contrário, respeita o que o usuário já digitou

def _ask_dir(raiz_var: StringVar, saida_var: StringVar, algo_var: StringVar):
    p = filedialog.askdirectory(title="Selecionar pasta raiz")
    if p:
        raiz_var.set(str(Path(p)))
        if not (saida_var.get() or "").strip():
            _suggest_output_filename(raiz_var, saida_var, algo_var)

def _ask_save(saida_var: StringVar, raiz_var: StringVar, algo_var: StringVar):
    algo = (algo_var.get() or "sha256").strip().lower()
    initialfile = f"manifest-{algo}.txt"
    initialdir = raiz_var.get().strip() or str(Path.home())
    p = filedialog.asksaveasfilename(
        title="Salvar manifesto como",
        defaultextension=".txt",
        initialfile=initialfile,
        initialdir=initialdir,
        filetypes=[("Manifesto BagIt", "manifest-*.txt"), ("TXT", "*.txt"), ("Todos", "*.*")]
    )
    if p:
        saida_var.set(str(Path(p)))

def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
