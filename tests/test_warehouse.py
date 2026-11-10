from __future__ import annotations

from pathlib import Path

import pandas as pd

from eurogrid.bronze.warehouse import collect_frames, table_name
from eurogrid.bronze.writer import write_bronze_batch


def _frame(value: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp_utc": pd.Timestamp("2026-11-03T00:00:00Z"),
                "dataset": "actual_load",
                "series_id": "1",
                "series_name": "actual_load",
                "value": value,
                "unit": "MAW",
            },
            {
                "timestamp_utc": pd.Timestamp("2026-11-03T00:15:00Z"),
                "dataset": "actual_load",
                "series_id": "1",
                "series_name": "actual_load",
                "value": value + 1,
                "unit": "MAW",
            },
        ]
    )


def _tulis(tmp_path: Path, value: float, raw: dict) -> None:
    write_bronze_batch(
        tmp_path,
        source="entsoe",
        dataset="actual_load",
        partition_values={"country": "de"},
        raw=raw,
        frame=_frame(value),
        request_url="https://contoh",
        request_params={},
    )


def test_table_name_menggabungkan_sumber_dan_dataset() -> None:
    assert table_name("energy_charts", "public_power") == "energy_charts_public_power"
    assert table_name("entsoe", "actual_load") == "entsoe_actual_load"


def test_collect_frames_menggabungkan_batch_dan_membuang_duplikat(
    tmp_path: Path,
) -> None:
    _tulis(tmp_path, value=10.0, raw={"versi": 1})
    _tulis(tmp_path, value=20.0, raw={"versi": 2})

    frames = collect_frames(tmp_path)

    assert list(frames) == ["entsoe_actual_load"]
    frame = frames["entsoe_actual_load"]
    assert len(frame) == 2
    assert frame["value"].tolist() == [20.0, 21.0]
    assert frame["timestamp_utc"].is_monotonic_increasing