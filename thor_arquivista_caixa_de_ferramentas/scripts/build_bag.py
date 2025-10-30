#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_bag.py — Cria um pacote BagIt mínimo (v0.97) com manifest-sha256.txt.
"""
import argparse, datetime
from pathlib import Path
from pd_common import sha256_file, iter_files, relpath, ensure_dir, add_common_args, load_config, iso_now, write_json, safe_copy

def payload_oxum(root: Path) -> str:
    total_bytes = 0
    total_files = 0
    for p in iter_files(root):
        st = p.stat()
        total_bytes += st.st_size
        total_files += 1
    return f"{total_bytes}.{total_files}"

def main():
    ap = argparse.ArgumentParser(description="Criar pacote BagIt (mínimo)")
    ap.add_argument("--fonte", required=True, help="Pasta de origem dos objetos (payload).")
    ap.add_argument("--destino", required=True, help="Pasta de saída do Bag.")
    ap.add_argument("--bag-name", required=True, help="Nome do diretório do bag a ser criado.")
    ap.add_argument("--org", default="APESP", help="Source-Organization (bag-info.txt).")
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    src = Path(args.fonte).resolve()
    out_root = Path(args.destino).resolve()
    bag_dir = out_root / args.bag_name
    data_dir = bag_dir / "data"
    ensure_dir(data_dir)

    # Copia payload
    for p in iter_files(src):
        rel = relpath(p, src)
        dst = data_dir / rel
        safe_copy(p, dst)

    # Manifest
    manifest = bag_dir / "manifest-sha256.txt"
    with manifest.open("w", encoding="utf-8") as f:
        for p in iter_files(data_dir):
            h = sha256_file(p)
            rel = relpath(p, bag_dir)  # manifest usa caminhos relativos ao bag root
            f.write(f"{h}  {rel}\n")

    # bagit.txt
    (bag_dir / "bagit.txt").write_text(
        "BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n",
        encoding="utf-8"
    )

    # bag-info.txt
    (bag_dir / "bag-info.txt").write_text(
        f"Source-Organization: {args.org}\n"
        f"Bagging-Date: {datetime.date.today().isoformat()}\n"
        f"Payload-Oxum: {payload_oxum(data_dir)}\n"
        f"Bag-Software-Agent: build_bag.py\n",
        encoding="utf-8"
    )

    print(f"Bag criado em: {bag_dir}")

if __name__ == "__main__":
    main()
