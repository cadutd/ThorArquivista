"""Streaming parser contracts; no database, S3, or application startup required."""
import builtins
import csv
import io
import json

import pytest
from fastapi import HTTPException

from app.services import importacao_arquivo as legacy
from app.services import importacao_stream as stream


def source(tmp_path, content):
    path = tmp_path / "source"
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return str(path)


def parse(tmp_path, content, formato="csv", **kwargs):
    return list(stream.iter_registros(source(tmp_path, content), formato, **kwargs))


@pytest.mark.parametrize("separator", [",", ";", "\t", "|"])
def test_csv_delimiters(tmp_path, separator):
    content = separator.join(["nome", "porto"]) + "\n" + separator.join(["Ana", "Santos"]) + "\n"
    assert parse(tmp_path, content) == [{"nome": "Ana", "porto": "Santos"}]


def test_csv_bom_trimmed_unique_headers(tmp_path):
    assert parse(tmp_path, "\ufeff nome ; porto \r\nAna;Santos\r\n") == [
        {"nome": "Ana", "porto": "Santos"},
    ]


def test_csv_cp1252_sample_and_restart(tmp_path):
    content = "nome;cidade\nJo\u00e3o;Bel\u00e9m\n"
    assert parse(tmp_path, content.encode("cp1252")) == [{"nome": "Jo\u00e3o", "cidade": "Bel\u00e9m"}]


def test_csv_multiline_quotes_and_crlf(tmp_path):
    assert parse(tmp_path, 'nome,nota\r\n"Ana\r\nMaria","disse ""oi"", sim"\r\n') == [
        {"nome": "Ana\r\nMaria", "nota": 'disse "oi", sim'},
    ]


def test_csv_blank_lines_and_fields(tmp_path):
    assert parse(tmp_path, "a;b\n\n ; \nx;\n") == [{"a": "x", "b": ""}]


@pytest.mark.parametrize("content", [
    b"", b"a\n", b"\n", b",b\nx,y\n", b"a,a\nx,y\n",
    b" a ,a\nx,y\n", b"a,b\nx\n", b"a,b\nx,y,z\n",
    b'a\n"unfinished\n', b'a\n"x"garbage\n',
    b"a\x00\nx\n", b"a\nx\x00\n", ("a" * 256 + "\nx\n").encode(),
])
def test_csv_rejects_invalid_input(tmp_path, content):
    with pytest.raises(HTTPException) as exc:
        parse(tmp_path, content)
    assert exc.value.status_code == 422


def test_csv_large_field_below_record_cap_and_global_limit_restored(tmp_path):
    previous = csv.field_size_limit()
    assert parse(tmp_path, b"a\n" + b"x" * 200000)[0]["a"] == "x" * 200000
    assert csv.field_size_limit() == previous


def test_csv_field_limit_restored_on_error(tmp_path):
    previous = csv.field_size_limit()
    with pytest.raises(HTTPException):
        parse(tmp_path, b'a\n"' + b"x" * 200000)
    assert csv.field_size_limit() == previous


@pytest.mark.parametrize("content", [
    b"a\n" + b"x" * 1048577,
    b"a,b\n" + b"x" * 600000 + b"," + b"y" * 600000,
    b'a\n"' + (b"x\n" * 530000) + b'"',
    b"x" * 1048577 + b"\nx\n",
], ids=["single-field", "aggregate-fields", "multiline", "header"])
def test_csv_default_byte_cap_including_whole_multiline_record(tmp_path, content):
    with pytest.raises(HTTPException):
        parse(tmp_path, content)


def test_csv_exact_limit_and_multibyte_source_bytes(tmp_path):
    assert parse(tmp_path, b"a\n12345678", max_record_bytes=8) == [{"a": "12345678"}]
    with pytest.raises(HTTPException) as exc:
        parse(tmp_path, "a\n\u00e9\u00e9\u00e9", max_record_bytes=5)
    assert "5 bytes" in exc.value.detail


def test_csv_large_file_has_no_legacy_row_limit(tmp_path):
    assert len(parse(tmp_path, "a\n" + "x\n" * 3000)) == 3000


@pytest.mark.parametrize("prefix,suffix", [
    ("[", "]"), ('{"registros":[', "]}"), ('{"items":[', "]}"),
])
def test_json_supported_roots_and_nested_data(tmp_path, prefix, suffix):
    row = {"nome": "Ana", "dados": [{"n": [1, None, True]}, ["a", "b"]]}
    assert parse(tmp_path, prefix + json.dumps(row) + suffix, "json") == [row]


def test_json_utf8_bom(tmp_path):
    assert parse(tmp_path, '\ufeff[{"nome":"Jo\u00e3o"}]', "json") == [{"nome": "Jo\u00e3o"}]


