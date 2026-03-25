#!/usr/bin/env bash
# Single-shot Shodan cycle with a fixture (no real API), JSONL + hook receive JSON.
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
FIXDIR="$(mktemp -d)"
OUT="$(mktemp -d)"

cleanup() {
  rm -rf "$FIXDIR" "$OUT"
}
trap cleanup EXIT

cat >"$FIXDIR/host.json" <<'EOF'
{
  "ip_str": "203.0.113.1",
  "tags": ["honeypot"],
  "hostnames": ["hp.example.test"],
  "country_name": "Exampleland",
  "org": "Example Org",
  "data": []
}
EOF

cat >"$FIXDIR/hook.sh" <<'EOF'
#!/bin/sh
set -eu
cat >/out/received.json
EOF
chmod +x "$FIXDIR/hook.sh"

docker run --rm \
  -v "$FIXDIR:/fixtures:ro" \
  -v "$OUT:/out" \
  -e SHODAN_FIXTURE_FILE=/fixtures/host.json \
  -e SHODAN_TEST_PUBLIC_IP=203.0.113.1 \
  -e SHODAN_SINGLE_SHOT=true \
  -e SHODAN_POLL_INTERVAL=1 \
  -e SHODAN_EVENTS_JSONL=/out/events.jsonl \
  -e SHODAN_HOOK_SCRIPT=/fixtures/hook.sh \
  -e PERSONA=generic \
  -e SWAP_SCRIPT=/bin/true \
  "$IMAGE" \
  python3 /app/shodan_watcher.py

test -s "$OUT/events.jsonl"
grep -q '"classification":"fingerprinted"' "$OUT/events.jsonl" || {
  echo "FAIL: expected fingerprinted classification in $OUT/events.jsonl" >&2
  cat "$OUT/events.jsonl" >&2
  exit 1
}
test -s "$OUT/received.json" || {
  echo "FAIL: hook did not write received.json" >&2
  exit 1
}
grep -q '"classification":"fingerprinted"' "$OUT/received.json" || {
  echo "FAIL: hook payload missing classification" >&2
  exit 1
}

echo "PASS: Shodan fixture cycle wrote JSONL and invoked hook"
