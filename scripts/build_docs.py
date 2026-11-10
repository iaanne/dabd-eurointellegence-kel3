from __future__ import annotations

import html
from pathlib import Path
from textwrap import dedent

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

INK = "#141414"
MUTED = "#6B7280"
ACCENT = "#145C4C"
ACCENT_SOFT = "#E6F0EC"
AMBER = "#B46A0A"
AMBER_SOFT = "#FBEFDD"
LINE = "#D6D6D0"
SOFT = "#F1F2EE"
WHITE = "#FFFFFF"

PERSON_COLORS = {
    "Ian": "#145C4C",
    "Nad": "#B46A0A",
    "Jim": "#2B5C8A",
    "El": "#6B4C8A",
}

BASE_CSS = f"""
@page {{
  size: A4;
  margin: 22mm 18mm 20mm 18mm;
  @top-left {{
    content: "EuroGrid Intelligence";
    font-family: "Liberation Sans", Arial, sans-serif;
    font-size: 7.5pt;
    color: {MUTED};
    letter-spacing: 0.04em;
  }}
  @top-right {{
    content: string(doctitle);
    font-family: "Liberation Sans", Arial, sans-serif;
    font-size: 7.5pt;
    color: {MUTED};
  }}
  @bottom-left {{
    content: "Kelompok 3 · TBP Advanced Data Platform";
    font-family: "Liberation Sans", Arial, sans-serif;
    font-size: 7.5pt;
    color: {MUTED};
  }}
  @bottom-right {{
    content: counter(page) " / " counter(pages);
    font-family: "Liberation Sans", Arial, sans-serif;
    font-size: 7.5pt;
    color: {MUTED};
  }}
}}

@page cover {{
  margin: 0;
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
  @bottom-left {{ content: none; }}
  @bottom-right {{ content: none; }}
}}

html {{ font-family: "Liberation Sans", Arial, sans-serif; color: {INK}; }}
body {{ margin: 0; font-size: 10.2pt; line-height: 1.55; }}

h1, h2, h3, h4 {{ font-family: "Liberation Sans", Arial, sans-serif; color: {INK}; }}
h2 {{
  font-size: 17pt;
  line-height: 1.2;
  margin: 26pt 0 8pt 0;
  padding-top: 10pt;
  border-top: 0.8pt solid {LINE};
  page-break-after: avoid;
  bookmark-level: 1;
}}
h2:first-of-type {{ border-top: none; padding-top: 0; margin-top: 0; }}
h3 {{
  font-size: 12pt;
  margin: 16pt 0 5pt 0;
  page-break-after: avoid;
  bookmark-level: 2;
}}
h4 {{ font-size: 10.5pt; margin: 12pt 0 4pt 0; page-break-after: avoid; }}
p {{ margin: 0 0 7pt 0; orphans: 3; widows: 3; }}
ul, ol {{ margin: 0 0 8pt 0; padding-left: 16pt; }}
li {{ margin-bottom: 3pt; }}
strong {{ font-weight: 700; }}
a {{ color: {ACCENT}; text-decoration: none; }}

table {{
  width: 100%;
  border-collapse: collapse;
  margin: 6pt 0 12pt 0;
  font-size: 8.6pt;
  line-height: 1.35;
}}
thead {{ display: table-header-group; }}
th {{
  background: {INK};
  color: {WHITE};
  text-align: left;
  font-weight: 700;
  padding: 5pt 6pt;
  border: 0.5pt solid {INK};
  vertical-align: top;
}}
td {{
  padding: 4.5pt 6pt;
  border: 0.5pt solid {LINE};
  vertical-align: top;
}}
tbody tr:nth-child(even) td {{ background: {SOFT}; }}
tr {{ page-break-inside: avoid; }}

code {{
  font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
  font-size: 8.4pt;
  background: {SOFT};
  padding: 0.5pt 3pt;
  border-radius: 2pt;
}}
pre {{
  background: #171717;
  color: #E8E8E3;
  padding: 10pt 12pt;
  border-radius: 4pt;
  font-size: 8.2pt;
  line-height: 1.45;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  page-break-inside: avoid;
  margin: 8pt 0 12pt 0;
}}
pre code {{ background: none; color: inherit; padding: 0; font-size: inherit; }}

blockquote {{
  margin: 8pt 0;
  padding: 6pt 12pt;
  border-left: 2pt solid {ACCENT};
  background: {ACCENT_SOFT};
  color: {INK};
}}

/* ---------- cover ---------- */
.cover {{
  page: cover;
  height: 297mm;
  box-sizing: border-box;
  padding: 30mm 24mm 22mm 24mm;
  position: relative;
}}
.cover .eyebrow {{
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: {MUTED};
}}
.cover h1 {{
  font-size: 44pt;
  line-height: 1.02;
  margin: 26mm 0 0 0;
  letter-spacing: -0.02em;
}}
.cover .subtitle {{
  font-size: 20pt;
  color: {MUTED};
  margin-top: 4mm;
  string-set: doctitle "Product Requirements Document";
}}
.cover .rule {{
  width: 62mm;
  height: 1.6mm;
  background: {ACCENT};
  margin: 12mm 0 12mm 0;
}}
.cover .meta {{
  width: 118mm;
  font-size: 9pt;
  margin: 0;
}}
.cover .meta td {{
  border: none;
  border-bottom: 0.5pt solid {LINE};
  padding: 4pt 0;
  background: none;
}}
.cover .meta td:first-child {{ color: {MUTED}; width: 34mm; }}
.cover .foot {{
  position: absolute;
  left: 24mm;
  right: 24mm;
  bottom: 20mm;
  font-size: 8.5pt;
  color: {MUTED};
  border-top: 0.6pt solid {LINE};
  padding-top: 4mm;
}}

/* ---------- toc ---------- */
.toc-page {{ page-break-before: always; page-break-after: always; }}
.toc-page .eyebrow {{
  font-size: 8.5pt;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: {MUTED};
}}
.toc-page h1 {{ font-size: 30pt; margin: 3mm 0 10mm 0; }}
.toc ul {{ list-style: none; padding: 0; margin: 0; }}
.toc li {{
  margin: 0;
  padding: 3.4pt 0;
  border-bottom: 0.5pt solid {LINE};
  font-size: 10pt;
}}
.toc a::after {{
  content: target-counter(attr(href), page);
  float: right;
  color: {MUTED};
  font-size: 9pt;
}}

/* ---------- team ---------- */
.team-cover {{ page: cover; height: 297mm; padding: 30mm 24mm 22mm 24mm; box-sizing: border-box; position: relative; }}
.team-cover .eyebrow {{ font-size: 9pt; font-weight: 700; letter-spacing: 0.12em; color: {MUTED}; }}
.team-cover h1 {{ font-size: 40pt; line-height: 1.05; margin: 24mm 0 0 0; }}
.team-cover .subtitle {{ font-size: 17pt; color: {MUTED}; margin-top: 4mm; string-set: doctitle "Pembagian Tim dan Rencana Kerja"; }}
.team-cover .names {{ margin-top: 16mm; display: flex; gap: 4mm; }}
.team-cover .name-chip {{
  border-top: 2.2mm solid;
  padding: 4mm 4mm 3mm 0;
  width: 38mm;
}}
.team-cover .name-chip .n {{ font-size: 15pt; font-weight: 700; }}
.team-cover .name-chip .r {{ font-size: 8.5pt; color: {MUTED}; }}
.team-cover .foot {{ position: absolute; left: 24mm; right: 24mm; bottom: 20mm; font-size: 8.5pt; color: {MUTED}; border-top: 0.6pt solid {LINE}; padding-top: 4mm; }}

.section {{ page-break-before: always; }}
.section .eyebrow {{ font-size: 8.5pt; font-weight: 700; letter-spacing: 0.1em; color: {MUTED}; }}
.section h2 {{ border-top: none; padding-top: 0; font-size: 26pt; margin: 2mm 0 6mm 0; }}
.section h3 {{ font-size: 12.5pt; margin-top: 6mm; }}

.person {{
  border: 0.6pt solid {LINE};
  border-left: 3.2mm solid;
  border-radius: 2mm;
  padding: 4mm 5.5mm;
  margin: 0 0 5mm 0;
  page-break-inside: avoid;
}}
.person .head {{ display: flex; align-items: flex-start; gap: 5mm; margin-bottom: 3mm; }}
.person .initials {{
  width: 13mm; height: 13mm;
  border-radius: 50%;
  color: {WHITE};
  font-weight: 700;
  font-size: 13pt;
  text-align: center;
  line-height: 13mm;
}}
.person .who .name {{ font-size: 19pt; font-weight: 700; line-height: 1.1; }}
.person .who .role {{ font-size: 10pt; color: {MUTED}; }}
.person .row {{ display: flex; gap: 7mm; }}
.person .col {{ flex: 1; }}
.person h4 {{ font-size: 8.5pt; letter-spacing: 0.08em; color: {MUTED}; margin: 2mm 0 1.5mm 0; }}
.person ul {{ margin: 0; padding-left: 12pt; font-size: 9.2pt; }}
.person li {{ margin-bottom: 2pt; }}
.person .req {{
  display: inline-block;
  font-size: 8pt;
  font-weight: 700;
  color: {WHITE};
  padding: 1pt 5pt;
  border-radius: 6pt;
  margin: 0 2pt 2pt 0;
}}

.raci td, .raci th {{ text-align: center; font-size: 8pt; padding: 3.2pt 3pt; }}
.raci td:first-child, .raci th:first-child {{ text-align: left; width: 12mm; }}
.raci td:nth-child(2), .raci th:nth-child(2) {{ text-align: left; }}
.raci .a {{ background: {ACCENT_SOFT} !important; font-weight: 700; color: {ACCENT}; }}

.legend {{ font-size: 8pt; color: {MUTED}; margin: -6pt 0 10pt 0; }}

.compact {{ font-size: 8.2pt; }}
.compact td, .compact th {{ padding: 3.2pt 4pt; }}

.callout {{
  background: {ACCENT_SOFT};
  border-left: 3pt solid {ACCENT};
  padding: 5mm 6mm;
  margin: 5mm 0 7mm 0;
  font-size: 10pt;
}}
.callout strong {{ color: {ACCENT}; }}

.two-col {{ display: flex; gap: 8mm; }}
.two-col > div {{ flex: 1; }}
"""


def md_to_html(source: str) -> tuple[str, str]:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "2-2", "title": ""}},
    )
    body = md.convert(source)
    return body, md.toc


def render_prd() -> Path:
    source = (DOCS / "PRD.md").read_text(encoding="utf-8")
    marker = "## 1. Ringkasan"
    head, body_md = source.split(marker, 1)
    body_md = marker + body_md
    body_html, toc_html = md_to_html(body_md)

    cover = dedent(
        f"""
        <section class="cover">
          <div class="eyebrow">TBP ADVANCED DATA PLATFORM · KELOMPOK 3</div>
          <h1>EuroGrid<br>Intelligence</h1>
          <div class="subtitle">Product Requirements Document</div>
          <div class="rule"></div>
          <table class="meta">
            <tr><td>Versi</td><td>1.0</td></tr>
            <tr><td>Tanggal</td><td>10 November 2026</td></tr>
            <tr><td>Status</td><td>Disetujui untuk pelaksanaan</td></tr>
            <tr><td>Ruang lingkup</td><td>Jerman dan zona DE-LU, lalu ekspansi</td></tr>
            <tr><td>Stack inti</td><td>Garage S3, Iceberg, Prefect, Redpanda, Trino</td></tr>
            <tr><td>Pemilik</td><td>Kelompok 3</td></tr>
          </table>
          <div class="foot">Dokumen ini menjadi acuan lingkup, kebutuhan, arsitektur, dan kriteria selesai.</div>
        </section>
        """
    )

    toc_page = dedent(
        f"""
        <section class="toc-page">
          <div class="eyebrow">DAFTAR ISI</div>
          <h1>Isi dokumen</h1>
          {toc_html}
        </section>
        """
    )

    document = f"""<!doctype html>
<html lang="id">
<head><meta charset="utf-8"><title>PRD EuroGrid Intelligence</title>
<style>{BASE_CSS}</style></head>
<body>
{cover}
{toc_page}
<section class="body">
{body_html}
</section>
</body></html>"""

    out = DOCS / "PRD.pdf"
    HTML(string=document, base_url=str(ROOT)).write_pdf(out)
    return out


