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
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
from ttkbootstrap.constants import *

# -------------------------
# Utilidades do painel
# -------------------------
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_\-]+)\}")

_CALCULATED_KEYS = {
    "bagging_date",
    "payload_oxum",
    "algo",
    "total_bytes",
    "file_count",
    "src",
    "dst",
    "bag_software_agent",
    "bag_name",
}

_STANDARD_META_KEYS = {
    "organization",
    "source_organization",
    "contact_name",
    "contact_email",
    "external_description",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_WIN_FORBIDDEN = set('<>:"/\\|?*')
_WIN_RESERVED = {
    "CON","PRN","AUX","NUL",
    "COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9",
    "LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9",
}

def _valid_bag_name(name: str) -> tuple[bool, str]:
    if not name:
        return False, "O Nome do Pacote não pode ficar em branco."
    if os.name == "nt":
        if any(ch in _WIN_FORBIDDEN or ord(ch) < 32 for ch in name):
            return False, 'Nome inválido: não use caracteres <>:"/\\|?* nem caracteres de controle.'
        if name.endswith(" ") or name.endswith("."):
            return False, "No Windows, o nome não pode terminar com espaço ou ponto."
        if name.strip().upper().split(".")[0] in _WIN_RESERVED:
            return False, f'"{name}" é um nome reservado do Windows.'
    else:
        if "/" in name or "\x00" in name:
            return False, "Em sistemas Unix, o nome não pode conter '/'."
    return True, ""

def _repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]

def _find_profiles() -> List[Tuple[str, Path]]:
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
    data.setdefault("ui_options", {})
    data.setdefault("ui_defaults", {})
    return data

def _extract_placeholders(profile_data: Dict) -> List[str]:
    keys = set()
    for val in profile_data.get("bag_info", {}).values():
        if isinstance(val, str):
            for m in _PLACEHOLDER_RE.finditer(val):
                keys.add(m.group(1))
    keys = keys - _CALCULATED_KEYS - _STANDARD_META_KEYS
    return sorted(keys)

def _prettify_label(key: str) -> str:
    s = key.replace("-", " ").replace("_", " ")
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r" \1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.title()

