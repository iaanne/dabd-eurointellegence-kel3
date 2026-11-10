from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    energy_charts_base_url: str
    open_meteo_archive_url: str
    http_timeout_seconds: float
    user_agent: str
    entsoe_api_url: str
    entsoe_api_token: str | None
    iceberg_catalog_uri: str
    iceberg_catalog_name: str
    iceberg_warehouse: str
    iceberg_namespace: str
    garage_s3_endpoint: str
    garage_s3_region: str
    garage_s3_access_key: str | None
    garage_s3_secret_key: str | None
    garage_bucket_bronze: str
    garage_bucket_warehouse: str


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def load_settings() -> Settings:
    """Baca konfigurasi dari environment, dengan nilai bawaan untuk pengembangan lokal."""
    load_dotenv()
    return Settings(
        data_dir=Path(os.getenv("EUROGRID_DATA_DIR", "data")).expanduser(),
        energy_charts_base_url=os.getenv(
            "ENERGY_CHARTS_BASE_URL", "https://api.energy-charts.info"
        ).rstrip("/"),
        open_meteo_archive_url=os.getenv(
            "OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive"
        ),
        http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
        user_agent=os.getenv(
            "EUROGRID_USER_AGENT", "eurogrid-intelligence/0.1 (proyek-kampus)"
        ),
        entsoe_api_url=os.getenv(
            "ENTSOE_API_URL", "https://web-api.tp.entsoe.eu/api"
        ),
        entsoe_api_token=_optional(os.getenv("ENTSOE_API_TOKEN")),
        iceberg_catalog_uri=os.getenv(
            "ICEBERG_CATALOG_URI", "http://localhost:8181"
        ).rstrip("/"),
        iceberg_catalog_name=os.getenv("ICEBERG_CATALOG_NAME", "eurogrid"),
        iceberg_warehouse=os.getenv(
            "ICEBERG_WAREHOUSE", "s3://eurogrid-warehouse/"
        ),
        iceberg_namespace=os.getenv("ICEBERG_NAMESPACE", "bronze"),
        garage_s3_endpoint=os.getenv(
            "GARAGE_S3_ENDPOINT", "http://localhost:3900"
        ).rstrip("/"),
        garage_s3_region=os.getenv("GARAGE_S3_REGION", "garage"),
        garage_s3_access_key=_optional(os.getenv("GARAGE_S3_ACCESS_KEY")),
        garage_s3_secret_key=_optional(os.getenv("GARAGE_S3_SECRET_KEY")),
        garage_bucket_bronze=os.getenv(
            "GARAGE_BUCKET_BRONZE", "eurogrid-bronze"
        ),
        garage_bucket_warehouse=os.getenv(
            "GARAGE_BUCKET_WAREHOUSE", "eurogrid-warehouse"
        ),
    )