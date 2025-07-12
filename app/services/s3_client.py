import boto3
from botocore.client import Config
from app.config import settings

# Force the correct region and signature version
s3 = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
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


async def upload_file_to_s3(file_content: bytes, key: str) -> bool:
    """Upload file content directly to S3"""
    try:
        print(f"Would upload file {key} to S3 (disabled for testing)")
        return True
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=file_content
        )
        return True
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return False