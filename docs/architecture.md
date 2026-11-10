# Arsitektur Teknis: EuroGrid Intelligence

Dokumen ini menjelaskan arsitektur target, keputusan teknis, dan batas resource. Isinya melengkapi `docs/PRD.md` dan menjadi rujukan implementasi.

| Atribut | Isi |
| --- | --- |
| Versi | 1.0 |
| Tanggal | 10 November 2026 |
| Status | Target arsitektur, sebagian belum diimplementasikan |
| Stack utama | Garage S3, Apache Iceberg, Prefect 3, Redpanda, Trino |
| Deployment | Podman dan podman-compose |

## 1. Prinsip

1. Satu jalur data yang benar lebih berguna daripada banyak komponen yang belum tersambung.
2. Data mentah tidak boleh hilang. Semua transformasi harus dapat diulang dari Bronze.
3. Setiap komponen harus punya health check, batas memori, dan cara pemulihan.
4. Rahasia tidak masuk repositori. Konfigurasi dibaca dari `.env`.
5. Komponen dipilih karena dapat dijalankan di satu mesin, bukan karena populer.

## 2. Topologi service

| Service | Image atau paket | Port | Volume | Memori maksimal |
| --- | --- | --- | --- | --- |
| Garage S3 | `dxflrs/garage` | 3900, 3903 | `garage-data`, `garage-meta` | 2 GB |
| Postgres | `postgres:16` | 5432 | `pg-data` | 2 GB |
| Iceberg REST | `tabulario/iceberg-rest` | 8181 | tidak ada, metadata di Postgres | 1 GB |
| Prefect server | `prefecthq/prefect:3` | 4200 | `prefect-data` | 2 GB |
| Prefect worker | `prefecthq/prefect:3` | tidak ada | tidak ada | 2 GB |
| Redpanda | `redpandadata/redpanda` | 9092, 8080 | `redpanda-data` | 4 GB |
| Trino | `trinodb/trino` | 8081 | `trino-data` | 4 GB |
| MLflow | `ghcr.io/mlflow/mlflow` | 5000 | `mlflow-data` | 1 GB |
| FastAPI | image proyek | 8000 | tidak ada | 1 GB |
| Metabase | `metabase/metabase` | 3000 | `metabase-data` | 2 GB |
| Prometheus | `prom/prometheus` | 9090 | `prom-data` | 1 GB |
| Grafana | `grafana/grafana` | 3001 | `grafana-data` | 512 MB |
| Marquez | `marquezproject/marquez` | 5001, 3002 | `marquez-data` | 1 GB |

Jumlah memori maksimal sekitar 23,5 GB. Angka ini adalah anggaran, bukan hasil pengukuran. Batas akan disesuaikan setelah benchmark.

## 3. Alur batch

```
Prefect flow
  |-- extract: Energy-Charts, Open-Meteo, ENTSO-E
  |-- write Bronze: Garage S3, checksum, metadata
  |-- validate Silver: normalisasi, quality gate, karantina
  |-- build Gold: fact, agregat, fitur
  |-- register lineage: OpenLineage ke Marquez
  `-- publish metrics: Prometheus pushgateway atau exporter
```

Setiap langkah adalah Prefect task dengan retry, timeout, dan log terstruktur. Flow utama dijalankan harian. Backfill menerima parameter `start_date` dan `end_date`, lalu memproses per hari agar kegagalan satu hari tidak membatalkan seluruh rentang.

## 4. Alur stream

```
Energy-Charts poller
  -> Redpanda topic `eurogrid.events` (partisi per zona)
  -> Consumer Python
       |-- dedup event_id
       |-- watermark 15 menit
       |-- tulis Bronze stream
       `-- DLQ `eurogrid.events.dlq`
```

Semantik pengiriman at-least-once. Duplikat mungkin terjadi dan diselesaikan di consumer. Offset disimpan setelah batch ditulis, sehingga restart dapat mengulang batch terakhir tanpa kehilangan data.

## 5. Tata letak object storage

