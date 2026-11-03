# Decisions log

Dated findings, decisions and incidents, newest last. Search with grep; the key decisions that still shape
the work are in `CLAUDE.md`.

## 2026-11-03: full build, risks 1-2

- Plan: Netlify page (`web/`) + Python search/values API on Cloud Run (HF Spaces as fallback host), values
  verbatim for var / SIMDASI / static tables, monthly local refresh. Netlify Functions can't run the torch
  model; a Netlify-only build would drop semantic search (R@5 ~0.81 instead of 0.93).
- BPS WebAPI terms (all 23 sections read via a fetched summary; verbatim text and the BPS content policy
  of section 20 unverified): public non-commercial use allowed. Requirements: credential tied to its
  registered application (register / update the app description for the public site), token server-side
  only, one token and no rate-limit evasion, attribution "This service uses the Badan Pusat Statistik (BPS)
  API.", no implied endorsement, derived results not presented as official, no altered data, caching OK
  but never present stale data as current (show period + retrieved date), commercial use needs approval.
- var values: `/api/list/model/th/domain/{d}/key/{k}?var=` lists periods (`th_id`, `th`), newest = max `th`.
  `/api/list/model/data/domain/{d}/var/{var}/th/{th_id}/key/{k}` returns `vervar` (rows), `turvar`,
  `tahun`, `turtahun` (sub-periods, e.g. Februari/Agustus), `var` (unit, decimal, note), `last_update`,
  and `datacontent` keyed by the concatenated vals vervar+var+turvar+tahun+turtahun
  (e.g. `11005430126189` = Aceh, var 543, turvar 0, 2026, Februari -> 5.88).
- static table values: `/api/view/domain/{d}/model/statictable/lang/ind/id/{id}/key/{k}` -> `table` (HTML,
  82 KB for table 1555), `updt_date`, `excel` link. Parser to be checked on merged headers.
- Links without slug work (HTTP 200, right page): `https://{site}/id/publication/{YYYY/MM/DD rl_date}/{pub_id}`
  and `/id/pressrelease/{YYYY/MM/DD}/{brs_id}`; `{site}` is `www.bps.go.id` or the domain_url. PDF links
  carry a token and are never shown.
