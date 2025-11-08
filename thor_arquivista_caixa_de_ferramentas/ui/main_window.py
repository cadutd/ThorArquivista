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

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import json
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import BOTH, X, YES

from core.config import AppConfig, DEFAULTS
from core.jobstore import JobStore
from core.worker import Worker

# painéis (cada um com create_panel(app, enqueue_cb))
from ui.panels.premis_view import create_panel as panel_premis_view
from ui.panels.hash_manifest import create_panel as panel_hash
from ui.panels.verify_fixity import create_panel as panel_fixity
from ui.panels.build_bag import create_panel as panel_bag
from ui.panels.build_sip import create_panel as panel_sip
from ui.panels.format_identify import create_panel as panel_fmt
from ui.panels.replicate import create_panel as panel_rep
from ui.panels.premis_event import create_panel as panel_premis_evt
from ui.panels.worker_control import create_panel as panel_worker
from ui.panels.duplicate_analysis import create_panel as panel_duplicate_analysis
from ui.panels.duplicate_treatment import create_panel as panel_duplicate_treatment
from ui.panels.premis_converter import create_panel as panel_premis_converter

class MainApp(tb.Window):
    """Janela principal do Thor Arquivista – Caixa de Ferramentas de Preservação Digital."""

    def __init__(self, cfg: AppConfig):
        # Tema inicial: tenta usar o que está no config.json
        start_theme = getattr(cfg, "ui_theme", None) or "flatly"
        super().__init__(themename=start_theme)

        self.cfg = cfg
        setattr(self.cfg, "ui_theme", start_theme)

        self.title("Thor Arquivista - Caixa de Ferramentas de Preservação Digital")
        self.geometry("1200x800")

        # Worker e jobstore
        self.jobstore = JobStore(path=getattr(cfg, "jobstore_path", "./jobs_db.json"))
        self.worker = Worker(cfg=self.cfg, jobstore=self.jobstore)
        self.worker.start()

        # Style para gerenciar temas
        self._style = tb.Style()
        self._theme_var = tk.StringVar(value=self._style.theme_use())
        themes = sorted(self._style.theme_names())

        # =====================
        # Barra superior
        # =====================
        top = ttk.Frame(self, padding=10)
        top.pack(fill=X)

        # Esquerda: informações gerais
        left_box = ttk.Frame(top)
        left_box.pack(side=LEFT, fill=X, expand=True)
        ttk.Label(left_box, text=f"JobStore: {Path(self.jobstore.path).resolve()}", bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Label(left_box, text=f"Scripts: {self.cfg.scripts_dir}", bootstyle=INFO).pack(side=LEFT, padx=10)

        # Direita: seletor de tema + botão aplicar
        right_box = ttk.Frame(top)
        right_box.pack(side=RIGHT)

        ttk.Label(right_box, text="Tema:", bootstyle=SECONDARY).pack(side=LEFT, padx=(0, 6))
        self._theme_cbx = ttk.Combobox(
            right_box,
            textvariable=self._theme_var,
            values=themes,
            width=18,
            state="readonly"
        )
        self._theme_cbx.pack(side=LEFT)

        def apply_theme():
            """Aplica e salva o tema escolhido."""
            try:
                sel = (self._theme_var.get() or "").strip()
                if not sel:
                    return
                self._style.theme_use(sel)
                self._status.configure(text=f"Tema aplicado: {sel}")
                # Atualiza AppConfig e salva no config.json
                setattr(self.cfg, "ui_theme", sel)
                self.cfg.save()
            except Exception as e:
                self._status.configure(text=f"Falha ao aplicar tema: {e}")

        ttk.Button(right_box, text="Aplicar", command=apply_theme, bootstyle=PRIMARY).pack(side=LEFT, padx=6)

        # =====================
        # Menu principal
        # =====================
        menubar = tk.Menu(self)
        menu_tarefas = tk.Menu(menubar, tearoff=False)
        menu_visual = tk.Menu(menubar, tearoff=False)
        submenu_duplicatas = tk.Menu(menubar, tearoff=False)

        menubar.add_cascade(label="Tarefas", menu=menu_tarefas)
        menubar.add_cascade(label="Visualização", menu=menu_visual)
        self.config(menu=menubar)

        # =====================
        # Notebook (abas principais)
        # =====================
        self._main_nb = ttk.Notebook(self)
        self._main_nb.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # Aba inicial com logotipo
        start_frame = ttk.Frame(self._main_nb)
        self._main_nb.add(start_frame, text="Início")

        img_path = Path(__file__).resolve().parents[1] / "logo_inicial.png"
        if img_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(img_path).resize((800, 450), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                ttk.Label(start_frame, image=photo).pack(pady=30)
                setattr(self, "_start_img", photo)  # evita garbage collection
            except Exception as e:
                ttk.Label(start_frame, text=f"Falha ao carregar imagem: {e}", bootstyle=DANGER).pack(pady=50)
        else:
            ttk.Label(start_frame, text=f"Imagem não encontrada: {img_path.name}", bootstyle=WARNING).pack(pady=50)

        ttk.Label(
            start_frame,
            text="Thor Arquivista\nCaixa de Ferramentas de Preservação Digital",
            font=("Segoe UI", 14, "bold"),
            bootstyle=PRIMARY,
            anchor="center",
            justify="center"
        ).pack(pady=10, expand=True, fill="both")

        # =====================
        # Função auxiliar para abrir painéis
        # =====================
        def _open(title: str, builder):
            frame = builder(self, self._enqueue)
            self._main_nb.add(frame, text=title)
            self._main_nb.select(frame)

        # =====================
        # Menus → Painéis
        # =====================
        menu_tarefas.add_command(label="Gerar Manifesto (Hash)", command=lambda: _open("Gerar Manifesto", panel_hash))
        menu_tarefas.add_command(label="Verificar Fixidez", command=lambda: _open("Verificar Fixidez", panel_fixity))
        menu_tarefas.add_command(label="Gerar Pacote BagIt", command=lambda: _open("Gerar Pacote BagIt", panel_bag))

        submenu_duplicatas.add_command(label="Análise de Duplicatas", command=lambda: _open("Análise de Duplicatas", panel_duplicate_analysis))
        submenu_duplicatas.add_command(label="Tratamento de Duplicatas", command=lambda: _open("Tratamento de Duplicatas", panel_duplicate_treatment))
        menu_tarefas.add_cascade(label="Duplicatas", menu=submenu_duplicatas)

        menu_tarefas.add_command(label="Copiar", command=lambda: _open("Copiar", panel_rep))
        menu_tarefas.add_command(label="Conversor Premis", command=lambda: _open("Conversor Premis", panel_premis_converter))

        menu_tarefas.add_command(label="SIP", command=lambda: _open("SIP", panel_sip))
        menu_tarefas.add_command(label="Identificar Formatos", command=lambda: _open("Identificar Formatos", panel_fmt))
        menu_tarefas.add_command(label="Registrar Evento PREMIS", command=lambda: _open("Evento PREMIS", panel_premis_evt))

        menu_visual.add_command(label="Eventos PREMIS", command=lambda: _open("Eventos PREMIS", panel_premis_view))
        menu_visual.add_command(label="Controle do Worker", command=lambda: _open("Controle do Worker", panel_worker))

        # =====================
        # Rodapé (status)
        # =====================
        self._status = ttk.Label(self, text="Pronto.", anchor="w")
        self._status.pack(fill=X, padx=10, pady=(0, 10))

    # =====================
    # Encerramento e Enfileiramento
    # =====================
    def destroy(self):
        try:
            if self.worker and self.worker.is_alive():
                self.worker.stop()
                self.worker.join(timeout=2.0)
        finally:
            super().destroy()

    def _enqueue(self, job_type: str, params: Dict[str, Any]):
        try:
            jid = self.jobstore.add_job(job_type, params)
            self.jobstore.add_log(jid, f"Enfileirado {job_type}")
            self._status.configure(text=f"Job enfileirado: {job_type} (id {jid})")
        except Exception as e:
            self._status.configure(text=f"Falha ao enfileirar: {e}")


def run_app(cfg: Optional[AppConfig] = None):
    cfg = cfg or AppConfig.from_file("./config.json")
    app = MainApp(cfg)
    app.mainloop()
