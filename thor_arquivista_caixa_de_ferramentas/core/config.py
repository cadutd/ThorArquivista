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
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json, os
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um .env, se existir
def load_env():
    home_env = Path.home() / ".preservacao_app.env"
    if home_env.exists():
        load_dotenv(home_env.as_posix())
    load_dotenv()  # carrega ./.env se houver

# load_env()

# ----- valores padrão -----
DEFAULTS = {
    "scripts_dir": (Path(__file__).resolve().parent.parent / "scripts").as_posix(),
    "logs_dir": (Path.home() / ".preservacao_logs").as_posix(),
    "premis_log": os.getenv("PREMIS_LOG", (Path.home() / "premis_events.jsonl").as_posix()),
    "premis_agent": os.getenv("PREMIS_AGENT", "Gerenciador de Arquivos — Orquestração"),
    "ui_theme": os.getenv("UI_THEME", "flatly"),
    "jobstore_path": "./jobs_db.json",
}


# =====================================================
# Classe principal de configuração do Thor Arquivista
# =====================================================
@dataclass
class AppConfig:
    scripts_dir: str = "./scripts"
    logs_dir: str = "./logs"
    premis_log: str = "./logs/premis_events.jsonl"
    premis_agent: str = "Gerenciador de Arquivos — Orquestração"
    jobstore_path: str = "./jobs_db.json"
    ui_theme: str = "flatly"

    # Caminho do arquivo de configuração carregado
    path: Path = field(default_factory=lambda: Path("./config.json"))

    # -----------------------------
    # Compatibilidade com variáveis de ambiente
    # -----------------------------
    @classmethod
    def from_env(cls, defaults: "AppConfig") -> "AppConfig":
        cfg = defaults
        cfg.scripts_dir = os.getenv("SCRIPTS_DIR", cfg.scripts_dir)
        cfg.logs_dir = os.getenv("LOGS_DIR", cfg.logs_dir)
        cfg.premis_log = os.getenv("PREMIS_LOG", cfg.premis_log)
        cfg.premis_agent = os.getenv("PREMIS_AGENT", cfg.premis_agent)
        cfg.jobstore_path = os.getenv("JOBSTORE_PATH", cfg.jobstore_path)
        cfg.ui_theme = os.getenv("UI_THEME", cfg.ui_theme)
        return cfg

    # -----------------------------
    # Carregar de arquivo JSON
    # -----------------------------
    @classmethod
    def from_file(cls, path: Path | str = "./config.json") -> "AppConfig":
        path = Path(path)
        if not path.exists():
            return cls(path=path)  # cria um novo com defaults
        data = json.loads(path.read_text(encoding="utf-8"))
        cfg_data = dict(DEFAULTS)
        cfg_data.update(data or {})
        cfg = cls(**cfg_data)
        cfg.path = path
        return cfg

    # -----------------------------
    # Salvar configuração atual
    # -----------------------------

    # ----- salvar no arquivo de origem -----
    def save(self):
        data = asdict(self).copy()
        # Não grave 'path' no JSON (é um Path, além de ser metadado interno)
        data.pop("path", None)
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


    # ----- alias compatível com código antigo -----
    def to_file(self, path: Path | str | None = None):
        target = Path(path) if path else self.path
        data = asdict(self).copy()
        data.pop("path", None)
        target.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )