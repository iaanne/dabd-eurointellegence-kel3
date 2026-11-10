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
    )