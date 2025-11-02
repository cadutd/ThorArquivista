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


#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

CHUNK = 1024 * 1024  # 1 MiB
LINE_RE = re.compile(r"^([A-Fa-f0-9]+)\s+(.*\S)\s*$")  # hash + whitespace + path (não vazio)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Verifica fixidez a partir de manifesto BagIt ('<hash>  <caminho/relativo>')."
    )
    p.add_argument("--raiz", required=True, help="Pasta raiz onde os arquivos esperados se encontram.")
    p.add_argument("--manifesto", required=True, help="Arquivo de manifesto (ex.: manifest-sha256.txt).")
    p.add_argument("--algo", default=None,
                   help="Algoritmo de hash. Se omitido, tenta inferir do nome do manifesto (manifest-<algo>.txt).")
    p.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="Threads de verificação.")
    p.add_argument("--progress", action="store_true", default=False, help="Mostra progresso no stderr.")
    p.add_argument("--strict-missing", action="store_true", default=False,
                   help="Retorna erro se houver arquivos faltando (padrão: também retorna erro, mas essa flag deixa explícito).")
    p.add_argument("--report-extras", action="store_true", default=False,
                   help="Reporta arquivos presentes em disco mas ausentes no manifesto.")
    return p.parse_args()


def infer_algo_from_filename(path: Path) -> Optional[str]:
    # tenta achar manifest-<algo>.txt
    m = re.search(r"manifest-([A-Za-z0-9_]+)\.txt$", path.name)
    if m:
        return m.group(1).lower()
    return None


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
    mani = Path(args.manifesto).resolve()

    if not raiz.exists() or not raiz.is_dir():
        print(f"[ERRO] Pasta raiz inválida: {raiz}", file=sys.stderr)
        return 2
    if not mani.exists() or not mani.is_file():
        print(f"[ERRO] Manifesto inválido: {mani}", file=sys.stderr)
        return 2

    algo = (args.algo or infer_algo_from_filename(mani) or "sha256").lower()
    if algo not in hashlib.algorithms_available:
        print(f"[ERRO] Algoritmo não suportado: {algo}", file=sys.stderr)
        return 2

    entries: list[tuple[str, str]] = []  # (digest_hex, relpath_posix)
    with mani.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            m = LINE_RE.match(line)
            if not m:
                print(f"[AVISO] Linha ignorada (não casa com '<hash><espacos><path>'): {ln}", file=sys.stderr)
                continue
            digest = m.group(1).lower()
            rel = m.group(2)
            # normaliza para POSIX no manifesto
            rel = rel.replace("\\", "/")
            entries.append((digest, rel))

    if not entries:
        print("[ERRO] Manifesto sem entradas válidas.", file=sys.stderr)
        return 2

    total = len(entries)
    if args.progress:
        print(f"[INFO] Entradas no manifesto: {total} (algo={algo})", file=sys.stderr)

    mismatches: list[str] = []
    missing: list[str] = []
    ok = 0

    def _check_one(item: tuple[str, str]) -> tuple[str, Optional[str]]:
        exp_digest, rel = item
        p = raiz / Path(rel)
        if not p.exists() or not p.is_file():
            return (rel, "MISSING")
        try:
            d = hash_file(p, algo).lower()
            if d != exp_digest:
                return (rel, f"MISMATCH expected={exp_digest} got={d}")
            return (rel, None)
        except Exception as e:
            return (rel, f"ERROR {e}")

    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
        futs = {ex.submit(_check_one, it): it for it in entries}
        done = 0
        for fut in as_completed(futs):
            rel, err = fut.result()
            if err is None:
                ok += 1
            elif err == "MISSING":
                missing.append(rel)
            elif err.startswith("MISMATCH"):
                mismatches.append(f"{rel} :: {err}")
            else:
                mismatches.append(f"{rel} :: {err}")
            done += 1
            if args.progress and (done % 50 == 0 or done == total):
                print(f"[INFO] Progresso: {done}/{total}", file=sys.stderr)

    # Extras (arquivos em disco não listados)
    extras_count = 0
    if args.report_extras:
        in_manifest = {Path(rel) for _, rel in entries}
        for root, dirs, files in os.walk(raiz):
            root_path = Path(root)
            for name in files:
                p = root_path / name
                rel = p.relative_to(raiz)
                rel_posix = rel.as_posix()
                if Path(rel_posix) not in in_manifest:
                    extras_count += 1
                    print(f"[EXTRA] {rel_posix}", file=sys.stderr)

    # Resumo
    print("=== Verificação de fixidez ===")
    print(f"Manifesto : {mani}")
    print(f"Raiz      : {raiz}")
    print(f"Algoritmo : {algo}")
    print(f"Total     : {total}")
    print(f"OK        : {ok}")
    print(f"Faltando  : {len(missing)}")
    print(f"Divergências: {len(mismatches)}")
    if args.report_extras:
        print(f"Extras    : {extras_count}")

    if missing:
        print("\n-- Faltando --")
        for r in missing[:200]:
            print(r)
        if len(missing) > 200:
            print(f"... (+{len(missing)-200} ocultos)")

    if mismatches:
        print("\n-- Divergências --")
        for r in mismatches[:200]:
            print(r)
        if len(mismatches) > 200:
            print(f"... (+{len(mismatches)-200} ocultos)")

    # Exit code: 0 se tudo ok; 1 se houve mismatch/missing
    return 0 if (not mismatches and not missing) else 1


if __name__ == "__main__":
    raise SystemExit(main())
