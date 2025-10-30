from __future__ import annotations
from pathlib import Path
from core.config import AppConfig
from ui.main_window import run_app

def main():
    # Caminho do arquivo de configuração agora na raiz do projeto
    root_cfg = Path(__file__).resolve().parent / "preservacao_app.json"

    # cria o arquivo padrão se não existir
    if not root_cfg.exists():
        AppConfig().to_file(root_cfg)

    # carrega e executa
    cfg = AppConfig.from_file(root_cfg)
    run_app(cfg)

if __name__ == "__main__":
    main()
