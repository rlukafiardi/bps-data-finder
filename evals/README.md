# Golden set

`golden_set.csv`: one row per question, with every equally valid answer.

- `question`: as you would type it, Bahasa or English, with acronyms if you'd use them.
- `targets`: `type:domain:id`, several separated by `|`. Types: `var` (dynamic table), `statictable`,
  `simdasi` (Dalam Angka table; id = table code like `4.1.3`), `publication`, `pressrelease`.
  Domain is the 4-digit BPS code of the site the table sits on (`0000` national, `3200` Jawa Barat,
  `3273` Kota Bandung); a national table "menurut Kabupaten/Kota" is a valid target for a kab/kota question.
  The id is in the BPS link: var / static table id after base64-decoding the link token, pub_id, brs_id.
- `source`: `radikal` for questions from real searches, `claude` for drafted ones. Drafted questions were
  written from a need first and labelled afterwards with keyword filters, but they are still easier than
  real ones: judge pass / stop on `radikal` rows.

Aim for about 50 `radikal` rows, spread over types and levels, including a few you never found.

    uv run python -m evals.run_eval
