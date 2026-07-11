#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from backup_common import digest_file, iter_files, relposix, write_manifest


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gera manifesto de origem para backup preservacional BagIt.")
    p.add_argument("--raiz", required=True, help="Pasta de origem.")
    p.add_argument("--saida", required=True, help="Arquivo de manifesto a gravar.")
    p.add_argument("--prefix", default="", help="Prefixo BagIt para os caminhos, ex.: data/origem.")
    p.add_argument("--algo", default="sha256", help="Algoritmo de hash.")
    p.add_argument("--ignore-hidden", action="store_true", help="Ignora arquivos e pastas ocultos por ponto.")
    p.add_argument("--follow-symlinks", action="store_true", help="Segue links simbólicos.")
    p.add_argument("--progress", action="store_true", help="Mostra progresso no stderr.")
    return p.parse_args()


def build_manifest(
    raiz: Path,
    *,
    prefix: str = "",
    algo: str = "sha256",
    ignore_hidden: bool = False,
    follow_symlinks: bool = False,
    progress: bool = False,
) -> dict[str, str]:
    raiz = raiz.resolve()
    if not raiz.exists() or not raiz.is_dir():
        raise ValueError(f"Pasta de origem inválida: {raiz}")
    if algo.lower() not in hashlib.algorithms_available:
        raise ValueError(f"Algoritmo não suportado: {algo}")

    prefix = prefix.strip("/").replace("\\", "/")
    files = sorted(iter_files(raiz, ignore_hidden=ignore_hidden, follow_symlinks=follow_symlinks), key=lambda p: relposix(raiz, p))
    entries: dict[str, str] = {}
    total = len(files)
    for idx, src in enumerate(files, 1):
        rel = relposix(raiz, src)
        key = f"{prefix}/{rel}" if prefix else rel
        entries[key] = digest_file(src, algo)
        if progress and (idx % 50 == 0 or idx == total):
            print(f"[INFO] Manifesto origem: {idx}/{total}", file=sys.stderr)
    return entries


def main() -> int:
    args = parse_args()
    try:
        entries = build_manifest(
            Path(args.raiz),
            prefix=args.prefix,
            algo=args.algo,
            ignore_hidden=args.ignore_hidden,
            follow_symlinks=args.follow_symlinks,
            progress=args.progress,
        )
        write_manifest(Path(args.saida), entries)
        print(f"Manifesto gerado: {Path(args.saida).resolve()} ({len(entries)} entrada(s))")
        return 0
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