PEOPLE = [
    {
        "name": "Ian",
        "initials": "IA",
        "role": "Platform dan Storage",
        "summary": "Menjaga fondasi tempat semua data disimpan dan semua job dijalankan. Fokus pada Garage S3, Iceberg, Prefect, container, dan pemulihan.",
        "reqs": ["F-01", "F-02", "F-07", "F-17"],
        "focus": [
            "Menyiapkan Garage S3, bucket, kredensial terbatas, dan layout cluster.",
            "Mengelola katalog Iceberg, tabel Bronze, Silver, dan Gold.",
            "Menyusun Prefect deployment, jadwal harian, retry, dan backfill.",
            "Menulis compose Podman, health check, volume, dan batas memori.",
            "Menguji backup dan restore untuk Garage, Postgres, dan katalog.",
        ],
        "deliverables": [
            ("M1", "Garage S3 aktif, bucket dibuat, Iceberg menulis dan membaca tabel"),
            ("M2", "Tabel Silver tersedia, katalog stabil, backup harian berjalan"),
            ("M3", "Trino membaca Gold, konfigurasi katalog terdokumentasi"),
            ("M4", "Profil compose untuk stream, batas resource terukur"),
            ("M5", "Stack demo berjalan dengan profil hemat resource"),
            ("M6", "Restore terbukti, RTO dan RPO terukur"),
        ],
        "done": "Clone bersih dapat di-deploy ulang, data bertahan setelah restart, dan backup dapat dipulihkan.",
    },
    {
        "name": "Nad",
        "initials": "ND",
        "role": "Kualitas Data dan Governance",
        "summary": "Menentukan apakah data layak dipakai. Fokus pada quality gate, karantina, lineage, katalog, metrik, alert, dan bukti pengujian.",
        "reqs": ["F-08", "F-09", "F-14", "F-15", "F-18"],
        "focus": [
            "Menulis aturan kualitas untuk not-null, tipe, rentang, keunikan, dan konsistensi.",
            "Membangun tabel karantina dan laporan mutu per run.",
            "Menyambungkan OpenLineage dari Prefect ke Marquez.",
            "Menjaga katalog YAML berisi pemilik, retensi, dan jadwal refresh.",
            "Menyiapkan metrik, log terstruktur, dan tiga alert yang diuji.",
        ],
        "deliverables": [
            ("M1", "Rencana uji dan kontrak kualitas disetujui"),
            ("M2", "Silver quality gate aktif, karantina dan laporan mutu tersedia"),
            ("M3", "Lineage Bronze ke Gold lengkap, katalog terisi"),
            ("M4", "Pemeriksaan kualitas stream dan DLQ terdefinisi"),
            ("M5", "Metrik dan log terstruktur masuk Grafana"),
            ("M6", "Tiga alert teruji, matriks bukti F-18 lengkap"),
        ],
        "done": "Setiap data invalid terlacak, laporan mutu tersedia, dan satu jalur lineage dapat ditunjukkan.",
    },
    {
        "name": "Jim",
        "initials": "JM",
        "role": "Analitik dan Machine Learning",
        "summary": "Mengubah data bersih menjadi jawaban. Fokus pada Gold, query analitik, fitur, model peramalan beban, MLflow, dan tabel prediksi.",
        "reqs": ["F-03", "F-10 SQL", "F-11", "F-12"],
        "focus": [
            "Merancang grain dan business key tiga mart Gold.",
            "Menulis sepuluh query analitik yang dipakai dashboard dan API.",
            "Membangun fitur cuaca, kalender, dan lag beban.",
            "Melatih model baseline dengan split waktu dan seed tetap.",
            "Mencatat eksperimen di MLflow dan menulis tabel prediksi.",
        ],
        "deliverables": [
            ("M1", "Skema Gold dan daftar query disetujui"),
            ("M2", "Kebutuhan input Silver untuk fitur terdokumentasi"),
            ("M3", "Tiga mart Gold dan sepuluh query selesai"),
            ("M4", "Fitur dari data stream dan batch tergabung"),
            ("M5", "Model terdaftar, inference berjalan, tabel prediksi terisi"),
            ("M6", "Evaluasi model dan benchmark query dilaporkan"),
        ],
        "done": "Dua eksperimen dapat dibandingkan, prediksi dapat dilacak ke input dan versi model, dan query konsisten dengan dashboard.",
    },
    {
        "name": "El",
        "initials": "EL",
        "role": "Serving, Stream, dan Keamanan",
        "summary": "Membuat data bisa dipakai dan dijaga. Fokus pada stream Redpanda, API FastAPI, dashboard Metabase, autentikasi, dan audit.",
        "reqs": ["F-04", "F-05", "F-10 API", "F-13", "F-16"],
        "focus": [
            "Menyiapkan topik Redpanda, producer, consumer, watermark, dan DLQ.",
            "Membangun endpoint FastAPI dengan OpenAPI dan validasi input.",
            "Menyusun dashboard dengan empat metrik dan dua filter.",
            "Menerapkan JWT, peran admin, operator, viewer, dan rate limit.",
            "Menguji status 401 dan 403 serta mencatat audit log.",
        ],
        "deliverables": [
            ("M1", "Kontrak serving dan uji awal Redpanda"),
            ("M2", "Kerangka API dan skema respons"),
            ("M3", "Endpoint membaca Gold lewat Trino"),
            ("M4", "Producer dan consumer berjalan, lag dan DLQ terlihat"),
            ("M5", "Dashboard empat metrik, autentikasi aktif"),
            ("M6", "Uji keamanan dan audit selesai, video demo disiapkan"),
        ],
        "done": "Consumer berjalan tanpa trigger manual, tiga endpoint lulus uji, dashboard konsisten dengan SQL, dan viewer tidak dapat melakukan tindakan admin.",
    },
]

