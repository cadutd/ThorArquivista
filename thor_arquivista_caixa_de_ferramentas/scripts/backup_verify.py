#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from backup_common import append_premis, read_json, read_manifest, run_id


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verifica os manifestos por origem do backup preservacional.")
    p.add_argument("--destino", required=True, help="Pasta de destino do backup.")
    p.add_argument("--algo", help="Filtra o algoritmo; por padrão identifica os manifestos de todas as origens.")
    p.add_argument("--progress", action="store_true", help="Mostra progresso.")
    p.add_argument("--premis-log", help="Arquivo JSONL PREMIS.")
    p.add_argument("--agent", default="Thor Arquivista backup_verify.py", help="Agente PREMIS.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dest = Path(args.destino).resolve()
    if not dest.exists() or not dest.is_dir():
        print(f"[ERRO] Destino inválido: {dest}", file=sys.stderr)
        return 2
    manifests = sorted((dest / "thor-backup" / "manifests").glob("*/manifest-*.txt"))
    expected = set()
    try:
        for checkpoint in (dest / "thor-backup" / "checkpoints").glob("*.state.json"):
            state = read_json(checkpoint)
            if state.get("layout_version") == 2:
                algo = state.get("algorithm", "sha256")
                if not args.algo or args.algo.lower() == algo:
                    expected.update(dest / "thor-backup" / "manifests" / name / f"manifest-{algo}.txt" for name in state.get("manifests", {}))
    except (OSError, ValueError) as exc:
        print(f"[ERRO] Não foi possível ler os checkpoints: {exc}", file=sys.stderr)
        return 2
    if args.algo:
        manifests = [p for p in manifests if p.name == f"manifest-{args.algo.lower()}.txt"]
    if not manifests:
        print("[ERRO] Nenhum manifesto por origem encontrado no destino para o algoritmo solicitado.", file=sys.stderr)
        return 2
    verify = Path(__file__).resolve().parent / "verify_fixity.py"
    report_dir = dest / "thor-backup" / "relatorios" / f"verificacao_{run_id()}"
    report_dir.mkdir(parents=True, exist_ok=True)
    missing_manifests = expected.difference(manifests)
    for manifest in sorted(missing_manifests):
        print(f"[ERRO] Manifesto esperado não encontrado: {manifest}", file=sys.stderr)
    result = 2 if missing_manifests else 0
    for manifest in manifests:
        source_name = manifest.parent.name
        root = dest / source_name
        print(f"Verificando origem: {source_name}", flush=True)
        try:
            if root.is_symlink() or not root.resolve().is_relative_to(dest) or not root.is_dir():
                raise ValueError(f"Pasta de origem no destino inválida: {root}")
            entries = read_manifest(manifest)
            for rel in entries:
                if Path(rel).is_absolute() or ".." in Path(rel).parts or ":" in rel:
                    raise ValueError(f"Caminho inválido no manifesto: {rel}")
            report = report_dir / f"{source_name}_{manifest.stem}.txt"
            if entries:
                cmd = [sys.executable, "-B", str(verify), "--raiz", str(root), "--manifesto", str(manifest), "--report-file", str(report)]
                if args.progress:
                    cmd.append("--progress")
                rc = subprocess.call(cmd)
            else:
                extras = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
                text = f"Origem: {source_name}\nTotal no manifesto: 0\nArquivos extras: {len(extras)}\n" + "\n".join(extras)
                report.write_text(text + "\n", encoding="utf-8")
                print(text)
                rc = 0
        except (OSError, ValueError) as exc:
            print(f"[ERRO] {source_name}: {exc}", file=sys.stderr)
            rc = 2
        if args.premis_log:
            append_premis(
                Path(args.premis_log), "FIXITY_CHECK", str(manifest),
                f"Verificação da origem {source_name} concluída com exit code {rc}.",
                "success" if rc == 0 else "failure", args.agent,
            )
        result = max(result, rc)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
