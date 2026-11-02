"""Pull the BPS WebAPI catalog into data/raw/catalog/, one JSON file per page.

1. national + all provinces: tables from the search endpoint (100 rows/page, more tables than the list
   endpoints); publications and press releases from the list endpoint per year (search returns
   "list-not-available" for them, or for publications outside 0000)
2. SIMDASI (Dalam Angka) table lists for all provinces and kab/kota
3. var lists with notes for NOTES_DOMAINS (list endpoints are fixed at 10 rows/page)

Resumable: a page already on disk is never fetched again. Stops at the first 401/403, after
repeated 429/5xx, or at the wall-clock limit; rerun to continue.

    uv run python -m src.ingestion.pull_catalog [--minutes 120]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(".env")
KEY = os.environ["BPS_API_KEY"]
BASE = "https://webapi.bps.go.id/v1"
RAW = Path("data/raw/catalog")
LOG = RAW / "requests.log"

YEARS = [2025, 2026]  # publications and press releases
NOTES_DOMAINS = ["0000", "3200"]
DELAY_S = 3.0  # BPS returns 429 after ~20 requests/minute
RATE_LIMIT_WAIT_S = 65
RETRIES = 3


class Stop(Exception):
    pass


def log(path, status):
    with LOG.open("a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()}\t{status}\t{path}\n")


def get(client, path, params, out):
    """Fetch path (with {key}) to out unless cached; return the parsed JSON, or None if gone."""
    if out.exists():
        return json.loads(out.read_text())
    for attempt in range(RETRIES):
        time.sleep(DELAY_S)
        try:
            resp = client.get(path.format(key=KEY), params=params)
            status = resp.status_code
        except httpx.TransportError as e:
            resp, status = None, type(e).__name__
        log(f"{path}?{params}", status)
        if status == 200:
            body = resp.json()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(body, ensure_ascii=False))
            return body
        if status in (401, 403):
            raise Stop(f"HTTP {status} on {path}")
        if status in (404, 410):
            return None
        if status == 429:
            time.sleep(int(resp.headers.get("retry-after", RATE_LIMIT_WAIT_S)))
        else:
            time.sleep(DELAY_S * 2 ** (attempt + 1))
    raise Stop(f"still failing after {RETRIES} tries ({status}) on {path}")


def pages(body):
    data = body.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0].get("pages", 1)
    return 0  # "data-availability": "list-not-available"


def pull_pages(client, path, params, folder, deadline):
    first = get(client, path, {"page": 1, **params}, folder / "p0001.json")
    n = pages(first) if first else 0
    for page in range(2, n + 1):
        if time.monotonic() > deadline:
            raise Stop("wall-clock limit reached, rerun to resume")
        get(client, path, {"page": page, **params}, folder / f"p{page:04d}.json")
    return n


def main(minutes):
    deadline = time.monotonic() + minutes * 60
    RAW.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        base_url=BASE, timeout=60, headers={"User-Agent": "bps-data-finder/0.1 (personal research)"}
    ) as client:
        provs = get(client, "/api/domain/type/prov/key/{key}", {}, RAW / "domains_prov.json")
        provinces = [d["domain_id"] for d in provs["data"][1]]

        for domain in ["0000"] + provinces:
            path = f"/searching/content/domain/{domain}/model/tablestatistic/key/{{key}}"
            n = pull_pages(client, path, {"perpage": 100}, RAW / "search" / domain / "tablestatistic", deadline)
            print(f"search {domain} tablestatistic: {n} pages", flush=True)
            for model in ["publication", "pressrelease"]:
                for year in YEARS:
                    path = f"/api/list/model/{model}/domain/{domain}/key/{{key}}"
                    n = pull_pages(client, path, {"year": year}, RAW / domain / model / str(year), deadline)
                    print(f"{model} {domain} {year}: {n} pages", flush=True)

        # one list of all kab/kota: `kabbyprov?prov=` started returning Aceh for every province (2026-11-02)
        kabs = get(client, "/api/domain/type/kab/key/{key}", {}, RAW / "domains_kab.json")
        kab_ids = [d["domain_id"] for d in kabs["data"][1]]
        for prov in provinces:
            prov_kabs = [k for k in kab_ids if k[:2] == prov[:2]]
            for domain in [prov] + prov_kabs:
                if time.monotonic() > deadline:
                    raise Stop("wall-clock limit reached, rerun to resume")
                get(
                    client,
                    f"/api/interoperabilitas/datasource/simdasi/id/23/wilayah/{domain}000/key/{{key}}",
                    {},
                    RAW / "simdasi" / f"{domain}.json",
                )
            print(f"simdasi {prov}: {len(prov_kabs) + 1} table lists", flush=True)

        for domain in NOTES_DOMAINS:
            path = f"/api/list/model/var/domain/{domain}/key/{{key}}"
            n = pull_pages(client, path, {}, RAW / domain / "var" / "all", deadline)
            print(f"var notes {domain}: {n} pages", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=120)
    try:
        main(parser.parse_args().minutes)
    except Stop as e:
        print("STOP:", e, file=sys.stderr)
        sys.exit(1)
