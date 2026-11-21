#!/bin/sh
# Start Prometheus and Grafana for the demo (optional; the harness does not need them).
# Expects the macOS downloads unpacked in tools/ (see README, "Monitoring").
# Start the API separately first: uvicorn src.api:app --port 8000
set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)
PROM=$(ls -d tools/prometheus-*/ | head -1)
GRAFANA=$(ls -d tools/grafana-*/ | head -1)

"$PROM/prometheus" --config.file=monitoring/prometheus.yml \
  --storage.tsdb.path=tools/prometheus-data --web.listen-address=:9090 --web.external-url=http://localhost:9090 > tools/prometheus.log 2>&1 &
echo "Prometheus: http://localhost:9090 (pid $!)"

GF_PATHS_PROVISIONING="$ROOT/monitoring/grafana/provisioning" \
GF_DASHBOARDS_PATH="$ROOT/monitoring/grafana/dashboards" \
GF_PATHS_DATA="$ROOT/tools/grafana-data" \
GF_AUTH_ANONYMOUS_ENABLED=true GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer \
  "$GRAFANA/bin/grafana" server --homepath "$GRAFANA" > tools/grafana.log 2>&1 &
echo "Grafana:    http://localhost:3000/d/support-triage (pid $!; admin login admin/admin)"
