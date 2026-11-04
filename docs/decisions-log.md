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

## 2026-11-03: period matching and BM25 title weight

- Trigger: "BRS DKI Januari 2025" never found its exact-title publication. Cause: BM25 divides by document
  length and BRS publications carry long abstracts (979 chars vs an empty one for "Juli 2025"), and the abstract
  names the data month (Desember 2024), not the release month; the exact title ranked 98th in dense and
  beyond 300th in BM25, so no re-ranking could save it.
- Two changes, measured separately (88 questions, rewrite+hybrid+region R@5 / MRR; baseline 0.932 / 0.729):
  1. Period matching (`src/retrieval/period.py`, applied in `RegionRank`): month / quarter / year parsed from
     the question and each title (ranges expanded, glued "Desember2024" handled, base years like "Seri 2010",
     "2018=100", "SP2020" ignored; Dalam Angka rows use the years BPS has them for). Agreement boosts the
     score (x1.3 month / quarter, x1.15 year), a different period demotes it (x0.7 / x0.75), a title without
     a period is left alone. Alone: 0.943 / 0.737; period questions 0.92 -> 1.00. It cannot fix a document
     that is missing from the candidates.
  2. BM25 title weight 5 (`TITLE_WEIGHT`, title counted 5 times): tried 1, 2, 3, 5, 8, 12, 20 on all
     questions; flat from 5 to 12 (Recall@5 0.943-0.955), worse at 20 (kab/kota fallback questions slip).
     Took 5, the lowest value on the plateau, so abstracts still count. Together: 0.955 / 0.800.
- 13 period questions added before the change (`source=claude-period`, labelled by title keywords).
  16 questions improved, 6 got worse; the two big "regressions" were label gaps (the new ranking found
  other tables that answer the question: current wage tables by education, "NTP Menurut Subsektor") and
  were added by pooled judging under the same rule as before. Final: **0.977 / 0.831**; misses left:
  "garis kemiskinan provinsi" (rank 8), "harga sembako di pematangsiantar" (rank 7).
- A first unit test for the title weight passed even with the weight reverted (it set the weight itself);
  rewritten to use the shipped value, then confirmed to fail on a revert.
- Not done, by size: page numbers inside publications. The catalog holds only title, abstract and PDF link.
  Page-level search needs the PDFs read: all 3,649 PDFs of 2025-2026 are 36 GB (median 7.6 MB, 479 over 20 MB),
  too much at the BPS rate limit; the 80 yearbooks (Dalam Angka, Statistik Indonesia) are 1.1 GB. PDF links
  carry a token, whether they are text or scans is unchecked, and bulk downloads need a look at the terms.

## 2026-11-04: page numbers inside publications, pilot on one yearbook (parked)

- Terms re-read: the API terms PDF (Dec 2022, scanned images, read by eye) says nothing about downloading PDFs;
  section 12 sends content use to the website terms. The website terms (`https://www.bps.go.id/en/term-of-use`,
  section 13, read through a fetch summary with verbatim quotes) allow copying, distributing, extraction and
  modification, commercial or not, with credit (title, access date, direct link). No ban on bulk download found;
  sections 14-15 only reserve monitoring and blocking. Old `S&K.pdf` link is a 404.
- PDF link tokens expire: a link stored in the catalog returned "Invalid Token"; a fresh one comes from one
  `view/.../model/publication/.../id/` call (`data.pdf`). The download server ignores Range requests and ran at
  about 50 KB/s (12.8 MB in ~4 min).
- Pilot on Statistik Indonesia 2026 (920 pages, text layer, 36 near-empty pages): the contents pages list every
  table with its printed page. Parsed 406 tables (codes `x.y.z` and `x.y`; section headings dropped because they
  never get a page); printed page + 44 = PDF page, and the table title is on that page for 404 of 406. Table-title
  BM25 found the right page for the test questions ("garis kemiskinan" hal. 331, "kejahatan menurut polda" hal.
  302, "inflasi bulanan" hal. 635); "angka harapan hidup" has no table in that book.
