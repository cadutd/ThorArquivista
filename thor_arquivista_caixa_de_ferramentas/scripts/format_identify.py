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
format_identify.py — Identifica formato via Siegfried (sf) se disponível; fallback para mimetypes/python-magic.
Saída: JSON por arquivo (em JSONL se --saida for arquivo), ou impressão no stdout.
"""
import argparse, json, shutil, mimetypes
from pathlib import Path
from pd_common import iter_files, relpath, add_common_args, load_config

def identify_with_sf(path: Path):
    import subprocess, json
    p = subprocess.run(["sf", "-json", "-hash", "sha256", str(path)], capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.strip():
        data = json.loads(p.stdout)
        # Siegfried retorna um objeto com "files" lista
        if isinstance(data, dict) and "files" in data and data["files"]:
            f0 = data["files"][0]
            res = {
                "path": str(path),
                "sha256": f0.get("hash",""),
                "mime": f0.get("mime",""),
                "id": f0.get("id",""),
                "format": f0.get("format",""),
                "basis": f0.get("basis",""),
            }
            return res
    return None

def identify_basic(path: Path):
    mime, _ = mimetypes.guess_type(str(path))
    return {
        "path": str(path),
        "sha256": None,
        "mime": mime or "application/octet-stream",
        "id": None,
        "format": None,
        "basis": "mimetypes"
    }

def main():
    ap = argparse.ArgumentParser(description="Identificar formatos de arquivos.")
    ap.add_argument("--raiz", required=True, help="Pasta a varrer.")
    ap.add_argument("--saida", help="Arquivo JSONL de saída. Se omitido, imprime.")
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = Path(args.raiz).resolve()
    use_sf = shutil.which("sf") is not None

    out_f = Path(args.saida).open("w", encoding="utf-8") if args.saida else None
    try:
        for p in iter_files(root):
            rec = None
            if use_sf:
                rec = identify_with_sf(p)
            if not rec:
                rec = identify_basic(p)
            rec["relpath"] = relpath(p, root)
            line = json.dumps(rec, ensure_ascii=False)
            if out_f:
                out_f.write(line + "\n")
            else:
                print(line)
    finally:
        if out_f:
            out_f.close()

if __name__ == "__main__":
    main()
