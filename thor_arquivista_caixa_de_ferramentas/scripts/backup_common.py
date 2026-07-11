#!/usr/bin/env python3
from __future__ import annotations

import csv
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
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for rel in sorted(entries):
            f.write(f"{entries[rel]}  {rel}\n")


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
        if key in used:
            key = f"{key}_{idx}"
        used.add(key)
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


def ensure_repository(dest: Path, algo: str) -> None:
    (dest / "data").mkdir(parents=True, exist_ok=True)
    for sub in (
        "configs",
        "manifests/origem",
        "manifests/destino",
        "manifests/historico",
        "checkpoints",
        "relatorios",
        "logs",
        "versoes",
    ):
        (dest / "thor-backup" / sub).mkdir(parents=True, exist_ok=True)
    bagit = dest / "bagit.txt"
    if not bagit.exists():
        bagit.write_text("BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n", encoding="utf-8", newline="\n")
    bag_info = dest / "bag-info.txt"
    if not bag_info.exists():
        bag_info.write_text(
            "Bag-Software-Agent: Thor Arquivista backup_plan.py\n"
            f"Bagging-Date: {datetime.now(timezone.utc).date().isoformat()}\n",
            encoding="utf-8",
            newline="\n",
        )
    manifest = dest / f"manifest-{algo}.txt"
    if not manifest.exists():
        write_manifest(manifest, {})


def tag_files(dest: Path, algo: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for p in (dest / "bagit.txt", dest / "bag-info.txt", dest / f"manifest-{algo}.txt"):
        if p.exists():
            entries[relposix(dest, p)] = digest_file(p, algo)
    return entries


def update_tagmanifest(dest: Path, algo: str) -> None:
    write_manifest(dest / f"tagmanifest-{algo}.txt", tag_files(dest, algo))


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


def write_report_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["path", "status", "source", "destination", "digest_before", "digest_after", "detail"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in keys})