def test_json_wrapper_metadata_is_validated_not_imported(tmp_path):
    content = '{"meta":{"ok":true},"items":[{"a":1}],"total":1}'
    assert parse(tmp_path, content, "json") == [{"a": 1}]


@pytest.mark.parametrize("content", [
    b"", b" ", b"[]", b"{}", b'{"items":[]}', b"[",
    b'[{"a":1}', b'[{"a":1},]', b'{"items":[{"a":1}]',
    b'{"items":{}}', b'{"items":null}', b'{"other":[]}',
    b'[null]', b'[1]', b'["x"]', b'[[{"a":1}]]',
    b'[{"a":1},null]', b'[{"a":1}] trailing', b'[{"a":1}] {}',
    b'{"items":[{"a":1}]} garbage', b'{"items":[{"a":1}],"bad":[null,]}',
    b'{"items":[{"a":1}],"items":[{"a":2}]}',
    b'{"items":[{"a":1}],"registros":[{"b":2}]}',
    b'[{"a":1,"a":2}]', b'[{"x":{"a":1,"a":2}}]',
    b'[{"x":[{"a":1,"a":2}]}]',
    b'{"items":[{"a":1}],"meta":{"x":1,"x":2}}',
    b'[{"":1}]', b'[{" ":1}]', b'[{"\\u0000":1}]', b'[{null:1}]',
    b'[{"a":"\\u0000"}]', b'[{"a":NaN}]', b'[{"a":Infinity}]',
    b'[{"a":1e400}]', b'[{"a":01}]', b'[{"a":1/*comment*/}]',
    b'[{"a":"\xe9"}]', ('[{"' + "x" * 256 + '":1}]').encode(),
])
def test_json_rejects_malformed_invalid_or_duplicate_data(tmp_path, content):
    with pytest.raises(HTTPException) as exc:
        parse(tmp_path, content, "json")
    assert exc.value.status_code == 422


@pytest.mark.parametrize("formato,content", [
    ("json", '[{"i":1208925819614629174706176,"f":1.25,"z":null}]'),
    ("jsonl", '{"i":1208925819614629174706176,"f":1.25,"z":null}'),
])
def test_numbers_are_exact_integers_and_json_serializable_floats(tmp_path, formato, content):
    row = parse(tmp_path, content, formato)[0]
    assert row["i"] == 2**80 and type(row["i"]) is int
    assert row["f"] == 1.25 and type(row["f"]) is float
    assert row["z"] is None
    assert json.loads(stream.converter(row, "TEXTO_LONGO")) == row


@pytest.mark.parametrize("formato", ["jsonl", "ndjson", ".NDJSON"])
def test_jsonl_aliases_bom_blank_lines_and_nested_values(tmp_path, formato):
    content = '\ufeff{"a":[{"x":1}]}\r\n\n{"a":null}\n'
    assert parse(tmp_path, content, formato) == [{"a": [{"x": 1}]}, {"a": None}]


@pytest.mark.parametrize("content", [
    b"", b"\n \n", b"null\n", b"[]\n", b"1\n", b'{"a":1}\n{"a":',
    b'{"a":1} {"b":2}\n', b'{"a":1,"a":2}\n', b'{"x":{"a":1,"a":2}}\n',
    b'{"":1}\n', b'{"a":NaN}\n', b'{"a":1e400}\n', b'{"a":"\x00"}\n',
    b'{"a":"\xe9"}\n', b'{"a":"\\u0000"}\n', b'{\n"a":1\n}\n',
])
def test_jsonl_rejects_malformed_and_nonobjects(tmp_path, content):
    with pytest.raises(HTTPException) as exc:
        parse(tmp_path, content, "jsonl")
    assert exc.value.status_code == 422


@pytest.mark.parametrize("formato,content", [
    ("csv", b"a,b\nx,y\n"),
    ("json", b'[{"a":1,"b":2}]'),
    ("jsonl", b'{"a":1,"b":2}\n'),
])
def test_configurable_column_limit_per_row(tmp_path, formato, content):
    assert parse(tmp_path, content, formato, max_columns=2)
    with pytest.raises(HTTPException):
        parse(tmp_path, content, formato, max_columns=1)


@pytest.mark.parametrize("formato,content", [
    ("json", b'[{"a":1},{"b":2},{"c":3}]'),
    ("jsonl", b'{"a":1}\n{"b":2}\n{"c":3}\n'),
])
def test_total_column_union_is_limited(tmp_path, formato, content):
    rows = stream.iter_registros(source(tmp_path, content), formato, max_columns=2)
    assert next(rows) == {"a": 1}
    assert next(rows) == {"b": 2}
    with pytest.raises(HTTPException) as exc:
        next(rows)
    assert "Uniao" in exc.value.detail