- Values: `pymupdf` `find_tables().extract()` scrambles separators ("71896 ," for 718,96). Filling each cell with the
  words inside its box keeps the text exact ("718,96", "1.110,92"). Checked on all 406 tables: 55,789 numbers
  inside the table box, 0 lost and 0 duplicated (mutation check: a removed or swapped cell is caught). Not
  covered: wrong column header, multi-level headers (came out partly blank), tables that continue on a next page,
  and a footer URL that can land in a cell (filtered). `pymupdf` is 4x faster than `pypdf` (17 s vs 74 s).
- Catalog count: 157 yearbook-type publications, 153 province + 4 national, no kab/kota (publication lists were
  only pulled for national and provinces). Province and national yearbooks mostly compile tables already in
  var / SIMDASI (not measured). The known gap (kab/kota tables absent from SIMDASI) needs ~1,000 more PDFs.
- Decision: parked. Cost (new result type, per-layout parser, hours of polite downloading, "read from PDF,
  unchecked" labels) against an unmeasured gain. Revisit when the logged real queries show how many end with only
  a publication link and no table; first slice then = 4-5 kab/kota books. Pilot scripts were in the scratchpad
  and are not in the repo.

## 2026-11-04: web page redesign, answer-first (`web/`)

- Looked at the page as a first-time visitor (phone, light and dark, desktop) before changing it. Found: the how-to
  card sat above the search box; the panel opened on the oldest years, so on a phone a 2002-2016 table showed
  2002-2004; the asked region's value was not pulled out; an old archive table ranked first without any sign it was
  old; the desktop panel dimmed the list it belongs to. Radikal chose "answer-first" over a visual refresh or
  guided steps (steps would drop the free-text rewrite and region matching).
- Changes: headline + search first with a short "Cara pakai" card below (first visit, remembered, reopened by ?);
  "Paling cocok" tag on the first result unless it is old; "Data lama" tag when the newest year is more than 2
  years back (`OLD_AFTER_YEARS`), with "Tahun terakhir di judul: N" so the source of the year is clear; answer
  strip at the top of the panel: the asked region's row, last three columns with a value, cells copied as given;
  a table with years across opens on its newest year (only if the years ascend); desktop: panel beside the list
  (no dimming layer, `aria-modal` false), phone keeps the bottom sheet.
- API: results carry `latest_year` (`src/retrieval/period.latest_year`: newest year in the title, or the years BPS
  has a Dalam Angka table for). 98% of archive tables have a year in the title, only 2% of dynamic tables, so the
  tag mostly covers archive tables. A title year that is a base year (not a period) could in rare cases show a
  wrong "Tahun terakhir"; the card says where the year comes from.
- Tests: 11 browser steps pass. Mutation checks: no scroll to newest, answer strip taking the first three
  columns, no old tag, desktop without the side layout each fail a step. The first answer-strip assertion used a
  6-column fixture and could not tell first from last three columns; it now also checks the 15-column archive
  table.
- Open: kab/kota Dalam Angka link format still unverified; (12) rank tables with an old newest year lower when the
  question names no year (Garut question puts a 2002-2016 table first).

## 2026-11-04: web page ideas after the redesign (all open, ranked by value for cost)

Before deploy: (13) slow-server message after ~5 s (Cloud Run cold start 15-30 s is an estimate, not measured);
(14) "Cocok?" Ya/Tidak buttons per result, logged with question + doc_id, no IP, rate limited: real labels for the
next golden set. Cheap: (15) "Salin kutipan" button (BPS website terms section 13 require credit with title,
access date, direct link); (16) CSV download of the shown table, cells as given; (17) `?q=...&buka=<id>` link that
opens a table. Bigger: (18) small chart of the asked region's row for years-across tables (numbers parsed from
"1.110,92" for drawing only, needs a parse test); (19) a region dropdown to correct a wrongly recognised region.
Low: light/dark toggle (page follows the device setting, no switch), panel focus trap, recent searches, English.
Outside the page: idea 12 (rank old tables lower).

## 2026-11-04: ideas 10, 12, 13

