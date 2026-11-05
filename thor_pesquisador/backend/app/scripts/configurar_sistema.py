"""Generate private environment files and provision the first administrator."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import secrets
import sys
from types import SimpleNamespace
from urllib.parse import urlsplit


AMBIENTES = ("dev", "homolog", "prod")
SECRETS = {"DATABASE_URL", "MONGODB_URL", "REDIS_URL", "MEILISEARCH_API_KEY",
           "GOVBR_CLIENT_ID", "GOVBR_CLIENT_SECRET", "APP_SESSION_SECRET",
           "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"}


def modelo(ambiente):
    if ambiente not in AMBIENTES:
        raise ValueError("Ambiente invalido.")
    local = ambiente == "dev"
    return {
        "PUBLIC_APP_URL": "http://localhost:3000" if local else "https://SUBSTITUIR-PORTAL",
        "API_BASE_URL": "http://localhost:8000/api/v1" if local else "https://SUBSTITUIR-API/api/v1",
        "DATABASE_URL": "postgresql+psycopg://thor:thor@postgres:5432/thor_pesquisador" if local else "SUBSTITUIR",
        "MONGODB_URL": "mongodb://mongo:27017/thor_pesquisador" if local else "SUBSTITUIR",
        "MONGODB_DATABASE": "thor_pesquisador" if local else "thor_pesquisador_" + ambiente,
        "REDIS_URL": "redis://redis:6379/0" if local else "SUBSTITUIR",
        "MEILISEARCH_URL": "http://meilisearch:7700" if local else "SUBSTITUIR",
        "MEILISEARCH_API_KEY": "dev-master-key-123" if local else "SUBSTITUIR",
        "S3_ENDPOINT_URL": "http://minio:9000" if local else "SUBSTITUIR",
        "S3_BUCKET": "thor-pesquisador-imagens" if local else "SUBSTITUIR",
        "S3_REGION": "us-east-1", "S3_FORCE_PATH_STYLE": "true",
        "S3_ACCESS_KEY_ID": "thor-minio" if local else "SUBSTITUIR",
        "S3_SECRET_ACCESS_KEY": "thor-minio-dev-only" if local else "SUBSTITUIR",
        "GOVBR_CLIENT_ID": "change-me" if local else "SUBSTITUIR",
        "GOVBR_CLIENT_SECRET": "change-me" if local else "SUBSTITUIR",
    }


def _preenchido(value):
    return isinstance(value, str) and bool(value.strip()) and not any(
        marker in value.lower() for marker in ("substituir", "change-me", "example.", "exemplo"))


def _url(value, schemes, publica=False):
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme in schemes and parsed.hostname and not parsed.username and not parsed.password
        if publica:
            valid = valid and not parsed.query and not parsed.fragment
            if parsed.scheme == "https" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                valid = False
        if not valid:
            raise ValueError
        return parsed
    except ValueError:
        raise ValueError("URL invalida; confira protocolo, host e caminho.") from None


def preparar_config(ambiente, entrada):
    data = modelo(ambiente)
    if not isinstance(entrada, dict) or set(entrada) - (set(data) | {"APP_SESSION_SECRET"}):
        raise ValueError("Configuracao JSON invalida ou com chaves desconhecidas.")
    data.update(entrada)
    if any(not isinstance(v, str) or any(c in v for c in "\r\n\0") for v in data.values()):
        raise ValueError("Valores devem ser textos de uma unica linha.")
    local = ambiente == "dev"
    if not local and not all(_preenchido(v) for v in data.values()):
        raise ValueError("Substitua todos os exemplos por valores reais do ambiente.")
    schemes = {"http", "https"} if local else {"https"}
    portal = _url(data["PUBLIC_APP_URL"], schemes, publica=not local)
    api = _url(data["API_BASE_URL"], schemes, publica=not local)
    if (portal.path not in {"", "/"} or portal.query or portal.fragment or api.query or api.fragment
            or api.path.rstrip("/") != "/api/v1"):
        raise ValueError("Portal deve ser uma origem; API deve terminar em /api/v1.")
    for key in ("DATABASE_URL", "MONGODB_URL", "REDIS_URL"):
        try:
            parsed = urlsplit(data[key])
        except ValueError:
            raise ValueError("URL de dependencia invalida: " + key) from None
        schemes_allowed = {"DATABASE_URL": {"postgresql+psycopg"},
                           "MONGODB_URL": {"mongodb", "mongodb+srv"}, "REDIS_URL": {"redis", "rediss"}}
        if parsed.scheme not in schemes_allowed[key] or not parsed.netloc:
            raise ValueError("URL de dependencia invalida: " + key)
        if not local and key in {"DATABASE_URL", "MONGODB_URL"} and not (parsed.username and parsed.password):
            raise ValueError("Configure autenticacao da dependencia: " + key)
    for key in ("MEILISEARCH_URL", "S3_ENDPOINT_URL"):
        _url(data[key], {"http", "https"})
    if data["S3_FORCE_PATH_STYLE"] not in {"true", "false"}:
        raise ValueError("S3_FORCE_PATH_STYLE deve ser true ou false.")
    session_secret = data.pop("APP_SESSION_SECRET", None) or secrets.token_urlsafe(48)
    if len(session_secret) < 32 or not _preenchido(session_secret):
        raise ValueError("Segredo de sessao deve ser aleatorio e ter pelo menos 32 caracteres.")
    api_base = data.pop("API_BASE_URL").rstrip("/")
    authority = "https://sso.acesso.gov.br" if ambiente == "prod" else "https://sso.staging.acesso.gov.br"
    data.update(APP_ENV=ambiente, PUBLIC_APP_URL=data["PUBLIC_APP_URL"].rstrip("/"),
                CORS_ORIGINS=json.dumps([data["PUBLIC_APP_URL"].rstrip("/")]),
                GOVBR_REDIRECT_URI=api_base + "/auth/govbr/callback",
                GOVBR_AUTHORIZE_URL=authority + "/authorize", GOVBR_TOKEN_URL=authority + "/token",
                GOVBR_JWKS_URL=authority + "/jwk", GOVBR_DEV_LOGIN=str(local).lower(),
                DEV_ADMIN_ENABLED=str(local).lower(), AUTH_DISABLED_FOR_TESTS="false",
                SESSION_COOKIE_SECURE=str(not local or api.scheme == "https").lower(),
                APP_SESSION_SECRET=session_secret)
    return data, api_base


def gerar_config(ambiente, entrada, destino):
    data, api_base = preparar_config(ambiente, entrada)
    target = Path(destino)
    # A fresh directory prevents overwriting an existing deployment or rotating sessions.
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    files = {"config.env": {k: v for k, v in data.items() if k not in SECRETS},
             "secrets.env": {k: v for k, v in data.items() if k in SECRETS}}
    if ambiente == "dev":
        files[".env"] = data
    for name, values in files.items():
        with open(target / name, "x", encoding="utf-8", opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
            for key, value in sorted(values.items()):
                if name == ".env":
                    value = json.dumps(value, ensure_ascii=False).replace("$", "$$")
                stream.write(key + "=" + value + "\n")
    with open(target / "frontend.env", "x", encoding="utf-8", opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
        stream.write("NEXT_PUBLIC_API_BASE_URL=" + api_base + "\n")
    return {"ambiente": ambiente, "arquivos": list(files) + ["frontend.env"]}


def validar_ambiente(config, ambiente, local=False):
    if ambiente not in AMBIENTES or config.app_env != ambiente:
        raise ValueError("Ambiente solicitado difere de APP_ENV; nenhuma alteracao realizada.")
    # Revalidate even when a caller supplies a previously constructed Settings object.
    type(config).model_validate(config.model_dump())
    if ambiente != "dev":
        authority = "https://sso.acesso.gov.br" if ambiente == "prod" else "https://sso.staging.acesso.gov.br"
        if any(getattr(config, key) != authority + suffix for key, suffix in (
                ("govbr_authorize_url", "/authorize"), ("govbr_token_url", "/token"), ("govbr_jwks_url", "/jwk"))):
            raise ValueError("Endpoints gov.br nao correspondem ao ambiente solicitado.")
    if local and (ambiente != "dev" or not config.govbr_dev_login or not config.dev_admin_enabled):
        raise ValueError("Administrador local exige dev e os dois atalhos locais habilitados.")


def criar_administrador(db, config, ambiente, dados, operador, confirmar=False, local=False):
    from sqlalchemy import func, or_, select, text
    from alembic.script import ScriptDirectory
    from app.models import Usuario, AcessoInstrumento, Papel
    from app.schemas.usuario import UsuarioIn
    from app.services.cpf import normalizar_cpf
    from app.services.permissao_service import bloquear_administracao, ha_administrador
    from app.services.auditoria_service import registrar

    validar_ambiente(config, ambiente, local)
    if not confirmar or not isinstance(operador, str) or not 3 <= len(operador.strip()) <= 180 or any(
            ord(c) < 32 or ord(c) == 127 for c in operador):
        raise ValueError("Informe operador e --confirmar para autorizar o bootstrap.")
    if local:
        if dados:
            raise ValueError("Nao combine --local com dados de uma pessoa.")
        payload = dict(nome="Usuario Desenvolvimento", username="desenvolvimento", cpf="00000000000", email="dev@example.local")
    else:
        payload = UsuarioIn.model_validate(dados).model_dump()
        if not payload["ativo"]:
            raise ValueError("Administrador inicial deve estar ativo.")
    try:
        expected = ScriptDirectory(str(Path(__file__).resolve().parents[2] / "alembic")).get_current_head()
        if db.scalar(text("SELECT version_num FROM alembic_version")) != expected:
            raise ValueError("Execute as migrations ate head antes do bootstrap.")
        bloquear_administracao(db)
        profile = db.get(Papel, "ADMIN")
        if not profile or not profile.ativo or "*" not in profile.permissoes:
            raise ValueError("Perfil ADMIN ausente, inativo ou alterado; revise as migrations e permissoes.")
        users = list(db.scalars(select(Usuario).where(or_(
            Usuario.cpf == payload["cpf"], func.lower(Usuario.username) == payload["username"],
            Usuario.govbr_sub == payload["cpf"])).with_for_update()))
        if len(users) > 1:
            raise ValueError("CPF e username pertencem a contas diferentes; revise os cadastros.")
        user = users[0] if users else None
        if user:
            if user.cpf != payload["cpf"] or user.username != payload["username"]:
                raise ValueError("CPF ou username ja utilizado por outra identidade.")
            if not user.ativo or user.excluido_em:
                raise ValueError("Conta inativa ou excluida; o bootstrap nao reativa usuarios.")
            if user.govbr_sub and user.govbr_sub != payload["cpf"]:
                raise ValueError("Vinculo gov.br inconsistente; nenhuma alteracao realizada.")
            if local and user.govbr_sub != "00000000000":
                raise ValueError("Conta reservada local inconsistente; revise o cadastro.")
            if not local and user.govbr_sub:
                normalizar_cpf(user.govbr_sub)
            grant = db.scalar(select(AcessoInstrumento.id).where(AcessoInstrumento.usuario_id == user.id,
                AcessoInstrumento.papel == "ADMIN", AcessoInstrumento.instrumento_id.is_(None)))
            if grant:
                result = {"ambiente": ambiente, "status": "ja_configurado", "usuario_id": str(user.id)}
                db.rollback()
                return result
        if ha_administrador(db):
            raise ValueError("Ja existe administrador ativo; use o CRUD de concessoes para novos acessos.")
        if db.scalar(select(Usuario.id).where(func.lower(Usuario.email) == payload["email"].lower(),
                                              Usuario.id != user.id if user else True).limit(1)):
            raise ValueError("Email pertence a outra conta; revise a identidade antes do bootstrap.")
        created = user is None
        if not user:
            user = Usuario(**payload)
            if local:
                user.govbr_sub = "00000000000"
            db.add(user)
            db.flush()
        db.add(AcessoInstrumento(usuario_id=user.id, papel="ADMIN", instrumento_id=None, origem="MANUAL"))
        registrar(db, "CONFIGURACAO_INICIAL_ADMIN", "usuario", user.id,
                  usuario=SimpleNamespace(id=None, nome="Bootstrap: " + operador.strip()),
                  detalhe={"papel": "ADMIN", "escopo": "GLOBAL", "resultado": "CRIADO" if created else "ASSOCIADO"})
        result = {"ambiente": ambiente, "status": "configurado", "usuario_id": str(user.id), "usuario_criado": created}
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def _ler_json(arquivo):
    if arquivo == "-":
        raw = sys.stdin.read(65537)
    else:
        with Path(arquivo).open(encoding="utf-8") as stream:
            raw = stream.read(65537)
    if len(raw.encode("utf-8")) > 65536:
        raise ValueError("Arquivo JSON excede 64 KiB.")
    return json.loads(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="comando", required=True)
    template = commands.add_parser("modelo", help="Imprime somente exemplos, nunca credenciais do ambiente.")
    template.add_argument("--ambiente", choices=AMBIENTES, required=True)
    generate = commands.add_parser("gerar-config", help="Gera arquivos privados sem acessar bancos ou cluster.")
    generate.add_argument("--ambiente", choices=AMBIENTES, required=True)
    generate.add_argument("--entrada", help="JSON privado; use - para stdin. Obrigatorio fora de dev.")
    generate.add_argument("--destino", required=True, help="Diretorio novo e privado, preferencialmente em .local/.")
    admin = commands.add_parser("administrador", help="Cria somente o primeiro administrador, sem emitir sessao.")
    admin.add_argument("--ambiente", choices=AMBIENTES, required=True)
    admin.add_argument("--arquivo", help="JSON privado com nome, username, cpf e email; - para stdin.")
    admin.add_argument("--local", action="store_true", help="Conta reservada do login de desenvolvimento; apenas dev.")
    admin.add_argument("--operador", required=True, help="Identificacao do operador/ticket para auditoria.")
    admin.add_argument("--confirmar", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        if args.comando == "modelo":
            result = modelo(args.ambiente)
        elif args.comando == "gerar-config":
            if not args.entrada and args.ambiente != "dev":
                raise ValueError("Informe --entrada com a configuracao real do ambiente.")
            result = gerar_config(args.ambiente, _ler_json(args.entrada) if args.entrada else {}, args.destino)
        else:
            if args.local and args.arquivo:
                raise ValueError("Nao combine --local e --arquivo.")
            if args.local:
                data = None
            elif args.arquivo:
                data = _ler_json(args.arquivo)
            elif sys.stdin.isatty():
                data = {"nome": input("Nome do administrador: "), "username": input("Nome de usuario: "),
                        "email": input("Email: "), "cpf": getpass.getpass("CPF (nao sera exibido): ")}
            else:
                raise ValueError("Informe --arquivo ou execute em terminal interativo.")
            from app.core.config import settings
            from app.db.session import SessionLocal
            with SessionLocal() as db:
                result = criar_administrador(db, settings, args.ambiente, data, args.operador, args.confirmar, args.local)
    except (ValueError, OSError) as exc:
        # ValidationError and JSON parsing messages can contain personal data or secrets.
        message = str(exc) if type(exc) is ValueError else "Entrada/configuracao invalida ou arquivo indisponivel."
        parser.exit(1, message + "\n")
    except Exception:
        parser.exit(1, "Falha na configuracao; verifique conectividade, migrations e permissoes do operador.\n")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
