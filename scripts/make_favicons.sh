#!/usr/bin/env bash

set -euo pipefail

# Simple helper to turn the Leash logo PNG into assets served by the app.
#
# Usage:
#   ./scripts/make_favicons.sh path/to/source.png
# or rely on the default path where Cursor dropped the icon for you.

SRC="${1:-/Users/noemititarenco/.cursor/projects/Users-noemititarenco-phone-harness/assets/iOS_Icon_Heading-53292260-518a-41d7-be5f-5ccbc6f10b8d.png}"
WEB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/web"
ASSETS_DIR="${WEB_DIR}/assets"

mkdir -p "${ASSETS_DIR}"

if ! command -v convert >/dev/null 2>&1; then
  echo "ImageMagick 'convert' is required. Install it (e.g. 'brew install imagemagick') and re-run." >&2
  exit 1
fi

if [ ! -f "${SRC}" ]; then
  echo "Source icon not found: ${SRC}" >&2
  exit 1
fi

echo "Using source icon: ${SRC}"
cp "${SRC}" "${ASSETS_DIR}/leash-icon.png"

echo "Generating favicon.ico and apple-touch-icon..."
convert "${SRC}" -resize 32x32 "${ASSETS_DIR}/favicon-32.png"
convert "${SRC}" -resize 16x16 "${ASSETS_DIR}/favicon-16.png"
convert "${SRC}" -resize 180x180 "${ASSETS_DIR}/apple-touch-icon.png"
convert "${SRC}" -resize 16x16 "${ASSETS_DIR}/favicon-16.png" \
        -resize 32x32 "${ASSETS_DIR}/favicon-32.png" \
        "${ASSETS_DIR}/favicon.ico"

cat <<EOF
Assets written under: ${ASSETS_DIR}

- leash-icon.png        (brand icon in the header)
- favicon.ico           (classic browser tab icon)
- favicon-16.png
- favicon-32.png
- apple-touch-icon.png  (iOS/Android home-screen icon)

Your browser may cache favicons aggressively; hard-refresh or reopen the tab if you don't see the update immediately.
EOF

