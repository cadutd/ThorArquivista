# core/scripts_map.py
from __future__ import annotations
from typing import Callable, Dict, Any, Tuple
from core.config import AppConfig

# O builder recebe (params, cfg) e retorna a lista de argumentos CLI
ArgsBuilder = Callable[[Dict[str, Any], AppConfig], list[str]]

# Tipo do mapa: job_type -> (script_name, args_builder)
ScriptsMap = Dict[str, Tuple[str, ArgsBuilder]]

def get_scripts_map() -> ScriptsMap:
    """
    Retorna o mapeamento de jobs para scripts e seus builders de argumentos.
    Ajuste/estenda aqui conforme novas funcionalidades forem sendo adicionadas.
    """
    return {
        "HASH_MANIFEST": (
            "hash_files.py",
            lambda p, cfg: [
                "--raiz", p["raiz"],
                "--saida", p["saida"],
                "--algo", p.get("algo", "sha256"),
                *(["--progress"] if p.get("progress") else []),
                *(["--ignore-hidden"] if p.get("ignore_hidden") else []),
            ]
        ),
        "VERIFY_FIXITY": (
            "verify_fixity.py",
            lambda p, cfg: [
                "--raiz", p["raiz"],
                "--manifesto", p["manifesto"],
                *(["--report-extras"] if p.get("report_extras") else []),
                *(["--progress"] if p.get("progress") else []),
            ]
        ),        "BUILD_BAG": (
            "build_bag.py",
            lambda p, cfg: [
                "--fonte", p["fonte"],
                "--destino", p["destino"],
                "--bag-name", p["bag_name"],
                "--org", p.get("org", "APESP"),
            ],
        ),
        "BUILD_SIP": (
            "build_sip.py",
            lambda p, cfg: [
                "--fonte", p["fonte"],
                "--saida", p["saida"],
                "--sip-id", p["sip_id"],
            ] + (["--zip"] if p.get("zip_out") else []),
        ),
        "FORMAT_IDENTIFY": (
            "format_identify.py",
            lambda p, cfg: ["--raiz", p["raiz"], "--saida", p["saida"]],
        ),
        "REPLICATE": (
            "replicate_storage.py",
            lambda p, cfg: ["--fonte", p["fonte"]]
            + sum([["--destino", d] for d in p.get("destinos", [])], [])
            + (["--verificar-hash"] if p.get("verificar_hash") else []),
        ),
        "PREMIS_EVENT": (
            "premis_log.py",
            # usa cfg para default de agente
            lambda p, cfg: [
                "--arquivo-log", p["arquivo_log"],
                "--tipo", p["tipo"],
                "--obj-id", p["obj_id"],
                "--detalhe", p.get("detalhe", ""),
                "--resultado", p.get("resultado", "success"),
                "--agente", p.get("agente", cfg.premis_agent or "Gerenciador"),
            ],
        ),
    }
