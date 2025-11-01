# core/scripts_map.py
from __future__ import annotations
from typing import Callable, Dict, Any, Tuple
from core.config import AppConfig

# O builder recebe (params, cfg) e retorna a lista de argumentos CLI
ArgsBuilder = Callable[[Dict[str, Any], AppConfig], list[str]]

# Tipo do mapa: job_type -> (script_name, args_builder)
ScriptsMap = Dict[str, Tuple[str, ArgsBuilder]]

def _args_build_bag(p: Dict[str, Any], cfg: AppConfig) -> list[str]:
    """
    Constrói argv para scripts/build_bag.py a partir do payload do painel.

    Payload esperado (novo padrão):
      - src (obrigatório), dst (obrigatório)
      - algo, mode, pattern
      - include_hidden, follow_symlinks, tagmanifest (bool)
      - organization, source_organization, contact_name, contact_email, external_description
      - profile (nome lógico OU caminho)
      - profile_param (lista de 'K=V')

    Compatibilidade retro:
      - fonte -> src
      - destino -> dst
      - org -> organization
    """
    # Back-compat com chaves antigas
    src = p.get("src") or p.get("fonte")
    dst = p.get("dst") or p.get("destino")
    if not src or not dst:
        raise ValueError("BUILD_BAG: campos obrigatórios 'src'/'dst' ausentes (ou 'fonte'/'destino').")

    args: list[str] = [
        str(src),
        str(dst),
        "--algo", str(p.get("algo", "sha256")),
        "--mode", str(p.get("mode", "copy")),
        "--pattern", str(p.get("pattern", "*")),
    ]

    if p.get("include_hidden"):
        args.append("--include-hidden")
    if p.get("follow_symlinks"):
        args.append("--follow-symlinks")
    if p.get("tagmanifest"):
        args.append("--tagmanifest")

    # Metadados padrão
    organization = p.get("organization") or p.get("org")  # retrocompatibilidade
    if organization:
        args += ["--organization", str(organization)]
    if p.get("source_organization"):
        args += ["--source-organization", str(p["source_organization"])]
    if p.get("contact_name"):
        args += ["--contact-name", str(p["contact_name"])]
    if p.get("contact_email"):
        args += ["--contact-email", str(p["contact_email"])]
    if p.get("external_description"):
        args += ["--description", str(p["external_description"])]

    # Profile + múltiplos --profile-param
    if p.get("profile"):
        args += ["--profile", str(p["profile"])]
    for kv in (p.get("profile_param") or []):
        if isinstance(kv, str) and kv:
            args += ["--profile-param", kv]

    return args


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
        ),                
        "BUILD_BAG": (
            "build_bag.py",
            _args_build_bag,
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
        "DUPLICATE_FINDER": (
            "duplicate_finder.py",
            lambda p, cfg: (
                # O modo de execução é determinado pelo campo "acao"
                # suportando as mesmas operações do CLI do script.
                #
                # Campos esperados:
                #   modo: inventario | duplicatas | modelo_decisoes |
                #         script_tratamento | dashboard_duplicatas | dashboard_decisoes
                #   raiz, inventario, duplicatas, decisoes, etc.
                #
                # Exemplo de payloads:
                #   {"modo": "inventario", "raiz": "/dados", "inventario": "inventario.csv"}
                #   {"modo": "duplicatas", "inventario": "inventario.csv", "duplicatas": "duplicatas.csv"}
                #   {"modo": "script_tratamento", "decisoes": "decisoes.csv", "gerar_script_remocao": "tratar.sh", "sistema": "linux", "acao": "quarentena"}
                {
                    "inventario": [
                        "--raiz", p["raiz"],
                        "--inventario", p["inventario"],
                    ] + (["--mostrar-progresso"] if p.get("mostrar_progresso") else []),

                    "duplicatas": [
                        "--inventario", p["inventario"],
                        "--duplicatas", p["duplicatas"],
                    ],

                    "modelo_decisoes": [
                        "--from-duplicatas", p["duplicatas"],
                        "--decisoes", p["decisoes"],
                    ],

                    "script_tratamento": [
                        "--decisoes", p["decisoes"],
                        "--gerar-script-remocao", p["gerar_script_remocao"],
                        "--sistema", p.get("sistema", "linux"),
                        "--acao", p.get("acao", "quarentena"),
                        "--prefixo-quarentena", p.get("prefixo_quarentena", "quarentena"),
                    ] + (
                        ["--script-log-nome", p["script_log_nome"]] if p.get("script_log_nome") else []
                    ),

                    "dashboard_duplicatas": [
                        "--inventario", p["inventario"],
                        "--duplicatas", p["duplicatas"],
                        "--dashboard-duplicatas-csv", p["dashboard_duplicatas_csv"],
                    ] + (
                        ["--dashboard-duplicatas-xlsx", p["dashboard_duplicatas_xlsx"]]
                        if p.get("dashboard_duplicatas_xlsx") else []
                    ),

                    "dashboard_decisoes": [
                        "--inventario", p["inventario"],
                        "--decisoes", p["decisoes"],
                        "--dashboard-decisoes-csv", p["dashboard_decisoes_csv"],
                    ] + (
                        ["--dashboard-decisoes-xlsx", p["dashboard_decisoes_xlsx"]]
                        if p.get("dashboard_decisoes_xlsx") else []
                    ),
                }[p["modo"]]  # seleciona o conjunto de argumentos conforme o modo
            ),
        ),
    }