def test_json_nested_keys_are_data_not_flattened_columns(tmp_path):
    row = {"data": {str(n): n for n in range(200)}}
    assert parse(tmp_path, json.dumps([row]), "json", max_columns=1) == [row]


@pytest.mark.parametrize("formato", ["json", "jsonl"])
def test_default_hundred_column_limit(tmp_path, formato):
    row = {str(n): n for n in range(101)}
    content = json.dumps([row] if formato == "json" else row)
    with pytest.raises(HTTPException):
        parse(tmp_path, content, formato)


@pytest.mark.parametrize("wrapper", [False, True])
def test_json_exact_object_byte_limit_independent_of_framing(tmp_path, wrapper):
    row = b'{"a":"12345678"}'
    content = b'{"registros":[' + row + b"]}" if wrapper else b"[" + row + b"]"
    assert parse(tmp_path, content, "json", max_record_bytes=len(row)) == [{"a": "12345678"}]
    with pytest.raises(HTTPException) as exc:
        parse(tmp_path, content, "json", max_record_bytes=len(row) - 1)
    assert "bytes" in exc.value.detail


def test_json_escaped_structural_characters_do_not_confuse_framing(tmp_path):
    row = {"v": '{}[]\\" \u00e9', "nested": [{"q": "\\\\"}]}
    content = json.dumps([row], ensure_ascii=False).encode()
    size = len(json.dumps(row, ensure_ascii=False).encode())
    assert parse(tmp_path, content, "json", max_record_bytes=size) == [row]


@pytest.mark.parametrize("row", [
    b'{"a":"' + b"x" * 1048576 + b'"}',
    b'{"a":"' + b"\\u0061" * 180000 + b'"}',
    b'{"a":[' + b"0," * 530000 + b"0]}",
    b'{"a":' + b" " * 1048576 + b"1}",
    b'{"a":"' + b"x" * 1048576,  # Unfinished tokens must also hit the byte cap.
], ids=["large-string", "escaped-string", "array", "whitespace", "unfinished-string"])
def test_json_default_cap_checks_raw_bytes_not_just_final_object(tmp_path, row):
    with pytest.raises(HTTPException) as exc:
        parse(tmp_path, b"[" + row + b"]", "json")
    assert "1048576 bytes" in exc.value.detail


def test_jsonl_bounded_lines_and_exact_limit(tmp_path):
    row = b'{"a":"x"}'
    assert parse(tmp_path, row, "jsonl", max_record_bytes=len(row)) == [{"a": "x"}]
    with pytest.raises(HTTPException):
        parse(tmp_path, row + b"\n", "jsonl", max_record_bytes=len(row))
    with pytest.raises(HTTPException):
        parse(tmp_path, b'{"a":"' + b"x" * 1048576 + b'"}', "jsonl")


@pytest.mark.parametrize("formato", ["json", "jsonl"])
def test_deep_nesting_is_rejected_with_controlled_error(tmp_path, formato):
    row = '{"a":' + "[" * 150 + "0" + "]" * 150 + "}"
    with pytest.raises(HTTPException):
        parse(tmp_path, "[" + row + "]" if formato == "json" else row, formato)


class TrackedReader(io.BufferedReader):
    def __init__(self, path):
        super().__init__(builtins.open(path, "rb", buffering=0))
        self.bytes_read = 0

    def read(self, size=-1):
        assert size >= 0, "Unbounded read"
        data = super().read(size)
        self.bytes_read += len(data)
        return data

    def read1(self, size=-1):
        assert size >= 0, "Unbounded read1"
        data = super().read1(size)
        self.bytes_read += len(data)
        return data

    def readline(self, size=-1):
        assert size >= 0, "Unbounded readline"
        data = super().readline(size)
        self.bytes_read += len(data)
        return data


def track_open(monkeypatch):
    opened = []

    def tracked(path, mode):
        assert mode == "rb"
        file = TrackedReader(path)
        opened.append(file)
        return file

    monkeypatch.setattr(stream, "open", tracked, raising=False)
    return opened


@pytest.mark.parametrize("formato", ["csv", "json", "jsonl"])
def test_streams_first_row_without_reading_file_and_closes_on_abort(tmp_path, monkeypatch, formato):
    if formato == "csv":
        content = b"a\n" + b"x\n" * 200000
    elif formato == "json":
        content = b"[" + b'{"a":1},' * 200000 + b'{"a":1}]'
    else:
        content = b'{"a":1}\n' * 200000
    path = source(tmp_path, content)
    opened = track_open(monkeypatch)
    rows = stream.iter_registros(path, formato)
    assert next(rows) == {"a": "x" if formato == "csv" else 1}
    assert len(opened) == 1 and not opened[0].closed
    assert opened[0].bytes_read < len(content) // 2
    rows.close()
    assert opened[0].closed


