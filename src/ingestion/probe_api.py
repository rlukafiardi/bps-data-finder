"""One call per BPS WebAPI endpoint the POC needs; prints the response shape, never the key."""

import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ["BPS_API_KEY"]
BASE = "https://webapi.bps.go.id/v1"

CALLS = {
    "domains_prov": ("/api/domain/type/prov/key/{key}", {}),
    "subject": ("/api/list/model/subject/domain/0000/key/{key}", {}),
    "var": ("/api/list/model/var/domain/0000/key/{key}", {}),
    "statictable": ("/api/list/model/statictable/domain/0000/key/{key}", {}),
    "publication": ("/api/list/model/publication/domain/0000/key/{key}", {}),
    "pressrelease": ("/api/list/model/pressrelease/domain/0000/key/{key}", {}),
    "search_tablestatistic": (
        "/searching/content/domain/0000/model/tablestatistic/key/{key}",
        {"page": 1, "keyword": "tingkat+pengangguran+terbuka"},
    ),
    "simdasi_provinces": ("/api/interoperabilitas/datasource/simdasi/id/26/key/{key}", {}),
    "simdasi_23_jabar": ("/api/interoperabilitas/datasource/simdasi/id/23/wilayah/3200000/key/{key}", {}),
}


def describe(name, resp):
    print(f"\n== {name}: HTTP {resp.status_code}, {len(resp.content)} bytes")
    try:
        body = resp.json()
    except ValueError:
        print("   not JSON:", resp.text[:200].replace(KEY, "***"))
        return
    if not isinstance(body, dict):
        print("   top-level", type(body).__name__)
        return
    print("   top keys:", list(body))
    data = body.get("data")
    if isinstance(data, list) and len(data) == 2 and isinstance(data[0], dict) and isinstance(data[1], list):
        print("   paging:", data[0])
        rows = data[1]
    elif isinstance(data, list):
        rows = data
    else:
        print("   data:", type(data).__name__, list(data)[:15] if isinstance(data, dict) else str(data)[:200])
        return
    print("   rows on page:", len(rows))
    if rows and isinstance(rows[0], dict):
        print("   row fields:", list(rows[0]))
        title = next((rows[0][k] for k in ("title", "domain_name", "sub_name", "nama") if k in rows[0]), None)
        if title:
            print("   first title:", str(title)[:120])


with httpx.Client(base_url=BASE, timeout=30) as client:
    for name, (path, params) in CALLS.items():
        resp = client.get(path.format(key=KEY), params=params)
        describe(name, resp)
        if resp.status_code in (401, 403, 429):
            print("   stopping: access refused or rate limited")
            break
        time.sleep(1.5)
