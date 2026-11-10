from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Sequence

from .bronze.writer import WriteResult, write_bronze_batch
from .config import Settings, load_settings
from .http import build_client
from .sources import energy_charts, entsoe, open_meteo

SOURCE_ENERGY_CHARTS = "energy_charts"
SOURCE_OPEN_METEO = "open_meteo"
SOURCE_ENTSOE = "entsoe"


def result_payload(result: WriteResult) -> dict[str, Any]:
    """Ringkasan satu batch untuk ditampilkan di CLI, log flow, atau JSON."""
    return {
        "batch_id": result.batch_id,
        "path": str(result.path),
        "created": result.created,
        "row_count": result.row_count,
        "checksum_sha256": result.checksum_sha256,
    }


def resolve_window(days: int, today: date | None = None) -> tuple[str, str]:
    """Rentang tanggal bergulir yang berakhir kemarin.

    Data sumber biasanya belum lengkap untuk hari berjalan, jadi tanggal akhir
    selalu kemarin. `days` menghitung mundur dari titik itu.
    """
    if days < 1:
        raise ValueError("days minimal 1.")
    end = (today or date.today()) - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def ingest_energy_charts(
    *,
    dataset: str,
    start: str,
    end: str,
    country: str = "de",
    bzn: str = "DE-LU",
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Ambil satu dataset Energy-Charts lalu tulis batch Bronze."""
    settings = settings or load_settings()
    params = energy_charts.build_params(
        dataset=dataset,
        start=start,
        end=end,
        country=country,
        bzn=bzn,
    )
    url = f"{settings.energy_charts_base_url}/v2/{dataset}"

    with build_client(settings) as client:
        envelope = energy_charts.fetch(
            client,
            settings.energy_charts_base_url,
            dataset,
            params,
        )

    frame = energy_charts.to_long_frame(envelope)

    if dataset == "price":
        partition_values = {"bzn": bzn}
    else:
        partition_values = {"country": country}

    result = write_bronze_batch(
        settings.data_dir,
        source=SOURCE_ENERGY_CHARTS,
        dataset=dataset,
        partition_values=partition_values,
        raw=envelope,
        frame=frame,
        request_url=url,
        request_params=params,
        license=envelope.get("license"),
        extra_metadata={
            "country": envelope.get("country"),
            "bidding_zone": envelope.get("bidding_zone"),
            "available_from": envelope.get("available_from"),
            "available_until": envelope.get("available_until"),
        },
    )
    payload = result_payload(result)
    payload["dataset"] = dataset
    payload["partition"] = partition_values
    payload["series_count"] = len(envelope.get("series") or [])
    return payload


def ingest_weather(
    *,
    start: str,
    end: str,
    location: str = "berlin",
    country: str = "de",
    latitude: float = 52.52,
    longitude: float = 13.41,
    variables: Sequence[str] | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Ambil cuaca historis Open-Meteo lalu tulis batch Bronze."""
    settings = settings or load_settings()
    chosen = tuple(variables) if variables else open_meteo.DEFAULT_VARIABLES
    params = open_meteo.build_params(
        latitude=latitude,
        longitude=longitude,
        start=start,
        end=end,
        variables=chosen,
    )

    with build_client(settings) as client:
        payload = open_meteo.fetch(client, settings.open_meteo_archive_url, params)

    frame = open_meteo.to_long_frame(payload, location=location)
    partition_values = {"country": country, "location": location}

    result = write_bronze_batch(
        settings.data_dir,
        source=SOURCE_OPEN_METEO,
        dataset="weather_hourly",
        partition_values=partition_values,
        raw=payload,
        frame=frame,
        request_url=settings.open_meteo_archive_url,
        request_params=params,
        license=open_meteo.LICENSE,
        extra_metadata={
            "location": location,
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "timezone": payload.get("timezone"),
            "variables": list(chosen),
        },
    )
    result_payload_ = result_payload(result)
    result_payload_["dataset"] = "weather_hourly"
    result_payload_["partition"] = partition_values
    result_payload_["variables"] = list(chosen)
    return result_payload_


def ingest_entsoe(
    *,
    dataset: str = "actual_load",
    start: str,
    end: str,
    bidding_zone: str = "10Y1001A1001A82H",
    country: str = "de",
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Ambil beban aktual dari ENTSO-E lalu tulis batch Bronze.

    Token tidak ikut tersimpan di metadata batch. Parameter permintaan disalin
    dengan nilai ``securityToken`` diganti ``***``.
    """
    settings = settings or load_settings()
    if not settings.entsoe_api_token:
        raise ValueError(
            "ENTSOE_API_TOKEN belum diisi. Tambahkan token ke .env lebih dulu."
        )

    with build_client(settings) as client:
        xml_text, request_params = entsoe.fetch_document(
            client,
            settings.entsoe_api_url,
            security_token=settings.entsoe_api_token,
            dataset=dataset,
            bidding_zone=bidding_zone,
            start=start,
            end=end,
        )

    envelope = entsoe.parse_document(xml_text)
    frame = entsoe.to_long_frame(envelope, dataset=dataset, country=country)
    partition_values = {"country": country, "bzn": bidding_zone}

    result = write_bronze_batch(
        settings.data_dir,
        source=SOURCE_ENTSOE,
        dataset=dataset,
        partition_values=partition_values,
        raw=envelope,
        frame=frame,
        request_url=settings.entsoe_api_url,
        request_params=request_params,
        license=envelope.get("license"),
        extra_metadata={
            "country": country,
            "bidding_zone": bidding_zone,
            "document_type": envelope.get("document_type"),
            "process_type": envelope.get("process_type"),
            "series_count": len(envelope.get("series") or []),
            "xml_bytes": len(xml_text.encode("utf-8")),
        },
    )
    payload = result_payload(result)
    payload["dataset"] = dataset
    payload["partition"] = partition_values
    payload["series_count"] = len(envelope.get("series") or [])
    return payload
