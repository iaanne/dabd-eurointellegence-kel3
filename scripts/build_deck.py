from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# ---------------------------------------------------------------- design tokens
FONT = "Arial"
MONO = "Courier New"
BG = RGBColor(0xFA, 0xFA, 0xF8)
INK = RGBColor(0x14, 0x14, 0x14)
MUTED = RGBColor(0x6B, 0x72, 0x80)
LINE = RGBColor(0xD6, 0xD6, 0xD0)
ACCENT = RGBColor(0x14, 0x5C, 0x4C)
ACCENT_SOFT = RGBColor(0xE6, 0xF0, 0xEC)
AMBER = RGBColor(0xB4, 0x6A, 0x0A)
AMBER_SOFT = RGBColor(0xFB, 0xEF, 0xDD)
GRAY_SOFT = RGBColor(0xEE, 0xEE, 0xEA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SW = Inches(13.333)
SH = Inches(7.5)


# ---------------------------------------------------------------- primitives
def new_slide(prs: Presentation):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = BG
    return slide


def add_text(
    slide,
    x,
    y,
    w,
    h,
    text="",
    size=18,
    bold=False,
    color=INK,
    align=PP_ALIGN.LEFT,
    font=FONT,
    anchor=MSO_ANCHOR.TOP,
    line_spacing=1.1,
):
    box = slide.shapes.add_textbox(x, y, w, h)
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    paragraph.line_spacing = line_spacing
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_eyebrow(slide, text: str):
    add_text(slide, Inches(0.75), Inches(0.42), Inches(11.8), Inches(0.28), text, 10.5, True, MUTED)


def add_title(slide, text: str, size=38):
    add_text(slide, Inches(0.75), Inches(0.72), Inches(11.8), Inches(0.75), text, size, True, INK)


def add_footer(slide, number: int):
    add_text(
        slide,
        Inches(0.75),
        Inches(7.08),
        Inches(6.0),
        Inches(0.22),
        "Kelompok 3  ·  EuroGrid Intelligence",
        9,
        False,
        MUTED,
    )
    add_text(
        slide,
        Inches(11.6),
        Inches(7.08),
        Inches(0.95),
        Inches(0.22),
        f"{number:02d}",
        9,
        True,
        MUTED,
        PP_ALIGN.RIGHT,
    )


def add_rule(slide, y, x=Inches(0.75), w=Inches(11.8), color=LINE):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.012))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def add_list(slide, x, y, w, h, items, size=17, color=INK, gap=10, bullet="•", line_spacing=1.14):
    box = slide.shapes.add_textbox(x, y, w, h)
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(gap)
        paragraph.line_spacing = line_spacing
        if isinstance(item, tuple):
            lead, rest = item
            bullet_run = paragraph.add_run()
            bullet_run.text = f"{bullet}  " if bullet else ""
            bullet_run.font.name = FONT
            bullet_run.font.size = Pt(size)
            bullet_run.font.color.rgb = color
            lead_run = paragraph.add_run()
            lead_run.text = lead
            lead_run.font.name = FONT
            lead_run.font.size = Pt(size)
            lead_run.font.bold = True
            lead_run.font.color.rgb = color
            rest_run = paragraph.add_run()
            rest_run.text = f"  {rest}" if rest else ""
            rest_run.font.name = FONT
            rest_run.font.size = Pt(size)
            rest_run.font.color.rgb = color
        else:
            run = paragraph.add_run()
            run.text = f"{bullet}  {item}" if bullet else item
            run.font.name = FONT
            run.font.size = Pt(size)
            run.font.color.rgb = color
    return box


def add_card(slide, x, y, w, h, fill=WHITE, line=None, radius=0.06):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shape.adjustments[0] = radius
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    shape.text_frame.word_wrap = True
    return shape


def add_box(
    slide,
    x,
    y,
    w,
    h,
    title,
    subtitle=None,
    fill=WHITE,
    line=LINE,
    title_size=12,
    subtitle_size=9.5,
    title_color=INK,
    align=PP_ALIGN.CENTER,
):
    shape = add_card(slide, x, y, w, h, fill=fill, line=line)
    frame = shape.text_frame
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.08)
    frame.margin_top = Inches(0.05)
    frame.margin_bottom = Inches(0.05)
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = title
    run.font.name = FONT
    run.font.size = Pt(title_size)
    run.font.bold = True
    run.font.color.rgb = title_color
    if subtitle:
        second = frame.add_paragraph()
        second.alignment = align
        second.space_before = Pt(3)
        sub_run = second.add_run()
        sub_run.text = subtitle
        sub_run.font.name = FONT
        sub_run.font.size = Pt(subtitle_size)
        sub_run.font.color.rgb = MUTED
    return shape


