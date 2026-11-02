# Golden set

`golden_set.csv`: one row per question you have really searched for on bps.go.id.

- `question`: as you would type it, Bahasa or English, with acronyms if you'd use them.
- `expected_type`: `var` (dynamic table), `statictable`, `simdasi` (Dalam Angka table), `publication`, `pressrelease`.
- `expected_id`: the id from the BPS link (var id, table_id, pub_id, brs_id, or SIMDASI kode_tabel).
  Several correct answers: separate with `|`.
- `domain`: 4-digit BPS domain (`0000` national, `3200` Jawa Barat, `3273` Kota Bandung, ...).
- `year`: the period asked for, if any.

Aim for about 50, spread over types and levels (national / province / kab-kota), including a few you
never found.
