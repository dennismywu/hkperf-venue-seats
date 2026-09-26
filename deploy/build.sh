#!/usr/bin/env bash
# Assemble the project page, the public viewer and the seat lists in dist/hkperf-venue-seats/.
set -euo pipefail
cd "$(dirname "$0")/.."

out=dist/hkperf-venue-seats
rm -rf dist
mkdir -p "$out/viewer" "$out/data"
cp site/index.html "$out/"
cp app/*.html app/*.js app/*.css "$out/viewer/"
cp data/*.json data/*.csv "$out/data/"
# world-readable for the web server; publish.sh copies these modes as they are
find "$out" -type d -exec chmod 755 {} +
find "$out" -type f -exec chmod 644 {} +
echo "built $out ($(find "$out" -type f | wc -l | tr -d ' ') files)"
