from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import BOTH, X, YES

from core.config import AppConfig, DEFAULTS
from core.jobstore import JobStore
from core.worker import Worker

# painéis (cada um com create_panel(app, enqueue_cb))
# mantenha seus outros painéis anteriores, ex.:
from ui.panels.premis_view import create_panel as panel_premis_view
from ui.panels.hash_manifest import create_panel as panel_hash
from ui.panels.verify_fixity import create_panel as panel_fixity
from ui.panels.build_bag import create_panel as panel_bag
from ui.panels.build_sip import create_panel as panel_sip
from ui.panels.format_identify import create_panel as panel_fmt
from ui.panels.replicate import create_panel as panel_rep
from ui.panels.premis_event import create_panel as panel_premis_evt
from ui.panels.worker_control import create_panel as panel_worker
from ui.panels.duplicate_finder import create_panel as panel_duplicate_finder

class MainApp(ttk.Window):
    def __init__(self, cfg: AppConfig):
        super().__init__(themename="flatly")
        self.title("Thor Arquivista - Orquestrador de Preservação Digital")
        self.geometry("1200x800")

        self.cfg = cfg
        self.jobstore = JobStore(path=getattr(cfg, "jobstore_path", "./jobs_db.json"))
        self.worker = Worker(cfg=self.cfg, jobstore=self.jobstore)
        self.worker.start()

        # Barra superior
        top = ttk.Frame(self, padding=10)
        top.pack(fill=X)
        ttk.Label(top, text=f"JobStore: {Path(self.jobstore.path).resolve()}", bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Label(top, text=f"Scripts: {self.cfg.scripts_dir}", bootstyle=INFO).pack(side=LEFT, padx=10)

        # Menu + Notebook
        menubar = ttk.Menu(self)
        menu_tarefas = ttk.Menu(menubar, tearoff=False)
        menu_visual = ttk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Tarefas", menu=menu_tarefas)
        menubar.add_cascade(label="Visualização", menu=menu_visual)
        self.config(menu=menubar)

        self._main_nb = ttk.Notebook(self)
        self._main_nb.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # Tela inicial com imagem (logo_inicial.png)
        start_frame = ttk.Frame(self._main_nb)
        self._main_nb.add(start_frame, text="Início")

        img_path = Path(__file__).resolve().parents[1] / "logo_inicial.png"
        if img_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(img_path).resize((800, 450), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                ttk.Label(start_frame, image=photo).pack(pady=30)
                setattr(self, "_start_img", photo)
            except Exception as e:
                ttk.Label(start_frame, text=f"Falha ao carregar imagem: {e}", bootstyle=DANGER).pack(pady=50)
        else:
            ttk.Label(start_frame, text=f"Imagem não encontrada: {img_path.name}", bootstyle=WARNING).pack(pady=50)

        ttk.Label(
            start_frame,
            text="Thor Arquivista\nOrquestrador de Preservação Digital",
            font=("Segoe UI", 14, "bold"),
            bootstyle=PRIMARY,
            anchor="center",
            justify="center"
        ).pack(pady=10, expand=True, fill="both")

        def _open(title: str, builder):
            frame = builder(self, self._enqueue)
            self._main_nb.add(frame, text=title)
            self._main_nb.select(frame)

        # Menus → painéis
        menu_tarefas.add_command(label="Gerar Manifesto (Hash)", command=lambda: _open("Gerar Manifesto", panel_hash))
        menu_tarefas.add_command(label="Verificar Fixidez", command=lambda: _open("Verificar Fixidez", panel_fixity))
        menu_tarefas.add_command(label="Gerar Pacote BagIt", command=lambda: _open("Gerar Pacote BagIt", panel_bag))
        menu_tarefas.add_command(label="Localizador de Duplicatas", command=lambda: _open("Localizador de Duplicatas", panel_duplicate_finder))
        menu_tarefas.add_command(label="SIP", command=lambda: _open("SIP", panel_sip))
        menu_tarefas.add_command(label="Identificar Formatos", command=lambda: _open("Identificar Formatos", panel_fmt))
        menu_tarefas.add_command(label="Replicar", command=lambda: _open("Replicar", panel_rep))
        menu_tarefas.add_command(label="Evento PREMIS", command=lambda: _open("Evento PREMIS", panel_premis_evt))
        menu_visual.add_command(label="Eventos PREMIS", command=lambda: _open("Eventos PREMIS", panel_premis_view))
        menu_visual.add_command(label="Controle do Worker", command=lambda: _open("Controle do Worker", panel_worker))


        # Rodapé (status)
        self._status = ttk.Label(self, text="Pronto.", anchor="w")
        self._status.pack(fill=X, padx=10, pady=(0, 10))

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
    cfg = cfg or AppConfig.from_env(DEFAULTS)
    app = MainApp(cfg)
    app.mainloop()
