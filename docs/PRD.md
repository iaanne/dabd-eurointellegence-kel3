# PRD: EuroGrid Intelligence

**Product Requirements Document**

| Atribut | Isi |
| --- | --- |
| Versi | 1.0 |
| Tanggal | 10 November 2026 |
| Status | Disetujui untuk pelaksanaan |
| Pemilik produk | Kelompok 3, TBP Advanced Data Platform |
| Ruang lingkup | Jerman dan zona penawaran DE-LU, lalu ekspansi ke negara lain |
| Pengganti | Deck konsep awal dan catatan increment 1 |

## 1. Ringkasan

EuroGrid Intelligence adalah platform data kelistrikan Eropa yang mengubah data terbuka dari beberapa penyedia menjadi lakehouse, produk data, layanan API, dashboard, dan model peramalan beban.

Fase pertama memakai Jerman sebagai negara percontohan. Alasannya, data Jerman paling lengkap, lisensinya jelas, dan zona DE-LU memiliki harga day-ahead yang dapat dipakai publik. Setelah alur Jerman terbukti dari sumber sampai serving, negara lain ditambahkan tanpa mengubah kontrak inti.

Masalah utama bukan mendapatkan data. Data tersedia gratis di beberapa situs. Masalahnya adalah menyatukan format, satuan, zona waktu, definisi istilah, revisi, dan cara mengambil ulang data yang sama tanpa menggandakan hasil.

Produk ini menjawab masalah tersebut dengan satu jalur data yang dapat diulang, diuji, dan diaudit.

## 2. Latar belakang

### 2.1 Kondisi data saat ini

Data kelistrikan Eropa tersebar di beberapa penyedia:

- Energy-Charts Fraunhofer ISE menyediakan pembangkitan, beban, harga, dan perdagangan lintas negara.
- Open-Meteo menyediakan cuaca historis dan prakiraan.
- ENTSO-E Transparency Platform menyediakan data otoritatif beban dan aliran lintas negara, tetapi memerlukan token.

Setiap penyedia memakai format respons, satuan, dan resolusi waktu yang berbeda. Sebagian data diterbitkan ulang ketika ada koreksi. Istilah yang mirip juga punya arti berbeda. Contohnya, `load` dan `consumption`, atau `exchange` dan `physical flow`.

Akibatnya, dua analis dapat menjawab pertanyaan yang sama dengan angka berbeda tanpa tahu sumber perbedaannya.

### 2.2 Peluang

Satu pipeline yang menjaga provenance, riwayat revisi, dan kualitas data membuka beberapa produk:

- Dashboard harga dan bauran pembangkitan per jam.
- Peringatan dini ketika beban atau harga bergerak di luar kebiasaan.
- Peramalan beban jangka pendek untuk perencanaan.
- Perbandingan antarnegara setelah cakupan diperluas.

## 3. Tujuan dan metrik keberhasilan

### 3.1 Tujuan produk

1. Menyediakan satu jalur data dari sumber terbuka sampai lapisan serving.
2. Menjaga agar ingest ulang, backfill, dan revisi tidak menghasilkan duplikasi.
3. Menyediakan minimal tiga produk data dengan skema, pemilik, dan mutu yang jelas.
4. Menyediakan dashboard dan satu model peramalan yang dapat dievaluasi.
5. Menyediakan bukti operasional: metrik, log, alert, backup, dan pemulihan.

### 3.2 Metrik keberhasilan

| Metrik | Target | Cara mengukur |
| --- | --- | --- |
| Cakupan sumber | 2 penyedia listrik dan 1 penyedia cuaca aktif | Batch Bronze dan metadata sumber |
| Idempotensi batch | Ingest ulang pada snapshot sama menghasilkan batch yang sama | `created=false` dan `batch_id` identik |
| Backfill | Rentang 30 hari dapat diulang dengan hasil semantik sama | Checksum Gold sebelum dan sesudah |
| Ketepatan waktu batch | Data harian tersedia paling lambat 06.00 UTC | Waktu selesai flow Prefect |
| Kualitas Silver | 100 persen baris punya status valid atau alasan karantina | Laporan quality gate |
| Serving | 10 query dan 3 endpoint aktif | Uji kontrak API |
| Model | Satu model dengan MAE lebih baik dari baseline naif | Laporan eksperimen MLflow |
| Operasional | 3 alert teruji dari trigger sampai resolved | Log notifikasi |
| Pemulihan | RTO 30 menit dan RPO 24 jam untuk layer Gold | Uji restore tercatat |

