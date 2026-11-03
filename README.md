# BPS Data Finder

Ask for a statistic in plain Bahasa Indonesia or English and get a ranked list of where it lives on
bps.go.id: dynamic table, static table, publication (with table number and page) or press release.
It points to sources and does not answer with numbers.

## Status

POC: does hybrid retrieval over the BPS WebAPI catalog beat bps.go.id's own search? See `CLAUDE.md`.

## Data sources

- BPS WebAPI (webapi.bps.go.id): catalog of variables, static tables, publications and press releases per
  region code. Needs a free API key. Terms and rate limits not yet verified.

## How to run

```bash
uv sync
cp .env.example .env   # add BPS_API_KEY; GEMINI_API_KEY (aistudio.google.com) for the LLM rewrite
uv run python -m src.ingestion.pull_catalog    # resumable, ~20 requests/min
uv run python -m src.ingestion.build_catalog   # -> data/processed/catalog.parquet
uv run python -m evals.run_eval                # Recall@5 / MRR per method
uv run uvicorn app.main:app --port 8000        # API: /api/search?q=..., /api/value?doc_id=...
uv run pytest -q tests
npm install && npm run test:e2e                # page in real Chrome against a fake API
npm run serve -- 8080 http://localhost:8000    # the page on http://localhost:8080
```

This service uses the Badan Pusat Statistik (BPS) API.
