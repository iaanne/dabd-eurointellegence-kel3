"""Flow harian yang mengisi lapisan Bronze.

Dijalankan oleh worker Prefect dari deployment `bronze-daily/production`.
Rentang tanggal bawaan bergulir tujuh hari dan berakhir kemarin, sehingga data
yang terlambat tetap tertangkap dan ingest ulang tidak membuat batch ganda.
"""

from __future__ import annotations

from typing import Any

from prefect import flow, task

from eurogrid.ingest import ingest_energy_charts, ingest_weather, resolve_window

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


@flow(name="bronze-daily", log_prints=True)
def bronze_daily(
    days: int = 7,
    start: str | None = None,
    end: str | None = None,
    country: str = "de",
    bzn: str = "DE-LU",
    location: str = "berlin",
    latitude: float = 52.52,
    longitude: float = 13.41,
) -> dict[str, Any]:
    """Isi Bronze untuk public_power, price, dan cuaca satu lokasi."""
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
    }

    total_rows = sum(item["row_count"] for item in results.values())
    created = sum(1 for item in results.values() if item["created"])
    print(f"Selesai: {created} batch baru, {total_rows} baris")

    return {
        "window": {"start": window_start, "end": window_end},
        "batches": results,
        "total_rows": total_rows,
        "new_batches": created,
    }


if __name__ == "__main__":
    bronze_daily()
