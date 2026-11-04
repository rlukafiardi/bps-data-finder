#!/usr/bin/env bash
# Copy the files the API reads into its private bucket. Manual on purpose: the live API serves what is here
# after its next start (deploy a new revision to apply it). Run scripts/refresh.sh first.
set -euo pipefail
cd "$(dirname "$0")/.."
bucket=gs://bps-data-finder-data
./gcloud.sh storage cp data/processed/catalog.parquet data/processed/embeddings_intfloat__multilingual-e5-small.parquet "$bucket/processed/"
./gcloud.sh storage cp data/raw/catalog/domains_prov.json data/raw/catalog/domains_kab.json "$bucket/raw/catalog/"