### 3.3 Non-goals

- Bukan platform trading dan tidak mengirim order ke pasar.
- Tidak memakai data pribadi atau data pelanggan.
- Tidak menargetkan ketersediaan tinggi multi-region pada fase ini.
- Tidak memakai layanan cloud terkelola sebagai komponen utama.
- Tidak mengejar cakupan seluruh Eropa sebelum alur Jerman stabil.

## 4. Pengguna dan kebutuhan

| Persona | Kebutuhan utama | Produk yang dipakai |
| --- | --- | --- |
| Analis pasar energi | Harga, bauran pembangkitan, dan tren beban | Dashboard Metabase |
| Operator platform | Status job, kegagalan, dan freshness | Prefect UI, Grafana |
| Pengembang aplikasi | Akses data bersih lewat API | FastAPI dan Trino |
| Data scientist | Data latih dan riwayat eksperimen | Gold table, MLflow |
| Dosen dan penguji | Bukti pemenuhan F-01 sampai F-18 | Dokumentasi, evidence index |
| Publik | Penjelasan visual yang mudah dibaca | Portal analitik |

## 5. Lingkup dan asumsi

### 5.1 Lingkup fase

| Fase | Lingkup | Kriteria keluar |
| --- | --- | --- |
| Fase 0, selesai | Sumber ke Bronze lokal untuk Jerman | 3 batch, 15.456 baris, 15 tes lulus |
| Fase 1 | Garage S3, Iceberg, Prefect, backfill | Bronze di object store, jadwal berjalan |
| Fase 2 | Silver, quality gate, Gold, Trino | 3 dataset per layer, 10 query |
| Fase 3 | Stream Redpanda, event-time, dedup, DLQ | Consumer berjalan tanpa trigger manual |
| Fase 4 | ML, MLflow, inference, API, dashboard | Model terdaftar, 3 endpoint, 4 metrik dashboard |
| Fase 5 | Observability, alert, keamanan, backup | 3 alert teruji, restore terbukti |
| Fase 6 | Dokumentasi, video, matriks bukti | Semua F-01 sampai F-18 punya bukti |

### 5.2 Asumsi

- Pengerjaan dilakukan di satu mesin lokal dengan 12 vCPU, RAM 62 GB, dan ruang kosong minimal 200 GB.
- Container dijalankan dengan Podman dan `podman-compose` karena Docker tidak tersedia.
- Stack berjalan pada satu host. High availability multi-node bukan target.
- Token ENTSO-E sedang diurus. Selama belum aktif, beban diambil dari seri `load` Energy-Charts.
- Deadline kelas menjadi acuan akhir. Rencana memakai satuan minggu, bukan tanggal tetap.

### 5.3 Batasan

- Dataset harus legal, tidak mengandung data pribadi, dan mencantumkan lisensi.
- Data sintetis tidak dipakai sebagai pengganti data nyata.
- Seluruh komponen inti berjalan lokal, bukan layanan cloud terkelola.
- Resource satu mesin membatasi jumlah service yang dapat berjalan bersamaan.

## 6. Sumber data dan lisensi

| Sumber | Data | Akses | Lisensi | Status |
| --- | --- | --- | --- | --- |
| Energy-Charts API v2 | Pembangkitan, beban, harga, perdagangan lintas negara | REST JSON tanpa token | CC BY 4.0 untuk data yang dipakai, atribusi energy-charts.info | Aktif |
| Open-Meteo Historical Weather | Suhu, angin, radiasi, presipitasi | REST JSON tanpa token | CC BY 4.0 non-komersial, atribusi Open-Meteo.com | Aktif |
| ENTSO-E Transparency | Beban dan aliran otoritatif | REST XML dengan token | Sesuai ketentuan platform | Menunggu token aktif |

Aturan lisensi:

1. Lisensi asli setiap respons disimpan di `metadata.json` dan kolom `license`.
2. Harga di luar DE-LU tidak dipakai untuk artefak publik tanpa pengecekan ulang.
3. Atribusi penyedia ditampilkan di dashboard dan dokumentasi.
4. Data yang lisensinya tidak jelas tidak masuk Gold.

