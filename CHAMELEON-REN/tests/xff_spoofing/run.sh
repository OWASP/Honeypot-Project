#!/usr/bin/env bash
# CHAMELEON-REN: X-Forwarded-For spoofing regression test (OWASP/Honeypot-Project#111)
#
# Brings up real Nginx + Stimulus Engine + Redis with an echo-stub WAF and checks
# that a client-supplied X-Forwarded-For cannot change the identity used for
# rate limiting, the sticky persona session, or downstream telemetry.
#
# Usage:   ./run.sh                    # test the config in this repo (expect PASS)
#          NGINX_CONF=/tmp/old.conf ./run.sh   # test another nginx.conf
#          KEEP=1 ./run.sh             # leave the stack running afterwards
# Needs:   docker (compose v2), curl, python3
set -uo pipefail

cd "$(dirname "$0")"
PORT="${TEST_PORT:-18080}"
URL="http://127.0.0.1:${PORT}"
UA="Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0"
DC="docker compose"
PASS=0; FAIL=0

ok()   { echo "  PASS  $*"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL  $*"; FAIL=$((FAIL+1)); }
hdr()  { python3 -c 'import json,sys; print(json.load(sys.stdin).get(sys.argv[1], ""))' "$1"; }
rcli() { $DC exec -T redis redis-cli "$@"; }

cleanup() { [ "${KEEP:-0}" = "1" ] || $DC down -v --remove-orphans >/dev/null 2>&1; }
trap cleanup EXIT

echo "== Starting test stack (nginx.conf: ${NGINX_CONF:-repo default}) =="
$DC up -d --build --quiet-pull >/dev/null 2>&1 || { $DC up -d --build; exit 2; }

for _ in $(seq 1 60); do
  curl -fs -A "$UA" "$URL/" >/dev/null 2>&1 && break
  sleep 1
done
curl -fs -A "$UA" "$URL/" >/dev/null || { echo "stack did not come up"; $DC logs; exit 2; }
rcli FLUSHALL >/dev/null
sleep 2   # let the limit_req bucket drain after the readiness probes

# ---------------------------------------------------------------------------
echo "== T1: spoofed X-Forwarded-For is not used as client identity =="
resp=$(curl -s -A "$UA" -H 'X-Forwarded-For: 203.0.113.10' "$URL/")
real_ip=$(echo "$resp" | hdr x-real-ip)
fwd_for=$(echo "$resp" | hdr x-forwarded-for)
claimed=$(echo "$resp" | hdr x-client-claimed-xff)
echo "        X-Real-IP=$real_ip  X-Forwarded-For=$fwd_for  X-Client-Claimed-XFF=$claimed"
[ -n "$real_ip" ] && [ "$real_ip" != "203.0.113.10" ] \
  && ok "X-Real-IP is the TCP peer ($real_ip), not the spoofed value" \
  || bad "X-Real-IP was taken from the client header ($real_ip)"
[ "$fwd_for" = "$real_ip" ] \
  && ok "X-Forwarded-For overwritten with the peer address" \
  || bad "X-Forwarded-For carries client-supplied data ($fwd_for)"
[ "$claimed" = "203.0.113.10" ] \
  && ok "claimed XFF preserved separately for research (X-Client-Claimed-XFF)" \
  || bad "claimed XFF not preserved in X-Client-Claimed-XFF"
rcli FLUSHALL >/dev/null

# ---------------------------------------------------------------------------
echo "== T2: rotating XFF cannot hop between personas =="
targets=""
for spec in "198.51.100.1 /login/index.php" "198.51.100.2 /web/database/manager" "198.51.100.3 /gibbon/"; do
  set -- $spec
  t=$(curl -s -A "$UA" -H "X-Forwarded-For: $1" "$URL$2" | hdr x-chameleon-target)
  targets="$targets $t"
done
echo "        personas served:$targets"
[ "$(echo $targets | tr ' ' '\n' | sort -u | wc -l | tr -d ' ')" = "1" ] \
  && ok "all requests stayed on one persona" \
  || bad "persona changed per request ->$targets (honeypot fingerprintable)"

# ---------------------------------------------------------------------------
echo "== T3: Redis holds one namespaced session for the real peer =="
keys=$(rcli --raw KEYS '*' | sort | tr '\n' ' ')
nkeys=$(echo $keys | wc -w | tr -d ' ')
echo "        keys: $keys"
[ "$nkeys" = "1" ] && ok "exactly one session key" || bad "$nkeys session keys created by one client"
case "$keys" in
  session:*) ok "key is namespaced (session:<ip>)";;
  *)         bad "key is not namespaced";;
esac
case "$keys" in
  *198.51.100.*) bad "spoofed IP leaked into Redis";;
  *)             ok "no spoofed IP stored in Redis";;
esac

# ---------------------------------------------------------------------------
echo "== T4: rate limit cannot be bypassed by rotating XFF =="
sleep 2
codes=$(for i in $(seq 1 60); do
  curl -s -o /dev/null -w '%{http_code}\n' -A "$UA" -H "X-Forwarded-For: 192.0.2.$i" "$URL/" &
done; wait)
n503=$(echo "$codes" | grep -c '^503$')
n200=$(echo "$codes" | grep -c '^200$')
echo "        60 parallel requests -> 200: $n200, 503: $n503"
[ "$n503" -gt 0 ] && ok "limit_req throttled the burst" || bad "no request throttled (rate limit bypassed)"

# ---------------------------------------------------------------------------
echo "== T5: Redis memory is bounded =="
maxmem=$(rcli --raw CONFIG GET maxmemory | tail -1)
policy=$(rcli --raw CONFIG GET maxmemory-policy | tail -1)
echo "        maxmemory=$maxmem policy=$policy"
[ "$maxmem" != "0" ] && ok "maxmemory set" || bad "maxmemory unlimited"

# ---------------------------------------------------------------------------
echo
echo "== Result: $PASS passed, $FAIL failed =="
[ "$FAIL" -eq 0 ]
