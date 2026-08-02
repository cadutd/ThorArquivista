#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
incremental_backup_from_fixity.py - Aplica backup incremental a partir do
relatório TXT estruturado emitido por verify_fixity.py.
Relatórios novos omitem registros OK; relatórios antigos com OK continuam
compatíveis e esses registros são ignorados.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ACTION_STATUSES = {"MISSING", "CORRUPT", "ERROR"}


def progress_marks(total: int) -> list[tuple[int, int]]:
    marks_by_count = {}
    for percent in range(5, 101, 5):
        mark = max(1, (total * percent + 99) // 100)
        marks_by_count[mark] = percent
    return sorted(marks_by_count.items())


def emit_progress(done: int, total: int, marks: list[tuple[int, int]], next_mark: int) -> int:
    while next_mark < len(marks) and done >= marks[next_mark][0]:
        percent = marks[next_mark][1]
        print(f"[INFO] Progresso {percent}%: aplicados {done}/{total}; faltam {total - done}", file=sys.stderr)
        next_mark += 1
    return next_mark


def default_report_path(destino: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return destino / f"incremental_backup_report_{stamp}.txt"


def _inside(base: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def read_fixity_records(report: Path) -> list[Dict[str, str]]:
    lines = report.read_text(encoding="utf-8").splitlines()
    header_index = None
    for index, line in enumerate(lines):
        if line == "status\tpath\texpected_hash\tactual_hash\tdetail":
            header_index = index
            break
    if header_index is None:
        raise ValueError("Relatório de fixidez sem seção TSV estruturada.")

    data = "\n".join(lines[header_index:])
    reader = csv.DictReader(data.splitlines(), delimiter="\t")
    records: list[Dict[str, str]] = []
    for row in reader:
        status = (row.get("status") or "").strip().upper()
        rel = (row.get("path") or "").strip().replace("\\", "/")
        if not status or not rel:
            continue
        records.append(
            {
                "status": status,
                "path": rel,
                "expected_hash": row.get("expected_hash") or "",
                "actual_hash": row.get("actual_hash") or "",
                "detail": row.get("detail") or "",
            }
        )
    return records


def _candidate_source_paths(origem: Path, rel: str) -> Iterable[Path]:
    yield origem / Path(rel)
    if rel.startswith("data/"):
        yield origem / Path(rel[5:])


def resolve_source(origem: Path, rel: str) -> Path | None:
    for candidate in _candidate_source_paths(origem, rel):
        if _inside(origem, candidate) and candidate.exists() and candidate.is_file():
            return candidate
    return None


def apply_incremental_backup(
    *,
    relatorio_fixidez: Path,
    origem: Path,
    destino: Path,
    report_file: Path,
    dry_run: bool = False,
    progress: bool = False,
) -> int:
    start = time.perf_counter()
    records = read_fixity_records(relatorio_fixidez)
    actionable = [r for r in records if r["status"] in ACTION_STATUSES]
    skipped_ok = sum(1 for r in records if r["status"] == "OK")
    skipped_extra = sum(1 for r in records if r["status"] == "EXTRA")

    if progress:
        print(f"[INFO] Registros no relatório de fixidez: {len(records)}", file=sys.stderr)
        print(f"[INFO] Arquivos a aplicar no incremental: {len(actionable)}", file=sys.stderr)

    copied: list[str] = []
    source_missing: list[str] = []
    invalid_paths: list[str] = []
    failed: list[str] = []

    marks = progress_marks(len(actionable)) if actionable else []
    next_mark = 0

    for index, record in enumerate(actionable, 1):
        rel = record["path"]
        dest_file = destino / Path(rel)
        if Path(rel).is_absolute() or not _inside(destino, dest_file):
            invalid_paths.append(rel)
        else:
            src_file = resolve_source(origem, rel)
            if src_file is None:
                source_missing.append(rel)
            else:
                try:
                    if not dry_run:
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dest_file)
                    copied.append(rel)
                except Exception as e:
                    failed.append(f"{rel} :: {e}")

        if progress:
            next_mark = emit_progress(index, len(actionable), marks, next_mark)

    elapsed = time.perf_counter() - start
    lines = [
        "=== Backup incremental por relatório de fixidez ===",
        f"Relatório de fixidez: {relatorio_fixidez}",
        f"Origem: {origem}",
        f"Destino: {destino}",
        f"Modo simulação: {'sim' if dry_run else 'não'}",
        f"Registros lidos: {len(records)}",
        f"Registros OK ignorados: {skipped_ok}",
        f"Registros EXTRA ignorados: {skipped_extra}",
        f"Arquivos candidatos a copiar: {len(actionable)}",
        f"Arquivos copiados: {len(copied)}",
        f"Arquivos ausentes na origem: {len(source_missing)}",
        f"Caminhos inválidos no relatório: {len(invalid_paths)}",
        f"Falhas de cópia: {len(failed)}",
        f"Tempo de aplicação: {elapsed:.2f}s",
        "",
        "-- Arquivos copiados --",
        *(copied or ["Nenhum"]),
        "",
        "-- Arquivos ausentes na origem --",
        *(source_missing or ["Nenhum"]),
        "",
        "-- Caminhos inválidos no relatório --",
        *(invalid_paths or ["Nenhum"]),
        "",
        "-- Falhas de cópia --",
        *(failed or ["Nenhum"]),
    ]
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if not (source_missing or invalid_paths or failed) else 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Aplica backup incremental usando relatório estruturado de verify_fixity.py."
    )
    parser.add_argument("--relatorio-fixidez", required=True, type=Path, help="Relatório TXT gerado por verify_fixity.py.")
    parser.add_argument("--origem", required=True, type=Path, help="Pasta de origem do backup.")
    parser.add_argument("--destino", required=True, type=Path, help="Pasta de destino a atualizar.")
    parser.add_argument("--saida-relatorio", default=None, type=Path, help="Relatório TXT da aplicação incremental.")
    parser.add_argument("--dry-run", action="store_true", help="Simula a aplicação sem copiar arquivos.")
    parser.add_argument("--progress", action="store_true", help="Mostra progresso em marcos de 5%%.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    relatorio = args.relatorio_fixidez.resolve()
    origem = args.origem.resolve()
    destino = args.destino.resolve()
    if not relatorio.exists() or not relatorio.is_file():
        print(f"[ERRO] Relatório de fixidez inválido: {relatorio}", file=sys.stderr)
        return 2
    if not origem.exists() or not origem.is_dir():
        print(f"[ERRO] Pasta de origem inválida: {origem}", file=sys.stderr)
        return 2
    if not destino.exists() or not destino.is_dir():
        print(f"[ERRO] Pasta de destino inválida: {destino}", file=sys.stderr)
        return 2
    report_file = args.saida_relatorio.resolve() if args.saida_relatorio else default_report_path(destino)
    try:
        return apply_incremental_backup(
            relatorio_fixidez=relatorio,
            origem=origem,
            destino=destino,
            report_file=report_file,
            dry_run=bool(args.dry_run),
            progress=bool(args.progress),
        )
    except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
