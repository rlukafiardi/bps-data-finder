"""Score retrieval methods on evals/golden_set.csv: Recall@5 and MRR@10, per source and per target type.

A target is `type:domain:id`; SIMDASI targets use the table code (e.g. `simdasi:3273:4.1.3`).

    uv run python -m evals.run_eval
"""

from pathlib import Path

import pandas as pd

from src.retrieval.bm25 import BM25
from src.retrieval.dense import Dense, Hybrid
from src.retrieval.region_rank import RegionRank

GOLDEN = Path("evals/golden_set.csv")
CATALOG = Path("data/processed/catalog.parquet")
K = 10


def keys(row):
    """Target keys a catalog row answers to."""
    out = {f"{row['type']}:{row['domain']}:{row['source_id']}"}
    if row["type"] == "simdasi" and row["table_code"]:
        out.add(f"simdasi:{row['domain']}:{row['table_code']}")
    return out


def score(method, golden):
    out = []
    for gold in golden.to_dict("records"):
        targets = set(gold["targets"].split("|"))
        results = method.search(gold["question"], k=K).to_dict("records")
        rank = next((i + 1 for i, r in enumerate(results) if keys(r) & targets), None)
        out.append({
            "question": gold["question"],
            "source": gold["source"],
            "type": gold["targets"].split(":")[0],
            "rank": rank,
            "top1": f"{results[0]['type']}:{results[0]['domain']} {results[0]['title'][:60]}" if results else "",
        })
    df = pd.DataFrame(out)
    df["recall@5"] = df["rank"].le(5)
    df["mrr"] = 1 / df["rank"].fillna(float("inf"))
    return df


def summary(df, by):
    s = df.groupby(by)[["recall@5", "mrr"]].mean()
    s["n"] = df.groupby(by).size()
    return s


def check_targets(golden, catalog):
    """Targets missing from the catalog: a labelling error or a gap in the pull."""
    known = set().union(*(keys(r) for r in catalog.to_dict("records")))
    missing = [t for ts in golden["targets"] for t in ts.split("|") if t not in known]
    if missing:
        print("targets not in catalog:", ", ".join(missing))


def main():
    golden = pd.read_csv(GOLDEN, dtype=str)
    catalog = pd.read_parquet(CATALOG)
    print(f"golden rows: {len(golden)} ({golden['source'].value_counts().to_dict()}), catalog rows: {len(catalog)}")
    check_targets(golden, catalog)
    bm25, dense = BM25(catalog), Dense(catalog)
    hybrid = Hybrid(bm25, dense)
    methods = {
        "bm25": bm25,
        "bm25+region": RegionRank(bm25),
        "dense": dense,
        "dense+region": RegionRank(dense),
        "hybrid+region": RegionRank(hybrid),
    }
    for name, method in methods.items():
        df = score(method, golden)
        print(f"\n== {name}")
        print(summary(df.assign(all="ALL"), "all").round(3).to_string())
        print(summary(df, "source").round(3).to_string())
        print(summary(df, "type").round(3).to_string())
        misses = df[df["recall@5"].eq(False)]
        for m in misses.itertuples():
            print(f"  miss (rank {m.rank}): {m.question!r} -> top1 {m.top1}")


if __name__ == "__main__":
    main()
