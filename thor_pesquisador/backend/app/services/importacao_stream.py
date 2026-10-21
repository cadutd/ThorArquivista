"""Disk-backed streaming imports, without inference or database writes.

Fully exhaust the iterator before committing a job: a later row or the JSON
trailer can still be invalid. Closing an abandoned iterator closes its file.
Limits count source bytes (including CSV/JSONL line endings, excluding a BOM);
JSON records count from their opening brace through their closing brace.
CSV encoding is selected from a bounded sample, never by buffering the file.
"""
import codecs
import csv
import io
import json
import math
import re
import threading
from decimal import Decimal
from typing import Iterator

import ijson
from ijson.common import ObjectBuilder

from app.services.importacao_arquivo import (
    chave_sugerida,
    converter,
    falha,
    sugerir_tipo,
)

__all__ = ["iter_registros", "converter", "sugerir_tipo", "chave_sugerida"]

_SAMPLE_BYTES = 65536
_CHUNK_BYTES = 16384
_MAX_DEPTH = 128
_CSV_LOCK = threading.RLock()
_STRUCTURAL = re.compile(rb"[{}\[\]]")


def _key(key):
    if not isinstance(key, str) or not key.strip() or len(key) > 255 or "\x00" in key:
        falha("Colunas/chaves devem ter nomes nao vazios de ate 255 caracteres, sem nulos.")


def _keys(keys, max_columns=None):
    seen = set()
    for key in keys:
        _key(key)
        if key in seen:
            falha("Colunas/chaves duplicadas.")
        seen.add(key)
        if max_columns is not None and len(seen) > max_columns:
            falha("Quantidade de colunas excede o limite de " + str(max_columns) + ".")
    return seen


def _too_large(limit):
    falha("Registro excede o limite de " + str(limit) + " bytes.")


def _scalar(value):
    if isinstance(value, str) and "\x00" in value:
        falha("Arquivo contem caracteres nulos.")
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        falha("JSON deve conter numeros finitos.")
    return value


class _CSVLines:
    def __init__(self, text, encoding, limit):
        self.text = text
        self.encoding = "utf-8" if encoding == "utf-8-sig" else encoding
        self.limit = limit
        self.used = 0

    def __iter__(self):
        return self

    def __next__(self):
        line = self.text.readline(self.limit - self.used + 1)
        if not line:
            raise StopIteration
        self.used += len(line.encode(self.encoding))
        if self.used > self.limit:
            _too_large(self.limit)
        if "\x00" in line:
            falha("Arquivo contem caracteres nulos.")
        return line


def _csv_next(reader, lines, limit):
    lines.used = 0
    # csv's field limit is process-global. Restore it even after parser errors.
    with _CSV_LOCK:
        previous = csv.field_size_limit()
        try:
            csv.field_size_limit(max(previous, limit))
            return next(reader)
        finally:
            csv.field_size_limit(previous)


def _iter_csv(path, max_columns, limit):
    with open(path, "rb") as raw:
        sample = raw.read(_SAMPLE_BYTES)
        encoding = "utf-8-sig"
        try:
            text_sample = codecs.getincrementaldecoder(encoding)().decode(sample, final=False)
        except UnicodeDecodeError:
            encoding = "cp1252"
            text_sample = sample.decode(encoding)
        raw.seek(0)
        try:
            separator = csv.Sniffer().sniff(text_sample, delimiters=",;\t|").delimiter
        except csv.Error:
            first = text_sample.split("\n", 1)[0]
            separator = max(",;\t|", key=first.count)
        with io.TextIOWrapper(raw, encoding=encoding, newline="") as text:
            lines = _CSVLines(text, encoding, limit)
            reader = csv.reader(lines, delimiter=separator, strict=True)
            try:
                columns = [key.strip() for key in _csv_next(reader, lines, limit)]
            except StopIteration:
                falha("Arquivo CSV vazio.")
            _keys(columns, max_columns)
            if not columns:
                falha("Cabecalho CSV vazio.")
            while True:
                try:
                    values = _csv_next(reader, lines, limit)
                except StopIteration:
                    return
                if not values or all(not value.strip() for value in values):
                    continue
                if len(values) != len(columns):
                    falha("Linha CSV " + str(reader.line_num) + " tem quantidade de colunas diferente do cabecalho.")
                yield dict(zip(columns, values))


