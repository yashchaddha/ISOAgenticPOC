import boto3
from botocore.client import Config
from app.config import settings

# Force the correct region and signature version
s3 = boto3.client(
    "s3",
    region_name=settings.aws_region,
    endpoint_url=f"https://s3.{settings.aws_region}.amazonaws.com",
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"}
    )
)


def create_presigned_url(key: str, expires_in: int = 3600) -> str:
    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
        HttpMethod="PUT"     # explicitly generate a PUT URL
    )