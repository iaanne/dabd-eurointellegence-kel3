from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class BatchInfo:
    source: str
    dataset: str
    partition: dict[str, str]
    batch_id: str
    row_count: int
    ingest_time_utc: str
    license: str | None
    path: Path
    timestamp_min: str | None
    timestamp_max: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload


def _partition_label(partition: dict[str, str]) -> str:
    if not partition:
        return "-"
    return ",".join(f"{key}={value}" for key, value in partition.items())


def find_batches(data_dir: Path) -> list[BatchInfo]:
    """Cari semua batch Bronze dari berkas metadata.json."""
    root = Path(data_dir) / "bronze"
    if not root.exists():
        return []

    batches: list[BatchInfo] = []
    for metadata_path in sorted(root.rglob("metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        parquet_path = metadata_path.parent / "data.parquet"
        timestamp_min: str | None = None
        timestamp_max: str | None = None
        if parquet_path.exists():
            timestamps = pd.read_parquet(parquet_path, columns=["timestamp_utc"])[
                "timestamp_utc"
            ]
            if not timestamps.empty:
                timestamp_min = str(timestamps.min())
                timestamp_max = str(timestamps.max())

        batches.append(
            BatchInfo(
                source=str(metadata.get("source", "")),
                dataset=str(metadata.get("dataset", "")),
                partition={
                    str(key): str(value)
                    for key, value in (metadata.get("partition") or {}).items()
                },
                batch_id=str(metadata.get("batch_id", metadata_path.parent.name)),
                row_count=int(metadata.get("row_count", 0)),
                ingest_time_utc=str(metadata.get("ingest_time_utc", "")),
                license=metadata.get("license"),
                path=metadata_path.parent,
                timestamp_min=timestamp_min,
                timestamp_max=timestamp_max,
            )
        )

    return sorted(
        batches,
        key=lambda batch: (batch.source, batch.dataset, batch.ingest_time_utc),
    )


def format_batch_table(batches: list[BatchInfo]) -> str:
    if not batches:
        return "Belum ada batch. Jalankan `make demo` lebih dulu."

    headers = [
        "SUMBER",
        "DATASET",
        "PARTISI",
        "BATCH",
        "BARIS",
        "AWAL UTC",
        "AKHIR UTC",
    ]
    rows = [
        [
            batch.source,
            batch.dataset,
            _partition_label(batch.partition),
            batch.batch_id,
            f"{batch.row_count:,}".replace(",", "."),
            (batch.timestamp_min or "-")[:19],
            (batch.timestamp_max or "-")[:19],
        ]
        for batch in batches
    ]

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    lines = [
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(headers)),
        "  ".join("-" * width for width in widths),
    ]
    for row in rows:
        lines.append(
            "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        )
    return "\n".join(lines)


def newest_batch(batches: list[BatchInfo], dataset: str) -> BatchInfo | None:
    candidates = [batch for batch in batches if batch.dataset == dataset]
    if not candidates:
        return None
    return max(candidates, key=lambda batch: batch.ingest_time_utc)


def load_batch_frame(batch: BatchInfo) -> pd.DataFrame:
    return pd.read_parquet(batch.path / "data.parquet")


def format_frame(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "Tidak ada baris yang cocok."
    return frame.to_string(index=False)