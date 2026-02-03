################################################################################
# Script Name: run.ps1
#
# Purpose:
#   PowerShell one-click runner for CHECKLIST flow.
#   Invokes common/check_flowtool.py to execute modules and optional items.
#   Provides argument parsing, banner display, and result summary.
#
# Usage:
#   .\run.ps1                                           (run all modules, auto-optimized)
#   .\run.ps1 -stage Initial                            (specify stage)
#   .\run.ps1 -check_module 5.0_SYNTHESIS_CHECK         (run single module)
#   .\run.ps1 -check_module 5.0_SYNTHESIS_CHECK -check_item IMP-5-0-0-10,IMP-5-0-0-03
#   .\run.ps1 -check_module 5.0_SYNTHESIS_CHECK -check_item IMP-5-0-0-10 -skip_distribution
#
# Development Mode:
#   -skip_distribution: Skip DATA_INTERFACE distribution (use when developing/testing 
#                       single checker to preserve manual edits to input files)
#
# Note: Execution mode (serial/parallel) is automatically optimized based on workload
#
# Author: Converted from run.csh
# Date:   2025-11-10
################################################################################

param(
    [string]$root = "",
    [string]$stage = "Initial",
    [string]$check_module = "",
    [string[]]$check_item = @(),
    [switch]$skip_distribution = $false
)

# ============================================================================
# 0. Set Console Encoding for UTF-8 Support
# ============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# ============================================================================
# 1. Initialize Paths
# ============================================================================

# Get script directory and root directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$WORK_DIR = $SCRIPT_DIR
$ROOT_DIR = if ($root) { $root } else { Split-Path -Parent $WORK_DIR }

# Set CHECKLIST_ROOT environment variable for path resolution
$env:CHECKLIST_ROOT = $ROOT_DIR
Write-Host "[INFO] CHECKLIST_ROOT = $env:CHECKLIST_ROOT" -ForegroundColor Gray
$CHECK_FLOWTOOL = Join-Path $ROOT_DIR "Check_modules\common\check_flowtool.py"

# Verify check_flowtool.py exists
if (-not (Test-Path $CHECK_FLOWTOOL)) {
    Write-Host "[ERROR] check_flowtool.py not found at: $CHECK_FLOWTOOL" -ForegroundColor Red
    exit 1
}

# Find Python executable
$PYTHON_EXE = $null
$PYTHON_PATHS = @(
    "C:\Users\wentao\AppData\Local\Programs\Python\Python314\python.exe",
    "C:\Python314\python.exe",
    "python"
)

foreach ($path in $PYTHON_PATHS) {
    if ($path -eq "python") {
        try {
            $null = & python --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $PYTHON_EXE = "python"
                break
            }
        } catch {
            continue
        }
    } elseif (Test-Path $path) {
        $PYTHON_EXE = $path
        break
    }
}

if (-not $PYTHON_EXE) {
    Write-Host "[ERROR] Python not found. Please install Python 3.6+" -ForegroundColor Red
    exit 1
}

# ============================================================================
# 2. DATA_INTERFACE Management (Unified Script)
# ============================================================================