def add_arrow(slide, x, y, w=Inches(0.45), h=Inches(0.3), color=LINE):
    shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def add_table(slide, x, y, w, col_widths, data, font_size=12, row_height=0.55, header=True):
    rows = len(data)
    columns = len(data[0])
    shape = slide.shapes.add_table(
        rows, columns, x, y, w, Inches(row_height * rows)
    )
    table = shape.table
    table.first_row = header
    table.horz_banding = False
    for index, width in enumerate(col_widths):
        table.columns[index].width = Inches(width)
    for r, row in enumerate(data):
        table.rows[r].height = Inches(row_height)
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.1)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            is_header = header and r == 0
            cell.fill.fore_color.rgb = INK if is_header else (WHITE if r % 2 == 1 else GRAY_SOFT)
            frame = cell.text_frame
            frame.word_wrap = True
            paragraph = frame.paragraphs[0]
            paragraph.text = ""
            run = paragraph.add_run()
            run.text = str(value)
            run.font.name = FONT
            run.font.size = Pt(font_size)
            run.font.bold = is_header
            run.font.color.rgb = WHITE if is_header else INK
    return shape


def add_notes(slide, text: str):
    slide.notes_slide.notes_text_frame.text = text


def add_code_card(slide, x, y, w, h, lines, font_size=12):
    card = add_card(slide, x, y, w, h, fill=RGBColor(0x17, 0x17, 0x17), line=None, radius=0.04)
    frame = card.text_frame
    frame.margin_left = Inches(0.22)
    frame.margin_right = Inches(0.18)
    frame.margin_top = Inches(0.18)
    frame.margin_bottom = Inches(0.12)
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.space_after = Pt(2)
        run = paragraph.add_run()
        run.text = line
        run.font.name = MONO
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xE8, 0xE8, 0xE3)


# ---------------------------------------------------------------- slides
def slide_title(prs):
    slide = new_slide(prs)
    add_text(slide, Inches(0.75), Inches(0.55), Inches(11.8), Inches(0.3),
             "TBP ADVANCED DATA PLATFORM  ·  KELOMPOK 3", 11, True, MUTED)
    add_text(slide, Inches(0.75), Inches(1.65), Inches(11.8), Inches(1.0),
             "EuroGrid Intelligence", 60, True, INK)
    add_text(slide, Inches(0.75), Inches(2.8), Inches(9.6), Inches(1.1),
             "Platform data kelistrikan Eropa: dari sumber terbuka ke lakehouse, API, dan peramalan.",
             21, False, MUTED, line_spacing=1.2)
    add_rule(slide, Inches(4.15), Inches(0.75), Inches(4.0), ACCENT)
    add_text(slide, Inches(0.75), Inches(4.4), Inches(6.0), Inches(0.4),
             "Progress Report  ·  9 November 2026", 14, True, INK)
    add_text(slide, Inches(0.75), Inches(4.85), Inches(7.2), Inches(0.4),
             "End-to-End European Electricity Data Lakehouse & Market Intelligence Platform",
             11, False, MUTED)
    add_text(slide, Inches(10.0), Inches(6.55), Inches(2.55), Inches(0.4),
             "sumber → Bronze", 11, True, ACCENT, PP_ALIGN.RIGHT)
    add_notes(
        slide,
        "Deck ini melanjutkan deck perkenalan. Fokusnya bukan lagi rencana, "
        "tetapi apa yang sudah berjalan, kendala yang ditemukan, dan langkah berikutnya.",
    )


def slide_agenda(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "AGENDA")
    add_title(slide, "Isi presentasi")
    items = [
        ("01", "Masalah dan tujuan"),
        ("02", "Sumber dan kontrak data"),
        ("03", "Arsitektur target dan status"),
        ("04", "Progress minggu ini"),
        ("05", "Kendala dan rencana"),
    ]
    y = Inches(1.85)
    for index, (num, label) in enumerate(items):
        add_text(slide, Inches(0.75), y, Inches(0.8), Inches(0.5), num, 16, True, ACCENT)
        add_text(slide, Inches(1.6), y - Inches(0.04), Inches(9.0), Inches(0.55), label, 24, True, INK)
        if index < len(items) - 1:
            add_rule(slide, y + Inches(0.62), Inches(0.75), Inches(11.8))
        y += Inches(0.95)
    add_footer(slide, number)
    add_notes(slide, "Lima bagian singkat. Bagian empat adalah inti progress minggu ini.")


