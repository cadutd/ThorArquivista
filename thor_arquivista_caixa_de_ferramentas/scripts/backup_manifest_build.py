#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

from backup_common import digest_file, iter_files, relposix, write_manifest


def progress_marks(total: int) -> list[tuple[int, int]]:
    marks_by_count = {}
    for percent in range(5, 101, 5):
        mark = max(1, (total * percent + 99) // 100)
        marks_by_count[mark] = percent
    return sorted(marks_by_count.items())


def emit_progress(done: int, total: int, marks: list[tuple[int, int]], next_mark: int, label: str) -> int:
    while next_mark < len(marks) and done >= marks[next_mark][0]:
        percent = marks[next_mark][1]
        print(f"[INFO] {label} {percent}%: processados {done}/{total}; faltam {total - done}", file=sys.stderr)
        next_mark += 1
    return next_mark


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
    marks = progress_marks(total) if total else []
    next_mark = 0
    started_at = time.perf_counter()
    if progress:
        print(f"[INFO] Arquivos a processar no manifesto de origem: {total}", file=sys.stderr)
    for idx, src in enumerate(files, 1):
        rel = relposix(raiz, src)
        key = f"{prefix}/{rel}" if prefix else rel
        entries[key] = digest_file(src, algo)
        if progress:
            next_mark = emit_progress(idx, total, marks, next_mark, "Manifesto origem")
    if progress:
        elapsed = time.perf_counter() - started_at
        avg = elapsed / total if total else 0.0
        print(
            f"[INFO] Manifesto origem finalizado: {total} arquivo(s) processado(s) em "
            f"{elapsed:.2f}s; média {avg:.4f}s/arquivo",
            file=sys.stderr,
        )
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
