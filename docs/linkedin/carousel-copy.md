Carousel copy v5 (plain text for approval; nothing is built from it yet). Changes from v2: page 4 loses "bukan ditulis AI"; new page 5 explains the search (word match plus meaning match); 9 pages.

1 cover (screenshot: home)
  Cari data BPS tanpa buka situsnya satu-satu.
  Cari Data BPS

2 problem
  Lebih dari 540 situs BPS.
  Pusat, provinsi, dan tiap kabupaten/kota punya situs sendiri. Satu angka bisa bikin buka tiga situs, dan angka di dalam publikasi lebih susah lagi.
  (bps.go.id / jabar.bps.go.id / garutkab.bps.go.id as the visual)

3 search (screenshot: search)
  Ketik pertanyaannya.
  Nama daerah dibaca dari kalimatnya, jadi nggak perlu pilih provinsi dulu.

4 answer (screenshot: Garut)
  Barisnya langsung ketemu.
  Baris daerah yang dicari ada paling atas. Angkanya langsung dari API BPS.

5 why it differs (new, no screenshot; two stacked blocks like page 2)
  Bedanya sama pencarian biasa.
  Cuma kata kunci (BM25): "turis asing yang datang" nemu tabel harga valuta asing, karena sama-sama ada kata "asing".
  Kata dan arti (semantic): "turis asing yang datang" nemu Jumlah Kedatangan Wisatawan Mancanegara.
  (small line under the blocks) AI nerjemahin pertanyaan ke istilah BPS dulu, misalnya "turis asing" jadi "wisatawan mancanegara".

6 numbers
  74.945 sumber data yang bisa dicari
  Dalam Angka 28.926, tabel angka 20.898, tabel arsip 16.016, berita resmi 5.450, publikasi 3.655.

7 tools (screenshot: tools)
  Tinggal salin.
  Salin kutipan (judul, tanggal akses, link BPS), unduh CSV, atau salin link ke tabelnya. Di bawah tabel ada sumber dan kapan angkanya diambil.

8 limits
  Yang belum bisa.
  Publikasi: baru link ke publikasinya (terbitan 2025 dan 2026), angka di dalam PDF belum bisa ditarik.
  Kabupaten/kota: baru tabel Dalam Angka.
  AI-nya versi gratis, jadi kalau lagi sibuk hasilnya bisa kurang pas dan lebih lambat.

9 end
  cari-data-bps.netlify.app
  Data dari BPS. Situs ini bukan produk resmi BPS.
