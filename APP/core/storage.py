from typing import Annotated

import boto3
from botocore.config import Config
from fastapi import Depends, HTTPException, Request


class ObjectStorage:
    def __init__(self, settings):
        self.settings = settings
        credentials = dict(
            aws_access_key_id=settings.s3_access_key.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name=settings.s3_region,
        )
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=settings.s3_connect_timeout_seconds,
            read_timeout=settings.s3_read_timeout_seconds,
            retries={"max_attempts": 2},
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=str(settings.s3_endpoint_url),
            config=config,
            **credentials,
        )
        self.public_client = boto3.client(
            "s3",
            endpoint_url=str(
                settings.s3_public_endpoint_url or settings.s3_endpoint_url
            ),
            config=config,
            **credentials,
        )

    def put(self, key, body, content_type):
        self.client.put_object(
            Bucket=self.settings.s3_bucket, Key=key, Body=body, ContentType=content_type
        )

    def delete(self, key):
        self.client.delete_object(Bucket=self.settings.s3_bucket, Key=key)

    def url(self, key, content_type):
        return self.public_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.settings.s3_bucket,
                "Key": key,
                "ResponseContentType": content_type,
            },
            ExpiresIn=self.settings.s3_presign_ttl_seconds,
        )

    def close(self):
        self.client.close()
        self.public_client.close()


def create_storage(settings):
    return ObjectStorage(settings) if settings.s3_endpoint_url is not None else None


def get_storage(request: Request):
    storage = request.app.state.storage
    if storage is None:
        raise HTTPException(status_code=503, detail="Object storage is not configured")
    return storage


StorageDependency = Annotated[ObjectStorage, Depends(get_storage)]
