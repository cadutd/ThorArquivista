import hashlib
import uuid
from app.core.config import settings
from app.services.armazenamento_service import armazenamento


def test_copia_restaurada_s3_preserva_sha256_e_bytes():
    assert settings.app_env == "test" and settings.s3_bucket.endswith("test")
    prefix = "fase6_continuidade/" + uuid.uuid4().hex + "/"
    source, restored = prefix + "original", prefix + "restaurado"
    client = armazenamento.client()
    payload = b"Preservacao digital: copia de continuidade.\n" * 1000
    try:
        client.put_object(Bucket=settings.s3_bucket, Key=source, Body=payload, ContentType="application/octet-stream")
        client.copy_object(Bucket=settings.s3_bucket, Key=restored,
                           CopySource={"Bucket":settings.s3_bucket,"Key":source})
        obj = client.get_object(Bucket=settings.s3_bucket, Key=restored)
        digest, size = hashlib.sha256(), 0
        try:
            for part in obj["Body"].iter_chunks(chunk_size=4096):
                digest.update(part); size += len(part)
        finally:
            obj["Body"].close()
        assert digest.hexdigest() == hashlib.sha256(payload).hexdigest()
        assert size == len(payload)
    finally:
        client.delete_objects(Bucket=settings.s3_bucket, Delete={"Objects":[{"Key":source},{"Key":restored}]})