RACI = [
    ("F-01", "Deployment dan isolasi service", "A/R", "C", "I", "C"),
    ("F-02", "Batch dan penjadwalan", "A/R", "I", "C", "I"),
    ("F-03", "Incremental, retry, backfill", "C", "C", "A/R", "I"),
    ("F-04", "Stream processing", "C", "I", "I", "A/R"),
    ("F-05", "Event-time dan deduplikasi", "I", "C", "I", "A/R"),
    ("F-06", "Medallion architecture", "A/R", "R", "C", "I"),
    ("F-07", "Penyimpanan analitik", "A/R", "I", "C", "I"),
    ("F-08", "Quality gate", "C", "A/R", "C", "I"),
    ("F-09", "Metadata dan lineage", "C", "A/R", "I", "I"),
    ("F-10", "Serving SQL dan API", "C", "I", "A/R", "R"),
    ("F-11", "Dataset dan versioning ML", "I", "C", "A/R", "I"),
    ("F-12", "Integrasi inference", "I", "I", "A/R", "C"),
    ("F-13", "Dashboard analitik", "I", "C", "C", "A/R"),
    ("F-14", "Metrik dan log", "C", "A/R", "I", "C"),
    ("F-15", "Tiga alert", "C", "A/R", "I", "C"),
    ("F-16", "Keamanan dan audit", "C", "C", "I", "A/R"),
    ("F-17", "Recovery dan backup", "A/R", "C", "I", "I"),
    ("F-18", "Tes dan reproducibility", "C", "A/R", "C", "C"),
]

