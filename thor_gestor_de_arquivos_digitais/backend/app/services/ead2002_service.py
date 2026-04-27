from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from app.models.descricao_arquivistica import RegistroDescritivo
from app.schemas.descricao_arquivistica import EAD2002ImportResult
from app.services.descricao_arquivistica_service import ALLOWED_CHILDREN, DescricaoArquivisticaService

EAD_NS = "urn:isbn:1-931666-22-9"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

LEVEL_TO_EAD = {
    "1": "collection",
    "2": "subfonds",
    "2.5": "subgrp",
    "3": "series",
    "3.5": "subseries",
    "4": "file",
    "5": "item",
}
EAD_TO_LEVEL = {
    "collection": "1",
    "fonds": "1",
    "recordgrp": "1",
    "subfonds": "2",
    "subgrp": "2.5",
    "series": "3",
    "subseries": "3.5",
    "file": "4",
    "item": "5",
}
COMPONENT_TAGS = {f"c{index:02d}" for index in range(1, 13)} | {"c"}


class EAD2002Service:
    @staticmethod
    def exportar(db: Session, root_id: uuid.UUID) -> bytes | None:
        root_record = db.get(RegistroDescritivo, root_id)
        if not root_record:
            return None

        ET.register_namespace("", EAD_NS)
        ET.register_namespace("xsi", XSI_NS)
        ead = ET.Element(
            _q("ead"),
            {
                f"{{{XSI_NS}}}schemaLocation": (
                    "urn:isbn:1-931666-22-9 http://www.loc.gov/ead/ead.xsd"
                )
            },
        )
        EAD2002Service._build_header(ead, root_record)
        archdesc = ET.SubElement(ead, _q("archdesc"), {"level": LEVEL_TO_EAD.get(root_record.nivel, "otherlevel")})
        EAD2002Service._append_description(archdesc, root_record)
        children = EAD2002Service._children(db, root_record.id)
        if children:
            dsc = ET.SubElement(archdesc, _q("dsc"))
            for child in children:
                EAD2002Service._append_component(db, dsc, child, depth=1)

        EAD2002Service._indent(ead)
        return ET.tostring(ead, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def importar(db: Session, xml_content: bytes) -> EAD2002ImportResult:
        warnings: list[str] = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            raise ValueError(f"XML EAD2002 inválido: {exc}") from exc

        if _local(root.tag) != "ead":
            raise ValueError("O documento informado não possui elemento raiz <ead>.")

        archdesc = _first(root, "archdesc")
        if archdesc is None:
            raise ValueError("O documento EAD2002 não possui <archdesc>.")

        root_ids: list[uuid.UUID] = []
        imported = 0
        try:
            root_record = EAD2002Service._record_from_node(db, archdesc, None, warnings)
            root_ids.append(root_record.id)
            imported += 1
            dsc = _first(archdesc, "dsc")
            if dsc is not None:
                for child in _component_children(dsc):
                    imported += EAD2002Service._import_component(db, child, root_record, warnings)
            db.commit()
        except Exception:
            db.rollback()
            raise

        return EAD2002ImportResult(imported=imported, root_ids=root_ids, warnings=warnings)

    @staticmethod
    def _build_header(ead: ET.Element, record: RegistroDescritivo) -> None:
        header = ET.SubElement(ead, _q("eadheader"))
        ET.SubElement(header, _q("eadid")).text = record.codigo_referencia
        filedesc = ET.SubElement(header, _q("filedesc"))
        titlestmt = ET.SubElement(filedesc, _q("titlestmt"))
        ET.SubElement(titlestmt, _q("titleproper")).text = record.titulo
        profiledesc = ET.SubElement(header, _q("profiledesc"))
        creation = ET.SubElement(profiledesc, _q("creation"))
        creation.text = "Exportado pelo Thor Gestor de Arquivos Digitais"
        if record.data_descricao:
            normal = record.data_descricao.date().isoformat()
            ET.SubElement(creation, _q("date"), {"normal": normal}).text = normal

    @staticmethod
    def _append_component(db: Session, parent: ET.Element, record: RegistroDescritivo, depth: int) -> None:
        tag = "c" if depth > 12 else f"c{depth:02d}"
        component = ET.SubElement(parent, _q(tag), {"level": LEVEL_TO_EAD.get(record.nivel, "otherlevel")})
        EAD2002Service._append_description(component, record)
        for child in EAD2002Service._children(db, record.id):
            EAD2002Service._append_component(db, component, child, depth + 1)

    @staticmethod
    def _append_description(parent: ET.Element, record: RegistroDescritivo) -> None:
        did = ET.SubElement(parent, _q("did"))
        ET.SubElement(did, _q("unitid")).text = record.codigo_referencia
        ET.SubElement(did, _q("unittitle")).text = record.titulo
        if record.data_inicial or record.data_final:
            attrs = {"normal": _date_normal(record.data_inicial, record.data_final)}
            ET.SubElement(did, _q("unitdate"), attrs).text = _date_text(record.data_inicial, record.data_final)
        if record.dimensao or record.suporte:
            physdesc = ET.SubElement(did, _q("physdesc"))
            if record.dimensao:
                ET.SubElement(physdesc, _q("extent")).text = record.dimensao
            if record.suporte:
                ET.SubElement(physdesc, _q("physfacet")).text = record.suporte
        if record.produtor:
            origination = ET.SubElement(did, _q("origination"))
            ET.SubElement(origination, _q("corpname")).text = record.produtor
        if record.idioma:
            langmaterial = ET.SubElement(did, _q("langmaterial"))
            ET.SubElement(langmaterial, _q("language")).text = record.idioma

        text_blocks = {
            "bioghist": record.historia_administrativa,
            "custodhist": record.historia_arquivistica or record.procedencia,
            "scopecontent": record.ambito_conteudo,
            "appraisal": record.avaliacao_eliminacao,
            "accruals": record.incorporacoes,
            "arrangement": record.sistema_arranjo,
            "accessrestrict": record.condicoes_acesso,
            "userestrict": record.condicoes_reproducao,
            "phystech": record.caracteristicas_tecnicas,
            "originalsloc": record.originais,
            "altformavail": record.copias,
            "relatedmaterial": record.unidades_relacionadas,
            "bibliography": record.publicacoes,
            "note": record.notas,
            "processinfo": record.regras_convencoes,
        }
        for tag, value in text_blocks.items():
            _append_text_block(parent, tag, value)

        if record.arquivista_responsavel or record.data_descricao:
            processinfo = ET.SubElement(parent, _q("processinfo"))
            pieces = [record.arquivista_responsavel]
            if record.data_descricao:
                pieces.append(record.data_descricao.date().isoformat())
            ET.SubElement(processinfo, _q("p")).text = " | ".join(piece for piece in pieces if piece)

        EAD2002Service._append_controlaccess(parent, record)

    @staticmethod
    def _append_controlaccess(parent: ET.Element, record: RegistroDescritivo) -> None:
        values = {
            "subject": record.assuntos,
            "persname": record.pessoas,
            "geogname": record.locais,
            "corpname": record.entidades,
            "function": record.eventos,
        }
        if not any(values.values()):
            return
        controlaccess = ET.SubElement(parent, _q("controlaccess"))
        for tag, raw in values.items():
            for value in _split_terms(raw):
                ET.SubElement(controlaccess, _q(tag)).text = value

    @staticmethod
    def _record_from_node(
        db: Session,
        node: ET.Element,
        parent: RegistroDescritivo | None,
        warnings: list[str],
    ) -> RegistroDescritivo:
        did = _first(node, "did")
        if did is None:
            raise ValueError(f"Elemento <{_local(node.tag)}> sem <did>.")

        level = EAD_TO_LEVEL.get((node.attrib.get("level") or "").lower())
        if not level:
            level = "1" if parent is None else _next_level(parent.nivel)
            warnings.append(f"Nível EAD ausente ou não mapeado; usado nível {level}.")
        if parent is None and level != "1":
            warnings.append(f"Nível raiz {level} ajustado para 1 por compatibilidade com a descrição multinível.")
            level = "1"
        if parent and level not in ALLOWED_CHILDREN.get(parent.nivel, set()):
            adjusted = _next_level(parent.nivel)
            warnings.append(f"Nível {level} ajustado para {adjusted} por compatibilidade hierárquica.")
            level = adjusted

        unitdate = _first(did, "unitdate")
        data_inicial, data_final = _parse_date_range(unitdate)
        payload = {
            "parent_id": parent.id if parent else None,
            "nivel": level,
            "norma": "EAD2002",
            "codigo_referencia": _text(_first(did, "unitid")) or f"EAD-{uuid.uuid4()}",
            "titulo": _text(_first(did, "unittitle")) or "Registro EAD sem título",
            "data_inicial": data_inicial,
            "data_final": data_final,
            "dimensao": _text(_first(_first(did, "physdesc"), "extent")),
            "suporte": _text(_first(_first(did, "physdesc"), "physfacet")),
            "produtor": _text(_first(_first(did, "origination"), "corpname"))
            or _text(_first(_first(did, "origination"), "persname")),
            "historia_administrativa": _block_text(node, "bioghist"),
            "historia_arquivistica": _block_text(node, "custodhist"),
            "procedencia": None,
            "ambito_conteudo": _block_text(node, "scopecontent"),
            "avaliacao_eliminacao": _block_text(node, "appraisal"),
            "incorporacoes": _block_text(node, "accruals"),
            "sistema_arranjo": _block_text(node, "arrangement"),
            "condicoes_acesso": _block_text(node, "accessrestrict"),
            "condicoes_reproducao": _block_text(node, "userestrict"),
            "idioma": _text(_first(_first(did, "langmaterial"), "language")) or _text(_first(did, "langmaterial")),
            "caracteristicas_tecnicas": _block_text(node, "phystech"),
            "originais": _block_text(node, "originalsloc"),
            "copias": _block_text(node, "altformavail"),
            "unidades_relacionadas": _block_text(node, "relatedmaterial"),
            "publicacoes": _block_text(node, "bibliography"),
            "notas": _block_text(node, "note"),
            "arquivista_responsavel": None,
            "regras_convencoes": _block_text(node, "processinfo"),
            "data_descricao": datetime.now(timezone.utc),
            "assuntos": _control_terms(node, "subject"),
            "pessoas": _control_terms(node, "persname"),
            "locais": _control_terms(node, "geogname"),
            "entidades": _control_terms(node, "corpname"),
            "eventos": _control_terms(node, "function"),
        }
        DescricaoArquivisticaService._validate_parent(db, payload["parent_id"], payload["nivel"])
        DescricaoArquivisticaService._inherit_context(db, payload)
        record = RegistroDescritivo(**payload)
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def _import_component(
        db: Session,
        node: ET.Element,
        parent: RegistroDescritivo,
        warnings: list[str],
    ) -> int:
        record = EAD2002Service._record_from_node(db, node, parent, warnings)
        count = 1
        for child in _component_children(node):
            count += EAD2002Service._import_component(db, child, record, warnings)
        return count

    @staticmethod
    def _children(db: Session, parent_id: uuid.UUID) -> list[RegistroDescritivo]:
        return (
            db.query(RegistroDescritivo)
            .filter(RegistroDescritivo.parent_id == parent_id)
            .order_by(RegistroDescritivo.codigo_referencia, RegistroDescritivo.titulo)
            .all()
        )

    @staticmethod
    def _indent(element: ET.Element, level: int = 0) -> None:
        space = "\n" + level * "  "
        if len(element):
            if not element.text or not element.text.strip():
                element.text = space + "  "
            for child in element:
                EAD2002Service._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = space
        if level and (not element.tail or not element.tail.strip()):
            element.tail = space


def _q(tag: str) -> str:
    return f"{{{EAD_NS}}}{tag}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first(parent: ET.Element | None, tag: str) -> ET.Element | None:
    if parent is None:
        return None
    for child in list(parent):
        if _local(child.tag) == tag:
            return child
    return None


def _text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    value = " ".join(" ".join(element.itertext()).split())
    return value or None


def _block_text(parent: ET.Element, tag: str) -> str | None:
    element = _first(parent, tag)
    return _text(element)


def _append_text_block(parent: ET.Element, tag: str, value: str | None) -> None:
    if not value:
        return
    element = ET.SubElement(parent, _q(tag))
    ET.SubElement(element, _q("p")).text = value


def _date_normal(start: date | None, end: date | None) -> str:
    if start and end and start != end:
        return f"{start.isoformat()}/{end.isoformat()}"
    return (start or end or date.today()).isoformat()


def _date_text(start: date | None, end: date | None) -> str:
    if start and end and start != end:
        return f"{start.isoformat()} - {end.isoformat()}"
    return (start or end or date.today()).isoformat()


def _parse_date_range(unitdate: ET.Element | None) -> tuple[date | None, date | None]:
    if unitdate is None:
        return None, None
    value = unitdate.attrib.get("normal") or _text(unitdate) or ""
    parts = re.split(r"\s*/\s*|\s+-\s+", value, maxsplit=1)
    start = _parse_date(parts[0]) if parts else None
    end = _parse_date(parts[1]) if len(parts) > 1 else start
    return start, end


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    if re.fullmatch(r"\d{4}-\d{2}", value):
        return datetime.strptime(f"{value}-01", "%Y-%m-%d").date()
    if re.fullmatch(r"\d{4}", value):
        return date(int(value), 1, 1)
    return None


def _split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    return [term.strip() for term in re.split(r"[;\n]", value) if term.strip()]


def _control_terms(parent: ET.Element, tag: str) -> str | None:
    controlaccess = _first(parent, "controlaccess")
    if controlaccess is None:
        return None
    terms = [_text(child) for child in list(controlaccess) if _local(child.tag) == tag]
    values = [term for term in terms if term]
    return "; ".join(values) if values else None


def _component_children(parent: ET.Element) -> list[ET.Element]:
    return [child for child in list(parent) if _local(child.tag) in COMPONENT_TAGS]


def _next_level(parent_level: str) -> str:
    options = sorted(ALLOWED_CHILDREN.get(parent_level, {"5"}))
    return options[0] if options else "5"
