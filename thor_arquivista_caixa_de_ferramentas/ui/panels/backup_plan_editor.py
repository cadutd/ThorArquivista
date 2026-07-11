# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
from __future__ import annotations

import json
from pathlib import Path
from tkinter import END, IntVar, StringVar, Text, Toplevel, filedialog, messagebox
from tkinter import BOTH, LEFT, RIGHT, X, Y

import ttkbootstrap as ttk
from ttkbootstrap.constants import DANGER, INFO, PRIMARY, SECONDARY, SUCCESS


def create_panel(app, enqueue_cb):
    page = ttk.Frame(app._main_nb, padding=10)

    topbar = ttk.Frame(page)
    topbar.pack(fill=X)
    ttk.Button(topbar, text="Fechar aba", bootstyle=DANGER, command=lambda: _close_tab(app, page)).pack(side=RIGHT)

    plan_path = StringVar(value="")
    backup_name = StringVar(value="")
    dest_path = StringVar(value="")
    algo = StringVar(value="sha256")
    ignore_hidden = IntVar(value=1)
    follow_symlinks = IntVar(value=0)
    status = StringVar(value="Crie um plano novo ou abra um JSON existente.")

    path_row = ttk.Frame(page)
    path_row.pack(fill=X, pady=4)
    ttk.Label(path_row, text="Arquivo JSON").pack(side=LEFT, padx=4)
    ttk.Entry(path_row, textvariable=plan_path).pack(side=LEFT, fill=X, expand=True)
    ttk.Button(path_row, text="Novo", bootstyle=SECONDARY, command=lambda: _new_plan(plan_path, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, sources_tree, output, status)).pack(side=LEFT, padx=3)
    ttk.Button(path_row, text="Abrir...", command=lambda: _ask_plan(plan_path, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, sources_tree, output, status)).pack(side=LEFT, padx=3)
    ttk.Button(path_row, text="Salvar", bootstyle=SUCCESS, command=lambda: _save_plan(plan_path, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, sources_tree, output, status, page, save_as=False)).pack(side=LEFT, padx=3)
    ttk.Button(path_row, text="Salvar como...", bootstyle=INFO, command=lambda: _save_plan(plan_path, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, sources_tree, output, status, page, save_as=True)).pack(side=LEFT, padx=3)

    form = ttk.Frame(page)
    form.pack(fill=X, pady=4)
    ttk.Label(form, text="Nome do backup").grid(row=0, column=0, sticky="w", padx=4, pady=3)
    ttk.Entry(form, textvariable=backup_name, width=32).grid(row=0, column=1, sticky="we", padx=4, pady=3)
    ttk.Label(form, text="Destino BagIt").grid(row=0, column=2, sticky="w", padx=4, pady=3)
    ttk.Entry(form, textvariable=dest_path).grid(row=0, column=3, sticky="we", padx=4, pady=3)
    ttk.Button(form, text="Selecionar...", command=lambda: _ask_dir(dest_path, "Selecionar destino BagIt")).grid(row=0, column=4, sticky="w", padx=4, pady=3)
    ttk.Label(form, text="Algoritmo").grid(row=1, column=0, sticky="w", padx=4, pady=3)
    ttk.Combobox(form, textvariable=algo, values=["sha256", "sha512", "md5"], width=12, state="readonly").grid(row=1, column=1, sticky="w", padx=4, pady=3)
    ttk.Checkbutton(form, text="Ignorar ocultos", variable=ignore_hidden).grid(row=1, column=2, sticky="w", padx=4, pady=3)
    ttk.Checkbutton(form, text="Seguir symlinks", variable=follow_symlinks).grid(row=1, column=3, sticky="w", padx=4, pady=3)
    form.grid_columnconfigure(1, weight=1)
    form.grid_columnconfigure(3, weight=2)

    sources_box = ttk.LabelFrame(page, text="Origens")
    sources_box.pack(fill=BOTH, expand=True, pady=6)

    source_actions = ttk.Frame(sources_box)
    source_actions.pack(fill=X, pady=(4, 2))
    ttk.Button(source_actions, text="Adicionar pasta", bootstyle=PRIMARY, command=lambda: _open_source_dialog(page, sources_tree)).pack(side=LEFT, padx=4)
    ttk.Button(source_actions, text="Editar", bootstyle=INFO, command=lambda: _edit_selected_source(page, sources_tree)).pack(side=LEFT, padx=4)
    ttk.Button(source_actions, text="Remover", bootstyle=DANGER, command=lambda: _remove_selected_source(sources_tree)).pack(side=LEFT, padx=4)

    sources_tree = ttk.Treeview(sources_box, columns=("name", "path"), show="headings", height=7)
    sources_tree.heading("name", text="Nome")
    sources_tree.heading("path", text="Pasta")
    sources_tree.column("name", width=180, anchor="w")
    sources_tree.column("path", width=760, anchor="w")
    sources_tree.pack(fill=BOTH, expand=True, padx=4, pady=(0, 4))

    actions = ttk.Frame(page)
    actions.pack(fill=X, pady=6)
    ttk.Button(actions, text="Pré-visualizar JSON", bootstyle=SECONDARY, command=lambda: _preview_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, sources_tree, output, status)).pack(side=LEFT, padx=4)
    ttk.Button(actions, text="Validar plano", bootstyle=INFO, command=lambda: _validate_editor(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, sources_tree, output, status)).pack(side=LEFT, padx=4)
    ttk.Label(actions, textvariable=status, bootstyle=SECONDARY).pack(side=LEFT, padx=12)

    body = ttk.Frame(page)
    body.pack(fill=BOTH, expand=True, pady=(4, 0))
    output = Text(body, height=12, wrap="none")
    output.pack(side=LEFT, fill=BOTH, expand=True)
    scroll = ttk.Scrollbar(body, orient="vertical", command=output.yview)
    scroll.pack(side=RIGHT, fill=Y)
    output.configure(yscrollcommand=scroll.set)

    _preview_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, sources_tree, output, status)
    return page