MILESTONES = [
    ("M0", "Selesai", "Bronze lokal, 3 batch, 15.456 baris, 15 tes", "Tim", "Semua"),
    ("M1", "Minggu 1", "Garage S3, Iceberg, Prefect, backfill 30 hari", "Ian", "Nad, Jim, El"),
    ("M2", "Minggu 2", "Silver, quality gate, karantina, lineage", "Nad", "Ian, Jim"),
    ("M3", "Minggu 3", "Gold 3 mart, 10 query, Trino", "Jim", "Ian, El"),
    ("M4", "Minggu 4", "Redpanda, producer, consumer, DLQ", "El", "Ian, Nad"),
    ("M5", "Minggu 5", "ML, MLflow, inference, API, dashboard", "Jim dan El", "Ian, Nad"),
    ("M6", "Minggu 6", "Observability, 3 alert, keamanan, backup", "Nad dan Ian", "Jim, El"),
    ("M7", "Minggu 7", "Dokumentasi, video, matriks F-01 sampai F-18", "Tim", "Semua"),
]

WEEKLY = [
    ("M1", "Garage, Iceberg, Prefect, compose", "Rencana uji dan kontrak mutu", "Skema Gold dan query", "Kontrak serving, uji Redpanda"),
    ("M2", "Dukungan Iceberg, backup awal", "Silver dan quality gate", "Input fitur Silver", "Kerangka API"),
    ("M3", "Trino dan katalog", "Lineage dan katalog", "Gold mart dan 10 query", "Endpoint baca Gold"),
    ("M4", "Tuning resource", "Mutu data stream", "Fitur gabungan", "Producer, consumer, DLQ"),
    ("M5", "Hardening deploy", "Metrik dan log", "Model, MLflow, inference", "Dashboard dan auth"),
    ("M6", "Backup dan restore", "Tiga alert dan Grafana", "Evaluasi dan benchmark", "Uji keamanan dan audit"),
    ("M7", "Dokumen deploy", "Matriks bukti dan tes", "Laporan eksperimen", "Video dan walkthrough"),
]


