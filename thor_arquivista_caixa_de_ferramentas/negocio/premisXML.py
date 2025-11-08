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

# negocio/premisXML.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Dict, Any, List
from datetime import datetime, timezone

from pathlib import Path

from lxml import etree

PREMIS_NS = "http://www.loc.gov/premis/v3"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
NSMAP = {None: PREMIS_NS, "xsi": XSI_NS}

# Caminho padrão para o esquema PREMIS 3.0 (relativo à raiz do projeto)
DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "schemas" / "premis-v3-0.xsd"
)

@dataclass(frozen=True)
class Identifier:
    id_type: str
    id_value: str


def _el(tag: str, text: Optional[str] = None, attrib: Optional[Dict[str, str]] = None, ns: str = PREMIS_NS):
    """Cria elemento em PREMIS_NS por padrão."""
    e = etree.Element(etree.QName(ns, tag), attrib=attrib or {})
    if text is not None:
        e.text = str(text)
    return e


def _sub(parent: etree._Element, tag: str, text: Optional[str] = None, attrib: Optional[Dict[str, str]] = None, ns: str = PREMIS_NS):
    e = _el(tag, text, attrib, ns)
    parent.append(e)
    return e

def _iso_datetime(dt: Optional[str | datetime]) -> str:
    """Normaliza para string ISO 8601 com timezone quando possível (recomendado pelo PREMIS)."""
    if dt is None:
        # Usa datetime com fuso UTC explícito (recomendado em 3.12+)
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            # acrescenta o fuso UTC se vier naive
            return dt.replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
        return dt.isoformat(timespec="seconds")
    return dt


