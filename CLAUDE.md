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
- Grain / key tables (probed 2026-11-02, `src/ingestion/probe_api.py`): one row per catalog item.
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
  `load_dotenv()` fails from stdin scripts: pass `.env` explicitly.

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

- 2026-11-02: Golden set v0: 30 questions drafted by Claude (`source=claude`), labelled with keyword filters,
  then pooled judging of all methods' top 5 under one rule (asked statistic at asked breakdown). Pass / stop
  is judged on Radikal's real questions (`source=radikal`), not on these.
- 2026-11-02: SIMDASI kab/kota lists (47 tables) are a subset of the printed Dalam Angka: rainfall (Kota Bekasi),
  hospitals (Depok), rice production (Kab Karawang) have no table there. PDF route may come back for kab/kota.

## Status
- Works: catalog builder, region lookup (`src/retrieval/regions.py`), BM25, dense (multilingual-e5-small),
  RRF hybrid, region-aware ranking, eval (`uv run python -m evals.run_eval`).
- Results on drafted set, partial catalog (national + 1100-1600 + Jabar SIMDASI), R@5 / MRR:
  bm25 0.57/0.43, bm25+region 0.80/0.72, dense 0.63/0.40, dense+region 0.83/0.59, hybrid+region 0.83/0.75.
  Region ranking is the big gain. Misses: English questions, acronyms (IPM), short exact titles.
- Next: catalog pull (`uv run python -m src.ingestion.pull_catalog`, resumable) -> build parquet;
  Radikal fills `evals/golden_set.csv` (~50 questions, see `evals/README.md`).
- Ideas: (1) finder-first [done: decided] (2) unified catalog index [open] (3) Dalam Angka table index via
  SIMDASI [open; PDF route dropped]
  (4) hybrid BM25 + embeddings [open] (5) LLM query parsing + domain gazetteer [open] (6) fallback
  kab/kota -> province / Dalam Angka [open] (7) fetch values verbatim (var data, SIMDASI 25 [tested OK], statictable view) [open, after POC]
  (8) MCP server or web page [open, after POC]
