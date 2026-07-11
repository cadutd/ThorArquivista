#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backup_common import read_manifest


def diff_manifests(source_entries: dict[str, str], destination_entries: dict[str, str]) -> dict[str, list[str]]:
    source_paths = set(source_entries)
    dest_paths = set(destination_entries)
    return {
        "new": sorted(source_paths - dest_paths),
        "changed": sorted(p for p in source_paths & dest_paths if source_entries[p] != destination_entries[p]),
        "same": sorted(p for p in source_paths & dest_paths if source_entries[p] == destination_entries[p]),
        "removed": sorted(dest_paths - source_paths),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compara manifesto de origem com manifesto do backup.")
    p.add_argument("--origem", required=True, help="Manifesto temporário/atual da origem.")
    p.add_argument("--destino", required=True, help="Manifesto atual do backup.")
    p.add_argument("--saida", help="JSON de diff a gravar.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = diff_manifests(read_manifest(Path(args.origem)), read_manifest(Path(args.destino)))
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
            Path(args.saida).write_text(text, encoding="utf-8")
        print(text)
        return 0
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
