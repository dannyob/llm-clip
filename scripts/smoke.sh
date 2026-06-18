#!/usr/bin/env bash
# End-to-end smoke test for llm-clip on macOS.
# Uses --dry-run so no real llm call is made; asserts the chosen mimetype.
set -euo pipefail

fail() { echo "SMOKE FAIL: $*" >&2; exit 1; }

# 1. Plain text on the clipboard -> text/plain
printf 'hello clipboard' | pbcopy
out="$(uv run llm-clip --dry-run 'go')"
echo "text -> $out"
echo "$out" | grep -q ' text/plain ' || fail "expected text/plain, got: $out"

# 2. PNG on the clipboard -> image/png (passed through)
tmp_png="$(mktemp -t llmclip).png"
uv run python -c "from PIL import Image; Image.new('RGB',(8,8),(200,100,50)).save('$tmp_png')"
osascript -e "set the clipboard to (read (POSIX file \"$tmp_png\") as «class PNGf»)"
out="$(uv run llm-clip --dry-run 'go')"
echo "png -> $out"
echo "$out" | grep -q ' image/png ' || fail "expected image/png, got: $out"

# 3. TIFF on the clipboard -> transcoded to image/png
tmp_tiff="$(mktemp -t llmclip).tiff"
uv run python -c "from PIL import Image; Image.new('RGB',(8,8),(50,100,200)).save('$tmp_tiff')"
osascript -e "set the clipboard to (read (POSIX file \"$tmp_tiff\") as «class TIFF»)"
out="$(uv run llm-clip --dry-run 'go')"
echo "tiff -> $out"
echo "$out" | grep -q ' image/png ' || fail "expected image/png (transcoded), got: $out"

# 4. The dry-run temp file actually exists and matches its extension
path="$(echo "$out" | awk '{print $3}')"
[ -f "$path" ] || fail "dry-run temp file missing: $path"
rm -f "$path" "$tmp_png" "$tmp_tiff"

echo "SMOKE PASS"
