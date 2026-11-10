from __future__ import annotations

from typing import Any

import httpx
import pandas as pd

from ..http import get_json

# Endpoint Energy-Charts API v2 yang dipakai proyek ini.
# Parameter wajib: "country" untuk semua endpoint, kecuali price yang memakai "bzn".
SUPPORTED_DATASETS = {
    "public_power",
    "total_power",
    "installed_power",
    "price",
    "cbet",
    "cbpf",
    "signal",
}

COLUMNS = [
    "timestamp_utc",
    "timestamp_local",
    "dataset",
    "series_id",
    "series_name",
    "value",
    "unit",
    "resolution",
    "country",
    "bidding_zone",
    "license",
    "generated_at",
    "available_from",
    "available_until",
]


def build_params(
    dataset: str,
    start: str,
    end: str,
    country: str | None = None,
    bzn: str | None = None,
) -> dict[str, str]:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Dataset tidak didukung: {dataset}")
    params = {"start": start, "end": end}
    if dataset == "price":
        if not bzn:
            raise ValueError("Dataset price membutuhkan bidding zone (bzn).")
        params["bzn"] = bzn
    else:
        if not country:
            raise ValueError(f"Dataset {dataset} membutuhkan country.")
        params["country"] = country
    return params


def fetch(
    client: httpx.Client,
    base_url: str,
    dataset: str,
    params: dict[str, str],
) -> dict[str, Any]:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Dataset tidak didukung: {dataset}")
    url = f"{base_url}/v2/{dataset}"
    return get_json(client, url, params)


def to_long_frame(envelope: dict[str, Any]) -> pd.DataFrame:
    """Ubah bungkus respons Energy-Charts menjadi tabel panjang per seri per interval."""
    data = envelope.get("data") or []
    if not data:
        return pd.DataFrame(columns=COLUMNS)

    series_names = {
        item.get("id"): item.get("name", item.get("id"))
        for item in envelope.get("series") or []
    }
    timestamps = pd.to_datetime([point["timestamp"] for point in data], utc=True)

    records: list[tuple[Any, ...]] = []
    for timestamp_utc, point in zip(timestamps, data, strict=True):
        values = point.get("values") or {}
        for series_id, value in values.items():
            records.append(
                (
                    timestamp_utc,
                    point["timestamp"],
                    envelope.get("endpoint"),
                    series_id,
                    series_names.get(series_id, series_id),
                    value,
                )
            )

    frame = pd.DataFrame(
        records,
        columns=[
            "timestamp_utc",
            "timestamp_local",
            "dataset",
            "series_id",
            "series_name",
            "value",
        ],
    )
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["unit"] = envelope.get("unit")
    frame["resolution"] = envelope.get("resolution")
    frame["country"] = envelope.get("country")
    frame["bidding_zone"] = envelope.get("bidding_zone")
    frame["license"] = envelope.get("license")
    frame["generated_at"] = envelope.get("generated_at")
    frame["available_from"] = envelope.get("available_from")
    frame["available_until"] = envelope.get("available_until")

    frame = frame.drop_duplicates(
        subset=["dataset", "series_id", "timestamp_utc"], keep="last"
    )
    frame = frame.sort_values(["timestamp_utc", "series_id"], ignore_index=True)
    return frame[COLUMNS]