## 7. Kebutuhan fungsional

Setiap requirement dipetakan langsung ke F-01 sampai F-18 pada spesifikasi TBP. Kolom pemilik memakai inisial anggota tim.

### 7.1 Platform dan orkestrasi

| ID | Kebutuhan | Implementasi | Kriteria lulus | Pemilik |
| --- | --- | --- | --- | --- |
| F-01 | Deployment dan isolasi service | Compose Podman berisi Garage, Postgres, Iceberg REST, Prefect, Redpanda, Trino, MLflow, Metabase, API, Prometheus, Grafana. Volume terpisah untuk data dan konfigurasi. Health check per service. | Clone bersih dapat deploy ulang dengan urutan terdokumentasi. Data bertahan setelah restart container. | Ian |
| F-02 | Pemrosesan batch dan penjadwalan | Prefect flow menarik data ke Bronze dengan `batch_id`, `source`, `ingest_time`, `checksum`, dan `row_count`. Jadwal harian dan mode manual. | Dua ingest pada snapshot sama tidak menggandakan output. Kegagalan job tercatat dan dapat diulang. | Ian |
| F-03 | Transformasi incremental, retry, dan backfill | Prefect task melakukan transformasi Bronze ke Silver dan Gold dengan business key. Retry otomatis dan backfill per rentang tanggal. | Backfill rentang sama dua kali menghasilkan isi semantik sama. Perubahan sumber mengikuti kebijakan revisi. | Jim |

### 7.2 Stream

| ID | Kebutuhan | Implementasi | Kriteria lulus | Pemilik |
| --- | --- | --- | --- | --- |
| F-04 | Stream processing | Redpanda sebagai broker. Producer Python membentuk event dari polling Energy-Charts. Consumer menulis ke Bronze stream dan tabel staging. | Consumer memproses event tanpa trigger manual. Lag terlihat. Setelah restart, pesan tertunda diproses. | El |
| F-05 | Event-time, keterlambatan, dan deduplikasi | `event_time` dipisahkan dari `ingest_time`. Watermark 15 menit. Dedup berdasarkan `event_id`. Event rusak masuk DLQ. | Event duplikat dihitung satu. Event tidak berurutan diproses sesuai kebijakan tertulis. | El |

### 7.3 Lakehouse dan kualitas

| ID | Kebutuhan | Implementasi | Kriteria lulus | Pemilik |
| --- | --- | --- | --- | --- |
| F-06 | Medallion architecture | Bronze menyimpan respons mentah dan metadata. Silver berisi data tervalidasi. Gold berisi fact, agregat, dan fitur dengan grain jelas. Minimal tiga dataset aktif per layer. | Perubahan di Bronze dapat ditelusuri sampai Gold. Skema dan business key terdokumentasi. | Ian dan Nad |
| F-07 | Penyimpanan analitik dan konsistensi | Parquet di Garage S3, tabel Iceberg dengan katalog REST, metadata katalog di Postgres. Snapshot dan schema evolution diaktifkan. | Write, update, upsert, dan replay berjalan. Snapshot tabel dapat ditunjukkan. | Ian |
| F-08 | Quality gate | Pemeriksaan not-null, tipe, rentang, keunikan, dan konsistensi antar dataset. Baris gagal masuk karantina dengan alasan. Ambang gagal memblokir publish Gold. | Setiap data invalid yang disuntikkan terlacak. Laporan memuat jumlah lulus dan gagal. | Nad |
| F-09 | Metadata, ownership, dan lineage | Katalog YAML di repositori, event OpenLineage dari Prefect, dan Marquez sebagai penampil lineage. Setiap dataset punya pemilik, retensi, dan jadwal refresh. | Satu jalur lineage lengkap dari Bronze ke Silver ke Gold cocok dengan run yang dijalankan. | Nad |

### 7.4 Serving

| ID | Kebutuhan | Implementasi | Kriteria lulus | Pemilik |
| --- | --- | --- | --- | --- |
| F-10 | Serving SQL dan API | Tiga mart Gold di Trino. Sepuluh query analitik terdokumentasi. FastAPI menyediakan minimal tiga endpoint baca. OpenAPI dihasilkan otomatis. | Query dan API mengembalikan data sesuai. Tanggal tidak valid menghasilkan pesan error yang jelas. | Jim dan El |

