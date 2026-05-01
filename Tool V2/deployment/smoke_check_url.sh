#!/usr/bin/env bash
# Quick HTTP check for a deployed Streamlit app on Posit Connect.
# Usage: bash deployment/smoke_check_url.sh 'https://connect.example.com/content/.../'
set -euo pipefail
url="${1:-}"
if [[ -z "$url" ]]; then
  echo "Usage: $0 'https://your-connect-host/.../'" >&2
  exit 2
fi
code=$(curl -sS -o /dev/null -w "%{http_code}" -L --max-time 30 "$url" || true)
echo "HTTP status: $code (for $url)"
if [[ "$code" =~ ^(200|302|303|307|308)$ ]]; then
  exit 0
fi
exit 1