class _JSONEvents:
    """Feed ijson bounded chunks; only ijson interprets JSON syntax.

    Braces/brackets are delivered separately, even inside strings. Thus a real
    container event has an exact byte offset, without implementing a lexer.
    The active byte budget stops an oversized *unfinished token* too, before
    ijson or ObjectBuilder can accumulate the rest of it.
    """

    def __init__(self, source, limit):
        self.source = source
        self.limit = limit
        self.offset = 0
        self.release()

    def release(self):
        self.anchor = self.offset
        self.budget = max(self.limit, 4096)

    def record(self):
        self.anchor = self.offset - 1
        self.budget = self.limit
        if self.offset - self.anchor > self.budget:
            _too_large(self.limit)

    def __iter__(self):
        events = ijson.sendable_list()
        parser = ijson.basic_parse_coro(events)
        closed = False

        def feed(data):
            if not data:
                return
            self.offset += len(data)
            if self.offset - self.anchor > self.budget:
                _too_large(self.limit)
            parser.send(data)
            for event, value in events:
                yield event, value
            events.clear()

        try:
            while True:
                chunk = self.source.read(min(_CHUNK_BYTES, self.limit + 1))
                if not chunk:
                    break
                start = 0
                for match in _STRUCTURAL.finditer(chunk):
                    yield from feed(chunk[start:match.start()])
                    yield from feed(chunk[match.start():match.end()])
                    start = match.end()
                yield from feed(chunk[start:])
            closed = True
            parser.close()
            yield from events
        finally:
            if not closed:
                try:
                    parser.close()
                except (ijson.JSONError, ValueError, OverflowError, RecursionError):
                    pass


def _json_value(first, events, stream, max_columns):
    event, value = first
    if event not in {"start_map", "start_array"}:
        if event not in {"null", "boolean", "number", "integer", "double", "string"}:
            falha("Valor JSON invalido.")
        return _scalar(value)
    stream.record()
    builder = ObjectBuilder()
    builder.event(event, value)
    containers = [set() if event == "start_map" else None]
    while containers:
        event, value = next(events)
        if event == "map_key":
            _key(value)
            keys = containers[-1]
            if value in keys:
                falha("JSON contem chaves duplicadas.")
            keys.add(value)
            if len(containers) == 1 and keys is not None and len(keys) > max_columns:
                falha("Quantidade de colunas excede o limite de " + str(max_columns) + ".")
        elif event in {"start_map", "start_array"}:
            if len(containers) >= _MAX_DEPTH:
                falha("JSON excede o limite de aninhamento.")
            containers.append(set() if event == "start_map" else None)
        elif event in {"end_map", "end_array"}:
            containers.pop()
        else:
            value = _scalar(value)
        builder.event(event, value)
    stream.release()
    return builder.value


def _json_array(events, stream, max_columns):
    while True:
        first = next(events)
        if first[0] == "end_array":
            stream.release()
            return
        if first[0] != "start_map":
            falha("Cada registro JSON deve ser um objeto.")
        yield _json_value(first, events, stream, max_columns)