```
s3://eurogrid-bronze/
  energy_charts/public_power/country=de/ingest_date=2026-11-09/batch_id=<checksum>/
  energy_charts/price/bzn=DE-LU/ingest_date=2026-11-09/batch_id=<checksum>/
  open_meteo/weather_hourly/location=berlin/ingest_date=2026-11-09/batch_id=<checksum>/

s3://eurogrid-warehouse/
  silver/electricity_generation/
  silver/electricity_price/
  silver/weather_hourly/
  gold/mart_hourly_mix/
  gold/mart_daily_price/
  gold/mart_forecast_features/
```

Bucket dipisah agar kebijakan retensi dan akses dapat berbeda. Kredensial Bronze hanya boleh menulis ke bucket Bronze. Kredensial transformasi boleh membaca Bronze dan menulis Silver serta Gold.

## 6. ADR-01: Broker dan semantik stream

| Aspek | Keputusan |
| --- | --- |
| Broker | Redpanda, satu binary, API Kafka |
| Partisi | Berdasarkan `partition_key`, misalnya `DE-LU` dan `de` |
| Delivery | At-least-once |
| Ack | Consumer mengakui setelah batch tulis selesai |
| Dedup | `event_id` disimpan di tabel dedup selama 7 hari |
| Keterlambatan | Watermark 15 menit, event lebih lambat masuk DLQ |
| Alasan | Volume proyek kecil, Redpanda lebih ringan dari Kafka penuh |
| Risiko | Redpanda tetap memakai memori besar saat banyak partisi |

## 7. ADR-02: Format file, object store, dan retensi

| Aspek | Keputusan |
| --- | --- |
| Object store | Garage S3 |
| Format | Parquet |
| Table format | Apache Iceberg |
| Katalog | Iceberg REST dengan metadata di Postgres |
| Partisi | `ingest_date` untuk Bronze, `event_date` untuk Silver dan Gold |
| Retensi Bronze | Selama proyek berjalan |
| Retensi Silver | 12 bulan |
| Retensi Gold | 24 bulan |
| Alasan | Iceberg memberi snapshot dan schema evolution tanpa mengunci ke satu vendor |
| Risiko | Kompatibilitas Garage dengan multipart dan listing harus diuji lebih dulu |

Langkah validasi sebelum M1:

1. Buat bucket dan kredensial terbatas.
2. Unggah file lebih dari 100 MB untuk menguji multipart.
3. Buat tabel Iceberg, tulis 100.000 baris, lalu baca lewat PyIceberg.
4. Lakukan `UPDATE`, `DELETE`, dan `SELECT` snapshot.
5. Baca tabel yang sama lewat Trino.
6. Catat hasil di `docs/evidence/`.

Jika salah satu langkah gagal dan tidak dapat diperbaiki dalam satu hari, MinIO dipakai sebagai cadangan. Keputusan itu dicatat sebagai revisi ADR.

## 8. ADR-03: Batch, stream processor, dan batas resource

| Aspek | Keputusan |
| --- | --- |
| Batch | Prefect 3, Python task, retry 3 kali |
| Stream | Consumer Python dengan `confluent-kafka` |
| Query | Trino |
| Batas resource | Lihat tabel pada bagian 2 |
| Penjadwalan | Harian 04.00 UTC, backfill manual |
| Alasan | Prefect lebih ringan dari Airflow dan cukup untuk satu mesin |
| Risiko | Prefect server dan worker menambah dua service yang harus dijaga |

Aturan operasional:

- Flow tidak boleh berjalan bersamaan pada partisi yang sama.
- Backfill dibatasi dua proses paralel.
- Service yang tidak dipakai saat demo dimatikan lewat profil compose.

## 9. ADR-04: Inference dan keamanan endpoint

| Aspek | Keputusan |
| --- | --- |
| Metode utama | Scheduled batch inference setelah Gold selesai |
| Metode tambahan | Endpoint FastAPI untuk prediksi satu record, opsional |
| Model baseline | Gradient boosting untuk regresi beban |
| Fitur | Jam, hari, bulan, suhu, radiasi, beban tertunda, harga tertunda |
| Split | Berdasarkan waktu, bukan acak |
| Keamanan | JWT, peran admin, operator, viewer, rate limit |
| Alasan | Batch inference lebih mudah diuji dan tidak menambah beban serving |
| Risiko | Data cuaca prakiraan berbeda dari data historis, perlu penanganan fitur |

