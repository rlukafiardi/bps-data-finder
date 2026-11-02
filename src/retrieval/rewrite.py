"""LLM query rewrite: turn a user question into a BPS-style Indonesian search query.

Results are cached in data/processed/rewrite_cache.jsonl per (model, prompt, question), so a rerun of
the eval only calls the API for new questions or a changed prompt.
"""

import hashlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from src.config import REWRITE_MODEL, REWRITE_SPACING_S

CACHE = Path("data/processed/rewrite_cache.jsonl")
RATE_LIMIT_WAIT_S = 65
RETRIES = 3

PROMPT = """You rewrite questions about Indonesian official statistics (BPS) into a search query that matches
how BPS titles its tables, publications and press releases.

Rules:
- Write the query in Indonesian, using BPS terminology. Translate English questions.
- Expand acronyms and add the full BPS term (TPT -> Tingkat Pengangguran Terbuka, IPM -> Indeks
  Pembangunan Manusia, P1/P2 -> Indeks Kedalaman/Keparahan Kemiskinan, NTP -> Nilai Tukar Petani,
  PDRB ADHB/ADHK -> Produk Domestik Regional Bruto Atas Dasar Harga Berlaku/Konstan, BPJS -> Jaminan
  Kesehatan, PMDN/PMA -> Penanaman Modal Dalam Negeri/Asing, wisman -> wisatawan mancanegara).
- Keep the breakdown the user asks for in BPS words ("per kabupaten" -> "menurut Kabupaten/Kota",
  "tiap provinsi" -> "menurut Provinsi") and keep the period (month, quarter as "Triwulan I", year).
- Add one or two synonyms BPS uses in titles when the user's word is informal (sembako -> harga eceran
  bahan pokok; gaji -> upah/gaji; pakai internet -> mengakses internet).
- Do not add facts, numbers or regions the user did not ask for.
- region: the region asked about, written as BPS names it ("Sumatera Selatan", "Kota Bandung",
  "Kabupaten Bogor", "Kepulauan Riau"); "Indonesia" if the user asks for national or all provinces;
  null if no region is named."""

SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "region": {"type": ["string", "null"]},
    },
    "required": ["query", "region"],
}


class Rewriter:
    def __init__(self, model=REWRITE_MODEL):
        load_dotenv(".env")
        self.model = model
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.cache = {}
        if CACHE.exists():
            for line in CACHE.read_text().splitlines():
                row = json.loads(line)
                self.cache[row["key"]] = row["result"]
        self.last_call = 0.0

    def _key(self, question):
        return hashlib.sha256(f"{self.model}\n{PROMPT}\n{question}".encode()).hexdigest()

    def rewrite(self, question):
        """{"query": str, "region": str | None}"""
        key = self._key(question)
        if key not in self.cache:
            result = self._call(question)
            self.cache[key] = result
            with CACHE.open("a") as f:
                f.write(json.dumps({"key": key, "model": self.model, "question": question, "result": result}) + "\n")
        return self.cache[key]

    def _call(self, question):
        config = types.GenerateContentConfig(
            system_instruction=PROMPT,
            response_mime_type="application/json",
            response_json_schema=SCHEMA,
        )
        for attempt in range(RETRIES):
            time.sleep(max(0.0, self.last_call + REWRITE_SPACING_S - time.monotonic()))
            self.last_call = time.monotonic()
            try:
                response = self.client.models.generate_content(model=self.model, contents=question, config=config)
                return json.loads(response.text)
            except errors.ClientError as e:
                if e.code != 429:
                    raise
                time.sleep(RATE_LIMIT_WAIT_S)
            except errors.ServerError:
                time.sleep(REWRITE_SPACING_S * 2 ** (attempt + 1))
        raise RuntimeError(f"rewrite still failing after {RETRIES} tries: {question!r}")


class Rewritten:
    """Search with the question plus its rewrite, so the original words still count."""

    def __init__(self, retriever, rewriter):
        self.retriever = retriever
        self.rewriter = rewriter

    def search(self, question, k=5):
        r = self.rewriter.rewrite(question)
        return self.retriever.search(" ".join(p for p in (question, r["query"], r["region"]) if p), k=k)
