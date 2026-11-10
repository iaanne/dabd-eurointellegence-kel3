from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from eurogrid.bronze.writer import (
    canonical_json_bytes,
    sha256_hex,
    write_bronze_batch,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2026-11-06T00:00:00Z", "2026-11-06T00:15:00Z"], utc=True
            ),
            "series_id": ["load", "load"],
            "value": [50000.0, 49800.0],
            "unit": ["MW", "MW"],
        }
    )


def test_checksum_tidak_bergantung_urutan_kunci() -> None:
    left = {"b": 1, "a": 2}
    right = {"a": 2, "b": 1}
    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert sha256_hex(canonical_json_bytes(left)) == sha256_hex(
        canonical_json_bytes(right)
    )


def test_ingest_ulang_tidak_membuat_batch_ganda(tmp_path: Path) -> None:
    frame = sample_frame()
    raw = {"endpoint": "public_power", "data": [{"timestamp": "x"}]}
    kwargs = dict(
        source="energy_charts",
        dataset="public_power",
        partition_values={"country": "de"},
        raw=raw,
        frame=frame,
        request_url="https://example.test/v2/public_power",
        request_params={"country": "de"},
        license="CC BY 4.0",
    )

    first = write_bronze_batch(tmp_path, **kwargs)
    second = write_bronze_batch(tmp_path, **kwargs)

    assert first.created is True
    assert second.created is False
    assert first.batch_id == second.batch_id
    assert first.row_count == 2

    batches = list(tmp_path.rglob("metadata.json"))
    assert len(batches) == 1

    batch_dir = first.path
    assert (batch_dir / "raw.json").exists()
    assert (batch_dir / "data.parquet").exists()
    parquet = pd.read_parquet(batch_dir / "data.parquet")
    assert len(parquet) == 2

    metadata = json.loads((batch_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["row_count"] == 2
    assert metadata["checksum_sha256"] == first.checksum_sha256
    assert metadata["license"] == "CC BY 4.0"


def test_field_volatil_tidak_mengubah_batch_id(tmp_path: Path) -> None:
    frame = sample_frame()
    common = dict(
        source="energy_charts",
        dataset="public_power",
        partition_values={"country": "de"},
        frame=frame,
        request_url="https://example.test/v2/public_power",
        request_params={"country": "de"},
    )

    first = write_bronze_batch(
        tmp_path,
        raw={"endpoint": "public_power", "generated_at": "2026-11-09T08:00:00Z", "data": [1]},
        **common,
    )
    second = write_bronze_batch(
        tmp_path,
        raw={"endpoint": "public_power", "generated_at": "2026-11-09T09:00:00Z", "data": [1]},
        **common,
    )

    assert first.batch_id == second.batch_id
    assert first.created is True
    assert second.created is False


def test_respons_berubah_membuat_batch_baru(tmp_path: Path) -> None:
    frame = sample_frame()
    common = dict(
        source="energy_charts",
        dataset="public_power",
        partition_values={"country": "de"},
        frame=frame,
        request_url="https://example.test/v2/public_power",
        request_params={"country": "de"},
    )

    first = write_bronze_batch(tmp_path, raw={"data": [1]}, **common)
    second = write_bronze_batch(tmp_path, raw={"data": [2]}, **common)

    assert first.batch_id != second.batch_id
    assert len(list(tmp_path.rglob("metadata.json"))) == 2