def slide_problem(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "LATAR BELAKANG")
    add_title(slide, "Masalah yang diselesaikan")
    add_list(
        slide,
        Inches(0.75),
        Inches(1.75),
        Inches(7.1),
        Inches(4.4),
        [
            "Data kelistrikan Eropa terbuka, tetapi tersebar di banyak penyedia.",
            "Format, satuan, dan zona waktu tidak seragam.",
            "Sebagian nilai diterbitkan ulang sebagai revisi.",
            "Istilah mirip berbeda arti: load dan consumption, exchange dan physical flow.",
            "Akibatnya, dua orang bisa menjawab pertanyaan yang sama dengan angka berbeda.",
        ],
        17,
        gap=16,
    )
    add_card(slide, Inches(8.2), Inches(1.75), Inches(4.35), Inches(3.9), ACCENT_SOFT)
    add_text(slide, Inches(8.55), Inches(2.1), Inches(3.7), Inches(1.6),
             "Data terbuka, tetapi belum siap dipakai.", 25, True, ACCENT, line_spacing=1.15)
    add_text(slide, Inches(8.55), Inches(3.85), Inches(3.6), Inches(1.5),
             "Yang sulit bukan mendapatkannya, melainkan menyatukan dan membuatnya bisa diulang.",
             13, False, INK, line_spacing=1.25)
    add_footer(slide, number)
    add_notes(
        slide,
        "Empat sumber masalah: penyebaran penyedia, format tidak seragam, revisi, "
        "dan definisi istilah. Ini yang membuat angka antarnegara sulit dibandingkan.",
    )


def slide_goals(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "TUJUAN")
    add_title(slide, "Tujuan dan indikator keberhasilan")
    data = [
        ["Indikator", "Target"],
        ["Integrasi sumber", "Minimal 2 penyedia listrik dan 1 penyedia cuaca, dengan provenance"],
        ["Batch dan inkremental", "Backfill dan revisi tercatat tanpa duplikasi"],
        ["Lakehouse", "Tabel Iceberg di Bronze, Silver, Gold dapat di-query"],
        ["Data product", "Minimal 3 produk dengan skema, mutu, akses, dan pemilik"],
        ["BI dan ML", "Dashboard interaktif dan satu model peramalan dengan evaluasi waktu"],
    ]
    add_table(slide, Inches(0.75), Inches(1.7), Inches(11.8), [3.1, 8.7], data, 14, 0.68)
    add_text(slide, Inches(0.75), Inches(6.15), Inches(11.8), Inches(0.4),
             "Indikator ini yang nanti dipetakan ke requirement F-01 sampai F-18 pada spek.",
             12, False, MUTED)
    add_footer(slide, number)
    add_notes(slide, "Lima indikator ini menjadi kompas. Yang sudah tercapai minggu ini baru bagian sumber dan kontrak data.")


def slide_sources(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "SUMBER DATA")
    add_title(slide, "Sumber data dan lisensi")
    data = [
        ["Sumber", "Data", "Akses", "Status lisensi"],
        ["Energy-Charts\nFraunhofer ISE", "Pembangkitan, beban, harga, aliran lintas negara",
         "REST JSON", "CC BY 4.0 untuk data yang dipakai"],
        ["Open-Meteo", "Suhu, angin, radiasi, presipitasi", "REST JSON",
         "CC BY 4.0 non-komersial, ada batas panggilan"],
        ["ENTSO-E\nTransparency", "Beban dan aliran otoritatif", "REST XML, token", "Menunggu akses"],
    ]
    add_table(slide, Inches(0.75), Inches(1.7), Inches(11.8), [2.9, 4.1, 2.0, 2.8], data, 12, 0.92)
    add_text(slide, Inches(0.75), Inches(6.0), Inches(11.8), Inches(0.6),
             "Harga DE-LU berlisensi CC BY 4.0. Zona lain dibatasi untuk pemakaian privat, "
             "jadi tidak dipakai untuk artefak publik.", 12, False, MUTED)
    add_footer(slide, number)
    add_notes(
        slide,
        "Dua penyedia sudah jalan dan lisensinya jelas. ENTSO-E masih menunggu token, "
        "jadi untuk sementara beban diambil dari seri load Energy-Charts.",
    )


