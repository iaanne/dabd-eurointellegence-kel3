# EuroGrid Intelligence

Platform data kelistrikan Eropa untuk tugas besar TBP. Tahap ini fokus pada
Jerman: menarik data pembangkitan, beban, harga, dan cuaca, menyimpannya ke
lapisan Bronze yang dapat direplay, lalu menerbitkannya sebagai tabel Iceberg
di Garage S3.

Kelompok 3: Ian (Platform dan Storage), Nad (Kualitas Data dan Governance),
Jim (Analitik dan Machine Learning), El (Serving, Stream, dan Keamanan).
Rincian peran, RACI, dan milestone ada di [`docs/TEAM.pdf`](docs/TEAM.pdf).

## Status

| Increment | Isi | Bukti |
| --- | --- | --- |
| 1 | Sumber ke Bronze: Energy-Charts dan Open-Meteo, batch idempoten dari checksum | [`docs/evidence/2026-11-09-ingest-bronze.md`](docs/evidence/2026-11-09-ingest-bronze.md) |
| 2 | Garage S3, Web UI, katalog Iceberg REST, smoke test tulis baca | [`docs/evidence/2026-11-10-garage-iceberg.md`](docs/evidence/2026-11-10-garage-iceberg.md) |
| 3 | Deployment Prefect harian, work pool, retry, jadwal 05:00 | [`docs/evidence/2026-11-10-prefect-deployment.md`](docs/evidence/2026-11-10-prefect-deployment.md) |
| 4 | ENTSO-E, katalog Iceberg di Postgres, tabel Bronze di Garage, arsip batch mentah | [`docs/evidence/2026-11-10-entsoe-postgres-iceberg.md`](docs/evidence/2026-11-10-entsoe-postgres-iceberg.md) |

Tabel Bronze yang sudah tersedia di namespace `bronze`:

| Tabel | Isi | Baris saat ini |
| --- | --- | --- |
| `bronze.energy_charts_public_power` | Pembangkitan per jenis di Jerman | 16.128 |
| `bronze.energy_charts_price` | Harga DE-LU | 768 |
| `bronze.open_meteo_weather_hourly` | Cuaca Berlin per jam | 768 |
| `bronze.entsoe_actual_load` | Beban aktual DE-LU dari ENTSO-E | 672 |

Jumlah baris bergerak mengikuti rentang yang di-ingest. Silver belum ada.
Rencana lengkap ada di [`docs/PRD.md`](docs/PRD.md) dan
[`docs/architecture.md`](docs/architecture.md).

## Struktur repositori

```
src/eurogrid/     paket Python: klien sumber, writer Bronze, publikasi Iceberg, CLI
flows/            flow Prefect untuk ingest harian
scripts/          pembuat dokumen dan dek, smoke test Iceberg
infra/garage/     konfigurasi Garage
infra/iceberg/    image Iceberg REST dengan driver JDBC Postgres
infra/prefect/    Dockerfile dan entrypoint worker Prefect
tests/            uji otomatis pytest
docs/             PRD, arsitektur, kontrak data, dan bukti pengujian
compose.yaml      Garage, Postgres, Iceberg REST, Prefect
prefect.yaml      definisi deployment Prefect
Makefile          perintah harian
```

## Prasyarat

- `uv` untuk lingkungan Python.
- Python 3.12, dapat diunduh otomatis oleh `uv`.
- Podman dan `podman-compose` untuk menjalankan container.

## Mulai cepat

```bash
cp .env.example .env      # isi kredensial, lihat bagian Menyiapkan Garage
uv sync --extra dev
make test
make demo
make publish-iceberg
make sync-bronze
```

`make demo` menarik data tujuh hari terakhir untuk empat sumber: `public_power`
Jerman, `price` DE-LU, cuaca Berlin, dan beban aktual DE-LU dari ENTSO-E.

## Stack container

```bash
podman-compose -p eurogrid up -d
```

| Layanan | Alamat | Catatan |
| --- | --- | --- |
| Garage S3 API | http://localhost:3900 | kredensial dari `.env` |
| Garage Admin API | http://localhost:3903 | token di `infra/garage/garage.toml` |
| Garage Web UI | http://127.0.0.1:3909 | hanya localhost |
| Postgres | 127.0.0.1:5432 | backend katalog Iceberg, database `iceberg` |
| Iceberg REST | http://localhost:8181 | katalog `eurogrid`, metadata di Postgres |
| Prefect UI | http://localhost:4200 | server dan worker |