def _iter_json(path, max_columns, limit):
    with open(path, "rb") as source:
        if source.read(3) != codecs.BOM_UTF8:
            source.seek(0)
        stream = _JSONEvents(source, limit)
        events = iter(stream)
        try:
            first = next(events)
            stream.release()
            if first[0] == "start_array":
                yield from _json_array(events, stream, max_columns)
            elif first[0] == "start_map":
                wrapper_keys = set()
                found = False
                while True:
                    event, key = next(events)
                    if event == "end_map":
                        break
                    if event != "map_key":
                        falha("Wrapper JSON invalido.")
                    _key(key)
                    if key in wrapper_keys:
                        falha("JSON contem chaves duplicadas.")
                    wrapper_keys.add(key)
                    if len(wrapper_keys) > max_columns:
                        falha("Wrapper JSON excede o limite de chaves.")
                    value = next(events)
                    if key in {"registros", "items"}:
                        if found or value[0] != "start_array":
                            falha("Informe apenas uma lista registros/items no wrapper JSON.")
                        found = True
                        stream.release()
                        yield from _json_array(events, stream, max_columns)
                    else:
                        # Metadata is bounded and validated, not silently skipped.
                        _json_value(value, events, stream, max_columns)
                    stream.release()
                if not found:
                    falha("JSON deve conter uma lista de objetos ou registros/items.")
            else:
                falha("JSON deve conter uma lista de objetos ou registros/items.")
            # Exhaust ijson even after closing the array/wrapper to reject trailers.
            for _ in events:
                falha("Conteudo adicional apos o JSON.")
        finally:
            events.close()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _key(key)
        if key in result:
            falha("JSON contem chaves duplicadas.")
        result[key] = value
    return result


def _invalid_constant(value):
    falha("Constante JSON invalida: " + value + ".")


def _validate_jsonl(row):
    pending = [(row, 1)]
    while pending:
        value, depth = pending.pop()
        if isinstance(value, (dict, list)):
            if depth > _MAX_DEPTH:
                falha("JSON excede o limite de aninhamento.")
            if isinstance(value, dict):
                _keys(value)
                children = value.values()
            else:
                children = value
            pending.extend((child, depth + 1) for child in children)
        else:
            _scalar(value)


def _iter_jsonl(path, limit):
    with open(path, "rb") as source:
        first = True
        while True:
            # Strip only the initial BOM; it is not part of the record budget.
            if first:
                if source.read(3) != codecs.BOM_UTF8:
                    source.seek(0)
                first = False
            line = source.readline(limit + 1)
            if not line:
                return
            if len(line) > limit:
                _too_large(limit)
            if not line.strip():
                continue
            row = json.loads(
                line.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_invalid_constant,
            )
            if not isinstance(row, dict):
                falha("Cada registro JSONL deve ser um objeto.")
            _validate_jsonl(row)
            yield row


def iter_registros(
    path: str,
    formato: str,
    max_columns: int = 100,
    max_record_bytes: int = 1048576,
) -> Iterator[dict]:
    """Yield validated dictionaries, limiting each row and the column union.

    Supported formats: csv, json, jsonl and ndjson (case-insensitive, optional
    leading dot). Null *values* and nested data are preserved. Empty inputs
    are invalid. There is no file-size or row-count cap, nor implicit inference.
    CSV decoding errors beyond the encoding sample are rejected, not replayed.
    Errors use the legacy HTTPException(422); filesystem errors propagate.
    """
    for name, limit in (("max_columns", max_columns), ("max_record_bytes", max_record_bytes)):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError(name + " deve ser um inteiro positivo.")
    if not isinstance(formato, str):
        falha("Formato de importacao invalido.")
    formato = formato.strip().lower().lstrip(".")
    if formato == "csv":
        rows = _iter_csv(path, max_columns, max_record_bytes)
    elif formato == "json":
        rows = _iter_json(path, max_columns, max_record_bytes)
    elif formato in {"jsonl", "ndjson"}:
        rows = _iter_jsonl(path, max_record_bytes)
    else:
        falha("Selecione CSV, JSON, JSONL ou NDJSON.")
    seen = set()
    count = 0
    try:
        for row in rows:
            columns = _keys(row, max_columns)
            seen.update(columns)
            if len(seen) > max_columns:
                falha("Uniao de colunas excede o limite de " + str(max_columns) + ".")
            count += 1
            yield row
        if not count:
            falha("Informe pelo menos um registro.")
    except (UnicodeError, csv.Error, ijson.JSONError, ValueError, OverflowError, RecursionError) as exc:
        falha("Arquivo " + formato.upper() + " invalido: " + str(exc))
    finally:
        rows.close()
