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
build_bag.py — Constrói pacote BagIt (v0.97) com suporte a profiles de bag-info.

Uso básico:
  python scripts/build_bag.py ./fonte ./bag

Com profile (profiles/apesp-profileBagit.json):
  python scripts/build_bag.py ./fonte ./bag_apesp \
    --profile apesp \
    --organization "APESP" \
    --source-organization "Secretaria X" \
    --contact-name "Carlos Eduardo" \
    --contact-email "carlos@example.org" \
    --description "Transferência 2025-10-30 - Série Y" \
    --profile-param transfer_id=TRF-2025-001 \
    --profile-param transfer_desc="Recolhimento série Y, Unidade Z" \
    --tagmanifest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, Tuple, List, Dict, Optional

CHUNK = 1024 * 1024


# ==========================
# Utilidades de hash/IO
# ==========================
def digest_file(path: Path, algo: str = "sha256") -> str:
    algo = algo.lower()
    try:
        h = getattr(hashlib, algo)()
    except AttributeError as e:
        raise ValueError(f"Algoritmo de hash não suportado: {algo}") from e
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_payload_files(
    src: Path,
    pattern: str,
    include_hidden: bool,
    follow_symlinks: bool,
) -> Iterable[Path]:
    for p in src.rglob(pattern):
        if p.is_dir():
            continue
        if not follow_symlinks and p.is_symlink():
            continue
        if not include_hidden and p.name.startswith("."):
            continue
        yield p


def relposix(base: Path, path: Path) -> str:
    """Caminho relativo com separador '/', como exige o padrão BagIt."""
    return path.relative_to(base).as_posix()


def ensure_empty_dir(p: Path):
    if p.exists():
        if p.is_file():
            raise RuntimeError(f"Caminho de destino existe como arquivo: {p}")
        if any(p.iterdir()):
            raise RuntimeError(f"Diretório de destino já existe e não está vazio: {p}")
    else:
        p.mkdir(parents=True, exist_ok=True)


def payload_oxum(files: Iterable[Path]) -> Tuple[int, int]:
    total_bytes = 0
    count = 0
    for f in files:
        s = f.stat()
        total_bytes += int(s.st_size)
        count += 1
    return total_bytes, count


def write_text(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# ==========================
# Profiles: carregar & renderizar
# ==========================
def _resolve_profile_path(profile: str) -> Path:
    """
    Se 'profile' for um caminho existente, usa direto.
    Caso contrário, procura em ../profiles/[profile]-profileBagit.json relativo a este script.
    """
    p = Path(profile)
    if p.exists():
        return p.resolve()
    here = Path(__file__).resolve().parent
    candidate = (here.parent / "profiles" / f"{profile}-profileBagit.json").resolve()
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"Profile não encontrado: {profile}\n"
        f"Tentativas:\n - {p}\n - {candidate}"
    )


def load_bagit_profile(profile: str) -> Dict:
    prof_path = _resolve_profile_path(profile)
    with prof_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "bag_info" not in data or not isinstance(data["bag_info"], dict):
        raise ValueError(f"Profile inválido: {prof_path} (faltando objeto 'bag_info')")
    data.setdefault("required_tags", [])
    if not isinstance(data["required_tags"], list):
        raise ValueError(f"'required_tags' deve ser lista no profile: {prof_path}")
    return data