def slide_contract(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "KONTRAK DATA")
    add_title(slide, "Yang sudah dibekukan")
    add_list(
        slide,
        Inches(0.75),
        Inches(1.8),
        Inches(11.6),
        Inches(4.8),
        [
            ("Lingkup.", "Jerman dan zona DE-LU lebih dulu. Negara lain menyusul setelah alur ini terbukti."),
            ("Grain.", "15 menit untuk data listrik, 1 jam untuk cuaca."),
            ("Waktu.", "Timestamp lokal dengan offset disimpan sebagai UTC. Waktu lokal tetap disimpan untuk audit."),
            ("Kunci bisnis.", "Dataset, zona, series_id, dan timestamp_utc."),
            ("Metadata.", "Timezone, resolution, unit, license, available_from, available_until."),
        ],
        18,
        gap=20,
    )
    add_text(slide, Inches(0.75), Inches(6.35), Inches(11.6), Inches(0.4),
             "Kontrak lengkap: docs/data-contract.md", 11, False, MUTED)
    add_footer(slide, number)
    add_notes(
        slide,
        "Kontrak data ditulis sebelum Silver dibuat. Perubahan di sini mahal, "
        "jadi kunci bisnis dan definisi waktu dikunci lebih dulu.",
    )


def slide_stream(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "STREAM")
    add_title(slide, "Definisi event stream")
    data = [
        ["Field", "Isi"],
        ["event_id", "Hash dataset, zona, waktu, series_id, nilai"],
        ["event_time", "Awal interval pengukuran"],
        ["ingest_time", "Waktu event masuk sistem"],
        ["partition_key", "Zona, misalnya DE-LU"],
        ["payload_version", "1"],
    ]
    add_table(slide, Inches(0.75), Inches(1.7), Inches(6.7), [1.8, 4.9], data, 12, 0.6)
    add_card(slide, Inches(7.8), Inches(1.7), Inches(4.75), Inches(3.5), ACCENT_SOFT)
    add_text(slide, Inches(8.1), Inches(1.95), Inches(4.15), Inches(0.4),
             "Cara kerjanya", 15, True, ACCENT)
    add_list(
        slide,
        Inches(8.1),
        Inches(2.45),
        Inches(4.15),
        Inches(2.5),
        [
            "Energy-Charts adalah API tarik, bukan push.",
            "Poller membentuk event untuk setiap interval.",
            "Duplikat dibuang lewat event_id.",
            "Keterlambatan dibatasi watermark, pesan gagal masuk DLQ.",
        ],
        12.5,
        gap=10,
    )
    add_text(slide, Inches(0.75), Inches(5.95), Inches(11.8), Inches(0.4),
             "Bentuk sudah dikunci, implementasi menyusul setelah lapisan batch stabil.",
             12, True, AMBER)
    add_footer(slide, number)
    add_notes(
        slide,
        "Stream belum jalan, tetapi envelope-nya sudah ditetapkan supaya Silver dan Gold "
        "tidak perlu berubah saat producer dibuat.",
    )


