#!/bin/csh -f
################################################################################
# Script Name: run.csh
#
# Purpose:
#   C Shell one-click runner for CHECKLIST flow.
#   Invokes common/check_flowtool.py to execute modules and optional items.
#   Provides argument parsing, banner display, and result summary.
#
# Usage:
#   ./run.csh                                           (run all modules, auto-optimized)
#   ./run.csh -stage Initial                            (specify stage)
#   ./run.csh -check_module 5.0_SYNTHESIS_CHECK         (run single module)
#   ./run.csh -check_module 5.0_SYNTHESIS_CHECK -check_item IMP-5-0-0-10 IMP-5-0-0-03
#   ./run.csh -check_module 5.0_SYNTHESIS_CHECK -check_item IMP-5-0-0-10 -skip_distribution
#
# Development Mode:
#   -skip_distribution: Skip DATA_INTERFACE distribution (use when developing/testing 
#                       single checker to preserve manual edits to input files)
#
# Note: Execution mode (serial/parallel) is automatically optimized based on workload
#
# Author: yyin
# Date:   2025-10-23
################################################################################

# ============================================================================
# 1. Initialize Paths
# ============================================================================

# Get script directory and root directory
set SCRIPT_DIR = `dirname $0`
set WORK_DIR = `cd $SCRIPT_DIR && pwd`
set ROOT_DIR = `cd $WORK_DIR/.. && pwd`

# Set CHECKLIST_ROOT environment variable for path resolution
setenv CHECKLIST_ROOT "$ROOT_DIR"
echo "[INFO] CHECKLIST_ROOT = $CHECKLIST_ROOT"
set CHECK_FLOWTOOL = "${ROOT_DIR}/Check_modules/common/check_flowtool.py"

# Verify check_flowtool.py exists
if (! -f $CHECK_FLOWTOOL) then
    echo "[ERROR] check_flowtool.py not found at: ${CHECK_FLOWTOOL}"
    exit 1
endif

# Find Python executable
set PYTHON_EXE = ""
foreach python_path ("python3" "python")
    which $python_path >& /dev/null
    if ($status == 0) then
        set PYTHON_EXE = $python_path
        break
    endif
end

if ("$PYTHON_EXE" == "") then
    echo "[ERROR] Python not found. Please install Python 3.6+"
    exit 1
endif

# ============================================================================
# 2. Parse Command Line Arguments
# ============================================================================

# Default values
set STAGE = "Initial"
set CHECK_MODULE = ""
set CHECK_ITEMS = ()
set EXTRA_ARGS = ()
set SKIP_DISTRIBUTION = 0

