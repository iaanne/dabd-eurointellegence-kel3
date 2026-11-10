"""Publikasi batch Bronze lokal menjadi tabel Iceberg di Garage.

Batch mentah tetap ditulis ke ``data/bronze`` oleh :mod:`eurogrid.bronze.writer`.
Modul ini menggabungkan seluruh batch untuk satu dataset, membuang duplikat, lalu
menulis ulang tabel Iceberg di namespace ``bronze``. Penulisan ulang penuh dipilih
karena volume Bronze masih kecil dan hasilnya selalu sama untuk masukan yang sama,
sehingga aman dijalankan berulang.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from ..config import Settings, load_settings
from ..inspect import find_batches, load_batch_frame


@dataclass(frozen=True)
class PublishResult:
    table: str
    rows: int
    created: bool
    location: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "rows": self.rows,
            "created": self.created,
            "location": self.location,
        }


def table_name(source: str, dataset: str) -> str:
    """Nama tabel Iceberg datar di namespace Bronze."""
    return f"{source}_{dataset}"


def build_catalog(settings: Settings | None = None):
    """Buat katalog PyIceberg REST dengan kredensial Garage dari pengaturan."""
    settings = settings or load_settings()
    if not settings.garage_s3_access_key or not settings.garage_s3_secret_key:
        raise ValueError(
            "GARAGE_S3_ACCESS_KEY dan GARAGE_S3_SECRET_KEY belum diisi di .env."
        )

    from pyiceberg.catalog import load_catalog

    return load_catalog(
        settings.iceberg_catalog_name,
        **{
            "type": "rest",
            "uri": settings.iceberg_catalog_uri,
            "warehouse": settings.iceberg_warehouse,
            "s3.endpoint": settings.garage_s3_endpoint,
            "s3.access-key-id": settings.garage_s3_access_key,
            "s3.secret-access-key": settings.garage_s3_secret_key,
            "s3.region": settings.garage_s3_region,
            "s3.path-style-access": "true",
        },
    )


def collect_frames(data_dir) -> dict[str, pd.DataFrame]:
    """Gabungkan semua batch lokal menjadi satu frame per nama tabel."""
    grouped: dict[str, list] = {}
    for batch in find_batches(data_dir):
        grouped.setdefault(table_name(batch.source, batch.dataset), []).append(batch)

    frames: dict[str, pd.DataFrame] = {}
    for name, batches in grouped.items():
        parts = [load_batch_frame(batch) for batch in batches]
        frame = pd.concat(parts, ignore_index=True, sort=False)
        frames[name] = _normalize(frame)
    return frames


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "timestamp_utc" in frame.columns:
        frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)

    if "series_id" in frame.columns:
        keys = ["series_id", "timestamp_utc"]
    elif "variable" in frame.columns:
        keys = [key for key in ("location", "variable", "timestamp_utc") if key in frame.columns]
    else:
        keys = ["timestamp_utc"]

    keys = [key for key in keys if key in frame.columns]
    if keys:
        frame = frame.drop_duplicates(subset=keys, keep="last")
    if "timestamp_utc" in frame.columns:
        frame = frame.sort_values("timestamp_utc", ignore_index=True)
    return frame


def _to_arrow(frame: pd.DataFrame):
    import pyarrow as pa

    arrays = []
    fields = []
    for name in frame.columns:
        series = frame[name]
        if pd.api.types.is_datetime64_any_dtype(series):
            if getattr(series.dt, "tz", None) is None:
                series = series.dt.tz_localize("UTC")
            else:
                series = series.dt.tz_convert("UTC")
            arrow_type = pa.timestamp("us", tz="UTC")
            arrays.append(pa.array(series, type=arrow_type))
        elif pd.api.types.is_bool_dtype(series):
            arrow_type = pa.bool_()
            arrays.append(pa.array(series, type=arrow_type))
        elif pd.api.types.is_integer_dtype(series):
            arrow_type = pa.int64()
            arrays.append(pa.array(series, type=arrow_type))
        elif pd.api.types.is_float_dtype(series):
            arrow_type = pa.float64()
            arrays.append(pa.array(series, type=arrow_type))
        else:
            arrow_type = pa.string()
            arrays.append(pa.array(series.astype("string"), type=arrow_type))
        fields.append(pa.field(name, arrow_type, nullable=True))

    return pa.Table.from_arrays(arrays, schema=pa.schema(fields))


def publish_frames(
    frames: dict[str, pd.DataFrame],
    *,
    settings: Settings | None = None,
    only: Iterable[str] | None = None,
) -> list[PublishResult]:
    settings = settings or load_settings()
    selected = set(only) if only else None
    catalog = build_catalog(settings)
    catalog.create_namespace_if_not_exists(settings.iceberg_namespace)

    results: list[PublishResult] = []
    for name, frame in sorted(frames.items()):
        if selected is not None and name not in selected:
            continue
        identifier = f"{settings.iceberg_namespace}.{name}"
        arrow_table = _to_arrow(frame)
        created = False

        if catalog.table_exists(identifier):
            table = catalog.load_table(identifier)
            existing_columns = [field.name for field in table.schema().fields]
            if existing_columns != arrow_table.column_names:
                catalog.drop_table(identifier)
                table = catalog.create_table(identifier, schema=arrow_table.schema)
                created = True
            else:
                table.overwrite(arrow_table)
        else:
            table = catalog.create_table(identifier, schema=arrow_table.schema)
            created = True
            table.append(arrow_table)

        results.append(
            PublishResult(
                table=identifier,
                rows=arrow_table.num_rows,
                created=created,
                location=table.location(),
            )
        )
    return results


def publish_bronze(
    *,
    settings: Settings | None = None,
    only: Iterable[str] | None = None,
) -> list[PublishResult]:
    settings = settings or load_settings()
    frames = collect_frames(settings.data_dir)
    if not frames:
        return []
    return publish_frames(frames, settings=settings, only=only)


def upload_bronze(*, settings: Settings | None = None) -> dict[str, Any]:
    """Salin batch mentah dari ``data/bronze`` ke bucket Bronze di Garage.

    Salinan ini adalah arsip replay. Tabel Iceberg di ``eurogrid-warehouse``
    adalah lapisan yang dibaca Silver.
    """
    settings = settings or load_settings()
    root = Path(settings.data_dir) / "bronze"
    if not root.exists() or not any(root.iterdir()):
        return {"bucket": settings.garage_bucket_bronze, "files": 0, "bytes": 0}

    import shutil

    import pyarrow.fs as pafs

    filesystem = pafs.S3FileSystem(
        access_key=settings.garage_s3_access_key,
        secret_key=settings.garage_s3_secret_key,
        endpoint_override=settings.garage_s3_endpoint,
        region=settings.garage_s3_region,
        scheme="http",
    )

    files = 0
    total_bytes = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        key = f"{settings.garage_bucket_bronze}/bronze/{relative}"
        with path.open("rb") as source, filesystem.open_output_stream(key) as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
        files += 1
        total_bytes += path.stat().st_size

    return {
        "bucket": settings.garage_bucket_bronze,
        "files": files,
        "bytes": total_bytes,
    }