Image `infra/iceberg/Dockerfile` menambahkan driver JDBC Postgres ke image
`apache/iceberg-rest-fixture`. Tanpa driver itu katalog tidak dapat memakai
Postgres. Build pertama membutuhkan akses internet untuk mengunduh driver dari
Maven Central. Metadata katalog sekarang bertahan ketika container dibuat ulang,
karena disimpan di volume `pg-data`.

## Menyiapkan Garage

Bucket `eurogrid-bronze` dan `eurogrid-warehouse` sudah dibuat di cluster lokal.
Bucket pertama menyimpan arsip batch mentah. Bucket kedua menyimpan tabel Iceberg.
Kredensial akses dibuat sekali, lalu disimpan di `.env` sebagai
`GARAGE_S3_ACCESS_KEY` dan `GARAGE_S3_SECRET_KEY`. Cara paling mudah lewat Web UI
di http://127.0.0.1:3909 pada menu Keys, atau lewat CLI:

```bash
podman exec eurogrid-garage /garage status
podman exec eurogrid-garage /garage bucket create eurogrid-bronze
podman exec eurogrid-garage /garage key create eurogrid-app
podman exec eurogrid-garage /garage bucket allow --read --write --owner eurogrid-bronze --key eurogrid-app
```

`admin_token` dan `metrics_token` di `infra/garage/garage.toml` perlu diisi nilai
acak sendiri sebelum cluster dipakai bersama.

## Prefect

Deployment harian bernama `bronze-daily/production`:

- Flow: `flows/bronze_daily.py` dengan empat task ingest, yaitu `public_power`, `price`, `weather`, dan `entsoe_load`.
- Setelah ingest, task `publish-bronze-iceberg` menulis ulang tabel Bronze di Garage.
- Task `sync-bronze-garage` menyalin batch mentah ke bucket `eurogrid-bronze`.
- Work pool: `eurogrid-pool` tipe process.
- Jadwal: cron `0 5 * * *` zona `Europe/Berlin`.
- Parameter bawaan: `days=7`, yaitu tujuh hari bergulir yang berakhir kemarin.

```bash
make prefect-up       # nyalakan server dan worker
make prefect-run      # jalankan satu run sekarang
make prefect-logs     # ikuti log worker
make prefect-deploy   # daftarkan ulang deployment dari prefect.yaml
```

Hasil run terlihat di http://localhost:4200. Menjalankan rentang yang sama dua
kali tidak membuat batch baru, karena nama batch ditentukan checksum isi respons.

Catatan tahap ini: server Prefect menyimpan metadata di SQLite pada volume
`prefect-data`. Worker berjalan sebagai root di dalam container rootless, jadi
berkas di `data/` tetap dimiliki user host.

## Iceberg

Katalog Iceberg REST memakai `org.apache.iceberg.jdbc.JdbcCatalog` dengan
metadata di Postgres dan berkas data di Garage. Smoke test menulis satu tabel
kecil lalu membacanya kembali:

```bash
uv run --extra iceberg python scripts/iceberg_smoke.py
uv run --extra iceberg python scripts/iceberg_smoke.py --drop
```

Batch Bronze lokal diterbitkan sebagai tabel Iceberg dengan perintah:

```bash
make publish-iceberg
uv run --extra iceberg eurogrid publish-iceberg --table entsoe_actual_load
```

Perintah ini menggabungkan semua batch lokal untuk satu dataset, membuang
duplikat berdasarkan `series_id` dan `timestamp_utc`, lalu menulis ulang tabel
secara penuh. Hasilnya sama untuk masukan yang sama, jadi aman dijalankan
berulang.

## Ingest Bronze dari CLI

```bash
uv run eurogrid ingest-energy-charts \
  --dataset public_power --country de \
  --start 2026-11-02 --end 2026-11-08

uv run eurogrid ingest-energy-charts \
  --dataset price --bzn DE-LU \
  --start 2026-11-02 --end 2026-11-08

uv run eurogrid ingest-weather \
  --location berlin --latitude 52.52 --longitude 13.41 \
  --start 2026-11-02 --end 2026-11-08

uv run eurogrid ingest-entsoe \
  --dataset actual_load --bzn 10Y1001A1001A82H \
  --start 2026-11-02 --end 2026-11-08
```

