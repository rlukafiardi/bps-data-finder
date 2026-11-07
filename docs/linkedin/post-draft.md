Cari data di BPS itu ribet. Tiap provinsi dan kabupaten punya situs sendiri, jadi satu pertanyaan kayak "berapa penduduk miskin di Garut" bisa bikin buka tiga situs: pusat, Jawa Barat, lalu Garut. Itu pun angkanya sering nggak ketemu, apalagi kalau adanya di dalam publikasi.

Makanya gua bikin Cari Data BPS. Ketik pertanyaan biasa, misalnya "jumlah penduduk miskin kabupaten garut", langsung keluar tabel Jawa Barat dengan baris Garut: 9,39 persen (Maret 2025). Angkanya langsung dari API BPS.

Nyarinya gabungan tiga hal: BM25 buat nyocokin kata kunci, semantic search buat nyocokin arti, dan AI buat nerjemahin pertanyaan ke istilah BPS. Contohnya "bayi yang meninggal": kalau cuma nyocokin kata, yang keluar tabel korban bencana dan kasus AIDS. Kalau artinya ikut dicocokin, yang keluar Angka Kematian Bayi. Kalau hasilnya publikasi, gua kasih link-nya aja, angka di dalam PDF belum bisa ditarik.

cari-data-bps.netlify.app
Codebase: github.com/rlukafiardi/bps-data-finder-showcase
