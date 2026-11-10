"""Flow harian yang mengisi lapisan Bronze.

Dijalankan oleh worker Prefect dari deployment `bronze-daily/production`.
Rentang tanggal bawaan bergulir tujuh hari dan berakhir kemarin, sehingga data
yang terlambat tetap tertangkap dan ingest ulang tidak membuat batch ganda.
"""

from __future__ import annotations

from typing import Any

from prefect import flow, task

from eurogrid.ingest import (
    ingest_energy_charts,
    ingest_entsoe,
    ingest_weather,
    resolve_window,
)

RETRY_DELAYS = [30, 60, 180]
TASK_TIMEOUT_SECONDS = 600


@task(
    name="ingest-public-power",
    retries=3,
    retry_delay_seconds=RETRY_DELAYS,
    timeout_seconds=TASK_TIMEOUT_SECONDS,
    log_prints=True,
)
def ingest_public_power(start: str, end: str, country: str) -> dict[str, Any]:
    return ingest_energy_charts(
        dataset="public_power",
        start=start,
        end=end,
        country=country,
    )


@task(
    name="ingest-price",
    retries=3,
    retry_delay_seconds=RETRY_DELAYS,
    timeout_seconds=TASK_TIMEOUT_SECONDS,
    log_prints=True,
)
def ingest_price(start: str, end: str, bzn: str) -> dict[str, Any]:
    return ingest_energy_charts(
        dataset="price",
        start=start,
        end=end,
        bzn=bzn,
    )


@task(
    name="ingest-weather",
    retries=3,
    retry_delay_seconds=RETRY_DELAYS,
    timeout_seconds=TASK_TIMEOUT_SECONDS,
    log_prints=True,
)
def ingest_weather_task(
    start: str,
    end: str,
    location: str,
    country: str,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    return ingest_weather(
        start=start,
        end=end,
        location=location,
        country=country,
        latitude=latitude,
        longitude=longitude,
    )


@task(
    name="ingest-entsoe-load",
    retries=3,
    retry_delay_seconds=RETRY_DELAYS,
    timeout_seconds=TASK_TIMEOUT_SECONDS,
    log_prints=True,
)
def ingest_entsoe_load(start: str, end: str, bidding_zone: str) -> dict[str, Any]:
    return ingest_entsoe(
        dataset="actual_load",
        start=start,
        end=end,
        bidding_zone=bidding_zone,
    )


@task(
    name="publish-bronze-iceberg",
    retries=2,
    retry_delay_seconds=[30, 120],
    timeout_seconds=1200,
    log_prints=True,
)
def publish_bronze_task() -> list[dict[str, Any]]:
    from eurogrid.bronze.warehouse import publish_bronze

    results = publish_bronze()
    for item in results:
        print(f"Tabel {item.table}: {item.rows} baris")
    return [item.to_dict() for item in results]


@task(
    name="sync-bronze-garage",
    retries=2,
    retry_delay_seconds=[30, 120],
    timeout_seconds=600,
    log_prints=True,
)
def sync_bronze_task() -> dict[str, Any]:
    from eurogrid.bronze.warehouse import upload_bronze

    result = upload_bronze()
    print(f"Arsip Bronze: {result['files']} berkas, {result['bytes']} byte")
    return result


@flow(name="bronze-daily", log_prints=True)
def bronze_daily(
    days: int = 7,
    start: str | None = None,
    end: str | None = None,
    country: str = "de",
    bzn: str = "DE-LU",
    entsoe_bzn: str = "10Y1001A1001A82H",
    location: str = "berlin",
    latitude: float = 52.52,
    longitude: float = 13.41,
) -> dict[str, Any]:
    """Isi Bronze untuk public_power, price, cuaca, dan beban ENTSO-E."""
    if start and end:
        window_start, window_end = start, end
    else:
        window_start, window_end = resolve_window(days)

    print(f"Rentang ingest: {window_start} sampai {window_end}")

    results = {
        "public_power": ingest_public_power(window_start, window_end, country),
        "price": ingest_price(window_start, window_end, bzn),
        "weather": ingest_weather_task(
            window_start,
            window_end,
            location,
            country,
            latitude,
            longitude,
        ),
        "entsoe_load": ingest_entsoe_load(window_start, window_end, entsoe_bzn),
    }

    total_rows = sum(item["row_count"] for item in results.values())
    created = sum(1 for item in results.values() if item["created"])
    print(f"Selesai: {created} batch baru, {total_rows} baris")

    published = publish_bronze_task()
    archived = sync_bronze_task()

    return {
        "window": {"start": window_start, "end": window_end},
        "batches": results,
        "total_rows": total_rows,
        "new_batches": created,
        "published_tables": published,
        "bronze_archive": archived,
    }


if __name__ == "__main__":
    bronze_daily()
