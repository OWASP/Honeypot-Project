#!/bin/sh
# Example hook: receives one JSON object on stdin (same as JSONL events).
# Copy to shodan_hook.sh, customize, set SHODAN_HOOK_SCRIPT=/app/scripts/shodan_hook.sh
# and mount or COPY into the image. Use for AWS EIP reassignment, Terraform, alerts, etc.
#
# Do not let failures kill the WAF; exit 0 unless you want logged nonzero exits.

set -eu

BODY="$(cat)"
# logger "[shodan-hook] would orchestrate infra from: $BODY"  # if logger available
echo "[shodan-hook] received event ($(printf '%s' "$BODY" | wc -c | tr -d ' ') bytes)" >&2
exit 0
