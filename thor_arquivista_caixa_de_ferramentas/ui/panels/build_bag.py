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

# thor_arquivista_caixa_de_ferramentas/panels/build_bag.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
from ttkbootstrap.constants import *

# -------------------------
# Utilidades do painel
# -------------------------
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")

# Placeholders calculados pelo script (não pedimos na UI)
_CALCULATED_KEYS = {
    "bagging_date",
    "payload_oxum",
    "algo",
    "total_bytes",
    "file_count",
    "src",
    "dst",
    "bag_software_agent",
}

# Chaves já cobertas por campos padrão do painel
_STANDARD_META_KEYS = {
    "organization",
    "source_organization",
    "contact_name",
    "contact_email",
    "external_description",
}

def _repo_root_from_here() -> Path:
    # panels/build_bag.py  -> repo root
    return Path(__file__).resolve().parents[2]

def _find_profiles() -> List[Tuple[str, Path]]:
    """
    Procura profiles na pasta <repo_root>/profiles com padrão *-profileBagit.json.
    Retorna [(nome_logico, caminho), ...]
    """
    profiles_dir = _repo_root_from_here() / "profiles"
    out: List[Tuple[str, Path]] = []
    if profiles_dir.exists():
        for p in sorted(profiles_dir.glob("*-profileBagit.json")):
            out.append((p.name.replace("-profileBagit.json", ""), p))
    return out

