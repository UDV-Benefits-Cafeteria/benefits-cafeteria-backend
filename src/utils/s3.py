from fastapi_storages import FileSystemStorage, S3Storage

from src.config import get_settings

settings = get_settings()


class PublicAssetS3Storage(S3Storage):
    AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
    AWS_S3_BUCKET_NAME = settings.AWS_S3_BUCKET_NAME
    AWS_S3_ENDPOINT_URL = settings.AWS_S3_ENDPOINT_URL
    AWS_DEFAULT_ACL = settings.AWS_DEFAULT_ACL
    AWS_S3_USE_SSL = settings.AWS_S3_USE_SSL
    AWS_S3_CUSTOM_DOMAIN = f"cloud.{settings.DOMAIN}"


storage = (
    PublicAssetS3Storage() if not settings.DEBUG else FileSystemStorage(path="/tmp")
)