def slide_architecture(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "ARSITEKTUR")
    add_title(slide, "Arsitektur target")

    add_box(slide, Inches(0.75), Inches(1.7), Inches(2.75), Inches(1.3),
            "SUMBER", "ENTSO-E · Energy-Charts · Open-Meteo")
    add_arrow(slide, Inches(3.62), Inches(2.2))
    add_box(slide, Inches(4.15), Inches(1.7), Inches(2.75), Inches(1.3),
            "INGESTION", "Prefect · Python worker")
    add_arrow(slide, Inches(7.02), Inches(2.2))

    lake = add_card(slide, Inches(7.55), Inches(1.45), Inches(5.0), Inches(1.85), WHITE, LINE)
    add_text(slide, Inches(7.72), Inches(1.55), Inches(4.6), Inches(0.3),
             "LAKEHOUSE · Garage S3 + Iceberg", 10.5, True, MUTED)
    add_box(slide, Inches(7.7), Inches(1.95), Inches(1.4), Inches(1.1), "Bronze", "raw", GRAY_SOFT, None, 12, 9)
    add_arrow(slide, Inches(9.15), Inches(2.38), Inches(0.28), Inches(0.24), MUTED)
    add_box(slide, Inches(9.5), Inches(1.95), Inches(1.4), Inches(1.1), "Silver", "validated", GRAY_SOFT, None, 12, 9)
    add_arrow(slide, Inches(10.95), Inches(2.38), Inches(0.28), Inches(0.24), MUTED)
    add_box(slide, Inches(11.3), Inches(1.95), Inches(1.1), Inches(1.1), "Gold", "mart", GRAY_SOFT, None, 12, 9)

    add_box(slide, Inches(0.75), Inches(4.1), Inches(1.75), Inches(1.2),
            "LAYANAN", "OpenLineage · Trino", title_size=11, subtitle_size=8.5)
    add_arrow(slide, Inches(2.62), Inches(4.55))
    add_box(slide, Inches(3.15), Inches(4.1), Inches(4.1), Inches(1.2),
            "ML", "Latih dari Gold · MLflow · tabel prediksi", title_size=11, subtitle_size=8.5)
    add_arrow(slide, Inches(7.37), Inches(4.55))
    add_box(slide, Inches(7.9), Inches(4.1), Inches(1.9), Inches(1.2),
            "AKSES", "Metabase · FastAPI", title_size=11, subtitle_size=8.5)
    add_arrow(slide, Inches(9.92), Inches(4.55))
    add_box(slide, Inches(10.45), Inches(4.1), Inches(2.1), Inches(1.2),
            "PORTAL", "Analytics · Forecasting", title_size=11, subtitle_size=8.5)

    add_card(slide, Inches(0.75), Inches(5.85), Inches(11.8), Inches(0.62), INK)
    add_text(slide, Inches(0.95), Inches(5.97), Inches(11.4), Inches(0.35),
             "OBSERVABILITY & KEAMANAN  ·  Prometheus, Grafana, alert, auth, audit, backup",
             11, True, WHITE)
    add_footer(slide, number)
    add_notes(
        slide,
        "Ini arsitektur target, bukan yang sudah selesai. Perhatikan bahwa observability, "
        "keamanan, dan backup adalah bagian dari gambar, bukan tambahan belakangan.",
    )


def slide_status(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "STATUS")
    add_title(slide, "Status arsitektur")

    def chip(x, y, w, text, fill, color=INK):
        add_box(slide, x, y, w, Inches(0.62), text, None, fill=fill, line=None, title_size=11, title_color=color)

    label_x = Inches(0.75)
    start_x = Inches(2.15)
    chip_w = Inches(1.55)
    gap = Inches(0.13)
    row1_y = Inches(1.75)
    add_text(slide, label_x, row1_y + Inches(0.16), Inches(1.3), Inches(0.3), "BATCH", 10, True, MUTED)
    batch = [
        ("Sumber batch", ACCENT_SOFT, ACCENT),
        ("Ingest manual", ACCENT_SOFT, ACCENT),
        ("Bronze lokal", ACCENT_SOFT, ACCENT),
        ("Garage + Iceberg", AMBER_SOFT, AMBER),
        ("Silver", GRAY_SOFT, MUTED),
        ("Gold", GRAY_SOFT, MUTED),
    ]
    x = start_x
    for text, fill, color in batch:
        chip(x, row1_y, chip_w, text, fill, color)
        x += chip_w + gap

    row2_y = Inches(2.65)
    add_text(slide, label_x, row2_y + Inches(0.16), Inches(1.3), Inches(0.3), "STREAM", 10, True, MUTED)
    stream = ["Poller", "Redpanda", "Consumer", "Event-time & DLQ"]
    x = start_x
    for text in stream:
        chip(x, row2_y, Inches(2.35), text, GRAY_SOFT, MUTED)
        x += Inches(2.35) + gap

    row3_y = Inches(3.55)
    add_text(slide, label_x, row3_y + Inches(0.16), Inches(1.3), Inches(0.3), "LAYANAN", 10, True, MUTED)
    serving = ["Trino", "ML + MLflow", "Dashboard", "API"]
    x = start_x
    for text in serving:
        chip(x, row3_y, Inches(2.35), text, GRAY_SOFT, MUTED)
        x += Inches(2.35) + gap

    add_card(slide, Inches(0.75), Inches(4.65), Inches(11.8), Inches(0.62), GRAY_SOFT)
    add_text(slide, Inches(0.95), Inches(4.77), Inches(11.4), Inches(0.35),
             "OPERASIONAL  ·  Metrics, structured logs, 3 alert, auth, backup, recovery",
             11, True, MUTED)

    add_text(slide, Inches(0.75), Inches(5.65), Inches(11.8), Inches(0.3),
             "Keterangan", 11, True, INK)
    add_box(slide, Inches(0.75), Inches(5.98), Inches(1.1), Inches(0.34), "Selesai", None, ACCENT_SOFT, None, 9, title_color=ACCENT)
    add_box(slide, Inches(1.98), Inches(5.98), Inches(1.35), Inches(0.34), "Sebagian", None, AMBER_SOFT, None, 9, title_color=AMBER)
    add_box(slide, Inches(3.46), Inches(5.98), Inches(1.1), Inches(0.34), "Belum", None, GRAY_SOFT, None, 9, title_color=MUTED)
    add_text(slide, Inches(4.75), Inches(6.02), Inches(7.7), Inches(0.3),
             "Hijau berarti berjalan dan diuji. Amber berarti berjalan tetapi belum sesuai target.",
             10, False, MUTED)
    add_footer(slide, number)
    add_notes(
        slide,
        "Yang hijau baru sumber, ingestion manual, dan Bronze lokal. "
        "Object store dan Iceberg belum, jadi statusnya amber. Sisanya masih abu-abu.",
    )


