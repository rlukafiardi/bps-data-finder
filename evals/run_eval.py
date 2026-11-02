"""Score retrieval methods on evals/golden_set.csv: Recall@5 and MRR@10, overall and per expected_type.

A hit is a result row with the expected type, one of the expected ids (SIMDASI also by table code),
and, when the golden row gives a domain, that domain.

    uv run python -m evals.run_eval
"""

from pathlib import Path

import pandas as pd

from src.retrieval.bm25 import BM25

GOLDEN = Path("evals/golden_set.csv")
CATALOG = Path("data/processed/catalog.parquet")
K = 10


def is_hit(row, gold):
    ids = {i.strip() for i in str(gold["expected_id"]).split("|")}
    if row["type"] != gold["expected_type"]:
        return False
    if pd.notna(gold["domain"]) and row["domain"] != str(gold["domain"]).zfill(4):
        return False
    return row["source_id"] in ids or (row["type"] == "simdasi" and row["table_code"] in ids)


def score(method, golden):
    out = []
    for gold in golden.to_dict("records"):
        results = method.search(gold["question"], k=K).to_dict("records")
        rank = next((i + 1 for i, r in enumerate(results) if is_hit(r, gold)), None)
        out.append({"question": gold["question"], "type": gold["expected_type"], "rank": rank})
    df = pd.DataFrame(out)
    df["recall@5"] = df["rank"].le(5)
    df["mrr"] = 1 / df["rank"].fillna(float("inf"))
    return df


def main():
    golden = pd.read_csv(GOLDEN, dtype=str)
    labeled = golden[golden["expected_id"].notna()]
    print(f"golden rows: {len(golden)}, with expected_id: {len(labeled)}")
    if labeled.empty:
        return
    catalog = pd.read_parquet(CATALOG)
    methods = {"bm25": BM25(catalog)}
    for name, method in methods.items():
        df = score(method, labeled)
        summary = df.groupby("type")[["recall@5", "mrr"]].mean()
        summary.loc["ALL"] = df[["recall@5", "mrr"]].mean()
        summary["n"] = df.groupby("type").size().reindex(summary.index).fillna(len(df)).astype(int)
        print(f"\n== {name}\n{summary.round(3).to_string()}")
        misses = df[df["rank"].isna()]
        if not misses.empty:
            print("misses:", "; ".join(misses["question"].head(10)))


if __name__ == "__main__":
    main()
