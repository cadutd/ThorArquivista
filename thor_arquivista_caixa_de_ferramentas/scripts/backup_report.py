#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lista histórico e checkpoint de um backup preservacional.")
    p.add_argument("--destino", required=True, help="Raiz do repositório BagIt de backup.")
    p.add_argument("--backup", help="Nome do backup para localizar checkpoint.")
    p.add_argument("--saida", help="Arquivo JSON de relatório consolidado.")
    return p.parse_args()


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    args = parse_args()
    dest = Path(args.destino).resolve()
    tb = dest / "thor-backup"
    if not tb.exists():
        print(f"[ERRO] Estrutura thor-backup não encontrada: {tb}", file=sys.stderr)
        return 2
    checkpoints = sorted((tb / "checkpoints").glob("*.state.json"))
    reports = sorted((tb / "relatorios").glob("*"))
    manifests = sorted((tb / "manifests" / "historico").glob("*"))
    if args.backup:
        cp = tb / "checkpoints" / f"{args.backup}.state.json"
        checkpoints = [cp] if cp.exists() else []
    data = {
        "destino": str(dest),
        "checkpoints": [{"path": str(p), "state": _load_json(p)} for p in checkpoints],
        "relatorios": [str(p) for p in reports],
        "manifestos_historicos": [str(p) for p in manifests],
    }
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.saida:
        Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(args.saida).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
