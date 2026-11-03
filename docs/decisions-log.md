# Decisions log

Dated findings, decisions and incidents, newest last. Search with grep; the key decisions that still shape
the work are in `CLAUDE.md`.

## 2026-11-03: full build, risks 1-2

- Plan: Netlify page (`web/`) + Python search/values API on Cloud Run (HF Spaces as fallback host), values
  verbatim for var / SIMDASI / static tables, monthly local refresh. Netlify Functions can't run the torch
  model; a Netlify-only build would drop semantic search (R@5 ~0.81 instead of 0.93).
- BPS WebAPI terms (all 23 sections read via a fetched summary; verbatim text and the BPS content policy
  of section 20 unverified): public non-commercial use allowed. Requirements: credential tied to its
  registered application (register / update the app description for the public site), token server-side
  only, one token and no rate-limit evasion, attribution "This service uses the Badan Pusat Statistik (BPS)
  API.", no implied endorsement, derived results not presented as official, no altered data, caching OK
  but never present stale data as current (show period + retrieved date), commercial use needs approval.
- var values: `/api/list/model/th/domain/{d}/key/{k}?var=` lists periods (`th_id`, `th`), newest = max `th`.
  `/api/list/model/data/domain/{d}/var/{var}/th/{th_id}/key/{k}` returns `vervar` (rows), `turvar`,
  `tahun`, `turtahun` (sub-periods, e.g. Februari/Agustus), `var` (unit, decimal, note), `last_update`,
  and `datacontent` keyed by the concatenated vals vervar+var+turvar+tahun+turtahun
  (e.g. `11005430126189` = Aceh, var 543, turvar 0, 2026, Februari -> 5.88).
- static table values: `/api/view/domain/{d}/model/statictable/lang/ind/id/{id}/key/{k}` -> `table` (HTML,
  82 KB for table 1555), `updt_date`, `excel` link. Parser to be checked on merged headers.
- Links without slug work (HTTP 200, right page): `https://{site}/id/publication/{YYYY/MM/DD rl_date}/{pub_id}`
  and `/id/pressrelease/{YYYY/MM/DD}/{brs_id}`; `{site}` is `www.bps.go.id` or the domain_url. PDF links
  carry a token and are never shown.

## 2026-11-03: risk 4, startup cost (measured locally, M-series Mac)

- Imports 4.4 s, catalog + BM25 2.5 s, e5-small + 75k embeddings 5.4 s, first hybrid query 1.0 s; peak
  memory ~1.6 GB (`ru_maxrss` is bytes on macOS). torch is 613 MB on disk (macOS wheel).
- Cloud Run needs 2 GiB; cold start with min instances 0 estimated 15-30 s. Mitigations in order: serve a
  plain float32 matrix (115 MB) instead of the cache parquet, CPU-only torch wheel in the image (the default
  Linux wheel bundles CUDA), then an ONNX query encoder without torch. Decide at deploy with a measured cold
  start. No local Docker: Cloud Build builds the image remotely.

## 2026-11-03: region filter + kab/kota name stripping (fallback ladder)

- Found by using the API: "TPT kota bandung 2025" and "jumlah penduduk miskin kabupaten garut" returned
  off-topic Dalam Angka tables of that kab/kota (civil servants, health workers): its own tables all repeat
  "di Kota X", which BM25 rewarded, while the answer was the province table "menurut Kabupaten/Kota".
- Added 5 golden questions for the case (`source=claude-ladder`, labelled with keyword filters before the
  change): kab/kota with no own table, answered at province or national level.
