import os
from functools import lru_cache
import boto3
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    users_table: str = "at-sv-users"
    transactions_table: str = "at-sv-transactions"
    tax_declarations_table: str = "at-sv-tax-declarations"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_dynamodb_client():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("dynamodb", **kwargs)


def get_dynamodb_resource():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.resource("dynamodb", **kwargs)
