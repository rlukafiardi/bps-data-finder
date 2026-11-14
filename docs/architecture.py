"""Source of docs/architecture.excalidraw and docs/architecture.svg. Edit the layout here, then run:

    python3 docs/architecture.py

Uses the architecture-diagram skill (excalidraw_lib, render_svg).
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "..", "..", ".claude", "skills", "architecture-diagram", "scripts")
sys.path.insert(0, SKILL)
from excalidraw_lib import Diagram  # noqa: E402

d = Diagram(seed=21)
d.title(
    "BPS Data Finder · architecture",
    "A question finds the right BPS source; table numbers come live from BPS, never from a model",
)
d.lane(20, 0, 1500, 520, "SERVING · every visit (Netlify page · Cloud Run API, asia-southeast2)")
d.lane(20, 560, 1500, 290, "REFRESH · monthly, on this Mac")

# Serving lane
d.person(58, 232, "Visitor")
d.box(250, 235, 190, 70, "code", "WEB PAGE", "static · Bahasa Indonesia")
d.box(520, 235, 190, 70, "code", "API", "Cloud Run · 1 instance · caps")
d.box(790, 30, 200, 60, "ai", "GEMINI", "rewrite · region (free tier)")
d.box(790, 120, 200, 60, "code", "HYBRID SEARCH", "BM25 + e5-small · RRF")
d.box(1060, 120, 200, 60, "code", "RANK", "region · period · top 5")
d.box(790, 240, 200, 60, "code", "VALUES", "cache 1 day · 3 s slot")
d.box(1060, 240, 200, 60, "service", "BPS WEBAPI", "var · SIMDASI · static table")
d.box(790, 350, 200, 60, "service", "LOG EVENTS", "no IP · feeds golden set")

d.arrow([(124, 270), (248, 270)], "question", at=(150, 252))
d.arrow([(442, 270), (518, 270)], "HTTPS", at=(456, 252))
d.arrow([(712, 270), (750, 270), (750, 60), (788, 60)])
d.arrow([(712, 270), (750, 270), (750, 150), (788, 150)])
d.arrow([(712, 270), (788, 270)])
d.arrow([(712, 270), (750, 270), (750, 380), (788, 380)])
d.arrow([(890, 92), (890, 118)], "rewrite", at=(898, 97))
d.arrow([(992, 150), (1058, 150)])
d.arrow([(992, 270), (1058, 270)], "live", at=(1010, 252))
d.arrow([(1262, 150), (1535, 150), (1535, 358), (1578, 358)], "read", at=(1330, 132), style="dotted")
d.arrow([(1262, 150), (1535, 150), (1535, 448), (1578, 448)], style="dotted")
d.arrow([(565, 307), (565, 470), (90, 470), (90, 296)], "top 5 · table numbers", at=(130, 476), style="dashed")

# Refresh lane
d.box(50, 650, 190, 64, "service", "BPS WEBAPI", "lists · tables · SIMDASI")
d.box(300, 650, 190, 64, "code", "PULL CATALOG", "recent | all · 3 s a request")
d.box(550, 650, 200, 64, "code", "BUILD + EMBED", "dedupe · links · new vectors")
d.box(290, 760, 190, 60, "service", "GOLDEN SET", "88 questions · real ones later")
d.box(550, 760, 200, 60, "code", "SMOKE EVAL", "Recall@5 ≥ 0.947 or rollback")
d.box(810, 760, 210, 60, "output", "EVAL REPORT", "history.csv · intervals")

d.arrow([(242, 682), (298, 682)])
d.arrow([(492, 682), (548, 682)])
d.arrow([(752, 682), (1548, 682), (1548, 358), (1578, 358)], "write", at=(1100, 664))
d.arrow([(752, 682), (1548, 682), (1548, 448), (1578, 448)])
d.arrow([(650, 716), (650, 758)])
d.arrow([(482, 790), (548, 790)])
d.arrow([(752, 790), (808, 790)])

# The catalog files, shared by both lanes
d.cylinder(1560, 20, 240, 830, "store", title="Catalog bucket")
d.box(1580, 330, 200, 56, "plain", "catalog.parquet", "74,945 sources · 5 types")
d.box(1580, 420, 200, 56, "plain", "embeddings.parquet", "e5-small vectors")

scene = os.path.join(HERE, "architecture.excalidraw")
d.save(scene)
sys.exit(
    subprocess.run(
        [sys.executable, os.path.join(SKILL, "render_svg.py"), scene, os.path.join(HERE, "architecture.svg")]
        + sys.argv[1:]
    ).returncode
)
