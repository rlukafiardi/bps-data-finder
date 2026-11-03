"use strict";

const API = window.API_BASE;
const $ = (id) => document.getElementById(id);
const TIMEOUT_MS = 45000; // a value can wait up to 15 s for a free slot with BPS, then BPS itself answers

const state = { regions: [], opener: null, doc: null };

function remembered(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch {
    return null; // private window or blocked storage: the page works, it just forgets
  }
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatDate(value) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value || "");
  if (!m) return null;
  return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])).toLocaleDateString("id-ID", {
    day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
  });
}

async function api(path, params) {
  const url = new URL(path, API);
  for (const [key, value] of Object.entries(params)) if (value) url.searchParams.set(key, value);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response;
  try {
    response = await fetch(url, { signal: controller.signal });
  } catch (e) {
    throw new Error(e.name === "AbortError"
      ? "Server lama menjawab. Coba lagi sebentar."
      : "Tidak bisa terhubung ke server. Cek koneksi internet, lalu coba lagi.");
  } finally {
    clearTimeout(timer);
  }
  if (response.ok) return response.json();
  let detail = null;
  try { detail = (await response.json()).detail; } catch { /* body is not JSON */ }
  throw new Error(typeof detail === "string" ? detail : "Pertanyaannya terlalu pendek atau terlalu panjang.");
}

/* search */

function showWelcome(visible) {
  $("welcome").hidden = !visible;
  $("help").setAttribute("aria-expanded", String(visible));
  if (!visible) remembered("welcome-seen", "1");
}

function setStatus(node, text, isError) {
  node.textContent = text;
  node.classList.toggle("error", Boolean(isError));
}

async function search(question) {
  const q = question.trim();
  const error = $("q-error");
  if (q.length < 2) {
    error.textContent = "Tulis dulu pertanyaannya, minimal dua huruf.";
    $("q").focus();
    return;
  }
  error.textContent = "";
  $("q").value = q;
  history.replaceState(null, "", "?q=" + encodeURIComponent(q));
  $("go").disabled = true;
  setStatus($("status"), "Mencari...");
  $("results").replaceChildren();
  $("regions").textContent = "";
  try {
    renderResults(await api("/api/search", { q }));
  } catch (e) {
    setStatus($("status"), e.message, true);
  } finally {
    $("go").disabled = false;
  }
}

function renderResults(data) {
  state.regions = data.regions.map((r) => r.id);
  $("examples").hidden = true;
  if (data.results.length === 0) {
    setStatus($("status"), "Belum ketemu. Coba kata yang lebih sederhana, misalnya nama datanya dan daerahnya.");
    return;
  }
  setStatus($("status"), `${data.results.length} hasil paling cocok`);
  $("regions").textContent = data.regions.length
    ? "Daerah yang dikenali: " + data.regions.map((r) => r.name).join(", ")
    : "Pertanyaanmu tidak menyebut daerah, jadi yang dicari data nasional.";
  $("results").replaceChildren(...data.results.map(resultCard));
}

function resultCard(item) {
  const card = el("li", "card result");
  const meta = el("div", "meta");
  meta.append(el("span", "badge", item.type_label), el("span", "region", item.region));
  const facts = [];
  if (item.years && item.years.length) facts.push(`Tahun tersedia: ${item.years[0]}-${item.years[item.years.length - 1]}`);
  const date = formatDate(item.date);
  if (date) facts.push((item.type === "publication" || item.type === "pressrelease" ? "Terbit: " : "Diperbarui: ") + date);
  card.append(meta, el("h3", "", item.title));
  if (facts.length) card.append(el("p", "small", facts.join(" · ")));

  const actions = el("div", "actions");
  const hasValues = item.type === "var" || item.type === "simdasi" || item.type === "statictable";
  if (hasValues) {
    const show = el("button", "primary", "Lihat Angkanya");
    show.type = "button";
    show.addEventListener("click", () => openPanel(item, show));
    actions.append(show);
  }
  if (item.url) actions.append(bpsLink(item.url, hasValues ? "secondary linkbtn" : "primary linkbtn"));
  card.append(actions);
  return card;
}

