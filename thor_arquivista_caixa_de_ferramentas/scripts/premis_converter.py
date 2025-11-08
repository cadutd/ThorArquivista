# Thor Arquivista – Caixa de Ferramentas de Preservação Digital
# Copyright (C) 2025  Carlos Eduardo Carvalho Amand
# Copyright (C) 2025  Tatiana Canelhas
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


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
premis_converter.py — Conversor/validador PREMIS 3.0 (XML ⇄ JSON ⇄ CSV)
alinhado ao padrão de CSV do projeto (prefixos ob./ev./ag./rt. e colunas de linking).

Uso:
  # Validar XML
  python premis_converter.py --in premis.xml --validate

  # Converter
  python premis_converter.py --in premis.xml  --out premis.csv
  python premis_converter.py --in premis.csv  --out premis.json
  python premis_converter.py --in premis.json --out premis.xml --validate

  # Gerar exemplos no padrão do projeto
  python premis_converter.py --example

Requisitos:
  - lxml
  - negocio/premisXML.py (PremisBuilder, Identifier, DEFAULT_SCHEMA_PATH)
"""

from __future__ import annotations

# --- bootstrap de import para rodar diretamente a partir de scripts/ ---
from pathlib import Path
import sys

# pasta .../thor_arquivista_caixa_de_ferramentas/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# -----------------------------------------------------------------------

import argparse
import csv
import json
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lxml import etree
from negocio.premisXML import PremisBuilder, Identifier, DEFAULT_SCHEMA_PATH

# -----------------------------------------------------------
# Configurações de escrita no estilo do projeto
# -----------------------------------------------------------
MAX_LINKS = 5  # número máximo de repetições exportadas por tipo de link no CSV

# Cabeçalhos "estilo do projeto" — serão usados na exportação
CSV_HEADERS_PROJECT = [
    "entity",

    # OBJECT (ob.*)
    "ob.objectCategory",
    "ob.objectIdentifierType",
    "ob.objectIdentifierValue",
    "ob.originalName",
    "ob.size",
    "ob.format.formatDesignation.formatName",
    "ob.format.formatDesignation.formatVersion",
    "ob.messageDigestAlgorithm",
    "ob.messageDigest",
    # links do object — padrão 1 ocorrência
    "linkingEventIdentifierType",
    "linkingEventIdentifierValue",
    "linkingRightsStatementIdentifierType",
    "linkingRightsStatementIdentifierValue",

    # EVENT (ev.*)
    "ev.eventIdentifierType",
    "ev.eventIdentifierValue",
    "ev.eventType",
    "ev.eventDateTime",
    "ev.eventDetailInformation.eventDetail",
    "ev.eventOutcomeInformation.eventOutcome",
    "ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote",
]

# Acrescenta colunas numeradas para múltiplos links de event
for i in range(1, MAX_LINKS + 1):
    CSV_HEADERS_PROJECT += [
        f"ev.linkingObjectIdentifierType_{i}",
        f"ev.linkingObjectIdentifierValue_{i}",
        f"ev.linkingObjectIdentifierRole_{i}",
    ]
for i in range(1, MAX_LINKS + 1):
    CSV_HEADERS_PROJECT += [
        f"ev.linkingAgentIdentifierType_{i}",
        f"ev.linkingAgentIdentifierValue_{i}",
        f"ev.linkingAgentRole_{i}",
    ]

# AGENT (ag.*)
CSV_HEADERS_PROJECT += [
    "ag.agentIdentifierType",
    "ag.agentIdentifierValue",
    "ag.agentName",
    "ag.agentType",
    "ag.agentVersion",
]

# RIGHTS (rt.*) + links numerados
CSV_HEADERS_PROJECT += [
    "rt.rightsStatementIdentifierType",
    "rt.rightsStatementIdentifierValue",
    "rt.rightsBasis",
    "rt.otherRightsBasis",
    "rt.otherRightsNote",
    "rt.act",
    "rt.restriction",
    "rt.copyrightStatus",
    "rt.copyrightJurisdiction",
    "rt.copyrightNote",
]
for i in range(1, MAX_LINKS + 1):
    CSV_HEADERS_PROJECT += [
        f"rt.linkingObjectIdentifierType_{i}",
        f"rt.linkingObjectIdentifierValue_{i}",
        f"rt.linkingObjectRole_{i}",
    ]
for i in range(1, MAX_LINKS + 1):
    CSV_HEADERS_PROJECT += [
        f"rt.linkingAgentIdentifierType_{i}",
        f"rt.linkingAgentIdentifierValue_{i}",
        f"rt.linkingAgentRole_{i}",
    ]

# -----------------------------------------------------------
# Utilidades gerais
# -----------------------------------------------------------
NBSP = "\xa0"

def norm_header(s: str) -> str:
    """Normaliza cabeçalhos: troca NBSP por espaço e remove espaços extras."""
    return re.sub(r"\s+", " ", (s or "").replace(NBSP, " ")).strip()

def detect_format(p: Path) -> str:
    ext = p.suffix.lower()
    if ext == ".xml": return "xml"
    if ext == ".json": return "json"
    if ext == ".csv": return "csv"
    raise ValueError(f"Formato não suportado para: {p.name}")

def split_list(s: Optional[str]) -> List[str]:
    if not s: return []
    return [x.strip() for x in str(s).split(";") if str(x).strip()]

def parse_fixities_from_alg_and_digest(alg: str, dig: str) -> List[Tuple[str, str]]:
    """Monta lista [('alg','digest')] a partir de duas colunas simples do CSV do projeto."""
    alg = (alg or "").strip()
    dig = (dig or "").strip()
    return [(alg, dig)] if (alg and dig) else []

def parse_link_triplets(s: Optional[str]) -> List[Tuple[Identifier, Optional[str]]]:
    """
    'type:value:role;type:value' -> [(Identifier(...),'role'),(...,None)]
    """
    out: List[Tuple[Identifier, Optional[str]]] = []
    for part in split_list(s):
        bits = part.split(":")
        if len(bits) >= 2:
            id_type = bits[0].strip()
            id_value = bits[1].strip()
            role = bits[2].strip() if len(bits) >= 3 and bits[2].strip() else None
            out.append((Identifier(id_type, id_value), role))
    return out

def _collect_repeat_links(row: Dict[str,str], type_key: str, value_key: str, role_key: Optional[str]=None) -> List[Tuple[str,str,str]]:
    """
    Coleta pares (type,value,role) quando o CSV traz múltiplas colunas com o mesmo nome
    (ou nomes numerados) para o mesmo tipo de vínculo. Usa sufixos _1.._N se existirem.
    Também aceita as chaves "puras" (sem sufixo) para o primeiro.
    """
    out: List[Tuple[str,str,str]] = []
    # Primeiro, tenta capturar a "pura"
    t0 = (row.get(type_key, "") or "").strip()
    v0 = (row.get(value_key, "") or "").strip()
    r0 = (row.get(role_key, "") or "").strip() if role_key else ""
    if t0 and v0:
        out.append((t0, v0, r0))
    # Agora percorre sufixos numerados
    for i in range(1, MAX_LINKS + 1):
        t = (row.get(f"{type_key}_{i}", "") or "").strip()
        v = (row.get(f"{value_key}_{i}", "") or "").strip()
        r = (row.get(f"{role_key}_{i}", "") or "").strip() if role_key else ""
        if t and v:
            out.append((t, v, r))
    return out

# -----------------------------------------------------------
# Modelo plano interno
# -----------------------------------------------------------
class FlatRecord:
    def __init__(self, entity: str, data: Dict[str, Any]):
        self.entity = entity
        self.data = data

# -----------------------------------------------------------
# XML -> FlatRecords
# -----------------------------------------------------------
def xml_to_records(xml_path: Path) -> List[FlatRecord]:
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    ns = {"p": "http://www.loc.gov/premis/v3"}

    records: List[FlatRecord] = []

    # OBJECT
    for obj in root.findall("p:object", ns):
        d: Dict[str, Any] = {}
        d["ob.objectCategory"] = obj.get("category") or ""

        oid = obj.find("p:objectIdentifier", ns)
        if oid is not None:
            d["ob.objectIdentifierType"]  = oid.findtext("p:objectIdentifierType", default="", namespaces=ns)
            d["ob.objectIdentifierValue"] = oid.findtext("p:objectIdentifierValue", default="", namespaces=ns)

        d["ob.originalName"] = obj.findtext("p:originalName", default="", namespaces=ns)

        oc = obj.find("p:objectCharacteristics", ns)
        if oc is not None:
            d["ob.size"] = oc.findtext("p:size", default="", namespaces=ns)
            # fixity → (alg,digest)
            fx = oc.find("p:fixity", ns)
            if fx is not None:
                d["ob.messageDigestAlgorithm"] = fx.findtext("p:messageDigestAlgorithm", default="", namespaces=ns)
                d["ob.messageDigest"]          = fx.findtext("p:messageDigest", default="", namespaces=ns)
            else:
                d["ob.messageDigestAlgorithm"] = ""
                d["ob.messageDigest"] = ""
            # format
            fmt = oc.find("p:format", ns)
            if fmt is not None:
                des = fmt.find("p:formatDesignation", ns)
                if des is not None:
                    d["ob.format.formatDesignation.formatName"]    = des.findtext("p:formatName", default="", namespaces=ns)
                    d["ob.format.formatDesignation.formatVersion"] = des.findtext("p:formatVersion", default="", namespaces=ns)
                else:
                    d["ob.format.formatDesignation.formatName"]    = ""
                    d["ob.format.formatDesignation.formatVersion"] = ""
            else:
                d["ob.format.formatDesignation.formatName"]    = ""
                d["ob.format.formatDesignation.formatVersion"] = ""

        # links a eventos/rights (uma ocorrência “padrão”)
        le = obj.find("p:linkingEventIdentifier", ns)
        d["linkingEventIdentifierType"]  = le.findtext("p:linkingEventIdentifierType", default="", namespaces=ns) if le is not None else ""
        d["linkingEventIdentifierValue"] = le.findtext("p:linkingEventIdentifierValue", default="", namespaces=ns) if le is not None else ""

        lr = obj.find("p:linkingRightsStatementIdentifier", ns)
        d["linkingRightsStatementIdentifierType"]  = lr.findtext("p:linkingRightsStatementIdentifierType", default="", namespaces=ns) if lr is not None else ""
        d["linkingRightsStatementIdentifierValue"] = lr.findtext("p:linkingRightsStatementIdentifierValue", default="", namespaces=ns) if lr is not None else ""

        records.append(FlatRecord("object", d))

    # EVENT
    for ev in root.findall("p:event", ns):
        d: Dict[str, Any] = {}
        eid = ev.find("p:eventIdentifier", ns)
        if eid is not None:
            d["ev.eventIdentifierType"]  = eid.findtext("p:eventIdentifierType", default="", namespaces=ns)
            d["ev.eventIdentifierValue"] = eid.findtext("p:eventIdentifierValue", default="", namespaces=ns)

        d["ev.eventType"]     = ev.findtext("p:eventType",     default="", namespaces=ns)
        d["ev.eventDateTime"] = ev.findtext("p:eventDateTime", default="", namespaces=ns)

        edi = ev.find("p:eventDetailInformation", ns)
        d["ev.eventDetailInformation.eventDetail"] = edi.findtext("p:eventDetail", default="", namespaces=ns) if edi is not None else ""

        eoi = ev.find("p:eventOutcomeInformation", ns)
        if eoi is not None:
            d["ev.eventOutcomeInformation.eventOutcome"] = eoi.findtext("p:eventOutcome", default="", namespaces=ns)
            eod = eoi.find("p:eventOutcomeDetail", ns)
            d["ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote"] = eod.findtext("p:eventOutcomeDetailNote", default="", namespaces=ns) if eod is not None else ""
        else:
            d["ev.eventOutcomeInformation.eventOutcome"] = ""
            d["ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote"] = ""

        # Links — exporta até MAX_LINKS
        los: List[Tuple[str,str,str]] = []
        for x in ev.findall("p:linkingObjectIdentifier", ns):
            t = x.findtext("p:linkingObjectIdentifierType", default="", namespaces=ns)
            v = x.findtext("p:linkingObjectIdentifierValue", default="", namespaces=ns)
            r = x.findtext("p:linkingObjectRole", default="", namespaces=ns)
            if t and v:
                los.append((t,v,r))
        las: List[Tuple[str,str,str]] = []
        for x in ev.findall("p:linkingAgentIdentifier", ns):
            t = x.findtext("p:linkingAgentIdentifierType", default="", namespaces=ns)
            v = x.findtext("p:linkingAgentIdentifierValue", default="", namespaces=ns)
            r = x.findtext("p:linkingAgentRole", default="", namespaces=ns)
            if t and v:
                las.append((t,v,r))

        for i in range(MAX_LINKS):
            t, v, r = los[i] if i < len(los) else ("", "", "")
            d[f"ev.linkingObjectIdentifierType_{i+1}"]  = t
            d[f"ev.linkingObjectIdentifierValue_{i+1}"] = v
            d[f"ev.linkingObjectIdentifierRole_{i+1}"]  = r
            t, v, r = las[i] if i < len(las) else ("", "", "")
            d[f"ev.linkingAgentIdentifierType_{i+1}"]  = t
            d[f"ev.linkingAgentIdentifierValue_{i+1}"] = v
            d[f"ev.linkingAgentRole_{i+1}"]            = r

        records.append(FlatRecord("event", d))

    # AGENT
    for ag in root.findall("p:agent", ns):
        d: Dict[str, Any] = {}
        aid = ag.find("p:agentIdentifier", ns)
        if aid is not None:
            d["ag.agentIdentifierType"]  = aid.findtext("p:agentIdentifierType", default="", namespaces=ns)
            d["ag.agentIdentifierValue"] = aid.findtext("p:agentIdentifierValue", default="", namespaces=ns)
        d["ag.agentName"]    = ag.findtext("p:agentName",    default="", namespaces=ns)
        d["ag.agentType"]    = ag.findtext("p:agentType",    default="", namespaces=ns)
        d["ag.agentVersion"] = ag.findtext("p:agentVersion", default="", namespaces=ns) or ""
        records.append(FlatRecord("agent", d))

    # RIGHTS
    for rs in root.findall("p:rights", ns):
        rstmt = rs.find("p:rightsStatement", ns)
        if rstmt is None:
            continue
        d: Dict[str, Any] = {}
        rsi = rstmt.find("p:rightsStatementIdentifier", ns)
        if rsi is not None:
            d["rt.rightsStatementIdentifierType"]  = rsi.findtext("p:rightsStatementIdentifierType",  default="", namespaces=ns)
            d["rt.rightsStatementIdentifierValue"] = rsi.findtext("p:rightsStatementIdentifierValue", default="", namespaces=ns)

        basis = rstmt.findtext("p:rightsBasis", default="", namespaces=ns)
        d["rt.rightsBasis"] = basis
        d["rt.otherRightsBasis"] = ""
        d["rt.otherRightsNote"]  = ""

        # rightsGranted
        act_list, restr_list = [], []
        for rg in rstmt.findall("p:rightsGranted", ns):
            a = rg.findtext("p:act", default="", namespaces=ns)
            if a: act_list.append(a)
            for r in rg.findall("p:restriction", ns):
                txt = (r.text or "").strip()
                if txt: restr_list.append(txt)
        d["rt.act"]         = ";".join(act_list)
        d["rt.restriction"] = ";".join(restr_list)

        # copyrightInformation
        ci = rstmt.find("p:copyrightInformation", ns)
        if ci is not None:
            d["rt.copyrightStatus"]       = ci.findtext("p:copyrightStatus",       default="", namespaces=ns)
            d["rt.copyrightJurisdiction"] = ci.findtext("p:copyrightJurisdiction", default="", namespaces=ns)
            d["rt.copyrightNote"]         = ci.findtext("p:copyrightNote",         default="", namespaces=ns)
        else:
            d["rt.copyrightStatus"]       = ""
            d["rt.copyrightJurisdiction"] = ""
            d["rt.copyrightNote"]         = ""

        # links — exporta até MAX_LINKS
        los: List[Tuple[str,str,str]] = []
        for x in rstmt.findall("p:linkingObjectIdentifier", ns):
            t = x.findtext("p:linkingObjectIdentifierType", default="", namespaces=ns)
            v = x.findtext("p:linkingObjectIdentifierValue", default="", namespaces=ns)
            r = x.findtext("p:linkingObjectRole", default="", namespaces=ns)
            if t and v:
                los.append((t,v,r))
        las: List[Tuple[str,str,str]] = []
        for x in rstmt.findall("p:linkingAgentIdentifier", ns):
            t = x.findtext("p:linkingAgentIdentifierType", default="", namespaces=ns)
            v = x.findtext("p:linkingAgentIdentifierValue", default="", namespaces=ns)
            r = x.findtext("p:linkingAgentRole", default="", namespaces=ns)
            if t and v:
                las.append((t,v,r))

        for i in range(MAX_LINKS):
            t, v, r = los[i] if i < len(los) else ("", "", "")
            d[f"rt.linkingObjectIdentifierType_{i+1}"]  = t
            d[f"rt.linkingObjectIdentifierValue_{i+1}"] = v
            d[f"rt.linkingObjectRole_{i+1}"]            = r
            t, v, r = las[i] if i < len(las) else ("", "", "")
            d[f"rt.linkingAgentIdentifierType_{i+1}"]  = t
            d[f"rt.linkingAgentIdentifierValue_{i+1}"] = v
            d[f"rt.linkingAgentRole_{i+1}"]            = r

        records.append(FlatRecord("rights", d))

    return records

# -----------------------------------------------------------
# FlatRecords -> XML (via PremisBuilder)
# -----------------------------------------------------------
def _g(row: Dict[str, Any], key: str) -> str:
    return (row.get(key) or "").strip()

def records_to_xml(records: List[FlatRecord], schema_path: Optional[Path] = None) -> etree._ElementTree:
    pb = PremisBuilder(schema_path or DEFAULT_SCHEMA_PATH)

    for r in records:
        ent = r.entity.lower()
        d = r.data

        if ent == "object":
            oid = Identifier(_g(d, "ob.objectIdentifierType") or "local", _g(d, "ob.objectIdentifierValue"))
            fixities = parse_fixities_from_alg_and_digest(_g(d, "ob.messageDigestAlgorithm"), _g(d, "ob.messageDigest"))

            # links object → event/rights (uma ocorrência exportada)
            linking_events = []
            if _g(d, "linkingEventIdentifierType") and _g(d, "linkingEventIdentifierValue"):
                linking_events.append(Identifier(_g(d, "linkingEventIdentifierType"), _g(d, "linkingEventIdentifierValue")))

            linking_rights = []
            if _g(d, "linkingRightsStatementIdentifierType") and _g(d, "linkingRightsStatementIdentifierValue"):
                linking_rights.append(Identifier(_g(d, "linkingRightsStatementIdentifierType"), _g(d, "linkingRightsStatementIdentifierValue")))

            size_int = None
            sz = _g(d, "ob.size")
            if sz.isdigit():
                size_int = int(sz)

            pb.add_object_file(
                identifier=oid,
                original_name=_g(d, "ob.originalName") or None,
                size_bytes=size_int,
                format_name=_g(d, "ob.format.formatDesignation.formatName") or None,
                format_version=_g(d, "ob.format.formatDesignation.formatVersion") or None,
                fixities=fixities or None,
                linking_events=linking_events or None,
                linking_rights=linking_rights or None,
            )

        elif ent == "event":
            eid = Identifier(_g(d, "ev.eventIdentifierType") or "local", _g(d, "ev.eventIdentifierValue"))
            # Recolhe links numerados
            los, las = [], []
            for i in range(1, MAX_LINKS + 1):
                t = _g(d, f"ev.linkingObjectIdentifierType_{i}")
                v = _g(d, f"ev.linkingObjectIdentifierValue_{i}")
                rrole = _g(d, f"ev.linkingObjectIdentifierRole_{i}")
                if t and v:
                    los.append((Identifier(t, v), rrole or None))
                t = _g(d, f"ev.linkingAgentIdentifierType_{i}")
                v = _g(d, f"ev.linkingAgentIdentifierValue_{i}")
                rrole = _g(d, f"ev.linkingAgentRole_{i}")
                if t and v:
                    las.append((Identifier(t, v), rrole or None))

            pb.add_event(
                identifier=eid,
                event_type=_g(d, "ev.eventType"),
                event_datetime=_g(d, "ev.eventDateTime"),
                detail=_g(d, "ev.eventDetailInformation.eventDetail") or None,
                outcome=_g(d, "ev.eventOutcomeInformation.eventOutcome") or None,
                outcome_note=_g(d, "ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote") or None,
                linking_objects=los or None,
                linking_agents=las or None,
            )

        elif ent == "agent":
            aid = Identifier(_g(d, "ag.agentIdentifierType") or "local", _g(d, "ag.agentIdentifierValue"))
            pb.add_agent(
                identifier=aid,
                agent_name=_g(d, "ag.agentName"),
                agent_type=_g(d, "ag.agentType") or "software",
                agent_version=_g(d, "ag.agentVersion") or None,
            )

        elif ent == "rights":
            rid = Identifier(_g(d, "rt.rightsStatementIdentifierType") or "local", _g(d, "rt.rightsStatementIdentifierValue"))

            acts = []
            acts_list  = split_list(_g(d, "rt.act"))
            restr_list = split_list(_g(d, "rt.restriction"))
            notes_list = []
            if _g(d, "rt.otherRightsNote"):
                notes_list.append(_g(d, "rt.otherRightsNote"))

            term_grant = None
            term_restrict = None

            if acts_list or restr_list or notes_list:
                if acts_list:
                    for a in acts_list:
                        acts.append((a, restr_list or None, term_grant, term_restrict, notes_list or None))
                else:
                    acts.append(("", restr_list or None, term_grant, term_restrict, notes_list or None))

            # links numerados
            los, las = [], []
            for i in range(1, MAX_LINKS + 1):
                t = _g(d, f"rt.linkingObjectIdentifierType_{i}")
                v = _g(d, f"rt.linkingObjectIdentifierValue_{i}")
                rrole = _g(d, f"rt.linkingObjectRole_{i}")
                if t and v:
                    los.append((Identifier(t, v), rrole or None))
                t = _g(d, f"rt.linkingAgentIdentifierType_{i}")
                v = _g(d, f"rt.linkingAgentIdentifierValue_{i}")
                rrole = _g(d, f"rt.linkingAgentRole_{i}")
                if t and v:
                    las.append((Identifier(t, v), rrole or None))

            basis = _g(d, "rt.rightsBasis") or ""
            other_basis = _g(d, "rt.otherRightsBasis") or ""
            rights_basis_final = basis if basis else ("other" if other_basis else "")

            pb.add_rights_statement(
                identifier=rid,
                rights_basis=rights_basis_final or "other",
                acts=acts or None,
                linking_objects=los or None,
                linking_agents=las or None,
                copyright_status=_g(d, "rt.copyrightStatus") or None,
                copyright_jurisdiction=_g(d, "rt.copyrightJurisdiction") or None,
                copyright_note=_g(d, "rt.copyrightNote") or None,
            )

    return pb.root.getroottree()

# -----------------------------------------------------------
# JSON <-> FlatRecords
# -----------------------------------------------------------
def json_to_records(obj: Any) -> List[FlatRecord]:
    records: List[FlatRecord] = []
    if isinstance(obj, list):
        for it in obj:
            ent = (it.get("entity") or "").lower()
            d = dict(it); d.pop("entity", None)
            records.append(FlatRecord(ent, d))
        return records
    if isinstance(obj, dict):
        def add_group(key: str, ent: str):
            for d in obj.get(key, []) or []:
                records.append(FlatRecord(ent, dict(d)))
        add_group("objects", "object")
        add_group("events", "event")
        add_group("agents", "agent")
        add_group("rights", "rights")
        if not records and "items" in obj and isinstance(obj["items"], list):
            for it in obj["items"]:
                ent = (it.get("entity") or "").lower()
                d = dict(it); d.pop("entity", None)
                records.append(FlatRecord(ent, d))
        return records
    raise ValueError("JSON em formato não reconhecido.")

def records_to_json(records: List[FlatRecord]) -> Any:
    return [{"entity": r.entity, **r.data} for r in records]

# -----------------------------------------------------------
# CSV <-> FlatRecords (ESTILO DO PROJETO)
# -----------------------------------------------------------
def csv_to_records(csv_path: Path) -> List[FlatRecord]:
    records: List[FlatRecord] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # normaliza cabeçalhos
        reader.fieldnames = [norm_header(h) for h in (reader.fieldnames or [])]

        for raw in reader:
            # normaliza chaves e valores
            row = {norm_header(k): (v if v is not None else "") for k, v in raw.items()}
            ent = (row.get("entity") or "").strip().lower()
            if not ent:
                continue

            if ent == "object":
                d: Dict[str, Any] = {}
                d["ob.objectCategory"] = row.get("ob.objectCategory", "")
                d["ob.objectIdentifierType"]  = row.get("ob.objectIdentifierType", "")
                d["ob.objectIdentifierValue"] = row.get("ob.objectIdentifierValue", "")
                d["ob.originalName"] = row.get("ob.originalName", "")
                d["ob.size"] = row.get("ob.size", "")
                d["ob.format.formatDesignation.formatName"]    = row.get("ob.format.formatDesignation.formatName", "")
                d["ob.format.formatDesignation.formatVersion"] = row.get("ob.format.formatDesignation.formatVersion", "")
                d["ob.messageDigestAlgorithm"] = row.get("ob.messageDigestAlgorithm", "")
                d["ob.messageDigest"]          = row.get("ob.messageDigest", "")
                # links simples (1 ocorrência padrão)
                d["linkingEventIdentifierType"]  = row.get("linkingEventIdentifierType", "")
                d["linkingEventIdentifierValue"] = row.get("linkingEventIdentifierValue", "")
                d["linkingRightsStatementIdentifierType"]  = row.get("linkingRightsStatementIdentifierType", "")
                d["linkingRightsStatementIdentifierValue"] = row.get("linkingRightsStatementIdentifierValue", "")
                records.append(FlatRecord("object", d))
                continue

            if ent == "event":
                d: Dict[str, Any] = {}
                d["ev.eventIdentifierType"]  = row.get("ev.eventIdentifierType", "")
                d["ev.eventIdentifierValue"] = row.get("ev.eventIdentifierValue", "")
                d["ev.eventType"]     = row.get("ev.eventType", "")
                d["ev.eventDateTime"] = row.get("ev.eventDateTime", "")
                d["ev.eventDetailInformation.eventDetail"] = row.get("ev.eventDetailInformation.eventDetail", "")
                d["ev.eventOutcomeInformation.eventOutcome"] = row.get("ev.eventOutcomeInformation.eventOutcome", "")
                d["ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote"] = row.get("ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote", "")

                # captura repetidos numerados (e também sem sufixo)
                los = _collect_repeat_links(row, "ev.linkingObjectIdentifierType", "ev.linkingObjectIdentifierValue", "ev.linkingObjectIdentifierRole")
                las = _collect_repeat_links(row, "ev.linkingAgentIdentifierType",  "ev.linkingAgentIdentifierValue",  "ev.linkingAgentRole")

                # aplica nos slots numerados
                for i in range(MAX_LINKS):
                    t, v, rrole = los[i] if i < len(los) else ("", "", "")
                    d[f"ev.linkingObjectIdentifierType_{i+1}"]  = t
                    d[f"ev.linkingObjectIdentifierValue_{i+1}"] = v
                    d[f"ev.linkingObjectIdentifierRole_{i+1}"]  = rrole
                    t, v, rrole = las[i] if i < len(las) else ("", "", "")
                    d[f"ev.linkingAgentIdentifierType_{i+1}"]  = t
                    d[f"ev.linkingAgentIdentifierValue_{i+1}"] = v
                    d[f"ev.linkingAgentRole_{i+1}"]            = rrole

                records.append(FlatRecord("event", d))
                continue

            if ent == "agent":
                d: Dict[str, Any] = {}
                d["ag.agentIdentifierType"]  = row.get("ag.agentIdentifierType", "")
                d["ag.agentIdentifierValue"] = row.get("ag.agentIdentifierValue", "")
                d["ag.agentName"]    = row.get("ag.agentName", "")
                d["ag.agentType"]    = row.get("ag.agentType", "")
                d["ag.agentVersion"] = row.get("ag.agentVersion", "")
                records.append(FlatRecord("agent", d))
                continue

            if ent == "rights":
                d: Dict[str, Any] = {}
                d["rt.rightsStatementIdentifierType"]  = row.get("rt.rightsStatementIdentifierType", "")
                d["rt.rightsStatementIdentifierValue"] = row.get("rt.rightsStatementIdentifierValue", "")
                d["rt.rightsBasis"]        = row.get("rt.rightsBasis", "")
                d["rt.otherRightsBasis"]   = row.get("rt.otherRightsBasis", "")
                d["rt.otherRightsNote"]    = row.get("rt.otherRightsNote", "")
                d["rt.act"]                = row.get("rt.act", "")
                d["rt.restriction"]        = row.get("rt.restriction", "")
                d["rt.copyrightStatus"]       = row.get("rt.copyrightStatus", "")
                d["rt.copyrightJurisdiction"] = row.get("rt.copyrightJurisdiction", "")
                d["rt.copyrightNote"]         = row.get("rt.copyrightNote", "")

                los = _collect_repeat_links(row, "rt.linkingObjectIdentifierType", "rt.linkingObjectIdentifierValue", "rt.linkingObjectRole")
                las = _collect_repeat_links(row, "rt.linkingAgentIdentifierType",  "rt.linkingAgentIdentifierValue",  "rt.linkingAgentRole")
                for i in range(MAX_LINKS):
                    t, v, rrole = los[i] if i < len(los) else ("", "", "")
                    d[f"rt.linkingObjectIdentifierType_{i+1}"]  = t
                    d[f"rt.linkingObjectIdentifierValue_{i+1}"] = v
                    d[f"rt.linkingObjectRole_{i+1}"]            = rrole
                    t, v, rrole = las[i] if i < len(las) else ("", "", "")
                    d[f"rt.linkingAgentIdentifierType_{i+1}"]  = t
                    d[f"rt.linkingAgentIdentifierValue_{i+1}"] = v
                    d[f"rt.linkingAgentRole_{i+1}"]            = rrole

                records.append(FlatRecord("rights", d))
                continue

            # entidade desconhecida → ignora
    return records

def records_to_csv(records: List[FlatRecord], out_path: Path) -> None:
    # Prepara linhas no estilo do projeto
    rows: List[Dict[str, Any]] = []
    for r in records:
        d: Dict[str, Any] = {h: "" for h in CSV_HEADERS_PROJECT}
        d["entity"] = r.entity

        if r.entity == "object":
            for k in [
                "ob.objectCategory","ob.objectIdentifierType","ob.objectIdentifierValue",
                "ob.originalName","ob.size",
                "ob.format.formatDesignation.formatName","ob.format.formatDesignation.formatVersion",
                "ob.messageDigestAlgorithm","ob.messageDigest",
                "linkingEventIdentifierType","linkingEventIdentifierValue",
                "linkingRightsStatementIdentifierType","linkingRightsStatementIdentifierValue",
            ]:
                d[k] = r.data.get(k, "")

        elif r.entity == "event":
            base_keys = [
                "ev.eventIdentifierType","ev.eventIdentifierValue","ev.eventType","ev.eventDateTime",
                "ev.eventDetailInformation.eventDetail",
                "ev.eventOutcomeInformation.eventOutcome",
                "ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote",
            ]
            for k in base_keys:
                d[k] = r.data.get(k, "")
            for i in range(1, MAX_LINKS + 1):
                d[f"ev.linkingObjectIdentifierType_{i}"]  = r.data.get(f"ev.linkingObjectIdentifierType_{i}", "")
                d[f"ev.linkingObjectIdentifierValue_{i}"] = r.data.get(f"ev.linkingObjectIdentifierValue_{i}", "")
                d[f"ev.linkingObjectIdentifierRole_{i}"]  = r.data.get(f"ev.linkingObjectIdentifierRole_{i}", "")
                d[f"ev.linkingAgentIdentifierType_{i}"]   = r.data.get(f"ev.linkingAgentIdentifierType_{i}", "")
                d[f"ev.linkingAgentIdentifierValue_{i}"]  = r.data.get(f"ev.linkingAgentIdentifierValue_{i}", "")
                d[f"ev.linkingAgentRole_{i}"]             = r.data.get(f"ev.linkingAgentRole_{i}", "")

        elif r.entity == "agent":
            for k in ["ag.agentIdentifierType","ag.agentIdentifierValue","ag.agentName","ag.agentType","ag.agentVersion"]:
                d[k] = r.data.get(k, "")

        elif r.entity == "rights":
            base_keys = [
                "rt.rightsStatementIdentifierType","rt.rightsStatementIdentifierValue",
                "rt.rightsBasis","rt.otherRightsBasis","rt.otherRightsNote","rt.act","rt.restriction",
                "rt.copyrightStatus","rt.copyrightJurisdiction","rt.copyrightNote",
            ]
            for k in base_keys:
                d[k] = r.data.get(k, "")
            for i in range(1, MAX_LINKS + 1):
                d[f"rt.linkingObjectIdentifierType_{i}"]  = r.data.get(f"rt.linkingObjectIdentifierType_{i}", "")
                d[f"rt.linkingObjectIdentifierValue_{i}"] = r.data.get(f"rt.linkingObjectIdentifierValue_{i}", "")
                d[f"rt.linkingObjectRole_{i}"]            = r.data.get(f"rt.linkingObjectRole_{i}", "")
                d[f"rt.linkingAgentIdentifierType_{i}"]   = r.data.get(f"rt.linkingAgentIdentifierType_{i}", "")
                d[f"rt.linkingAgentIdentifierValue_{i}"]  = r.data.get(f"rt.linkingAgentIdentifierValue_{i}", "")
                d[f"rt.linkingAgentRole_{i}"]             = r.data.get(f"rt.linkingAgentRole_{i}", "")

        rows.append(d)

    # Escreve CSV
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADERS_PROJECT, extrasaction="ignore")
        w.writeheader()
        for d in rows:
            w.writerow(d)

# -----------------------------------------------------------
# Validação XML
# -----------------------------------------------------------
def validate_xml(xml_path: Path, schema_path: Optional[Path] = None) -> Tuple[bool, str]:
    sch = Path(schema_path or DEFAULT_SCHEMA_PATH)
    if not sch.exists():
        return False, f"Esquema XSD não encontrado em: {sch}"
    try:
        with sch.open("rb") as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        doc = etree.parse(str(xml_path))
        ok = schema.validate(doc)
        if ok:
            return True, "XML válido segundo PREMIS 3.0."
        else:
            log = schema.error_log
            msg = "; ".join(str(e) for e in log) if log else "Falha de validação sem detalhes."
            return False, msg
    except Exception as e:
        return False, f"Erro ao validar: {e}"

# -----------------------------------------------------------
# Exemplos no estilo do projeto
# -----------------------------------------------------------
def generate_examples(base_dir: Path) -> Dict[str, Path]:
    base_dir.mkdir(parents=True, exist_ok=True)

    # Linhas de exemplo (uma por entidade), com 2 links em event/rights
    csv_rows: List[Dict[str, Any]] = []

    # OBJECT
    csv_rows.append({
        "entity": "object",
        "ob.objectCategory": "file",
        "ob.objectIdentifierType": "local",
        "ob.objectIdentifierValue": "obj:file:001",
        "ob.originalName": "C:/bags/ingest/files/A001.tif",
        "ob.size": "123456",
        "ob.format.formatDesignation.formatName": "TIFF",
        "ob.format.formatDesignation.formatVersion": "6.0",
        "ob.messageDigestAlgorithm": "sha256",
        "ob.messageDigest": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "linkingEventIdentifierType": "local",
        "linkingEventIdentifierValue": "evt:ing-001",
        "linkingRightsStatementIdentifierType": "local",
        "linkingRightsStatementIdentifierValue": "rights:001",
    })

    # EVENT
    ev = {
        "entity": "event",
        "ev.eventIdentifierType": "local",
        "ev.eventIdentifierValue": "evt:ing-001",
        "ev.eventType": "ingestion",
        "ev.eventDateTime": "2025-01-01T12:00:00+00:00",
        "ev.eventDetailInformation.eventDetail": "Ingest via Thor",
        "ev.eventOutcomeInformation.eventOutcome": "success",
        "ev.eventOutcomeInformation.eventOutcomeDetail.eventOutcomeDetailNote": "OK",
    }
    ev["ev.linkingObjectIdentifierType_1"]  = "local"
    ev["ev.linkingObjectIdentifierValue_1"] = "obj:file:001"
    ev["ev.linkingObjectIdentifierRole_1"]  = "outcome"
    ev["ev.linkingAgentIdentifierType_1"]   = "local"
    ev["ev.linkingAgentIdentifierValue_1"]  = "agent:thor"
    ev["ev.linkingAgentRole_1"]             = "executing program"
    # segundo link opcional (de exemplo)
    ev["ev.linkingAgentIdentifierType_2"]   = "orcid"
    ev["ev.linkingAgentIdentifierValue_2"]  = "0000-0002-0000-0000"
    ev["ev.linkingAgentRole_2"]             = "operator"
    csv_rows.append(ev)

    # AGENT
    csv_rows.append({
        "entity": "agent",
        "ag.agentIdentifierType": "local",
        "ag.agentIdentifierValue": "agent:thor",
        "ag.agentName": "Thor Arquivista – Worker",
        "ag.agentType": "software",
        "ag.agentVersion": "1.0.0",
    })

    # RIGHTS
    rt = {
        "entity": "rights",
        "rt.rightsStatementIdentifierType": "local",
        "rt.rightsStatementIdentifierValue": "rights:001",
        "rt.rightsBasis": "license",
        "rt.otherRightsBasis": "",
        "rt.otherRightsNote": "uso institucional",
        "rt.act": "disseminate",
        "rt.restriction": "",
        "rt.copyrightStatus": "",
        "rt.copyrightJurisdiction": "",
        "rt.copyrightNote": "",
    }
    rt["rt.linkingObjectIdentifierType_1"]  = "local"
    rt["rt.linkingObjectIdentifierValue_1"] = "obj:file:001"
    rt["rt.linkingObjectRole_1"]            = ""
    rt["rt.linkingAgentIdentifierType_1"]   = "local"
    rt["rt.linkingAgentIdentifierValue_1"]  = "agent:thor"
    rt["rt.linkingAgentRole_1"]             = "rightsholder"
    csv_rows.append(rt)

    # Escreve CSV (projeto)
    csv_path = base_dir / "premis_example_project.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADERS_PROJECT, extrasaction="ignore")
        w.writeheader()
        for row in csv_rows:
            w.writerow(row)

    # JSON (lista flat no mesmo estilo)
    json_path = base_dir / "premis_example_project.json"
    json_path.write_text(json.dumps(csv_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # XML (gerado dos registros)
    recs = []
    for r in csv_rows:
        ent = r.get("entity", "")
        data = {k: v for k, v in r.items() if k != "entity"}
        recs.append(FlatRecord(ent, data))
    tree = records_to_xml(recs)
    xml_path = base_dir / "premis_example_project.xml"
    xml_path.write_bytes(etree.tostring(tree.getroot(), pretty_print=True, xml_declaration=True, encoding="utf-8"))

    return {"csv": csv_path, "json": json_path, "xml": xml_path}

# -----------------------------------------------------------
# CLI
# -----------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Conversor/validador PREMIS 3.0 (XML ⇄ JSON ⇄ CSV) — estilo de CSV do projeto."
    )
    ap.add_argument("--in", dest="inp", help="Arquivo de entrada (.xml | .json | .csv)")
    ap.add_argument("--out", dest="out", help="Arquivo de saída (.xml | .json | .csv)")
    ap.add_argument("--validate", action="store_true", help="Validar XML de entrada contra o XSD do projeto")
    ap.add_argument("--schema", help="Caminho alternativo para premis-v3-0.xsd (opcional)")
    ap.add_argument("--example", action="store_true", help="Gerar exemplos (XML/CSV/JSON) em ./examples/ no estilo do projeto")
    args = ap.parse_args()

    # Geração de exemplos
    if args.example:
        out = generate_examples(Path("./examples"))
        print(f"[OK] Exemplos gerados:\n  CSV : {out['csv']}\n  JSON: {out['json']}\n  XML : {out['xml']}")
        return

    if not args.inp:
        raise SystemExit("[ERRO] Use --in <arquivo> ou --example.")

    in_path = Path(args.inp)
    if not in_path.exists():
        raise SystemExit(f"[ERRO] Arquivo de entrada não encontrado: {in_path}")

    schema_path = Path(args.schema) if args.schema else None
    in_fmt = detect_format(in_path)

    # Validação (se solicitada)
    if args.validate:
        if in_fmt != "xml":
            print("[AVISO] --validate: a validação só é feita para XML. Ignorando.")
        else:
            ok, msg = validate_xml(in_path, schema_path)
            print(("[OK] " if ok else "[ERRO] ") + msg)
            if not ok and not args.out:
                raise SystemExit(1)

    # Se não há saída e não é apenas validação, nada a fazer
    if not args.out:
        return

    out_path = Path(args.out)
    out_fmt = detect_format(out_path)

    # Carrega registros
    if in_fmt == "xml":
        records = xml_to_records(in_path)
    elif in_fmt == "json":
        data = json.loads(in_path.read_text(encoding="utf-8"))
        records = json_to_records(data)
    elif in_fmt == "csv":
        records = csv_to_records(in_path)
    else:
        raise SystemExit(f"[ERRO] Formato de entrada não suportado: {in_fmt}")

    # Converte para saída
    if out_fmt == "json":
        obj = records_to_json(records)
        out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] JSON escrito em: {out_path}")

    elif out_fmt == "csv":
        records_to_csv(records, out_path)
        print(f"[OK] CSV (estilo do projeto) escrito em: {out_path}")

    elif out_fmt == "xml":
        tree = records_to_xml(records, schema_path)
        out_path.write_bytes(etree.tostring(tree.getroot(), pretty_print=True, xml_declaration=True, encoding="utf-8"))
        print(f"[OK] XML PREMIS escrito em: {out_path}")
        ok, msg = validate_xml(out_path, schema_path)
        print(("[OK] " if ok else "[AVISO] ") + f"Validação pós-geração: {msg}")
    else:
        raise SystemExit(f"[ERRO] Formato de saída não suportado: {out_fmt}")

if __name__ == "__main__":
    main()
