from __future__ import annotations

import hashlib
from io import BytesIO
import warnings

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


class ArmazenamentoS3:
    def client(self):
        if not settings.s3_bucket or not settings.s3_endpoint_url:
            raise HTTPException(503, "Armazenamento S3 nao configurado.")
        return boto3.client(
            "s3", endpoint_url=settings.s3_endpoint_url, region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id or None,
            aws_secret_access_key=settings.s3_secret_access_key or None,
            config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=30,
                          retries={"max_attempts": 2}, s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"}),
        )

    def salvar_upload(self, key: str, conteudo: bytes, mime_type: str):
        try:
            self.client().put_object(Bucket=settings.s3_bucket, Key=key, Body=conteudo, ContentType=mime_type)
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(503, "Falha ao salvar imagem no armazenamento.") from exc

    def obter_url_acesso(self, key: str) -> str:
        return self.client().generate_presigned_url(
            "get_object", Params={"Bucket": settings.s3_bucket, "Key": key}, ExpiresIn=settings.s3_url_expiration,
        )

    def obter_objeto(self, key: str):
        try:
            return self.client().get_object(Bucket=settings.s3_bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(503, "Imagem indisponivel no armazenamento.") from exc

    def remover_objeto(self, key: str):
        try:
            self.client().delete_object(Bucket=settings.s3_bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(503, "Falha ao remover objeto do armazenamento.") from exc

    @staticmethod
    def calcular_checksum(conteudo: bytes) -> str:
        return hashlib.sha256(conteudo).hexdigest()


def validar_imagem(conteudo: bytes, mime_type: str):
    if not conteudo or len(conteudo) > settings.upload_max_bytes:
        raise HTTPException(413, "Arquivo vazio ou maior que o limite permitido.")
    if mime_type not in settings.upload_allowed_mime_types:
        raise HTTPException(422, "Tipo de arquivo nao permitido.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(conteudo)) as image:
                actual_mime = Image.MIME.get(image.format)
                largura, altura = image.size
                image.verify()
            if actual_mime != mime_type:
                raise HTTPException(422, "Conteudo do arquivo nao corresponde ao MIME informado.")
            with Image.open(BytesIO(conteudo)) as image:
                image.thumbnail((360, 360))
                thumb = BytesIO()
                image.convert("RGB").save(thumb, format="JPEG", quality=80)
                return largura, altura, thumb.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise HTTPException(422, "Imagem invalida ou dimensoes excessivas.") from exc


armazenamento = ArmazenamentoS3()
