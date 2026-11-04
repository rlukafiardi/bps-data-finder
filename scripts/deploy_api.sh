#!/usr/bin/env bash
# Build the image from the committed code with Cloud Build and deploy it as the Cloud Run service `api`.
#
#   SITE_ORIGIN=https://<site>.netlify.app scripts/deploy_api.sh
#
# One instance at most: the 3 s spacing of BPS requests lives in memory, so two instances would break the
# 20 requests a minute budget. The catalog bucket is mounted read-only at /app/data.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${SITE_ORIGIN:?set SITE_ORIGIN to the web page address, for CORS}"
[[ -z "$(git status --porcelain -- src app Dockerfile pyproject.toml uv.lock)" ]] || { echo "commit your changes first: the image must match a commit" >&2; exit 1; }

region=asia-southeast2
project=bps-data-finder
image="$region-docker.pkg.dev/$project/api/api:$(git rev-parse --short HEAD)"

./gcloud.sh builds submit --region "$region" --tag "$image" .
./gcloud.sh run deploy api --region "$region" --image "$image" \
  --service-account "api-runtime@$project.iam.gserviceaccount.com" \
  --memory 2Gi --cpu 1 --cpu-boost --min-instances 0 --max-instances 1 --concurrency 8 --timeout 60 \
  --allow-unauthenticated \
  --set-secrets BPS_API_KEY=bps-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars "ALLOWED_ORIGINS=$SITE_ORIGIN" \
  --add-volume name=data,type=cloud-storage,bucket=bps-data-finder-data,readonly=true \
  --add-volume-mount volume=data,mount-path=/app/data