# Parse command line arguments
set i = 1
while ($i <= $#argv)
    set arg = "$argv[$i]"
    
    switch ("$arg")
        case "-root":
            @ i++
            if ($i <= $#argv) then
                set ROOT_DIR = "$argv[$i]"
                setenv CHECKLIST_ROOT "$ROOT_DIR"
            endif
            breaksw
            
        case "-stage":
            @ i++
            if ($i <= $#argv) then
                set STAGE = "$argv[$i]"
            endif
            breaksw
            
        case "-check_module":
        case "--check_module":
            @ i++
            if ($i <= $#argv) then
                set CHECK_MODULE = "$argv[$i]"
            endif
            breaksw
            
        case "-check_item":
        case "--check_item":
            # Collect all check items until next flag
            @ i++
            while ($i <= $#argv)
                set next_arg = "$argv[$i]"
                if ("$next_arg" =~ -*) then
                    @ i--
                    break
                endif
                set CHECK_ITEMS = ($CHECK_ITEMS "$next_arg")
                @ i++
            end
            breaksw
            
        case "-skip_distribution":
        case "--skip_distribution":
            set SKIP_DISTRIBUTION = 1
            breaksw
            
        default:
            # Collect any other arguments
            set EXTRA_ARGS = ($EXTRA_ARGS "$arg")
            breaksw
    endsw
    
    @ i++
end

# ============================================================================
# 2.5. DATA_INTERFACE Management (Unified Script)
# ============================================================================

if ($SKIP_DISTRIBUTION == 1) then
    echo "[INFO] Skipping DATA_INTERFACE management (development mode)"
    echo "  Using existing input files without re-distribution"
else
    echo "[INFO] Managing DATA_INTERFACE..."

    # Use unified data_interface.py script
    set DATA_INTERFACE_SCRIPT = "${ROOT_DIR}/Project_config/scripts/data_interface.py"

    if (-f $DATA_INTERFACE_SCRIPT) then
        echo "  [Unified] Running full workflow (placeholder -> merge -> resolve)..."
        
        $PYTHON_EXE $DATA_INTERFACE_SCRIPT run $ROOT_DIR |& awk '/\[INFO\]|\[SUCCESS\]|\[MERGE\]|\[NEW\]|Phase [0-9]\/[0-9]/ {print "    " $0}'
        
        if ($status == 0) then
            echo "    [OK] DATA_INTERFACE workflow completed"
        else
            echo "    [WARNING] DATA_INTERFACE workflow had issues (exit code: $status)"
        endif
    else
        echo "  [WARNING] data_interface.py not found, skipping DATA_INTERFACE management"
    endif
endif

echo ""

# ============================================================================
# 2.6. Note: Distribution & Cache Management
# ============================================================================
# Note: DATA_INTERFACE distribution is now handled by check_flowtool.py
#       - Auto-distribution with hash-based change detection (parse_interface.py)
#       - Only regenerates when DATA_INTERFACE.yaml changes
#       - Supports filtering by check_module and check_item

# ============================================================================
# 3. Display Banner
# ============================================================================

echo "================================================================================"
echo "                    CHECKLIST Flow Tool - One-Click Runner"
echo "================================================================================"
echo ""
echo "  Configuration:"
echo "  +-------------------------------------------------------------------------+"
echo "  | Root Directory : $ROOT_DIR"
echo "  | Stage          : $STAGE"
echo "  | Execution Mode : Auto-optimized (intelligent parallel/serial selection)"
if ("$CHECK_MODULE" != "") then
    echo "  | Check Module   : $CHECK_MODULE"
endif
if ($#CHECK_ITEMS > 0) then
    echo "  | Check Items    : $CHECK_ITEMS"
endif
if ($SKIP_DISTRIBUTION == 1) then
    echo "  | Distribution   : SKIPPED (using existing inputs) ⚠️"
endif
echo "  +-------------------------------------------------------------------------+"
echo ""

# ============================================================================
# 4. Build Command
# ============================================================================

# Build command array
set CMD = ($PYTHON_EXE "$CHECK_FLOWTOOL" -root "$ROOT_DIR" -stage "$STAGE")

# Add module if specified
if ("$CHECK_MODULE" != "") then
    set CMD = ($CMD -check_module "$CHECK_MODULE")
endif

# Add check items if specified
if ($#CHECK_ITEMS > 0) then
    set CMD = ($CMD -check_item $CHECK_ITEMS)
endif

# Add any extra arguments
if ($#EXTRA_ARGS > 0) then
    set CMD = ($CMD $EXTRA_ARGS)
endif

# Note: Execution mode is automatically determined by check_flowtool.py
#       - Multi-module: Item-level parallel (max speed)
#       - Single module: Module-level serial (preserves structure)
#       - All settings (cache, workers) use intelligent defaults

# Display command
echo "  Executing Command:"
echo "  +-------------------------------------------------------------------------+"
echo "  | $CMD"
echo "  +-------------------------------------------------------------------------+"
echo ""
echo "================================================================================"
echo ""
# ============================================================================
# 5. Execute Command
# ============================================================================

# Run check_flowtool with constructed command
$CMD

# Capture exit status
set EXIT_STATUS = $status

# ============================================================================
# 6. Run Visual Signoff (always run to generate HTML dashboard)
# ============================================================================

echo ""
echo "================================================================================"
echo "                    Running Visual Signoff Report Generator"
echo "================================================================================"
echo ""

set VISUAL_SIGNOFF = "${ROOT_DIR}/Check_modules/common/visualize_signoff.py"

if (-f $VISUAL_SIGNOFF) then
    $PYTHON_EXE $VISUAL_SIGNOFF
    set VISUAL_EXIT = $status
    
    if ($VISUAL_EXIT != 0) then
        echo "[WARNING] Visual signoff generation failed (Exit Code: $VISUAL_EXIT)"
    else
        echo "[INFO] HTML dashboard generated successfully"
    endif
else
    echo "[WARNING] visualize_signoff.py not found at: $VISUAL_SIGNOFF"
endif

# ============================================================================
# 7. Display Result Banner
# ============================================================================

echo ""
echo "================================================================================"
if ($EXIT_STATUS == 0) then
    echo "                    [PASS] Auto-Checklist Verification PASSED"
    echo "================================================================================"
    echo ""
    echo "  Results Location:"
    echo "  +-------------------------------------------------------------------------+"
    echo "  | * CheckList.log    : ${WORK_DIR}/CheckList.log"
    echo "  | * CheckList.rpt    : ${WORK_DIR}/CheckList.rpt"
    echo "  | * HTML Dashboard   : ${WORK_DIR}/Reports/signoff_*.html"
    echo "  | * Origin.xlsx      : ${WORK_DIR}/Results/Origin.xlsx"
    echo "  | * Summary.xlsx     : ${WORK_DIR}/Results/Summary.xlsx"
    echo "  | * Module Results   : ${WORK_DIR}/Results/<module>/"
    echo "  +-------------------------------------------------------------------------+"
else
    echo "                    [FAIL] Auto-Checklist Verification FAILED"
    echo "================================================================================"
    echo ""
    echo "  Exit Code: $EXIT_STATUS"
    echo ""
    echo "  Please check the log files for error details:"
    echo "  +-------------------------------------------------------------------------+"
    echo "  | * CheckList.log    : ${WORK_DIR}/CheckList.log"
    echo "  | * CheckList.rpt    : ${WORK_DIR}/CheckList.rpt"
    echo "  | * HTML Dashboard   : ${WORK_DIR}/Reports/signoff_*.html  (if generated)"
    echo "  +-------------------------------------------------------------------------+"
endif
echo ""
echo "================================================================================"

exit $EXIT_STATUS