# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
# Copyright (C) 2025  Carlos Eduardo Carvalho Amand
#
# Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU GPL), conforme publicada
# pela Free Software Foundation, na versão 3 da Licença, ou (a seu critério)
# qualquer versão posterior.
#
# Este programa é distribuído na esperança de que seja útil,
# mas SEM QUALQUER GARANTIA; sem mesmo a garantia implícita de
# COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM PROPÓSITO PARTICULAR.
# Veja a Licença Pública Geral GNU para mais detalhes.
#
# Você deve ter recebido uma cópia da GNU GPL junto com este programa.
# Caso contrário, veja <https://www.gnu.org/licenses/>.

# negocio/premis.py
from __future__ import annotations
import json, csv
from pathlib import Path
from datetime import datetime
from typing import Iterable, List, Tuple, Optional, Any

# ---------------- Leitura / escrita de eventos PREMIS ----------------

def read_events(path: Path, limit: int | None = None) -> List[dict]:
    """Lê um arquivo JSONL de eventos PREMIS e retorna uma lista de dicts."""
    items: List[dict] = []
    p = Path(path)
    if not p.exists():
        return items
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
            if limit and len(items) >= limit:
                break
    return items

def append_event(log_path: Path, evt: dict) -> None:
    """Acrescenta um evento PREMIS (dict) ao JSONL de log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")

def export_csv(path_csv: Path, rows: Iterable[Tuple[str, ...]]) -> None:
    """Exporta linhas de eventos já formatadas para CSV."""
    with Path(path_csv).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "eventDateTime", "eventType", "eventOutcome",
            "linkingObjectIdentifier", "eventDetail",
            "linkingAgentName", "eventIdentifier"
        ])
        for r in rows:
            w.writerow(r)

# ---------------- Utilidades de filtro/ordenação ----------------

def unique_sorted(values: Iterable[Any]) -> List[str]:
    return sorted([v for v in set(values) if v not in (None, "")], key=lambda x: str(x).lower())

def parse_iso_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return datetime.fromisoformat(s + "T00:00:00+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        if s.endswith("Z"):
            try:
                return datetime.fromisoformat(s[:-1])
            except Exception:
                return None
        return None

def in_range(evt_dt: str, date_from: str, date_to: str) -> bool:
    if not date_from and not date_to:
        return True
    d = parse_iso_dt(evt_dt)
    if not d:
        return False
    if date_from:
        df = parse_iso_dt(date_from)
        if df and d < df:
            return False
    if date_to:
        end_str = date_to
        if len(date_to) == 10:
            end_str = date_to + "T23:59:59+00:00"
        dt = parse_iso_dt(end_str)
        if dt and d > dt:
            return False
    return True

def event_row(evt: dict) -> Tuple[str, str, str, str, str, str, str]:
    return (
        str(evt.get("eventDateTime", "")),
        str(evt.get("eventType", "")),
        str(evt.get("eventOutcome", "")),
        str(evt.get("linkingObjectIdentifier", "")),
        str(evt.get("eventDetail", "")),
        str(evt.get("linkingAgentName", "")),
        str(evt.get("eventIdentifier", "")),
    )

def sort_key(col_idx: int, row: Tuple[str, ...]):
    """Chave de ordenação para a tabela (0=data, demais=texto)."""
    val = row[col_idx]
    if col_idx == 0:
        dt = parse_iso_dt(val)
        return dt or val
    return (val or "").lower()

# ---------------- Ajuda para gerar eventos a partir de jobs ----------------

_JOBTYPE_TO_EVENTTYPE = {
    "HASH_MANIFEST": "message digest calculation",
    "VERIFY_FIXITY": "fixity check",
    "BUILD_BAG": "packaging",
    "BUILD_SIP": "ingestion preparation",
    "FORMAT_IDENTIFY": "format identification",
    "REPLICATE": "replication",
}

def event_type_for_job(job_type: str) -> str:
    return _JOBTYPE_TO_EVENTTYPE.get(job_type, job_type.lower())

def guess_object_id(job_type: str, params: dict) -> str:
    if job_type in ("HASH_MANIFEST", "FORMAT_IDENTIFY"):
        return params.get("raiz", "")
    if job_type == "VERIFY_FIXITY":
        return params.get("manifesto", "")
    if job_type == "BUILD_BAG":
        return params.get("bag_name", "") or params.get("destino", "")
    if job_type == "BUILD_SIP":
        return params.get("sip_id", "") or params.get("saida", "")
    if job_type == "REPLICATE":
        return params.get("fonte", "")
    if job_type == "PREMIS_EVENT":
        return params.get("obj_id", "")
    return ""
