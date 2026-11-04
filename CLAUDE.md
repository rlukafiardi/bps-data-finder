# BPS Data Finder

## Goal
Locate where a BPS statistic lives (dynamic table, static table, Dalam Angka table, publication, press release)
from a plain-language question, and later return the value. The LLM picks the source; numbers are only ever
copied from API responses, never generated.
Success measured by: Recall@5 and MRR on a golden question set, against bps.go.id site search.

POC: can retrieval over the BPS WebAPI catalog (+ SIMDASI Dalam Angka table lists) put the correct source
in the top 5, better than the site search?
- Slice: domains 0000 (national) + 3200 (Jawa Barat): vars, static tables, publications and press releases
  from 2025-2026; SIMDASI table lists for 3200 and all 27 kab/kota. No kab/kota catalogs: kab/kota questions
  are answered by province tables "menurut kabupaten/kota" or SIMDASI.
  ~50 golden questions written by Radikal from real past searches.
- Method: BM25 vs multilingual embeddings vs hybrid (in-memory numpy), no generation; then LLM query
  parsing (indicator / region / period, acronym expansion, place name -> domain code) as one variant.
- Pass: hybrid + parsing Recall@5 >= 0.70 and >= 15 points above the site-search baseline.
  Stop / rethink: site search already close, or catalog text too thin (titles only).
- Risks, riskiest first: API key + terms + rate limits [cleared 2026-11-02]; SIMDASI coverage vs the printed
  Dalam Angka; var region/period coverage; thin statictable text; golden set quality.
- Out of scope until it passes: value fetching, UI / MCP server, all 514 kab/kota, scheduled refresh, deployment.

## Data
- Sources: BPS WebAPI (webapi.bps.go.id, spec at /documentation/openapi.yaml). Key in the path:
  `/v1/api/list/model/{var|statictable|publication|pressrelease|subject|...}/domain/{domain}/key/{key}`,
  `/v1/api/view/domain/{d}/model/{m}/lang/{lang}/id/{id}/key/{key}`, `/v1/api/domain/type/{type}` (region list),
  `/v1/searching/content/domain/{d}/model/{m}` (BPS's own search: usable as the automatic baseline),
  `interoperabilitas/datasource/simdasi/...` (SIMDASI regional tables, may cover "Dalam Angka" without PDF parsing).
- Terms (excerpts read, full text unverified): key must stay private; non-commercial unless authorized;
  rate limited, no numbers published, no multiple keys/IPs to get around it; apps must show
  "This service uses the Badan Pusat Statistik (BPS) API." Key issued after BPS approves the application.
- Grain / key tables (probed 2026-11-02 with a one-off script, removed; see git history): one row per catalog item.
  Domain 0000: var 1766, statictable 722, publication 5975, pressrelease 2421. Domain 3200: var 612, statictable 503.
  Jabar has 27 kab/kota domains (`domain/type/kabbyprov?prov=3200`).
- Text per item: var has title + def + notes + unit + subject; statictable title + subject only (thin);
  publication and pressrelease have abstract + pdf link; search returns title + body + relevance.
- SIMDASI (Yearbook Dataset = Dalam Angka): service 23 lists tables per 7-digit MFD area (`3200000`):
  id_tabel, kode_tabel (e.g. 1.1.1), judul / judul_en, bab, ketersediaan_tahun. Jabar 153 tables,
  Kota Bandung and Kab Bogor 47 each. Whether that covers the full printed book is unverified.
- Known quirks: envelope is `data: [paging, rows]`; SIMDASI nests a second envelope in `data[1]` with rows
  in `data[1].data`. List endpoints return 10 rows per page, fixed (perpage/per_page/limit ignored).
  Kab/kota catalogs are large (Kota Bandung: var 2506, statictable 4701). Rate limit ~20 requests/min
  (429 after 22 requests at 1/s; 3 s spacing is clean). Search: perpage works (100), category 1 = statictable,
  2 = var, 3 = SIMDASI (url id = base64 of "<id>#<cat>", or of id_tabel for 3), more tables than the lists;
  but pagination is unstable: items repeat across pages and others never show (0-13% missing per domain).
  Search returns nothing for press releases, and for publications outside 0000: use list + `year`. Titles carry HTML (`<sup>`, `<i>`). `domain/type/prov` returns 34 provinces, not 38.
  `load_dotenv()` fails from stdin scripts: pass `.env` explicitly. `domain/type/kabbyprov?prov=` returned
  Aceh for every province from 2026-11-02 evening: use `domain/type/kab` (all 514) and group by code prefix.

## Decisions
- 2026-11-02: Project created. Type: llm. Tools: uv, httpx, pandas, pyarrow, python-dotenv; in-memory numpy
  vectors for the POC (vector store chosen after it passes). Embeddings / BM25 / pdfplumber added when used.
- 2026-11-02: The LLM picks the source, never the number. Values come verbatim from the API (var data,
  SIMDASI service 25, statictable view) with source, year and footnotes. PDF-only tables: pointer + page,
  any extracted preview labelled unverified. POC tests finding only; value fetching is phase 2.
- 2026-11-02: Slice is national + province only: all 27 Jabar kab/kota catalogs would be ~19k requests
  (~16 h at 3 s); this slice is ~480 requests. All 34 provinces: ~4,600 requests if needed later.
- 2026-11-02: SIMDASI table lists replace PDF table-list extraction (no pdfplumber in the POC). PDF
  extraction comes back only if golden questions miss tables that are in the book but not in SIMDASI.

- 2026-11-02: Golden set v0: 30 questions drafted by Claude (`source=claude`) + 40 seeded from a random
  catalog sample (`source=claude-seeded`), labelled with keyword filters,
  then pooled judging of all methods' top 5 under one rule (asked statistic at asked breakdown). Pass / stop
  is judged on Radikal's real questions (`source=radikal`), not on these.
- 2026-11-02: SIMDASI kab/kota lists (47 tables) are a subset of the printed Dalam Angka: rainfall (Kota Bekasi),
  hospitals (Depok), rice production (Kab Karawang) have no table there. PDF route may come back for kab/kota.
- 2026-11-02: LLM rewrite = Gemini API free tier, `gemini-3.5-flash-lite` (free; prompts may be used by
  Google, fine for public-statistics questions). Rewrite returns an Indonesian BPS-style query + region;
  search uses question + rewrite. Cached per model/prompt/question. Prompt examples must not come from
  eval questions (v2 swapped leaked examples for neutral ones).
- 2026-11-03: POC passed: rewrite+hybrid+region R@5 0.93 vs BPS search 0.19 (+74 points; brief asked
  >= 0.70 and >= 15 points). Judged on the 70 Claude-written questions only: Radikal chose not to add real
  ones (accepted risk: real searches are messier). Collect real queries once there is a user-facing app. Search
  coverage: second pass at 50/page cut dropped tables from 8.1% to 0.7%; BPS search API returns nothing
  for most full-sentence queries (199/210 empty), so the baseline is the keyword+retry variant.

## Status
- Works: catalog builder, region lookup (`src/retrieval/regions.py`), BM25, dense (multilingual-e5-small),
  RRF hybrid, region-aware ranking, eval (`uv run python -m evals.run_eval`).
- Results on the complete catalog (74,938 rows), 88 Claude-written questions, pooled judging, R@5 / MRR:
  BPS search literal 0.09/0.09 and keywords+retry 0.19/0.15 (measured on the first 70 questions,
  `evals/site_search_baseline.py`), bm25+region 0.85/0.68, hybrid+region 0.82/0.70,
  rewrite v2+hybrid+region 0.98/0.83 (`data/processed/eval_period_final.txt`). Misses: "garis kemiskinan
  provinsi" (rank 8), "harga sembako di pematangsiantar" (rank 7).
- Next (full build, plan approved 2026-11-03; log in `docs/decisions-log.md`): done: risks 1-4, search API,
  values API, region filter (rewrite+hybrid+region R@5 0.93 / MRR 0.70 on 75 q), web page `web/` (local;
  `uv run pytest -q tests`, `npm run test:e2e`). Not registered as a BPS application (Radikal's call). Refresh script and eval report done (`scripts/refresh.sh`,
  `docs/eval-report.html`). Architecture diagram done (`docs/architecture.py`; update it when a component, store or flow changes).
- Live since 2026-11-04: https://cari-data-bps.netlify.app (Netlify `cari-data-bps`, token copied from the jabodetabek
  project), API https://api-823141605435.asia-southeast2.run.app (Cloud Run `api`, GCP project `bps-data-finder`, personal
  account via `./gcloud.sh`, max 1 instance, 2 GiB, catalog bucket `bps-data-finder-data` mounted read-only, keys in Secret
  Manager). Cold start 53 s. Deploy steps in the README; after every deploy `scripts/check_live.py` and `node tests/e2e/live.mjs`.
