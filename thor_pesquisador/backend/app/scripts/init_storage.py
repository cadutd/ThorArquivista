"""Explicit, idempotent local bucket initialization. Never makes the bucket public."""
from botocore.exceptions import ClientError
from app.core.config import settings
from app.services.armazenamento_service import armazenamento


def main():
    if settings.app_env not in {"dev", "test"}:
        raise RuntimeError("Configure o bucket e as permissoes com a equipe de infraestrutura.")
    client = armazenamento.client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError as exc:
        if exc.response["Error"]["Code"] not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        options = {"Bucket": settings.s3_bucket}
        if settings.s3_region != "us-east-1":
            options["CreateBucketConfiguration"] = {"LocationConstraint": settings.s3_region}
        client.create_bucket(**options)
    print("Bucket privado disponivel:", settings.s3_bucket)


if __name__ == "__main__":
    main()
