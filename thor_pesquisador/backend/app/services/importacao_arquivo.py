"""Bounded CSV/JSON parsing and explicit conversions; no database writes."""
import csv
import io
import json
import math
import re
import unicodedata
from datetime import date, datetime
from pathlib import PurePath
from fastapi import HTTPException

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 1000
MAX_COLUMNS = 100


def falha(mensagem):
    raise HTTPException(422, mensagem)


def chave_sugerida(nome):
    ascii_name = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    key = re.sub(r"[^a-zA-Z0-9_]+", "_", ascii_name.strip()).strip("_").lower()
    if not key or not key[0].isalpha():
        key = "campo_" + key
    return key[:100]


def ler_arquivo(content, filename):
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Arquivo excede 5 MiB.")
    if not content:
        falha("Arquivo vazio.")
    extension = PurePath(filename or "").suffix.lower()
    if extension not in {".csv", ".json"}:
        falha("Selecione um arquivo CSV ou JSON.")
    encoding = "utf-8-sig"
    try:
        text = content.decode(encoding)
    except UnicodeDecodeError:
        if extension == ".json":
            falha("JSON deve usar UTF-8.")
        encoding = "cp1252"
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            falha("Codificacao do CSV invalida; use UTF-8 ou Windows-1252.")
    if "\x00" in text:
        falha("Arquivo contem caracteres nulos.")
    separator = None
    if extension == ".json":
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Chaves duplicadas.")
                result[key] = value
            return result
        try:
            rows = json.loads(text, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, RecursionError):
            falha("JSON invalido, muito aninhado ou com chaves duplicadas.")
        if isinstance(rows, dict):
            rows = rows.get("registros", rows.get("items"))
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            falha("JSON deve conter uma lista de objetos ou um objeto com registros/items.")
        columns = list(dict.fromkeys(key for row in rows for key in row))
    else:
        try:
            try:
                dialect = csv.Sniffer().sniff(text[:65536], delimiters=",;\t")
                separator = dialect.delimiter
            except csv.Error:
                separator = ";" if ";" in text.splitlines()[0] else ","
            reader = csv.reader(io.StringIO(text, newline=""), delimiter=separator, strict=True)
            columns = [key.strip() for key in next(reader)]
            if len(set(columns)) != len(columns):
                falha("Cabecalho CSV possui nomes duplicados.")
            rows = []
            for values in reader:
                if not values or all(not value.strip() for value in values):
                    continue
                if len(values) != len(columns):
                    falha("Linha CSV " + str(reader.line_num) + " tem quantidade de colunas diferente do cabecalho.")
                rows.append(dict(zip(columns, values)))
                if len(rows) > MAX_ROWS:
                    falha("Importacao limitada a 1000 registros por arquivo.")
        except (csv.Error, StopIteration, IndexError):
            falha("CSV invalido; verifique cabecalho, aspas e separadores.")
    if not rows or len(rows) > MAX_ROWS:
        falha("Informe entre 1 e 1000 registros por arquivo.")
    if not columns or len(columns) > MAX_COLUMNS or any(not k.strip() or len(k) > 255 or "\x00" in k for k in columns):
        falha("Informe ate 100 colunas, com nomes nao vazios de ate 255 caracteres.")
    return columns, rows, {"formato": extension[1:], "codificacao": encoding, "separador": separator}


def converter(value, tipo):
    if value is None or value == "" or value == []:
        return None
    if tipo == "BOOLEANO":
        if isinstance(value, bool):
            return value
        normalized = unicodedata.normalize("NFKD", str(value).strip().lower()).encode("ascii", "ignore").decode()
        if normalized in {"true", "sim", "1"}:
            return True
        if normalized in {"false", "nao", "0"}:
            return False
        raise ValueError("Informe Sim/Nao, true/false ou 1/0.")
    if tipo == "NUMERO":
        if isinstance(value, bool):
            raise ValueError("Informe um numero.")
        text = str(value).strip().replace(",", ".")
        if re.fullmatch(r"[+-]?\d+", text):
            integer = int(text)
            if not -(2**63) <= integer < 2**63:
                raise ValueError("Inteiro fora do intervalo de 64 bits.")
            return integer
        number = float(text)
        if not math.isfinite(number):
            raise ValueError("Informe um numero finito.")
        return int(number) if number.is_integer() and -(2**63) <= number < 2**63 else number
    if tipo == "DATA":
        text = str(value).strip()
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return datetime.strptime(text, "%d/%m/%Y").date().isoformat()
    if tipo == "LISTA_MULTIPLA":
        if isinstance(value, str):
            value = json.loads(value) if value.strip().startswith("[") else [s.strip() for s in value.split("|") if s.strip()]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError("Informe uma lista de textos ou valores separados por |.")
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def sugerir_tipo(values):
    values = [v for v in values if v is not None and v != ""]
    if not values:
        return "TEXTO_CURTO"
    if all(isinstance(v, list) and all(isinstance(s, str) for s in v) for v in values):
        return "LISTA_MULTIPLA"
    if all(isinstance(v, bool) or str(v).strip().lower() in {"true", "false", "sim", "nao", "não"} for v in values):
        return "BOOLEANO"
    for tipo in ["DATA", "NUMERO"]:
        try:
            if tipo == "NUMERO" and any(isinstance(v, str) and re.match(r"^0\d", v.strip()) for v in values):
                continue
            for value in values:
                converter(value, tipo)
            return tipo
        except (ValueError, TypeError, OverflowError):
            pass
    return "TEXTO_LONGO" if any(isinstance(v, (dict, list)) or len(str(v)) > 255 for v in values) else "TEXTO_CURTO"
