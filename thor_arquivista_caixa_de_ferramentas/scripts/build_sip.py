#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_sip.py — Constrói um SIP genérico (objects + metadata + manifest) opcionalmente compactado.
"""
import argparse, json, datetime, shutil, zipfile
from pathlib import Path
from pd_common import sha256_file, iter_files, relpath, ensure_dir, add_common_args, load_config, iso_now, safe_copy

def write_manifest_sha256(root: Path, target: Path):
    with target.open("w", encoding="utf-8") as f:
        for p in iter_files(root):
            if p.is_file():
                h = sha256_file(p)
                rel = relpath(p, root)
                f.write(f"{h}  {rel}\n")

def main():
    ap = argparse.ArgumentParser(description="Construir SIP simples (OAIS)")
    ap.add_argument("--fonte", required=True, help="Pasta de origem dos objetos.")
    ap.add_argument("--saida", required=True, help="Diretório de saída para o SIP.")
    ap.add_argument("--sip-id", required=True, help="Identificador do SIP (nome de pasta/arquivo).")
    ap.add_argument("--zip", dest="zip_out", action="store_true", help="Compactar o SIP em ZIP.")
    ap.add_argument("--no-zip", dest="zip_out", action="store_false", help="Não compactar (padrão).")
    ap.set_defaults(zip_out=False)
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    src = Path(args.fonte).resolve()
    out_root = Path(args.saida).resolve()
    sip_dir = out_root / args.sip_id
    obj_dir = sip_dir / "objects"
    meta_dir = sip_dir / "metadata"
    ensure_dir(obj_dir); ensure_dir(meta_dir)

    # Copiar objetos
    for p in iter_files(src):
        rel = relpath(p, src)
        safe_copy(p, obj_dir / rel)

    # metadata.json mínimo
    metadata = {
        "sip_id": args.sip_id,
        "created_at": iso_now(),
        "source_path": str(src),
        "object_count": sum(1 for _ in iter_files(obj_dir))
    }
    (meta_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    # manifest-sha256.txt
    write_manifest_sha256(obj_dir, sip_dir / "manifest-sha256.txt")

    print(f"SIP criado em: {sip_dir}")

    if args.zip_out:
        zip_path = out_root / f"{args.sip_id}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in sip_dir.rglob("*"):
                z.write(p, p.relative_to(out_root))
        print(f"ZIP gerado: {zip_path}")

if __name__ == "__main__":
    main()