# -------------------------
# Fábrica no padrão do projeto
# -------------------------
def create_panel(parent, enqueue_cb, close_cb=None):
    page = ttk.Frame(parent)

    # Vars principais
    raiz = tk.StringVar()
    bag_name = tk.StringVar()
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

    profile_choice = tk.StringVar()
    profile_map: Dict[str, Path] = {name: p for name, p in _find_profiles()}
    current_profile_path: Path | None = None
    current_profile_data: Dict | None = None
    dynamic_params: Dict[str, tuple[tk.Variable, str]] = {}

    # Layout fixo
    fr_paths = ttk.Frame(page)
    fr_paths.pack(fill="x", pady=2)

    ttk.Label(fr_paths, text="Pasta fonte (payload):").grid(row=0, column=0, sticky="w")
    ttk.Entry(fr_paths, textvariable=raiz, width=60).grid(row=0, column=1, sticky="we", padx=4)
    ttk.Button(fr_paths, text="Selecionar…", command=lambda: _pick_dir(raiz)).grid(row=0, column=2, sticky="w")

    ttk.Label(fr_paths, text="Nome do Pacote:").grid(row=1, column=0, sticky="w", pady=(4, 0))
    ttk.Entry(fr_paths, textvariable=bag_name, width=40).grid(row=1, column=1, sticky="w", padx=4, pady=(4, 0))

    ttk.Label(fr_paths, text="Diretório destino (pai):").grid(row=2, column=0, sticky="w", pady=(4, 0))
    ttk.Entry(fr_paths, textvariable=destino, width=60).grid(row=2, column=1, sticky="we", padx=4, pady=(4, 0))
    ttk.Button(fr_paths, text="Selecionar…", command=lambda: _pick_dir(destino)).grid(row=2, column=2, sticky="w", pady=(4, 0))
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

    # Opções
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

    # Metadados padrão
    fr_meta = ttk.LabelFrame(page, text="Metadados padrão")
    fr_meta.pack(fill="x", pady=6)
    _grid_pair(fr_meta, 0, "Organization:", organization, 24)
    _grid_pair(fr_meta, 0, "Source-Organization:", source_organization, 24, col=2)
    _grid_pair(fr_meta, 1, "Contact-Name:", contact_name, 24)
    _grid_pair(fr_meta, 1, "Contact-Email:", contact_email, 24, col=2)
    _grid_pair(fr_meta, 2, "External-Description:", external_description, 60, colspan=3)

    # Scrollable placeholders
    grp_dyn = ttk.LabelFrame(page, text="Parâmetros do Profile (placeholders)")
    grp_dyn.pack(fill="both", expand=True, pady=6)

    canvas = tk.Canvas(grp_dyn, highlightthickness=0)
    scrollbar = ttk.Scrollbar(grp_dyn, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)
    scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scroll_frame.bind("<Configure>", _on_frame_configure)

    def _on_canvas_configure(event):
        # Mantém o conteúdo com a mesma largura do canvas
        try:
            canvas.itemconfigure(scroll_window, width=event.width)
        except Exception:
            pass
    canvas.bind("<Configure>", _on_canvas_configure)

    # ---------- SUPORTE A RODA DO MOUSE (Windows/macOS/Linux) ----------
    # Em Windows/macOS usamos <MouseWheel>; em X11 (Linux) <Button-4/5>.
    # Usamos bind_all para garantir que o evento chegue, e filtramos com um flag
    # que indica se o mouse está sobre a área rolável.
    _wheel_inside = {"on": False}  # mutável para fechar sobre o escopo

    def _normalize_units(delta: int) -> int:
        """Normaliza o delta do Windows/macOS para 'units' de rolagem."""
        if delta == 0:
            return 0
        units = -int(delta / 120)  # Windows envia múltiplos de 120
        if units == 0:
            units = -1 if delta > 0 else 1
        if units > 0:
            return min(units, 10)
        return max(units, -10)

    def _on_mousewheel_all(event):
        # só reage se o ponteiro estiver sobre o canvas/área rolável
        if not _wheel_inside["on"]:
            return
        if hasattr(event, "delta"):
            units = _normalize_units(getattr(event, "delta", 0))
            if units:
                canvas.yview_scroll(units, "units")
                return "break"

    def _on_mousewheel_linux_up(event):
        if not _wheel_inside["on"]:
            return
        canvas.yview_scroll(-1, "units")
        return "break"

    def _on_mousewheel_linux_down(event):
        if not _wheel_inside["on"]:
            return
        canvas.yview_scroll(1, "units")
        return "break"

    def _enter_scroll_area(_=None):
        _wheel_inside["on"] = True
        # foco no canvas ajuda em alguns bindings de teclado
        canvas.focus_set()

    def _leave_scroll_area(_=None):
        _wheel_inside["on"] = False

    # Considera tanto o canvas quanto o frame interno como área sensível
    for _w in (canvas, scroll_frame):
        _w.bind("<Enter>", _enter_scroll_area, add="+")
        _w.bind("<Leave>", _leave_scroll_area, add="+")

    # Binds globais — chegam independente do foco; filtramos via _wheel_inside
    page.bind_all("<MouseWheel>", _on_mousewheel_all, add="+")     # Windows/macOS
    page.bind_all("<Button-4>", _on_mousewheel_linux_up, add="+")  # Linux up
    page.bind_all("<Button-5>", _on_mousewheel_linux_down, add="+")# Linux down
    # -------------------------------------------------------------------

    # Botões
    fr_btns = ttk.Frame(page)
    fr_btns.pack(fill="x", pady=8)
    ttk.Button(fr_btns, text="Executar", bootstyle=PRIMARY, command=lambda: _exec()).pack(side="left")
    ttk.Button(fr_btns, text="Fechar", bootstyle=DANGER, command=lambda: _close()).pack(side="left", padx=6)

    # ---------------
    def _pick_dir(var):
        d = filedialog.askdirectory()
        var.set(d if d else var.get())

    def _browse_profile_file():
        nonlocal current_profile_path, current_profile_data
        p = filedialog.askopenfilename(title="Selecione um profile JSON",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        if p:
            current_profile_path = Path(p)
            profile_choice.set(current_profile_path.name)
            current_profile_data = None
            _load_selected_profile()

    def _load_selected_profile():
        nonlocal current_profile_path, current_profile_data
        path = current_profile_path or profile_map.get(profile_choice.get().strip())
        if not path:
            messagebox.showwarning("Profile", "Selecione ou carregue um profile JSON.")
            return
        try:
            prof = _load_profile(path)
        except Exception as e:
            messagebox.showerror("Erro ao carregar profile", str(e))
            return
        current_profile_path, current_profile_data = path, prof
        _rebuild_dynamic_fields()

    def _rebuild_dynamic_fields():
        for w in list(scroll_frame.children.values()):
            w.destroy()
        dynamic_params.clear()

        if not current_profile_data:
            ttk.Label(scroll_frame, text="Nenhum profile carregado.").pack(anchor="w")
            return

        phs = _extract_placeholders(current_profile_data)
        ui_opts = current_profile_data.get("ui_options", {}) or {}
        ui_defaults = current_profile_data.get("ui_defaults", {}) or {}

        if not phs:
            ttk.Label(scroll_frame, text="O profile não define placeholders adicionais.").pack(anchor="w")
            return

        for r, key in enumerate(phs):
            label_text = _prettify_label(key)
            ttk.Label(scroll_frame, text=f"{label_text}:").grid(row=r, column=0, sticky="e", padx=(0, 6), pady=2)
            default_val = ui_defaults.get(key, "")
            opts = ui_opts.get(key)
            if isinstance(opts, list) and opts:
                var = tk.StringVar()
                cb = ttk.Combobox(scroll_frame, textvariable=var, values=opts, state="readonly", width=42)
                var.set(default_val if default_val in opts else opts[0])
                cb.grid(row=r, column=1, sticky="we", pady=2)
                dynamic_params[key] = (var, "combo")
            else:
                var = tk.StringVar(value=default_val)
                ttk.Entry(scroll_frame, textvariable=var, width=42).grid(row=r, column=1, sticky="we", pady=2)
                dynamic_params[key] = (var, "entry")
        scroll_frame.grid_columnconfigure(1, weight=1)

    def _close():
        if callable(close_cb):
            try: close_cb(page); return
            except Exception: pass
        try: page.destroy()
        except Exception: pass

    def _validate_fields():
        src, dst, name = raiz.get().strip(), destino.get().strip(), bag_name.get().strip()
        if not src or not dst or not name:
            messagebox.showwarning("Campos obrigatórios", "Informe a pasta fonte, destino e nome do pacote.")
            return False
        if not Path(src).exists():
            messagebox.showerror("Pasta fonte", f"A pasta fonte não existe:\n{src}")
            return False
        ok, reason = _valid_bag_name(name)
        if not ok:
            messagebox.showwarning("Nome do Pacote inválido", reason)
            return False
        em = contact_email.get().strip()
        if em and not _EMAIL_RE.match(em):
            messagebox.showwarning("Contact-Email", "E-mail inválido.")
            return False
        return True

    def _exec():
        if not _validate_fields(): return
        src, dst, name = raiz.get().strip(), destino.get().strip(), bag_name.get().strip()
        profile_arg = str(current_profile_path) if current_profile_path else (profile_choice.get().strip() or None)
        profile_param = [f"{k}={v.get().strip()}" for k, (v, _) in dynamic_params.items() if v.get().strip()]
        payload = {
            "src": src, "dst": dst, "bag_name": name,
            "algo": algo.get().strip() or "sha256",
            "mode": modo.get().strip() or "copy",
            "pattern": pattern.get().strip() or "*",
            "include_hidden": bool(include_hidden.get()),
            "follow_symlinks": bool(follow_symlinks.get()),
            "tagmanifest": bool(tagmanifest.get()),
            "organization": organization.get().strip() or None,
            "source_organization": source_organization.get().strip() or None,
            "contact_name": contact_name.get().strip() or None,
            "contact_email": contact_email.get().strip() or None,
            "external_description": external_description.get().strip() or None,
            "profile": profile_arg, "profile_param": profile_param or None,
        }
        enqueue_cb("BUILD_BAG", payload)
        messagebox.showinfo("Execução iniciada",
            f"O job de construção do Bag foi enviado para a fila.\n\nProfile: {profile_arg or '(padrão)'}",
            parent=page)

    if profile_map:
        try: _load_selected_profile()
        except Exception: pass

    return page

# Helper
def _grid_pair(parent, row, label, var, width, *, col=0, colspan=1):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(6 if col else 0, 4), pady=2)
    ttk.Entry(parent, textvariable=var, width=width).grid(row=row, column=col + 1, columnspan=colspan, sticky="we", pady=2)
