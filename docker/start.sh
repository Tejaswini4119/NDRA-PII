#!/usr/bin/env sh
set -eu

PROM_CONFIG="${PROM_CONFIG:-/app/config/prometheus.single.yml}"
PROM_LISTEN="${PROM_LISTEN:-0.0.0.0:9090}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8001}"

# Start Prometheus in the background for native UI observability charts.
/usr/local/bin/prometheus \
  --config.file="$PROM_CONFIG" \
  --web.listen-address="$PROM_LISTEN" \
  --storage.tsdb.path=/tmp/prometheus-data \
  >/tmp/prometheus.log 2>&1 &
PROM_PID=$!

cleanup() {
  kill "$PROM_PID" 2>/dev/null || true
}

trap cleanup INT TERM

# Start API in foreground so container lifecycle follows app lifecycle.
exec uvicorn ndra_stack.api:app --host "$API_HOST" --port "$API_PORT"