### 7.5 Machine learning

| ID | Kebutuhan | Implementasi | Kriteria lulus | Pemilik |
| --- | --- | --- | --- | --- |
| F-11 | Dataset ML dan versioning | Data latih dari Gold. Split waktu untuk mencegah kebocoran. Seed tetap. MLflow mencatat parameter, metrik, artefak, versi kode, dan versi dataset. | Dua eksperimen dapat dibandingkan pada test set yang sama. Artefak dan versi dapat ditunjukkan. | Jim |
| F-12 | Integrasi inference | Scheduled batch inference sebagai jalur utama. Tabel prediksi memuat `input_record_id`, `model_version`, `predicted_at`, nilai, dan status error. | Prediksi dapat dikaitkan ke record input dan model. Payload rusak ditolak atau ditandai. | Jim |

### 7.6 Analitik dan operasional

| ID | Kebutuhan | Implementasi | Kriteria lulus | Pemilik |
| --- | --- | --- | --- | --- |
| F-13 | Dashboard analitik | Metabase membaca Trino. Empat metrik bisnis, dua filter, indikator freshness, dan nilai prediksi. Refresh otomatis. | Angka dashboard konsisten dengan SQL untuk dua rentang tanggal. | El |
| F-14 | Metrik dan log terstruktur | Prometheus mengumpulkan metrik host dan aplikasi. Log JSON memuat timestamp, severity, service, dan run_id. Grafana menjadi tampilan utama. | Satu error dapat dilacak dari dashboard sampai run atau input bermasalah. | Nad |
| F-15 | Tiga alert teruji | Alert job gagal, lag stream tinggi, dan resource kritis. Setiap alert punya ambang, jendela, severity, pemilik, dan kanal notifikasi. | Setiap alert terpicu, notifikasi diterima, lalu resolved setelah perbaikan. | Nad |
| F-16 | Keamanan dan audit | Autentikasi FastAPI dengan JWT. Peran admin, operator, viewer. Secret di `.env` di luar Git. Port internal dibatasi. Audit log untuk akses sensitif. | Viewer gagal melakukan tindakan admin. Tidak ada secret di repositori. Akses sensitif tercatat. | El |
| F-17 | Recovery, backup, dan restore | Backup Garage, Postgres, katalog Iceberg, dan model registry ke direktori berbeda. Uji restart satu komponen. RTO dan RPO diukur. | Pipeline melanjutkan tanpa duplikasi Gold. Checksum setelah restore sesuai baseline. | Ian |
| F-18 | Tes dan reproducibility | Satu perintah `make test`. Fixture deterministik. Image dipin. `.env.example` lengkap. Instruksi deploy dari clone bersih. | Tes berjalan dari clone bersih. Hasil dapat direproduksi. | Nad |

## 8. Arsitektur solusi

### 8.1 Gambaran lapisan

```
Sumber
  Energy-Charts  Open-Meteo  ENTSO-E (menunggu token)
        |             |            |
        +-------------+------------+
                      |
             Prefect flows (batch)
                      |
        Garage S3 + Apache Iceberg
        Bronze -> Silver -> Gold
                      |
        +-------------+-------------+
        |             |             |
      Trino        MLflow        OpenLineage
        |             |             |
   FastAPI        Prediksi       Marquez
        |             |
    Metabase      Dashboard
```

Jalur stream berjalan terpisah:

```
Energy-Charts poller -> Redpanda -> Consumer -> Bronze stream -> Silver
```

### 8.2 Pilihan teknologi

