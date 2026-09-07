$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot "venv\Scripts\python.exe"
$runPath = Join-Path $projectRoot "run.py"

Set-Location $projectRoot
$env:PYTHONUTF8 = "1"

if (-not (Test-Path $pythonPath)) {
    Write-Host "MediCare+ virtual environment was not found." -ForegroundColor Red
    Write-Host "Expected: $pythonPath"
    Write-Host "Create it first with: python -m venv venv"
    Read-Host "Press Enter to close"
    exit 1
}

if (-not (Test-Path $runPath)) {
    Write-Host "run.py was not found in $projectRoot" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$existingServer = Get-NetTCPConnection -LocalPort 10000 -State Listen -ErrorAction SilentlyContinue
if ($existingServer) {
    Write-Host "MediCare+ already appears to be running on port 10000." -ForegroundColor Green
    Start-Process "http://localhost:10000/"
    Write-Host "Opened http://localhost:10000/ in your browser."
    Read-Host "Press Enter to close this window"
    exit 0
}

Write-Host "Starting MediCare+ on http://localhost:10000/" -ForegroundColor Green
Write-Host "Keep this window open while using the app."
Write-Host ""
Start-Process "http://localhost:10000/"
& $pythonPath $runPath

Write-Host ""
Write-Host "MediCare+ server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to close"
