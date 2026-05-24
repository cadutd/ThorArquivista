from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

SEED_NAMESPACE = uuid.UUID("0c931f19-b2c2-481b-9b17-c3a1911c0a81")
ACTIONS = ("CRIAR", "EDITAR", "CONSULTAR", "EXCLUIR")


@dataclass(frozen=True)
class FuncaoSeed:
    modulo: str
    funcao: str
    nome: str


@dataclass(frozen=True)
class PerfilSeed:
    codigo: str
    nome: str
    descricao: str


FUNCOES = [
    FuncaoSeed("painel", "dashboard", "Dashboard"),
    FuncaoSeed("admissao", "admissao", "Admissão de acervos"),
    FuncaoSeed("gestao-acervos", "unidades", "Unidades de acondicionamento"),
    FuncaoSeed("gestao-acervos", "descricao-arquivistica", "Descrição arquivística"),
    FuncaoSeed("gestao-acervos", "entidades-produtoras", "Entidades produtoras"),
    FuncaoSeed("gestao-acervos", "enderecamento", "Endereçamento de armazenamento"),
    FuncaoSeed("gestao-acervos", "instrumentos-pesquisa", "Instrumentos de pesquisa"),
    FuncaoSeed("gestao-acervos", "modelos-ficha-espelho", "Modelos de ficha espelho"),
    FuncaoSeed("pesquisa", "pesquisa-descricao-arquivistica", "Pesquisa de descrição arquivística"),
    FuncaoSeed("pesquisa", "pesquisa-instrumentos-pesquisa", "Pesquisa de instrumentos de pesquisa"),
    FuncaoSeed("preservacao-digital", "midias", "Mídias de armazenamento"),
    FuncaoSeed("preservacao-digital", "eventos-preservacao", "Eventos de preservação"),
    FuncaoSeed("administracao", "admin", "Administração geral"),
    FuncaoSeed("administracao", "instituicao-arquivo", "Instituição de arquivo"),
    FuncaoSeed("administracao", "usuarios", "Usuários"),
    FuncaoSeed("administracao", "perfis", "Perfis"),
    FuncaoSeed("administracao", "permissoes", "Permissões"),
    FuncaoSeed("preservacao-digital", "aips", "AIPs"),
]

PERFIS = [
    PerfilSeed("ADMIN", "Administrador", "Acesso administrativo completo a todas as funções."),
    PerfilSeed("ARQUIVISTA", "Arquivista", "Opera funções arquivísticas e de preservação sem administrar segurança."),
    PerfilSeed("ADMISSAO", "Admissão", "Opera processos de admissão de acervos e consulta dados relacionados."),
    PerfilSeed("GESTOR_ARMAZENAMENTO", "Gestor de Armazenamento", "Opera endereçamento, mídias e rotinas de armazenamento."),
    PerfilSeed("CONSULTA", "Consulta", "Acesso somente leitura para pesquisa e acompanhamento."),
]


def deterministic_id(kind: str, value: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, f"{kind}:{value}")


def permission_code(funcao: str, acao: str) -> str:
    return f"{funcao}.{acao.lower()}"


def permission_name(nome_funcao: str, acao: str) -> str:
    labels = {
        "CRIAR": "Criar",
        "EDITAR": "Editar",
        "CONSULTAR": "Consultar",
        "EXCLUIR": "Excluir",
    }
    return f"{labels[acao]} {nome_funcao}"


def seed_permissions(db: Session) -> tuple[int, int]:
    created = 0
    updated = 0
    for funcao in FUNCOES:
        for acao in ACTIONS:
            codigo = permission_code(funcao.funcao, acao)
            result = db.execute(
                text(
                    """
                    INSERT INTO permissoes (
                        id, codigo, nome, descricao, modulo, funcao, acao, ativo
                    )
                    VALUES (
                        :id, :codigo, :nome, :descricao, :modulo, :funcao, :acao, TRUE
                    )
                    ON CONFLICT (codigo) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        descricao = EXCLUDED.descricao,
                        modulo = EXCLUDED.modulo,
                        funcao = EXCLUDED.funcao,
                        acao = EXCLUDED.acao,
                        ativo = TRUE,
                        atualizado_em = now()
                    RETURNING (xmax = 0) AS inserted
                    """
                ),
                {
                    "id": deterministic_id("permissao", codigo),
                    "codigo": codigo,
                    "nome": permission_name(funcao.nome, acao),
                    "descricao": f"Permite {acao.lower()} registros ou operações da função {funcao.nome}.",
                    "modulo": funcao.modulo,
                    "funcao": funcao.funcao,
                    "acao": acao,
                },
            )
            if result.scalar():
                created += 1
            else:
                updated += 1
    return created, updated


