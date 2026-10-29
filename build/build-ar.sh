#!/usr/bin/env bash
# Build the Arabic EPUB and PDF from the chapters listed in SUMMARY.md.
#
# Usage (from the repository root):
#   ./build/build-ar.sh          build both
#   ./build/build-ar.sh epub     EPUB only
#   ./build/build-ar.sh pdf      PDF only
#
# Requirements: pandoc 3+, LuaLaTeX (TeX Live), the Amiri and
# DejaVu Sans Mono fonts installed on the system.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AR_DIR="$ROOT"
BUILD_DIR="$ROOT/build"
OUT_DIR="$BUILD_DIR/out"
TARGET="${1:-all}"

mkdir -p "$OUT_DIR"

# Chapter order = the order of the .md links in SUMMARY.md.
# A file whose prose has no Arabic yet is skipped (still English).
mapfile -t CHAPTERS < <(
  grep -oE '\]\([^)#]+\.md' "$AR_DIR/SUMMARY.md" \
    | sed -E 's/^\]\(//' \
    | awk '!seen[$0]++'
)

if [ "${#CHAPTERS[@]}" -eq 0 ]; then
  echo "No chapters found in $AR_DIR/SUMMARY.md" >&2
  exit 1
fi

FILES=()
for chapter in "${CHAPTERS[@]}"; do
  if [ -f "$AR_DIR/$chapter" ] && LC_ALL=C grep -qE $'[\xd8-\xdb]' "$AR_DIR/$chapter"; then
    FILES+=("$chapter")
  else
    echo "skip (not translated yet): $chapter" >&2
  fi
done

cd "$AR_DIR"

COMMON=(
  --metadata-file="$BUILD_DIR/metadata-ar.yaml"
  --lua-filter="$BUILD_DIR/rtl.lua"
  --toc
  --toc-depth=2
  --resource-path="$ROOT"
  --highlight-style=tango
)

if [ "$TARGET" = "all" ] || [ "$TARGET" = "epub" ]; then
  pandoc "${COMMON[@]}" \
    --css="$BUILD_DIR/epub-rtl.css" \
    --output="$OUT_DIR/learn-go-with-tests-ar.epub" \
    "${FILES[@]}"
  echo "built: $OUT_DIR/learn-go-with-tests-ar.epub"
fi

if [ "$TARGET" = "all" ] || [ "$TARGET" = "pdf" ]; then
  pandoc "${COMMON[@]}" \
    --pdf-engine=lualatex \
    --output="$OUT_DIR/learn-go-with-tests-ar.pdf" \
    "${FILES[@]}"
  echo "built: $OUT_DIR/learn-go-with-tests-ar.pdf"
fi
