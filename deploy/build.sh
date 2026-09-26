#!/usr/bin/env bash
# Assemble the project page, the public viewer and the seat lists in dist/hkperf-venue-seats/.
set -euo pipefail
cd "$(dirname "$0")/.."

out=dist/hkperf-venue-seats
rm -rf dist
mkdir -p "$out/viewer" "$out/data"
cp site/index.html "$out/"
cp app/index.html app/config.js "$out/viewer/"
cp data/*.json "$out/data/"
echo "built $out ($(find "$out" -type f | wc -l | tr -d ' ') files)"
