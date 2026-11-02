"""Region-aware ranking on top of a base retriever.

No region in the question: national (0000) only. Regions named: those domains, their province, and
national, ranked in that order of preference. Region abbreviations are expanded in the query.
"""

import pandas as pd

from src.retrieval.regions import domains, find_regions

CANDIDATES = 300
WEIGHTS = {"own": 1.0, "province": 0.85, "national": 0.7}


def allowed_domains(region_ids):
    if not region_ids:
        return {"0000": 1.0}
    out = {"0000": WEIGHTS["national"]}
    for d in region_ids:
        if d == "0000":
            continue
        province = d[:2] + "00"
        if province != d:
            out[province] = max(out.get(province, 0), WEIGHTS["province"])
        out[d] = WEIGHTS["own"]
    if "0000" in region_ids:
        out["0000"] = WEIGHTS["own"]
    return out


class RegionRank:
    def __init__(self, base):
        self.base = base

    def search(self, question, k=5):
        region_ids = find_regions(question)
        names = " ".join(domains()[d]["name"] for d in region_ids)
        hits = self.base.search(f"{question} {names}", k=CANDIDATES)
        weights = allowed_domains(region_ids)
        hits = hits[hits["domain"].isin(weights)]
        hits = hits.assign(score=hits["score"] * hits["domain"].map(weights))
        return hits.sort_values("score", ascending=False).head(k)
