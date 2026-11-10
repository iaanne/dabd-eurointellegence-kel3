"""Adapter sumber ENTSO-E Transparency Platform.

Hanya dokumen beban aktual (``documentType=A65``, ``processType=A16``) yang
dipakai pada tahap ini. Dokumen berisi satu atau beberapa ``TimeSeries``, tiap
seri punya ``Period`` dengan ``resolution`` dan daftar ``Point`` berisi
``position`` serta ``quantity``.

Nilai yang berubah pada setiap panggilan, seperti ``mRID`` dokumen,
``revisionNumber``, dan ``createdDateTime``, tidak dimasukkan ke envelope yang
dihitung checksum-nya. Nilai itu tetap dicatat di metadata batch supaya
provenance tidak hilang tanpa merusak idempotensi.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
import pandas as pd

from ..http import get_text

DATASETS: dict[str, dict[str, str]] = {
    "actual_load": {
        "document_type": "A65",
        "process_type": "A16",
        "unit": "MAW",
        "description": "Beban listrik aktual per bidding zone",
    },
}

LICENSE = (
    "ENTSO-E Transparency Platform. Data dipakai ulang dengan atribusi ENTSO-E "
    "dan tunduk pada syarat penggunaan platform."
)

COLUMNS = [
    "timestamp_utc",
    "dataset",
    "series_id",
    "series_name",
    "value",
    "unit",
    "resolution",
    "bidding_zone",
    "country",
    "document_type",
    "process_type",
    "license",
]

# Pemetaan kode resolusi IEC 62325 ke durasi.
_RESOLUTIONS = {
    "PT1M": pd.Timedelta(minutes=1),
    "PT15M": pd.Timedelta(minutes=15),
    "PT30M": pd.Timedelta(minutes=30),
    "PT60M": pd.Timedelta(hours=1),
    "PT1H": pd.Timedelta(hours=1),
    "P1D": pd.Timedelta(days=1),
}


def build_params(
    *,
    security_token: str,
    dataset: str,
    bidding_zone: str,
    start: str,
    end: str,
) -> dict[str, str]:
    """Susun parameter permintaan untuk satu rentang tanggal inklusif.

    ``end`` adalah tanggal terakhir yang diinginkan, jadi ``periodEnd`` memakai
    awal hari berikutnya. ENTSO-E memakai format ``YYYYMMDDHHMM`` dalam UTC.
    """
    spec = DATASETS.get(dataset)
    if spec is None:
        raise ValueError(f"Dataset ENTSO-E tidak didukung: {dataset}")
    if not security_token:
        raise ValueError("ENTSOE_API_TOKEN belum diisi.")
    return {
        "securityToken": security_token,
        "documentType": spec["document_type"],
        "processType": spec["process_type"],
        "outBiddingZone_Domain": bidding_zone,
        "periodStart": _period_stamp(start, days=0),
        "periodEnd": _period_stamp(end, days=1),
    }


def _period_stamp(value: str, *, days: int) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Tanggal tidak valid: {value!r}, pakai YYYY-MM-DD.") from exc
    moment = datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)
    return (moment + timedelta(days=days)).strftime("%Y%m%d%H%M")


def fetch(
    client: httpx.Client,
    url: str,
    params: dict[str, str],
) -> str:
    return get_text(client, url, params)


def fetch_document(
    client: httpx.Client,
    url: str,
    *,
    security_token: str,
    dataset: str,
    bidding_zone: str,
    start: str,
    end: str,
) -> tuple[str, dict[str, str]]:
    """Ambil XML dan kembalikan parameter yang sudah disunting tokennya."""
    params = build_params(
        security_token=security_token,
        dataset=dataset,
        bidding_zone=bidding_zone,
        start=start,
        end=end,
    )
    xml_text = fetch(client, url, params)
    redacted = dict(params)
    redacted["securityToken"] = "***"
    return xml_text, redacted


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ElementTree.Element | None, name: str) -> str | None:
    if element is None:
        return None
    child = element.find(f"{{*}}{name}")
    if child is None or child.text is None:
        return None
    return child.text.strip()


def parse_document(xml_text: str) -> dict[str, Any]:
    """Ubah XML ENTSO-E menjadi envelope deterministik untuk checksum."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Respons ENTSO-E bukan XML yang valid: {exc}") from exc

    if _local_name(root.tag) not in {"GL_MarketDocument", "Publication_MarketDocument"}:
        raise ValueError(f"Jenis dokumen ENTSO-E tidak dikenal: {_local_name(root.tag)}")

    document_type = _child_text(root, "type")
    process_type = _child_text(root, "process.processType")

    series: list[dict[str, Any]] = []
    resolutions: list[str] = []
    units: list[str] = []
    bidding_zones: list[str] = []

    for time_series in root.findall("{*}TimeSeries"):
        unit = _child_text(time_series, "quantity_Measure_Unit.name") or _child_text(
            time_series, "price_Measure_Unit.name"
        )
        zone = _child_text(time_series, "outBiddingZone_Domain.mRID") or _child_text(
            time_series, "in_Domain.mRID"
        )
        periods: list[dict[str, Any]] = []
        for period in time_series.findall("{*}Period"):
            interval = period.find("{*}timeInterval")
            start = _child_text(interval, "start")
            end = _child_text(interval, "end")
            resolution = _child_text(period, "resolution")
            if resolution is not None:
                resolutions.append(resolution)
            points: list[list[float]] = []
            for point in period.findall("{*}Point"):
                position = _child_text(point, "position")
                quantity = _child_text(point, "quantity") or _child_text(
                    point, "price.amount"
                )
                if position is None or quantity is None:
                    continue
                points.append([int(position), float(quantity)])
            periods.append(
                {
                    "start": start,
                    "end": end,
                    "resolution": resolution,
                    "points": points,
                }
            )
        if unit is not None:
            units.append(unit)
        if zone is not None:
            bidding_zones.append(zone)
        series.append(
            {
                "series_id": _child_text(time_series, "mRID") or str(len(series) + 1),
                "business_type": _child_text(time_series, "businessType"),
                "unit": unit,
                "bidding_zone": zone,
                "periods": periods,
            }
        )

    if not series:
        raise ValueError("Dokumen ENTSO-E tidak memuat TimeSeries.")

    return {
        "endpoint": "entsoe",
        "document_type": document_type,
        "process_type": process_type,
        "resolution": resolutions[0] if resolutions else None,
        "unit": units[0] if units else None,
        "bidding_zone": bidding_zones[0] if bidding_zones else None,
        "timezone": "UTC",
        "series": series,
        "license": LICENSE,
    }


