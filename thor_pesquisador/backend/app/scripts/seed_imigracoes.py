"""Synthetic immigration records, opt-in publication and no overwrite of existing data."""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select

from app.core.config import settings
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.models.editorial import EditorialRegistro
from app.models.instrumento import Instrumento
from app.models.user import Usuario
from app.schemas.editorial import TransicaoIn
from app.schemas.instrumento import InstrumentoCreate
from app.schemas.instrumento_campo import InstrumentoCampoCreate
from app.schemas.registro import RegistroCreate
from app.services import editorial_service, instrumento_service, registro_service
from app.services.auditoria_service import registrar
from app.services.permissao_service import require

INSTRUMENTO_ID = uuid.UUID("639efff1-507f-5f1e-a043-7d55894b119d")
LOCK_ID = 866734126
NOME = "Registros de Imigracao (dados ficticios)"
DESCRICAO = ("MASSA_IMIGRACAO_V1: registros inteiramente ficticios para testes de pesquisa. "
             "Nomes, filiacao, viagens e datas sao sinteticos e nao comprovam fatos historicos.")
OBSERVACAO = "Dado inteiramente ficticio, gerado para testes. Nao e documento historico."
ORIGENS = (
    ("Italiana", ("Giovanni", "Rosa", "Luigi", "Lucia"), ("Rossi", "Bianchi", "Romano", "Costa"), ("Maria", "Anna", "Teresa", "Giulia")),
    ("Portuguesa", ("Manuel", "Ana", "Joaquim", "Isabel"), ("Silva", "Pereira", "Santos", "Almeida"), ("Maria", "Amelia", "Rosa", "Leonor")),
    ("Espanhola", ("Jose", "Carmen", "Miguel", "Pilar"), ("Garcia", "Lopez", "Torres", "Navarro"), ("Dolores", "Isabel", "Elena", "Ana")),
    ("Alema", ("Karl", "Anna", "Otto", "Clara"), ("Schmidt", "Muller", "Weber", "Fischer"), ("Emma", "Marta", "Greta", "Helena")),
    ("Japonesa", ("Hiroshi", "Hana", "Kenji", "Yuki"), ("Tanaka", "Sato", "Yamamoto", "Kato"), ("Aiko", "Haruko", "Fumiko", "Emiko")),
    ("Polonesa", ("Jan", "Zofia", "Piotr", "Helena"), ("Kowalski", "Nowak", "Zielinski", "Wisniewski"), ("Maria", "Anna", "Irena", "Jadwiga")),
    ("Francesa", ("Pierre", "Jeanne", "Louis", "Claire"), ("Martin", "Bernard", "Moreau", "Laurent"), ("Louise", "Marie", "Alice", "Camille")),
    ("Libanesa", ("Youssef", "Nadia", "Elias", "Leila"), ("Haddad", "Mansour", "Nassar", "Khoury"), ("Salma", "Mariam", "Lina", "Amal")),
    ("Siria", ("Khalil", "Samira", "Nabil", "Rania"), ("Aziz", "Darwish", "Salem", "Habib"), ("Amina", "Nour", "Huda", "Samar")),
    ("Ucraniana", ("Ivan", "Olena", "Petro", "Kateryna"), ("Shevchenko", "Kovalenko", "Bondarenko", "Melnyk"), ("Iryna", "Maria", "Nadia", "Sofia")),
)
PORTOS = ("Santos", "Rio de Janeiro", "Recife", "Salvador", "Belem", "Rio Grande")
NAVIOS = ("Aurora de Teste", "Horizonte de Teste", "Estrela de Teste", "Travessia de Teste", "Oceano de Teste")