class _Missing(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def _safe_format(template: str, ctx: dict) -> str:
    """Formata preservando placeholders não resolvidos como {chave}."""
    return str(template).format_map(_Missing(**ctx))


def render_bag_info_from_profile(profile_data: dict, ctx: dict) -> List[str]:
    """
    Recebe profile e contexto e devolve linhas 'Tag: Valor' já renderizadas.
    Mantém ordem do JSON (dicts preservam ordem em Python 3.7+).
    """
    lines = []
    for tag, val in profile_data["bag_info"].items():
        if isinstance(val, (str, int, float)):
            rendered = _safe_format(val, ctx)
            if str(rendered).strip() != "":
                lines.append(f"{tag}: {rendered}")
    return lines


def parse_profile_params(kv_list: Optional[List[str]]) -> Dict[str, str]:
    """
    Converte ["k=v", "x=y", "flag"] em dict {"k":"v", "x":"y", "flag":"true"}.
    """
    res: Dict[str, str] = {}
    for item in kv_list or []:
        if "=" in item:
            k, v = item.split("=", 1)
            res[k.strip()] = v
        else:
            res[item.strip()] = "true"
    return res


def _warn_unresolved_placeholders(lines: List[str]) -> List[str]:
    """
    Retorna lista de tags com placeholders ainda não resolvidos {algo}.
    """
    unresolved = []
    for ln in lines:
        if "{" in ln and "}" in ln:
            unresolved.append(ln)
    return unresolved


# ==========================
# Construção do Bag
# ==========================
def build_bag(
    src: Path,
    dst: Path,
    *,
    algo: str = "sha256",
    mode: str = "copy",  # copy | link | move
    include_hidden: bool = False,
    follow_symlinks: bool = False,
    pattern: str = "*",
    organization: str | None = None,
    contact_name: str | None = None,
    contact_email: str | None = None,
    external_description: str | None = None,
    source_organization: str | None = None,
    bag_software_agent: str | None = "ThorArquivista build_bag.py",
    tagmanifest: bool = False,
    profile: str | None = None,
    profile_params: dict | None = None,
) -> Path:
    src = src.resolve()
    dst = dst.resolve()

    if not src.exists() or not src.is_dir():
        raise RuntimeError(f"Pasta fonte inválida: {src}")

    ensure_empty_dir(dst)

    data_dir = dst / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1) Seleciona arquivos do payload
    files_src = list(iter_payload_files(src, pattern, include_hidden, follow_symlinks))
    if not files_src:
        raise RuntimeError("Nenhum arquivo elegível encontrado na pasta fonte.")

    # 2) Transfere para data/ conforme modo
    print(f"[1/6] Transferindo {len(files_src)} arquivo(s) (mode={mode})…")
    transferred: List[Path] = []
    for i, p in enumerate(files_src, 1):
        rel = relposix(src, p)
        dst_file = data_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        if mode == "copy":
            shutil.copy2(p, dst_file)
        elif mode == "move":
            shutil.move(str(p), str(dst_file))
        elif mode == "link":
            try:
                os.link(p, dst_file)
            except OSError:
                shutil.copy2(p, dst_file)
        else:
            raise ValueError("mode deve ser 'copy', 'move' ou 'link'.")

        if i % 50 == 0 or i == len(files_src):
            print(f"  - {i}/{len(files_src)}")
        transferred.append(dst_file)

    # 3) Calcula manifest do payload
    print("[2/6] Gerando manifest do payload…")
    manifest_path = dst / f"manifest-{algo.lower()}.txt"
    transferred_sorted = sorted(transferred, key=lambda x: relposix(data_dir, x))
    with manifest_path.open("w", encoding="utf-8", newline="\n") as mf:
        for i, f in enumerate(transferred_sorted, 1):
            dig = digest_file(f, algo=algo)
            # caminho relativo ao ROOT do bag, ex.: "data/dir/arquivo.ext"
            path_in_bag = relposix(dst, f)
            mf.write(f"{dig}  {path_in_bag}\n")
            if i % 200 == 0 or i == len(transferred_sorted):
                print(f"  - {i}/{len(transferred_sorted)}")

    # 4) bagit.txt
    print("[3/6] Escrevendo bagit.txt…")
    bagit_txt = "BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n"
    write_text(dst / "bagit.txt", bagit_txt)

    # 5) bag-info.txt via profile
    print("[4/6] Escrevendo bag-info.txt…")
    total_bytes, count = payload_oxum(transferred)

    # contexto para templates
    ctx = {
        # calculadas
        "bagging_date": date.today().isoformat(),
        "payload_oxum": f"{total_bytes}.{count}",
        "algo": algo.lower(),
        "total_bytes": total_bytes,
        "file_count": count,
        "src": str(src),
        "dst": str(dst),
        # passadas por CLI (mantém nomes simples)
        "organization": organization,
        "source_organization": source_organization,
        "contact_name": contact_name,
        "contact_email": contact_email,
        "external_description": external_description,
        "bag_software_agent": bag_software_agent,
    }
    if profile_params:
        ctx.update(profile_params)

    profile_lines: List[str] = []
    required_tags: List[str] = []

    if profile:
        prof = load_bagit_profile(profile)
        required_tags = list(prof.get("required_tags", []))
        profile_lines = render_bag_info_from_profile(prof, ctx)

        # valida tags obrigatórias: checar se foram produzidas e não vazias/placeholder
        missing_required = []
        produced_tags = {ln.split(":")[0] for ln in profile_lines if ":" in ln}
        for tag in required_tags:
            if tag not in produced_tags:
                missing_required.append(tag)

        if missing_required:
            print(
                "AVISO: as seguintes 'required_tags' do profile não foram geradas:",
                ", ".join(missing_required),
                file=sys.stderr,
            )

    # Linhas base: sempre incluímos as tags canônicas
    lines: List[str] = []
    lines.append(f"Bagging-Date: {ctx['bagging_date']}")
    lines.append(f"Payload-Oxum: {ctx['payload_oxum']}")
    if bag_software_agent:
        lines.append(f"Bag-Software-Agent: {bag_software_agent}")

    # Linhas do profile (já formatadas)
    lines.extend(profile_lines)

    # Avisar se sobraram placeholders não resolvidos
    unresolved = _warn_unresolved_placeholders(lines)
    if unresolved:
        print(
            "AVISO: alguns campos em bag-info.txt contêm placeholders não resolvidos {chave}:",
            *("\n  - " + ln for ln in unresolved),
            sep="\n",
            file=sys.stderr,
        )

    write_text(dst / "bag-info.txt", "\n".join(lines) + "\n")

    # 6) tagmanifest (opcional)
    if tagmanifest:
        print("[5/6] Gerando tagmanifest…")
        tag_paths = [
            dst / "bagit.txt",
            dst / "bag-info.txt",
            manifest_path,
        ]
        tagmanifest_path = dst / f"tagmanifest-{algo.lower()}.txt"
        with tagmanifest_path.open("w", encoding="utf-8", newline="\n") as tf:
            for p in tag_paths:
                dig = digest_file(p, algo=algo)
                tf.write(f"{dig}  {relposix(dst, p)}\n")

    print("[6/6] Bag construído em:", dst)
    return dst


