#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="${HERE}/tests"
IMAGE="${IMAGE:-waf_modsec:ci}"

echo "==> Building image: ${IMAGE}"
docker build -t "${IMAGE}" "${HERE}"

echo "==> Discovering tests in: ${TEST_DIR}"
mapfile -t tests < <(find "${TEST_DIR}" -maxdepth 1 -type f -name 'test_*.sh' | LC_ALL=C sort)

printf "==> Tests (%s):\n" "${#tests[@]}"
printf " - %s\n" "${tests[@]##*/}"

on_fail() {
  echo "==> FAILURE: ${1:-unknown}" >&2
  docker ps -a >&2 || true
  docker images >&2 || true
}

for t in "${tests[@]}"; do
  echo "==> RUN: ${t##*/}"
  if ! IMAGE="${IMAGE}" bash "${t}"; then
    on_fail "${t##*/}"
    exit 1
  fi
done

echo "==> ALL TESTS PASSED"
