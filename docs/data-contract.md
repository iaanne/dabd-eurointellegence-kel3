# Kontrak Data: Jerman

Dokumen ini berlaku untuk lapisan Bronze yang sudah berjalan. Semua waktu
disimpan dalam UTC di kolom `timestamp_utc`, sedangkan waktu asli dari sumber
disimpan di `timestamp_local` agar bisa diaudit.

## 1. Energy-Charts API v2

Basis URL: `https://api.energy-charts.info`. Semua endpoint mengembalikan satu
bungkus JSON yang menjelaskan datanya sendiri.

### 1.1 Metadata bungkus

| Field | Arti | Contoh |
| --- | --- | --- |
| `schema_version` | Versi skema respons | `2.0` |
| `endpoint` | Nama dataset | `public_power` |
| `country` | Kode negara | `de` |
| `bidding_zone` | Zona penawaran untuk harga | `DE-LU` |
| `timezone` | Zona waktu timestamp | `Europe/Berlin` |
| `resolution` | Resolusi ISO 8601 | `PT15M` |
| `interval_minutes` | Panjang interval dalam menit | `15` |
| `unit` | Satuan nilai | `MW`, `EUR / MWh`, `GW` |
| `generated_at` | Waktu respons dibuat | ISO 8601 dengan offset |
| `available_from`, `available_until` | Rentang yang benar-benar berisi data | ISO 8601 |
| `series` | Daftar seri berisi `id` dan `name` | `[{"id": "solar", ...}]` |
| `data` | Daftar titik waktu | `[{"timestamp": ..., "values": {...}}]` |
| `license` | Lisensi respons | CC BY 4.0, atribusi |
| `deprecated` | Penanda endpoint lama | `false` |

Setiap titik data memakai `timestamp` yang menandai awal interval dan `values`
berisi pasangan `series_id` ke nilai. Nilai bisa negatif, misalnya ekspor atau
konsumsi penyimpanan pompa.

### 1.2 Dataset yang dipakai

| Dataset | Parameter | Grain | Satuan | Kegunaan |
| --- | --- | --- | --- | --- |
| `public_power` | `country` | 15 menit | MW | Pembangkitan per jenis, beban, residual load, porsi terbarukan |
| `price` | `bzn` | 15 menit | EUR / MWh | Harga day-ahead per zona |
| `cbet` | `country` | 15 menit | GW | Perdagangan lintas negara terjadwal |
| `cbpf` | `country` | 15 menit | GW | Aliran fisik lintas negara |

Nilai positif pada `cbet` dan `cbpf` berarti impor, nilai negatif berarti ekspor.
Seri `load` pada `public_power` adalah beban aktual, dan inilah target peramalan
untuk model ML.

### 1.3 Lisensi

- `public_power` di Jerman: CC BY 4.0, atribusi energy-charts.info.
- `price` zona DE-LU: CC BY 4.0 dari Bundesnetzagentur dan SMARD.
- `price` di luar DE-LU: dibatasi untuk pemakaian privat dan internal sesuai
  dokumentasi API. Zona seperti ini tidak dipakai untuk artefak yang
  dipublikasikan tanpa pengecekan ulang.
- Lisensi asli dari respons selalu disimpan di `metadata.json` dan di kolom
  `license` pada Parquet.

## 2. Open-Meteo Historical Weather API

Basis URL: `https://archive-api.open-meteo.com/v1/archive`.

| Field | Arti |
| --- | --- |
| `latitude`, `longitude` | Koordinat yang dipakai penyedia, bisa sedikit berbeda dari permintaan |
| `timezone` | `UTC` karena permintaan memakai `timezone=UTC` |
| `hourly.time` | Daftar timestamp awal jam |
| `hourly.<variable>` | Nilai per jam, bisa `null` |
| `hourly_units` | Satuan tiap variabel |

Variabel awal: `temperature_2m` (derajat Celsius), `wind_speed_10m` (km/jam),
`shortwave_radiation` (W/m2), dan `precipitation` (mm).

Lisensi CC BY 4.0 untuk pemakaian non-komersial dengan atribusi Open-Meteo.com.
Batas gratis 10.000 panggilan per hari, 5.000 per jam, dan 600 per menit.

## 3. ENTSO-E Transparency Platform

