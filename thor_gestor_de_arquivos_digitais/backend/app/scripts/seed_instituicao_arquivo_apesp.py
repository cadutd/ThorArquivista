from __future__ import annotations

from sqlalchemy import text

from app.db.session import SessionLocal
from app.schemas.instituicao_arquivo import InstituicaoArquivoCreate


APESP_PAYLOAD = {
    "nome": "Arquivo Público do Estado de São Paulo",
    "sigla": "APESP",
    "codigo_referencia": "BR SPAPESP",
    "natureza_juridica": "Órgão público estadual",
    "esfera_administrativa": "ESTADUAL",
    "cnpj": "39.467.292/0003-74",
    "email": "faleconosco@arquivoestado.sp.gov.br",
    "telefone": "(11) 2868-4500 / 2868-4451",
    "site": "https://www.arquivoestado.sp.gov.br/",
    "endereco_logradouro": "Rua Voluntários da Pátria",
    "endereco_numero": "596",
    "endereco_bairro": "Santana",
    "endereco_municipio": "São Paulo",
    "endereco_uf": "SP",
    "endereco_cep": "02010-000",
    "endereco_pais": "Brasil",
    "responsavel_nome": "Thiago Nicodemo",
    "responsavel_cargo": "Diretor do Arquivo Público do Estado de São Paulo",
    "historico": (
        "Instituição arquivística do Poder Executivo do Estado de São Paulo. "
        "O cadastro nacional de entidades custodiadoras informa o ano de criação "
        "1892 e a vinculação administrativa à Secretaria de Governo do Estado de "
        "São Paulo. A Unidade do Arquivo Público do Estado atua na formulação e "
        "implementação da política estadual de arquivos, abrangendo gestão "
        "documental, acesso, preservação e difusão do acervo."
    ),
    "missao": (
        "Formular e implementar a política estadual de arquivos, por meio da "
        "gestão, do recolhimento, da preservação e da difusão do patrimônio "
        "documental do Estado."
    ),
    "observacoes": (
        "Massa de teste baseada em dados públicos do CONARQ, do portal oficial "
        "do Arquivo Público do Estado de São Paulo e da Secretaria de Gestão e "
        "Governo Digital do Estado de São Paulo. CODEARQ: BR SPAPESP. "
        "Atendimento informado publicamente: segunda a sexta-feira, das 9h às 17h."
    ),
}


def seed_instituicao_arquivo_apesp() -> tuple[bool, str]:
    dados = InstituicaoArquivoCreate.model_validate(APESP_PAYLOAD)
    payload = dados.model_dump()

    with SessionLocal() as db:
        existing_id = db.execute(
            text("SELECT id FROM instituicao_arquivo WHERE singleton_key = TRUE")
        ).scalar_one_or_none()
        created = existing_id is None

        instituicao_id = db.execute(
            text(
                """
                INSERT INTO instituicao_arquivo (
                    singleton_key,
                    nome,
                    sigla,
                    codigo_referencia,
                    natureza_juridica,
                    esfera_administrativa,
                    cnpj,
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
                    responsavel_nome,
                    responsavel_cargo,
                    responsavel_email,
                    responsavel_telefone,
                    historico,
                    missao,
                    observacoes
                )
                VALUES (
                    TRUE,
                    :nome,
                    :sigla,
                    :codigo_referencia,
                    :natureza_juridica,
                    :esfera_administrativa,
                    :cnpj,
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
                    :responsavel_nome,
                    :responsavel_cargo,
                    :responsavel_email,
                    :responsavel_telefone,
                    :historico,
                    :missao,
                    :observacoes
                )
                ON CONFLICT (singleton_key)
                DO UPDATE SET
                    nome = EXCLUDED.nome,
                    sigla = EXCLUDED.sigla,
                    codigo_referencia = EXCLUDED.codigo_referencia,
                    natureza_juridica = EXCLUDED.natureza_juridica,
                    esfera_administrativa = EXCLUDED.esfera_administrativa,
                    cnpj = EXCLUDED.cnpj,
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
                    responsavel_nome = EXCLUDED.responsavel_nome,
                    responsavel_cargo = EXCLUDED.responsavel_cargo,
                    responsavel_email = EXCLUDED.responsavel_email,
                    responsavel_telefone = EXCLUDED.responsavel_telefone,
                    historico = EXCLUDED.historico,
                    missao = EXCLUDED.missao,
                    observacoes = EXCLUDED.observacoes,
                    atualizada_em = now()
                RETURNING id
                """
            ),
            payload,
        ).scalar_one()

        db.commit()

    return created, str(instituicao_id)


if __name__ == "__main__":
    was_created, id_ = seed_instituicao_arquivo_apesp()
    action = "criada" if was_created else "atualizada"
    print(
        "Massa de teste da Instituição de Arquivo concluida: "
        f"Instituição {action} com id {id_}."
    )
