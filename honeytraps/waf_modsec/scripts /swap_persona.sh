#!/bin/sh
set -eu

NEW_PERSONA="${1:-generic}"
log() { echo "[swap-persona] $*" >&2; }

log "Swapping to persona: $NEW_PERSONA"

# Stop all persona containers
docker stop persona-wordpress 2>/dev/null || true
docker stop persona-drupal 2>/dev/null || true
docker stop persona-generic 2>/dev/null || true

# Start the new persona container
docker start "persona-${NEW_PERSONA}" 2>/dev/null || \
  docker compose --profile "$NEW_PERSONA" up -d "persona-${NEW_PERSONA}"

log "Persona swap complete: $NEW_PERSONA"
