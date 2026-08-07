"""Script to config endpoints and connections"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True, slots=True)
class DataEndpointsConfig:
    products_url:str = "https://dummyjson.com/products"
    customers_url:str = "https://dummyjson.com/users"
    carts_url:str = "https://dummyjson.com/carts"
    page_size: int = int(os.getenv("EXTRACT_PAGE_SIZE", "100"))
    timeout_seconds: int = int(os.getenv("EXTRACT_TIMEOUT_SECONDS", "10"))
    max_retries: int = int(os.getenv("EXTRACT_MAX_RETRIES", "3"))

@dataclass
class DataWarehouseConfig:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER", "")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    database: str = os.getenv("POSTGRES_DB", "dw")

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

@dataclass
class DataLakeConfig:
    host: str = os.getenv("MINIO_HOST", "localhost")
    port: int = int(os.getenv("MINIO_PORT", "9000"))
    access_key: str = os.getenv("MINIO_ROOT_USER", "")
    secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "")
    secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    region: str = os.getenv("MINIO_REGION", "us-east-1")
    bronze_bucket: str = os.getenv("MINIO_BRONZE_BUCKET", "bronze")
    silver_bucket: str = os.getenv("MINIO_SILVER_BUCKET", "silver")

    @property
    def endpoint_url(self) -> str:
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.host}:{self.port}"


endpoints_config = DataEndpointsConfig()
warehouse_config = DataWarehouseConfig()
lake_config = DataLakeConfig()
