<#
.SYNOPSIS
    Runs OWASP ZAP OpenAPI Security Scan against Cold-Chain Service via Docker.
.DESCRIPTION
    Uses zap-api-scan.py to parse http://host.docker.internal:8000/openapi.json
    and actively/passively fuzz all registered API endpoints.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  OWASP ZAP OpenAPI Security Scanner (Docker Edition)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker is not installed or not available on PATH." -ForegroundColor Red
    exit 1
}

$WorkspaceRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$ReportsDir = Join-Path $WorkspaceRoot "reports"
if (-not (Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
}

Write-Host "[INFO] Scanning OpenAPI definition at http://host.docker.internal:8000/openapi.json" -ForegroundColor Green

docker run --rm `
    -v "${ReportsDir}:/zap/wrk/:rw" `
    -t ghcr.io/zaproxy/zaproxy:stable `
    zap-api-scan.py -t "http://host.docker.internal:8000/openapi.json" -f openapi -r zap-openapi-report.html -I

Write-Host "[SUCCESS] OpenAPI scan complete. Report: $ReportsDir\zap-openapi-report.html" -ForegroundColor Green