def person_card(person: dict) -> str:
    color = PERSON_COLORS[person["name"]]
    reqs = "".join(
        f'<span class="req" style="background:{color}">{html.escape(r)}</span>'
        for r in person["reqs"]
    )
    focus = "".join(f"<li>{html.escape(item)}</li>" for item in person["focus"])
    rows = "".join(
        f"<tr><td><strong>{m}</strong></td><td>{html.escape(task)}</td></tr>"
        for m, task in person["deliverables"]
    )
    return f"""
    <div class="person" style="border-left-color:{color}">
      <div class="head">
        <div class="initials" style="background:{color}">{person['initials']}</div>
        <div class="who">
          <div class="name">{person['name']}</div>
          <div class="role">{person['role']}</div>
        </div>
      </div>
      <p style="font-size:9.4pt;margin-bottom:3mm">{html.escape(person['summary'])}</p>
      <div style="margin-bottom:2mm">{reqs}</div>
      <div class="row">
        <div class="col">
          <h4>FOKUS KERJA</h4>
          <ul>{focus}</ul>
        </div>
        <div class="col">
          <h4>DELIVERABLE PER MILESTONE</h4>
          <table class="compact" style="margin:0">
            <tbody>{rows}</tbody>
          </table>
        </div>
      </div>
      <h4 style="margin-top:3mm">DEFINISI SELESAI</h4>
      <p style="font-size:9.2pt;margin:0">{html.escape(person['done'])}</p>
    </div>
    """


