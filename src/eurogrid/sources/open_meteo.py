from __future__ import annotations

from typing import Any

import httpx
import pandas as pd

from ..http import get_json

DEFAULT_VARIABLES = (
    "temperature_2m",
    "wind_speed_10m",
    "shortwave_radiation",
    "precipitation",
)

LICENSE = (
    "CC BY 4.0, non-komersial, atribusi Open-Meteo.com. "
    "Batas gratis 10.000 panggilan per hari, 5.000 per jam, 600 per menit."
)

COLUMNS = [
    "timestamp_utc",
    "location",
    "variable",
    "value",
    "unit",
    "latitude",
    "longitude",
    "timezone",
]


def build_params(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    variables: tuple[str, ...] = DEFAULT_VARIABLES,
) -> dict[str, str]:
    return {
        "latitude": str(latitude),
        "longitude": str(longitude),
        "start_date": start,
        "end_date": end,
        "hourly": ",".join(variables),
        "timezone": "UTC",
    }


def fetch(
    client: httpx.Client,
    url: str,
    params: dict[str, str],
) -> dict[str, Any]:
    return get_json(client, url, params)


def to_long_frame(payload: dict[str, Any], location: str) -> pd.DataFrame:
    """Ubah array hourly Open-Meteo menjadi tabel panjang per variabel per jam."""
    hourly = payload.get("hourly") or {}
    units = payload.get("hourly_units") or {}
    times = hourly.get("time") or []
    if not times:
        return pd.DataFrame(columns=COLUMNS)

    timestamps = pd.to_datetime(times, utc=True)
    records: list[tuple[Any, ...]] = []
    for variable, unit in units.items():
        if variable == "time":
            continue
        values = hourly.get(variable) or []
        for timestamp_utc, value in zip(timestamps, values, strict=False):
            records.append((timestamp_utc, location, variable, value, unit))

    frame = pd.DataFrame(
        records,
        columns=["timestamp_utc", "location", "variable", "value", "unit"],
    )
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["latitude"] = payload.get("latitude")
    frame["longitude"] = payload.get("longitude")
    frame["timezone"] = payload.get("timezone")
    frame = frame.sort_values(["timestamp_utc", "variable"], ignore_index=True)
    return frame[COLUMNS]