#!/usr/bin/env bash
# itch.io 업로드용 zip 만들기: index.html 안의 VERSION을 읽어 dist/room-defense_vX.XX.zip 생성
set -euo pipefail
cd "$(dirname "$0")"
VER=$(grep -oE "const VERSION = 'v[0-9.]+'" index.html | grep -oE "v[0-9.]+")
mkdir -p dist
OUT="dist/room-defense_${VER}.zip"
rm -f "$OUT"
zip -j -q "$OUT" index.html
echo "$OUT"
