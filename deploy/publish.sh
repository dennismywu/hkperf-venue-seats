#!/usr/bin/env bash
# Build, then copy dist/hkperf-venue-seats/ to the web server.
#   DEPLOY_HOST=user@code.denniswu.org deploy/publish.sh
# DEPLOY_PATH defaults to the document root in deploy/code.denniswu.org.conf.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${DEPLOY_HOST:?set DEPLOY_HOST, e.g. user@code.denniswu.org}"
path="${DEPLOY_PATH:-/var/www/code.denniswu.org/public/hkperf-venue-seats/}"

deploy/build.sh
# -rlpt: keep modes and times, not the local owner (macOS openrsync has no --chmod)
rsync -rlptv --delete dist/hkperf-venue-seats/ "$DEPLOY_HOST:$path"
