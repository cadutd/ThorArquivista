#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from backup_common import append_premis


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Valida fixidez do repositório BagIt de backup preservacional.")
    p.add_argument("--destino", required=True, help="Raiz do repositório BagIt de backup.")
    p.add_argument("--algo", default="sha256", help="Algoritmo do manifesto.")
    p.add_argument("--progress", action="store_true", help="Mostra progresso.")
    p.add_argument("--premis-log", help="Arquivo JSONL PREMIS.")
    p.add_argument("--agent", default="Thor Arquivista backup_verify.py", help="Agente PREMIS.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dest = Path(args.destino).resolve()
    manifest = dest / f"manifest-{args.algo.lower()}.txt"
    if not dest.exists() or not dest.is_dir():
        print(f"[ERRO] Destino inválido: {dest}", file=sys.stderr)
        return 2
    if not manifest.exists():
        print(f"[ERRO] Manifesto do backup não encontrado: {manifest}", file=sys.stderr)
        return 2
    verify = Path(__file__).resolve().parent / "verify_fixity.py"
    cmd = [sys.executable, str(verify), "--raiz", str(dest), "--manifesto", str(manifest)]
    if args.progress:
        cmd.append("--progress")
    rc = subprocess.call(cmd)
    if args.premis_log:
        append_premis(
            Path(args.premis_log),
            "FIXITY_CHECK",
            str(manifest),
            f"Verificação do backup {dest} concluída com exit code {rc}.",
            "success" if rc == 0 else "failure",
            args.agent,
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
