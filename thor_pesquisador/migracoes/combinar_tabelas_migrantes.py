import argparse
import csv
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse


PASTA = Path(__file__).resolve().parent
ARQUIVO_DELEGACIA = PASTA / "tb_memig_delegacia_estrangeiros.csv"
ARQUIVO_HOSPEDARIA = PASTA / "tb_memimig_hospedaria_202611101114.csv"
ARQUIVO_SAIDA = PASTA / "migrantes_unificados.csv"


def texto_valido(valor):
    valor = valor.strip()
    return "" if valor in ("", r"\N") else valor


def ano_valido(valor):
    valor = texto_valido(valor)
    if re.fullmatch(r"\d{4}", valor):
        return str(int(valor))
    data = re.match(r"^(\d{4})-\d{2}-\d{2}$", valor)
    return str(int(data.group(1))) if data else ""


def validar_url(url, argumento):
    if not url:
        return
    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError(f"{argumento} deve ser uma URL http ou https.")


def linhas_csv(
    caminho,
    nome_indice,
    sobrenome_indice,
    origem_indice,
    ano_indice,
    fonte,
    campos_esperados,
    total_colunas,
):
    with caminho.open("r", encoding="latin-1", newline="") as arquivo:
        leitor = csv.reader(arquivo, delimiter=";", quotechar='"')
        cabecalho = next(leitor, None)
        if cabecalho is None:
            raise ValueError(f"Arquivo vazio: {caminho}")
        for campo, indice in campos_esperados.items():
            if len(cabecalho) <= indice or cabecalho[indice] != campo:
                raise ValueError(
                    f"Cabeçalho inesperado em {caminho}: campo {campo!r} "
                    f"não encontrado na posição {indice}."
                )

        for numero_linha, linha in enumerate(leitor, start=2):
            if len(linha) != total_colunas:
                raise ValueError(
                    f"{caminho}, linha {numero_linha}: esperadas "
                    f"{total_colunas} colunas, encontradas {len(linha)}."
                )
            yield (
                texto_valido(linha[nome_indice]),
                texto_valido(linha[sobrenome_indice]),
                texto_valido(linha[origem_indice]),
                ano_valido(linha[ano_indice]),
                fonte,
            )


def gerar_csv(saida, fonte_delegacia, fonte_hospedaria):
    validar_url(fonte_delegacia, "--fonte-delegacia")
    validar_url(fonte_hospedaria, "--fonte-hospedaria")

    entradas = (
        linhas_csv(
            ARQUIVO_DELEGACIA,
            nome_indice=1,
            sobrenome_indice=3,
            origem_indice=27,
            ano_indice=33,
            fonte=fonte_delegacia,
            campos_esperados={
                "primeiro_nome_original": 1,
                "sobrenome_original": 3,
                "nacionalidade_original": 22,
                "ano_entrada_alterado": 28,
            },
            # A exportação tem cinco valores sem cabeçalho antes destes campos.
            total_colunas=37,
        ),
        linhas_csv(
            ARQUIVO_HOSPEDARIA,
            nome_indice=7,
            sobrenome_indice=8,
            origem_indice=20,
            ano_indice=6,
            fonte=fonte_hospedaria,
            campos_esperados={
                "dt_chegada": 6,
                "nome": 7,
                "sobrenome": 8,
                "procedencia": 20,
            },
            total_colunas=45,
        ),
    )

    saida.parent.mkdir(parents=True, exist_ok=True)
    nome_temporario = None
    total = 0
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=saida.parent,
            suffix=".tmp",
            delete=False,
        ) as arquivo_temporario:
            nome_temporario = arquivo_temporario.name
            escritor = csv.writer(arquivo_temporario)
            escritor.writerow(
                ("nome_original", "sobrenome_original", "origem", "ano_chegada", "fonte_externa")
            )
            for linhas in entradas:
                for linha in linhas:
                    escritor.writerow(linha)
                    total += 1
        os.replace(nome_temporario, saida)
    except Exception:
        if nome_temporario and os.path.exists(nome_temporario):
            os.unlink(nome_temporario)
        raise
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Combina as tabelas da Delegacia e da Hospedaria em um CSV."
    )
    parser.add_argument("--saida", type=Path, default=ARQUIVO_SAIDA)
    parser.add_argument(
        "--fonte-delegacia",
        default="",
        help="URL externa para os registros da tabela da Delegacia.",
    )
    parser.add_argument(
        "--fonte-hospedaria",
        default="",
        help="URL externa para os registros da tabela da Hospedaria.",
    )
    argumentos = parser.parse_args()
    total = gerar_csv(
        argumentos.saida,
        argumentos.fonte_delegacia,
        argumentos.fonte_hospedaria,
    )
    print(f"CSV gerado: {argumentos.saida} ({total} registros).")


if __name__ == "__main__":
    main()