def _load_plan(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise ValueError(f"Plano não encontrado: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("O plano JSON deve conter um objeto.")
    return data


def _collect_sources(tree) -> list[dict[str, str]]:
    out = []
    for item in tree.get_children():
        name, path = tree.item(item, "values")
        out.append({"name": str(name).strip(), "path": str(path).strip()})
    return out


def _collect_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree) -> dict:
    return {
        "name": backup_name.get().strip(),
        "destination": dest_path.get().strip(),
        "sources": _collect_sources(tree),
        "options": {
            "algo": algo.get().strip() or "sha256",
            "ignore_hidden": bool(ignore_hidden.get()),
            "follow_symlinks": bool(follow_symlinks.get()),
        },
    }


def _apply_plan(data: dict, plan_file: str, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree) -> None:
    backup_name.set(str(data.get("name") or data.get("nome") or Path(plan_file).stem))
    dest_path.set(str(data.get("destination") or data.get("destino") or ""))
    opts = data.get("options") or data.get("opcoes") or {}
    if not isinstance(opts, dict):
        opts = {}
    algo.set(str(opts.get("algo") or opts.get("algorithm") or "sha256"))
    ignore_hidden.set(1 if bool(opts.get("ignore_hidden") or opts.get("ignorar_ocultos")) else 0)
    follow_symlinks.set(1 if bool(opts.get("follow_symlinks") or opts.get("seguir_symlinks")) else 0)

    tree.delete(*tree.get_children())
    for idx, item in enumerate(_plan_sources(data), 1):
        if isinstance(item, str):
            name = Path(item).name or f"origem_{idx}"
            path = item
        elif isinstance(item, dict):
            path = item.get("path") or item.get("raiz") or item.get("source") or ""
            name = item.get("name") or item.get("nome") or (Path(path).name if path else f"origem_{idx}")
        else:
            continue
        tree.insert("", END, values=(str(name), str(path)))


def _plan_sources(data: dict) -> list:
    sources = data.get("sources") or data.get("pastas") or data.get("folders") or []
    return sources if isinstance(sources, list) else []


def _new_plan(plan_path, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status):
    plan_path.set("")
    backup_name.set("")
    dest_path.set("")
    algo.set("sha256")
    ignore_hidden.set(1)
    follow_symlinks.set(0)
    tree.delete(*tree.get_children())
    _preview_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status)
    status.set("Novo plano iniciado.")


def _ask_plan(plan_path, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status):
    p = filedialog.askopenfilename(title="Selecionar plano de backup", filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
    if not p:
        return
    plan_path.set(p)
    try:
        data = _load_plan(p)
        _apply_plan(data, p, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree)
        _preview_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status)
        status.set("Plano carregado para edição.")
    except Exception as e:
        status.set(f"Plano inválido: {e}")
        messagebox.showerror("Plano inválido", str(e), parent=tree.winfo_toplevel())


def _ask_dir(var, title):
    p = filedialog.askdirectory(title=title)
    if p:
        var.set(p)


