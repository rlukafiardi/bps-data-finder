#!/usr/bin/env bash
# Publish web/ to Netlify (cari-data-bps.netlify.app) with the live API address filled in.
#
#   API_ORIGIN=https://api-....run.app scripts/deploy_site.sh           # deploy
#   API_ORIGIN=... scripts/deploy_site.sh --create                       # first time: create the site, then deploy
#
# Needs web/.netlify.env with NETLIFY_AUTH_TOKEN (gitignored). The CLI keeps its state in web/.netlify-home/.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${API_ORIGIN:?set API_ORIGIN to the Cloud Run address of the API}"
site=cari-data-bps

rm -rf web/dist && mkdir web/dist
cp web/index.html web/style.css web/app.js web/dist/
printf 'window.API_BASE = "%s";\n' "$API_ORIGIN" > web/dist/config.js
sed "s#API_ORIGIN#$API_ORIGIN#" web/_headers > web/dist/_headers
grep -q "connect-src 'self' $API_ORIGIN;" web/dist/_headers || { echo "API origin missing from the CSP" >&2; exit 1; }

netlify() { (cd web && set -a && . ./.netlify.env && set +a && HOME="$PWD/.netlify-home" NETLIFY_TELEMETRY_DISABLED=1 ../node_modules/.bin/netlify "$@"); }
[[ "${1:-}" == --create ]] && netlify sites:create --name "$site" --disable-linking
netlify deploy --dir dist --no-build --prod --site "$site"