def slide_current_flow(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "PROGRESS")
    add_title(slide, "Yang sudah berjalan: sumber ke Bronze")
    boxes = [
        ("SUMBER", "Energy-Charts\nOpen-Meteo"),
        ("INGEST CLI", "Tarik data\nper rentang"),
        ("NORMALISASI", "UTC, tabel\npanjang"),
        ("BRONZE", "raw.json\ndata.parquet\nmetadata.json"),
    ]
    x = Inches(0.75)
    width = Inches(2.55)
    for index, (title, subtitle) in enumerate(boxes):
        add_box(slide, x, Inches(1.8), width, Inches(1.3), title, subtitle, WHITE, LINE, 10.5, 9)
        x += width
        if index < len(boxes) - 1:
            add_arrow(slide, x + Inches(0.11), Inches(2.3), Inches(0.28), Inches(0.26), MUTED)
            x += Inches(0.5)

    add_text(slide, Inches(0.75), Inches(3.35), Inches(11.8), Inches(0.35),
             "Satu batch = satu checksum isi data. Ingest ulang tidak menggandakan hasil.",
             12, False, MUTED)
    add_code_card(
        slide,
        Inches(0.75),
        Inches(3.95),
        Inches(11.8),
        Inches(1.9),
        [
            "$ uv run eurogrid list",
            "",
            "SUMBER         DATASET         PARTISI          BARIS",
            "energy_charts  public_power    country=de       14.112",
            "energy_charts  price           bzn=DE-LU        672",
            "open_meteo     weather_hourly  berlin           672",
        ],
        11.5,
    )
    add_text(slide, Inches(0.75), Inches(6.45), Inches(11.8), Inches(0.3),
             "Pemeriksaan: eurogrid list, eurogrid show, dan metadata.json per batch.",
             11, False, MUTED)
    add_footer(slide, number)
    add_notes(
        slide,
        "Alur ini berjalan manual lewat CLI. Belum ada jadwal, tetapi jalur data dan "
        "penyimpanannya sudah nyata dan bisa diperiksa.",
    )


def slide_results(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "HASIL")
    add_title(slide, "Hasil ingest minggu ini")

    cards = [
        ("3", "batch tersimpan"),
        ("15.456", "baris data nyata"),
        ("0", "nilai kosong"),
    ]
    x = Inches(0.75)
    for value, label in cards:
        add_card(slide, x, Inches(1.6), Inches(3.7), Inches(1.25), WHITE, LINE)
        add_text(slide, x + Inches(0.25), Inches(1.72), Inches(3.2), Inches(0.6), value, 30, True, ACCENT)
        add_text(slide, x + Inches(0.25), Inches(2.33), Inches(3.2), Inches(0.3), label, 11, False, MUTED)
        x += Inches(4.05)

    data = [
        ["Dataset", "Baris", "Rentang UTC", "Kosong"],
        ["public_power de", "14.112", "1 Nov 23:00  sampai  8 Nov 22:45", "0"],
        ["price DE-LU", "672", "1 Nov 23:00  sampai  8 Nov 22:45", "0"],
        ["weather Berlin", "672", "2 Nov 00:00  sampai  8 Nov 23:00", "0"],
    ]
    add_table(slide, Inches(0.75), Inches(3.2), Inches(11.8), [3.1, 1.7, 5.5, 1.5], data, 12.5, 0.66)
    add_text(slide, Inches(0.75), Inches(6.05), Inches(11.8), Inches(0.4),
             "14.112 baris berasal dari 672 interval 15 menit dikali 21 seri pembangkitan.",
             11.5, False, MUTED)
    add_footer(slide, number)
    add_notes(
        slide,
        "Semua angka berasal dari API sungguhan, bukan data sintetis. "
        "Tidak ada nilai kosong pada ketiga batch yang diambil.",
    )


def slide_proof(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "BUKTI")
    add_title(slide, "Kualitas dan idempotensi")
    add_list(
        slide,
        Inches(0.75),
        Inches(1.8),
        Inches(6.5),
        Inches(4.2),
        [
            "15 unit test lulus.",
            "Ingest ulang menghasilkan created=false dan batch_id yang sama.",
            "Checksum mengabaikan generated_at dan generationtime_ms.",
            "Checksum respons mentah tetap disimpan terpisah untuk audit.",
            "Data, metadata, dan lisensi tersimpan dalam satu batch.",
        ],
        16,
        gap=16,
        bullet="✓",
    )
    add_code_card(
        slide,
        Inches(7.6),
        Inches(1.8),
        Inches(4.95),
        Inches(2.0),
        [
            "$ ingest ulang",
            "",
            '{"batch_id":',
            ' "1567602672bcd4ad",',
            ' "created": false,',
            ' "row_count": 14112}',
        ],
        11.5,
    )
    add_text(slide, Inches(7.6), Inches(4.55), Inches(4.95), Inches(0.9),
             "Artinya dua ingest pada snapshot yang sama tidak menambah output ganda.",
             11.5, False, MUTED, line_spacing=1.3)
    add_text(slide, Inches(0.75), Inches(6.2), Inches(11.8), Inches(0.35),
             "Bukti lengkap: docs/evidence/2026-11-09-ingest-bronze.md",
             11, False, MUTED)
    add_footer(slide, number)
    add_notes(
        slide,
        "Idempotensi diuji dengan menjalankan perintah yang sama dua kali. "
        "Awalnya gagal karena generated_at berubah, lalu checksum diperbaiki.",
    )


def slide_delta(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "PROGRESS")
    add_title(slide, "Perbedaan dari minggu lalu")

    add_card(slide, Inches(0.75), Inches(1.7), Inches(5.65), Inches(4.15), GRAY_SOFT)
    add_text(slide, Inches(1.0), Inches(1.9), Inches(5.2), Inches(0.3),
             "MINGGU LALU", 10.5, True, MUTED)
    add_list(
        slide,
        Inches(1.0),
        Inches(2.3),
        Inches(5.1),
        Inches(3.2),
        [
            "Baru deck konsep dan arsitektur di atas kertas.",
            "Belum ada kode, data, atau bukti eksekusi.",
            "Sumber belum diverifikasi dan lisensi belum dicatat.",
            "Observability, keamanan, recovery belum masuk gambar.",
        ],
        14,
        gap=12,
    )

    add_card(slide, Inches(6.9), Inches(1.7), Inches(5.65), Inches(4.15), ACCENT_SOFT)
    add_text(slide, Inches(7.15), Inches(1.9), Inches(5.2), Inches(0.3),
             "MINGGU INI", 10.5, True, ACCENT)
    add_list(
        slide,
        Inches(7.15),
        Inches(2.3),
        Inches(5.1),
        Inches(3.2),
        [
            "Pipeline nyata dari sumber ke Bronze untuk Jerman.",
            "3 batch dan 15.456 baris data asli.",
            "15 tes lulus, idempotensi terbukti.",
            "Kontrak data dan lisensi terdokumentasi.",
            "Keputusan teknis: Podman, Parquet, definisi event.",
        ],
        14,
        gap=9,
    )
    add_text(slide, Inches(0.75), Inches(6.1), Inches(11.8), Inches(0.4),
             "Perubahan terbesar: dari rencana menjadi bukti yang bisa dijalankan.",
             14, True, INK)
    add_footer(slide, number)
    add_notes(
        slide,
        "Ini bagian yang diminta: apa yang berubah dibanding minggu lalu. "
        "Minggu lalu masih konsep, minggu ini sudah ada data dan tes.",
    )


def slide_obstacles(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "KENDALA")
    add_title(slide, "Kendala dan keputusan")
    data = [
        ["Kendala", "Dampak", "Keputusan"],
        ["Token ENTSO-E belum tersedia", "Sumber otoritatif tertunda", "Mulai dari Energy-Charts dan Open-Meteo"],
        ["Docker tidak terpasang", "Compose standar tidak bisa dipakai", "Pakai Podman dan podman-compose"],
        ["generated_at berubah tiap panggilan", "Ingest ulang dianggap data baru", "Checksum hanya isi data"],
        ["Stack berat untuk satu mesin", "Risiko resource", "Ukur dulu, siapkan pemangkasan"],
        ["Stream belum dimulai", "Gap terbesar terhadap spek", "Prioritaskan setelah batch utuh"],
    ]
    add_table(slide, Inches(0.75), Inches(1.65), Inches(11.8), [3.0, 3.3, 5.5], data, 12, 0.70)
    add_text(slide, Inches(0.75), Inches(6.2), Inches(11.8), Inches(0.35),
             "Dua kendala yang butuh perhatian: akses ENTSO-E dan kapasitas mesin untuk seluruh stack.",
             11, False, MUTED)
    add_footer(slide, number)
    add_notes(
        slide,
        "Kendala utama bukan teknis berat, tetapi akses data dan resource. "
        "Keduanya sudah punya jalan keluar sementara.",
    )


def slide_next(prs, number):
    slide = new_slide(prs)
    add_eyebrow(slide, "RENCANA")
    add_title(slide, "Rencana berikutnya")

    steps = [
        ("Selesai", "Sumber ke Bronze untuk Jerman", ACCENT),
        ("Minggu depan", "Garage S3 + Iceberg + Prefect, uji restart, backfill 30 hari", INK),
        ("Berikutnya", "Silver dengan quality gate, Gold 3 mart, 10 query", INK),
        ("Setelah itu", "Stream Redpanda, ML + MLflow, dashboard, observability", MUTED),
    ]
    y = Inches(1.8)
    for index, (label, detail, color) in enumerate(steps):
        add_text(slide, Inches(0.85), y, Inches(1.6), Inches(0.3), label, 11, True, color)
        add_text(slide, Inches(2.55), y - Inches(0.05), Inches(4.0), Inches(0.85), detail, 13.5, False, INK, line_spacing=1.15)
        if index < len(steps) - 1:
            add_rule(slide, y + Inches(0.95), Inches(0.85), Inches(5.5))
        y += Inches(1.08)

    add_card(slide, Inches(6.75), Inches(1.85), Inches(5.8), Inches(2.1), ACCENT_SOFT)
    add_text(slide, Inches(7.05), Inches(2.1), Inches(5.2), Inches(1.6),
             "Satu alur yang benar lebih berguna daripada banyak komponen yang belum tersambung.",
             20, True, ACCENT, line_spacing=1.2)
    add_text(slide, Inches(6.75), Inches(4.25), Inches(5.8), Inches(1.2),
             "Butuh keputusan: alokasi resource untuk seluruh stack dan prioritas stream setelah batch utuh.",
             12, False, MUTED, line_spacing=1.3)
    add_text(slide, Inches(0.85), Inches(6.35), Inches(11.7), Inches(0.35),
             "Target milestone: pipeline batch Jerman berjalan penuh, lalu stream dan ML.",
             11, True, INK)
    add_footer(slide, number)
    add_notes(
        slide,
        "Fokus minggu depan adalah memindahkan Bronze ke object store dan menjadwalkan ingest. "
        "Stream menyusul setelah batch punya satu mart yang bisa dipakai.",
    )


def build(output: Path):
    prs = Presentation()
    prs.slide_width = SW
    prs.slide_height = SH

    slide_title(prs)
    slide_agenda(prs, 2)
    slide_problem(prs, 3)
    slide_goals(prs, 4)
    slide_sources(prs, 5)
    slide_contract(prs, 6)
    slide_stream(prs, 7)
    slide_architecture(prs, 8)
    slide_status(prs, 9)
    slide_current_flow(prs, 10)
    slide_results(prs, 11)
    slide_proof(prs, 12)
    slide_delta(prs, 13)
    slide_obstacles(prs, 14)
    slide_next(prs, 15)

    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)
    return output


if __name__ == "__main__":
    destination = Path("slides/EuroGrid_Progress_2026-11-09.pptx")
    print(build(destination))