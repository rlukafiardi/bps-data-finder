# BPS Data Finder

## Goal
Locate where a BPS statistic lives (dynamic table, static table, publication table + page, press release)
from a plain-language question. Returns pointers with links, never generated numbers.
Success measured by: Recall@5 and MRR on a golden question set, against bps.go.id site search.

POC: can retrieval over the BPS WebAPI catalog (+ publication table lists) put the correct source in the
top 5, better than the site search?
- Slice: domain 0000 (national) + one province (e.g. 3200 Jawa Barat) and its kab/kota; vars, static tables,
  press releases, publications from the last 2 years (table lists for ~20 "Dalam Angka" PDFs).
  ~50 golden questions written by Radikal from real past searches.
- Method: BM25 vs multilingual embeddings vs hybrid (in-memory numpy), no generation; then LLM query
  parsing (indicator / region / period, acronym expansion, place name -> domain code) as one variant.
- Pass: hybrid + parsing Recall@5 >= 0.70 and >= 15 points above the site-search baseline.
  Stop / rethink: site search already close, or catalog text too thin (titles only).
- Risks, riskiest first: API key + terms + rate limits; publication PDFs available and table lists
  extractable; var region/period coverage; catalog size and freshness; golden set quality.
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
- Grain / key tables: TBD
- Known quirks: none yet

## Decisions
- 2026-11-02: Project created. Type: llm. Tools: uv, httpx, pandas, pyarrow, python-dotenv; in-memory numpy
  vectors for the POC (vector store chosen after it passes). Embeddings / BM25 / pdfplumber added when used.
- 2026-11-02: Finder, not answerer: results are source pointers so the LLM cannot invent statistics.

## Status
- Works: scaffold only.
- Next: API key (waiting on BPS approval); then one call per model for domain 0000 (print keys + fields),
  check search endpoint as baseline and whether SIMDASI replaces PDF table extraction.
- Ideas: (1) finder-first [open] (2) unified catalog index [open] (3) publication table-list index [open]
  (4) hybrid BM25 + embeddings [open] (5) LLM query parsing + domain gazetteer [open] (6) fallback
  kab/kota -> province / Dalam Angka [open] (7) fetch values for dynamic tables [open, after POC]
  (8) MCP server or web page [open, after POC]
