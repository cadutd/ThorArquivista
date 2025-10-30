
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, os
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um .env, se existir
def load_env():
    # Procura .env na raiz do app (~/.preservacao_app.env) e no cwd
    home_env = Path.home() / ".preservacao_app.env"
    if home_env.exists():
        load_dotenv(home_env.as_posix())
    load_dotenv()  # carrega ./.env se houver

#load_env()

DEFAULTS = {
    "scripts_dir": (Path(__file__).resolve().parent.parent / "scripts").as_posix(),
    "logs_dir": (Path.home() / ".preservacao_logs").as_posix(),
    "premis_log": os.getenv("PREMIS_LOG", (Path.home() / "premis_events.jsonl").as_posix()),
    "premis_agent": os.getenv("PREMIS_AGENT", "Gerenciador de Arquivos — Orquestração")
}

from dataclasses import field

@dataclass
class AppConfig:
    scripts_dir: str = "./scripts"
    logs_dir: str = "./logs"
    premis_log: str = "./logs/premis_events.jsonl"
    premis_agent: str = "Gerenciador de Arquivos — Orquestração"
    jobstore_path: str = "./jobs_db.json"   # <-- novo


    # ----- compatibilidade com .env (opcional) -----
    @classmethod
    def from_env(cls, defaults: "AppConfig") -> "AppConfig":
        cfg = defaults
        cfg.scripts_dir = os.getenv("SCRIPTS_DIR", cfg.scripts_dir)
        cfg.logs_dir = os.getenv("LOGS_DIR", cfg.logs_dir)
        cfg.premis_log = os.getenv("PREMIS_LOG", cfg.premis_log)
        cfg.premis_agent = os.getenv("PREMIS_AGENT", cfg.premis_agent)
        cfg.jobstore_path = os.getenv("JOBSTORE_PATH", cfg.jobstore_path)
        return cfg
    
    # ----- carregar de JSON -----
    @classmethod
    def from_file(cls, path: Path) -> "AppConfig":
        if not Path(path).exists():
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**{**asdict(cls()), **data})

    # ----- salvar para JSON -----
    def to_file(self, path: Path):
        Path(path).write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def from_file(cls, path: Path) -> "AppConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        cfg = dict(DEFAULTS)
        cfg.update(data or {})
        return cls(**cfg)
