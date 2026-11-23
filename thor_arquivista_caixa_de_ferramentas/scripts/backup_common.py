#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CHUNK = 1024 * 1024
LINE_RE = re.compile(r"^([A-Fa-f0-9]+)\s+(.*?)\s*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def safe_name(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE)
    value = value.strip("._")
    return value or "origem"


def relposix(base: Path, path: Path) -> str:
    return path.relative_to(base).as_posix()


def digest_file(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo.lower())
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path, *, ignore_hidden: bool = False, follow_symlinks: bool = False) -> Iterable[Path]:
    for dirpath, dirs, files in os.walk(root, followlinks=follow_symlinks):
        if ignore_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
        base = Path(dirpath)
        for name in files:
            p = base / name
            rel = p.relative_to(root)
            if ignore_hidden and any(part.startswith(".") for part in rel.parts):
                continue
            if not follow_symlinks and p.is_symlink():
                continue
            if p.is_file():
                yield p


def read_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    if not path.exists():
        return entries
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            m = LINE_RE.match(line)
            if not m:
                raise ValueError(f"Linha inválida no manifesto {path}:{line_no}")
            entries[m.group(2).replace("\\", "/")] = m.group(1).lower()
    return entries


def write_manifest(path: Path, entries: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for rel in sorted(entries):
            f.write(f"{entries[rel]}  {rel}\n")
    tmp.replace(path)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def load_plan(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        plan = json.load(f)
    if not isinstance(plan, dict):
        raise ValueError("Plano JSON deve conter um objeto.")
    if not (plan.get("destination") or plan.get("destino")):
        raise ValueError("Plano deve informar 'destination' ou 'destino'.")
    sources = plan.get("sources") or plan.get("pastas") or plan.get("folders")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Plano deve informar lista 'sources', 'pastas' ou 'folders'.")
    return plan


def normalize_sources(plan: dict[str, Any]) -> list[dict[str, str]]:
    raw = plan.get("sources") or plan.get("pastas") or plan.get("folders") or []
    out: list[dict[str, str]] = []
    used: set[str] = set()
    for idx, item in enumerate(raw, 1):
        if isinstance(item, str):
            path = item
            name = Path(item).name or f"origem_{idx}"
        elif isinstance(item, dict):
            path = item.get("path") or item.get("raiz") or item.get("source")
            name = item.get("name") or item.get("nome") or (Path(path).name if path else f"origem_{idx}")
        else:
            raise ValueError(f"Origem inválida na posição {idx}.")
        if not path:
            raise ValueError(f"Origem sem caminho na posição {idx}.")
        key = safe_name(str(name))
        if key.casefold() == "thor-backup":
            raise ValueError("Nome de origem reservado: thor-backup.")
        if key.casefold() in used:
            raise ValueError(f"Nome de origem duplicado após normalização: {key}")
        used.add(key.casefold())
        out.append({"name": key, "path": str(path)})
    return out


def plan_name(plan: dict[str, Any], config_path: Path) -> str:
    return safe_name(str(plan.get("name") or plan.get("nome") or config_path.stem))


def destination(plan: dict[str, Any]) -> Path:
    return Path(plan.get("destination") or plan.get("destino")).resolve()


def options(plan: dict[str, Any]) -> dict[str, Any]:
    opts = plan.get("options") or plan.get("opcoes") or {}
    if not isinstance(opts, dict):
        opts = {}
    return opts


def ensure_repository(dest: Path, algo: str, sources: list[dict[str, str]]) -> None:
    if any(dest.glob("manifest-*.txt")):
        raise ValueError("Destino com estrutura anterior incompatível. Escolha um novo destino; os arquivos existentes não serão convertidos.")
    manifests_dir = dest / "thor-backup" / "manifests"
    existing = {p.name.casefold(): p.name for p in manifests_dir.iterdir() if p.is_dir()} if manifests_dir.exists() else {}
    for source in sources:
        name = source["name"]
        if name.casefold() in existing and existing[name.casefold()] != name:
            raise ValueError(f"O nome da origem difere apenas em maiúsculas/minúsculas de uma origem existente: {name}")
        manifest = source_manifest_path(dest, name, algo)
        if any(p != manifest for p in manifest.parent.glob("manifest-*.txt")):
            raise ValueError(f"Algoritmo diferente do manifesto existente para {name}.")
    for sub in (
        "configs",
        "manifests",
        "historico",
        "checkpoints",
        "relatorios",
        "logs",
        "versoes",
    ):
        (dest / "thor-backup" / sub).mkdir(parents=True, exist_ok=True)
    for source in sources:
        (dest / source["name"]).mkdir(parents=True, exist_ok=True)
        manifest = source_manifest_path(dest, source["name"], algo)
        if not manifest.exists():
            write_manifest(manifest, {})


def source_manifest_path(dest: Path, source_name: str, algo: str) -> Path:
    return dest / "thor-backup" / "manifests" / source_name / f"manifest-{algo}.txt"


def read_source_manifests(dest: Path, algo: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for manifest in sorted((dest / "thor-backup" / "manifests").glob(f"*/manifest-{algo}.txt")):
        name = manifest.parent.name
        for rel, digest in read_manifest(manifest).items():
            if Path(rel).is_absolute() or ".." in Path(rel).parts or ":" in rel:
                raise ValueError(f"Caminho inválido no manifesto {manifest}: {rel}")
            entries[f"{name}/{rel}"] = digest
    return entries


def write_source_manifests(base: Path, entries: dict[str, str], algo: str, names: Iterable[str]) -> None:
    grouped: dict[str, dict[str, str]] = {name: {} for name in names}
    for path, digest in entries.items():
        name, rel = path.split("/", 1)
        grouped.setdefault(name, {})[rel] = digest
    for name, manifest_entries in grouped.items():
        write_manifest(base / name / f"manifest-{algo}.txt", manifest_entries)


def validate_source_paths(dest: Path, sources: list[dict[str, str]]) -> None:
    for source in sources:
        root = Path(source["path"]).resolve()
        if dest.is_relative_to(root) or root.is_relative_to(dest):
            raise ValueError(f"Origem e destino não podem se sobrepor: {root}")
        target = dest / source["name"]
        if target.is_symlink() or not target.resolve().is_relative_to(dest):
            raise ValueError(f"Pasta de destino da origem inválida: {target}")


def append_premis(log_path: Path, event_type: str, obj_id: str, detail: str, outcome: str, agent: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    evt = {
        "eventIdentifier": str(uuid.uuid4()),
        "eventType": event_type,
        "eventDateTime": utc_now(),
        "eventDetail": detail,
        "eventOutcome": outcome,
        "linkingObjectIdentifier": obj_id,
        "linkingAgentName": agent,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def backup_report_summary(rows: list[dict[str, Any]], elapsed: float) -> list[str]:
    counts = {status: sum(row.get("status") == status for row in rows) for status in ("new", "changed", "same", "removed", "failed")}
    copied = counts["new"] + counts["changed"]
    return [
        f"Total de arquivos no relatório: {len(rows)}",
        f"Arquivos novos copiados: {counts['new']}",
        f"Arquivos alterados copiados: {counts['changed']}",
        f"Cópias com hash conferido: {copied}",
        f"Arquivos iguais ao manifesto (sem nova cópia): {counts['same']}",
        f"Arquivos ausentes na origem e preservados no destino: {counts['removed']}",
        f"Arquivos com falha: {counts['failed']}",
        f"Tempo total de execução: {elapsed:.2f}s",
    ]


def write_backup_report(
    path: Path, rows: list[dict[str, Any]], *, name: str, execution: str,
    config: Path, dest: Path, algo: str, sources: list[dict[str, str]],
    elapsed: float, resumed: bool = False,
) -> None:
    lines = [
        "=== Backup preservacional ===",
        f"Backup    : {name}",
        f"Execução  : {execution}",
        f"Plano     : {config}",
        f"Destino   : {dest}",
        f"Algoritmo : {algo}",
        "Resultado : CONCLUÍDO",
        f"Retomada de checkpoint: {'sim' if resumed else 'não'}",
        "", "-- Origens e manifestos --",
    ]
    for source in sources:
        lines.extend([
            f"Origem: {source['name']}",
            f"  Pasta de origem: {source['path']}",
            f"  Pasta no destino: {dest / source['name']}",
            f"  Manifesto: {source_manifest_path(dest, source['name'], algo)}",
        ])
    lines.extend(["", "-- Contagens da execução --", *backup_report_summary(rows, elapsed)])
    for status, title in (
        ("new", "Arquivos novos copiados"),
        ("changed", "Arquivos alterados copiados"),
        ("same", "Arquivos iguais ao manifesto"),
        ("removed", "Arquivos ausentes na origem e preservados no destino"),
        ("failed", "Arquivos com falha"),
    ):
        items = sorted((row for row in rows if row.get("status") == status), key=lambda row: row["path"])
        lines.extend(["", f"-- {title} ({len(items)}) --"])
        if not items:
            lines.append("Nenhum")
        for row in items:
            lines.append(str(row["path"]))
            for key, label in (
                ("source", "Origem"), ("destination", "Destino"),
                ("digest_before", "Hash anterior"), ("digest_after", "Hash registrado"),
                ("detail", "Detalhe"),
            ):
                if row.get(key):
                    lines.append(f"  {label}: {row[key]}")
    lines.extend([
        "", "-- Critérios de leitura --",
        "Os caminhos dos arquivos são relativos à raiz do destino e incluem o nome da origem.",
        "Novos e alterados: o hash da cópia foi conferido contra o hash da origem.",
        "Iguais: o hash da origem coincide com o manifesto; o conteúdo no destino não foi verificado novamente.",
        "Ausentes na origem: os arquivos e seus registros no manifesto foram mantidos no destino.",
        "As contagens descrevem esta execução; em uma retomada, cópias já persistidas podem aparecer como iguais.",
        "", "=== Resumo final do backup ===", *backup_report_summary(rows, elapsed),
        f"Relatório completo: {path}",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(path)