def render_team() -> Path:
    chips = "".join(
        f'<div class="name-chip" style="border-top-color:{PERSON_COLORS[p["name"]]}">'
        f'<div class="n">{p["name"]}</div><div class="r">{html.escape(p["role"])}</div></div>'
        for p in PEOPLE
    )

    cards = "".join(person_card(p) for p in PEOPLE)

    raci_rows = ""
    for fid, title, ian, nad, jim, el in RACI:
        cells = []
        for value in (ian, nad, jim, el):
            cls = ' class="a"' if "A" in value else ""
            cells.append(f"<td{cls}>{value}</td>")
        raci_rows += (
            f"<tr><td><strong>{fid}</strong></td><td>{html.escape(title)}</td>"
            + "".join(cells)
            + "</tr>"
        )

    milestone_rows = "".join(
        f"<tr><td><strong>{m}</strong></td><td>{week}</td><td>{html.escape(desc)}</td>"
        f"<td>{html.escape(lead)}</td><td>{html.escape(support)}</td></tr>"
        for m, week, desc, lead, support in MILESTONES
    )

    weekly_rows = "".join(
        f"<tr><td><strong>{m}</strong></td><td>{html.escape(ian)}</td>"
        f"<td>{html.escape(nad)}</td><td>{html.escape(jim)}</td><td>{html.escape(el)}</td></tr>"
        for m, ian, nad, jim, el in WEEKLY
    )

    document = f"""<!doctype html>
<html lang="id">
<head><meta charset="utf-8"><title>Pembagian Tim EuroGrid Intelligence</title>
<style>{BASE_CSS}
.team-cover h1 {{ bookmark-level: none; }}
</style></head>
<body>

<section class="team-cover">
  <div class="eyebrow">TBP ADVANCED DATA PLATFORM · KELOMPOK 3</div>
  <h1>Pembagian Tim<br>dan Rencana Kerja</h1>
  <div class="subtitle">EuroGrid Intelligence</div>
  <div class="names">{chips}</div>
  <div class="foot">Empat peran, delapan milestone, satu jalur data dari sumber sampai serving. Versi 1.0, 10 November 2026.</div>
</section>

<section class="section">
  <div class="eyebrow">CARA KERJA</div>
  <h2>Satu tim, empat jalur yang saling mengunci</h2>
  <p>Pembagian ini dibuat agar setiap requirement F-01 sampai F-18 punya pemilik yang jelas, tanpa membuat silo. Setiap orang memimpin satu bidang, tetapi deliverable tetap diuji bersama.</p>

  <div class="callout">
    <strong>Aturan utama.</strong> Tidak ada pekerjaan yang dianggap selesai hanya karena kodenya jalan. Setiap deliverable harus punya tes, dokumentasi singkat, dan bukti yang dapat ditunjukkan saat demo.
  </div>

  <h3>Ritme mingguan</h3>
  <table>
    <thead><tr><th>Waktu</th><th>Kegiatan</th><th>Keluaran</th></tr></thead>
    <tbody>
      <tr><td>Senin 20.00</td><td>Perencanaan sprint 30 menit</td><td>Target minggu, pemilik task, risiko baru</td></tr>
      <tr><td>Rabu 20.00</td><td>Check-in 15 menit</td><td>Blocker dan keputusan yang perlu diambil</td></tr>
      <tr><td>Sabtu 10.00</td><td>Demo internal dan review pull request</td><td>Bukti jalan, catatan perbaikan, merge</td></tr>
      <tr><td>Setiap hari</td><td>Update singkat di kanal tim</td><td>Apa yang selesai, apa berikutnya, apa yang menghambat</td></tr>
    </tbody>
  </table>

  <h3>Aturan kolaborasi</h3>
  <ul>
    <li>Satu branch per task, satu pull request per perubahan logis, minimal satu reviewer.</li>
    <li>Branch utama tidak menerima commit langsung. Semua lewat pull request.</li>
    <li>Perubahan kontrak data harus disetujui pemilik lapisan yang terdampak.</li>
    <li>Secret hanya di <code>.env</code>. Berkas contoh memakai nilai palsu.</li>
    <li>Setiap keputusan teknis besar dicatat sebagai ADR di <code>docs/architecture.md</code>.</li>
    <li>Jika dua orang menyentuh berkas yang sama, pemilik requirement menjadi penentu akhir.</li>
  </ul>

  <h3>Definisi selesai untuk setiap task</h3>
  <table>
    <thead><tr><th>Aspek</th><th>Bukti minimum</th></tr></thead>
    <tbody>
      <tr><td>Kode</td><td>Berjalan lokal, tidak ada secret, mengikuti gaya repositori</td></tr>
      <tr><td>Tes</td><td>Tes baru atau tes yang diperbarui, lulus dengan <code>make test</code></td></tr>
      <tr><td>Dokumentasi</td><td>Bagian README atau dokumen teknis yang menjelaskan cara pakai</td></tr>
      <tr><td>Bukti</td><td>Log, tangkapan layar, checksum, atau berkas di <code>docs/evidence/</code></td></tr>
      <tr><td>Demo</td><td>Dapat ditunjukkan dalam waktu kurang dari lima menit</td></tr>
    </tbody>
  </table>
</section>

<section class="section">
  <div class="eyebrow">PERAN</div>
  <h2>Empat pemilik bidang</h2>
  <p>Setiap kartu memuat ringkasan peran, requirement yang dipimpin, fokus kerja, dan deliverable per milestone.</p>
  {cards}
</section>

<section class="section">
  <div class="eyebrow">MATRIKS</div>
  <h2>RACI requirement</h2>
  <p>R berarti responsible, pihak yang mengerjakan. A berarti accountable, pihak yang menanggung hasil akhir. C berarti consulted, dimintai masukan. I berarti informed, cukup diberi kabar.</p>
  <p class="legend">Sel yang diberi latar hijau memuat huruf A, yaitu penanggung jawab akhir.</p>
  <table class="raci">
    <thead><tr><th>ID</th><th>Requirement</th><th>Ian</th><th>Nad</th><th>Jim</th><th>El</th></tr></thead>
    <tbody>{raci_rows}</tbody>
  </table>
</section>

<section class="section">
  <div class="eyebrow">JADWAL</div>
  <h2>Milestone dan kepemilikan</h2>
  <p>M0 sudah selesai. M1 sampai M7 adalah rencana kerja. Tanggal menyesuaikan deadline kelas, sedangkan urutan tidak berubah karena setiap milestone bergantung pada milestone sebelumnya.</p>
  <table>
    <thead><tr><th>ID</th><th>Minggu</th><th>Isi</th><th>Lead</th><th>Pendukung</th></tr></thead>
    <tbody>{milestone_rows}</tbody>
  </table>

  <h3>Fokus per orang per minggu</h3>
  <table class="compact">
    <thead><tr><th>Minggu</th><th>Ian</th><th>Nad</th><th>Jim</th><th>El</th></tr></thead>
    <tbody>{weekly_rows}</tbody>
  </table>
</section>

<section class="section">
  <div class="eyebrow">SERAH TERIMA</div>
  <h2>Kontrak antaranggota</h2>
  <p>Setiap orang menerima dan menyerahkan artefak yang jelas. Ini mencegah pekerjaan berhenti karena menunggu informasi yang tidak terdokumentasi.</p>

  <table>
    <thead><tr><th>Dari</th><th>Yang diserahkan</th><th>Kepada</th></tr></thead>
    <tbody>
      <tr><td><strong>Ian</strong></td><td>Endpoint Garage, nama bucket, URI katalog Iceberg, nama deployment Prefect, profil compose</td><td>Nad, Jim, El</td></tr>
      <tr><td><strong>Nad</strong></td><td>Skema laporan mutu, tabel karantina, nama event lineage, aturan alert</td><td>Ian, Jim, El</td></tr>
      <tr><td><strong>Jim</strong></td><td>DDL tabel Gold, daftar query, versi model, skema tabel prediksi</td><td>Ian, Nad, El</td></tr>
      <tr><td><strong>El</strong></td><td>Spesifikasi OpenAPI, peran akses, URL dashboard, nama topik stream</td><td>Ian, Nad, Jim</td></tr>
    </tbody>
  </table>

  <h3>Titik keputusan bersama</h3>
  <table>
    <thead><tr><th>Keputusan</th><th>Kapan</th><th>Diputuskan oleh</th></tr></thead>
    <tbody>
      <tr><td>Katalog Iceberg REST atau Nessie</td><td>Sebelum M1</td><td>Ian, dengan masukan Nad</td></tr>
      <tr><td>Redpanda atau Kafka KRaft</td><td>Sebelum M4</td><td>El, dengan masukan Ian</td></tr>
      <tr><td>Marquez atau OpenMetadata</td><td>Sebelum M2</td><td>Nad, dengan masukan Ian</td></tr>
      <tr><td>Ambang quality gate</td><td>Sebelum M2</td><td>Nad dan Jim</td></tr>
      <tr><td>Metrik dashboard</td><td>Sebelum M5</td><td>El dan Jim</td></tr>
      <tr><td>Batas resource final</td><td>Setelah M1</td><td>Ian, dengan masukan semua</td></tr>
    </tbody>
  </table>
</section>

<section class="section">
  <div class="eyebrow">RISIKO</div>
  <h2>Pemilik risiko dan jalur eskalasi</h2>
  <table>
    <thead><tr><th>Risiko</th><th>Pemilik</th><th>Tindakan awal</th></tr></thead>
    <tbody>
      <tr><td>Token ENTSO-E belum aktif</td><td>El</td><td>Pakai seri load Energy-Charts, siapkan adapter di belakang antarmuka yang sama</td></tr>
      <tr><td>Garage tidak kompatibel dengan Iceberg</td><td>Ian</td><td>Uji multipart dan listing pada hari pertama M1, siapkan MinIO sebagai cadangan</td></tr>
      <tr><td>Resource satu mesin tidak cukup</td><td>Ian</td><td>Batasi memori per service, jalankan profil bertahap, ukur pada M1</td></tr>
      <tr><td>Kualitas data sumber buruk</td><td>Nad</td><td>Karantina, laporan mutu, dan ambang blokir publish</td></tr>
      <tr><td>Model tidak lebih baik dari baseline</td><td>Jim</td><td>Sederhanakan fitur, evaluasi ulang split, laporkan apa adanya</td></tr>
      <tr><td>Waktu pengerjaan mepet</td><td>Semua</td><td>Prioritaskan F-01 sampai F-18, tunda fitur opsional</td></tr>
    </tbody>
  </table>

  <h3>Checklist pribadi menjelang demo</h3>
  <table>
    <thead><tr><th>Anggota</th><th>Yang harus bisa ditunjukkan</th></tr></thead>
    <tbody>
      <tr><td><strong>Ian</strong></td><td>Deploy dari clone bersih, health check, snapshot Iceberg, restore backup</td></tr>
      <tr><td><strong>Nad</strong></td><td>Laporan mutu, contoh karantina, lineage Bronze ke Gold, tiga alert</td></tr>
      <tr><td><strong>Jim</strong></td><td>Tiga mart, sepuluh query, dua eksperimen MLflow, tabel prediksi</td></tr>
      <tr><td><strong>El</strong></td><td>Consumer berjalan, tiga endpoint, dashboard empat metrik, uji 401 dan 403</td></tr>
    </tbody>
  </table>

  <div class="callout">
    <strong>Ukuran keberhasilan tim.</strong> Bukan banyaknya komponen yang menyala, tetapi satu alur yang dapat dijelaskan dari sumber sampai keputusan, dengan bukti di setiap perpindahan.
  </div>
</section>

</body></html>"""

    out = DOCS / "TEAM.pdf"
    HTML(string=document, base_url=str(ROOT)).write_pdf(out)
    return out


if __name__ == "__main__":
    prd = render_prd()
    team = render_team()
    print(prd)
    print(team)
