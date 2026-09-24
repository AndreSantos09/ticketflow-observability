#!/usr/bin/env bash
#
# Generates traffic against the TicketFlow API so there is telemetry to look at
# in Grafana. Buys 1-2 tickets for random events in a loop.
#
# Usage:
#   ./scripts/generate-load.sh [BASE_URL] [REQUESTS]
#
#   BASE_URL   default: http://localhost:9000
#   REQUESTS   default: 200
set -euo pipefail

BASE_URL="${1:-http://localhost:9000}"
REQUESTS="${2:-200}"

echo "Sending $REQUESTS purchase requests to $BASE_URL ..."

for i in $(seq 1 "$REQUESTS"); do
  event_id=$(( (RANDOM % 3) + 1 ))
  qty=$(( (RANDOM % 2) + 1 ))
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST "$BASE_URL/events/$event_id/buy" \
    -H 'Content-Type: application/json' \
    -d "{\"buyer\":\"user$i@example.com\",\"quantity\":$qty}"
  # small pause so metrics spread over time
  sleep 0.1
done

echo ""
echo "Done. Open Grafana at http://localhost:3000 to inspect metrics, logs and traces."
