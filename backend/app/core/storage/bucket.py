"""S3-compatible bucket access for stored files."""
from functools import lru_cache

from app.core.settings import settings

CONNECT_TIMEOUT_SECONDS = 5
READ_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 3
EXPLICIT_ADDRESS_STYLES = ("path", "virtual")
NOT_FOUND_CODES = ("404", "NoSuchKey", "NotFound")


def is_active() -> bool:
    # Berkas demo disimpan di tabel skema demo, sehingga ikut hilang bersih saat skema itu dihapus dan tidak pernah masuk bucket asli.
    return settings.bucket_active and not settings.demo_mode


@lru_cache(maxsize=1)
def _client():
    import boto3
    from botocore.config import Config

    style = settings.bucket_address_style.strip().lower()
    s3_options = {"addressing_style": style} if style in EXPLICIT_ADDRESS_STYLES else {}
    return boto3.client(
        "s3",
        endpoint_url=settings.bucket_endpoint,
        aws_access_key_id=settings.bucket_access_key_id,
        aws_secret_access_key=settings.bucket_secret_access_key,
        region_name=settings.bucket_region or "auto",
        config=Config(
            signature_version="s3v4",
            s3=s3_options,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
            read_timeout=READ_TIMEOUT_SECONDS,
            retries={"max_attempts": MAX_ATTEMPTS, "mode": "standard"},
        ),
    )


def put(key: str, content: bytes, content_type: str) -> None:
    """Raises on failure so the caller never believes a missing file was stored."""
    _client().put_object(Bucket=settings.bucket_name, Key=key, Body=content, ContentType=content_type)


def get(key: str) -> bytes | None:
    """The object's bytes, or None when it does not exist."""
    from botocore.exceptions import ClientError

    try:
        found = _client().get_object(Bucket=settings.bucket_name, Key=key)
    except ClientError as error:
        if str(error.response.get("Error", {}).get("Code", "")) in NOT_FOUND_CODES:
            return None
        raise
    return found["Body"].read()


def delete(key: str) -> None:
    _client().delete_object(Bucket=settings.bucket_name, Key=key)


def size_of(key: str) -> int | None:
    """Size in bytes without downloading the object, or None when it does not exist."""
    from botocore.exceptions import ClientError

    try:
        head = _client().head_object(Bucket=settings.bucket_name, Key=key)
    except ClientError as error:
        if str(error.response.get("Error", {}).get("Code", "")) in NOT_FOUND_CODES:
            return None
        raise
    return int(head.get("ContentLength", 0))
