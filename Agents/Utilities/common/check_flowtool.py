################################################################################
# Script Name: check_flowtool.py
#
# Purpose:
#   1. Distribute DATA_INTERFACE data to individual check items (via parse_interface)
#   2. Execute checker scripts with flexible parallelism strategies
#   3. Aggregate logs, reports, and generate Excel summary artifacts
#
# Execution Modes:
#   Mode 1: Item-level parallel (default) - Maximum speed, all items run in parallel
#   Mode 2: Module-level parallel (--use-module-runners) - Preserves module independence
#
# Usage:
#   # Item-level parallel (fastest, default for multiple modules):
#   python check_flowtool.py -root .. -stage Initial
#   
#   # Module-level parallel (compatible with existing module runners):
#   python check_flowtool.py -root .. -stage Initial --use-module-runners
#   
#   # Single module or specific items (auto-detects best mode):
#   python check_flowtool.py -root .. -stage Initial -check_module 5.0_SYNTHESIS_CHECK
#   python check_flowtool.py -root .. -stage Initial -check_module 5.0_SYNTHESIS_CHECK \
#       -check_item IMP-5-0-0-00 IMP-5-0-0-10
#
# Author: yyin
# Date:   2025-10-23
# Updated: 2025-10-30 (Added item-level parallel + hybrid execution modes)
################################################################################
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time

# Try to import tqdm for progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("[INFO] tqdm not installed. Install with 'pip install tqdm' for progress bar support.")

from get_check import get_check_modules  # module/item config loader
from log_generator import log_generator
from rpt_generator import rpt_generator
from excel_generator import summary_yaml_to_excel  # per-module Excel summary
from checklist_fillin import annotate_excel_template_multi, annotate_excel_template_auto  # aggregated Origin.xlsx
from excel_summary_generator import build as build_summary  # aggregated Summary.xlsx

# Import parse_interface for data distribution
try:
    from parse_interface import parse_and_distribute
    PARSE_INTERFACE_AVAILABLE = True
except ImportError:
    PARSE_INTERFACE_AVAILABLE = False
    print("[WARN] parse_interface not available. Data distribution will be skipped.")


class TeeLogger:
    """Capture stdout/stderr to log file and optionally to terminal."""
    def __init__(self, log_path: Path):
        self.terminal = sys.stdout
        self.log_file = open(log_path, 'w', encoding='utf-8')
        self._write_header()
    
    def _write_header(self):
        """Write log file header."""
        header = f"""===== CheckFlow Execution Log =====
Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Command: {' '.join(sys.argv)}

"""
        self.log_file.write(header)
        self.log_file.flush()
    
    def write(self, message):
        # Write to log file
        self.log_file.write(message)
        self.log_file.flush()
        
        # Filter out checker directory/script warnings from terminal
        # (they are verbose and should only appear in log file)
        if 'Checker directory not found' in message or 'Checker script not found' in message:
            return  # Only write to log, skip terminal
        
        # Filter out summary YAML warnings (too verbose for terminal)
        if any(keyword in message for keyword in [
            'Summary directory not found',
            'Failed to generate summary YAML',
            'Summary YAML missing, skip Excel/CSV'
        ]):
            return  # Only write to log, skip terminal
        
        # Also write important messages to terminal
        if any(keyword in message for keyword in [
            'DEVELOPMENT MODE', 'SKIPPED', 'Skipping', '⚠️',
            '[INFO] Execution mode:', '[INFO] Item-level parallel',
            'Executing checkers:', 'Execution summary:',
            '[INFO] Distributing DATA_INTERFACE', '[INFO] Skipping distribute',
            '[INFO] DATA_INTERFACE distribution',
            'Processing', '📦', '⏭️',  # Distribution status messages
            '[ERROR]', '[WARN]'
        ]):
            try:
                self.terminal.write(message)
                self.terminal.flush()
            except UnicodeEncodeError:
                # Fallback: encode with error handling for terminals that don't support UTF-8
                safe_message = message.encode(self.terminal.encoding or 'utf-8', errors='replace').decode(self.terminal.encoding or 'utf-8')
                self.terminal.write(safe_message)
                self.terminal.flush()
    
    def flush(self):
        self.log_file.flush()
        self.terminal.flush()
    
    def close(self):
        self.log_file.close()


