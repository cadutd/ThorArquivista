# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
# Copyright (C) 2025  Carlos Eduardo Carvalho Amand
#
# Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral Affero GNU (GNU AGPL), conforme publicada
# pela Free Software Foundation, na versão 3 da Licença, ou (a seu critério)
# qualquer versão posterior.
#
# Este programa é distribuído na esperança de que seja útil,
# mas SEM QUALQUER GARANTIA; sem mesmo a garantia implícita de
# COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM PROPÓSITO PARTICULAR.
# Veja a Licença Pública Geral Affero GNU para mais detalhes.
#
# Você deve ter recebido uma cópia da GNU AGPL junto com este programa.
# Caso contrário, veja <https://www.gnu.org/licenses/>.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
replicate_storage.py — Replica arquivos para múltiplos destinos e valida com manifesto BagIt.
"""
import argparse, subprocess, sys, time
from pathlib import Path
from pd_common import iter_files, relpath, safe_copy, add_common_args, load_config


MANIFEST_NAME = "manifest-sha256.txt"


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


def run_script(script_path: Path, args: list[str]) -> int:
    cmd = [sys.executable, str(script_path), *args]
    proc = subprocess.run(cmd, text=True)  # noqa: S603
    return proc.returncode


def path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser(description="Replicar dados para destinos múltiplos.")
    ap.add_argument("--fonte", required=True, help="Pasta de origem.")
    ap.add_argument("--destino", required=True, action="append", help="Pasta de destino (pode repetir).")
    ap.add_argument("--verificar-hash", action="store_true", help="Compatibilidade: a verificação por manifesto é sempre executada.")
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    progress = not args.quiet
    src = Path(args.fonte).resolve()
    if not src.exists() or not src.is_dir():
        print(f"[ERRO] Pasta de origem inválida: {src}", file=sys.stderr)
        sys.exit(2)

    dests = [Path(d).resolve() for d in args.destino]
    for d in dests:
        if path_is_relative_to(d, src):
            print(f"[ERRO] Destino não pode estar dentro da origem: {d}", file=sys.stderr)
            sys.exit(2)
        d.mkdir(parents=True, exist_ok=True)

    scripts_dir = Path(__file__).resolve().parent
    hash_script = scripts_dir / "hash_files.py"
    verify_script = scripts_dir / "verify_fixity.py"

    files = list(iter_files(src))
    if progress:
        print(f"[INFO] Arquivos a copiar: {len(files)}; destinos: {len(dests)}", file=sys.stderr)

    for d in dests:
        manifest = d / MANIFEST_NAME
        if progress:
            print(f"[INFO] Gerando manifesto BagIt em: {manifest}", file=sys.stderr)
        hash_args = [
            "--raiz", str(src),
            "--saida", str(manifest),
            "--algo", "sha256",
        ]
        if progress:
            hash_args.append("--progress")
        rc = run_script(
            hash_script,
            hash_args,
        )
        if rc != 0:
            print(f"[ERRO] Falha ao gerar manifesto para {d} (rc={rc})", file=sys.stderr)
            sys.exit(rc)

    copy_total = len(files) * len(dests)
    copy_marks = progress_marks(copy_total) if copy_total else []
    copy_next_mark = 0
    copy_done = 0
    copy_start = time.perf_counter()
    for p in files:
        rel = relpath(p, src)
        for d in dests:
            target = d / rel
            safe_copy(p, target)
            copy_done += 1
            if progress:
                copy_next_mark = emit_progress(copy_done, copy_total, copy_marks, copy_next_mark, "Cópia")
    copy_elapsed = time.perf_counter() - copy_start
    if progress:
        avg = copy_elapsed / copy_total if copy_total else 0.0
        print(
            f"[INFO] Cópia finalizada: {copy_total} operação(ões) em "
            f"{copy_elapsed:.2f}s; média {avg:.4f}s/operação",
            file=sys.stderr,
        )

    for d in dests:
        manifest = d / MANIFEST_NAME
        if progress:
            print(f"[INFO] Verificando destino com manifesto: {manifest}", file=sys.stderr)
        verify_args = [
            "--raiz", str(d),
            "--manifesto", str(manifest),
            "--algo", "sha256",
        ]
        if progress:
            verify_args.append("--progress")
        rc = run_script(
            verify_script,
            verify_args,
        )
        if rc != 0:
            print(f"[ERRO] Verificação de fixidez falhou em {d} (rc={rc})", file=sys.stderr)
            sys.exit(rc)

    print("Replicação concluída.")

if __name__ == "__main__":
    main()
