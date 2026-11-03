"""Search API for the BPS data finder: question -> top 5 BPS sources with public links.

    ALLOWED_ORIGINS=http://localhost:8080 uv run uvicorn app.main:app --port 8000
"""

import json
import os
import time
from collections import defaultdict, deque

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from src.retrieval.bm25 import BM25
from src.retrieval.dense import Dense, Hybrid
from src.retrieval.region_rank import RegionRank
from src.retrieval.regions import domains, find_regions
from src.retrieval.rewrite import Rewriter
from src.values.bps import Busy, BpsError
from src.values.tables import mark_regions, simdasi_table, static_table, var_table

CATALOG = "data/processed/catalog.parquet"
SEARCHES_PER_MINUTE = 20  # per client IP
TYPE_LABELS = {
    "var": "Tabel dinamis",
    "statictable": "Tabel statis",
    "simdasi": "Tabel Daerah Dalam Angka",
    "publication": "Publikasi",
    "pressrelease": "Berita Resmi Statistik",
}

catalog = pd.read_parquet(CATALOG)
by_id = catalog.set_index("doc_id", drop=False)
search = RegionRank(Hybrid(BM25(catalog), Dense(catalog)))
rewriter = Rewriter(serving=True)
recent = defaultdict(deque)

app = FastAPI(title="BPS Data Finder")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:8080").split(","),
    allow_methods=["GET"],
)


def over_limit(request):
    # Cloud Run puts the client first in X-Forwarded-For
    ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
    now = time.monotonic()
    calls = recent[ip]
    while calls and calls[0] < now - 60:
        calls.popleft()
    if len(calls) >= SEARCHES_PER_MINUTE:
        return True
    calls.append(now)
    return False


def result(row):
    return {
        "doc_id": row["doc_id"],
        "type": row["type"],
        "type_label": TYPE_LABELS[row["type"]],
        "title": row["title"],
        "region": domains()[row["domain"]]["name"],
        "date": row["date"],
        "years": row["years"].tolist() if row["years"] is not None else None,  # SIMDASI only, numpy array
        "table_code": row["table_code"],
        "url": row["url"],
        "url_built": row["url_built"],
    }


@app.get("/api/search")
def api_search(request: Request, q: str = Query(min_length=2, max_length=200)):
    if over_limit(request):
        raise HTTPException(429, "Terlalu banyak pencarian. Coba lagi sebentar.")
    rewrite = rewriter.rewrite_or_none(q)
    text = " ".join(p for p in (q, rewrite["query"], rewrite["region"]) if p) if rewrite else q
    hits = search.search(text, k=5)
    hits = hits.astype(object).where(hits.notna(), None)
    # question text only, no IP: real queries become the next golden set
    print(json.dumps({"event": "search", "q": q, "rewrite": rewrite is not None, "results": hits["doc_id"].tolist()}), flush=True)
    return {
        "question": q,
        "rewrite": rewrite,
        "regions": [{"id": d, "name": domains()[d]["name"]} for d in find_regions(text)],
        "results": [result(r) for r in hits.to_dict("records")],
    }


@app.get("/api/value")
def api_value(
    request: Request,
    doc_id: str = Query(max_length=120),
    period: str | None = Query(None, max_length=10),
    regions: str = Query("", max_length=60),
):
    """The table behind one search result, as BPS gives it. Publications and press releases are links only."""
    if doc_id not in by_id.index:
        raise HTTPException(404, "Tabel tidak ditemukan.")
    if over_limit(request):
        raise HTTPException(429, "Terlalu banyak permintaan. Coba lagi sebentar.")
    row = by_id.loc[doc_id]
    try:
        if row["type"] == "var":
            table = var_table(row["domain"], row["source_id"], period)
        elif row["type"] == "simdasi":
            table = simdasi_table(row["domain"], row["source_id"], [int(y) for y in row["years"]], period)
        elif row["type"] == "statictable":
            table = static_table(row["domain"], row["source_id"])
        else:
            raise HTTPException(400, "Publikasi dan Berita Resmi Statistik hanya berupa tautan ke BPS.")
    except ValueError:
        raise HTTPException(400, "Periode tidak tersedia.")
    except Busy:
        raise HTTPException(429, "Sedang ramai. Coba lagi sebentar.")
    except BpsError as e:
        print(json.dumps({"event": "bps_error", "doc_id": doc_id, "error": str(e)}), flush=True)
        raise HTTPException(502, "BPS belum menjawab. Coba lagi nanti.")
    table["fetched_at"] = pd.Timestamp(table["fetched_at"], unit="s", tz="UTC").isoformat(timespec="seconds")
    print(json.dumps({"event": "value", "doc_id": doc_id, "period": table["period"]}), flush=True)
    return {
        "doc_id": doc_id,
        "type": row["type"],
        "url": row["url"],
        **mark_regions(table, [d for d in regions.split(",") if d in domains()]),
    }