## 10. ADR-05: Recovery dan backup

| Aspek | Keputusan |
| --- | --- |
| State kritis | Bucket Garage, Postgres, katalog Iceberg, MLflow, konfigurasi |
| Backup | Harian ke direktori berbeda, retensi 7 hari |
| Restore | Diuji pada service terpisah sebelum demo |
| RTO | 30 menit untuk Gold dan serving |
| RPO | 24 jam untuk batch, 5 menit untuk stream |
| Kegagalan yang ditoleransi | Satu service mati, host restart, worker mati saat job |
| Kegagalan yang tidak ditoleransi | Kehilangan bucket Garage, korupsi Postgres tanpa backup |
| Alasan | Satu mesin tidak dapat menjanjikan high availability, jadi fokus pada pemulihan yang terukur |
| Risiko | Backup pada disk yang sama tidak melindungi dari kegagalan disk |

## 11. Keamanan

| Kontrol | Implementasi |
| --- | --- |
| Secret | `.env` di luar Git, izin file 600, rotasi token |
| Akses object storage | Kredensial terpisah per peran, hanya bucket yang diperlukan |
| Akses API | JWT, peran, rate limit, audit log |
| Akses database | User terpisah untuk aplikasi dan admin |
| Port | Hanya API, dashboard, dan Grafana yang diekspos ke host |
| Audit | Log akses tulis dan tindakan admin |
| Data pribadi | Tidak ada data pribadi yang diproses |

## 12. Observability

| Sinyal | Sumber | Tujuan |
| --- | --- | --- |
| Metrik host | Node exporter | Prometheus dan Grafana |
| Status job | Prefect | Prometheus dan Grafana |
| Durasi dan row count | Prefect task | Log dan metrik |
| Lag stream | Consumer | Prometheus |
| Error API | FastAPI middleware | Loki dan Grafana |
| Freshness | Query Gold | Dashboard dan alert |

Tiga alert wajib:

| Alert | Ambang | Jendela | Severity |
| --- | --- | --- | --- |
| Job gagal | Satu flow run gagal | Segera | Kritis |
| Lag stream | Di atas 10 menit | 5 menit | Peringatan |
| Resource kritis | RAM di atas 85 persen atau disk di atas 85 persen | 10 menit | Peringatan |

## 13. Urutan deploy dari clone bersih

1. `git clone` repositori.
2. `cp .env.example .env`, lalu isi token dan kredensial.
3. `podman-compose up -d garage postgres`.
4. Inisialisasi layout Garage dan buat bucket.
5. `podman-compose up -d iceberg-rest prefect-server`.
6. Jalankan migrasi katalog dan buat tabel.
7. `podman-compose up -d redpanda trino mlflow metabase api`.
8. `podman-compose up -d prometheus grafana marquez`.
9. Jalankan `make test`.
10. Jalankan flow pertama dan periksa dashboard.

Setiap langkah harus punya health check. Deploy dianggap berhasil bila semua service berstatus sehat dan flow pertama selesai.

## 14. Struktur repositori target

```
.
|-- compose.yaml
|-- Makefile
|-- pyproject.toml
|-- .env.example
|-- data/
|-- docs/
|   |-- PRD.md
|   |-- PRD.pdf
|   |-- TEAM.pdf
|   |-- architecture.md
|   |-- data-contract.md
|   `-- evidence/
|-- flows/
|   |-- batch_ingest.py
|   |-- silver_transform.py
|   `-- gold_build.py
|-- src/eurogrid/
|   |-- bronze/
|   |-- silver/
|   |-- gold/
|   |-- sources/
|   |-- serving/
|   `-- stream/
|-- tests/
`-- dashboards/
```

## 15. Hal yang belum diputuskan

| Pertanyaan | Tenggat | Pemilik |
| --- | --- | --- |
| Katalog Iceberg memakai REST atau Nessie | Sebelum M1 | Ian |
| Redpanda atau Kafka KRaft | Sebelum M4 | El |
| Marquez atau OpenMetadata | Sebelum M2 | Nad |
| Metabase atau Superset | Sebelum M5 | El |
| Batas memori final per service | Setelah benchmark M1 | Ian |