Basis URL: `https://web-api.tp.entsoe.eu/api`. Autentikasi memakai
`securityToken` pada query string. Token hanya dibaca dari `.env`, tidak pernah
disimpan di batch. Di metadata, nilainya diganti `***`.

Dataset yang dipakai baru `actual_load` dengan `documentType=A65` dan
`processType=A16`, yaitu beban listrik aktual per bidding zone. Parameter lain
adalah `outBiddingZone_Domain` berisi kode EIC zona, misalnya
`10Y1001A1001A82H` untuk DE-LU, serta `periodStart` dan `periodEnd` berformat
`YYYYMMDDHHMM` dalam UTC.

Respons berupa `GL_MarketDocument` berisi satu atau beberapa `TimeSeries`. Setiap
`TimeSeries` punya `Period` dengan `timeInterval`, `resolution`, dan daftar
`Point`. Nilai diambil dari `quantity`, sedangkan posisi waktu dihitung dari
`position`:

```
timestamp_utc = timeInterval.start + (position - 1) * resolution
```

Kolom Parquet: `timestamp_utc`, `dataset`, `series_id`, `series_name`, `value`,
`unit`, `resolution`, `bidding_zone`, `country`, `document_type`,
`process_type`, dan `license`. Satuan beban adalah `MAW` (megawatt).

Field dokumen yang berubah setiap panggilan, seperti `mRID`, `revisionNumber`,
dan `createdDateTime`, tidak ikut dihitung dalam checksum. Karena itu ingest
ulang dengan isi sama tetap menghasilkan `batch_id` yang sama.

## 4. Kunci bisnis

| Dataset | Kunci bisnis |
| --- | --- |
| Energy-Charts | `(dataset, country atau bzn, series_id, timestamp_utc)` |
| Cuaca | `(location, variable, timestamp_utc)` |
| ENTSO-E | `(dataset, bidding_zone, series_id, timestamp_utc)` |

Kunci ini yang nanti dipakai untuk deduplikasi di Silver. Revisi dari sumber
disimpan sebagai batch baru di Bronze, lalu Silver memilih nilai terbaru
berdasarkan `generated_at` atau `available_until` dari batch yang lebih baru.

## 5. Envelope event untuk stream

Event stream belum dijalankan, tetapi bentuknya sudah ditetapkan agar Silver dan
Gold tidak berubah saat producer dibuat.

| Field | Isi |
| --- | --- |
| `event_id` | SHA-256 dari `dataset`, zona, `timestamp_utc`, `series_id`, dan nilai |
| `event_time` | Awal interval pengukuran, UTC |
| `ingest_time` | Waktu event masuk ke sistem, UTC |
| `payload_version` | `1` |
| `partition_key` | Kode zona, misalnya `DE-LU` atau `de` |
| `source` | `energy_charts` |
| `payload` | Objek berisi `series_id`, `value`, `unit` |

Karena Energy-Charts adalah API tarik, bukan push, producer akan memanggil
endpoint setiap interval dan membentuk event dari data terbaru. Ini tetap
memenuhi syarat stream selama consumer berjalan terus, lag terlihat, dan event
duplikat dibuang berdasarkan `event_id`.

## 6. Zona waktu dan daylight saving

Timestamp Energy-Charts membawa offset lokal, misalnya `+01:00` atau `+02:00`.
Konversi ke UTC memakai offset tersebut, sehingga jam yang berulang saat
daylight saving berakhir tetap dapat dibedakan. Pengujian wajib mencakup
2026-03-29 dan 2026-10-25, dua tanggal pergantian waktu di Eropa.

## 7. Nilai kosong dan kualitas

- Bronze menyimpan nilai `null` apa adanya.
- Silver menandai baris dengan nilai kosong, duplikat, atau di luar rentang wajar.
- Baris bermasalah dipindahkan ke karantina dengan alasan yang tercatat.
- Gold hanya menerima data yang lolos pemeriksaan.

## 8. Retensi

Raw disimpan tanpa batas selama proyek berjalan agar bisa replay. Satu batch
disimpan sebagai satu direktori bernama checksum, sehingga ingest ulang tidak
menambah salinan. Kebijakan retensi untuk Gold dan serving akan ditetapkan saat
tahap penyimpanan analitik dibuat.