def find_runner(root: Path, module: str) -> Path:
    """DEPRECATED: Find module runner script (kept for backward compatibility)."""
    run_file = root / "Check_modules" / module / "run" / f"{module}.py"
    if not run_file.is_file():
        raise FileNotFoundError(f"Runner not found: {run_file}")
    return run_file


def find_checker_scripts(root: Path, module: str, items: Optional[List[str]] = None) -> List[Tuple[str, str, Path]]:
    """
    Find all checker scripts for a module.
    
    Args:
        root: Project root path
        module: Check module name (e.g., "5.0_SYNTHESIS_CHECK")
        items: Optional list of specific item IDs to run (e.g., ["IMP-5-0-0-00"])
               If None, returns all checker scripts in the module
    
    Returns:
        List of tuples: (module, item_id, checker_script_path)
    """
    checker_dir = root / "Check_modules" / module / "scripts" / "checker"
    
    if not checker_dir.exists():
        print(f"[WARN] Checker directory not found: {checker_dir}")
        return []
    
    checkers = []
    
    if items:
        # Only find specified items
        for item_id in items:
            script_path = checker_dir / f"{item_id}.py"
            if script_path.exists():
                checkers.append((module, item_id, script_path))
            else:
                print(f"[WARN] Checker script not found: {script_path}")
    else:
        # Find all .py files in checker directory
        for script_path in sorted(checker_dir.glob("*.py")):
            if script_path.stem.startswith("IMP-") or script_path.stem.startswith("CHECK-"):
                item_id = script_path.stem
                checkers.append((module, item_id, script_path))
    
    return checkers

def run_single_checker(python_exe: str, checker_script: Path, root: Path) -> int:
    """
    Run a single checker script.
    
    UPDATED: Use subprocess to avoid multiprocessing compatibility issues.
    Windows spawn mode + in-process execution causes silent failures.
    
    Args:
        python_exe: Python executable path
        checker_script: Path to checker script
        root: Project root path
    
    Returns:
        Return code (0 = success, non-zero = failure)
    """
    # Use subprocess for reliable execution in multiprocessing environment
    return run_checker_subprocess(python_exe, checker_script, root)


