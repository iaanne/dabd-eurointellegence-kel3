from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from eurogrid.sources import energy_charts

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_public_power_dinormalkan_ke_utc_dan_bentuk_panjang() -> None:
    frame = energy_charts.to_long_frame(load("energy_charts_public_power.json"))

    assert len(frame) == 9
    assert set(frame["series_id"]) == {"solar", "wind_onshore", "load"}
    assert frame["dataset"].unique().tolist() == ["public_power"]
    assert frame["unit"].unique().tolist() == ["MW"]
    assert frame["resolution"].unique().tolist() == ["PT15M"]
    assert frame["license"].iloc[0].startswith("CC BY 4.0")

    first = frame.iloc[0]
    assert first["timestamp_local"] == "2026-11-06T00:00:00+01:00"
    assert first["timestamp_utc"] == pd.Timestamp("2026-11-05T23:00:00Z")


def test_price_memakai_bidding_zone() -> None:
    frame = energy_charts.to_long_frame(load("energy_charts_price.json"))

    assert len(frame) == 3
    assert frame["series_id"].unique().tolist() == ["day_ahead_price"]
    assert frame["bidding_zone"].unique().tolist() == ["DE-LU"]
    assert frame["unit"].unique().tolist() == ["EUR / MWh"]


def test_build_params_price_membutuhkan_bzn() -> None:
    params = energy_charts.build_params(
        "price", "2026-11-06", "2026-11-06", bzn="DE-LU"
    )
    assert params == {
        "start": "2026-11-06",
        "end": "2026-11-06",
        "bzn": "DE-LU",
    }


def test_data_kosong_tetap_memiliki_kolom() -> None:
    frame = energy_charts.to_long_frame({"endpoint": "public_power", "data": []})
    assert len(frame) == 0
    assert list(frame.columns) == energy_charts.COLUMNS