# ==========================
# CLI
# ==========================
def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="Constrói um BagIt (v0.97) a partir de uma pasta fonte."
    )
    ap.add_argument("src", type=Path, help="Pasta fonte (payload)")
    ap.add_argument("dst", type=Path, help="Pasta destino (bag será criado aqui)")
    ap.add_argument("--algo", default="sha256", help="Algoritmo de hash (padrão: sha256)")
    ap.add_argument(
        "--mode",
        choices=["copy", "link", "move"],
        default="copy",
        help="Como transferir os arquivos para data/ (padrão: copy)",
    )
    ap.add_argument("--pattern", default="*", help="Glob de seleção dos arquivos do payload (padrão: *)")
    ap.add_argument("--include-hidden", action="store_true", help="Inclui arquivos ocultos")
    ap.add_argument("--follow-symlinks", action="store_true", help="Segue symlinks")
    ap.add_argument("--tagmanifest", action="store_true", help="Gera tagmanifest do(s) arquivo(s) de tag")
    # metadados básicos (podem alimentar profiles)
    ap.add_argument("--organization", default=None)
    ap.add_argument("--source-organization", default=None)
    ap.add_argument("--contact-name", default=None)
    ap.add_argument("--contact-email", default=None)
    ap.add_argument("--description", default=None, help="External-Description")
    # profiles
    ap.add_argument("--profile", default=None, help="Nome lógico (profiles/[nome]-profileBagit.json) ou caminho para JSON")
    ap.add_argument(
        "--profile-param",
        action="append",
        default=None,
        help="Parâmetro extra para o profile no formato CHAVE=VALOR (pode repetir)",
    )
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        build_bag(
            src=args.src,
            dst=args.dst,
            algo=args.algo,
            mode=args.mode,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            pattern=args.pattern,
            organization=args.organization,
            source_organization=args.source_organization,
            contact_name=args.contact_name,
            contact_email=args.contact_email,
            external_description=args.description,
            tagmanifest=args.tagmanifest,
            profile=args.profile,
            profile_params=parse_profile_params(args.profile_param),
        )
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
