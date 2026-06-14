from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.admissao import (
    AcordoAdmissao,
    CanalSubmissao,
    EventoAdmissao,
    ProcessoAdmissao,
    RelacaoSipAip,
    ResultadoEventoAdmissao,
    ResultadoFinalAdmissao,
    ReuniaoAdmissao,
    SessaoSubmissao,
    SipAdmissao,
    StatusAcordoAdmissao,
    StatusProcessoAdmissao,
    StatusSessaoSubmissao,
    StatusSipAdmissao,
    TipoEventoAdmissao,
    TipoIngressoAdmissao,
    TipoProcessoAdmissao,
    TipoRelacaoSipAip,
    TipoReuniaoAdmissao,
)
from app.models.entidade_produtora import EntidadeProdutora
from app.models.enums import TipoSuporte
from app.models.instituicao_arquivo import InstituicaoArquivo
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.scripts.seed_entidades_produtoras import build_seed_data, seed_entidades_produtoras
from app.scripts.seed_instituicao_arquivo_apesp import seed_instituicao_arquivo_apesp
from app.scripts.seed_test_units import seed_test_units


SEED_NAMESPACE = uuid.UUID("1dd5b7ff-5eb6-4a2e-8af6-dde19f264e11")
SEED_AUTHOR = "seed_admissao"


def seed_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, key)


@dataclass(frozen=True)
class ProcessoSeed:
    key: str
    numero: str
    titulo: str
    entidade_codigo: str
    tipo_processo: TipoProcessoAdmissao
    tipo_ingresso: TipoIngressoAdmissao
    tipo_suporte: TipoSuporte
    status: StatusProcessoAdmissao
    data_inicio: date
    data_fim_prevista: date | None
    data_encerramento: date | None
    resultado_final: ResultadoFinalAdmissao | None
    volume_estimado: str
    volume_recebido: str | None
    unidades_estimadas: int
    unidades_recebidas: int | None
    ativo: bool = True
    recorrente: bool = False

    @property
    def id(self) -> uuid.UUID:
        return seed_uuid(f"processo:{self.numero}")


PROCESSOS = [
    ProcessoSeed(
        key="preservacao-digital",
        numero="ADM-TEST-2026-001",
        titulo="Recolhimento de acervo digital de preservacao",
        entidade_codigo="TEST-EP-CENTRO-PRESERVACAO-DIGITAL",
        tipo_processo=TipoProcessoAdmissao.CONTINUO,
        tipo_ingresso=TipoIngressoAdmissao.RECOLHIMENTO,
        tipo_suporte=TipoSuporte.DIGITAL,
        status=StatusProcessoAdmissao.EM_VALIDACAO,
        data_inicio=date(2026, 1, 12),
        data_fim_prevista=date(2026, 8, 30),
        data_encerramento=None,
        resultado_final=None,
        volume_estimado="4,5 TB",
        volume_recebido="2,1 TB",
        unidades_estimadas=120,
        unidades_recebidas=48,
        recorrente=True,
    ),
    ProcessoSeed(
        key="migracao-legado",
        numero="ADM-TEST-2026-002",
        titulo="Regularizacao de base legada de sistemas administrativos",
        entidade_codigo="TEST-EP-GT-MIGRACAO-SISTEMAS",
        tipo_processo=TipoProcessoAdmissao.FECHADO,
        tipo_ingresso=TipoIngressoAdmissao.REGULARIZACAO_LEGADO,
        tipo_suporte=TipoSuporte.DIGITAL,
        status=StatusProcessoAdmissao.EM_GERACAO_AIP,
        data_inicio=date(2026, 2, 3),
        data_fim_prevista=date(2026, 6, 15),
        data_encerramento=None,
        resultado_final=None,
        volume_estimado="850 GB",
        volume_recebido="842 GB",
        unidades_estimadas=35,
        unidades_recebidas=35,
    ),
    ProcessoSeed(
        key="colecao-fotografica",
        numero="ADM-TEST-2026-003",
        titulo="Doacao de colecao fotografica com representantes digitais",
        entidade_codigo="TEST-EP-COLECAO-FOTOGRAFICA",
        tipo_processo=TipoProcessoAdmissao.FECHADO,
        tipo_ingresso=TipoIngressoAdmissao.DOACAO,
        tipo_suporte=TipoSuporte.HIBRIDO,
        status=StatusProcessoAdmissao.CONCLUIDO,
        data_inicio=date(2025, 10, 7),
        data_fim_prevista=date(2026, 1, 30),
        data_encerramento=date(2026, 1, 22),
        resultado_final=ResultadoFinalAdmissao.ADMITIDO_COM_RESSALVA,
        volume_estimado="22 caixas e 180 GB",
        volume_recebido="21 caixas e 176 GB",
        unidades_estimadas=22,
        unidades_recebidas=21,
        ativo=False,
    ),
    ProcessoSeed(
        key="data-center",
        numero="ADM-TEST-2026-004",
        titulo="Transferencia de midias removiveis do data center",
        entidade_codigo="TEST-EP-UNIDADE-DATA-CENTER",
        tipo_processo=TipoProcessoAdmissao.FECHADO,
        tipo_ingresso=TipoIngressoAdmissao.TRANSFERENCIA,
        tipo_suporte=TipoSuporte.FISICO,
        status=StatusProcessoAdmissao.PENDENTE_COMPLEMENTACAO,
        data_inicio=date(2026, 3, 18),
        data_fim_prevista=date(2026, 7, 1),
        data_encerramento=None,
        resultado_final=None,
        volume_estimado="64 fitas LTO",
        volume_recebido="58 fitas LTO",
        unidades_estimadas=64,
        unidades_recebidas=58,
    ),
]


