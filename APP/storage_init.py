import logging
import time

from botocore.exceptions import BotoCoreError, ClientError

from APP.core.config import get_settings
from APP.core.logging import configure_logging
from APP.core.storage import create_storage

logger = logging.getLogger(__name__)
RETRY_SECONDS = 1


def main():
    settings = get_settings()
    configure_logging(settings.log_level)
    storage = create_storage(settings)
    if storage is None:
        raise RuntimeError("S3 configuration is required")
    deadline = time.monotonic() + settings.s3_init_timeout_seconds
    try:
        while True:
            try:
                try:
                    storage.client.head_bucket(Bucket=settings.s3_bucket)
                except ClientError as error:
                    if error.response["Error"]["Code"] not in (
                        "404",
                        "NoSuchBucket",
                        "NotFound",
                    ):
                        raise
                    args = {"Bucket": settings.s3_bucket}
                    if settings.s3_region != "us-east-1":
                        args["CreateBucketConfiguration"] = {
                            "LocationConstraint": settings.s3_region
                        }
                    storage.client.create_bucket(**args)
                if settings.s3_cors_origins:
                    try:
                        storage.client.put_bucket_cors(
                            Bucket=settings.s3_bucket,
                            CORSConfiguration={
                                "CORSRules": [
                                    {
                                        "AllowedOrigins": settings.s3_cors_origins,
                                        "AllowedMethods": ["GET", "HEAD"],
                                        "AllowedHeaders": ["*"],
                                        "ExposeHeaders": [
                                            "Content-Length",
                                            "Content-Range",
                                            "Accept-Ranges",
                                        ],
                                    }
                                ]
                            },
                        )
                    except ClientError as error:
                        if error.response["Error"]["Code"] != "NotImplemented":
                            raise
                        logger.info(
                            "Bucket CORS API unavailable; use provider CORS configuration"
                        )
                logger.info("Object storage initialized")
                return
            except (ClientError, BotoCoreError):
                if time.monotonic() >= deadline:
                    raise RuntimeError("Object storage initialization failed") from None
                time.sleep(RETRY_SECONDS)
    finally:
        storage.close()


if __name__ == "__main__":
    main()