- (13) done: the page shows "Servernya baru bangun..." when a search takes over 5 s (`SLOW_AFTER_MS`), cleared when the
  answer arrives. Browser step added; fails if the timer is never cleared (it overwrote the result count) or the
  threshold is raised to 50 s.
- (10) blocked: `/v1/api/list/model/glosarium/key/{key}` returned HTTP 500 `{"status":"Error","message":"This service is
  currently unavailable"}` with no parameters, with `prefix=t`, and with `prefix=t&perpage=500` (3 calls, 3 s apart). Not
  our parameters; retry on another day before dropping. Not built: nothing to put in the prompt without the entries.
- (12) dropped: demoting tables whose newest title year is older than today minus 2 (no year in the question), measured
  on the 88-question set with the cached rewrite (baseline R@5 0.977, MRR 0.831): all old-year tables, factor 0.85 ->
  0.966 / 0.812, 0.7 -> 0.955 / 0.810; archive tables only (`statictable`), 0.85 -> 0.977 / 0.821, 0.7 -> 0.966 / 0.820.
  The Garut question improved (archive "2002-2016" tables left the top 5), but 4-5 golden questions gained one rank and
  1-2 lost their top-1, because their golden answer is an old table ("2008 - 2017" visitors; a regional-revenue archive).
  Old tables are valid answers, so the page keeps the "Data lama" tag and does not mark an old table "Paling cocok".
  Reopen if real feedback (idea 14) shows people skipping old tables.

## 2026-11-04: idea 14, "Hasil ini cocok?" Ya/Tidak per result

- `POST /api/feedback` {q, doc_id, verdict ya|tidak} -> 204 and one stdout log line (`event: feedback`), like searches: no IP.
  doc_id must be in the catalog (404 otherwise); per-IP limit shared with search (20/min) plus a global 200/min cap.
  CORS now allows POST and the Content-Type header. The page footer says questions and ratings are logged without identity.
- Probe found a bug: a body of `NaN` returned 500, because FastAPI's 422 reply echoes the input and nan cannot be encoded.
  Fixed with a `RequestValidationError` handler that returns only loc + msg; NaN, Infinity, `[1]`, empty body now give 422.
  With 230 spoofed client IPs: 200 x 204, then 30 x 429 (the global cap works).
- Logs are the only store: Cloud Run keeps stdout in Cloud Logging for a default retention (30 days, unverified). Export the
  `feedback` and `search` events to a file before they expire (part of the refresh script) or the labels are lost.
- Unverified before deploy: the per-IP limit trusts the first X-Forwarded-For entry, which a caller can set; the global
  cap is what protects the log volume.

## 2026-11-04: ideas 15-17 in the table panel

- (15) "Salin Kutipan": `"<table title>", Badan Pusat Statistik, diakses <date, Asia/Jakarta> dari <BPS link>` (title, access date and
  direct link, as the website terms ask). Hidden when the table has no BPS link. Panel only: publications and press
  releases have no panel, so they have no citation button yet.
- (16) "Unduh CSV": the shown table, cells as BPS gave them, separated by `;` (CSV_SEPARATOR) with a BOM: Excel in an Indonesian
  locale splits on `;` because `,` is its decimal mark. pandas needs `sep=";"`. A cell that starts with `= + - @` and is not a number
  (or a lone "-") gets a `'` in front so a spreadsheet does not run it as a formula.
- (17) "Salin Tautan": `?q=<question>&buka=<doc_id>`. The search runs first (the asked region is highlighted), then the panel
  opens; a link with only `buka` opens the table without searching. The period is not in the link.
- Browser clipboard needs `clipboard-sanitized-write` as well as `clipboard-write` in the test's permission override. Running the
  browser suite while the catalog refresh was loading the machine crashed Chrome ("Connection closed"): run them one at a time.

## 2026-11-04: BPS Dalam Angka (simdasi) table pages fail to load

- Radikal opened a BPS-supplied Jawa Barat Dalam Angka link in a normal browser: "Gagal Memuat Tabel. Silakan coba beberapa saat lagi.
  (Error: Error Unknown)". The built Kota Bandung link failed the same way. So the failure is BPS's page, not our kab/kota link
  format, and the format cannot be verified while it lasts. Plain curl and headless Chrome are no use as a check: curl gets the same
  error shell for every link, and the anti-bot layer refuses headless Chrome (HTTP 520 from /TSPD/).
