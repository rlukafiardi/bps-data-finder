Cari data di BPS kadang agak back and forth Tiap provinsi dan kabupaten punya situs sendiri, semisal mau cari data "berapa penduduk miskin di Garut" bisa bikin buka tiga situs: BPS nasional, Jawa Barat, dan Garut. Itu pun kadang datanya ada di dalam publikasi pdf.

Dari sini, gua coba bikin Cari Data BPS menggunakan API BPS & Hybrid Retrieval buat ngeproses 74k+ metadata data nasional, provinsi, dan kabupaten/kota jadi cepat buat didapetin datanya.

Simpelnya, menggunakan BM25 buat nyocokin kata kunci, semantic search buat nyocokin arti, dan AI buat nerjemahin pertanyaan ke istilah BPS. Contohnya "turis asing yang datang": kalau cuma nyocokin kata, yang keluar tabel harga valuta asing. Kalau artinya ikut dicocokin, yang keluar Jumlah Kedatangan Wisatawan Mancanegara.

cari-data-bps.netlify.app

Codebase: github.com/rlukafiardi/bps-data-finder-showcase
