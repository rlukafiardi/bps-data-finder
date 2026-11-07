"""Builds docs/linkedin/cari-data-bps-carousel.pdf (LinkedIn document post, 9 pages of 1080 x 1350). Identity and builder: the workspace skill social-posting.
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

k = Carousel(HERE / "cari-data-bps-carousel.pdf", total=9, title="Cari Data BPS: satu pencarian untuk data BPS pusat dan daerah", shots=SHOTS)
c, slide, headline, shot, feature = k.c, k.slide, k.headline, k.shot, k.feature


def fits(lines, size, font="PJS-XBold", width=W - 2 * M):
    for s in lines:
        assert pdfmetrics.stringWidth(s, font, size) <= width, f"headline too wide: {s!r}"


# 1 sampul
fits(["Cari data BPS", "tanpa buka", "situsnya", "satu-satu."], 100)
slide(1, NAVY, PAPER)
y = headline(M, H - 230, [("Cari data BPS", False), ("tanpa buka", False), ("situsnya", False), ("satu-satu.", True)], 100, PAPER)
text(c, M, y - 6, "Cari Data BPS", "PJS-Bold", 44, SKY, 400)
shot("crop_home.png", W - M - 500, 90, 500)

# 2 masalahnya
fits(["Lebih dari 540", "situs BPS."], 100)
slide(2, PAPER, NAVY)
y = headline(M, H - 240, [("Lebih dari 540", False), ("situs BPS.", False)], 100, NAVY)
y = text(c, M, y - 14, "Pusat, provinsi, dan tiap kabupaten/kota punya situs sendiri. Satu angka bisa bikin buka tiga situs, dan angka di dalam publikasi lebih susah lagi.", "PJS-Medium", 38, INK2, W - 2 * M, 1.3)
y -= 72
for host in ["bps.go.id", "jabar.bps.go.id", "garutkab.bps.go.id"]:
    c.setStrokeColor(SKY); c.setLineWidth(2); c.line(M, y + 62, W - M, y + 62)
    c.setFillColor(BLUE); c.setFont("PJS-XBold", 44); c.drawString(M, y + 8, host)
    y -= 100

# 3 ketik pertanyaannya
fits(["Ketik", "pertanyaannya."], 84)
feature(3, SKY, NAVY, [("Ketik", False), ("pertanyaannya.", False)], "crop_search.png",
        caption="Nama daerah dibaca dari kalimatnya, jadi nggak perlu pilih provinsi dulu.")

# 4 baris daerah
fits(["Barisnya", "langsung ketemu."], 84)
feature(4, PAPER, NAVY, [("Barisnya", False), ("langsung ketemu.", False)], "crop_garut.png",
        caption="Baris daerah yang dicari ada paling atas. Angkanya langsung dari API BPS.")

# 5 bedanya
fits(["Bedanya sama", "pencarian biasa."], 84)
fits(["Cuma kata kunci (BM25)", "Kata dan arti (semantic)"], 56)
slide(5, NAVY, PAPER)
y = headline(M, H - 230, [("Bedanya sama", False), ("pencarian biasa.", False)], 84, PAPER)
y -= 60
for head, line in [("Cuma kata kunci (BM25)", '"turis asing yang datang" nemu tabel harga valuta asing, karena sama-sama ada kata "asing".'),
                   ("Kata dan arti (semantic)", '"turis asing yang datang" nemu Jumlah Kedatangan Wisatawan Mancanegara.')]:
    c.setStrokeColor(SKY); c.setLineWidth(2); c.line(M, y + 74, W - M, y + 74)
    y = text(c, M, y, head, "PJS-XBold", 56, SKY, W - 2 * M)
    y = text(c, M, y - 4, line, "PJS-Medium", 44, PAPER, W - 2 * M, 1.3) - 80
text(c, M, y, 'AI nerjemahin pertanyaan ke istilah BPS dulu, misalnya "turis asing" jadi "wisatawan mancanegara".', "PJS-Regular", 32, SKY, W - 2 * M, 1.3)

# 6 angka
slide(6, BLUE, PAPER)
headline(M, H - 270, [("74.945", True)], 190, PAPER)
text(c, M, H - 360, "sumber data yang bisa dicari", "PJS-Bold", 40, PAPER, W - 2 * M)
y = 770
for label, value in [("DALAM ANGKA", "28.926"), ("TABEL ANGKA", "20.898"), ("TABEL ARSIP", "16.016"), ("BERITA RESMI", "5.450"), ("PUBLIKASI", "3.655")]:
    c.setStrokeColor(SKY); c.setLineWidth(2); c.line(M, y + 78, W - M, y + 78)
    c.setFillColor(SKY); c.setFont("PJS-Bold", 28); c.drawString(M, y + 14, label)
    c.setFillColor(PAPER); c.setFont("PJS-XBold", 62); c.drawRightString(W - M, y + 8, value)
    y -= 120

# 7 salin
fits(["Tinggal", "salin."], 84)
feature(7, SKY, NAVY, [("Tinggal", False), ("salin.", False)], "crop_tools.png",
        caption="Salin kutipan (judul, tanggal akses, link BPS), unduh CSV, atau salin link ke tabelnya. Di bawah tabel ada sumber dan kapan angkanya diambil.")

# 8 batasan
fits(["Yang belum", "bisa."], 100)
slide(8, PAPER, NAVY)
headline(M, H - 240, [("Yang belum", False), ("bisa.", False)], 100, NAVY)
y = H - 500
for s_ in ["Publikasi: baru link ke publikasinya (terbitan 2025 dan 2026), angka di dalam PDF belum bisa ditarik.",
           "Kabupaten/kota: baru tabel Dalam Angka.",
           "AI-nya versi gratis, jadi kalau lagi sibuk hasilnya bisa kurang pas dan lebih lambat."]:
    c.setStrokeColor(SKY); c.setLineWidth(2); c.line(M, y + 50, W - M, y + 50)
    y = text(c, M, y, s_, "PJS-SemiBold", 40, NAVY, W - 2 * M, 1.22) - 64

# 9 penutup
slide(9, NAVY, PAPER)
text(c, M, H - 560, "cari-data-bps.netlify.app", "PJS-XBold", 56, PAPER, W - 2 * M)
text(c, M, H - 640, "Data dari BPS. Situs ini bukan produk resmi BPS.", "PJS-Regular", 30, SKY, W - 2 * M)

k.save()