def upsert(db: Session, model, object_id, values: dict):
    obj = db.get(model, object_id)
    created = obj is None
    if created:
        obj = model(id=object_id)
        db.add(obj)
    for field, value in values.items():
        setattr(obj, field, value)
    return obj, created


def first_unit_id(db: Session, identificador: str) -> int | None:
    return db.execute(
        select(UnidadeAcondicionamento.id).where(
            UnidadeAcondicionamento.identificador == identificador
        )
    ).scalar_one_or_none()


def seed_admissao() -> dict[str, int]:
    seed_instituicao_arquivo_apesp()
    seed_entidades_produtoras()
    seed_test_units()

    counts = {
        "processos_criados": 0,
        "processos_atualizados": 0,
        "reunioes": 0,
        "acordos": 0,
        "sessoes": 0,
        "sips": 0,
        "relacoes_sip_aip": 0,
        "eventos": 0,
    }

    with SessionLocal() as db:
        instituicao_id = db.execute(
            select(InstituicaoArquivo.id).where(InstituicaoArquivo.singleton_key.is_(True))
        ).scalar_one()
        entidades = {seed.codigo: seed.id for seed in build_seed_data()}
        unidades = {
            "TEST-DIG-001": first_unit_id(db, "TEST-DIG-001"),
            "TEST-DIG-002": first_unit_id(db, "TEST-DIG-002"),
            "TEST-FIS-001": first_unit_id(db, "TEST-FIS-001"),
        }

        for index, processo_seed in enumerate(PROCESSOS, start=1):
            processo, created = upsert(
                db,
                ProcessoAdmissao,
                processo_seed.id,
                {
                    "numero_processo": processo_seed.numero,
                    "titulo": processo_seed.titulo,
                    "descricao": (
                        "Processo de admissao criado pela massa de teste para validar "
                        "listagem, detalhe, filtros, abas operacionais e historico."
                    ),
                    "id_instituicao_arquivo": instituicao_id,
                    "id_entidade_produtora": entidades[processo_seed.entidade_codigo],
                    "nome_usuario_responsavel": f"Arquivista Teste {index}",
                    "tipo_processo_admissao": processo_seed.tipo_processo,
                    "tipo_ingresso": processo_seed.tipo_ingresso,
                    "tipo_suporte": processo_seed.tipo_suporte,
                    "data_inicio": processo_seed.data_inicio,
                    "data_fim_prevista": processo_seed.data_fim_prevista,
                    "data_encerramento": processo_seed.data_encerramento,
                    "processo_ativo": processo_seed.ativo,
                    "admissoes_recorrentes": processo_seed.recorrente,
                    "status": processo_seed.status,
                    "resultado_final": processo_seed.resultado_final,
                    "codigo_classificacao": f"TEST.ADM.{index:03d}",
                    "codigo_classificacao_descricao": "Massa de teste de admissao",
                    "restricao_acesso": "Acesso interno durante validacao",
                    "hipotese_legal_restricao": "Dados operacionais simulados",
                    "volume_estimado": processo_seed.volume_estimado,
                    "volume_recebido": processo_seed.volume_recebido,
                    "quantidade_unidades_estimadas": processo_seed.unidades_estimadas,
                    "quantidade_unidades_recebidas": processo_seed.unidades_recebidas,
                    "observacoes": "Registro idempotente gerado para demonstracao do modulo.",
                    "parecer_final": "Admissao homologada com ressalvas tecnicas."
                    if processo_seed.resultado_final
                    else None,
                    "criado_por": SEED_AUTHOR,
                    "atualizado_por": SEED_AUTHOR,
                },
            )
            counts["processos_criados" if created else "processos_atualizados"] += 1
            db.flush()

            reuniao_id = seed_uuid(f"reuniao:{processo_seed.numero}:1")
            upsert(
                db,
                ReuniaoAdmissao,
                reuniao_id,
                {
                    "id_processo_admissao": processo.id,
                    "numero_reuniao": 1,
                    "titulo": "Reuniao inicial de alinhamento",
                    "descricao": "Registro de alinhamento de escopo e responsabilidades.",
                    "tipo_reuniao": TipoReuniaoAdmissao.NEGOCIACAO_INICIAL,
                    "data_reuniao": datetime(2026, min(index + 1, 12), 10, 14, tzinfo=timezone.utc),
                    "participantes": "Arquivo; entidade produtora; equipe de preservacao",
                    "deliberacoes": "Definidos escopo, prazos e criterios de recebimento.",
                    "pendencias": "Confirmar inventario preliminar e responsaveis.",
                    "proximos_passos": "Formalizar acordo e iniciar sessao de submissao.",
                    "criado_por": SEED_AUTHOR,
                    "atualizado_por": SEED_AUTHOR,
                },
            )
            counts["reunioes"] += 1

            acordo_id = seed_uuid(f"acordo:{processo_seed.numero}:1")
            acordo, _ = upsert(
                db,
                AcordoAdmissao,
                acordo_id,
                {
                    "id_processo_admissao": processo.id,
                    "numero_versao": 1,
                    "titulo": "Acordo de admissao - versao inicial",
                    "descricao": "Conjunto de regras de empacotamento, validacao e sigilo.",
                    "status": StatusAcordoAdmissao.ATIVO,
                    "data_inicio_vigencia": processo_seed.data_inicio,
                    "data_fim_vigencia": None,
                    "motivo_revisao": "Versao inicial da massa de teste.",
                    "regras_empacotamento": "SIPs em diretorio unico com manifesto e checksums.",
                    "regras_nomenclatura": "ADM_TEST_<processo>_<sequencial>.",
                    "formatos_aceitos": "PDF/A, TIFF, CSV, XML, TXT, EML e objetos binarios documentados.",
                    "metadados_obrigatorios": "titulo; produtor; data; identificador; checksum.",
                    "requisitos_fixidez": "SHA-256 obrigatorio para cada arquivo e hash global do pacote.",
                    "requisitos_representacao": "Representantes de acesso quando aplicavel.",
                    "politica_validacao": "Validacao tecnica, antivirus, contagem e conferencia amostral.",
                    "politica_rejeicao": "Rejeitar SIP sem manifesto, hash invalido ou escopo divergente.",
                    "politica_normalizacao": "Normalizacao apenas apos validacao tecnica.",
                    "politica_sigilo": "Restricao interna ate homologacao.",
                    "periodicidade_submissao": "Mensal" if processo_seed.recorrente else "Unica",
                    "observacoes": "Acordo gerado por seed idempotente.",
                    "documento_acordo": f"/documentos/admissao/{processo_seed.numero}/acordo-v1.pdf",
                    "criado_por": SEED_AUTHOR,
                    "atualizado_por": SEED_AUTHOR,
                },
            )
            counts["acordos"] += 1
            db.flush()

            sessao_id = seed_uuid(f"sessao:{processo_seed.numero}:1")
            sessao, _ = upsert(
                db,
                SessaoSubmissao,
                sessao_id,
                {
                    "id_processo_admissao": processo.id,
                    "id_acordo_utilizado": acordo.id,
                    "numero_sessao": 1,
                    "titulo": "Sessao de submissao inicial",
                    "descricao": "Primeiro lote de objetos recebidos para teste de fluxo.",
                    "data_inicio": datetime(2026, min(index + 1, 12), 12, 9, tzinfo=timezone.utc),
                    "data_fim": datetime(2026, min(index + 1, 12), 16, 18, tzinfo=timezone.utc)
                    if processo_seed.status in {StatusProcessoAdmissao.CONCLUIDO, StatusProcessoAdmissao.EM_GERACAO_AIP}
                    else None,
                    "canal_submissao": CanalSubmissao.REDE_INTERNA
                    if processo_seed.tipo_suporte != TipoSuporte.FISICO
                    else CanalSubmissao.ENTREGA_FISICA,
                    "responsavel_envio": "Responsavel da entidade produtora",
                    "responsavel_recebimento": f"Arquivista Teste {index}",
                    "tipo_suporte": processo_seed.tipo_suporte,
                    "volume_informado": processo_seed.volume_estimado,
                    "volume_recebido": processo_seed.volume_recebido,
                    "caminho_origem": f"/origem/{processo_seed.numero}",
                    "caminho_destino_quarentena": f"/quarentena/{processo_seed.numero}",
                    "status": StatusSessaoSubmissao.FINALIZADA
                    if processo_seed.status == StatusProcessoAdmissao.CONCLUIDO
                    else StatusSessaoSubmissao.VALIDADA,
                    "resultado_validacao": "Manifesto conferido; hashes validos; ressalvas registradas.",
                    "observacoes": "Sessao criada pela massa de admissao.",
                    "criado_por": SEED_AUTHOR,
                    "atualizado_por": SEED_AUTHOR,
                },
            )
            counts["sessoes"] += 1
            db.flush()

            for sip_number in range(1, 3):
                sip_id = seed_uuid(f"sip:{processo_seed.numero}:{sip_number}")
                codigo_sip = f"SIP-{processo_seed.numero}-{sip_number:02d}"
                sip_status = (
                    StatusSipAdmissao.TRANSFORMADO_EM_AIP
                    if processo_seed.key in {"migracao-legado", "colecao-fotografica"} and sip_number == 1
                    else StatusSipAdmissao.VALIDADO_COM_RESSALVA
                    if processo_seed.status == StatusProcessoAdmissao.CONCLUIDO
                    else StatusSipAdmissao.VALIDADO
                )
                sip, _ = upsert(
                    db,
                    SipAdmissao,
                    sip_id,
                    {
                        "id_processo_admissao": processo.id,
                        "id_sessao_submissao": sessao.id,
                        "codigo_sip": codigo_sip,
                        "titulo": f"Pacote SIP {sip_number} - {processo_seed.titulo}",
                        "descricao": "Pacote gerado para massa de teste de admissao.",
                        "tipo_sip": processo_seed.tipo_suporte,
                        "status": sip_status,
                        "data_recebimento": datetime(2026, min(index + 1, 12), 13 + sip_number, 11, tzinfo=timezone.utc),
                        "estrutura_original": "manifest.json; data/; checksums.sha256",
                        "caminho_armazenamento_temporario": f"/quarentena/{processo_seed.numero}/{codigo_sip}",
                        "manifesto_arquivos": "manifest.json",
                        "algoritmo_hash": "SHA-256",
                        "hash_global": uuid.uuid5(SEED_NAMESPACE, codigo_sip).hex,
                        "tamanho_bytes": 75_000_000_000 * sip_number,
                        "quantidade_arquivos": 420 * sip_number,
                        "quantidade_unidades_fisicas": 3 * sip_number
                        if processo_seed.tipo_suporte != TipoSuporte.DIGITAL
                        else None,
                        "resultado_validacao": "Pacote aprovado na validacao automatica.",
                        "observacoes": "SIP criado pela massa de admissao.",
                        "criado_por": SEED_AUTHOR,
                        "atualizado_por": SEED_AUTHOR,
                    },
                )
                counts["sips"] += 1
                db.flush()

                unit_id = (
                    unidades["TEST-DIG-001"]
                    if processo_seed.tipo_suporte == TipoSuporte.DIGITAL
                    else unidades["TEST-FIS-001"]
                    if processo_seed.tipo_suporte == TipoSuporte.FISICO
                    else unidades["TEST-DIG-002"]
                )
                if sip_status == StatusSipAdmissao.TRANSFORMADO_EM_AIP and unit_id:
                    upsert(
                        db,
                        RelacaoSipAip,
                        seed_uuid(f"relacao:{codigo_sip}:{unit_id}"),
                        {
                            "id_sip": sip.id,
                            "id_unidade_acondicionamento": unit_id,
                            "tipo_relacao": TipoRelacaoSipAip.ORIGEM_TOTAL,
                            "observacoes": "Relacao AIP criada pela massa de admissao.",
                            "criado_por": SEED_AUTHOR,
                        },
                    )
                    counts["relacoes_sip_aip"] += 1
                    db.flush()

            event_specs = [
                (TipoEventoAdmissao.CRIACAO_PROCESSO, "Processo de admissao criado."),
                (TipoEventoAdmissao.REUNIAO_ADMISSAO, "Reuniao inicial registrada."),
                (TipoEventoAdmissao.CRIACAO_VERSAO_ACORDO, "Acordo inicial criado."),
                (TipoEventoAdmissao.ATIVACAO_ACORDO, "Acordo inicial ativado."),
                (TipoEventoAdmissao.SESSAO_VALIDADA, "Sessao validada pela equipe tecnica."),
            ]
            if processo_seed.status == StatusProcessoAdmissao.CONCLUIDO:
                event_specs.append((TipoEventoAdmissao.ENCERRAMENTO_PROCESSO, "Processo concluido."))
            for event_number, (tipo_evento, descricao) in enumerate(event_specs, start=1):
                upsert(
                    db,
                    EventoAdmissao,
                    seed_uuid(f"evento:{processo_seed.numero}:{event_number}"),
                    {
                        "id_processo_admissao": processo.id,
                        "id_sessao_submissao": sessao.id if event_number >= 5 else None,
                        "id_sip": None,
                        "id_unidade_acondicionamento": None,
                        "tipo_evento": tipo_evento,
                        "descricao": descricao,
                        "resultado": ResultadoEventoAdmissao.SUCESSO,
                        "agente": SEED_AUTHOR,
                        "data_evento": datetime(2026, min(index + 1, 12), 15, 10 + event_number, tzinfo=timezone.utc),
                        "detalhe_tecnico": "Evento gerado por seed idempotente.",
                        "evidencia": f"/evidencias/{processo_seed.numero}/evento-{event_number}.json",
                        "criado_por": SEED_AUTHOR,
                    },
                )
                counts["eventos"] += 1

        db.commit()

    return counts


if __name__ == "__main__":
    result = seed_admissao()
    print(
        "Massa de teste de admissao concluida: "
        f"{result['processos_criados']} processos criados, "
        f"{result['processos_atualizados']} processos atualizados, "
        f"{result['reunioes']} reunioes, {result['acordos']} acordos, "
        f"{result['sessoes']} sessoes, {result['sips']} SIPs, "
        f"{result['relacoes_sip_aip']} relacoes SIP/AIP e "
        f"{result['eventos']} eventos processados."
    )
