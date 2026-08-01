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
from datetime import datetime, timezone
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
    p.add_argument(
        "--max-list-items",
        type=int,
        default=200,
        help="Máximo de itens por lista no stdout/log. Use 0 para listar tudo.",
    )
    p.add_argument(
        "--report-file",
        default=None,
        help="Arquivo TXT do relatório completo e estruturado. Se omitido, gera automaticamente.",
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


def list_section_lines(title: str, items: List[str], *, max_items: Optional[int] = None) -> tuple[list[str], bool]:
    lines = ["", f"-- {title} --"]
    if not items:
        lines.append("Nenhum")
        return lines, False
    limited = max_items is not None and max_items > 0 and len(items) > max_items
    shown = items[:max_items] if limited else items
    lines.extend(shown)
    if limited:
        lines.append(f"... {len(items) - len(shown)} item(s) omitidos nesta visualização.")
    return lines, limited


def build_report_lines(
    *,
    mani: Path,
    raiz: Path,
    algo: str,
    total: int,
    ok: int,
    corrupted: List[str],
    missing: List[str],
    mismatches: List[str],
    extras: List[str],
    verify_elapsed: float,
    avg_per_file: float,
    max_list_items: Optional[int] = None,
    full_report_path: Optional[Path] = None,
    structured_records: Optional[List[Tuple[str, str, str, str, str]]] = None,
) -> tuple[list[str], bool]:
    lines = [
        "=== Verificação de fixidez ===",
        f"Manifesto : {mani}",
        f"Raiz      : {raiz}",
        f"Algoritmo : {algo}",
        f"Total no manifesto: {total}",
        f"Arquivos verificados íntegros: {ok}",
        f"Arquivos verificados corrompidos: {len(corrupted)}",
        f"Arquivos no manifesto ausentes na pasta analisada: {len(missing)}",
        f"Divergências: {len(mismatches)}",
        f"Arquivos na pasta analisada ausentes no manifesto: {len(extras)}",
    ]
    omitted = False
    for title, items in (
        ("Arquivos no manifesto ausentes na pasta analisada", missing),
        ("Arquivos verificados corrompidos ou com erro", mismatches),
        ("Arquivos na pasta analisada ausentes no manifesto", extras),
    ):
        section, section_omitted = list_section_lines(title, items, max_items=max_list_items)
        lines.extend(section)
        omitted = omitted or section_omitted

    if full_report_path:
        lines.extend(["", f"Relatório completo: {full_report_path}"])

    lines.extend(
        [
            "",
            "=== Resumo final da verificação ===",
            f"Total no manifesto: {total}",
            f"Arquivos verificados íntegros: {ok}",
            f"Arquivos verificados corrompidos: {len(corrupted)}",
            f"Arquivos no manifesto ausentes na pasta analisada: {len(missing)}",
            f"Arquivos na pasta analisada ausentes no manifesto: {len(extras)}",
            f"Tempo de verificação: {verify_elapsed:.2f}s",
            f"Média por arquivo verificado: {avg_per_file:.4f}s/arquivo",
        ]
    )
    if structured_records is not None:
        lines.extend(
            [
                "",
                "=== Dados estruturados para backup incremental ===",
                "# Formato: TSV",
                "# Colunas: status\tpath\texpected_hash\tactual_hash\tdetail",
                "status\tpath\texpected_hash\tactual_hash\tdetail",
            ]
        )
        for status, path, expected_hash, actual_hash, detail in structured_records:
            lines.append(
                "\t".join(
                    [
                        status,
                        path.replace("\t", " "),
                        expected_hash,
                        actual_hash,
                        detail.replace("\t", " "),
                    ]
                )
            )
    return lines, omitted


def default_report_path(manifest: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return manifest.parent / f"verify_fixity_report_{stamp}.txt"


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
    structured_records: List[Tuple[str, str, str, str, str]] = []
    ok = 0

    def _check_one(item: Tuple[str, str]) -> Tuple[str, str, str, str, str]:
        exp_digest, rel = item
        p = raiz / Path(rel)
        if not p.exists() or not p.is_file():
            return (rel, "MISSING", exp_digest, "", "Arquivo listado no manifesto ausente na pasta analisada")
        try:
            d = hash_file(p, algo).lower()
            if d != exp_digest:
                return (rel, "CORRUPT", exp_digest, d, "Hash gerado diferente do hash no manifesto")
            return (rel, "OK", exp_digest, d, "")
        except Exception as e:
            return (rel, "ERROR", exp_digest, "", str(e))

    # verificação em paralelo
    verify_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
        futs = {ex.submit(_check_one, it): it for it in entries}
        done = 0
        for fut in as_completed(futs):
            try:
                rel, status, expected_hash, actual_hash, detail = fut.result()
            except Exception as e:
                # erro inesperado em uma thread
                rel = "<desconhecido>"
                status = "ERROR"
                expected_hash = ""
                actual_hash = ""
                detail = f"THREAD_ERROR {e}"

            structured_records.append((status, rel, expected_hash, actual_hash, detail))
            if status == "OK":
                ok += 1
            elif status == "MISSING":
                missing.append(rel)
            elif status == "CORRUPT":
                corrupted.append(rel)
                mismatches.append(f"{rel} :: MISMATCH expected={expected_hash} got={actual_hash}")
            else:
                corrupted.append(rel)
                mismatches.append(f"{rel} :: ERROR {detail}")
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
                structured_records.append(("EXTRA", rel_posix, "", "", "Arquivo presente na pasta analisada e ausente no manifesto"))
    extras.sort()
    missing.sort()
    corrupted.sort()
    mismatches.sort()
    structured_records.sort(key=lambda item: (item[0], item[1]))

    max_list_items = max(0, int(args.max_list_items))
    report_path = Path(args.report_file).resolve() if args.report_file else default_report_path(mani)
    full_lines, _ = build_report_lines(
        mani=mani,
        raiz=raiz,
        algo=algo,
        total=total,
        ok=ok,
        corrupted=corrupted,
        missing=missing,
        mismatches=mismatches,
        extras=extras,
        verify_elapsed=verify_elapsed,
        avg_per_file=avg_per_file,
        max_list_items=None,
        structured_records=structured_records,
    )
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(full_lines) + "\n", encoding="utf-8")
    except OSError:
        report_path = Path.cwd() / report_path.name
        report_path.write_text("\n".join(full_lines) + "\n", encoding="utf-8")

    compact_lines, omitted = build_report_lines(
        mani=mani,
        raiz=raiz,
        algo=algo,
        total=total,
        ok=ok,
        corrupted=corrupted,
        missing=missing,
        mismatches=mismatches,
        extras=extras,
        verify_elapsed=verify_elapsed,
        avg_per_file=avg_per_file,
        max_list_items=max_list_items or None,
        full_report_path=report_path,
    )

    print("\n".join(compact_lines))

    # Exit code: 0 se tudo ok; 1 se houve mismatch/missing
    return 0 if (not mismatches and not missing) else 1


if __name__ == "__main__":
    raise SystemExit(main())
