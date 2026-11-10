from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from eurogrid.bronze.writer import write_bronze_batch
from eurogrid.cli import main
from eurogrid.inspect import find_batches, format_batch_table, newest_batch


def frame(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2026-11-06T00:00:00Z", "2026-11-06T00:15:00Z"], utc=True
            ),
            "series_id": ["load", "load"],
            "value": values,
            "unit": ["MW", "MW"],
        }
    )


def write(tmp_path: Path, dataset: str, values: list[float], raw_id: int):
    return write_bronze_batch(
        tmp_path,
        source="energy_charts",
        dataset=dataset,
        partition_values={"country": "de"},
        raw={"data": [raw_id]},
        frame=frame(values),
        request_url="https://example.test",
        request_params={},
        license="CC BY 4.0",
    )


def test_find_batches_membaca_metadata_dan_rentang_waktu(tmp_path: Path) -> None:
    write(tmp_path, "public_power", [1.0, 2.0], 1)
    write(tmp_path, "price", [3.0, 4.0], 2)

    batches = find_batches(tmp_path)

    assert len(batches) == 2
    datasets = {batch.dataset for batch in batches}
    assert datasets == {"public_power", "price"}
    sample = next(batch for batch in batches if batch.dataset == "public_power")
    assert sample.row_count == 2
    assert sample.timestamp_min.startswith("2026-11-06 00:00")
    assert sample.timestamp_max.startswith("2026-11-06 00:15")

    table = format_batch_table(batches)
    assert "public_power" in table
    assert "BARIS" in table


def test_newest_batch_memilih_yang_terbaru(tmp_path: Path) -> None:
    first = write(tmp_path, "public_power", [1.0, 2.0], 1)
    second = write(tmp_path, "public_power", [3.0, 4.0], 2)

    batches = find_batches(tmp_path)
    newest = newest_batch(batches, "public_power")

    assert newest is not None
    assert {first.batch_id, second.batch_id} == {
        batch.batch_id for batch in batches
    }
    assert newest.ingest_time_utc >= min(batch.ingest_time_utc for batch in batches)


def test_cli_show_menangani_kolom_variable(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("EUROGRID_DATA_DIR", str(tmp_path))
    frame = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2026-11-06T00:00:00Z", "2026-11-06T01:00:00Z"], utc=True
            ),
            "location": ["berlin", "berlin"],
            "variable": ["temperature_2m", "temperature_2m"],
            "value": [7.5, 7.1],
            "unit": ["°C", "°C"],
        }
    )
    write_bronze_batch(
        tmp_path,
        source="open_meteo",
        dataset="weather_hourly",
        partition_values={"country": "de", "location": "berlin"},
        raw={"data": [1]},
        frame=frame,
        request_url="https://example.test",
        request_params={},
        license="CC BY 4.0",
    )

    assert main(["show", "--dataset", "weather_hourly", "--series", "temperature_2m"]) == 0
    output = capsys.readouterr().out
    assert "temperature_2m" in output
    assert "7.5" in output


def test_cli_list_json(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("EUROGRID_DATA_DIR", str(tmp_path))
    write(tmp_path, "public_power", [1.0, 2.0], 1)

    assert main(["list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert len(payload) == 1
    assert payload[0]["dataset"] == "public_power"
    assert payload[0]["row_count"] == 2