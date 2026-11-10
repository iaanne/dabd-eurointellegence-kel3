# EuroGrid Intelligence

Platform data kelistrikan Eropa untuk tugas besar TBP. Tahap ini fokus pada
Jerman: menarik data pembangkitan, beban, harga, dan cuaca, menyimpannya ke
lapisan Bronze yang dapat direplay, lalu menjadwalkan ingest harian.

Kelompok 3: Ian (Platform dan Storage), Nad (Kualitas Data dan Governance),
Jim (Analitik dan Machine Learning), El (Serving, Stream, dan Keamanan).
Rincian peran, RACI, dan milestone ada di [`docs/TEAM.pdf`](docs/TEAM.pdf).

## Status

| Increment | Isi | Bukti |
| --- | --- | --- |
| 1 | Sumber ke Bronze: Energy-Charts dan Open-Meteo, batch idempoten dari checksum | [`docs/evidence/2026-11-09-ingest-bronze.md`](docs/evidence/2026-11-09-ingest-bronze.md) |
| 2 | Garage S3, Web UI, katalog Iceberg REST, smoke test tulis baca | [`docs/evidence/2026-11-10-garage-iceberg.md`](docs/evidence/2026-11-10-garage-iceberg.md) |
| 3 | Deployment Prefect harian, work pool, retry, jadwal 05:00 | [`docs/evidence/2026-11-10-prefect-deployment.md`](docs/evidence/2026-11-10-prefect-deployment.md) |

Belum dikerjakan: Silver, Gold, Redpanda, Trino, ML, API, dashboard, dan
observability. Rencana lengkap ada di [`docs/PRD.md`](docs/PRD.md) dan
[`docs/architecture.md`](docs/architecture.md).

## Struktur repositori

```
src/eurogrid/     paket Python: klien sumber, writer Bronze, inspeksi, CLI
flows/            flow Prefect untuk ingest harian
scripts/          pembuat dokumen dan dek, smoke test Iceberg
infra/garage/     konfigurasi Garage
infra/prefect/    Dockerfile dan entrypoint worker Prefect
tests/            uji otomatis pytest
docs/             PRD, arsitektur, kontrak data, dan bukti pengujian
compose.yaml      Garage, Garage Web UI, Iceberg REST, Prefect
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
```

`make demo` menarik data tujuh hari terakhir untuk tiga sumber: `public_power`
Jerman, `price` DE-LU, dan cuaca Berlin.

## Stack container

```bash
podman-compose -p eurogrid up -d
```

| Layanan | Alamat | Catatan |
| --- | --- | --- |
| Garage S3 API | http://localhost:3900 | kredensial dari `.env` |
| Garage Admin API | http://localhost:3903 | token di `infra/garage/garage.toml` |
| Garage Web UI | http://127.0.0.1:3909 | hanya localhost |
| Iceberg REST | http://localhost:8181 | katalog `eurogrid` |
| Prefect UI | http://localhost:4200 | server dan worker |

## Menyiapkan Garage

Bucket `eurogrid-bronze` dan `eurogrid-warehouse` sudah dibuat di cluster lokal.
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

- Flow: `flows/bronze_daily.py` dengan tiga task, yaitu `public_power`, `price`, dan `weather`.
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

Katalog Iceberg REST berjalan di atas Garage. Smoke test menulis satu tabel kecil
lalu membacanya kembali:

```bash
uv run --extra iceberg python scripts/iceberg_smoke.py
uv run --extra iceberg python scripts/iceberg_smoke.py --drop
```

Catatan tahap ini: katalog memakai SQLite di dalam container, jadi metadata
katalog hilang bila container dibuat ulang. Berkas di S3 tidak ikut hilang.

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
```

Keluaran perintah berupa JSON berisi `batch_id`, `path`, `created`, `row_count`,
dan `checksum_sha256`.

## Layout Bronze

```
data/bronze/<source>/<dataset>/<partition>/batch_id=<checksum>/
  raw.json        respons asli, diserialisasi deterministik
  data.parquet    tabel panjang: timestamp_utc, series_id, value, unit, dan metadata
  metadata.json   batch_id, checksum, parameter request, lisensi, jumlah baris
```

Metadata sumber seperti `timezone`, `resolution`, `license`, `available_from`,
dan `available_until` disimpan bersama data untuk provenance dan lineage.

## Cara mengecek hasil

```bash
make list                                          # semua batch tersimpan
uv run eurogrid list --json
uv run eurogrid show --dataset price --limit 8
uv run eurogrid show --dataset weather_hourly --series temperature_2m --limit 8
cat data/bronze/energy_charts/public_power/country=de/batch_id=*/metadata.json
```

Uji otomatis dijalankan dengan `make test`. Dokumen PDF dibangun ulang dengan
`make docs`.

## Sumber dan lisensi

| Sumber | Data | Lisensi | Catatan |
| --- | --- | --- | --- |
| Energy-Charts API v2 | Pembangkitan, beban, harga, aliran lintas negara | CC BY 4.0 untuk data yang dipakai, atribusi energy-charts.info | Lisensi harga berbeda per zona. DE-LU memakai CC BY 4.0 dari Bundesnetzagentur dan SMARD. |
| Open-Meteo Historical Weather | Suhu, angin, radiasi, presipitasi | CC BY 4.0, non-komersial, atribusi Open-Meteo.com | Batas gratis 10.000 panggilan per hari, 5.000 per jam, 600 per menit. |
| ENTSO-E Transparency Platform | Beban dan aliran otoritatif lintas negara | Menunggu akses token | Belum dipakai karena token belum aktif. |

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
6. Pindahkan Bronze ke Garage dan ganti katalog Iceberg ke PostgreSQL.