class PremisBuilder:
    """
    Construtor de PREMIS 3.0.

    - build_root(): cria <premis> (container).
    - add_object_file()/add_object_representation(): adiciona Object.
    - add_event(): adiciona Event (com links).
    - add_agent(): adiciona Agent (pessoa, organização, software ou hardware).
    - add_rights_statement(): adiciona Rights (com links).
    - serialize(): bytes/string.
    - validate(): valida via XSD (lxml.etree.XMLSchema).
    """

    def __init__(self, schema_path: Path | str = DEFAULT_SCHEMA_PATH):
        self.schema_path = Path(schema_path)
        self.root = etree.Element(etree.QName(PREMIS_NS, "premis"), nsmap=NSMAP)
        # schemaLocation útil para validadores externos
        self.root.set(etree.QName(XSI_NS, "schemaLocation"),
                      f"{PREMIS_NS} {self.schema_path.as_posix()}")

    # ---------- Objetos ----------
    def add_object_file(
        self,
        identifier: Identifier,
        original_name: Optional[str] = None,
        size_bytes: Optional[int] = None,
        format_name: Optional[str] = None,
        format_version: Optional[str] = None,
        fixities: Optional[Iterable[Tuple[str, str]]] = None,  # [(algorithm, value)]
        significant_properties: Optional[Iterable[str]] = None,
        storage_location: Optional[str] = None,
        linking_events: Optional[Iterable[Identifier]] = None,
        linking_rights: Optional[Iterable[Identifier]] = None,
    ) -> etree._Element:
        """
        Cria um <object> category='file' com identificador, formato e fixity.
        """
        obj = _sub(self.root, "object")
        obj.set("category", "file")

        # objectIdentifier (M): type + value
        oid = _sub(obj, "objectIdentifier")
        _sub(oid, "objectIdentifierType", identifier.id_type)
        _sub(oid, "objectIdentifierValue", identifier.id_value)

        # objectCharacteristics
        oc = _sub(obj, "objectCharacteristics")

        if size_bytes is not None:
            _sub(oc, "size", str(size_bytes))

        # fixity (R)
        for alg, val in (fixities or []):
            fx = _sub(oc, "fixity")
            _sub(fx, "messageDigestAlgorithm", alg)
            _sub(fx, "messageDigest", val)

        # format (R) — nome/versão (ver seção “Format information”)
        if format_name or format_version:
            fmt = _sub(oc, "format")
            ide = _sub(fmt, "formatDesignation")
            if format_name:
                _sub(ide, "formatName", format_name)
            if format_version:
                _sub(ide, "formatVersion", format_version)

        # significantProperties (R)
        for sp in (significant_properties or []):
            sp_el = _sub(oc, "significantProperties")
            _sub(sp_el, "significantPropertiesType", "local")
            _sub(sp_el, "significantPropertiesValue", sp)

        # originalName (O)
        if original_name:
            _sub(obj, "originalName", original_name)

        # storage (O)
        if storage_location:
            st = _sub(obj, "storage")
            _sub(st, "contentLocationType", "path")
            _sub(st, "contentLocationValue", storage_location)

        # linkingEventIdentifier (O, R)
        for e in (linking_events or []):
            lei = _sub(obj, "linkingEventIdentifier")
            _sub(lei, "linkingEventIdentifierType", e.id_type)
            _sub(lei, "linkingEventIdentifierValue", e.id_value)

        # linkingRightsStatementIdentifier (O, R)
        for r in (linking_rights or []):
            lri = _sub(obj, "linkingRightsStatementIdentifier")
            _sub(lri, "linkingRightsStatementIdentifierType", r.id_type)
            _sub(lri, "linkingRightsStatementIdentifierValue", r.id_value)

        return obj

    def add_object_representation(
        self,
        identifier: Identifier,
        constituent_object_ids: Optional[Iterable[Identifier]] = None,
    ) -> etree._Element:
        """
        Cria um <object> category='representation' e, opcionalmente, relaciona arquivos.
        """
        obj = _sub(self.root, "object")
        obj.set("category", "representation")

        oid = _sub(obj, "objectIdentifier")
        _sub(oid, "objectIdentifierType", identifier.id_type)
        _sub(oid, "objectIdentifierValue", identifier.id_value)

        # relationship com files (deriva da modelagem de Representations em PREMIS)
        for cid in (constituent_object_ids or []):
            rel = _sub(obj, "relationship")
            _sub(rel, "relationshipType", "structural")
            _sub(rel, "relationshipSubType", "has part")
            rid = _sub(rel, "relatedObjectIdentifier")
            _sub(rid, "relatedObjectIdentifierType", cid.id_type)
            _sub(rid, "relatedObjectIdentifierValue", cid.id_value)

        return obj

    # ---------- Eventos ----------
    def add_event(
        self,
        identifier: Identifier,
        event_type: str,
        event_datetime: str | datetime,
        detail: Optional[str] = None,
        outcome: Optional[str] = None,
        outcome_note: Optional[str] = None,
        linking_objects: Optional[Iterable[Tuple[Identifier, Optional[str]]]] = None,  # (id, role?)
        linking_agents: Optional[Iterable[Tuple[Identifier, Optional[str]]]] = None,   # (id, role?)
    ) -> etree._Element:
        """
        Adiciona <event> com campos obrigatórios e links para objetos e agentes.
        """
        ev = _sub(self.root, "event")

        eid = _sub(ev, "eventIdentifier")
        _sub(eid, "eventIdentifierType", identifier.id_type)
        _sub(eid, "eventIdentifierValue", identifier.id_value)

        _sub(ev, "eventType", event_type)
        _sub(ev, "eventDateTime", _iso_datetime(event_datetime))  # ISO 8601 recomendado

        if detail:
            edi = _sub(ev, "eventDetailInformation")
            _sub(edi, "eventDetail", detail)

        if outcome or outcome_note:
            eoi = _sub(ev, "eventOutcomeInformation")
            if outcome:
                _sub(eoi, "eventOutcome", outcome)
            if outcome_note:
                od = _sub(eoi, "eventOutcomeDetail")
                _sub(od, "eventOutcomeDetailNote", outcome_note)

        # linkingObjectIdentifier (O, R)
        for obj_id, role in (linking_objects or []):
            loi = _sub(ev, "linkingObjectIdentifier")
            _sub(loi, "linkingObjectIdentifierType", obj_id.id_type)
            _sub(loi, "linkingObjectIdentifierValue", obj_id.id_value)
            if role:
                _sub(loi, "linkingObjectRole", role)

        # linkingAgentIdentifier (O, R)
        for ag_id, role in (linking_agents or []):
            lai = _sub(ev, "linkingAgentIdentifier")
            _sub(lai, "linkingAgentIdentifierType", ag_id.id_type)
            _sub(lai, "linkingAgentIdentifierValue", ag_id.id_value)
            if role:
                _sub(lai, "linkingAgentRole", role)

        return ev

    # ---------- Agentes ----------
    def add_agent(
        self,
        identifier: Identifier,
        agent_name: str,
        agent_type: str,               # person|organization|software|hardware
        agent_version: Optional[str] = None,
        notes: Optional[Iterable[str]] = None,
    ) -> etree._Element:
        """
        Adiciona <agent> com identificação, tipo e (se software/hardware) versão.
        """
        ag = _sub(self.root, "agent")

        aid = _sub(ag, "agentIdentifier")
        _sub(aid, "agentIdentifierType", identifier.id_type)
        _sub(aid, "agentIdentifierValue", identifier.id_value)

        _sub(ag, "agentName", agent_name)
        _sub(ag, "agentType", agent_type)  # vocabulário recomendado (person/organization/software/hardware)

        if agent_version:
            _sub(ag, "agentVersion", agent_version)

        for n in (notes or []):
            _sub(ag, "agentNote", n)

        return ag

    # ---------- Direitos ----------
    def add_rights_statement(
        self,
        identifier: Identifier,
        rights_basis: str,  # e.g., "copyright", "license", "statute", "other"
        acts: Optional[Iterable[Tuple[str, Optional[List[str]], Optional[Tuple[str, Optional[str]]], Optional[Tuple[str, Optional[str]]], Optional[Iterable[str]]]]] = None,
        # acts: [(act, restrictions, termOfGrant(start,end), termOfRestriction(start,end), notes)]
        linking_objects: Optional[Iterable[Tuple[Identifier, Optional[str]]]] = None,
        linking_agents: Optional[Iterable[Tuple[Identifier, Optional[str]]]] = None,
        copyright_status: Optional[str] = None,
        copyright_jurisdiction: Optional[str] = None,
        copyright_note: Optional[str] = None,
    ) -> etree._Element:
        """
        Adiciona <rights> com um <rightsStatement> principal + links a objetos e agentes.
        """
        rights = _sub(self.root, "rights")
        rs = _sub(rights, "rightsStatement")

        rsid = _sub(rs, "rightsStatementIdentifier")
        _sub(rsid, "rightsStatementIdentifierType", identifier.id_type)
        _sub(rsid, "rightsStatementIdentifierValue", identifier.id_value)

        _sub(rs, "rightsBasis", rights_basis)

        # Copyright (opcional)
        if any([copyright_status, copyright_jurisdiction, copyright_note]):
            ci = _sub(rs, "copyrightInformation")
            if copyright_status:
                _sub(ci, "copyrightStatus", copyright_status)
            if copyright_jurisdiction:
                _sub(ci, "copyrightJurisdiction", copyright_jurisdiction)
            if copyright_note:
                _sub(ci, "copyrightNote", copyright_note)

        # rightsGranted (R)
        for act, restrictions, term_grant, term_restrict, notes in (acts or []):
            rg = _sub(rs, "rightsGranted")
            _sub(rg, "act", act)
            for r in (restrictions or []):
                _sub(rg, "restriction", r)
            if term_grant:
                tg = _sub(rg, "termOfGrant")
                _sub(tg, "startDate", term_grant[0] or "")
                if term_grant[1]:
                    _sub(tg, "endDate", term_grant[1])
            if term_restrict:
                tr = _sub(rg, "termOfRestriction")
                _sub(tr, "startDate", term_restrict[0] or "")
                if term_restrict[1]:
                    _sub(tr, "endDate", term_restrict[1])
            for n in (notes or []):
                _sub(rg, "rightsGrantedNote", n)

        # linkingObjectIdentifier (O, R)
        for obj_id, role in (linking_objects or []):
            loi = _sub(rs, "linkingObjectIdentifier")
            _sub(loi, "linkingObjectIdentifierType", obj_id.id_type)
            _sub(loi, "linkingObjectIdentifierValue", obj_id.id_value)
            if role:
                _sub(loi, "linkingObjectRole", role)

        # linkingAgentIdentifier (O, R)
        for ag_id, role in (linking_agents or []):
            lai = _sub(rs, "linkingAgentIdentifier")
            _sub(lai, "linkingAgentIdentifierType", ag_id.id_type)
            _sub(lai, "linkingAgentIdentifierValue", ag_id.id_value)
            if role:
                _sub(lai, "linkingAgentRole", role)

        return rights

    # ---------- Utilidades ----------
    def tostring(self, pretty: bool = True, xml_declaration: bool = True, encoding: str = "utf-8") -> bytes:
        return etree.tostring(self.root, pretty_print=pretty, xml_declaration=xml_declaration, encoding=encoding)

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Valida o documento contra premis-v3-0.xsd. Retorna (ok, mensagem_erro_ou_None).
        """
        if not self.schema_path.exists():
            return False, f"Esquema não encontrado em {self.schema_path}"
        with self.schema_path.open("rb") as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        ok = schema.validate(self.root.getroottree())
        if ok:
            return True, None
        # coleta erros
        log = schema.error_log
        if log:
            return False, "; ".join([str(e) for e in log])
        return False, "Falha de validação PREMIS (sem detalhes no log)."

    def write(self, path: Path | str, pretty: bool = True, xml_declaration: bool = True, encoding: str = "utf-8") -> Path:
        p = Path(path)
        p.write_bytes(self.tostring(pretty=pretty, xml_declaration=xml_declaration, encoding=encoding))
        return p