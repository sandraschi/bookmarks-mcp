#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_NAME="bookmarks-mcp"
VERSION="0.2.0"
BUILD_DIR="$ROOT/mcpb-build"
DIST_DIR="$ROOT/dist"
SRC_PACKAGE="browser_bookmarks_tools"
MAX_SIZE_MB=25

echo "=== bookmarks-mcp MCPB build (staging) ==="

if ! command -v mcpb >/dev/null 2>&1; then
  npm install -g @anthropic-ai/mcpb
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/src" "$DIST_DIR"

rsync -a \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '*.bak' \
  "$ROOT/src/$SRC_PACKAGE/" "$BUILD_DIR/src/$SRC_PACKAGE/"

for rel in prompts/system.md prompts/user.md prompts/examples.json; do
  if [[ ! -f "$ROOT/assets/$rel" ]]; then
    echo "Missing required MCPB prompt asset: assets/$rel" >&2
    exit 1
  fi
done
rsync -a "$ROOT/assets/" "$BUILD_DIR/assets/"
rsync -a "$ROOT/assets/prompts/" "$BUILD_DIR/prompts/"

for rel in prompts/system.md prompts/user.md prompts/examples.json assets/prompts/examples.json; do
  if [[ ! -f "$BUILD_DIR/$rel" ]]; then
    echo "Staging missing required prompt file: $rel" >&2
    exit 1
  fi
done

cp "$ROOT/manifest.json" "$BUILD_DIR/"
[[ -f "$ROOT/README.md" ]] && cp "$ROOT/README.md" "$BUILD_DIR/"
[[ -f "$ROOT/CHANGELOG.md" ]] && cp "$ROOT/CHANGELOG.md" "$BUILD_DIR/"

cat > "$BUILD_DIR/requirements.txt" <<'EOF'
fastmcp>=3.3.0
prefab-ui>=0.18.0
pydantic>=2.7
aiohttp>=3.9
aiosqlite>=0.20
httpx>=0.27
requests>=2.31.0
beautifulsoup4>=4.12.0
psutil>=5.9.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
EOF

(cd "$BUILD_DIR" && mcpb validate manifest.json)

OUTPUT_FILE="$DIST_DIR/${PACKAGE_NAME}-v${VERSION}.mcpb"
rm -f "$OUTPUT_FILE"
mcpb pack "$BUILD_DIR" "$OUTPUT_FILE"

SIZE_MB=$(python3 - <<PY
import os
print(f"{os.path.getsize('$OUTPUT_FILE') / (1024 * 1024):.2f}")
PY
)

python3 - <<PY
size = float("$SIZE_MB")
limit = $MAX_SIZE_MB
if size > limit:
    raise SystemExit(f"MCPB bundle is {size} MB (limit {limit} MB)")
PY

rm -rf "$BUILD_DIR"
echo "=== MCPB ready ==="
echo "  $OUTPUT_FILE (${SIZE_MB} MB)"
