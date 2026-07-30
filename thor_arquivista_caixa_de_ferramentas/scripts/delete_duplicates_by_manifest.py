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
# -*- coding: utf-8 -*-
"""
delete_duplicates_by_manifest.py — Apaga arquivos duplicados de uma pasta usando
um manifesto BagIt gerado a partir de uma pasta de origem.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from hash_files import hash_file
from pd_common import iter_files, relpath


ALGO = "sha256"
DEFAULT_MANIFEST_NAME = "manifest-sha256.txt"
DEFAULT_REPORT_NAME = "relatorio_exclusao_duplicatas.csv"
DEFAULT_MANIFEST_DIR_NAME = "manifesto_origem"
DEFAULT_REPORT_DIR_NAME = "relatorio_exclusao"
LINE_RE = re.compile(r"^([A-Fa-f0-9]+)\s+(.*?)\s*$")


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
    p = argparse.ArgumentParser(
        description="Apaga arquivos em uma pasta de possíveis duplicatas quando o SHA-256 já existe no manifesto da origem."
    )
    p.add_argument("--origem", required=True, help="Pasta de origem usada para gerar o manifesto de referência.")
    p.add_argument("--duplicatas", required=True, help="Pasta a percorrer e limpar de possíveis duplicatas.")
    p.add_argument("--manifesto", help="Pasta onde o manifesto da origem será gravado. Padrão: subpasta dentro da pasta de duplicatas.")
    p.add_argument("--relatorio", help="Pasta onde o relatório CSV será gravado. Padrão: subpasta dentro da pasta de duplicatas.")
    p.add_argument("--progress", action="store_true", help="Mostra progresso no stderr.")
    return p.parse_args()


def path_overlaps(a: Path, b: Path) -> bool:
    try:
        a.relative_to(b)
        return True
    except ValueError:
        pass
    try:
        b.relative_to(a)
        return True
    except ValueError:
        return False


def run_hash_files(src: Path, manifest: Path, progress: bool) -> int:
    script_path = Path(__file__).resolve().parent / "hash_files.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--raiz",
        str(src),
        "--saida",
        str(manifest),
        "--algo",
        ALGO,
    ]
    if progress:
        cmd.append("--progress")
    proc = subprocess.run(cmd, text=True)  # noqa: S603
    return proc.returncode


def load_manifest_hashes(manifest: Path) -> set[str]:
    hashes: set[str] = set()
    with manifest.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            m = LINE_RE.match(line)
            if m:
                hashes.add(m.group(1).lower())
    return hashes


def write_report(report: Path, rows: list[dict[str, str]], total_bytes: int) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "record_type",
        "deleted_at",
        "path",
        "relpath",
        "sha256",
        "size_bytes",
        "detail",
    ]
    with report.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(
            {
                "record_type": "SUMMARY",
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "path": "",
                "relpath": "",
                "sha256": "",
                "size_bytes": str(total_bytes),
                "detail": f"arquivos_apagados={len(rows)};espaco_recuperado_bytes={total_bytes}",
            }
        )


def main() -> int:
    args = parse_args()
    origem = Path(args.origem).resolve()
    duplicatas = Path(args.duplicatas).resolve()

    if not origem.exists() or not origem.is_dir():
        print(f"[ERRO] Pasta de origem inválida: {origem}", file=sys.stderr)
        return 2
    if not duplicatas.exists() or not duplicatas.is_dir():
        print(f"[ERRO] Pasta de possíveis duplicatas inválida: {duplicatas}", file=sys.stderr)
        return 2
    if path_overlaps(origem, duplicatas):
        print("[ERRO] Origem e pasta de duplicatas não podem ser iguais nem sobrepostas.", file=sys.stderr)
        return 2

    manifest_dir = Path(args.manifesto).resolve() if args.manifesto else duplicatas / DEFAULT_MANIFEST_DIR_NAME
    report_dir = Path(args.relatorio).resolve() if args.relatorio else duplicatas / DEFAULT_REPORT_DIR_NAME
    manifest = manifest_dir / DEFAULT_MANIFEST_NAME
    report = report_dir / DEFAULT_REPORT_NAME
    protected_dirs = {manifest_dir, report_dir}
    protected_outputs = {manifest, report}

    if args.progress:
        print(f"[INFO] Gerando manifesto da origem: {manifest}", file=sys.stderr)
    rc = run_hash_files(origem, manifest, args.progress)
    if rc != 0:
        print(f"[ERRO] Falha ao gerar manifesto da origem (rc={rc})", file=sys.stderr)
        return rc

    ref_hashes = load_manifest_hashes(manifest)
    if not ref_hashes:
        print("[ERRO] Manifesto da origem não contém hashes válidos.", file=sys.stderr)
        return 2

    deleted_rows: list[dict[str, str]] = []
    recovered_bytes = 0
    candidates = [
        p for p in iter_files(duplicatas)
        if p.resolve() not in protected_outputs
        and not any(path_overlaps(p.resolve(), protected_dir) for protected_dir in protected_dirs)
    ]
    total = len(candidates)
    marks = progress_marks(total) if total else []
    next_mark = 0
    started_at = time.perf_counter()
    if args.progress:
        print(f"[INFO] Arquivos a verificar em possíveis duplicatas: {total}", file=sys.stderr)
        print("[INFO] Iniciando exclusão por manifesto...", file=sys.stderr)

    for idx, path in enumerate(candidates, 1):
        try:
            digest = hash_file(path, ALGO).lower()
            if digest not in ref_hashes:
                continue
            size = path.stat().st_size
            rel = relpath(path, duplicatas)
            path.unlink()
            recovered_bytes += size
            deleted_rows.append(
                {
                    "record_type": "DELETED",
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "path": str(path),
                    "relpath": rel,
                    "sha256": digest,
                    "size_bytes": str(size),
                    "detail": "",
                }
            )
        except Exception as e:  # noqa: BLE001
            print(f"[ERRO] Falha ao processar {path}: {e}", file=sys.stderr)
        finally:
            if args.progress:
                next_mark = emit_progress(idx, total, marks, next_mark, "Exclusão por manifesto")

    write_report(report, deleted_rows, recovered_bytes)
    elapsed = time.perf_counter() - started_at
    if args.progress:
        avg = elapsed / total if total else 0.0
        print(
            f"[INFO] Exclusão por manifesto finalizada: {total} arquivo(s) avaliados em "
            f"{elapsed:.2f}s; média {avg:.4f}s/arquivo",
            file=sys.stderr,
        )

    print("=== Exclusão de duplicatas ===")
    print(f"Manifesto origem : {manifest}")
    print(f"Relatório        : {report}")
    print(f"Arquivos apagados: {len(deleted_rows)}")
    print(f"Espaço recuperado: {recovered_bytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
