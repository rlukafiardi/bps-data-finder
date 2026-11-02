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
cp .env.example .env   # add BPS_API_KEY
```

Entry points come with the first pipeline step.
