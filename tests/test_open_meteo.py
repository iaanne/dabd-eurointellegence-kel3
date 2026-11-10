from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from eurogrid.sources import open_meteo

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_cuaca_dinormalkan_menjadi_tabel_panjang() -> None:
    frame = open_meteo.to_long_frame(load("open_meteo_berlin.json"), location="berlin")

    assert len(frame) == 9
    assert set(frame["variable"]) == {
        "temperature_2m",
        "wind_speed_10m",
        "shortwave_radiation",
    }
    assert frame["location"].unique().tolist() == ["berlin"]
    assert frame["unit"].notna().all()
    assert frame["timestamp_utc"].iloc[0] == pd.Timestamp("2026-11-02T00:00:00Z")


def test_payload_kosong_tetap_memiliki_kolom() -> None:
    frame = open_meteo.to_long_frame({"hourly": {"time": []}}, location="berlin")
    assert len(frame) == 0
    assert list(frame.columns) == open_meteo.COLUMNS