#!/bin/sh
# gcloud with a config folder inside this project (.gcloud/, gitignored), never the work one in ~/.config/gcloud.
# Refuses to run anything but login and info commands unless the active account is the personal one.
export CLOUDSDK_CONFIG="$(cd "$(dirname "$0")" && pwd)/.gcloud"
# the personal account lives in an ignored file, not in the repo: echo you@example.com > .personal_account
PERSONAL=$(cat "$(dirname "$0")/.personal_account" 2>/dev/null)
case "$1" in
  auth|config|version|--version|help|info) ;;
  *)
    account=$(/opt/homebrew/bin/gcloud config get-value account 2>/dev/null)
    if [ -z "$PERSONAL" ] || [ "$account" != "$PERSONAL" ]; then
      echo "gcloud.sh: active account is '${account:-none}', expected $PERSONAL. Run: ./gcloud.sh auth login" >&2
      exit 1
    fi ;;
esac
exec /opt/homebrew/bin/gcloud "$@"
