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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, List, Tuple

CHUNK = 1024 * 1024  # 1 MiB
# hash + whitespace + path (não vazio, mas pode ter espaços)
LINE_RE = re.compile(r"^([A-Fa-f0-9]+)\s+(.*?)\s*$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Verifica fixidez a partir de manifesto BagIt ('<hash>  <caminho/relativo>')."
    )
    p.add_argument("--raiz", required=True, help="Pasta raiz onde os arquivos esperados se encontram.")
    p.add_argument("--manifesto", required=True, help="Arquivo de manifesto (ex.: manifest-sha256.txt).")
    p.add_argument(
        "--algo",
        default=None,
        help="Algoritmo de hash. Se omitido, tenta inferir do nome do manifesto (manifest-<algo>.txt).",
    )
    p.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="Threads de verificação.")
    p.add_argument("--progress", action="store_true", default=False, help="Mostra progresso no stderr.")
    p.add_argument(
        "--strict-missing",
        action="store_true",
        default=False,
        help="Retorna erro se houver arquivos faltando (padrão: também retorna erro, mas essa flag deixa explícito).",
    )
    p.add_argument(
        "--report-extras",
        action="store_true",
        default=False,
        help="Compatibilidade: o relatório final sempre lista arquivos extras.",
    )
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


def print_list_section(title: str, items: List[str]) -> None:
    print(f"\n-- {title} --")
    if not items:
        print("Nenhum")
        return
    for item in items:
        print(item)


def main() -> int:
    args = parse_args()

    # remove aspas extras se algum chamador tiver passado com "..." literal
    args.raiz = args.raiz.strip('"').strip("'")
    args.manifesto = args.manifesto.strip('"').strip("'")

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

    entries: List[Tuple[str, str]] = []  # (digest_hex, relpath_posix)
    with mani.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            m = LINE_RE.match(line)
            if not m:
                print(
                    f"[AVISO] Linha ignorada (não casa com '<hash><espacos><path>'): {ln}",
                    file=sys.stderr,
                )
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
    progress_marks_by_count = {}
    for percent in range(5, 101, 5):
        mark = max(1, (total * percent + 99) // 100)
        progress_marks_by_count[mark] = percent
    progress_marks = sorted(progress_marks_by_count.items())
    next_mark_index = 0
    if args.progress:
        print(f"[INFO] Arquivos a verificar: {total} (algo={algo})", file=sys.stderr)
        print("[INFO] Iniciando verificação de arquivos...", file=sys.stderr)

    mismatches: List[str] = []
    corrupted: List[str] = []
    missing: List[str] = []
    ok = 0

    def _check_one(item: Tuple[str, str]) -> Tuple[str, Optional[str]]:
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

    # verificação em paralelo
    verify_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
        futs = {ex.submit(_check_one, it): it for it in entries}
        done = 0
        for fut in as_completed(futs):
            try:
                rel, err = fut.result()
            except Exception as e:
                # erro inesperado em uma thread
                rel = "<desconhecido>"
                err = f"THREAD_ERROR {e}"

            if err is None:
                ok += 1
            elif err == "MISSING":
                missing.append(rel)
            elif err.startswith("MISMATCH"):
                corrupted.append(rel)
                mismatches.append(f"{rel} :: {err}")
            else:
                corrupted.append(rel)
                mismatches.append(f"{rel} :: {err}")
            done += 1

            if args.progress:
                while next_mark_index < len(progress_marks) and done >= progress_marks[next_mark_index][0]:
                    percent = progress_marks[next_mark_index][1]
                    remaining = total - done
                    print(
                        f"[INFO] Progresso {percent}%: verificados {done}/{total}; faltam {remaining}",
                        file=sys.stderr,
                    )
                    next_mark_index += 1

    verify_elapsed = time.perf_counter() - verify_start
    avg_per_file = verify_elapsed / total
    if args.progress:
        print(
            f"[INFO] Verificação finalizada: {total} arquivo(s) verificado(s) em "
            f"{verify_elapsed:.2f}s; média {avg_per_file:.4f}s/arquivo",
            file=sys.stderr,
        )

    # Extras (arquivos em disco não listados)
    extras: List[str] = []
    if args.progress:
        print("[INFO] Procurando arquivos extras em disco...", file=sys.stderr)

    # usa conjunto de strings POSIX para evitar sutilezas de Path
    in_manifest = {rel for _, rel in entries}
    manifest_file_rel = None
    try:
        manifest_file_rel = mani.relative_to(raiz).as_posix()
    except ValueError:
        pass
    for root, dirs, files in os.walk(raiz):
        root_path = Path(root)
        for name in files:
            p = root_path / name
            rel = p.relative_to(raiz)
            rel_posix = rel.as_posix()
            if rel_posix == manifest_file_rel:
                continue
            if rel_posix not in in_manifest:
                extras.append(rel_posix)
    extras.sort()

    # Resumo
    print("=== Verificação de fixidez ===")
    print(f"Manifesto : {mani}")
    print(f"Raiz      : {raiz}")
    print(f"Algoritmo : {algo}")
    print(f"Total no manifesto: {total}")
    print(f"Arquivos verificados íntegros: {ok}")
    print(f"Arquivos verificados corrompidos: {len(corrupted)}")
    print(f"Arquivos no manifesto ausentes na pasta analisada: {len(missing)}")
    print(f"Divergências: {len(mismatches)}")
    print(f"Arquivos na pasta analisada ausentes no manifesto: {len(extras)}")

    print_list_section("Arquivos no manifesto ausentes na pasta analisada", missing)
    print_list_section("Arquivos verificados corrompidos ou com erro", mismatches)
    print_list_section("Arquivos na pasta analisada ausentes no manifesto", extras)

    print("\n=== Resumo final da verificação ===")
    print(f"Total no manifesto: {total}")
    print(f"Arquivos verificados íntegros: {ok}")
    print(f"Arquivos verificados corrompidos: {len(corrupted)}")
    print(f"Arquivos no manifesto ausentes na pasta analisada: {len(missing)}")
    print(f"Arquivos na pasta analisada ausentes no manifesto: {len(extras)}")
    print(f"Tempo de verificação: {verify_elapsed:.2f}s")
    print(f"Média por arquivo verificado: {avg_per_file:.4f}s/arquivo")

    # Exit code: 0 se tudo ok; 1 se houve mismatch/missing
    return 0 if (not mismatches and not missing) else 1


if __name__ == "__main__":
    raise SystemExit(main())