if ($skip_distribution) {
    Write-Host "[INFO] Skipping DATA_INTERFACE management (development mode)" -ForegroundColor Yellow
    Write-Host "  Using existing input files without re-distribution" -ForegroundColor Gray
} else {
    Write-Host "[INFO] Managing DATA_INTERFACE..." -ForegroundColor Cyan

    # Use unified data_interface.py script
    $DATA_INTERFACE_SCRIPT = Join-Path $ROOT_DIR "Project_config\scripts\data_interface.py"

    if (Test-Path $DATA_INTERFACE_SCRIPT) {
        Write-Host "  [Unified] Running full workflow (placeholder -> merge -> resolve)..." -ForegroundColor Yellow
        
        try {
            & $PYTHON_EXE $DATA_INTERFACE_SCRIPT run $ROOT_DIR 2>&1 | ForEach-Object {
                if ($_ -match "\[INFO\]|\[SUCCESS\]|\[MERGE\]|\[NEW\]|Phase \d/\d") {
                    Write-Host "    $_" -ForegroundColor Gray
                }
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    [OK] DATA_INTERFACE workflow completed" -ForegroundColor Green
            } else {
                Write-Host "    [WARNING] DATA_INTERFACE workflow had issues (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    [ERROR] DATA_INTERFACE workflow failed: $_" -ForegroundColor Red
            Write-Host "    [FALLBACK] Continuing with existing DATA_INTERFACE.yaml..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [WARNING] data_interface.py not found, skipping DATA_INTERFACE management" -ForegroundColor Yellow
    }
}

Write-Host ""

# ============================================================================
# 2.5. Note: Distribution & Cache Management
# ============================================================================
# Note: DATA_INTERFACE distribution is now handled by check_flowtool.py
#       - Auto-distribution with hash-based change detection (parse_interface.py)
#       - Only regenerates when DATA_INTERFACE.yaml changes
#       - Supports filtering by check_module and check_item

# ============================================================================
# 3. Display Banner
# ============================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                    CHECKLIST Flow Tool - One-Click Runner" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Configuration:"
Write-Host "  +-------------------------------------------------------------------------+"
Write-Host "  | Root Directory : $ROOT_DIR"
Write-Host "  | Stage          : $stage"
Write-Host "  | Execution Mode : Auto-optimized (intelligent parallel/serial selection)"
if ($check_module) {
    Write-Host "  | Check Module   : $check_module"
}
if ($check_item.Count -gt 0) {
    Write-Host "  | Check Items    : $($check_item -join ', ')"
}
if ($skip_distribution) {
    Write-Host "  | Distribution   : SKIPPED (using existing inputs) [WARNING]" -ForegroundColor Yellow
}
Write-Host "  +-------------------------------------------------------------------------+"
Write-Host ""

# ============================================================================
# 4. Build Command
# ============================================================================

# Build command arguments
$CMD_ARGS = @(
    $CHECK_FLOWTOOL,
    "-root", $ROOT_DIR,
    "-stage", $stage
)

# Add module if specified
if ($check_module) {
    $CMD_ARGS += @("-check_module", $check_module)
}

# Add check items if specified
if ($check_item.Count -gt 0) {
    $CMD_ARGS += "-check_item"
    $CMD_ARGS += $check_item
}

# Note: Execution mode is automatically determined by check_flowtool.py
#       - Multi-module: Item-level parallel (max speed)
#       - Single module: Module-level serial (preserves structure)
#       - All settings (cache, workers) use intelligent defaults

# Display command
Write-Host "  Executing Command:"
Write-Host "  +-------------------------------------------------------------------------+"
Write-Host "  | $PYTHON_EXE $($CMD_ARGS -join ' ')"
Write-Host "  +-------------------------------------------------------------------------+"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 5. Execute Command
# ============================================================================

# Run check_flowtool with constructed command
& $PYTHON_EXE $CMD_ARGS

# Capture exit status
$EXIT_STATUS = $LASTEXITCODE

# ============================================================================
# 6. Run Visual Signoff (always run to generate HTML dashboard)
# ============================================================================

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                    Running Visual Signoff Report Generator" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$VISUAL_SIGNOFF = Join-Path $ROOT_DIR "Check_modules\common\visualize_signoff.py"

if (Test-Path $VISUAL_SIGNOFF) {
    & $PYTHON_EXE $VISUAL_SIGNOFF
    $VISUAL_EXIT = $LASTEXITCODE
    
    if ($VISUAL_EXIT -ne 0) {
        Write-Host "[WARNING] Visual signoff generation failed (Exit Code: $VISUAL_EXIT)" -ForegroundColor Yellow
    } else {
        Write-Host "[INFO] HTML dashboard generated successfully" -ForegroundColor Green
    }
} else {
    Write-Host "[WARNING] visualize_signoff.py not found at: $VISUAL_SIGNOFF" -ForegroundColor Yellow
}

# ============================================================================
# 8. Display Result Banner
# ============================================================================

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
if ($EXIT_STATUS -eq 0) {
    Write-Host "                    [PASS] Auto-Checklist Verification PASSED" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Results Location:"
    Write-Host "  +-------------------------------------------------------------------------+"
    Write-Host "  | * CheckList.log    : $WORK_DIR\CheckList.log"
    Write-Host "  | * CheckList.rpt    : $WORK_DIR\CheckList.rpt"
    Write-Host "  | * HTML Dashboard   : $WORK_DIR\Reports\signoff_*.html"
    Write-Host "  | * Origin.xlsx      : $WORK_DIR\Results\Origin.xlsx"
    Write-Host "  | * Summary.xlsx     : $WORK_DIR\Results\Summary.xlsx"
    Write-Host "  | * Module Results   : $WORK_DIR\Results\<module>\"
    Write-Host "  +-------------------------------------------------------------------------+"
} else {
    Write-Host "                    [FAIL] Auto-Checklist Verification FAILED" -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Exit Code: $EXIT_STATUS"
    Write-Host ""
    Write-Host "  Please review the following files for error details:"
    Write-Host "  +-------------------------------------------------------------------------+"
    Write-Host "  | * CheckList.log    : $WORK_DIR\CheckList.log"
    Write-Host "  | * CheckList.rpt    : $WORK_DIR\CheckList.rpt"
    Write-Host "  | * HTML Dashboard   : $WORK_DIR\Reports\signoff_*.html  (if generated)"
    Write-Host "  +-------------------------------------------------------------------------+"
}
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan

exit $EXIT_STATUS