| Lapisan | Pilihan | Alasan | Alternatif yang ditolak |
| --- | --- | --- | --- |
| Object storage | Garage S3 | Ringan, satu binary, S3-compatible, cocok untuk satu mesin | MinIO lebih berat; cloud storage melanggar batasan lokal |
| Table format | Apache Iceberg | Snapshot, schema evolution, ACID, dukungan Trino dan PyIceberg | Delta dan Hudi lebih terikat ekosistem tertentu |
| Katalog | Iceberg REST catalog dengan Postgres | Stabil, terpisah dari compute, mudah di-backup | Katalog berbasis file lebih rapuh saat konkurensi |
| Batch orchestration | Prefect 3 | Python-native, UI jelas, retry dan scheduling bawaan | Airflow lebih berat untuk satu mesin |
| Stream broker | Redpanda | Satu binary, API Kafka, lag mudah dipantau | Kafka KRaft lebih berat; tetap didukung sebagai cadangan |
| Stream processing | Consumer Python | Cukup untuk volume proyek, mudah diuji | Flink dan Spark Streaming berlebihan |
| Query engine | Trino | SQL atas Iceberg, mendukung banyak katalog | DuckDB cukup untuk lokal tetapi kurang untuk multi-user |
| ML | scikit-learn dan MLflow | Baseline cepat, tracking dan registry lengkap | Model deep learning tidak diperlukan untuk baseline |
| Serving | FastAPI | Ringan, OpenAPI otomatis, mudah diuji | Flask kurang terstruktur untuk kontrak API |
| BI | Metabase | Dashboard cepat, koneksi Trino, filter bawaan | Superset lebih berat |
| Observability | Prometheus, Grafana, Loki | Standar lokal, metrik dan log terpisah | Solusi cloud melanggar batasan |
| Governance | OpenLineage dan Marquez, katalog YAML | Lineage otomatis dari Prefect, ringan | OpenMetadata berat untuk satu mesin |
| Deployment | Podman dan podman-compose | Docker tidak tersedia, kompatibel compose | Kubernetes lokal terlalu berat |

### 8.3 Keputusan arsitektur

Lima keputusan wajib didokumentasikan pada `docs/architecture.md`, yaitu ADR-01 sampai ADR-05. Ringkasnya:

- ADR-01: Redpanda sebagai broker, at-least-once delivery, partisi per zona, dedup di consumer.
- ADR-02: Parquet di Garage S3, Iceberg, partisi per tanggal, retensi Bronze tanpa batas selama proyek.
- ADR-03: Prefect untuk batch, consumer Python untuk stream, anggaran resource per service.
- ADR-04: Batch inference sebagai jalur utama, endpoint API opsional, model baseline gradient boosting.
- ADR-05: Backup Garage dan Postgres, RTO 30 menit, RPO 24 jam, kegagalan satu service dapat ditoleransi.

## 9. Alur data

### 9.1 Alur batch

1. Prefect flow dijalankan oleh jadwal atau manual.
2. Flow menentukan rentang tanggal dan daftar dataset.
3. Klien memanggil API sumber dengan retry dan timeout.
4. Respons mentah disimpan ke Bronze bersama metadata dan checksum.
5. Jika checksum sudah ada, batch tidak dibuat ulang.
6. Task Silver membaca batch baru, menormalkan waktu, tipe, dan satuan.
7. Quality gate memeriksa baris. Baris gagal masuk karantina.
8. Task Gold membentuk fact, agregat, dan fitur.
9. Trino membaca tabel Iceberg. API dan dashboard membaca Trino.
10. Metrik dan lineage dikirim ke Prometheus dan Marquez.

### 9.2 Alur stream

1. Producer memanggil Energy-Charts setiap interval.
2. Producer membentuk event dengan `event_id`, `event_time`, `ingest_time`, `partition_key`, dan payload.
3. Event dikirim ke topik Redpanda per zona.
4. Consumer membaca event, membuang duplikat, dan menangani keterlambatan dengan watermark.
5. Event valid ditulis ke Bronze stream. Event rusak masuk DLQ.
6. Consumer mencatat offset dan lag ke Prometheus.

### 9.3 Lapisan medallion

| Lapisan | Isi | Format | Retensi |
| --- | --- | --- | --- |
| Bronze | Respons mentah, metadata ingest, checksum | JSON dan Parquet | Selama proyek |
| Silver | Data tervalidasi, tipe dan waktu seragam, status kualitas | Iceberg Parquet | 12 bulan |
| Gold | Fact, agregat, fitur, tabel prediksi | Iceberg Parquet | 24 bulan |
| Serving | View dan tabel untuk API serta dashboard | Trino view | Mengikuti Gold |

## 10. Kontrak data

Kontrak lengkap ada di `docs/data-contract.md`. Ringkasan yang tidak boleh berubah tanpa versi baru:

