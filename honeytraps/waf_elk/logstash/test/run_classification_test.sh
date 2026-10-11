#!/bin/bash
# Regression test for attack_classification in the waf_elk logstash pipeline.
#
# Feeds a recorded ModSecurity audit event through the real filter chain and
# asserts the resulting attack_classification type and severity.
#
# A single request trips rules from several CRS categories at once: the 942
# SQLi family carries broad, warning-level quote and metacharacter patterns
# that also match XSS, traversal and RCE payloads. This test guards against
# the classifier being decided by an incidental rule match instead of by the
# dominant, high-confidence one.
#
# Usage: ./run_classification_test.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PIPELINE="$HERE/../pipeline/logstash.conf"
FIXTURE="${FIXTURE:-$HERE/../../../waf_modsec/example-log.json}"
IMAGE="${LOGSTASH_IMAGE:-logstash:7.17.10}"
EXPECTED_TYPE="${EXPECTED_TYPE:-XSS}"
EXPECTED_SEVERITY="${EXPECTED_SEVERITY:-CRITICAL}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Build a standalone copy of the pipeline:
#  - beats input -> stdin, elasticsearch output -> stdout, so the filter chain
#    runs without Elasticsearch or a honeypot container
#  - drop the ASN enrichment block, exactly as logstash/Dockerfile does when
#    MAXMIND_LICENSE_KEY is unset. Logstash validates every plugin config at
#    pipeline creation, including inside a conditional that is false at
#    runtime, so leaving it in fails with a missing-.mmdb ConfigurationError.
python3 - "$PIPELINE" "$WORK/test.conf" <<'PY'
import re, sys
src = open(sys.argv[1]).read()
src = re.sub(
    r"[ \t]*# --- ASN/ISP enrichment start ---.*?# --- ASN/ISP enrichment end ---\n",
    "", src, count=1, flags=re.S)
src = re.sub(r"input \{.*?\n\}\n", "input { stdin { } }\n", src, count=1, flags=re.S)
src = re.sub(r"output \{.*?\n\}\n?\s*$", "output { stdout { codec => json_lines } }\n",
             src, count=1, flags=re.S)
open(sys.argv[2], "w").write(src)
PY

# The fixture is pretty-printed; the pipeline expects one JSON object per line.
python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))" \
  "$FIXTURE" > "$WORK/input.jsonl"

echo "Running pipeline against $(basename "$FIXTURE")..."
docker run --rm -i \
  -v "$WORK/test.conf:/usr/share/logstash/pipeline/logstash.conf:ro" \
  -e LS_JAVA_OPTS="-Xms256m -Xmx256m" \
  -e XPACK_MONITORING_ENABLED=false \
  "$IMAGE" \
  logstash -f /usr/share/logstash/pipeline/logstash.conf \
  < "$WORK/input.jsonl" > "$WORK/out.txt" 2>"$WORK/err.txt" || true

ACTUAL="$(python3 - "$WORK/out.txt" <<'PY'
import json, sys
for line in open(sys.argv[1]):
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    ac = ev.get("attack_classification")
    if ac:
        print("%s %s" % (ac.get("type"), ac.get("severity")))
        break
PY
)"

if [ -z "$ACTUAL" ]; then
  echo "FAIL: pipeline produced no classified event"
  echo "--- logstash stderr (tail) ---"
  tail -40 "$WORK/err.txt"
  exit 1
fi

ACTUAL_TYPE="${ACTUAL%% *}"
ACTUAL_SEVERITY="${ACTUAL##* }"
echo "expected: type=$EXPECTED_TYPE severity=$EXPECTED_SEVERITY"
echo "actual:   type=$ACTUAL_TYPE severity=$ACTUAL_SEVERITY"

if [ "$ACTUAL_TYPE" != "$EXPECTED_TYPE" ] || [ "$ACTUAL_SEVERITY" != "$EXPECTED_SEVERITY" ]; then
  echo "FAIL: attack_classification regression"
  exit 1
fi

echo "PASS: attack_classification is correct"
