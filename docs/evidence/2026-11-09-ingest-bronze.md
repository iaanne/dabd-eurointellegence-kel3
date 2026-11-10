# Bukti Increment 1: Sumber ke Bronze

Tanggal: 2026-11-09

## Lingkungan

- 12 vCPU, RAM 62 GB, disk bebas 459 GB.
- Python 3.12 melalui `uv`.
- Docker tidak terpasang. Podman 6.1.4 dan `podman-compose` tersedia untuk tahap
  container berikutnya.

## Perintah yang dijalankan

```bash
uv sync --extra dev
make test
make demo
```

`make demo` menjalankan tiga ingest untuk rentang 2026-11-02 sampai 2026-11-08:

```bash
eurogrid ingest-energy-charts --dataset public_power --country de ...
eurogrid ingest-energy-charts --dataset price --bzn DE-LU ...
eurogrid ingest-weather --location berlin --latitude 52.52 --longitude 13.41 ...
```

## Hasil ingest

| Dataset | Batch ID | Baris | Rentang UTC | Nilai kosong |
| --- | --- | --- | --- | --- |
| `public_power` Jerman | `1567602672bcd4ad` | 14.112 | 2026-11-01 23:00 sampai 2026-11-08 22:45 | 0 |
| `price` DE-LU | `5d454ff790b9c456` | 672 | 2026-11-01 23:00 sampai 2026-11-08 22:45 | 0 |
| `weather_hourly` Berlin | `9ed0e344c08a2a42` | 672 | 2026-11-02 00:00 sampai 2026-11-08 23:00 | 0 |

14.112 baris berasal dari 672 interval 15 menit dikali 21 seri pembangkitan.
672 baris harga berasal dari 672 interval. 672 baris cuaca berasal dari 168 jam
dikali 4 variabel.

Contoh nilai yang diperiksa:

- Beban Jerman pada 2026-11-02 00:00 waktu setempat tersimpan sebagai
  2026-11-01 23:00 UTC, sesuai offset `+01:00`.
- Harga DE-LU tersimpan dalam `EUR / MWh` dengan lisensi CC BY 4.0 dari
  Bundesnetzagentur dan SMARD.
- Suhu Berlin berkisar -0,3 sampai 9,4 derajat Celsius pada pekan tersebut.

## Uji idempotensi

Perintah `public_power` dan `ingest-weather` dijalankan ulang dengan parameter
yang sama. Hasilnya:

```json
{"batch_id": "1567602672bcd4ad", "created": false, "row_count": 14112}
{"batch_id": "9ed0e344c08a2a42", "created": false, "row_count": 672}
```

Jumlah batch tidak bertambah. Checksum konten tidak menghitung `generated_at`
dan `generationtime_ms`, dua field yang berubah pada setiap panggilan. Checksum
respons mentah tetap disimpan terpisah di `metadata.json` sebagai
`raw_checksum_sha256`.

## Uji otomatis

```text
15 passed
```

Cakupan: normalisasi waktu ke UTC, bentuk tabel panjang, kunci bisnis, metadata
lisensi, checksum deterministik, idempotensi ingest ulang, deteksi respons yang
berubah, perintah `list` dan `show`, serta integrasi CLI dengan HTTP tiruan.

## Batasan tahap ini

- Penyimpanan masih Parquet lokal, belum MinIO dan belum Iceberg.
- Belum ada jadwal Airflow.
- Belum ada stream producer dan consumer.
- ENTSO-E belum dipakai karena token belum tersedia.
- Belum ada API, dashboard, ML, observability, dan keamanan.

## Lokasi bukti

- Kode: `src/eurogrid/`
- Kontrak data: `docs/data-contract.md`
- Data: `data/bronze/` (tidak masuk Git)
- Metadata tiap batch: `data/bronze/**/metadata.json`