def run_checker_in_process(checker_script: Path, root: Path) -> int:
    """
    Run checker by importing and executing in the same process.
    This enables memory cache sharing between checkers and write_summary_yaml.
    
    Args:
        checker_script: Path to checker script
        root: Project root path
        
    Returns:
        Return code (0 = success, non-zero = failure)
    """
    import importlib.util
    import os
    
    # Save current directory
    original_cwd = os.getcwd()
    work_dir = root / "Work"
    
    try:
        # Change to Work directory (checkers expect to run from there)
        os.chdir(str(work_dir))
        
        # Import the checker module
        spec = importlib.util.spec_from_file_location(
            checker_script.stem,  # module name
            checker_script
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {checker_script}")
        
        module = importlib.util.module_from_spec(spec)
        
        # Execute the module (this runs the checker)
        spec.loader.exec_module(module)
        
        # If module has a main() function, call it
        if hasattr(module, 'main'):
            module.main()
        
        return 0  # Success
        
    except Exception as e:
        # Let caller handle the fallback
        raise
        
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def run_checker_subprocess(python_exe: str, checker_script: Path, root: Path) -> int:
    """
    Run checker in subprocess (original implementation).
    
    Args:
        python_exe: Python executable path
        checker_script: Path to checker script
        root: Project root path
        
    Returns:
        Return code (0 = success, non-zero = failure)
    """
    cmd = [python_exe, str(checker_script)]
    
    try:
        # Run checker with suppressed output (checkers write their own logs)
        cp = subprocess.run(cmd, 
                          capture_output=True,
                          text=True,
                          cwd=str(root / "Work"),  # Run from Work directory
                          timeout=300)  # 5 minute timeout per checker
        return cp.returncode
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Checker timed out (5min): {checker_script.name}")
        return 1
    except Exception as e:
        print(f"[ERROR] Checker failed: {checker_script.name} - {e}")
        return 1


def run_single_checker_wrapper(args_tuple: Tuple[str, Path, Path, str, str]) -> Tuple[str, str, int]:
    """
    Wrapper for parallel execution - unpacks arguments and runs checker.
    
    Args:
        args_tuple: (python_exe, checker_script, root, module, item_id)
    
    Returns:
        Tuple of (module, item_id, return_code)
    """
    python_exe, checker_script, root, module, item_id = args_tuple
    try:
        rc = run_single_checker(python_exe, checker_script, root)
        return (module, item_id, rc)
    except Exception as e:
        print(f"[ERROR] Checker {item_id} failed with exception: {e}")
        return (module, item_id, 1)


def run_module_runner(python_exe: str,
                      runner: Path,
                      root: Path,
                      stage: str,
                      module: str,
                      items: List[str]) -> int:
    """
    Run a single module runner script (for module-level execution mode).
    
    This preserves backward compatibility with existing module runners.
    """
    cmd = [python_exe, str(runner),
           "-root", str(root),
           "-stage", stage,
           "-check_module", module]
    if items:
        cmd.append("-check_item")
        cmd.extend(items)
    print(f"[INFO] Running module: {module}")
    cp = subprocess.run(cmd)
    return cp.returncode


def _get_optimal_workers(num_modules: int) -> int:
    """Calculate optimal number of workers based on CPU count and module count.
    
    Strategy:
    - For small module counts (1-2): use serial or minimal parallelism
    - For moderate counts (3-8): use 75% of CPU cores
    - For large counts (9+): use all CPU cores
    """
    cpu_count = multiprocessing.cpu_count()
    
    if num_modules == 1:
        return 1
    elif num_modules == 2:
        return 2
    elif num_modules <= 8:
        # Use 75% of CPUs, minimum 2, maximum num_modules
        return min(max(2, int(cpu_count * 0.75)), num_modules)
    else:
        # Use all CPUs, cap at num_modules
        return min(cpu_count, num_modules)


def run_single_module_wrapper(args_tuple: Tuple[str, Path, Path, str, str, List[str]]) -> Tuple[str, int]:
    """Wrapper for parallel execution - unpacks arguments and runs module.
    
    Returns:
        Tuple of (module_name, return_code)
    """
    python_exe, runner, root, stage, module, items = args_tuple
    try:
        rc = run_module_runner(python_exe, runner, root, stage, module, items)
        return (module, rc)
    except Exception as e:
        print(f"[ERROR] Module {module} failed with exception: {e}")
        return (module, 1)

def parse_args():
    p = argparse.ArgumentParser(
        description="Execute checklist modules and items with flexible parallel strategies."
    )
    p.add_argument("-root", default="..", help="Root of CheckList (default: ..)")
    p.add_argument("-stage", default="Initial", help="Stage (default: Initial)")
    p.add_argument("-check_module", "--check_module", dest="check_module",
                   help="Specific check module to run (default: all from config)")
    p.add_argument("-check_item", "--check_item", dest="check_items",
                   nargs="*", help="Specific check items (only with --check-module).")
    p.add_argument("--serial", action="store_true",
                   help="Force serial execution (disable parallel mode)")
    p.add_argument("-skip_distribution", "--skip_distribution", action="store_true",
                   help="Skip DATA_INTERFACE distribution (for checker development/testing)")
    p.add_argument("--use-module-runners", action="store_true",
                   help="Use module-level execution (calls module runners, preserves module independence)")
    p.add_argument("--item-parallel", action="store_true",
                   help="Force item-level parallel execution (maximum speed, bypasses module runners)")
    
    # Cache configuration options (for distributed execution)
    p.add_argument("--enable-file-cache", action="store_true",
                   help="Enable file-based cache for cross-process sharing (for distributed execution)")
    p.add_argument("--cache-dir", type=str, default=None,
                   help="Directory for file cache (default: <root>/Work/.cache)")
    p.add_argument("--max-cache-size", type=int, default=200,
                   help="Maximum number of items in memory cache (default: 200)")
    p.add_argument("--show-cache-stats", action="store_true",
                   help="Show detailed cache statistics at the end")
    
    return p.parse_args()

def _clean_generated(root: Path, modules: List[str]) -> None:
    """Remove previously generated artifacts to ensure a fresh run.

    Cleans:
      - Work/Results/<module>/ directory contents (but keeps directory)
      - Work/Results/Origin.xlsx / Summary.xlsx
      - Work/CheckList.log / Work/CheckList.rpt
    """
    work_dir = root / "Work"
    results_dir = work_dir / "Results"
    # Ensure base dirs exist
    work_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Remove aggregated Excel files
    for fp in [results_dir / "Origin.xlsx", results_dir / "Summary.xlsx"]:
        if fp.exists():
            try:
                fp.unlink()
                print(f"[INFO] Removed previous file: {fp}")
            except Exception as e:
                print(f"[WARN] Cannot remove {fp}: {e}")

    # Remove per-module Excel folders contents (leave folder)
    for m in modules:
        mod_dir = results_dir / m
        if mod_dir.is_dir():
            for child in mod_dir.glob("*"):
                try:
                    if child.is_file():
                        child.unlink()
                    elif child.is_dir():
                        # only remove shallow directories; avoid recursive complexity now
                        for sub in child.glob("**/*"):
                            if sub.is_file():
                                sub.unlink()
                        child.rmdir()
                except Exception as e:
                    print(f"[WARN] Could not clean {child}: {e}")
        else:
            # create empty directory for upcoming output
            mod_dir.mkdir(parents=True, exist_ok=True)

    # Remove aggregated log & rpt in Work directory
    for fp in [work_dir / "CheckList.log", work_dir / "CheckList.rpt"]:
        if fp.exists():
            try:
                fp.unlink()
                print(f"[INFO] Removed previous file: {fp}")
            except Exception as e:
                print(f"[WARN] Cannot remove {fp}: {e}")


def _run_items_parallel(root: Path, modules: List[str], modules_map: Dict[str, List[str]], 
                       check_module: Optional[str], check_items: Optional[List[str]], 
                       max_workers: int) -> int:
    """
    Execute checker scripts in parallel at item level (maximum speed).
    
    This bypasses module runners and directly executes individual checker scripts.
    """
    # Step 1: Collect all checker scripts to run
    all_checkers = []
    
    for module in modules:
        if check_module and check_items:
            # Specific items requested
            items_to_run = check_items
        else:
            # All items in the module
            items_to_run = modules_map.get(module, [])
        
        # Find checker scripts for this module
        checkers = find_checker_scripts(root, module, items_to_run if items_to_run else None)
        all_checkers.extend(checkers)
    
    if not all_checkers:
        print("[WARN] No checker scripts found to execute")
        return 1
    
    print(f"[INFO] Item-level parallel execution: {len(all_checkers)} checker(s) with {max_workers} worker(s)")
    
    # Step 2: Prepare tasks for parallel execution
    tasks = []
    for module, item_id, checker_script in all_checkers:
        tasks.append((sys.executable, checker_script, root, module, item_id))
    
    # Step 3: Execute in parallel with progress tracking
    overall_rc = 0
    start_time = time.time()
    failed_items = []
    passed_items = []
    
    # Create progress bar if tqdm is available
    if TQDM_AVAILABLE:
        pbar = tqdm(total=len(tasks), desc="Executing checkers", unit="item",
                   bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {
            executor.submit(run_single_checker_wrapper, task): (task[3], task[4])  # (module, item_id)
            for task in tasks
        }
        
        # Process results as they complete
        for future in as_completed(future_to_item):
            module, item_id = future_to_item[future]
            try:
                returned_module, returned_item_id, rc = future.result()
                
                # Track pass/fail
                if rc == 0:
                    passed_items.append(f"{returned_module}/{returned_item_id}")
                else:
                    failed_items.append(f"{returned_module}/{returned_item_id}")
                    overall_rc = 1
                
                # Update progress
                if TQDM_AVAILABLE:
                    pbar.update(1)
                    status = "✓" if rc == 0 else "✗"
                    pbar.set_postfix_str(f"{status} {returned_item_id}")
                else:
                    completed = len(passed_items) + len(failed_items)
                    status = "✓" if rc == 0 else "✗"
                    print(f"[INFO] [{completed}/{len(tasks)}] {status} {returned_module}/{returned_item_id}")
                    
            except Exception as e:
                failed_items.append(f"{module}/{item_id}")
                overall_rc = 1
                if TQDM_AVAILABLE:
                    pbar.update(1)
                    pbar.set_postfix_str(f"✗ {item_id} (exception)")
                else:
                    print(f"[ERROR] Item {module}/{item_id} failed with exception: {e}")
    
    if TQDM_AVAILABLE:
        pbar.close()
    
    total_time = time.time() - start_time
    print(f"\n[INFO] Execution summary:")
    print(f"  Total items: {len(tasks)}")
    print(f"  Passed: {len(passed_items)}")
    print(f"  Failed: {len(failed_items)}")
    print(f"  Duration: {total_time:.1f}s (avg: {total_time/len(tasks):.2f}s per item)")
    
    if failed_items and len(failed_items) <= 10:
        print(f"\n[WARN] Failed items:")
        for item in failed_items:
            print(f"  - {item}")
    
    return overall_rc


def _run_modules_serial(root: Path, args, modules: List[str], modules_map: Dict[str, List[str]]) -> int:
    """Execute modules one by one (traditional serial execution)."""
    overall_rc = 0
    for mod in modules:
        if args.check_module and args.check_items:
            items = args.check_items
        else:
            # Use all configured items for that module
            items = modules_map.get(mod, [])
        try:
            runner = find_runner(root, mod)
        except FileNotFoundError as e:
            print(f"[WARN] {e}")
            # Don't fail overall execution for missing runners (module not yet implemented)
            continue
        rc = run_module_runner(sys.executable, runner, root, args.stage, mod, items)
        if rc != 0:
            overall_rc = overall_rc or rc
    return overall_rc


def _run_modules_parallel(root: Path, args, modules: List[str], modules_map: Dict[str, List[str]], max_workers: int) -> int:
    """Execute modules in parallel using ProcessPoolExecutor with progress bar."""
    
    print(f"[INFO] Running {len(modules)} module(s) with {max_workers} worker(s)")
    
    # Prepare tasks
    tasks = []
    for mod in modules:
        if args.check_module and args.check_items:
            items = args.check_items
        else:
            items = modules_map.get(mod, [])
        try:
            runner = find_runner(root, mod)
            tasks.append((sys.executable, runner, root, args.stage, mod, items))
        except FileNotFoundError as e:
            print(f"[WARN] {e}")
            # Don't fail for missing runners (module not yet implemented)
    
    if not tasks:
        print("[WARN] No valid modules to execute (all runners missing)")
        # Don't fail overall if runners are just not implemented yet
        return 0
    
    # Execute in parallel with progress tracking
    overall_rc = 0
    start_time = time.time()
    
    # Create progress bar if tqdm is available
    if TQDM_AVAILABLE:
        pbar = tqdm(total=len(tasks), desc="Executing modules", unit="module",
                   bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_module = {
            executor.submit(run_single_module_wrapper, task): task[4]  # task[4] is module name
            for task in tasks
        }
        
        # Process results as they complete
        for future in as_completed(future_to_module):
            module_name = future_to_module[future]
            try:
                module, rc = future.result()
                
                # Calculate progress info
                completed = len(tasks) - len([f for f in future_to_module if not f.done()])
                elapsed = time.time() - start_time
                avg_time = elapsed / completed if completed > 0 else 0
                remaining_tasks = len(tasks) - completed
                eta = avg_time * remaining_tasks if avg_time > 0 else 0
                
                if TQDM_AVAILABLE:
                    pbar.update(1)
                    if rc == 0:
                        pbar.set_postfix_str(f"✓ {module}")
                    else:
                        pbar.set_postfix_str(f"✗ {module} (rc={rc})")
                else:
                    # Fallback: print progress without tqdm
                    if rc == 0:
                        print(f"[INFO] [{completed}/{len(tasks)}] ✓ {module} completed (ETA: {eta:.0f}s)")
                    else:
                        print(f"[WARN] [{completed}/{len(tasks)}] ✗ {module} failed (rc={rc}, ETA: {eta:.0f}s)")
                
                if rc != 0:
                    overall_rc = overall_rc or rc
                    
            except Exception as e:
                if TQDM_AVAILABLE:
                    pbar.update(1)
                    pbar.set_postfix_str(f"✗ {module_name} (exception)")
                else:
                    print(f"[ERROR] Module {module_name} failed with exception: {e}")
                overall_rc = 1
    
    if TQDM_AVAILABLE:
        pbar.close()
    
    total_time = time.time() - start_time
    print(f"[INFO] All modules completed in {total_time:.1f}s (avg: {total_time/len(tasks):.1f}s per module)")
    
    return overall_rc


def main():
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"[ERROR] Root not found: {root}")
        return 2

    # Initialize log file in Work directory
    work_dir = root / "Work"
    work_dir.mkdir(parents=True, exist_ok=True)
    checkflow_log = work_dir / "Checkflow.log"
    
    # Start logging to file and console
    logger = TeeLogger(checkflow_log)
    sys.stdout = logger
    sys.stderr = logger
    
    try:
        return _execute_checks(root, args)
    finally:
        # Before restoring, write termination note directly to log
        logger.log_file.write(f"\n[INFO] Execution log saved to: {checkflow_log}\n")
        logger.log_file.flush()
        # Restore stdout/stderr and close log file
        sys.stdout = logger.terminal
        sys.stderr = sys.__stderr__
        logger.close()


def _execute_checks(root: Path, args) -> int:
    """Main execution logic (separated for clean logging)."""

    # Configure cache system based on command-line arguments
    try:
        from result_cache_manager import configure_global_cache
        
        # Determine cache directory
        if args.enable_file_cache:
            if args.cache_dir:
                cache_dir = Path(args.cache_dir).resolve()
            else:
                cache_dir = root / "Work" / ".cache"
            
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] File cache enabled: {cache_dir}")
            print(f"[INFO] Max memory cache size: {args.max_cache_size}")
        else:
            cache_dir = None
            print(f"[INFO] Memory-only cache enabled (max size: {args.max_cache_size})")
        
        # Configure global cache
        configure_global_cache(
            cache_dir=cache_dir,
            max_memory_size=args.max_cache_size,
            enable_file_cache=args.enable_file_cache
        )
    except Exception as e:
        print(f"[WARN] Cache configuration failed, using defaults: {e}")

    # Load config mapping: module -> list of items
    try:
        modules_map: Dict[str, List[str]] = get_check_modules(root=root, stage=args.stage)
        # Add debug output
        print(f"[DEBUG] Root path: {root}")
        print(f"[DEBUG] Stage: {args.stage}")
        print(f"[DEBUG] Available modules: {list(modules_map.keys())}")
        if args.check_module:
            print(f"[DEBUG] Looking for module: '{args.check_module}'")
    except Exception as e:
        print(f"[ERROR] Failed to obtain modules: {e}")
        return 3

    # Decide modules to run
    if args.check_module:
        if args.check_module not in modules_map:
            print(f"[ERROR] Module {args.check_module} not in config.")
            return 4
        modules = [args.check_module]
    else:
        modules = list(modules_map.keys())
        if not modules:
            print("[ERROR] No modules found in configuration.")
            return 5

    # Comprehensive cleanup (fresh run)
    _clean_generated(root, modules)
    
    # Step 0: Distribute DATA_INTERFACE data (if available and not skipped)
    if args.skip_distribution:
        print("\n" + "="*70)
        print("⚠️  DEVELOPMENT MODE: DATA_INTERFACE Distribution SKIPPED")
        print("="*70)
        print("[INFO] Using existing input files - manual edits will be preserved")
        print("[INFO] This mode is for checker development/testing only")
        print("="*70 + "\n")
    elif PARSE_INTERFACE_AVAILABLE:
        try:
            print("\n[INFO] Distributing DATA_INTERFACE data to check modules...")
            data_interface_path = root / "Data_interface" / "outputs" / "DATA_INTERFACE.yaml"
            if data_interface_path.exists():
                # Call parse_and_distribute with filtering parameters
                parse_and_distribute(
                    force=False, 
                    output_format='yaml',
                    check_modules=[args.check_module] if args.check_module else None,
                    check_items=args.check_items if args.check_items else None
                )
                print("[INFO] DATA_INTERFACE distribution completed\n")
            else:
                print(f"[WARN] DATA_INTERFACE not found: {data_interface_path}\n")
        except Exception as e:
            print(f"[WARN] DATA_INTERFACE distribution failed: {e}\n")
    else:
        print("\n[INFO] Skipping distribute DATA_INTERFACE data to check modules (parse_interface not available)\n")
    
    # Determine execution mode with intelligent defaults
    use_item_parallel = False
    use_module_parallel = False
    
    if args.item_parallel:
        # Explicit item-level parallel request
        use_item_parallel = True
        print("[INFO] Execution mode: Item-level parallel (explicit --item-parallel)")
    elif args.use_module_runners:
        # Explicit module-level request  
        use_module_parallel = not args.serial and len(modules) > 1
        print(f"[INFO] Execution mode: Module-level {'parallel' if use_module_parallel else 'serial'} (explicit --use-module-runners)")
    elif args.serial:
        # Explicit serial request
        use_module_parallel = False
        print("[INFO] Execution mode: Module-level serial (explicit --serial)")
    else:
        # Intelligent default: item-parallel for multi-module, module-runners for single module
        if len(modules) > 1:
            use_item_parallel = True
            print(f"[INFO] Execution mode: Item-level parallel (auto-selected for {len(modules)} modules)")
        else:
            use_module_parallel = False
            print(f"[INFO] Execution mode: Module-level serial (auto-selected for single module)")
    
    # Calculate optimal workers
    if use_item_parallel:
        # For item-level, estimate total items
        total_items = sum(len(modules_map.get(m, [])) for m in modules)
        max_workers = min(multiprocessing.cpu_count(), max(1, total_items))
    elif use_module_parallel:
        max_workers = _get_optimal_workers(len(modules))
    else:
        max_workers = 1
    
    # Execute checks based on selected mode
    if use_item_parallel:
        overall_rc = _run_items_parallel(root, modules, modules_map, 
                                        args.check_module, args.check_items, 
                                        max_workers)
    elif use_module_parallel:
        overall_rc = _run_modules_parallel(root, args, modules, modules_map, max_workers)
    else:
        overall_rc = _run_modules_serial(root, args, modules, modules_map)

    # Aggregate logs after running all modules (write under Work/)
    try:
        aggregated_log = log_generator(root=root, modules=modules, output_file=root / "Work" / "CheckList.log")
        print(f"[INFO] Aggregated log written: {aggregated_log}")
    except Exception as e:
        print(f"[WARN] Failed to generate aggregated log: {e}")

    # Print cache statistics after all checks completed
    try:
        from base_checker import BaseChecker
        if args.show_cache_stats:
            BaseChecker.print_cache_stats()
        else:
            stats = BaseChecker.get_cache_stats()
            if stats['total_requests'] > 0:
                print(f"\n[CACHE STATS] Requests: {stats['total_requests']}, Hits: {stats['hits']}, "
                      f"Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']}")
                if stats['evictions'] > 0:
                    print(f"[CACHE STATS] Evictions: {stats['evictions']} (consider increasing --max-cache-size)")
    except Exception:
        pass  # Cache stats are optional

    # Aggregate reports after running all modules (write under Work/)
    try:
        aggregated_rpt = rpt_generator(root=root, modules=modules, output_file=root / "Work" / "CheckList.rpt")
        print(f"[INFO] Aggregated report written: {aggregated_rpt}")
    except Exception as e:
        print(f"[WARN] Failed to generate aggregated report: {e}")

    # Generate summary YAML for each module (parse logs and reports)
    from write_summary_yaml import write_summary_yaml
    for mod in modules:
        try:
            items = modules_map.get(mod, [])
            if items:
                summary_yaml = write_summary_yaml(root, args.stage, mod, items)
                print(f"[INFO] Summary YAML written: {summary_yaml}")
        except Exception as e:
            print(f"[WARN] Failed to generate summary YAML for {mod}: {e}")

    # Generate Excel (.xlsx) for each module from its summary YAML (requires openpyxl)
    for mod in modules:
        try:
            summary_yaml = root / "Check_modules" / mod / "outputs" / f"{mod}.yaml"
            if not summary_yaml.is_file():
                print(f"[WARN] Summary YAML missing, skip Excel/CSV: {summary_yaml}")
                continue
            produced = summary_yaml_to_excel(summary_yaml, root)
            if produced:
                print(f"[INFO] Tabular summary written: {produced}")
        except Exception as e:
            print(f"[WARN] Failed to generate Excel/CSV for {mod}: {e}")

    # After all modules processed, produce a single aggregated Origin.xlsx
    try:
        template_xlsx = root / "Project_config" / "collaterals" / "Initial" / "latest" / "DR3_SSCET_BE_Check_List_v0.1.xlsx"
        if template_xlsx.is_file():
            out_xlsx = root / "Work" / "Results" / "Origin.xlsx"
            out_xlsx.parent.mkdir(parents=True, exist_ok=True)
            # Use explicit summaries from this run (avoid stale ones)
            summary_list = [root / "Check_modules" / m / "outputs" / f"{m}.yaml" for m in modules if (root / "Check_modules" / m / "outputs" / f"{m}.yaml").is_file()]
            if summary_list:
                annotate_excel_template_multi(summary_list, template_xlsx, sheet="BE_check", out_xlsx=out_xlsx)
                print(f"[INFO] Aggregated annotated Excel written: {out_xlsx}")
            else:
                print("[INFO] No summary YAMLs from this run; attempting auto annotation")
                try:
                    annotate_excel_template_auto(root, template_xlsx, sheet="BE_check", out_xlsx=out_xlsx)
                    print(f"[INFO] Auto annotated Excel written: {out_xlsx}")
                except Exception as inner:
                    print(f"[INFO] Skip Origin.xlsx (auto): {inner}")
        else:
            print(f"[INFO] Template Excel not found, skip aggregated annotation: {template_xlsx}")
    except Exception as e:
        print(f"[WARN] Aggregated checklist Excel annotation failed: {e}")

    # Generate aggregated Summary.xlsx using only summaries from this run (falls back to auto if none)
    try:
        summary_list = [root / "Check_modules" / m / "outputs" / f"{m}.yaml" for m in modules if (root / "Check_modules" / m / "outputs" / f"{m}.yaml").is_file()]
        if summary_list:
            summary_path = build_summary(root=root, summary_yamls=summary_list)
        else:
            summary_path = build_summary(root=root)
        print(f"[INFO] Aggregated Summary.xlsx generated: {summary_path}")
    except SystemExit as e:
        print(f"[INFO] Skip Summary.xlsx: {e}")
    except Exception as e:
        print(f"[WARN] Failed to build aggregated Summary.xlsx: {e}")
    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
