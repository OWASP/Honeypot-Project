#!/bin/sh
set -eu

NEW_PERSONA="${1:-generic}"

log() { echo "[swap-persona] $*" >&2; }

# Validate persona name
case "$NEW_PERSONA" in
  generic|wordpress|drupal) ;;
  *)
    log "Unknown persona: $NEW_PERSONA"
    exit 1
    ;;
esac

log "Swapping to persona: $NEW_PERSONA"

# Stop all persona containers (ignore errors)
for p in generic wordpress drupal; do
  docker stop "persona-${p}" 2>/dev/null || true
done

# Start the requested persona container
if ! docker start "persona-${NEW_PERSONA}" 2>/dev/null; then
  log "persona-${NEW_PERSONA} container not found or not built"
  exit 1
fi

log "Persona swap complete: $NEW_PERSONA"
