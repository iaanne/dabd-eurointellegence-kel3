"""Smoke test katalog Iceberg REST di atas Garage S3.

Jalankan dengan:
    uv run --extra iceberg python scripts/iceberg_smoke.py
    uv run --extra iceberg python scripts/iceberg_smoke.py --drop

Skrip ini menulis tabel kecil ke namespace `smoke`, membacanya kembali, lalu
menampilkan jumlah baris. Dengan `--drop`, tabel dan namespace dibersihkan.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pyarrow as pa
from pyiceberg.catalog import load_catalog

ROOT = Path(__file__).resolve().parent.parent


def baca_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            kunci, nilai = line.split("=", 1)
            env[kunci.strip()] = nilai.strip()
    return env


def buat_katalog(env: dict[str, str]):
    return load_catalog(
        "eurogrid",
        type="rest",
        uri=env["ICEBERG_CATALOG_URI"],
        warehouse=env["ICEBERG_WAREHOUSE"],
        **{
            "s3.endpoint": env["GARAGE_S3_ENDPOINT"],
            "s3.access-key-id": env["GARAGE_S3_ACCESS_KEY"],
            "s3.secret-access-key": env["GARAGE_S3_SECRET_KEY"],
            "s3.region": env["GARAGE_S3_REGION"],
            "s3.path-style-access": "true",
        },
    )


def skema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("ts", pa.timestamp("us")),
            pa.field("zone", pa.string()),
            pa.field("price_eur_mwh", pa.float64()),
        ]
    )


def contoh_data() -> pa.Table:
    return pa.table(
        {
            "ts": pa.array(
                [1762732800000000, 1762736400000000, 1762740000000000],
                type=pa.timestamp("us"),
            ),
            "zone": ["DE-LU", "DE-LU", "FR"],
            "price_eur_mwh": [86.4, 91.2, 74.8],
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test Iceberg REST + Garage S3")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="hapus tabel dan namespace smoke setelah pengujian",
    )
    args = parser.parse_args()

    env = baca_env(ROOT / ".env")
    catalog = buat_katalog(env)

    catalog.create_namespace_if_not_exists("smoke")
    if catalog.table_exists("smoke.prices"):
        catalog.drop_table("smoke.prices")

    tabel = catalog.create_table(
        "smoke.prices",
        schema=skema(),
        location=f"{env['ICEBERG_WAREHOUSE'].rstrip('/')}/smoke/prices",
    )
    tabel.append(contoh_data())

    hasil = catalog.load_table("smoke.prices").scan().to_arrow()
    print(f"katalog     : {catalog.name}")
    print(f"tabel       : smoke.prices")
    print(f"lokasi      : {catalog.load_table('smoke.prices').location()}")
    print(f"baris dibaca: {hasil.num_rows}")
    print(f"isi         : {hasil.to_pylist()}")

    if args.drop:
        catalog.drop_table("smoke.prices")
        catalog.drop_namespace("smoke")
        print("tabel dan namespace smoke dihapus")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
