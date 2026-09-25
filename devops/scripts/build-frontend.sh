#!/usr/bin/env bash
set -euo pipefail
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
api_base="${NEXT_PUBLIC_API_BASE_URL:-}"
if [[ -z "$api_base" ]]; then
  echo 'Set NEXT_PUBLIC_API_BASE_URL to the public FastAPI origin before building.' >&2
  exit 1
fi
if [[ ! "$api_base" =~ ^https:// ]] && [[ ! "$api_base" =~ ^http://localhost(:[0-9]+)?$ ]]; then
  echo 'NEXT_PUBLIC_API_BASE_URL must use HTTPS (HTTP is accepted only for localhost development).' >&2
  exit 1
fi
cd "$root_dir/frontend"
npm ci
NEXT_PUBLIC_API_BASE_URL="$api_base" npm run build
test -s out/index.html || { echo 'Static export missing out/index.html' >&2; exit 1; }
echo "Static frontend ready: $root_dir/frontend/out"
