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
replicate_storage.py — Replica arquivos para múltiplos destinos e valida com manifesto BagIt.
"""
import argparse, subprocess, sys
from pathlib import Path
from pd_common import iter_files, relpath, safe_copy, try_import_tqdm, add_common_args, load_config


MANIFEST_NAME = "manifest-sha256.txt"


def run_script(script_path: Path, args: list[str]) -> int:
    cmd = [sys.executable, str(script_path), *args]
    proc = subprocess.run(cmd, text=True)  # noqa: S603
    return proc.returncode


def path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser(description="Replicar dados para destinos múltiplos.")
    ap.add_argument("--fonte", required=True, help="Pasta de origem.")
    ap.add_argument("--destino", required=True, action="append", help="Pasta de destino (pode repetir).")
    ap.add_argument("--verificar-hash", action="store_true", help="Compatibilidade: a verificação por manifesto é sempre executada.")
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    src = Path(args.fonte).resolve()
    if not src.exists() or not src.is_dir():
        print(f"[ERRO] Pasta de origem inválida: {src}", file=sys.stderr)
        sys.exit(2)

    dests = [Path(d).resolve() for d in args.destino]
    for d in dests:
        if path_is_relative_to(d, src):
            print(f"[ERRO] Destino não pode estar dentro da origem: {d}", file=sys.stderr)
            sys.exit(2)
        d.mkdir(parents=True, exist_ok=True)

    scripts_dir = Path(__file__).resolve().parent
    hash_script = scripts_dir / "hash_files.py"
    verify_script = scripts_dir / "verify_fixity.py"

    files = list(iter_files(src))

    for d in dests:
        manifest = d / MANIFEST_NAME
        print(f"[INFO] Gerando manifesto BagIt em: {manifest}", file=sys.stderr)
        rc = run_script(
            hash_script,
            [
                "--raiz", str(src),
                "--saida", str(manifest),
                "--algo", "sha256",
            ],
        )
        if rc != 0:
            print(f"[ERRO] Falha ao gerar manifesto para {d} (rc={rc})", file=sys.stderr)
            sys.exit(rc)

    tqdm = try_import_tqdm()
    iterator = tqdm(files, desc="Replicando") if tqdm else files

    for p in iterator:
        rel = relpath(p, src)
        for d in dests:
            target = d / rel
            safe_copy(p, target)

    for d in dests:
        manifest = d / MANIFEST_NAME
        print(f"[INFO] Verificando destino com manifesto: {manifest}", file=sys.stderr)
        rc = run_script(
            verify_script,
            [
                "--raiz", str(d),
                "--manifesto", str(manifest),
                "--algo", "sha256",
            ],
        )
        if rc != 0:
            print(f"[ERRO] Verificação de fixidez falhou em {d} (rc={rc})", file=sys.stderr)
            sys.exit(rc)

    print("Replicação concluída.")

if __name__ == "__main__":
    main()
