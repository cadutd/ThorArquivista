#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_bag.py - Valida pacotes BagIt gerados pelo Thor Arquivista.

Valida a estrutura basica, manifestos de payload (manifest-*.txt), arquivos
em data/ e tagmanifest-*.txt quando presentes.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

CHUNK = 1024 * 1024


@dataclass
class BagValidationReport:
    bag: Path
    payload_manifests: list[Path] = field(default_factory=list)
    tag_manifests: list[Path] = field(default_factory=list)
    payload_ok: int = 0
    payload_corrupt: list[str] = field(default_factory=list)
    payload_missing: list[str] = field(default_factory=list)
    payload_extra: list[str] = field(default_factory=list)
    tag_ok: int = 0
    tag_corrupt: list[str] = field(default_factory=list)
    tag_missing: list[str] = field(default_factory=list)
    invalid_lines: list[str] = field(default_factory=list)
    structure_errors: list[str] = field(default_factory=list)
    elapsed: float = 0.0

    @property
    def checked_total(self) -> int:
        return self.payload_ok + len(self.payload_corrupt) + self.tag_ok + len(self.tag_corrupt)

    @property
    def is_valid(self) -> bool:
        return not (
            self.structure_errors
            or self.invalid_lines
            or self.payload_corrupt
            or self.payload_missing
            or self.payload_extra
            or self.tag_corrupt
            or self.tag_missing
        )


