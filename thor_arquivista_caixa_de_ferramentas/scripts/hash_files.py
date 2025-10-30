#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

CHUNK = 1024 * 1024  # 1 MiB


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gera manifesto BagIt: '<hash>  <caminho/relativo>'."
    )
    p.add_argument("--raiz", required=True, help="Pasta raiz para varredura.")
    p.add_argument("--saida", required=True, help="Arquivo de saída do manifesto (ex.: manifest-sha256.txt).")
    p.add_argument("--algo", default="sha256", choices=sorted(hashlib.algorithms_available),
                   help="Algoritmo de hash (padrão: sha256).")
    p.add_argument("--include-ext", nargs="*", default=[],
                   help="Extensões a incluir (sem ponto) ex.: pdf jpg png. Vazio = todas.")
    p.add_argument("--exclude-ext", nargs="*", default=[],
                   help="Extensões a excluir (sem ponto).")
    p.add_argument("--min-size", type=int, default=None, help="Tamanho mínimo (bytes).")
    p.add_argument("--max-size", type=int, default=None, help="Tamanho máximo (bytes).")
    p.add_argument("--modified-after", type=str, default=None, help="YYYY-MM-DD.")
    p.add_argument("--modified-before", type=str, default=None, help="YYYY-MM-DD.")
    p.add_argument("--pattern", type=str, default=None, help="Glob relativo (ex.: **/*.pdf).")
    p.add_argument("--ignore-hidden", action="store_true", default=False, help="Ignora itens ocultos (prefixo .).")
    p.add_argument("--follow-symlinks", action="store_true", default=False, help="Segue links simbólicos.")
    p.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="Threads (padrão: núcleos da máquina).")
    p.add_argument("--progress", action="store_true", default=False, help="Mostra progresso no stderr.")
    return p.parse_args()


def is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def dt_from_yyyy_mm_dd(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").timestamp()


def iter_files(raiz: Path, follow_symlinks: bool, ignore_hidden_flag: bool):
    for root, dirs, files in os.walk(raiz, followlinks=follow_symlinks):
        root_path = Path(root)
        if ignore_hidden_flag:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            p = root_path / name
            rel = p.relative_to(raiz)
            if ignore_hidden_flag and is_hidden(rel):
                continue
            if not follow_symlinks and p.is_symlink():
                continue
            if p.is_file():
                yield p


def ext_of(p: Path) -> str:
    return (p.suffix[1:] if p.suffix.startswith(".") else p.suffix).lower()


def pass_filters(p: Path,
                 raiz: Path,
                 include_ext: list[str],
                 exclude_ext: list[str],
                 min_size: Optional[int],
                 max_size: Optional[int],
                 mod_after_ts: Optional[float],
                 mod_before_ts: Optional[float],
                 pattern: Optional[str]) -> bool:
    rel = p.relative_to(raiz).as_posix()
    if pattern and not fnmatch(rel, pattern):
        return False

    e = ext_of(p)
    if include_ext and e not in [x.lower() for x in include_ext]:
        return False
    if exclude_ext and e in [x.lower() for x in exclude_ext]:
        return False

    try:
        st = p.stat()
    except OSError:
        return False

    if (min_size is not None) and st.st_size < min_size:
        return False
    if (max_size is not None) and st.st_size > max_size:
        return False

    if (mod_after_ts is not None) and st.st_mtime <= mod_after_ts:
        return False
    if (mod_before_ts is not None) and st.st_mtime >= mod_before_ts:
        return False

    return True


def hash_file(p: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with p.open("rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    args = parse_args()
    raiz = Path(args.raiz).resolve()
    saida = Path(args.saida).resolve()

    if not raiz.exists() or not raiz.is_dir():
        print(f"[ERRO] Pasta raiz inválida: {raiz}", file=sys.stderr)
        return 2

    mod_after_ts = dt_from_yyyy_mm_dd(args.modified_after)
    mod_before_ts = dt_from_yyyy_mm_dd(args.modified_before)

    candidates: list[Path] = []
    for p in iter_files(raiz, args.follow_symlinks, args.ignore_hidden):
        if pass_filters(
            p, raiz,
            args.include_ext, args.exclude_ext,
            args.min_size, args.max_size,
            mod_after_ts, mod_before_ts,
            args.pattern
        ):
            candidates.append(p)

    total = len(candidates)
    if args.progress:
        print(f"[INFO] Arquivos a processar: {total}", file=sys.stderr)

    results: list[tuple[Path, str | None, str | None]] = []
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
        futs = {ex.submit(hash_file, p, args.algo): p for p in candidates}
        done = 0
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                digest = fut.result()
                results.append((p, digest, None))
            except Exception as e:
                results.append((p, None, str(e)))
            done += 1
            if args.progress and (done % 50 == 0 or done == total):
                print(f"[INFO] Progresso: {done}/{total}", file=sys.stderr)

    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="\n") as out:
        for p, digest, err in sorted(results, key=lambda t: t[0].relative_to(raiz).as_posix()):
            if digest is None:
                print(f"[ERRO] Falha ao calcular hash: {p} -> {err}", file=sys.stderr)
                continue
            rel = p.relative_to(raiz).as_posix()
            # BagIt: hash + dois espaços + caminho relativo (POSIX)
            out.write(f"{digest}  {rel}\n")

    if args.progress:
        print(f"[INFO] Manifesto gerado em: {saida}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
