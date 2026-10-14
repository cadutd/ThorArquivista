"""Catalogue of operation permissions; legacy bundles are used only for migration."""

CRUD_MODULES = {
    "instrumentos": "Instrumentos",
    "campos": "Campos",
    "registros": "Registros",
    "imagens": "Imagens",
    "galerias": "Galerias",
    "usuarios": "Usuarios",
    "perfis": "Perfis",
    "acessos": "Concessoes de acesso"
}
OPERATIONS = ("consultar", "incluir", "editar", "excluir")
PERMISSIONS = [
    {"codigo": f"{code}_{action}", "nome": f"{action.capitalize()} {label}",
     "modulo": label, "funcao": action.capitalize(), "acao": action.upper()}
    for code, label in CRUD_MODULES.items() for action in OPERATIONS
]
PERMISSIONS += [
    {"codigo": f"{code}_consultar", "nome": f"Consultar {label}",
     "modulo": label, "funcao": "Consultar", "acao": "CONSULTAR"}
    for code, label in {"permissoes": "Permissoes", "pesquisa": "Pesquisa",
                        "editorial": "Editorial", "dashboard": "Dashboard"}.items()
]
PERMISSIONS += [
    {"codigo": code, "nome": label, "modulo": module, "funcao": label, "acao": action}
    for code, label, module, action in [
        ("enviar_revisao", "Enviar para revisao", "Editorial", "EDITAR"),
        ("revisar", "Aprovar e devolver", "Editorial", "EDITAR"),
        ("publicar", "Publicar", "Editorial", "EDITAR"),
        ("arquivar", "Arquivar", "Editorial", "EDITAR"),
        ("reindexar", "Reindexar", "Pesquisa", "EDITAR"),
        ("consulta_publicada", "Consultar publicacoes", "Consulta publica", "CONSULTAR"),
    ]
]
LEGACY_PERMISSIONS = {
    "consultar": [
        "instrumentos_consultar",
        "campos_consultar",
        "registros_consultar",
        "imagens_consultar",
        "galerias_consultar",
        "pesquisa_consultar",
        "editorial_consultar",
        "dashboard_consultar"
    ],
    "criar_instrumento": [
        "instrumentos_incluir"
    ],
    "gerenciar": [
        "instrumentos_editar",
        "instrumentos_excluir",
        "campos_incluir",
        "campos_editar",
        "campos_excluir"
    ],
    "editar_registro": [
        "registros_incluir",
        "registros_editar",
        "registros_excluir"
    ],
    "gerenciar_imagens": [
        "imagens_consultar",
        "imagens_incluir",
        "imagens_editar",
        "imagens_excluir",
        "galerias_consultar",
        "galerias_incluir",
        "galerias_editar",
        "galerias_excluir"
    ]
}


def expand_legacy(permissions):
    return sorted({code for old in permissions for code in LEGACY_PERMISSIONS.get(old, [old])})
