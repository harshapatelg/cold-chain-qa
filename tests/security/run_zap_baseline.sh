#!/usr/bin/env bash
# ==============================================================================
# OWASP ZAP Baseline Security Scanner (Linux / macOS / Git Bash)
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo "  OWASP ZAP Baseline Security Scanner (Docker Edition)"
echo "=========================================================="

# 1. Verify Docker CLI is present
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH."
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 2. Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "[ERROR] Docker daemon is not active. Please start the Docker service."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPORTS_DIR="${WORKSPACE_ROOT}/reports"
mkdir -p "${REPORTS_DIR}"

# Detect Docker host target (host.docker.internal works on macOS/Windows, --network="host" for native Linux)
TARGET_URL="http://host.docker.internal:8000"
EXTRA_ARGS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    EXTRA_ARGS="--network=host"
    TARGET_URL="http://localhost:8000"
fi

echo "[INFO] Target: ${TARGET_URL}"
echo "[INFO] Reports directory: ${REPORTS_DIR}"
echo "[INFO] Running OWASP ZAP baseline scan..."

docker run --rm ${EXTRA_ARGS} \
    -v "${REPORTS_DIR}:/zap/wrk/:rw" \
    -t ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py -t "${TARGET_URL}" -r zap-baseline-report.html -I || true

echo "=========================================================="
echo "[SUCCESS] Baseline scan complete. Report: ${REPORTS_DIR}/zap-baseline-report.html"
echo "=========================================================="
