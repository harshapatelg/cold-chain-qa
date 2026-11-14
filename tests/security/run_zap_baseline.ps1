<#
.SYNOPSIS
    Runs OWASP ZAP Baseline Security Scan against Cold-Chain Service via Docker.
.DESCRIPTION
    Launches official ghcr.io/zaproxy/zaproxy:stable container to perform automated
    passive security analysis, checking for security headers, cookie flags, CORS,
    and information disclosure. Saves HTML report into reports/zap-baseline-report.html.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  OWASP ZAP Baseline Security Scanner (Docker Edition)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Docker prerequisite
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker is not installed or not available on PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop for Windows: https://docs.docker.com/desktop/setup/install/windows-install/" -ForegroundColor Yellow
    exit 1
}

# Check Docker daemon running
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker daemon is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Docker daemon is not accessible." -ForegroundColor Red
    exit 1
}

$WorkspaceRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$ReportsDir = Join-Path $WorkspaceRoot "reports"
if (-not (Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
}

Write-Host "[INFO] Target URL: http://host.docker.internal:8000" -ForegroundColor Green
Write-Host "[INFO] Output directory: $ReportsDir" -ForegroundColor Green
Write-Host "[INFO] Pulling and running ghcr.io/zaproxy/zaproxy:stable..." -ForegroundColor Green

# Note: zap-baseline.py returns 0 for clean, 1 for WARN, 2 for FAIL.
# We include -I to not fail the build on warnings during development.
docker run --rm `
    -v "${ReportsDir}:/zap/wrk/:rw" `
    -t ghcr.io/zaproxy/zaproxy:stable `
    zap-baseline.py -t "http://host.docker.internal:8000" -r zap-baseline-report.html -I

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Scan completed. Report saved to: $ReportsDir\zap-baseline-report.html" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
