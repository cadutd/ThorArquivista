#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pd_common.py — Utilitários comuns para scripts de preservação digital (OAIS-like)
Autor: Você (Carlos Eduardo C. Amand)
Licença: MIT
"""
from __future__ import annotations
import os, sys, json, hashlib, datetime, argparse, shutil
from pathlib import Path
from typing import Optional, Dict, Any, Iterable, Tuple

CHUNK_SIZE = 1024 * 1024  # 1 MiB

def load_config(path: Optional[str]) -> Dict[str, Any]:
    """Carrega um arquivo de configuração JSON ou YAML (se PyYAML disponível)."""
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config não encontrada: {p}")
    text = p.read_text(encoding="utf-8")
    # Tenta YAML se disponível, senão JSON
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        return json.loads(text)

def sha256_file(path: Path, chunk_size: int = CHUNK_SIZE) -> str:
    """Calcula SHA-256 do arquivo, em blocos."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def relpath(path: Path, root: Path) -> str:
    return str(path.relative_to(root).as_posix())

def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p

def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def append_jsonl(path: Path, data: Any) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def human_bytes(n: int) -> str:
    units = ["B","KiB","MiB","GiB","TiB"]
    i = 0
    x = float(n)
    while x >= 1024 and i < len(units)-1:
        x /= 1024.0
        i += 1
    return f"{x:.2f} {units[i]}"

def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def try_import_tqdm():
    try:
        from tqdm import tqdm  # type: ignore
        return tqdm
    except Exception:
        return None

def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Caminho do arquivo de configuração (YAML ou JSON).", default=None)
    parser.add_argument("--log-jsonl", help="Arquivo de log JSONL para eventos PREMIS/operacionais.", default=None)
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso.")
