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
replicate_storage.py — Replica um conjunto de arquivos para múltiplos destinos com verificação opcional de hash.
"""
import argparse, sys
from pathlib import Path
from pd_common import iter_files, relpath, safe_copy, sha256_file, try_import_tqdm, add_common_args, load_config

def main():
    ap = argparse.ArgumentParser(description="Replicar dados para destinos múltiplos.")
    ap.add_argument("--fonte", required=True, help="Pasta de origem.")
    ap.add_argument("--destino", required=True, action="append", help="Pasta de destino (pode repetir).")
    ap.add_argument("--verificar-hash", action="store_true", help="Após copiar, recalcular sha256 e comparar.")
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    src = Path(args.fonte).resolve()
    dests = [Path(d).resolve() for d in args.destino]
    for d in dests:
        d.mkdir(parents=True, exist_ok=True)

    tqdm = try_import_tqdm()
    files = list(iter_files(src))
    iterator = tqdm(files, desc="Replicando") if tqdm else files

    for p in iterator:
        rel = relpath(p, src)
        for d in dests:
            target = d / rel
            safe_copy(p, target)
            if args.verificar_hash:
                h1 = sha256_file(p)
                h2 = sha256_file(target)
                if h1 != h2:
                    print(f"[ERRO HASH] {rel} em {d}", file=sys.stderr)
                    sys.exit(2)
    print("Replicação concluída.")

if __name__ == "__main__":
    main()
