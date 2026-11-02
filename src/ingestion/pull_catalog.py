"""Pull the BPS WebAPI catalog for the POC slice into data/raw/catalog/, one JSON file per page.

Resumable: a page already on disk is never fetched again. Stops at the first 401/403, after
repeated 429/5xx, or at the wall-clock limit; rerun to continue.

    uv run python -m src.ingestion.pull_catalog [--minutes 40]
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

PROVINCE = "3200"
DOMAINS = ["0000", PROVINCE]
MODELS = ["var", "statictable", "publication", "pressrelease"]
DATED_MODELS = {"publication", "pressrelease"}  # pulled for YEARS only
YEARS = [2025, 2026]
DELAY_S = 3.0
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
            status = type(e).__name__
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
        time.sleep(DELAY_S * 2 ** (attempt + 1))
    raise Stop(f"still failing after {RETRIES} tries ({status}) on {path}")


def pages(body):
    data = body.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0].get("pages", 1)
    return 0  # "data-availability": "list-not-available"


def main(minutes):
    deadline = time.monotonic() + minutes * 60
    RAW.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        base_url=BASE, timeout=60, headers={"User-Agent": "bps-data-finder/0.1 (personal research)"}
    ) as client:
        kabs = get(client, "/api/domain/type/kabbyprov/key/{key}", {"prov": PROVINCE}, RAW / "domains_kab.json")
        for domain in [PROVINCE] + [d["domain_id"] for d in kabs["data"][1]]:
            get(
                client,
                f"/api/interoperabilitas/datasource/simdasi/id/23/wilayah/{domain}000/key/{{key}}",
                {},
                RAW / "simdasi" / f"{domain}.json",
            )
        print("simdasi table lists done", flush=True)

        for domain in DOMAINS:
            for model in MODELS:
                path = f"/api/list/model/{model}/domain/{domain}/key/{{key}}"
                for year in YEARS if model in DATED_MODELS else [None]:
                    params = {"year": year} if year else {}
                    folder = RAW / domain / model / (str(year) if year else "all")
                    first = get(client, path, {"page": 1, **params}, folder / "p0001.json")
                    n = pages(first) if first else 0
                    for page in range(2, n + 1):
                        if time.monotonic() > deadline:
                            raise Stop("wall-clock limit reached, rerun to resume")
                        get(client, path, {"page": page, **params}, folder / f"p{page:04d}.json")
                    print(f"{domain} {model} {year or 'all'}: {n} pages", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=40)
    try:
        main(parser.parse_args().minutes)
    except Stop as e:
        print("STOP:", e, file=sys.stderr)
        sys.exit(1)
