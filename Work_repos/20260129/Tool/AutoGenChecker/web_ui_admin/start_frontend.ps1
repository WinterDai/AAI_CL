# Start script for AutoGenChecker Web UI Frontend

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "AutoGenChecker Web UI - Frontend Server" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
$frontendDir = Join-Path $PSScriptRoot "frontend"
$nodeModules = Join-Path $frontendDir "node_modules"

if (-not (Test-Path $nodeModules)) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    Write-Host ""
    Push-Location $frontendDir
    npm install
    Pop-Location
    Write-Host ""
}

Write-Host "Starting Vite development server..." -ForegroundColor Green
Write-Host "UI will be available at: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Start frontend
Push-Location $frontendDir
npm run dev
Pop-Location
