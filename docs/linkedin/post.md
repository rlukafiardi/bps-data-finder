Cari data di BPS kadang agak back and forth. Tiap provinsi dan kabupaten punya situs sendiri, jadi buat nyari "berapa penduduk miskin di Garut" bisa bikin buka tiga situs: BPS nasional, Jawa Barat, dan Garut. Itu pun kadang angkanya cuma ada di dalam publikasi PDF.

Dari sini muncul ide bikin Cari Data BPS, pakai API BPS dan hybrid retrieval buat nyari di 74 ribu lebih dari metadata tabel, publikasi, dan berita resmi dari pusat, provinsi, sampai kabupaten/kota sekaligus.

Simpelnya, menggunakan BM25 nyocokin kata kunci, semantic search nyocokin semantically dari suatu kata, dan AI bantu rewrite ulang pertanyaan ke istilah BPS jika terjadi ambigu. Contohnya "turis asing yang datang": kalau cuma nyocokin kata, yang keluar tabel harga valuta asing. Kalau pake metode hybrid retrieval, yang keluar tabel Jumlah Kedatangan Wisatawan Mancanegara.

Feel free to explore di cari-data-bps.netlify.app

Codebase: github.com/rlukafiardi/bps-data-finder-showcase