def _save_plan(plan_path, backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status, page, *, save_as: bool) -> bool:
    try:
        data = _validate_editor(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status)
    except Exception:
        return False

    target = plan_path.get().strip()
    if save_as or not target:
        target = filedialog.asksaveasfilename(
            title="Salvar plano de backup",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not target:
            return False
        plan_path.set(target)

    try:
        p = Path(target)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        status.set(f"Plano salvo: {p}")
        messagebox.showinfo("Plano salvo", f"Arquivo salvo:\n{p}", parent=page)
        return True
    except Exception as e:
        status.set(f"Falha ao salvar: {e}")
        messagebox.showerror("Falha ao salvar", str(e), parent=page)
        return False


def _validate_editor(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status) -> dict:
    output.delete("1.0", END)
    data = _collect_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree)
    problems = []
    if not data["name"]:
        problems.append("Informe o nome do backup.")
    if not data["destination"]:
        problems.append("Informe o destino BagIt.")
    if not data["sources"]:
        problems.append("Adicione pelo menos uma pasta de origem.")
    names = set()
    for source in data["sources"]:
        if not source["name"]:
            problems.append("Há origem sem nome.")
        if source["name"] in names:
            problems.append(f"Nome de origem duplicado: {source['name']}")
        names.add(source["name"])
        if not source["path"]:
            problems.append(f"Origem {source['name']} sem pasta.")
        elif not Path(source["path"]).exists():
            problems.append(f"Origem não encontrada: {source['path']}")
    output.insert(END, json.dumps(data, ensure_ascii=False, indent=2))
    if problems:
        status.set(f"Plano com {len(problems)} pendência(s).")
        output.insert(END, "\n\nPendências:\n" + "\n".join(f"- {p}" for p in problems))
        raise ValueError("; ".join(problems))
    status.set("Plano válido.")
    return data


def _preview_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree, output, status):
    data = _collect_plan(backup_name, dest_path, algo, ignore_hidden, follow_symlinks, tree)
    output.delete("1.0", END)
    output.insert(END, json.dumps(data, ensure_ascii=False, indent=2))
    status.set("Pré-visualização atualizada.")


def _open_source_dialog(parent, tree, item_id: str | None = None):
    win = Toplevel(parent)
    win.title("Origem do backup")
    win.transient(parent.winfo_toplevel())
    win.grab_set()
    win.geometry("720x150")

    current_name = ""
    current_path = ""
    if item_id:
        values = tree.item(item_id, "values")
        if values:
            current_name, current_path = str(values[0]), str(values[1])

    name = StringVar(value=current_name)
    path = StringVar(value=current_path)

    row1 = ttk.Frame(win, padding=8)
    row1.pack(fill=X)
    ttk.Label(row1, text="Nome").pack(side=LEFT, padx=4)
    ttk.Entry(row1, textvariable=name, width=28).pack(side=LEFT, padx=4)
    ttk.Label(row1, text="Pasta").pack(side=LEFT, padx=4)
    ttk.Entry(row1, textvariable=path).pack(side=LEFT, fill=X, expand=True, padx=4)
    ttk.Button(row1, text="Selecionar...", command=lambda: _select_source_dir(name, path)).pack(side=LEFT, padx=4)

    buttons = ttk.Frame(win, padding=8)
    buttons.pack(fill=X)

    def save():
        n = name.get().strip()
        p = path.get().strip()
        if not n or not p:
            messagebox.showwarning("Origem", "Informe nome e pasta da origem.", parent=win)
            return
        if item_id:
            tree.item(item_id, values=(n, p))
        else:
            tree.insert("", END, values=(n, p))
        win.destroy()

    ttk.Button(buttons, text="Salvar", bootstyle=SUCCESS, command=save).pack(side=LEFT, padx=4)
    ttk.Button(buttons, text="Cancelar", bootstyle=SECONDARY, command=win.destroy).pack(side=LEFT, padx=4)


def _select_source_dir(name, path):
    p = filedialog.askdirectory(title="Selecionar pasta de origem")
    if not p:
        return
    path.set(p)
    if not name.get().strip():
        name.set(Path(p).name or "origem")


def _edit_selected_source(parent, tree):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Origens", "Selecione uma origem para editar.", parent=parent)
        return
    _open_source_dialog(parent, tree, sel[0])


def _remove_selected_source(tree):
    for item in tree.selection():
        tree.delete(item)


def _close_tab(app, page):
    app._main_nb.forget(page)
    page.destroy()
