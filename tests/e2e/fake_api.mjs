// A stand-in for the API that answers with real responses recorded in fixtures/ and counts what it is asked.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = join(fileURLToPath(new URL(".", import.meta.url)), "fixtures");
const fixture = (name) => JSON.parse(readFileSync(join(dir, name), "utf8"));
const OWN_ORIGIN = "http://localhost:8080";

export function fakeApi(port) {
  const calls = { search: [], value: [] };
  const server = createServer((req, res) => {
    const url = new URL(req.url, "http://x");
    const send = (status, body) => {
      res.writeHead(status, { "Content-Type": "application/json", "Access-Control-Allow-Origin": OWN_ORIGIN });
      res.end(JSON.stringify(body));
    };
    if (url.pathname === "/api/search") {
      const q = url.searchParams.get("q");
      calls.search.push(q);
      if (q.includes("putus")) return req.socket.destroy();
      if (q.includes("limit")) return send(429, { detail: "Terlalu banyak pencarian. Coba lagi sebentar." });
      if (q.includes("kosong")) return send(200, { ...fixture("search.json"), question: q, results: [], regions: [] });
      if (q.includes("tanpa daerah")) return send(200, { ...fixture("search.json"), question: q, regions: [] });
      if (q.includes("xss")) {
        const hostile = fixture("search.json");
        hostile.results[0].title = '<img src=x onerror="window.__xss=1">Judul';
        hostile.results[1].doc_id = "simdasi:3200:xss";
        return send(200, hostile);
      }
      if (q.includes("tanpa tautan")) {  // rows whose BPS link could not be checked have url null
        const unlinked = fixture("search.json");
        unlinked.results.forEach((r) => (r.url = null));
        return send(200, unlinked);
      }
      if (q.includes("antre")) {
        const busy = fixture("search.json");
        busy.results[1].doc_id = "simdasi:3200:antre";
        return send(200, busy);
      }
      return send(200, fixture(q.includes("inflasi") ? "search_brs.json" : "search.json"));
    }
    if (url.pathname === "/api/value") {
      const docId = url.searchParams.get("doc_id");
      calls.value.push(Object.fromEntries(url.searchParams));
      if (docId.includes("antre")) return send(429, { detail: "Sedang ramai. Coba lagi sebentar." });
      const kind = docId.startsWith("simdasi") ? "simdasi" : docId.startsWith("var") ? "var" : "static";
      const value = fixture(`value_${kind}.json`);
      if (url.searchParams.get("period")) value.period = url.searchParams.get("period");
      if (docId.includes("xss")) value.rows[0].label = '<img src=x onerror="window.__xss=1">';
      return send(200, value);
    }
    send(404, { detail: "tidak ada" });
  });
  return new Promise((resolve) => server.listen(port, () => resolve({ server, calls })));
}
