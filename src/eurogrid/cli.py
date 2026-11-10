from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

import httpx

from .config import load_settings
from .ingest import ingest_energy_charts, ingest_weather, resolve_window
from .inspect import (
    find_batches,
    format_batch_table,
    format_frame,
    load_batch_frame,
    newest_batch,
)
from .sources import energy_charts, open_meteo


def _default_dates(days: int = 7) -> tuple[str, str]:
    return resolve_window(days)


def _ingest_energy_charts(args: argparse.Namespace) -> dict[str, Any]:
    return ingest_energy_charts(
        dataset=args.dataset,
        start=args.start,
        end=args.end,
        country=args.country,
        bzn=args.bzn,
    )


def _ingest_weather(args: argparse.Namespace) -> dict[str, Any]:
    variables = tuple(item.strip() for item in args.variables.split(",") if item.strip())
    return ingest_weather(
        start=args.start,
        end=args.end,
        location=args.location,
        country=args.country,
        latitude=args.latitude,
        longitude=args.longitude,
        variables=variables,
    )


def _list_batches(args: argparse.Namespace) -> None:
    settings = load_settings()
    batches = find_batches(settings.data_dir)
    if args.json:
        print(
            json.dumps(
                [batch.to_dict() for batch in batches],
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    print(format_batch_table(batches))


def _show_batch(args: argparse.Namespace) -> int | None:
    settings = load_settings()
    batches = find_batches(settings.data_dir)

    batch = None
    if args.batch_id:
        batch = next((item for item in batches if item.batch_id == args.batch_id), None)
    else:
        batch = newest_batch(batches, args.dataset)

    if batch is None:
        print(
            f"Batch untuk dataset {args.dataset!r} tidak ditemukan. "
            "Jalankan `eurogrid list` untuk melihat yang tersedia.",
            file=sys.stderr,
        )
        return 1

    frame = load_batch_frame(batch)
    series_column = (
        "series_id"
        if "series_id" in frame.columns
        else "variable"
        if "variable" in frame.columns
        else None
    )
    if args.series and series_column:
        frame = frame[frame[series_column] == args.series]
    columns = [
        column
        for column in ("timestamp_utc", series_column, "value", "unit")
        if column is not None and column in frame.columns
    ]
    frame = frame[columns]
    frame = frame.tail(args.limit) if args.tail else frame.head(args.limit)

    if args.json:
        printable = frame.assign(timestamp_utc=frame["timestamp_utc"].astype(str))
        print(
            json.dumps(
                printable.to_dict(orient="records"),
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
        return None

    partition = ",".join(f"{key}={value}" for key, value in batch.partition.items())
    print(
        f"{batch.dataset}  partisi={partition}  batch={batch.batch_id}  "
        f"baris={batch.row_count}"
    )
    print(f"lisensi: {batch.license or '-'}")
    print(format_frame(frame))
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eurogrid",
        description="Ingest data kelistrikan Eropa ke lapisan Bronze.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    start, end = _default_dates()

    ec = sub.add_parser(
        "ingest-energy-charts",
        help="Ambil data dari Energy-Charts API v2.",
    )
    ec.add_argument(
        "--dataset",
        required=True,
        choices=sorted(energy_charts.SUPPORTED_DATASETS),
    )
    ec.add_argument("--country", default="de", help="Kode negara, contoh de.")
    ec.add_argument("--bzn", default="DE-LU", help="Bidding zone untuk dataset price.")
    ec.add_argument("--start", default=start, help="Tanggal awal, format YYYY-MM-DD.")
    ec.add_argument("--end", default=end, help="Tanggal akhir, format YYYY-MM-DD.")
    ec.set_defaults(handler=_ingest_energy_charts)

    om = sub.add_parser(
        "ingest-weather",
        help="Ambil data cuaca historis dari Open-Meteo.",
    )
    om.add_argument("--location", default="berlin")
    om.add_argument("--country", default="de")
    om.add_argument("--latitude", type=float, default=52.52)
    om.add_argument("--longitude", type=float, default=13.41)
    om.add_argument(
        "--variables",
        default=",".join(open_meteo.DEFAULT_VARIABLES),
        help="Daftar variabel dipisah koma.",
    )
    om.add_argument("--start", default=start, help="Tanggal awal, format YYYY-MM-DD.")
    om.add_argument("--end", default=end, help="Tanggal akhir, format YYYY-MM-DD.")
    om.set_defaults(handler=_ingest_weather)

    list_parser = sub.add_parser(
        "list",
        help="Tampilkan semua batch Bronze yang tersimpan.",
    )
    list_parser.add_argument("--json", action="store_true", help="Keluarkan JSON.")
    list_parser.set_defaults(handler=_list_batches)

    show_parser = sub.add_parser(
        "show",
        help="Tampilkan contoh baris dari satu batch Bronze.",
    )
    show_parser.add_argument("--dataset", required=True)
    show_parser.add_argument("--series", help="Filter satu series_id.")
    show_parser.add_argument("--batch-id", help="Pilih batch tertentu.")
    show_parser.add_argument("--limit", type=int, default=12)
    show_parser.add_argument(
        "--tail",
        action="store_true",
        help="Ambil baris terakhir, bukan baris awal.",
    )
    show_parser.add_argument("--json", action="store_true", help="Keluarkan JSON.")
    show_parser.set_defaults(handler=_show_batch)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.handler(args)
    except (httpx.HTTPError, ValueError) as exc:
        print(f"Gagal: {exc}", file=sys.stderr)
        return 1
    if isinstance(result, int):
        return result
    if result is not None:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())