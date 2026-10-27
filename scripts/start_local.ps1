# ==============================================================================
# LungRay: 1-Click Native Localhost Launcher (Backend + Frontend)
# ==============================================================================
# Usage: powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
# ==============================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [LungRay] MEDICAL PACS CADx & WSOL SYSTEM - LOCAL LAUNCHER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..").Path
$FrontendDir = Join-Path $WorkspaceRoot "app\frontend"
Set-Location -LiteralPath $WorkspaceRoot

Write-Host "[1/3] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$BackendJob = Start-Process powershell -WorkingDirectory $WorkspaceRoot -ArgumentList "-NoExit", "-Command", "Set-Location -LiteralPath '$WorkspaceRoot'; Write-Host '--- LungRay FastAPI Backend (Port 8000) ---' -ForegroundColor Green; python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000 --reload" -PassThru

Write-Host "[2/3] Starting Next.js PACS Viewer on http://localhost:3000..." -ForegroundColor Green
$FrontendJob = Start-Process powershell -WorkingDirectory $FrontendDir -ArgumentList "-NoExit", "-Command", "Set-Location -LiteralPath '$FrontendDir'; Write-Host '--- LungRay Next.js PACS Viewer (Port 3000) ---' -ForegroundColor Cyan; npm run dev" -PassThru

Write-Host "[3/3] Waiting 4 seconds for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

Write-Host "`n>>> Opening LungRay PACS Viewer in default browser: http://localhost:3000 <<<" -ForegroundColor Magenta
Start-Process "http://localhost:3000"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " [INFO] SYSTEM IS RUNNING NATIVELY ON LOCALHOST:" -ForegroundColor White
Write-Host "   - Frontend PACS Viewer: http://localhost:3000" -ForegroundColor Yellow
Write-Host "   - FastAPI Swagger Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "   - Backend Health Check: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "`n [EXIT] To stop the servers, simply close the 2 opened terminal windows." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