function bpsLink(url, className) {
  const link = el("a", className, "Buka di BPS");
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

/* value panel */

function openPanel(item, opener) {
  state.opener = opener;
  state.doc = item;
  $("panel-title").textContent = item.title;
  $("panel-link").hidden = !item.url;
  if (item.url) $("panel-link").href = item.url;
  $("backdrop").hidden = false;
  $("panel").hidden = false;
  $("panel-close").focus();
  loadValue();
}

function closePanel() {
  $("panel").hidden = true;
  $("backdrop").hidden = true;
  if (state.opener) state.opener.focus();
}

async function loadValue(period) {
  const wrap = $("table-wrap");
  wrap.hidden = true;
  for (const id of ["unit", "panel-note", "panel-source", "panel-fetched"]) $(id).textContent = "";
  $("legend").hidden = true;
  $("period-box").hidden = true;
  setStatus($("panel-status"), "Mengambil angka dari BPS... Kalau lagi ramai, bisa sampai setengah menit.");
  const doc = state.doc;
  try {
    const data = await api("/api/value", { doc_id: doc.doc_id, period, regions: state.regions.join(",") });
    if (doc !== state.doc) return; // another table was opened while this one loaded
    renderValue(data);
  } catch (e) {
    if (doc === state.doc) setStatus($("panel-status"), e.message, true);
  }
}

function renderValue(data) {
  setStatus($("panel-status"), "");
  if (data.unit) $("unit").textContent = "Satuan: " + data.unit;
  if (data.periods.length > 1) {
    $("period").replaceChildren(...data.periods.map((p) => {
      const option = el("option", "", p.label);
      option.value = p.id;
      option.selected = p.label === data.period;
      return option;
    }));
    $("period-box").hidden = false;
  }
  const table = el("table");
  const head = el("tr");
  head.append(el("th", "", "Keterangan"), ...data.columns.map((c) => el("th", "", c)));
  const thead = el("thead");
  thead.append(head);
  const body = el("tbody");
  for (const row of data.rows) {
    const tr = el("tr", row.highlight ? "hit" : "");
    const label = el("th", "", row.label);
    label.scope = "row";
    tr.append(label, ...row.values.map((v) => (v === null ? el("td", "none", "–") : el("td", "", v))));
    body.append(tr);
  }
  table.append(thead, body);
  const wrap = $("table-wrap");
  wrap.replaceChildren(table);
  wrap.hidden = false;
  const hit = body.querySelector("tr.hit");
  if (hit) {
    wrap.scrollTop = hit.offsetTop - wrap.clientHeight / 2;
    $("legend").hidden = false;
  }
  $("panel-note").textContent = data.note || "";
  $("panel-source").textContent = data.source ? "Sumber: " + data.source : "";
  const fetched = new Date(data.fetched_at).toLocaleString("id-ID", {
    day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Jakarta",
  });
  $("panel-fetched").textContent = `Angka diambil dari BPS pada ${fetched} WIB.`;
}

/* wiring */

$("search").addEventListener("submit", (e) => {
  e.preventDefault();
  search($("q").value);
});
$("q").addEventListener("input", () => { $("q-error").textContent = ""; });
for (const chip of document.querySelectorAll(".chip")) {
  chip.addEventListener("click", () => { $("q").value = chip.textContent; search(chip.textContent); });
}
$("help").addEventListener("click", () => showWelcome($("welcome").hidden));
$("welcome-start").addEventListener("click", () => { showWelcome(false); $("q").focus(); });
$("welcome-example").addEventListener("click", () => {
  showWelcome(false);
  const example = document.querySelector(".chip").textContent;
  $("q").value = example;
  search(example);
});
$("panel-close").addEventListener("click", closePanel);
$("backdrop").addEventListener("click", closePanel);
$("period").addEventListener("change", () => loadValue($("period").value));
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("panel").hidden) closePanel(); });

const initial = new URLSearchParams(location.search).get("q");
if (initial) {
  $("q").value = initial;
  search(initial);
} else if (!remembered("welcome-seen")) {
  showWelcome(true);
}
