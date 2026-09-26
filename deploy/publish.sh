#!/usr/bin/env bash
# Build, then copy dist/hkperf-venue-seats/ to the web server.
#   DEPLOY_HOST=user@code.denniswu.org deploy/publish.sh
# DEPLOY_PATH defaults to the document root in deploy/code.denniswu.org.conf.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${DEPLOY_HOST:?set DEPLOY_HOST, e.g. user@code.denniswu.org}"
path="${DEPLOY_PATH:-/var/www/code.denniswu.org/public/hkperf-venue-seats/}"

deploy/build.sh
rsync -av --delete --chmod=D755,F644 dist/hkperf-venue-seats/ "$DEPLOY_HOST:$path"
