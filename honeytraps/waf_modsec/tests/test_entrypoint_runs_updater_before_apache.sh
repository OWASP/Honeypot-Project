
#!/usr/bin/env bashset -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-entry-order-$RANDOM$RANDOM"
TMPDIR="$(mktemp -d)"

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

# Override /crs_update.sh with a slow fake updater to prove ordering:
# if Apache starts before the updater finishes, the test fails.
cat >"$TMPDIR/crs_update.sh" <<'SH'
#!/bin/sh
set -eu
echo "[fake-updater] starting" >&2
sleep 3
echo "[fake-updater] done" >&2
exit 0
SH
chmod +x "$TMPDIR/crs_update.sh"

docker run -d --name "$NAME" \
  -e CRSUPDATE=true \
  -v "$TMPDIR/crs_update.sh:/crs_update.sh:ro" \
  "$IMAGE" >/dev/null

# Give the entrypoint time to invoke the fake updater
sleep 1

# While fake updater is still sleeping, Apache must NOT be running yet
if docker exec "$NAME" sh -lc 'pgrep -f "(apache2|httpd)" >/dev/null 2>&1'; then
  echo "FAIL: Apache started before updater completed" >&2
  docker logs "$NAME" >&2 || true
  exit 1
fi

# After updater completes, Apache should come up
for _ in {1..30}; do
  if docker exec "$NAME" sh -lc 'pgrep -f "(apache2|httpd)" >/dev/null 2>&1'; then
    echo "PASS: updater ran before Apache start"
    exit 0
  fi
  sleep 0.5
done

echo "FAIL: Apache did not start after updater" >&2
docker logs "$NAME" >&2 || true
exit 1