- Grain listrik 15 menit dan cuaca 1 jam.
- `timestamp_utc` menjadi waktu utama. `timestamp_local` disimpan untuk audit.
- Kunci bisnis listrik: `dataset`, `country` atau `bzn`, `series_id`, `timestamp_utc`.
- Kunci bisnis cuaca: `location`, `variable`, `timestamp_utc`.
- Setiap baris membawa `license`, `source`, `batch_id`, dan `ingested_at`.
- Revisi sumber disimpan sebagai batch baru. Silver memilih nilai terbaru berdasarkan `generated_at` dan `available_until`.

## 11. Kualitas data

| Pemeriksaan | Aturan | Tindakan bila gagal |
| --- | --- | --- |
| Not null | Kolom kunci dan nilai wajib terisi, kecuali nilai sumber memang null | Karantina |
| Tipe | `timestamp_utc` harus timestamp UTC, nilai harus numerik | Karantina |
| Rentang | Beban 0 sampai 150.000 MW, harga -500 sampai 5.000 EUR/MWh, suhu -50 sampai 60 Celsius | Karantina dan alert |
| Keunikan | Tidak ada duplikat pada business key | Pilih baris terbaru, catat jumlah duplikat |
| Konsistensi | Jumlah pembangkitan dan beban masuk akal terhadap kapasitas terpasang | Tandai dan alert |
| Kelengkapan | Minimal 95 persen interval hadir per hari | Tandai sebagian, blokir publish bila di bawah ambang |

Ambang dapat diubah lewat konfigurasi. Setiap perubahan dicatat di repositori.

## 12. Kebutuhan non-fungsional

| Aspek | Target |
| --- | --- |
| Resource | Maksimal 24 GB RAM dan 8 vCPU untuk seluruh stack saat demo |
| Freshness batch | Data harian selesai paling lambat 06.00 UTC |
| Freshness stream | Lag di bawah 5 menit pada kondisi normal |
| Latensi API | Persentil 95 di bawah 500 ms untuk query satu bulan |
| Ketersediaan | Satu host, target 99 persen selama jam demo |
| Keamanan | Tidak ada secret di Git, peran terpisah, port internal tidak terbuka ke jaringan publik |
| Audit | Akses tulis dan tindakan admin tercatat |
| Portabilitas | Deploy dari clone bersih dengan satu perintah compose dan satu perintah migrasi |
| Reproducibility | Versi image dipin, seed tetap, fixture deterministik |

## 13. Roadmap dan milestone

| Milestone | Minggu | Isi | Kriteria selesai | Penanggung jawab |
| --- | --- | --- | --- | --- |
| M0 | Selesai | Bronze lokal, 3 batch, 15.456 baris, 15 tes, kontrak data | Bukti di `docs/evidence/` | Tim |
| M1 | 1 | Garage S3, Iceberg, Prefect, Bronze pindah ke object store, backfill 30 hari | Job terjadwal berjalan, snapshot Iceberg ada | Ian |
| M2 | 2 | Silver, quality gate, karantina, lineage awal | 3 dataset Silver, laporan mutu | Nad |
| M3 | 3 | Gold 3 mart, 10 query, Trino | Query konsisten, mart terdokumentasi | Jim |
| M4 | 4 | Redpanda, producer, consumer, event-time, DLQ | Lag terlihat, replay berhasil | El |
| M5 | 5 | ML, MLflow, inference, API, dashboard | Model terdaftar, 3 endpoint, 4 metrik | Jim dan El |
| M6 | 6 | Observability, 3 alert, keamanan, backup, restore | Alert teruji, restore terbukti | Nad dan Ian |
| M7 | 7 | Dokumentasi, video demo, matriks F-01 sampai F-18 | Semua bukti terkumpul | Tim |

## 14. Pembagian tim

Rincian peran, kepemilikan requirement, dan aturan kolaborasi ada di `docs/TEAM.pdf`.

| Anggota | Peran | Requirement utama |
| --- | --- | --- |
| Ian | Platform dan storage | F-01, F-02, F-07, F-17 |
| Nad | Kualitas data dan governance | F-08, F-09, F-14, F-15, F-18 |
| Jim | Analitik dan machine learning | F-03, F-10 SQL, F-11, F-12 |
| El | Serving, stream, dan keamanan | F-04, F-05, F-10 API, F-13, F-16 |

## 15. Risiko dan mitigasi

