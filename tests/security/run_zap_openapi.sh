#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPORTS_DIR="${WORKSPACE_ROOT}/reports"
mkdir -p "${REPORTS_DIR}"

TARGET_URL="http://host.docker.internal:8000/openapi.json"
EXTRA_ARGS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    EXTRA_ARGS="--network=host"
    TARGET_URL="http://localhost:8000/openapi.json"
fi

echo "[INFO] Running OWASP ZAP OpenAPI API scan against ${TARGET_URL}..."

docker run --rm ${EXTRA_ARGS} \
    -v "${REPORTS_DIR}:/zap/wrk/:rw" \
    -t ghcr.io/zaproxy/zaproxy:stable \
    zap-api-scan.py -t "${TARGET_URL}" -f openapi -r zap-openapi-report.html -I || true

echo "[SUCCESS] OpenAPI scan complete. Report: ${REPORTS_DIR}/zap-openapi-report.html"