def campos():
    definitions = (
        ("Nome", "nome", "TEXTO_CURTO", None, True),
        ("Nome da mae", "nome_mae", "TEXTO_CURTO", None, True),
        ("Nacionalidade", "nacionalidade", "LISTA_SIMPLES", [row[0] for row in ORIGENS], True),
        ("Data de chegada", "data_chegada", "DATA", None, True),
        ("Porto de chegada", "porto_chegada", "LISTA_SIMPLES", list(PORTOS), True),
        ("Codigo do registro", "codigo_registro", "TEXTO_CURTO", None, True),
        ("Navio", "navio", "TEXTO_CURTO", None, False),
        ("Idade na chegada", "idade_chegada", "NUMERO", None, False),
        ("Observacoes", "observacoes", "TEXTO_LONGO", None, False),
    )
    return [InstrumentoCampoCreate(nome=nome, chave=key, tipo=tipo, ordem=i,
        obrigatorio=required, opcoes=options, exibir_publico=True,
        filtro_avancado=key in {"nome", "nome_mae", "nacionalidade", "data_chegada", "porto_chegada"},
        facetavel=key in {"nacionalidade", "porto_chegada"}, ordenavel=True,
        aparece_listagem=key not in {"navio", "idade_chegada", "observacoes"})
        for i, (nome, key, tipo, options, required) in enumerate(definitions)]