| Risiko | Dampak | Kemungkinan | Mitigasi |
| --- | --- | --- | --- |
| Token ENTSO-E belum aktif | Sumber otoritatif tertunda | Tinggi | Pakai `load` Energy-Charts, siapkan adapter ENTSO-E di belakang antarmuka yang sama |
| Garage tidak sepenuhnya kompatibel dengan Iceberg | Gagal tulis atau multipart | Sedang | Uji multipart dan listing lebih dulu, siapkan MinIO sebagai cadangan |
| Resource satu mesin tidak cukup | Service saling mengganggu | Sedang | Batasi memori per service, jalankan bertahap, matikan service yang tidak dipakai saat demo |
| Prefect worker mati saat job | Batch tertunda | Sedang | Retry, health check, dan alert job gagal |
| Redpanda berat | Lag dan konsumsi memori | Sedang | Batasi partisi dan retensi, siapkan Kafka KRaft sebagai cadangan |
| Skema sumber berubah | Transformasi gagal | Sedang | Kontrak data, tes fixture, dan validasi skema |
| Waktu pengerjaan mepet | Fitur tidak selesai | Tinggi | Prioritaskan F-01 sampai F-18, tunda fitur opsional |
| Kebocoran secret | Risiko keamanan | Rendah | `.env` di luar Git, rotasi token, audit konfigurasi |

## 16. Definisi selesai

Produk dianggap selesai untuk penilaian bila:

1. Semua F-01 sampai F-18 punya implementasi dan bukti.
2. `podman-compose up` dari clone bersih menghasilkan stack yang sehat.
3. `make test` lulus tanpa error.
4. Dashboard menampilkan minimal empat metrik dan dua filter.
5. Tiga alert teruji dari trigger sampai resolved.
6. Backup dan restore terbukti dengan checksum yang cocok.
7. Video demo dan matriks pemenuhan tersedia.
8. Tidak ada secret atau data pribadi di repositori.

## 17. Status saat ini

| Item | Status | Bukti |
| --- | --- | --- |
| Klien Energy-Charts | Selesai | `src/eurogrid/sources/energy_charts.py` |
| Klien Open-Meteo | Selesai | `src/eurogrid/sources/open_meteo.py` |
| Bronze lokal | Selesai | 3 batch, 15.456 baris |
| Idempotensi | Selesai | `created=false`, batch id sama |
| Perintah inspeksi | Selesai | `eurogrid list`, `eurogrid show` |
| Tes | Selesai | 15 tes lulus |
| Kontrak data | Selesai | `docs/data-contract.md` |
| Deck progress | Selesai | `slides/EuroGrid_Progress_2026-11-09.pptx` |
| Garage S3 dan Iceberg | Belum | Rencana M1 |
| Prefect | Belum | Rencana M1 |
| Silver dan Gold | Belum | Rencana M2 dan M3 |
| Stream | Belum | Rencana M4 |
| ML dan serving | Belum | Rencana M5 |
| Observability dan backup | Belum | Rencana M6 |
| ENTSO-E | Terblokir | Token mengembalikan 401 per 10 November 2026 |

## 18. Glosarium

| Istilah | Arti |
| --- | --- |
| Batch | Proses mengolah sekumpulan data pada satu waktu, bukan per event. |
| Stream | Aliran event yang diproses terus-menerus saat tiba. |
| Lakehouse | Gabungan penyimpanan file murah dan kemampuan tabel analitik. |
| Medallion | Pola tiga lapisan data: Bronze mentah, Silver tervalidasi, Gold siap pakai. |
| Idempoten | Dijalankan berulang dengan hasil akhir yang sama. |
| Watermark | Batas waktu untuk memutuskan kapan event terlambat tidak ditunggu lagi. |
| DLQ | Dead letter queue, tempat pesan yang gagal diproses. |
| Lineage | Jejak asal dan perjalanan data dari input sampai output. |
| Quality gate | Pemeriksaan otomatis yang menentukan data boleh lanjut atau tidak. |
| Mart | Tabel atau view yang disusun untuk kebutuhan analitik tertentu. |
| Inference | Proses memakai model terlatih untuk menghasilkan prediksi. |
| Freshness | Seberapa baru data yang tersedia dibandingkan waktu sekarang. |
| RTO | Recovery time objective, batas waktu pemulihan yang ditargetkan. |
| RPO | Recovery point objective, batas kehilangan data yang dapat diterima. |