def progress_marks(total: int) -> list[tuple[int, int]]:
    marks_by_count = {}
    for percent in range(5, 101, 5):
        mark = max(1, (total * percent + 99) // 100)
        marks_by_count[mark] = percent
    return sorted(marks_by_count.items())


def emit_progress(done: int, total: int, marks: list[tuple[int, int]], next_mark: int) -> int:
    while next_mark < len(marks) and done >= marks[next_mark][0]:
        percent = marks[next_mark][1]
        print(f"[INFO] Progresso {percent}%: verificados {done}/{total}; faltam {total - done}", file=sys.stderr)
        next_mark += 1
    return next_mark


def digest_file(path: Path, algo: str) -> str:
    try:
        h = getattr(hashlib, algo.lower())()
    except AttributeError as e:
        raise ValueError(f"Algoritmo de hash nao suportado: {algo}") from e
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def relposix(base: Path, path: Path) -> str:
    return path.relative_to(base).as_posix()


def _is_inside(base: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _manifest_algo(path: Path, prefix: str) -> str:
    name = path.name
    if not name.startswith(prefix) or not name.endswith(".txt"):
        return ""
    return name[len(prefix) : -4].lower()


def read_manifest(path: Path) -> tuple[dict[str, str], list[str]]:
    entries: dict[str, str] = {}
    invalid: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = line.strip()
        if not text:
            continue
        parts = text.split(None, 1)
        if len(parts) != 2:
            invalid.append(f"{path.name}:{number}: {line}")
            continue
        digest, rel = parts[0].strip(), parts[1].strip()
        if not digest or not rel:
            invalid.append(f"{path.name}:{number}: {line}")
            continue
        entries[rel] = digest
    return entries, invalid


def iter_data_files(bag: Path) -> Iterable[Path]:
    data_dir = bag / "data"
    if not data_dir.exists():
        return []
    return (p for p in data_dir.rglob("*") if p.is_file())


def _validate_bagit_txt(bag: Path, report: BagValidationReport) -> None:
    bagit = bag / "bagit.txt"
    if not bagit.exists():
        report.structure_errors.append("bagit.txt ausente")
        return
    text = bagit.read_text(encoding="utf-8", errors="replace")
    if "BagIt-Version: 0.97" not in text:
        report.structure_errors.append("bagit.txt sem BagIt-Version: 0.97")
    if "Tag-File-Character-Encoding: UTF-8" not in text:
        report.structure_errors.append("bagit.txt sem Tag-File-Character-Encoding: UTF-8")


def validate_bag(bag: Path, *, algo: str | None = None, progress: bool = False) -> BagValidationReport:
    start = time.perf_counter()
    bag = bag.resolve()
    report = BagValidationReport(bag=bag)

    if not bag.exists() or not bag.is_dir():
        report.structure_errors.append(f"Pasta BagIt invalida: {bag}")
        report.elapsed = time.perf_counter() - start
        return report

    _validate_bagit_txt(bag, report)
    if not (bag / "bag-info.txt").exists():
        report.structure_errors.append("bag-info.txt ausente")
    if not (bag / "data").exists() or not (bag / "data").is_dir():
        report.structure_errors.append("diretorio data/ ausente")

    payload_manifests = sorted(bag.glob("manifest-*.txt"))
    if algo:
        payload_manifests = [p for p in payload_manifests if _manifest_algo(p, "manifest-") == algo.lower()]
    report.payload_manifests = payload_manifests
    if not payload_manifests:
        suffix = f" para o algoritmo {algo}" if algo else ""
        report.structure_errors.append(f"manifesto de payload ausente{suffix}")

    tag_manifests = sorted(bag.glob("tagmanifest-*.txt"))
    if algo:
        tag_manifests = [p for p in tag_manifests if _manifest_algo(p, "tagmanifest-") == algo.lower()]
    report.tag_manifests = tag_manifests

    parsed_payload: list[tuple[Path, str, dict[str, str]]] = []
    parsed_tags: list[tuple[Path, str, dict[str, str]]] = []
    total_entries = 0

    for manifest in payload_manifests:
        manifest_algo = _manifest_algo(manifest, "manifest-")
        entries, invalid = read_manifest(manifest)
        report.invalid_lines.extend(invalid)
        parsed_payload.append((manifest, manifest_algo, entries))
        total_entries += len(entries)

    for manifest in tag_manifests:
        manifest_algo = _manifest_algo(manifest, "tagmanifest-")
        entries, invalid = read_manifest(manifest)
        report.invalid_lines.extend(invalid)
        parsed_tags.append((manifest, manifest_algo, entries))
        total_entries += len(entries)

    if progress:
        print(f"[INFO] Arquivos a verificar no BagIt: {total_entries}", file=sys.stderr)
        print("[INFO] Iniciando validação do BagIt...", file=sys.stderr)

    marks = progress_marks(total_entries) if total_entries else []
    next_mark = 0
    checked = 0
    payload_paths_in_manifests: set[str] = set()

    for manifest, manifest_algo, entries in parsed_payload:
        if not manifest_algo:
            report.structure_errors.append(f"Algoritmo nao identificado em {manifest.name}")
            continue
        for rel, expected in entries.items():
            payload_paths_in_manifests.add(rel)
            target = bag / rel
            if Path(rel).is_absolute() or not _is_inside(bag, target):
                report.structure_errors.append(f"Caminho fora do BagIt em {manifest.name}: {rel}")
            elif not rel.startswith("data/"):
                report.structure_errors.append(f"Payload fora de data/ em {manifest.name}: {rel}")
            elif not target.exists() or not target.is_file():
                report.payload_missing.append(rel)
            else:
                try:
                    actual = digest_file(target, manifest_algo)
                except Exception as e:
                    report.payload_corrupt.append(f"{rel} :: ERRO: {e}")
                else:
                    if actual.lower() == expected.lower():
                        report.payload_ok += 1
                    else:
                        report.payload_corrupt.append(f"{rel} :: MISMATCH")
            checked += 1
            if progress:
                next_mark = emit_progress(checked, total_entries, marks, next_mark)

    data_files = {relposix(bag, p) for p in iter_data_files(bag)}
    report.payload_extra = sorted(data_files - payload_paths_in_manifests)

    for manifest, manifest_algo, entries in parsed_tags:
        if not manifest_algo:
            report.structure_errors.append(f"Algoritmo nao identificado em {manifest.name}")
            continue
        for rel, expected in entries.items():
            target = bag / rel
            if Path(rel).is_absolute() or not _is_inside(bag, target):
                report.structure_errors.append(f"Caminho fora do BagIt em {manifest.name}: {rel}")
            elif not target.exists() or not target.is_file():
                report.tag_missing.append(rel)
            else:
                try:
                    actual = digest_file(target, manifest_algo)
                except Exception as e:
                    report.tag_corrupt.append(f"{rel} :: ERRO: {e}")
                else:
                    if actual.lower() == expected.lower():
                        report.tag_ok += 1
                    else:
                        report.tag_corrupt.append(f"{rel} :: MISMATCH")
            checked += 1
            if progress:
                next_mark = emit_progress(checked, total_entries, marks, next_mark)

    report.elapsed = time.perf_counter() - start
    return report


def _print_list(title: str, items: list[str]) -> None:
    print(f"\n-- {title} --")
    if items:
        for item in items:
            print(item)
    else:
        print("Nenhum")


def print_report(report: BagValidationReport) -> None:
    avg = report.elapsed / report.checked_total if report.checked_total else 0.0
    print("=== Validação de BagIt ===")
    print(f"BagIt: {report.bag}")
    print(f"Manifestos de payload: {len(report.payload_manifests)}")
    print(f"Tagmanifests: {len(report.tag_manifests)}")
    print(f"Arquivos de payload verificados íntegros: {report.payload_ok}")
    print(f"Arquivos de payload verificados corrompidos: {len(report.payload_corrupt)}")
    print(f"Arquivos de payload ausentes: {len(report.payload_missing)}")
    print(f"Arquivos extras em data/ ausentes nos manifestos: {len(report.payload_extra)}")
    print(f"Arquivos de tag verificados íntegros: {report.tag_ok}")
    print(f"Arquivos de tag verificados corrompidos: {len(report.tag_corrupt)}")
    print(f"Arquivos de tag ausentes: {len(report.tag_missing)}")
    print(f"Erros de estrutura: {len(report.structure_errors)}")
    print(f"Linhas inválidas em manifestos: {len(report.invalid_lines)}")

    _print_list("Erros de estrutura", report.structure_errors)
    _print_list("Linhas inválidas em manifestos", report.invalid_lines)
    _print_list("Arquivos de payload ausentes", report.payload_missing)
    _print_list("Arquivos de payload corrompidos ou com erro", report.payload_corrupt)
    _print_list("Arquivos extras em data/ ausentes nos manifestos", report.payload_extra)
    _print_list("Arquivos de tag ausentes", report.tag_missing)
    _print_list("Arquivos de tag corrompidos ou com erro", report.tag_corrupt)

    print("\n=== Resumo final da validação BagIt ===")
    print(f"Resultado: {'VÁLIDO' if report.is_valid else 'INVÁLIDO'}")
    print(f"Total de arquivos verificados: {report.checked_total}")
    print(f"Tempo de validação: {report.elapsed:.2f}s")
    print(f"Média por arquivo verificado: {avg:.4f}s/arquivo")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Valida um pacote BagIt gerado pelo Thor Arquivista.")
    ap.add_argument("bag", type=Path, help="Pasta raiz do pacote BagIt")
    ap.add_argument("--algo", default=None, help="Valida apenas manifestos deste algoritmo, ex.: sha256")
    ap.add_argument("--progress", action="store_true", help="Mostra progresso em marcos de 5%%")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    report = validate_bag(args.bag, algo=args.algo, progress=args.progress)
    print_report(report)
    return 0 if report.is_valid else 2


if __name__ == "__main__":
    sys.exit(main())