Keluaran perintah berupa JSON berisi `batch_id`, `path`, `created`, `row_count`,
dan `checksum_sha256`. Token ENTSO-E tidak pernah ditulis ke metadata batch,
nilainya diganti `***`.

## Layout Bronze

Batch mentah di mesin lokal dan salinannya di Garage:

```
data/bronze/<source>/<dataset>/<partition>/batch_id=<checksum>/
  raw.json        respons asli, diserialisasi deterministik
  data.parquet    tabel panjang: timestamp_utc, series_id, value, unit, dan metadata
  metadata.json   batch_id, checksum, parameter request, lisensi, jumlah baris

s3://eurogrid-bronze/bronze/<source>/<dataset>/<partition>/batch_id=<checksum>/
```

Tabel Iceberg di Garage:

```
s3://eurogrid-warehouse/bronze/<source>_<dataset>/
  data/
  metadata/
```

Metadata sumber seperti `timezone`, `resolution`, `license`, `available_from`,
dan `available_until` disimpan bersama data untuk provenance dan lineage.

## Cara mengecek hasil

```bash
make list                                          # semua batch tersimpan
uv run eurogrid list --json
uv run eurogrid show --dataset price --limit 8
uv run eurogrid show --dataset weather_hourly --series temperature_2m --limit 8
uv run eurogrid show --dataset actual_load --limit 8
cat data/bronze/energy_charts/public_power/country=de/batch_id=*/metadata.json
```

Membaca tabel Iceberg lewat PyIceberg:

```bash
uv run --extra iceberg python - <<'PY'
from eurogrid.config import load_settings
from eurogrid.bronze.warehouse import build_catalog

catalog = build_catalog(load_settings())
print(catalog.list_tables("bronze"))
print(catalog.load_table("bronze.entsoe_actual_load").scan().to_arrow().num_rows)
PY
```

Uji otomatis dijalankan dengan `make test`. Dokumen PDF dibangun ulang dengan
`make docs`.

## Sumber dan lisensi

| Sumber | Data | Lisensi | Catatan |
| --- | --- | --- | --- |
| Energy-Charts API v2 | Pembangkitan, harga, aliran lintas negara | CC BY 4.0 untuk data yang dipakai, atribusi energy-charts.info | Lisensi harga berbeda per zona. DE-LU memakai CC BY 4.0 dari Bundesnetzagentur dan SMARD. |
| Open-Meteo Historical Weather | Suhu, angin, radiasi, presipitasi | CC BY 4.0, non-komersial, atribusi Open-Meteo.com | Batas gratis 10.000 panggilan per hari, 5.000 per jam, 600 per menit. |
| ENTSO-E Transparency Platform | Beban aktual per bidding zone | Atribusi ENTSO-E, tunduk pada syarat penggunaan platform | Token aktif. Dataset yang dipakai `actual_load`, documentType A65, processType A16. |

Rincian kontrak data ada di [`docs/data-contract.md`](docs/data-contract.md).

## Dokumen

| Dokumen | Isi |
| --- | --- |
| [`docs/PRD.md`](docs/PRD.md) | Product requirements, kebutuhan F-01 sampai F-18, roadmap |
| [`docs/PRD.pdf`](docs/PRD.pdf) | Versi PDF dari PRD |
| [`docs/TEAM.pdf`](docs/TEAM.pdf) | Pembagian peran Ian, Nad, Jim, El, RACI, milestone |
| [`docs/architecture.md`](docs/architecture.md) | Arsitektur target, ADR-01 sampai ADR-05, batas resource |
| [`docs/data-contract.md`](docs/data-contract.md) | Kontrak data dan envelope stream |
| [`docs/evidence/`](docs/evidence/) | Bukti pengujian dan hasil ingest |

## Langkah berikutnya

1. Silver: normalisasi, quality gate, dan tabel karantina.
2. Gold: tiga mart, sepuluh query, lalu Trino sebagai lapisan serving.
3. Stream producer dan consumer Redpanda dengan dedup dan DLQ.
4. Model prakiraan beban, MLflow, API, dan dashboard.
5. Observability, alert, keamanan, dan backup.