# Start both backend and frontend servers

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "AutoGenChecker Web UI - Starting All Services" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Start backend in new window (with visible window for debugging)
Write-Host "Starting Backend Server..." -ForegroundColor Green

# Use venv Python if available
$venvPython = "C:\Users\yuyin\Desktop\CHECKLIST_V4\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    Write-Host "Using virtual environment Python" -ForegroundColor Cyan
} else {
    $pythonExe = "python"
    Write-Host "Using system Python" -ForegroundColor Yellow
}

$backendScript = Join-Path $PSScriptRoot "start_backend.py"
$backendProcess = Start-Process $pythonExe -ArgumentList $backendScript -PassThru -WindowStyle Normal

# Wait a bit for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start frontend in new window
Write-Host "Starting Frontend Server..." -ForegroundColor Green
$frontendScript = Join-Path $PSScriptRoot "start_frontend.ps1"
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-File", $frontendScript -PassThru

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Services Started!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend UI:  http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to stop all services..." -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop all processes
Write-Host ""
Write-Host "Stopping all services..." -ForegroundColor Yellow

# Stop backend process and its children
if ($backendProcess -and !$backendProcess.HasExited) {
    Write-Host "Stopping backend (PID: $($backendProcess.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
}

# Stop frontend process and its children  
if ($frontendProcess -and !$frontendProcess.HasExited) {
    Write-Host "Stopping frontend (PID: $($frontendProcess.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
}

# Cleanup any remaining python/node processes on our ports
Write-Host "Cleaning up remaining processes..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($port8000) {
    Stop-Process -Id $port8000.OwningProcess -Force -ErrorAction SilentlyContinue
}
$port5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
if ($port5173) {
    Stop-Process -Id $port5173.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host "All services stopped." -ForegroundColor Green
