import logging
import uuid
from io import BytesIO
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageOps
from app.models.capa_instrumento import CapaInstrumento
from app.models.editorial import PublicacaoInstrumento
from app.models.instrumento import Instrumento
from app.services.armazenamento_service import armazenamento, validar_imagem
from app.services.auditoria_service import registrar
from app.services.permissao_service import require, permissoes, filtro_escopo, require_any_scope
from sqlalchemy import select

SIZE = (960, 540)


def validar_vinculo(db, capa_id):
    if capa_id is None:
        return
    capa = db.get(CapaInstrumento, capa_id)
    if not capa or (capa.criado_por != db.info["usuario"].id and "*" not in permissoes(db)):
        raise HTTPException(404, "Imagem de card nao encontrada.")


def upload(db, conteudo, mime, instrumento_id=None):
    actor = require(db, "instrumentos_editar", instrumento_id) if instrumento_id else require(db, "instrumentos_incluir")
    if instrumento_id and not db.get(Instrumento, instrumento_id):
        raise HTTPException(404, "Instrumento nao encontrado.")
    validar_imagem(conteudo, mime, max_pixels=16_000_000)
    with Image.open(BytesIO(conteudo)) as original:
        image = ImageOps.exif_transpose(original).convert("RGBA")
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        normalized = ImageOps.pad(background, SIZE, method=Image.Resampling.LANCZOS, color="white")
        output = BytesIO()
        normalized.save(output, format="JPEG", quality=85)
    data = output.getvalue()
    capa_id = uuid.uuid4()
    key = f"instrumentos/capas/{capa_id}.jpg"
    armazenamento.salvar_upload(key, data, "image/jpeg")
    try:
        capa = CapaInstrumento(id=capa_id, object_key=key, checksum_sha256=armazenamento.calcular_checksum(data),
            tamanho_bytes=len(data), criado_por=actor.id)
        db.add(capa)
        registrar(db, "UPLOAD_CAPA_INSTRUMENTO", "capa_instrumento", capa_id, instrumento_id)
        db.commit()
    except Exception:
        db.rollback()
        try:
            armazenamento.remover_objeto(key)
        except Exception:
            logging.getLogger(__name__).warning("Falha na compensacao de upload de capa.")
        raise
    return {"id": str(capa_id), "largura": SIZE[0], "altura": SIZE[1]}


def resposta(capa):
    if not capa:
        raise HTTPException(404, "Imagem de card nao encontrada.")
    body = armazenamento.obter_objeto(capa.object_key)["Body"]
    def chunks():
        try:
            yield from body.iter_chunks(chunk_size=65536)
        finally:
            body.close()
    return StreamingResponse(chunks(), media_type="image/jpeg", headers={"Cache-Control":"private, no-store",
        "X-Content-Type-Options":"nosniff"})


def previa(db, capa_id):
    capa = db.get(CapaInstrumento, capa_id)
    actor = db.info["usuario"]
    if not capa:
        raise HTTPException(404, "Imagem de card nao encontrada.")
    own = permissoes(db)
    if "*" not in own:
        linked = db.scalar(select(Instrumento.id).where(Instrumento.imagem_card_id == capa_id,
            filtro_escopo(db, Instrumento.id, "instrumentos_consultar")).limit(1))
        if not linked:
            if capa.criado_por != actor.id:
                raise HTTPException(404, "Imagem de card nao encontrada.")
            if not ({"instrumentos_incluir", "instrumentos_editar"} & own):
                try:
                    require_any_scope(db, "instrumentos_editar")
                except HTTPException:
                    raise HTTPException(404, "Imagem de card nao encontrada.") from None
    return resposta(capa)


def publica(db, instrumento_id, capa_id):
    from app.services.publicacao_service import publico
    instrument = publico(db, instrumento_id, lock=True)
    schema = db.get(PublicacaoInstrumento, instrument.publicacao_id).schema_json
    if str(instrument.imagem_card_id) != str(capa_id) or schema.get("imagem_card_id") != str(capa_id):
        raise HTTPException(404, "Imagem de card nao encontrada.")
    return resposta(db.get(CapaInstrumento, capa_id))