- Decision: change nothing on the page. "Lihat Angkanya" shows the numbers from the API, which does not depend on that page;
  kab/kota Dalam Angka cards keep having no BPS link. Retry in a browser on another day; if the BPS pages load again, check the
  built kab/kota link then. Untested: whether dynamic-table (var) links open.

## 2026-11-04: catalog refresh script and the first eval report

- `scripts/refresh.sh [recent|all]`: `pull_catalog --refresh` (recent = current-year publication and press-release lists;
  all = every page, resumable through `data/raw/catalog/refresh_started`), build the catalog, show added/removed rows by type,
  run `evals.run_eval --smoke` (fails below Recall@5 0.947 = 0.977 minus 3 points, then the previous catalog is put back), and
  rebuild `docs/eval-report.html`. First real run: 74,938 -> 74,945 rows (6 publications, 1 press release added, none removed),
  smoke 0.977. Not in the script yet: the bucket upload and the Cloud Logging export of `search`/`feedback` events (deploy).
- Eval report: every `run_eval` run saves its questions to `data/processed/eval_results.parquet` and appends one row per method to
  `evals/history.csv` (58 rows backfilled from the old text outputs, no intervals for those). `evals/report.py` builds the HTML with
  bootstrap 95% intervals and paired comparisons of each step.
- Finding: hybrid vs BM25 + region alone is -2.3 points (interval -6.8 to +2.3), and embeddings on top of rewrite + BM25 are
  +3.4 points (-1.1 to +9.1): both within noise on these 88 questions. Region ranking (+31.8) and the rewrite (+14.8) are clear.
  The embedding model costs the Cloud Run image size and cold start, so whether to ship it is open until real questions
  (idea 14 ratings) can settle it. MRR differences were not tested.

## 2026-11-04: first deploy

- GCP project `bps-data-finder` (personal account, billing "My Billing Account 1"; the Rp 20,000 budget alert has no project
  filter, so it covers this project too). Free tiers of Cloud Run and Artifact Registry are per billing account, shared with
  the jabodetabek project (pricing pages could not be read in full: unverified). CLI through `./gcloud.sh` (copy of the
  jabodetabek wrapper, login in `.gcloud/`, refuses project commands unless the account is the personal one).
- Image: CPU-only torch 2.15.0 (installed before the other locked packages: installing it after let sentence-transformers pull the
  NVIDIA build), embedding model baked in, `HF_HUB_OFFLINE=1`. 739 MB compressed, built by Cloud Build in 2 min 45 s. Catalog,
  embeddings and the two region lists in the private bucket `bps-data-finder-data`, mounted read-only at /app/data.
- Cloud Run `api`: max 1 instance (the BPS spacing is in memory), 2 GiB, 1 vCPU, CPU boost, min 0, service account `api-runtime`
  (bucket objectViewer, accessor on the two secrets only). Cold start 53 s (mount <1 s, imports + catalog + BM25 ~41 s, model <1 s,
  embeddings ~12 s); the page's timeout went from 45 s to 90 s. Speed-up candidates: vectors as .npy, BM25 index saved.
- Limits before going public: the per-client key is the last X-Forwarded-For entry (Cloud Run appends the address it saw; a forged
  first entry did not lift the limit on the live service), global caps search 120 / value 60 / feedback 200 a minute.
- Gemini free tier on 2026-11-04 evening: 3.5-flash-lite 14-40 s or 504, other Flash models mostly 503; a 2-minute cooldown after a
  failure keeps searches fast (without the rewrite, R@5 0.83 instead of 0.977). Re-measure and consider `gemini-3.5-flash`
  (2 of 5 calls ok at about 2.5 s) once it answers; a model change needs a new eval run.
- Netlify site `cari-data-bps` was created with Netlify login protection on (`sso_login: true`, every visitor got 401): turned
  off through the API. Live checks: `scripts/check_live.py` (14 checks) and `tests/e2e/live.mjs` (desktop and phone) pass.