def _load_profile(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "bag_info" not in data or not isinstance(data["bag_info"], dict):
        raise ValueError(f"Profile inválido: {path} (faltando objeto 'bag_info')")
    data.setdefault("required_tags", [])
    return data

def _extract_placeholders(profile_data: Dict) -> List[str]:
    keys = set()
    for val in profile_data.get("bag_info", {}).values():
        if isinstance(val, str):
            for m in _PLACEHOLDER_RE.finditer(val):
                keys.add(m.group(1))
    # remove calculados e já mapeados por campos padrão
    keys = keys - _CALCULATED_KEYS - _STANDARD_META_KEYS
    return sorted(keys)

# -------------------------
# Fábrica no padrão do projeto
# -------------------------
def create_panel(parent, enqueue_cb, close_cb=None):
    """
    Mantém o mesmo padrão do hash_manifest.py:
    - cria 'page' (Frame)
    - define handler local _exec()
    - retorna 'page'
    """
    page = ttk.Frame(parent)

    # ----------------- Vars principais -----------------
    raiz = tk.StringVar()
    destino = tk.StringVar()
    algo = tk.StringVar(value="sha256")
    modo = tk.StringVar(value="copy")
    pattern = tk.StringVar(value="*")
    include_hidden = tk.BooleanVar(value=False)
    follow_symlinks = tk.BooleanVar(value=False)
    tagmanifest = tk.BooleanVar(value=False)

    organization = tk.StringVar()
    source_organization = tk.StringVar()
    contact_name = tk.StringVar()
    contact_email = tk.StringVar()
    external_description = tk.StringVar()

    # Profile
    profile_choice = tk.StringVar()
    profile_map: Dict[str, Path] = {name: p for name, p in _find_profiles()}
    current_profile_path: Path | None = None
    current_profile_data: Dict | None = None

    # Placeholders dinâmicos (k -> StringVar)
    dynamic_params: Dict[str, tk.StringVar] = {}

    # ----------------- Layout simples (pack) -----------------
    # Título
    # ttk.Label(page, text="Gerar Pacote BagIt", font="-size 11 -weight bold").pack(anchor="w", pady=(0, 6))

    # Pasta fonte/destino
    fr_paths = ttk.Frame(page)
    fr_paths.pack(fill="x", pady=2)
    ttk.Label(fr_paths, text="Pasta fonte (payload):").grid(row=0, column=0, sticky="w")
    ttk.Entry(fr_paths, textvariable=raiz, width=60).grid(row=0, column=1, sticky="we", padx=4)
    ttk.Button(fr_paths, text="Selecionar…", command=lambda: _pick_dir(raiz)).grid(row=0, column=2, sticky="w")

    ttk.Label(fr_paths, text="Pasta destino (bag):").grid(row=1, column=0, sticky="w", pady=(4, 0))
    ttk.Entry(fr_paths, textvariable=destino, width=60).grid(row=1, column=1, sticky="we", padx=4, pady=(4, 0))
    ttk.Button(fr_paths, text="Selecionar…", command=lambda: _pick_dir(destino)).grid(row=1, column=2, sticky="w", pady=(4, 0))
    fr_paths.grid_columnconfigure(1, weight=1)

    # Profile
    fr_prof = ttk.Frame(page)
    fr_prof.pack(fill="x", pady=6)
    ttk.Label(fr_prof, text="Profile:").grid(row=0, column=0, sticky="w")
    cmb = ttk.Combobox(fr_prof, textvariable=profile_choice, state="readonly", width=40,
                       values=sorted(list(profile_map.keys())))
    if cmb["values"]:
        cmb.current(0)
    cmb.grid(row=0, column=1, sticky="w", padx=4)
    ttk.Button(fr_prof, text="Abrir JSON…", command=lambda: _browse_profile_file()).grid(row=0, column=2, padx=(6, 0))
    ttk.Button(fr_prof, text="Carregar campos", command=lambda: _load_selected_profile()).grid(row=0, column=3, padx=(6, 0))

    # Opções fixas
    fr_opts = ttk.Frame(page)
    fr_opts.pack(fill="x", pady=4)
    ttk.Label(fr_opts, text="Algoritmo:").grid(row=0, column=0, sticky="e")
    ttk.Combobox(fr_opts, textvariable=algo, values=["sha256", "sha512", "md5"], width=10, state="readonly").grid(row=0, column=1, sticky="w", padx=4)

    ttk.Label(fr_opts, text="Modo:").grid(row=0, column=2, sticky="e")
    ttk.Combobox(fr_opts, textvariable=modo, values=["copy", "link", "move"], width=10, state="readonly").grid(row=0, column=3, sticky="w", padx=4)

    ttk.Label(fr_opts, text="Pattern:").grid(row=0, column=4, sticky="e")
    ttk.Entry(fr_opts, textvariable=pattern, width=14).grid(row=0, column=5, sticky="w", padx=4)

    ttk.Checkbutton(fr_opts, text="Incluir ocultos", variable=include_hidden).grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Checkbutton(fr_opts, text="Seguir symlinks", variable=follow_symlinks).grid(row=1, column=1, sticky="w", pady=(6, 0))
    ttk.Checkbutton(fr_opts, text="Gerar tagmanifest", variable=tagmanifest).grid(row=1, column=2, sticky="w", pady=(6, 0))
    fr_opts.grid_columnconfigure(6, weight=1)

    # Metadados padrão
    fr_meta = ttk.LabelFrame(page, text="Metadados padrão")
    fr_meta.pack(fill="x", pady=6)
    _grid_pair(fr_meta, 0, "Organization:", organization, 24)
    _grid_pair(fr_meta, 0, "Source-Organization:", source_organization, 24, col=2)
    _grid_pair(fr_meta, 1, "Contact-Name:", contact_name, 24)
    _grid_pair(fr_meta, 1, "Contact-Email:", contact_email, 24, col=2)
    _grid_pair(fr_meta, 2, "External-Description:", external_description, 60, colspan=3)

    # Parâmetros dinâmicos do profile
    grp_dyn = ttk.LabelFrame(page, text="Parâmetros do Profile (placeholders)")
    grp_dyn.pack(fill="both", expand=True, pady=6)
    dyn_container = ttk.Frame(grp_dyn)
    dyn_container.pack(fill="both", expand=True, padx=6, pady=6)

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

    def _browse_profile_file():
        nonlocal current_profile_path, current_profile_data
        p = filedialog.askopenfilename(
            title="Selecione um profile JSON",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if p:
            current_profile_path = Path(p)
            profile_choice.set(current_profile_path.name)
            current_profile_data = None
            _load_selected_profile()

    def _load_selected_profile():
        nonlocal current_profile_path, current_profile_data
        # determina path a partir do combo ou arquivo escolhido
        path: Path | None = current_profile_path
        if path is None:
            choice = profile_choice.get().strip()
            if not choice:
                messagebox.showwarning("Profile", "Selecione um profile ou carregue um JSON.")
                return
            path = profile_map.get(choice)
            if path is None:
                messagebox.showwarning("Profile", f"Profile '{choice}' não encontrado.")
                return

        try:
            prof = _load_profile(path)
        except Exception as e:
            messagebox.showerror("Erro ao carregar profile", str(e))
            return

        current_profile_path = path
        current_profile_data = prof
        _rebuild_dynamic_fields()

    def _rebuild_dynamic_fields():
        # limpa container
        for w in list(dyn_container.children.values()):
            w.destroy()
        dynamic_params.clear()

        if not current_profile_data:
            ttk.Label(dyn_container, text="Nenhum profile carregado.").grid(row=0, column=0, sticky="w")
            return

        phs = _extract_placeholders(current_profile_data)
        if not phs:
            ttk.Label(dyn_container, text="O profile não define placeholders adicionais.").grid(row=0, column=0, sticky="w")
            return

        # grade simples
        r = 0
        for key in phs:
            var = tk.StringVar()
            dynamic_params[key] = var
            ttk.Label(dyn_container, text=f"{key}:").grid(row=r, column=0, sticky="e", padx=(0, 6), pady=2)
            ttk.Entry(dyn_container, textvariable=var, width=42).grid(row=r, column=1, sticky="we", pady=2)
            r += 1
        dyn_container.grid_columnconfigure(1, weight=1)

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

    # Botão Executar (padrão igual ao hash_manifest: enfileira + modal)
    def _exec():
        src = raiz.get().strip()
        dst = destino.get().strip()
        if not src or not dst:
            messagebox.showwarning("Campos obrigatórios", "Informe a pasta fonte (payload) e a pasta destino (bag).")
            return

        # profile: nome lógico (se do combo) ou caminho absoluto (se carregado via arquivo)
        if current_profile_path is not None:
            profile_arg = str(current_profile_path)
        else:
            profile_arg = profile_choice.get().strip() or None

        # monta profile_param (lista CHAVE=VALOR)
        profile_param = []
        for k, v in dynamic_params.items():
            val = v.get().strip()
            if val != "":
                profile_param.append(f"{k}={val}")

        # payload compatível com core/scripts_map.py (JOB "BUILD_BAG")
        enqueue_cb("BUILD_BAG", {
            "src": src,
            "dst": dst,
            "algo": (algo.get().strip() or "sha256"),
            "mode": (modo.get().strip() or "copy"),
            "pattern": (pattern.get().strip() or "*"),
            "include_hidden": bool(include_hidden.get()),
            "follow_symlinks": bool(follow_symlinks.get()),
            "tagmanifest": bool(tagmanifest.get()),
            "organization": organization.get().strip() or None,
            "source_organization": source_organization.get().strip() or None,
            "contact_name": contact_name.get().strip() or None,
            "contact_email": contact_email.get().strip() or None,
            "external_description": external_description.get().strip() or None,
            "profile": profile_arg,
            "profile_param": profile_param or None,
        })

        # 🔔 feedback modal ao usuário (mesma UX do hash_manifest que você ajustou)
        parent = page.winfo_toplevel() if hasattr(page, "winfo_toplevel") else page
        msg = "O job de construção do Bag foi enviado para a fila de execução."
        if profile_arg:
            msg += f"\n\nProfile: {profile_arg}"
        messagebox.showinfo("Execução iniciada", msg, parent=parent)

    # Carrega automaticamente o primeiro profile (se houver)
    if profile_map:
        try:
            # finge um "Carregar campos" para sincronizar placeholders
            _load_selected_profile()
        except Exception:
            pass

    return page

# -------------------------
# Helpers de layout
# -------------------------
def _grid_pair(parent, row, label, var, width, *, col=0, colspan=1):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    ttk.Entry(parent, textvariable=var, width=width).grid(row=row, column=col + 1, columnspan=colspan, sticky="we", pady=2)