@pytest.mark.parametrize("formato", ["csv", "json", "jsonl"])
def test_oversized_unterminated_record_stops_reading_early(tmp_path, monkeypatch, formato):
    prefix = {"csv": b'a\n"', "json": b'[{"a":"', "jsonl": b'{"a":"'}[formato]
    path = source(tmp_path, prefix + b"x" * (3 * 1048576))
    opened = track_open(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        list(stream.iter_registros(path, formato, max_record_bytes=256))
    assert "256 bytes" in exc.value.detail
    assert opened[0].bytes_read <= 2 * stream._SAMPLE_BYTES
    assert opened[0].closed


@pytest.mark.parametrize("formato,content", [
    ("csv", b"a,b\nx,y\nz\n"),
    ("json", b'[{"a":1},null]'),
    ("json", b'[{"a":1}]garbage'),
    ("jsonl", b'{"a":1}\nnot-json\n'),
])
def test_failure_after_a_valid_row_is_not_silently_ignored(tmp_path, formato, content):
    rows = stream.iter_registros(source(tmp_path, content), formato)
    assert isinstance(next(rows), dict)
    with pytest.raises(HTTPException):
        list(rows)


def test_json_large_file_and_many_rows_are_not_legacy_limited(tmp_path):
    row = b'{"a":"' + b"x" * 1000 + b'"}'
    content = b"[" + b",".join([row] * 6000) + b"]"
    assert len(parse(tmp_path, content, "json")) == 6000


@pytest.mark.parametrize("kwargs", [
    {"max_columns": 0}, {"max_columns": True}, {"max_columns": 1.5},
    {"max_record_bytes": 0}, {"max_record_bytes": -1}, {"max_record_bytes": None},
])
def test_invalid_configuration_is_value_error(tmp_path, kwargs):
    with pytest.raises(ValueError):
        parse(tmp_path, b"a\nx", **kwargs)


@pytest.mark.parametrize("formato", ["xml", "", None])
def test_unsupported_format(tmp_path, formato):
    with pytest.raises(HTTPException):
        parse(tmp_path, b"a\nx", formato)


def test_missing_file_propagates_os_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(stream.iter_registros(str(tmp_path / "missing"), "json"))


def test_reuses_legacy_conversion_and_inference_functions():
    assert stream.converter is legacy.converter
    assert stream.sugerir_tipo is legacy.sugerir_tipo
    assert stream.chave_sugerida is legacy.chave_sugerida


def test_utf8_sample_may_end_in_middle_of_multibyte_character(tmp_path):
    content = b"a\n" + b"x" * (stream._SAMPLE_BYTES - 3) + "\u00e9\n".encode()
    row = parse(tmp_path, content)[0]
    assert row["a"].endswith("\u00e9")


def test_late_csv_decoding_failure_does_not_replay_already_emitted_rows(tmp_path):
    content = b"a\n" + b"x\n" * 40000 + b"\xe9\n"
    with pytest.raises(HTTPException):
        list(stream.iter_registros(source(tmp_path, content), "csv"))


@pytest.mark.parametrize("formato", ["csv", "json", "jsonl"])
def test_default_limit_accepts_record_at_exactly_one_mib(tmp_path, formato):
    limit = 1048576
    if formato == "csv":
        content = b"a\n" + b"x" * limit
        expected = "x" * limit
    else:
        row = b'{"a":"' + b"x" * (limit - len(b'{"a":""}')) + b'"}'
        content = b"[" + row + b"]" if formato == "json" else row
        expected = "x" * (limit - len(b'{"a":""}'))
    assert parse(tmp_path, content, formato)[0]["a"] == expected


def test_csv_default_hundred_column_header_limit(tmp_path):
    headers = ",".join("c" + str(n) for n in range(101))
    values = ",".join("x" for _ in range(101))
    with pytest.raises(HTTPException):
        parse(tmp_path, headers + "\n" + values)


@pytest.mark.parametrize("formato", ["json", "jsonl"])
def test_nested_invalid_keys_are_not_ignored(tmp_path, formato):
    row = '{"a":[{"":1}]}'
    with pytest.raises(HTTPException):
        parse(tmp_path, "[" + row + "]" if formato == "json" else row, formato)


def test_json_invalid_wrapper_metadata_before_rows(tmp_path):
    with pytest.raises(HTTPException):
        parse(tmp_path, '{"meta":{"x":1,"x":2},"items":[{"a":1}]}', "json")
