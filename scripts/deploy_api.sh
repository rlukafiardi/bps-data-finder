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
# tagged by the last commit that changed what goes into the image, so a deploy without code changes reuses it
image="$region-docker.pkg.dev/$project/api/api:$(git log -1 --format=%h -- Dockerfile pyproject.toml uv.lock src app)"

./gcloud.sh artifacts docker images describe "$image" >/dev/null 2>&1 || ./gcloud.sh builds submit --region "$region" --tag "$image" .
./gcloud.sh run deploy api --region "$region" --image "$image" \
  --service-account "api-runtime@$project.iam.gserviceaccount.com" \
  --memory 2Gi --cpu 1 --cpu-boost --min-instances 0 --max-instances 1 --concurrency 8 --timeout 60 \
  --allow-unauthenticated \
  --set-secrets BPS_API_KEY=bps-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars "ALLOWED_ORIGINS=$SITE_ORIGIN" \
  --add-volume name=data,type=cloud-storage,bucket=bps-data-finder-data,readonly=true \
  --add-volume-mount volume=data,mount-path=/app/data

# each deploy of new code leaves its image behind (about 0.74 GB, and 0.5 GB is free): keep only the one now serving.
# Revisions before this one then point at deleted images, so a rollback means redeploying an older commit.
[[ "$(./gcloud.sh run services describe api --region "$region" --format='value(spec.template.spec.containers[0].image)')" == "$image" ]] \
  || { echo "the service does not run $image: not pruning" >&2; exit 1; }
repo="$region-docker.pkg.dev/$project/api"
./gcloud.sh artifacts docker images list "$repo" --include-tags --format='csv[no-heading](IMAGE,DIGEST,TAGS)' \
  | while IFS=, read -r name digest tags; do
      [[ "$tags" == *"${image##*:}"* ]] || ./gcloud.sh artifacts docker images delete "${name}@${digest}" --delete-tags --quiet
    done
