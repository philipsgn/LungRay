# ==============================================================================
# LungRay: Smart 1-Click Native Localhost Launcher (Backend + Frontend)
# ==============================================================================
# Usage: powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
# ==============================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [LungRay] MEDICAL PACS CADx & WSOL SYSTEM - SMART LAUNCHER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $WorkspaceRoot

# Function to check if a port is currently listening
function Test-PortListening ($Port) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
        return ($null -ne $conn)
    } catch {
        return $false
    }
}

# Function to wait for an HTTP endpoint with retry loop
function Wait-HttpEndpoint ($Url, $TimeoutSeconds = 25, $ServiceName = "Service") {
    Write-Host "[WAIT] Checking $ServiceName at $Url..." -ForegroundColor Yellow
    $Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    while ($Stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response -and $response.StatusCode -eq 200) {
                Write-Host "[READY] $ServiceName is UP & RESPONDING (HTTP 200)! [$([math]::Round($Stopwatch.Elapsed.TotalSeconds, 1))s]" -ForegroundColor Green
                return $true
            }
        } catch {
            # Still warming up...
        }
        Start-Sleep -Milliseconds 600
    }
    Write-Host "[WARNING] $ServiceName did not respond within $TimeoutSeconds seconds." -ForegroundColor Red
    return $false
}

# 1. Start FastAPI Backend if not already running
if (Test-PortListening 8000) {
    Write-Host "[1/2] FastAPI Backend is ALREADY running on http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$WorkspaceRoot`"; Write-Host '--- LungRay FastAPI Backend (Port 8000) ---' -ForegroundColor Green; python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000 --reload"
}

# 2. Start Next.js Frontend if not already running
if (Test-PortListening 3000) {
    Write-Host "[2/2] Next.js PACS Viewer is ALREADY running on http://127.0.0.1:3000" -ForegroundColor Green
} else {
    Write-Host "[2/2] Starting Next.js PACS Viewer on http://127.0.0.1:3000..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$WorkspaceRoot\app\frontend`"; Write-Host '--- LungRay Next.js PACS Viewer (Port 3000) ---' -ForegroundColor Cyan; npm run dev"
}

# 3. Synchronous Health Polling: Wait until both are actually answering HTTP 200
Write-Host "`n[SYNC] Synchronizing services before opening browser..." -ForegroundColor Yellow
$BackendReady = Wait-HttpEndpoint "http://127.0.0.1:8000/health" 20 "FastAPI Backend"
$FrontendReady = Wait-HttpEndpoint "http://127.0.0.1:3000" 30 "Next.js PACS Viewer"

if ($FrontendReady) {
    Write-Host "`n>>> Both Services Ready! Opening LungRay PACS Viewer in Browser <<<" -ForegroundColor Magenta
    Start-Process "http://localhost:3000"
} else {
    Write-Host "`n[NOTICE] Next.js is still compiling in background. Please open http://localhost:3000 in your browser manually when ready." -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " [INFO] SYSTEM IS RUNNING NATIVELY ON LOCALHOST:" -ForegroundColor White
Write-Host "   - Frontend PACS Viewer: http://localhost:3000" -ForegroundColor Yellow
Write-Host "   - FastAPI Swagger Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "   - Backend Health Check: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "`n [EXIT] To stop servers, simply close the 2 terminal windows." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan