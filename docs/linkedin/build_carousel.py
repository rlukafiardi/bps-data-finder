"""Builds docs/linkedin/cari-data-bps-carousel.pdf (LinkedIn document post, 8 pages of 1080 x 1350). Identity and builder: the workspace skill social-posting.
Screenshots come from docs/linkedin/capture_shots.mjs (the live page, phone size, 3x); this script crops them.

    uv run --no-project --with reportlab --with pillow python -I docs/linkedin/build_carousel.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT.parents[1] / ".claude" / "skills" / "social-posting" / "scripts"))
from PIL import Image  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from social_brand import BLUE, INK2, NAVY, PAPER, SKY, H, M, W, Carousel, text  # noqa: E402

SHOTS = HERE / "shots"
# (source, crop box in the 1170 px wide screenshot, output): the parts of each phone screen that carry the point; the feature pages
# expect 752 px of height (840 x 540 pt)
for src, box, out in [
    ("home_dark.png", (0, 0, 1170, 1435), "crop_home.png"),
    ("search_light.png", (0, 540, 1170, 1292), "crop_search.png"),
    ("panel_garut_light.png", (0, 584, 1170, 1336), "crop_garut.png"),
    ("panel_var_light.png", (0, 1780, 1170, 2532), "crop_tools.png"),
]:
    Image.open(SHOTS / src).crop(box).save(SHOTS / out)

k = Carousel(HERE / "cari-data-bps-carousel.pdf", total=8, title="Cari Data BPS: satu pencarian untuk data BPS pusat dan daerah", shots=SHOTS)
c, slide, headline, shot, feature = k.c, k.slide, k.headline, k.shot, k.feature


def fits(lines, size, font="PJS-XBold", width=W - 2 * M):
    for s in lines:
        assert pdfmetrics.stringWidth(s, font, size) <= width, f"headline too wide: {s!r}"


# 1 sampul
fits(["Data BPS ada di", "lebih dari 540", "situs berbeda."], 100)
slide(1, NAVY, PAPER)
y = headline(M, H - 230, [("Data BPS ada di", False), ("lebih dari 540", True), ("situs berbeda.", False)], 100, PAPER)
text(c, M, y - 6, "Cari Data BPS: satu kotak pencarian untuk menemukannya.", "PJS-Medium", 36, SKY, 400, 1.25)
shot("crop_home.png", W - M - 500, 90, 500)

# 2 masalahnya
fits(["Satu angka,", "banyak situs."], 100)
slide(2, PAPER, NAVY)
y = headline(M, H - 240, [("Satu angka,", False), ("banyak situs.", False)], 100, NAVY)
y = text(c, M, y - 14, "BPS pusat, provinsi, dan kabupaten/kota masing-masing punya situs sendiri.", "PJS-Medium", 38, INK2, W - 2 * M, 1.3)
y -= 56
for host in ["bps.go.id", "jabar.bps.go.id", "garutkab.bps.go.id"]:
    c.setStrokeColor(SKY); c.setLineWidth(2); c.line(M, y + 62, W - M, y + 62)
    c.setFillColor(BLUE); c.setFont("PJS-XBold", 44); c.drawString(M, y + 8, host)
    y -= 100
text(c, M, y + 8, "Mencari satu angka berarti loncat dari situs ke situs. Angka di dalam publikasi paling susah ditemukan.", "PJS-SemiBold", 36, NAVY, W - 2 * M, 1.3)

# 3 tulis seperti ngobrol
fits(["Tulis seperti", "ngobrol."], 84)
feature(3, SKY, NAVY, [("Tulis seperti", False), ("ngobrol.", False)], "crop_search.png",
        [("Bahasa biasa", "Istilah dan singkatan BPS dibantu model bahasa."),
         ("Daerah dikenali", "Nama provinsi dan kabupaten dibaca dari kalimat."),
         ("Banyak sumber sekaligus", "Pusat, provinsi, dan Dalam Angka kabupaten/kota.")], sub=NAVY)

# 4 baris daerah
fits(["Daerah yang dicari", "langsung di atas."], 84)
feature(4, PAPER, NAVY, [("Daerah yang dicari", False), ("langsung di atas.", False)], "crop_garut.png",
        [("Baris daerahnya dulu", "Tiga kolom terakhir, lengkapnya ada di tabel."),
         ("Angka apa adanya", "Disalin dari API BPS. Model tidak menulis angka."),
         ("Tahun lain", "Pilih tahun, angkanya diambil lagi dari BPS.")])

# 5 katalog
slide(5, BLUE, PAPER)
headline(M, H - 270, [("74.945", True)], 190, PAPER)
text(c, M, H - 360, "sumber data dalam satu katalog", "PJS-Bold", 40, PAPER, W - 2 * M)
y = 770
for label, value in [("DALAM ANGKA", "28.926"), ("TABEL ANGKA", "20.898"), ("TABEL ARSIP", "16.016"), ("BERITA RESMI", "5.450"), ("PUBLIKASI", "3.655")]:
    c.setStrokeColor(SKY); c.setLineWidth(2); c.line(M, y + 78, W - M, y + 78)
    c.setFillColor(SKY); c.setFont("PJS-Bold", 28); c.drawString(M, y + 14, label)
    c.setFillColor(PAPER); c.setFont("PJS-XBold", 62); c.drawRightString(W - M, y + 8, value)
    y -= 120

# 6 kutipan
fits(["Siap dikutip", "dan diunduh."], 84)
feature(6, SKY, NAVY, [("Siap dikutip", False), ("dan diunduh.", False)], "crop_tools.png",
        [("Sumber dan waktu", "Sumber dari BPS dan kapan angkanya diambil."),
         ("Salin kutipan", "Judul, tanggal akses, dan tautan BPS sekali klik."),
         ("Unduh CSV", "Tabelnya apa adanya, atau salin tautan ke tabel.")], sub=NAVY)

# 7 batasan
fits(["Yang belum", "ada."], 100)
slide(7, PAPER, NAVY)
headline(M, H - 240, [("Yang belum", False), ("ada.", False)], 100, NAVY)
y = H - 520
for head, body in [("Publikasi", "Hasilnya baru mengarah ke publikasinya (terbitan 2025 dan 2026). Angka di dalam PDF belum ditampilkan."),
                   ("Kabupaten/kota", "Baru tabel Dalam Angka. Tabel dan publikasi lainnya belum masuk."),
                   ("Model bahasa gratis", "Kalau sedang sibuk, hasil bisa kurang pas dan lebih lambat.")]:
    c.setStrokeColor(SKY); c.setLineWidth(2); c.line(M, y + 56, W - M, y + 56)
    c.setFillColor(BLUE); c.setFont("PJS-Bold", 26); c.drawString(M, y + 6, head.upper())
    y = text(c, M, y - 44, body, "PJS-SemiBold", 38, NAVY, W - 2 * M, 1.22) - 44

# 8 ajakan
fits(["Coba", "sendiri."], 100)
slide(8, NAVY, PAPER)
headline(M, H - 240, [("Coba", False), ("sendiri.", False)], 100, PAPER)
c.setFillColor(PAPER); c.rect(M, 250, W - 2 * M, 430, stroke=0, fill=1)
text(c, M + 40, 610, "cari-data-bps.netlify.app", "PJS-XBold", 50, NAVY, W - 2 * M - 80)
text(c, M + 40, 520, "Ada angka yang terlihat janggal? Itu angka BPS apa adanya. Tulis di komentar, nanti dicek.", "PJS-Medium", 30, INK2, W - 2 * M - 80, 1.3)
text(c, M + 40, 360, "Data dari Badan Pusat Statistik. Situs ini bukan produk resmi BPS.", "PJS-Regular", 26, INK2, W - 2 * M - 80)

k.save()
