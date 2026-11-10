from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import respx
from httpx import Response

from eurogrid.ingest import ingest_weather, resolve_window

FIXTURES = Path(__file__).parent / "fixtures"


def test_resolve_window_tujuh_hari() -> None:
    assert resolve_window(7, today=date(2026, 11, 10)) == ("2026-11-03", "2026-11-09")


def test_resolve_window_satu_hari_berakhir_kemarin() -> None:
    assert resolve_window(1, today=date(2026, 11, 10)) == ("2026-11-09", "2026-11-09")


def test_resolve_window_menolak_nol() -> None:
    with pytest.raises(ValueError):
        resolve_window(0)


def test_ingest_weather_menulis_batch_dan_idempoten(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("EUROGRID_DATA_DIR", str(tmp_path))
    payload = json.loads(
        (FIXTURES / "open_meteo_berlin.json").read_text(encoding="utf-8")
    )

    def panggil() -> dict:
        with respx.mock(assert_all_called=True) as mock:
            mock.get("https://archive-api.open-meteo.com/v1/archive").mock(
                return_value=Response(200, json=payload)
            )
            return ingest_weather(start="2026-11-02", end="2026-11-08")

    pertama = panggil()
    assert pertama["dataset"] == "weather_hourly"
    assert pertama["created"] is True
    assert pertama["row_count"] > 0
    assert len(list(tmp_path.rglob("data.parquet"))) == 1

    kedua = panggil()
    assert kedua["batch_id"] == pertama["batch_id"]
    assert kedua["created"] is False
    assert len(list(tmp_path.rglob("data.parquet"))) == 1