def dados_registro(index):
    if not 1 <= index <= 1000:
        raise ValueError("Limites: 1 a 1000 registros.")
    nationality, names, surnames, mothers = ORIGENS[(index-1) % len(ORIGENS)]
    cycle = (index-1) // len(ORIGENS)
    return {
        "nome": names[cycle % 4] + " " + surnames[(cycle // 4) % 4],
        "nome_mae": mothers[(cycle+1) % 4] + " " + surnames[(cycle // 4+1) % 4],
        "nacionalidade": nationality,
        "data_chegada": (date(1880, 1, 1) + timedelta(days=((index-1)*137) % 19358)).isoformat(),
        "porto_chegada": PORTOS[(index-1) % len(PORTOS)],
        "codigo_registro": "IMIG-TESTE-" + str(index).zfill(4),
        "navio": NAVIOS[(index-1) % len(NAVIOS)],
        "idade_chegada": 1 + (index*7) % 75,
        "observacoes": OBSERVACAO,
    }


def publicar(db, instrumento, registro_id=None):
    if registro_id:
        row = db.scalar(select(EditorialRegistro).where(
            EditorialRegistro.instrumento_id == instrumento.id, EditorialRegistro.registro_id == registro_id))
        state, version = row.status_editorial, row.versao
    else:
        state, version = instrumento.status, instrumento.versao_editorial
    if state == "PUBLICADO":
        return False
    if state not in {"RASCUNHO", "EM_REVISAO", "APROVADO"}:
        return False
    for expected, action in (("RASCUNHO", "enviar-revisao"), ("EM_REVISAO", "aprovar"), ("APROVADO", "publicar")):
        if state != expected:
            continue
        result = editorial_service.transicionar(db, instrumento.id, action,
            TransicaoIn(operacao_id=uuid.uuid4(), versao=version,
                justificativa="Publicacao explicita de massa inteiramente ficticia de imigracao para testes."),
            registro_id=registro_id)
        state = result["status_editorial"]
    return state == "PUBLICADO"


def seed_imigracoes(db, usuario_id, quantidade=200, publicar_registros=False):
    if settings.app_env not in {"dev", "test"}:
        raise ValueError("Massa permitida somente em dev/test.")
    if settings.app_env == "dev" and not (settings.govbr_dev_login and settings.dev_admin_enabled):
        raise ValueError("Ative explicitamente o ambiente local de desenvolvimento.")
    if not 1 <= quantidade <= 1000:
        raise ValueError("Limites: 1 a 1000 registros.")
    actor = db.get(Usuario, usuario_id)
    if not actor or not actor.ativo or actor.excluido_em:
        raise ValueError("Informe um usuario cadastrado e ativo como agente.")
    db.info["usuario"] = actor
    required = ["instrumentos_incluir", "instrumentos_consultar", "campos_incluir", "registros_incluir", "registros_consultar"]
    if publicar_registros:
        required += ["enviar_revisao", "revisar", "publicar"]
    for permission in required:
        require(db, permission)
    # Services commit each business operation; a separate session-level lock spans the entire run.
    with db.get_bind().connect() as guard:
        if not guard.scalar(select(func.pg_try_advisory_lock(LOCK_ID))):
            raise ValueError("Outra geracao desta massa esta em andamento.")
        guard.commit()
        try:
            return _seed(db, actor, quantidade, publicar_registros)
        finally:
            guard.execute(select(func.pg_advisory_unlock(LOCK_ID)))
            guard.commit()


def _seed(db, actor, quantidade, publicar_registros):
    instrument = db.get(Instrumento, INSTRUMENTO_ID)
    expected = InstrumentoCreate(nome=NOME, tipo="BASE_TEMATICA", descricao=DESCRICAO, visibilidade="PUBLICO")
    if instrument:
        if any(getattr(instrument, key) != value for key, value in
               expected.model_dump(mode="json", exclude={"status"}).items()) or instrument.status == "ARQUIVADO":
            raise ValueError("Instrumento existente alterado ou arquivado; nenhum cadastro sera sobrescrito.")
    elif db.scalar(select(Instrumento.id).where(Instrumento.nome == NOME)):
        raise ValueError("Nome ja utilizado fora desta massa; nenhum cadastro sera sobrescrito.")
    definitions = campos()
    current = {field.chave: field for field in instrument.campos} if instrument else {}
    if set(current) - {field.chave for field in definitions}:
        raise ValueError("Schema existente alterado; nenhum campo sera sobrescrito.")
    for definition in definitions:
        if definition.chave in current and any(
                getattr(current[definition.chave], key) != value for key,value in definition.model_dump(mode="json").items()):
            raise ValueError("Campo existente alterado; nenhum campo sera sobrescrito.")
    missing = [field for field in definitions if field.chave not in current]
    if instrument and missing and (instrument.status != "RASCUNHO" or instrument.publicacao_id):
        raise ValueError("Schema publicado incompleto; revise manualmente antes de continuar.")
    if not instrument:
        instrument = Instrumento(id=INSTRUMENTO_ID, **expected.model_dump(mode="json"), criado_por=actor.id)
        db.add(instrument)
        db.commit()
    for field in missing:
        instrumento_service.criar_campo(db, instrument.id, field)
    db.expire_all()
    instrument = db.get(Instrumento, INSTRUMENTO_ID)
    if publicar_registros:
        publicar(db, instrument)
        if not instrument.publicacao_id:
            raise ValueError("Instrumento sem publicacao valida; registros nao foram publicados.")
    result = {"instrumento_id": str(instrument.id), "criados": 0, "existentes": 0, "publicados_nesta_execucao": 0,
              "preservados": 0, "campos_criados": len(missing)}
    collection = registros_collection()
    for index in range(1, quantidade+1):
        data = dados_registro(index)
        matches = list(collection.find({"instrumento_id": str(instrument.id), "$or": [
            {"_massa_imigracao_codigo": data["codigo_registro"]},
            {"dados.codigo_registro": data["codigo_registro"]}]}).limit(2))
        if len(matches) > 1:
            raise ValueError("Codigo duplicado nesta massa; revise os registros antes de continuar.")
        if matches:
            result["existentes"] += 1
            doc = matches[0]
        else:
            created = registro_service.criar_registro(db, instrument.id, RegistroCreate(dados=data), actor.id)
            collection.update_one({"_id": created.id}, {"$set": {"_massa_imigracao_codigo": data["codigo_registro"]}})
            doc = collection.find_one({"_id": created.id})
            result["criados"] += 1
        row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.instrumento_id == instrument.id,
            EditorialRegistro.registro_id == doc["_id"]))
        if (doc["dados"] != data or doc["status"] != "ATIVO" or doc.get("_revision", 1) != 1
                or (row and (row.versao != 1 or row.status_operacional != "ATIVO" or row.status_editorial == "ARQUIVADO"))):
            result["preservados"] += 1
            continue
        if publicar_registros:
            if not row:
                editorial_service.controle(db, instrument.id, doc["_id"], doc)
                db.commit()
            result["publicados_nesta_execucao"] += int(publicar(db, instrument, doc["_id"]))
    result["total_registros"] = collection.count_documents({"instrumento_id": str(instrument.id)})
    if result["criados"] or missing or result["publicados_nesta_execucao"]:
        registrar(db, "GERAR_MASSA_IMIGRACAO", "instrumento", instrument.id, instrument.id,
            detalhe={"quantidade": quantidade, "processados": result["criados"]})
        db.commit()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usuario-id", type=uuid.UUID, required=True)
    parser.add_argument("--quantidade", type=int, default=200)
    parser.add_argument("--publicar", action="store_true", help="Publica instrumento e registros pelo fluxo editorial.")
    args = parser.parse_args()
    with SessionLocal() as db:
        result = seed_imigracoes(db, args.usuario_id, args.quantidade, args.publicar)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
