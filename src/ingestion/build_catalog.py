"""Flatten data/raw/catalog/ into data/processed/catalog.parquet, one row per catalog item.

Sources (see pull_catalog.py): search pages for tables, list pages for publications and press
releases, SIMDASI table lists, and var lists whose notes are joined onto the var rows.

    uv run python -m src.ingestion.build_catalog
"""

import base64
import html
import json
import re
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/catalog")
OUT = Path("data/processed/catalog.parquet")
QUARANTINE = Path("data/processed/catalog_quarantine.parquet")

TABLE_TYPES = {"1": "statictable", "2": "var", "3": "simdasi"}  # search `category`
TAG = re.compile(r"<[^>]+>")


def clean(value):
    if value is None:
        return ""
    return " ".join(TAG.sub(" ", html.unescape(str(value))).split())


def page_rows(pattern):
    for path in sorted(RAW.glob(pattern)):
        data = json.loads(path.read_text()).get("data")
        if isinstance(data, list) and len(data) == 2:
            yield path, data[1]


def search_tables():
    for path, rows in page_rows("search*/*/tablestatistic/p*.json"):  # search/ and the second pass search50/
        domain = path.parts[-3]
        for r in rows:
            # url: .../statistics-table/{category}/{base64 id}/slug; for var and statictable the id is "<id>#<category>"
            token = r["url"].split("/statistics-table/")[1].split("/")[1]
            decoded = base64.b64decode(token + "=" * (-len(token) % 4)).decode()
            source_id = decoded.split("#")[0]
            yield {
                "type": TABLE_TYPES.get(r["category"], f"table{r['category']}"),
                "domain": domain,
                "source_id": source_id,
                "title": clean(r["title"]),
                "text_parts": [r.get("subject"), r.get("body")],
                "date": r.get("updated"),
                "url": r["url"],
            }


def listed(model, id_field, text_fields):
    for path, rows in page_rows(f"*/{model}/*/p*.json"):
        domain = path.parts[-4]
        for r in rows:
            yield {
                "type": model,
                "domain": domain,
                "source_id": str(r.get(id_field) or ""),
                "title": clean(r.get("title")),
                "text_parts": [r.get(f) for f in text_fields],
                "date": r.get("rl_date"),
                "pdf": r.get("pdf"),
            }


def simdasi_lists():
    domain_urls = {}
    for path in [RAW / "domains_prov.json", RAW / "domains_kab.json"]:
        for d in json.loads(path.read_text())["data"][1]:
            domain_urls[d["domain_id"]] = d["domain_url"].rstrip("/")
    for path in sorted((RAW / "simdasi").glob("*.json")):
        domain = path.stem
        for r in json.loads(path.read_text())["data"][1].get("data") or []:
            token = base64.b64encode(r["id_tabel"].encode()).decode().rstrip("=")
            yield {
                "type": "simdasi",
                "domain": domain,
                "source_id": r["id_tabel"],
                "title": clean(r.get("judul")),
                "text_parts": [r.get("judul_en"), r.get("bab"), r.get("subject")],
                "date": r.get("latest_update"),
                "years": r.get("ketersediaan_tahun"),
                "table_code": r.get("kode_tabel"),
                # link pattern copied from search rows of category 3; unverified for kab/kota sites
                "url": f"{domain_urls[domain]}/id/statistics-table/3/{token}/" if domain in domain_urls else None,
            }


def listed_vars():
    """var rows from the list endpoint, where pulled: they fill tables the search paging dropped."""
    for path, rows in page_rows("*/var/all/p*.json"):
        domain = path.parts[-4]
        for r in rows:
            yield {
                "type": "var",
                "domain": domain,
                "source_id": str(r["var_id"]),
                "title": clean(r.get("title")),
                "text_parts": [r.get("sub_name")],
            }


def var_notes():
    notes = {}
    for path, rows in page_rows("*/var/all/p*.json"):
        domain = path.parts[-4]
        for r in rows:
            notes[(domain, str(r["var_id"]))] = " | ".join(
                p for p in (clean(r.get("def")), clean(r.get("notes")), clean(r.get("unit"))) if p
            )
    return notes


def main():
    rows = [
        *simdasi_lists(),  # first, so its table_code and years win the dedupe against search rows
        *search_tables(),  # before listed_vars, so search rows keep their url in the dedupe
        *listed_vars(),
        *listed("publication", "pub_id", ["abstract", "subject_csa"]),
        *listed("pressrelease", "brs_id", ["subj", "abstract"]),
    ]
    df = pd.DataFrame(rows)
    df["text_parts"] = df["text_parts"].map(lambda parts: " | ".join(p for p in map(clean, parts) if p))
    df = df.rename(columns={"text_parts": "body"})
    notes = var_notes()
    df["notes"] = [notes.get((d, i), "") if t == "var" else "" for t, d, i in zip(df["type"], df["domain"], df["source_id"])]
    df["doc_id"] = df["type"] + ":" + df["domain"] + ":" + df["source_id"]

    bad = (df["source_id"] == "") | (df["title"] == "")
    df[bad].to_parquet(QUARANTINE, index=False)
    out = df[~bad].groupby("doc_id", as_index=False).first()  # simdasi: list row + search row with its url
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)

    print(out.groupby(["type"]).agg(rows=("doc_id", "size"), domains=("domain", "nunique")).to_string())
    print(f"\nrows: {len(out)}, quarantined: {int(bad.sum())}, merged duplicates: {int((~bad).sum()) - len(out)}")
    print(f"var rows with notes: {(out['notes'] != '').sum()}")


if __name__ == "__main__":
    main()