- Next (from 2026-11-05): recheck a Dalam Angka link in a browser (BPS's statistics-table/3 pages failed on 11-04, BPS-supplied
  links included; if they still fail, add a note on those results; if they work, try the kab/kota link to enable 23,598 links);
  re-measure Gemini (free tier 503/504 on 11-04; candidate `gemini-3.5-flash`, needs an eval run); read billing after a day of
  keep-warm pings (`api-keep-warm`, every 5 min); cold-start speed-up (vectors as .npy, saved BM25 index).
- Ideas: (1) finder-first [done] (2) unified catalog index [done] (3) Dalam Angka index via SIMDASI
  [done for lists; PDF route dropped] (4) hybrid BM25 + embeddings [done] (5) LLM query rewrite + region
  gazetteer [done: Gemini free tier, prompt v2] (6) fallback kab/kota -> province -> national [done:
  region filter + kab/kota name stripping] (7) fetch values verbatim (var data, SIMDASI 25, statictable view)
  [done: `src/values/`, `/api/value`] (8) web page [done, local; redesigned answer-first 2026-11-04; MCP server dropped] (9) period matching (month / quarter /
  year in the question vs title) [done] + BM25 title weight 5 [done] (10) BPS glosarium endpoint as acronym list [blocked 2026-11-04: endpoint returns HTTP 500 "service is currently unavailable"; retry later] (11) page numbers in publications: read the 80
  yearbook PDFs (1.1 GB; all 3,649 are 36 GB) [parked 2026-11-04: pilot works on one book, value unmeasured, see decisions log] (12) rank tables with an old newest year lower when the question names no year [dropped 2026-11-04: no eval gain, see decisions log] (13) slow-server message [done 2026-11-04]; (14) Cocok? feedback buttons [done 2026-11-04]; (15) copy citation, (16) CSV, (17) open-table link [done 2026-11-04]; (18-19) web ideas: chart, region dropdown [open, ranked in decisions log] (20) a note on BPS numbers that look odd (e.g. DIY hotel rooms), never a correction [open]