def allowed_actions(profile_code: str, funcao: str) -> set[str]:
    admin_functions = {"admin", "instituicao-arquivo", "usuarios", "perfis", "permissoes"}
    archival_functions = {
        "unidades",
        "descricao-arquivistica",
        "entidades-produtoras",
        "instrumentos-pesquisa",
        "modelos-ficha-espelho",
        "eventos-preservacao",
        "aips",
    }
    admission_functions = {
        "admissao",
        "unidades",
        "descricao-arquivistica",
        "entidades-produtoras",
        "pesquisa-descricao-arquivistica",
        "pesquisa-instrumentos-pesquisa",
        "dashboard",
    }
    storage_functions = {
        "enderecamento",
        "midias",
        "eventos-preservacao",
        "unidades",
        "dashboard",
    }
    if profile_code == "ADMIN":
        return set(ACTIONS)
    if profile_code == "CONSULTA":
        return {"CONSULTAR"}
    if profile_code == "ARQUIVISTA":
        if funcao in admin_functions:
            return {"CONSULTAR"}
        if funcao in archival_functions:
            return set(ACTIONS)
        return {"CONSULTAR"}
    if profile_code == "ADMISSAO":
        if funcao == "admissao":
            return set(ACTIONS)
        if funcao in admission_functions:
            return {"CONSULTAR"}
        return set()
    if profile_code == "GESTOR_ARMAZENAMENTO":
        if funcao in {"enderecamento", "midias", "eventos-preservacao"}:
            return set(ACTIONS)
        if funcao in storage_functions:
            return {"CONSULTAR"}
        return set()
    return set()


def seed_profiles(db: Session) -> tuple[int, int, int]:
    created = 0
    updated = 0
    links = 0
    arquivista_id = deterministic_id("perfil", "ARQUIVISTA")

    db.execute(text("UPDATE usuarios SET papel = 'ARQUIVISTA' WHERE papel = 'OPERADOR'"))
    db.execute(
        text(
            """
            UPDATE usuarios u
               SET id_perfil = :arquivista_id
              FROM perfis p
             WHERE p.codigo = 'OPERADOR'
               AND u.id_perfil = p.id
            """
        ),
        {"arquivista_id": arquivista_id},
    )
    db.execute(text("DELETE FROM perfil_permissao WHERE perfil_id IN (SELECT id FROM perfis WHERE codigo = 'OPERADOR')"))
    db.execute(text("DELETE FROM perfis WHERE codigo = 'OPERADOR'"))

    for perfil in PERFIS:
        perfil_id = deterministic_id("perfil", perfil.codigo)
        result = db.execute(
            text(
                """
                INSERT INTO perfis (id, codigo, nome, descricao, ativo, sistema)
                VALUES (:id, :codigo, :nome, :descricao, TRUE, TRUE)
                ON CONFLICT (codigo) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    descricao = EXCLUDED.descricao,
                    ativo = TRUE,
                    sistema = TRUE,
                    atualizado_em = now()
                RETURNING (xmax = 0) AS inserted
                """
            ),
            {
                "id": perfil_id,
                "codigo": perfil.codigo,
                "nome": perfil.nome,
                "descricao": perfil.descricao,
            },
        )
        if result.scalar():
            created += 1
        else:
            updated += 1

        for funcao in FUNCOES:
            for acao in allowed_actions(perfil.codigo, funcao.funcao):
                permissao_id = deterministic_id("permissao", permission_code(funcao.funcao, acao))
                db.execute(
                    text(
                        """
                        INSERT INTO perfil_permissao (perfil_id, permissao_id)
                        VALUES (:perfil_id, :permissao_id)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"perfil_id": perfil_id, "permissao_id": permissao_id},
                )
                links += 1

    db.execute(
        text(
            """
            UPDATE usuarios u
               SET id_perfil = p.id
              FROM perfis p
             WHERE p.codigo = u.papel
               AND u.id_perfil IS NULL
            """
        )
    )
    return created, updated, links


def seed_perfis_permissoes() -> None:
    with SessionLocal() as db:
        permissions_created, permissions_updated = seed_permissions(db)
        profiles_created, profiles_updated, links = seed_profiles(db)
        db.commit()
        print(
            "Carga de permissões e perfis concluída: "
            f"{permissions_created} permissões criadas, "
            f"{permissions_updated} permissões atualizadas, "
            f"{profiles_created} perfis criados, "
            f"{profiles_updated} perfis atualizados, "
            f"{links} vínculos processados."
        )


if __name__ == "__main__":
    seed_perfis_permissoes()
