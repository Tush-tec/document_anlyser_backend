import boto3
from botocore.client import Config
from app.core.config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name=settings.S3_REGION,
    config=Config(signature_version="s3v4"),
)

def upload_bytes(key: str, data: bytes, content_type: str) -> None:
    _s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)

def download_bytes(key: str) -> bytes:
    return _s3.get_object(Bucket=settings.S3_BUCKET, Key=key)["Body"].read()

def delete_prefix(prefix: str) -> None:
    resp = _s3.list_objects_v2(Bucket=settings.S3_BUCKET, Prefix=prefix)
    for obj in resp.get("Contents", []):
        _s3.delete_object(Bucket=settings.S3_BUCKET, Key=obj["Key"])