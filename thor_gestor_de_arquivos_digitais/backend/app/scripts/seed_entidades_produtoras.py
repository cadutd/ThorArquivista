from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import TipoEntidadeProdutora

SEED_NAMESPACE = uuid.UUID("2d89cda0-7a08-4d1b-b4ea-105e5c3f7d0a")


@dataclass(frozen=True)
class EntidadeProdutoraSeed:
    codigo: str
    nome: str
    tipo_entidade: TipoEntidadeProdutora
    sigla: str | None = None
    codigo_referencia: str | None = None
    natureza_juridica: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    entidade_ativa: bool = True
    historico: str | None = None
    competencias_funcoes: str | None = None
    observacoes: str | None = None
    email: str | None = None
    telefone: str | None = None
    site: str | None = None
    endereco_logradouro: str | None = None
    endereco_numero: str | None = None
    endereco_complemento: str | None = None
    endereco_bairro: str | None = None
    endereco_municipio: str | None = None
    endereco_uf: str | None = None
    endereco_cep: str | None = None
    endereco_pais: str = "Brasil"
    superior_codigo: str | None = None

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(SEED_NAMESPACE, self.codigo)


def normalizar_nome(nome: str) -> str:
    import re
    import unicodedata

    sem_acentos = "".join(
        char
        for char in unicodedata.normalize("NFKD", nome)
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", sem_acentos).strip().lower()


def build_seed_data() -> list[EntidadeProdutoraSeed]:
    return [
        EntidadeProdutoraSeed(
            codigo="TEST-EP-SEC-GOVERNO-DIGITAL",
            nome="Secretaria de Governo Digital",
            sigla="SGD",
            codigo_referencia="EP-SGD",
            tipo_entidade=TipoEntidadeProdutora.ORGAO_PUBLICO,
            natureza_juridica="Órgão público estadual",
            data_inicio=date(2001, 1, 1),
            historico="Órgão central de coordenação de políticas digitais e gestão documental.",
            competencias_funcoes="Normatização, coordenação e supervisão de programas digitais.",
            email="sgd.teste@thor.local",
            telefone="(11) 3000-1000",
            site="https://sgd.example.local",
            endereco_logradouro="Rua da Administração Pública",
            endereco_numero="100",
            endereco_bairro="Centro",
            endereco_municipio="São Paulo",
            endereco_uf="SP",
            endereco_cep="01000-000",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-ARQUIVO-PUBLICO-SP",
            nome="Arquivo Público do Estado de São Paulo",
            sigla="APESP",
            codigo_referencia="EP-SGD-APESP",
            tipo_entidade=TipoEntidadeProdutora.UNIDADE_ADMINISTRATIVA,
            natureza_juridica="Unidade administrativa",
            data_inicio=date(1892, 4, 10),
            historico="Unidade de preservação, acesso e difusão do patrimônio documental.",
            competencias_funcoes="Gestão de arquivos permanentes e orientação técnica arquivística.",
            email="apesp.teste@thor.local",
            telefone="(11) 3000-1100",
            endereco_logradouro="Avenida Arquivo Público",
            endereco_numero="51",
            endereco_bairro="Santana",
            endereco_municipio="São Paulo",
            endereco_uf="SP",
            endereco_cep="02000-000",
            superior_codigo="TEST-EP-SEC-GOVERNO-DIGITAL",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-CENTRO-PRESERVACAO-DIGITAL",
            nome="Centro de Preservação e Acesso Digital",
            sigla="CPAD",
            codigo_referencia="EP-SGD-APESP-CPAD",
            tipo_entidade=TipoEntidadeProdutora.UNIDADE_ADMINISTRATIVA,
            data_inicio=date(2018, 6, 1),
            historico="Centro responsável por processos de admissão, preservação e acesso digital.",
            competencias_funcoes="Ingestão, fixidez, armazenamento, descrição técnica e geração de DIPs.",
            email="cpad.teste@thor.local",
            endereco_municipio="São Paulo",
            endereco_uf="SP",
            superior_codigo="TEST-EP-ARQUIVO-PUBLICO-SP",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-NUCLEO-INGESTAO",
            nome="Núcleo de Ingestão OAIS",
            sigla="NIO",
            codigo_referencia="EP-SGD-APESP-CPAD-NIO",
            tipo_entidade=TipoEntidadeProdutora.GRUPO_TRABALHO,
            data_inicio=date(2020, 3, 15),
            historico="Grupo de trabalho operacional para recebimento e validação de SIPs.",
            competencias_funcoes="Conferência de pacotes, normalização de metadados e registro de eventos.",
            email="ingestao.teste@thor.local",
            endereco_municipio="São Paulo",
            endereco_uf="SP",
            superior_codigo="TEST-EP-CENTRO-PRESERVACAO-DIGITAL",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-LAB-DIGITALIZACAO",
            nome="Laboratório de Digitalização e Captura",
            sigla="LDC",
            codigo_referencia="EP-SGD-APESP-LDC",
            tipo_entidade=TipoEntidadeProdutora.UNIDADE_ADMINISTRATIVA,
            data_inicio=date(2012, 8, 20),
            historico="Laboratório de geração de representantes digitais e controle de qualidade.",
            competencias_funcoes="Digitalização, controle de qualidade e entrega de matrizes digitais.",
            email="digitalizacao.teste@thor.local",
            endereco_municipio="São Paulo",
            endereco_uf="SP",
            superior_codigo="TEST-EP-ARQUIVO-PUBLICO-SP",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-COMISSAO-AVALIACAO",
            nome="Comissão Permanente de Avaliação Documental",
            sigla="CPADoc",
            codigo_referencia="EP-SGD-CPADOC",
            tipo_entidade=TipoEntidadeProdutora.COMISSAO,
            data_inicio=date(2005, 2, 1),
            historico="Comissão de avaliação, destinação e recolhimento documental.",
            competencias_funcoes="Avaliação de séries, aprovação de tabelas e deliberação sobre recolhimento.",
            email="avaliacao.teste@thor.local",
            superior_codigo="TEST-EP-SEC-GOVERNO-DIGITAL",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-DEPTO-ADMINISTRACAO",
            nome="Departamento de Administração e Logística",
            sigla="DAL",
            codigo_referencia="EP-SGD-DAL",
            tipo_entidade=TipoEntidadeProdutora.UNIDADE_ADMINISTRATIVA,
            data_inicio=date(1999, 1, 1),
            historico="Unidade produtora de processos administrativos, contratos e relatórios.",
            competencias_funcoes="Contratações, gestão patrimonial, almoxarifado e serviços gerais.",
            email="dal.teste@thor.local",
            endereco_municipio="São Paulo",
            endereco_uf="SP",
            superior_codigo="TEST-EP-SEC-GOVERNO-DIGITAL",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-COORD-FINANCAS",
            nome="Coordenação de Finanças e Orçamento",
            sigla="CFO",
            codigo_referencia="EP-SGD-DAL-CFO",
            tipo_entidade=TipoEntidadeProdutora.UNIDADE_ADMINISTRATIVA,
            data_inicio=date(2008, 5, 1),
            historico="Coordenação produtora de documentação orçamentária e financeira.",
            competencias_funcoes="Execução orçamentária, pagamentos, prestação de contas e relatórios fiscais.",
            email="financas.teste@thor.local",
            superior_codigo="TEST-EP-DEPTO-ADMINISTRACAO",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-EMPRESA-PUBLICA-PROCESSAMENTO",
            nome="Companhia Pública de Processamento de Dados",
            sigla="CPPD",
            codigo_referencia="EP-CPPD",
            tipo_entidade=TipoEntidadeProdutora.EMPRESA_PUBLICA,
            natureza_juridica="Empresa pública",
            data_inicio=date(1978, 9, 12),
            historico="Empresa pública produtora de sistemas, bases e documentação técnica.",
            competencias_funcoes="Hospedagem, desenvolvimento de sistemas e sustentação tecnológica.",
            email="cppd.teste@thor.local",
            site="https://cppd.example.local",
            endereco_municipio="Campinas",
            endereco_uf="SP",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-UNIDADE-DATA-CENTER",
            nome="Unidade de Operações de Data Center",
            sigla="UDC",
            codigo_referencia="EP-CPPD-UDC",
            tipo_entidade=TipoEntidadeProdutora.UNIDADE_ADMINISTRATIVA,
            data_inicio=date(2010, 7, 1),
            historico="Unidade operacional de armazenamento, backup e monitoramento.",
            competencias_funcoes="Operação de ambientes, rotinas de backup e guarda de mídias.",
            email="datacenter.teste@thor.local",
            superior_codigo="TEST-EP-EMPRESA-PUBLICA-PROCESSAMENTO",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-ACME-MIGRACAO",
            nome="ACME Digitalização e Migração Ltda.",
            sigla="ACME-DM",
            codigo_referencia="EP-ACME-DM",
            tipo_entidade=TipoEntidadeProdutora.EMPRESA_PRIVADA,
            natureza_juridica="Sociedade empresária limitada",
            data_inicio=date(2015, 1, 5),
            historico="Prestadora de serviços de digitalização, OCR e migração de suportes.",
            competencias_funcoes="Preparação, digitalização, controle de qualidade e entrega de lotes.",
            email="contato@acme-dm.example.local",
            telefone="(11) 3000-2200",
            endereco_municipio="Barueri",
            endereco_uf="SP",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-FAMILIA-ALMEIDA-PRADO",
            nome="Família Almeida Prado",
            codigo_referencia="EP-FAM-ALMEIDA-PRADO",
            tipo_entidade=TipoEntidadeProdutora.FAMILIA,
            data_inicio=date(1880, 1, 1),
            historico="Família produtora e acumuladora de correspondências, fotografias e diários.",
            competencias_funcoes="Produção e acumulação de documentos privados de interesse histórico.",
            observacoes="Datas aproximadas usadas para massa de teste.",
            endereco_municipio="Santos",
            endereco_uf="SP",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-MARIA-HELENA-PRADO",
            nome="Maria Helena Almeida Prado",
            codigo_referencia="EP-PF-MHAP",
            tipo_entidade=TipoEntidadeProdutora.PESSOA_FISICA,
            data_inicio=date(1934, 5, 13),
            data_fim=date(2019, 11, 28),
            entidade_ativa=False,
            historico="Pesquisadora e titular de arquivo pessoal incorporado ao fundo familiar.",
            competencias_funcoes="Produção de correspondências, cadernos de pesquisa e fotografias.",
            endereco_municipio="Santos",
            endereco_uf="SP",
            superior_codigo="TEST-EP-FAMILIA-ALMEIDA-PRADO",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-FUNDO-ADMINISTRACAO-CENTRAL",
            nome="Fundo Administração Central",
            sigla="FAC",
            codigo_referencia="BR-SP-THOR-FAC",
            tipo_entidade=TipoEntidadeProdutora.FUNDO,
            data_inicio=date(1988, 1, 1),
            historico="Fundo de teste com séries de administração, orçamento e tecnologia.",
            competencias_funcoes="Representa proveniência agregada para unidades documentais administrativas.",
            observacoes="Registro de fundo usado para testes de hierarquia e filtros.",
            superior_codigo="TEST-EP-SEC-GOVERNO-DIGITAL",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-FUNDO-PRESERVACAO-DIGITAL",
            nome="Fundo Preservação Digital",
            sigla="FPD",
            codigo_referencia="BR-SP-THOR-FPD",
            tipo_entidade=TipoEntidadeProdutora.FUNDO,
            data_inicio=date(2018, 6, 1),
            historico="Fundo de teste para pacotes digitais, eventos e metadados técnicos.",
            competencias_funcoes="Reúne documentação produzida nas rotinas de preservação digital.",
            superior_codigo="TEST-EP-CENTRO-PRESERVACAO-DIGITAL",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-COLECAO-FOTOGRAFICA",
            nome="Coleção Fotográfica Institucional",
            sigla="CFI",
            codigo_referencia="BR-SP-THOR-CFI",
            tipo_entidade=TipoEntidadeProdutora.COLECAO,
            data_inicio=date(1940, 1, 1),
            historico="Coleção de teste composta por fotografias analógicas e representantes digitais.",
            competencias_funcoes="Agrupamento artificial de itens iconográficos.",
            observacoes="Datas de acumulação aproximadas.",
            superior_codigo="TEST-EP-ARQUIVO-PUBLICO-SP",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-GT-MIGRACAO-SISTEMAS",
            nome="Grupo de Trabalho Migração de Sistemas Legados",
            sigla="GT-MSL",
            codigo_referencia="EP-SGD-GT-MSL",
            tipo_entidade=TipoEntidadeProdutora.GRUPO_TRABALHO,
            data_inicio=date(2022, 2, 1),
            data_fim=date(2023, 12, 20),
            entidade_ativa=True,
            historico="Grupo temporário de teste criado para migrar bases legadas.",
            competencias_funcoes="Levantamento, saneamento, migração e validação de dados.",
            observacoes="Mantido ativo para fins de acompanhamento pós-migração.",
            superior_codigo="TEST-EP-SEC-GOVERNO-DIGITAL",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-COMISSAO-VERDADE-DIGITAL",
            nome="Comissão Especial de Memória Digital",
            sigla="CEMD",
            codigo_referencia="EP-CEMD",
            tipo_entidade=TipoEntidadeProdutora.COMISSAO,
            data_inicio=date(2014, 1, 10),
            data_fim=date(2016, 6, 30),
            entidade_ativa=False,
            historico="Comissão extinta produtora de relatórios, atas e acervos de entrevistas.",
            competencias_funcoes="Apuração, documentação e consolidação de relatórios temáticos.",
            observacoes="Entidade extinta usada em filtros de situação.",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-OUTRO-REDE-PARCEIROS",
            nome="Rede de Parceiros de Preservação Colaborativa",
            sigla="RPPC",
            codigo_referencia="EP-RPPC",
            tipo_entidade=TipoEntidadeProdutora.OUTRO,
            data_inicio=date(2021, 9, 1),
            historico="Rede colaborativa usada para testar tipo OUTRO.",
            competencias_funcoes="Articulação técnica, cooperação e compartilhamento de boas práticas.",
            email="rede.teste@thor.local",
        ),
        EntidadeProdutoraSeed(
            codigo="TEST-EP-COLECAO-HISTORIA-ORAL",
            nome="Coleção História Oral",
            sigla="CHO",
            codigo_referencia="BR-SP-THOR-CHO",
            tipo_entidade=TipoEntidadeProdutora.COLECAO,
            data_inicio=date(1995, 3, 1),
            historico="Coleção de entrevistas, transcrições, termos e arquivos de áudio.",
            competencias_funcoes="Agrupamento de documentos produzidos em projetos de história oral.",
            superior_codigo="TEST-EP-ARQUIVO-PUBLICO-SP",
        ),
    ]


def upsert_entidade(db: Session, seed: EntidadeProdutoraSeed, ids_by_code: dict[str, uuid.UUID]) -> bool:
    superior_id = ids_by_code.get(seed.superior_codigo) if seed.superior_codigo else None
    existing_id = db.execute(
        text(
            """
            SELECT id
            FROM entidades_produtoras
            WHERE id = :id
            """
        ),
        {"id": seed.id},
    ).scalar_one_or_none()
    created = existing_id is None

    db.execute(
        text(
            """
            INSERT INTO entidades_produtoras (
                id,
                nome,
                nome_normalizado,
                sigla,
                codigo_referencia,
                tipo_entidade,
                natureza_juridica,
                data_inicio,
                data_fim,
                entidade_ativa,
                historico,
                competencias_funcoes,
                observacoes,
                email,
                telefone,
                site,
                endereco_logradouro,
                endereco_numero,
                endereco_complemento,
                endereco_bairro,
                endereco_municipio,
                endereco_uf,
                endereco_cep,
                endereco_pais,
                id_entidade_superior
            )
            VALUES (
                :id,
                :nome,
                :nome_normalizado,
                :sigla,
                :codigo_referencia,
                :tipo_entidade,
                :natureza_juridica,
                :data_inicio,
                :data_fim,
                :entidade_ativa,
                :historico,
                :competencias_funcoes,
                :observacoes,
                :email,
                :telefone,
                :site,
                :endereco_logradouro,
                :endereco_numero,
                :endereco_complemento,
                :endereco_bairro,
                :endereco_municipio,
                :endereco_uf,
                :endereco_cep,
                :endereco_pais,
                :id_entidade_superior
            )
            ON CONFLICT (id)
            DO UPDATE SET
                nome = EXCLUDED.nome,
                nome_normalizado = EXCLUDED.nome_normalizado,
                sigla = EXCLUDED.sigla,
                codigo_referencia = EXCLUDED.codigo_referencia,
                tipo_entidade = EXCLUDED.tipo_entidade,
                natureza_juridica = EXCLUDED.natureza_juridica,
                data_inicio = EXCLUDED.data_inicio,
                data_fim = EXCLUDED.data_fim,
                entidade_ativa = EXCLUDED.entidade_ativa,
                historico = EXCLUDED.historico,
                competencias_funcoes = EXCLUDED.competencias_funcoes,
                observacoes = EXCLUDED.observacoes,
                email = EXCLUDED.email,
                telefone = EXCLUDED.telefone,
                site = EXCLUDED.site,
                endereco_logradouro = EXCLUDED.endereco_logradouro,
                endereco_numero = EXCLUDED.endereco_numero,
                endereco_complemento = EXCLUDED.endereco_complemento,
                endereco_bairro = EXCLUDED.endereco_bairro,
                endereco_municipio = EXCLUDED.endereco_municipio,
                endereco_uf = EXCLUDED.endereco_uf,
                endereco_cep = EXCLUDED.endereco_cep,
                endereco_pais = EXCLUDED.endereco_pais,
                id_entidade_superior = EXCLUDED.id_entidade_superior,
                atualizado_em = now()
            """
        ),
        {
            "id": seed.id,
            "nome": seed.nome,
            "nome_normalizado": normalizar_nome(seed.nome),
            "sigla": seed.sigla,
            "codigo_referencia": seed.codigo_referencia,
            "tipo_entidade": seed.tipo_entidade.value,
            "natureza_juridica": seed.natureza_juridica,
            "data_inicio": seed.data_inicio,
            "data_fim": seed.data_fim,
            "entidade_ativa": seed.entidade_ativa,
            "historico": seed.historico,
            "competencias_funcoes": seed.competencias_funcoes,
            "observacoes": seed.observacoes,
            "email": seed.email,
            "telefone": seed.telefone,
            "site": seed.site,
            "endereco_logradouro": seed.endereco_logradouro,
            "endereco_numero": seed.endereco_numero,
            "endereco_complemento": seed.endereco_complemento,
            "endereco_bairro": seed.endereco_bairro,
            "endereco_municipio": seed.endereco_municipio,
            "endereco_uf": seed.endereco_uf,
            "endereco_cep": seed.endereco_cep,
            "endereco_pais": seed.endereco_pais,
            "id_entidade_superior": superior_id,
        },
    )
    return created


def count_seeded_entidades(db: Session, seeds: list[EntidadeProdutoraSeed]) -> tuple[int, int, int]:
    ids = [str(seed.id) for seed in seeds]
    total = int(
        db.execute(
            text(
                """
                SELECT count(*)
                FROM entidades_produtoras
                WHERE id = ANY(:ids)
                """
            ),
            {"ids": ids},
        ).scalar_one()
    )
    roots = int(
        db.execute(
            text(
                """
                SELECT count(*)
                FROM entidades_produtoras
                WHERE id = ANY(:ids)
                  AND id_entidade_superior IS NULL
                """
            ),
            {"ids": ids},
        ).scalar_one()
    )
    children = int(
        db.execute(
            text(
                """
                SELECT count(*)
                FROM entidades_produtoras
                WHERE id = ANY(:ids)
                  AND id_entidade_superior IS NOT NULL
                """
            ),
            {"ids": ids},
        ).scalar_one()
    )
    return total, roots, children


def seed_entidades_produtoras() -> tuple[int, int, int, int, int]:
    seeds = build_seed_data()
    ids_by_code = {seed.codigo: seed.id for seed in seeds}
    created = 0
    updated = 0

    with SessionLocal() as db:
        for seed in seeds:
            if upsert_entidade(db, seed, ids_by_code):
                created += 1
            else:
                updated += 1

        total, roots, children = count_seeded_entidades(db, seeds)
        if total != len(seeds) or roots < 1 or children < 1:
            raise RuntimeError(
                "Contagem inesperada apos seed de entidades produtoras: "
                f"{total} de {len(seeds)} registros, {roots} raizes, {children} subordinadas."
            )

        db.commit()

    return created, updated, total, roots, children


if __name__ == "__main__":
    created_count, updated_count, total_count, root_count, child_count = (
        seed_entidades_produtoras()
    )
    print(
        "Massa de teste de entidades produtoras concluida: "
        f"{created_count} criadas, {updated_count} atualizadas, "
        f"{total_count} registros no total, {root_count} raizes, "
        f"{child_count} subordinadas."
    )
