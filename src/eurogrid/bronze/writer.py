from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

SCHEMA_VERSION = "1"

# Field yang berubah pada setiap panggilan walaupun datanya sama. Field ini tidak
# ikut dihitung dalam checksum supaya ingest ulang tetap idempoten.
VOLATILE_KEYS = ("generated_at", "generationtime_ms")


@dataclass(frozen=True)
class WriteResult:
    batch_id: str
    path: Path
    created: bool
    row_count: int
    checksum_sha256: str


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialisasi deterministik supaya checksum tidak berubah karena urutan kunci."""
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def content_checksum_payload(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Salinan payload tanpa field yang berubah pada setiap panggilan."""
    return {key: value for key, value in raw.items() if key not in VOLATILE_KEYS}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_bronze_batch(
    root: Path,
    *,
    source: str,
    dataset: str,
    partition_values: Mapping[str, str],
    raw: Mapping[str, Any],
    frame: pd.DataFrame,
    request_url: str,
    request_params: Mapping[str, Any],
    license: str | None = None,
    extra_metadata: Mapping[str, Any] | None = None,
) -> WriteResult:
    """Tulis satu batch Bronze: raw.json, data.parquet, dan metadata.json.

    Direktori batch ditentukan oleh checksum isi respons. Ingest ulang dengan respons
    identik akan menghasilkan batch_id yang sama dan tidak menulis apa pun.
    """
    raw_bytes = canonical_json_bytes(raw)
    raw_checksum = sha256_hex(raw_bytes)
    checksum = sha256_hex(canonical_json_bytes(content_checksum_payload(raw)))
    batch_id = checksum[:16]

    partition = [f"{key}={value}" for key, value in partition_values.items()]
    batch_dir = Path(root).resolve() / "bronze" / source / dataset / Path(*partition) / f"batch_id={batch_id}"
    metadata_path = batch_dir / "metadata.json"

    if metadata_path.exists():
        existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        return WriteResult(
            batch_id=batch_id,
            path=batch_dir,
            created=False,
            row_count=int(existing.get("row_count", len(frame))),
            checksum_sha256=checksum,
        )

    batch_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = batch_dir.parent / f".tmp-{batch_id}-{uuid.uuid4().hex[:8]}"
    tmp_dir.mkdir()

    try:
        (tmp_dir / "raw.json").write_bytes(raw_bytes)
        frame.to_parquet(tmp_dir / "data.parquet", index=False)

        source_metadata = {
            key: raw.get(key)
            for key in (
                "schema_version",
                "endpoint",
                "country",
                "bidding_zone",
                "timezone",
                "resolution",
                "unit",
                "generated_at",
                "available_from",
                "available_until",
                "license",
            )
            if key in raw
        }
        metadata = {
            "schema_version": SCHEMA_VERSION,
            "batch_id": batch_id,
            "source": source,
            "dataset": dataset,
            "partition": dict(partition_values),
            "request": {"url": request_url, "params": dict(request_params)},
            "checksum_sha256": checksum,
            "checksum_scope": "raw tanpa field volatil",
            "checksum_ignored_keys": list(VOLATILE_KEYS),
            "raw_checksum_sha256": raw_checksum,
            "row_count": int(len(frame)),
            "column_names": list(frame.columns),
            "ingest_time_utc": _now_utc(),
            "license": license,
            "source_metadata": source_metadata,
            "extra": dict(extra_metadata or {}),
        }
        (tmp_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        try:
            tmp_dir.rename(batch_dir)
        except OSError:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            if not metadata_path.exists():
                raise
            existing = json.loads(metadata_path.read_text(encoding="utf-8"))
            return WriteResult(
                batch_id=batch_id,
                path=batch_dir,
                created=False,
                row_count=int(existing.get("row_count", len(frame))),
                checksum_sha256=checksum,
            )
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    return WriteResult(
        batch_id=batch_id,
        path=batch_dir,
        created=True,
        row_count=int(len(frame)),
        checksum_sha256=checksum,
    )