- Fix: retrievers take an allowed-domain set (bm25s `weight_mask`, dense score mask); RegionRank searches
  only kab/kota + province + national, and removes **kab/kota** names from the scored text. Removing
  province/national names too cost 5 questions whose answering titles contain the name ("Statistik
  Indonesia 2026", "Provinsi Sumatera Utara Dalam Angka 2026"), so those stay.
- rewrite+hybrid+region R@5 / MRR: before 0.88 / 0.67 (75 q), after 0.93 / 0.70; ladder questions 0.20 -> 1.00,
  original 70 unchanged at 0.93. One genuine shift: "indeks kedalaman kemiskinan tiap provinsi kota dan desa"
  4th -> 6th. Pooled judging added var:1900:1017 (NTP Tanaman Perkebunan Rakyat) for "NTP perkebunan babel".

## 2026-11-03: public app not registered with BPS (Radikal's decision)

- Radikal decided not to register the public website as an application in the BPS developer portal. The
  terms (section 2) tie each credential to its registered application and let BPS restrict or revoke
  requests; if the key stops working after the site goes public, check this first.

## 2026-11-03: values (`/api/value`, `src/values/`)

- One shape for all three table types (title, unit, period + available periods, columns, rows with
  `highlight`, note, source, updated, `fetched_at`). Numbers are the API's own text: var values via the
  `datacontent` key (vervar + var + turvar + tahun + turtahun), Dalam Angka via each cell's `value`, static
  tables via the exported HTML. Nothing is computed, rounded or reformatted.
- BPS client: one slot per 3 s for all visitors together (the key's limit is ~20/min), a visitor whose slot is
  more than 15 s away gets 429 "coba lagi sebentar"; answers cached 24 h and shown with their fetch time (the
  terms forbid presenting stale stored data as current). Errors never carry the URL: it contains the key.
- Dalam Angka tables list columns that most rows have no value for (the province total row has them): a
  missing cell is shown empty, not treated as an error.
- Static tables are Excel exports without header tags (title row, header row, data, footnotes). pandas
  `read_html` corrupted them (years became `2021.0`, thousands separator guesses), so `html_grid` reads the
  cells with lxml (merged cells repeated across their span). Known limits: a two-level header shows its
  second row as the first data row; short footnotes (<20 chars, e.g. `*)Backcasting`) stay as data rows.
- Tests: `tests/test_values.py` (7, inline tables copied from live shapes). A deliberate bug in the value-key
  order made one fail; after restoring the file a stale `.pyc` (same size, same second) still failed: clear
  `__pycache__` when a mutation check looks wrong.
- Live checks through the API: var (national, Jabar), Dalam Angka (Jabar, years 2023/2025), static (Jabar);
  400 for a publication, an unknown period; 404 for an unknown doc; the key does not appear in the log.

## 2026-11-03: web page (`web/`) and link checks

- Page: plain HTML/CSS/JS, no build step, Netlify-ready. Welcome card, search box + example chips, result
  cards (type badge, region, years/date, "Lihat Angkanya" + "Buka di BPS"), value panel (phone: bottom sheet,
  desktop: right side panel; year picker, sticky header and first column, asked region highlighted and scrolled
  into view, fetch time, BPS attribution). Text is set with `textContent` only; CSP `script-src 'self'`.
  Light and dark follow the system. Not done: other languages, a focus trap inside the panel, an About page.
- Security headers: `web/_headers` (CSP with `connect-src 'self' API_ORIGIN`, frame-ancestors none, nosniff,
  referrer and permissions policy). At deploy replace `API_ORIGIN` there and `API_BASE` in `web/config.js`;
  the API's `ALLOWED_ORIGINS` must be the Netlify site.
- Tests: `npm run test:e2e` (11 checks, real Chrome, fake API replaying recorded responses, served under the
  real headers; asserts the CSP is not violated, no third-party requests, wording rules, 44 px targets, no
  sideways scroll, phone/desktop/light layouts; screenshots in `tests/e2e/shots/`, ignored by git).
  `LIVE=1 npm run test:e2e` runs the page against the real API on :8000 (one Gemini + a few BPS calls).
  Three deliberate breaks (titles as HTML, no bottom sheet, a stiff word) each failed the matching check.
- Link checks (`tests/e2e/links.mjs sample.json`, 15 s between pages): publication and press-release links
  built by us open the right page (6 of 6, including province sites). Tables: BPS's own national link
  renders; province and kab/kota sites answer headless Chrome with a bot-defense challenge (HTTP 520 on a
  `TSPD` request), which we do not work around, so their table pages cannot be checked here. Our Dalam Angka
  token form (`id#3#domain`) equals the 5,271 national/province links BPS gave us; for kab/kota it is
  unchecked, and the 3 dynamic tables that search never listed fail inside bps.go.id. Those 23,598 + 3 rows
  now have no link (`url` null): the page shows their numbers but no "Buka di BPS".
- Found while testing: the BPS websites rate-limit visitors (429 after ~6 page loads in 20 s).