def to_long_frame(
    envelope: dict[str, Any],
    *,
    dataset: str,
    country: str = "de",
) -> pd.DataFrame:
    """Ubah envelope hasil parse menjadi tabel panjang per titik waktu."""
    records: list[tuple[Any, ...]] = []
    for item in envelope.get("series") or []:
        series_id = item.get("series_id")
        unit = item.get("unit") or envelope.get("unit")
        zone = item.get("bidding_zone") or envelope.get("bidding_zone")
        for period in item.get("periods") or []:
            start = period.get("start")
            resolution = period.get("resolution")
            step = _RESOLUTIONS.get(str(resolution))
            if start is None or step is None:
                continue
            start_at = pd.Timestamp(start)
            if start_at.tzinfo is None:
                start_at = start_at.tz_localize("UTC")
            else:
                start_at = start_at.tz_convert("UTC")
            for position, value in period.get("points") or []:
                timestamp = start_at + step * (int(position) - 1)
                records.append(
                    (
                        timestamp,
                        dataset,
                        series_id,
                        dataset,
                        value,
                        unit,
                        resolution,
                        zone,
                        country,
                        envelope.get("document_type"),
                        envelope.get("process_type"),
                        envelope.get("license"),
                    )
                )

    frame = pd.DataFrame(records, columns=COLUMNS)
    if frame.empty:
        return frame
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.drop_duplicates(
        subset=["dataset", "series_id", "timestamp_utc"], keep="last"
    )
    return frame.sort_values(["timestamp_utc", "series_id"], ignore_index=True)