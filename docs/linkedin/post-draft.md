Cari data di BPS kadang agak back and forth. Tiap provinsi dan kabupaten punya situs sendiri, jadi buat nyari "berapa penduduk miskin di Garut" bisa bikin buka tiga situs: BPS nasional, Jawa Barat, dan Garut. Itu pun kadang angkanya cuma ada di dalam publikasi PDF.

Dari situ gua bikin Cari Data BPS, pakai API BPS dan hybrid retrieval buat nyari di 74 ribu lebih tabel, publikasi, dan berita resmi dari pusat, provinsi, sampai kabupaten/kota sekaligus. Ketik pertanyaan biasa, langsung keluar tabelnya, angkanya dari API BPS.

Simpelnya, BM25 nyocokin kata kunci, semantic search nyocokin arti, dan AI nerjemahin pertanyaan ke istilah BPS. Contohnya "turis asing yang datang": kalau cuma nyocokin kata, yang keluar tabel harga valuta asing. Kalau artinya ikut dicocokin, yang keluar Jumlah Kedatangan Wisatawan Mancanegara.

cari-data-bps.netlify.app
Codebase: github.com/rlukafiardi/bps-data-finder-showcase
