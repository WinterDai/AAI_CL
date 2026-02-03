import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional, Tuple
import shutil
import yaml  # still used if needed elsewhere
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time

# Try to import tqdm for progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Add the common directory to Python path for imports
script_dir = Path(__file__).parent
common_dir = script_dir.parent.parent / "common"
sys.path.insert(0, str(common_dir))

from prep_input import link_input_path
from get_check import get_check_modules
from write_summary_yaml import write_summary_yaml   # NEW

DEFAULT_MODULE = "8.1_PHYSICAL_IMPLEMENTATION_CHECK"

def run_check_item(script: Path) -> Tuple[str, bool]:
    """
    Run a single checker script. Returns (item_id, success).
    Pass/fail will be determined later from log by write_summary_yaml.
    """
    item_id = script.stem
    if not script.is_file():
        return (item_id, False)
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=600,
        )
        return (item_id, True)
    except Exception:
        return (item_id, True)  # executed attempt, even if failed


def _get_optimal_item_workers(num_items: int) -> int:
    """Calculate optimal number of workers for item-level parallelism."""
    cpu_count = multiprocessing.cpu_count()
    
    if num_items == 1:
        return 1
    elif num_items == 2:
        return 2
    elif num_items <= 4:
        return min(num_items, max(2, int(cpu_count * 0.5)))
    else:
        # For many items, use 75% of CPUs
        return min(num_items, max(2, int(cpu_count * 0.75)))

def run_checks(root: str = "..",
               stage: str = "Initial",
               check_module: str = DEFAULT_MODULE,
               check_items: Optional[List[str]] = None,
               parallel: bool = True):
    base = Path(root).expanduser().resolve()
    module_dir = base / "Check_modules" / check_module
    if not module_dir.is_dir():
        raise NotADirectoryError(f"Module directory not found: {module_dir}")

    # Refresh artifact dirs
    for sub in ("logs", "reports", "outputs"):
        d = module_dir / sub
        if d.exists():
            for p in d.iterdir():
                try:
                    if p.is_file() or p.is_symlink():
                        p.unlink()
                    elif p.is_dir():
                        shutil.rmtree(p, ignore_errors=True)
                except Exception:
                    pass
        else:
            d.mkdir(parents=True, exist_ok=True)

    # Link inputs
    #link_input_path(root=root, stage=stage, check_module=check_module)

    # Determine items
    if not check_items:
        modules_map = get_check_modules(root=root, stage=stage)
        if check_module not in modules_map:
            raise ValueError(f"Check module not found in config: {check_module}")
        check_items = modules_map[check_module]
        if not check_items:
            raise ValueError(f"No check items defined for module: {check_module}")

    # Prepare item scripts
    item_scripts = [(item, module_dir / "scripts" / "checker" / f"{item}.py") for item in check_items]
    
    # Execute items (parallel or serial)
    if parallel and len(item_scripts) > 1:
        max_workers = _get_optimal_item_workers(len(item_scripts))
        print(f"[INFO] Running {len(item_scripts)} item(s) in parallel with {max_workers} worker(s)")
        _run_items_parallel(item_scripts, max_workers)
    else:
        if len(item_scripts) == 1:
            print(f"[INFO] Running single item {item_scripts[0][0]}")
        else:
            print(f"[INFO] Running {len(item_scripts)} item(s) serially")
        _run_items_serial(item_scripts)

    # Delegate YAML creation to common helper
    summary_yaml, has_failures = write_summary_yaml(base, stage, check_module, check_items)
    
    # Return exit code based on failures
    if has_failures:
        print(f"[INFO] Summary written to {summary_yaml} (contains failures)")
        sys.exit(1)
    else:
        print(f"[INFO] Summary written to {summary_yaml} (all passed)")
        sys.exit(0)


def _run_items_serial(item_scripts: List[Tuple[str, Path]]):
    """Execute items one by one."""
    for item_id, script in item_scripts:
        run_check_item(script)


def _run_items_parallel(item_scripts: List[Tuple[str, Path]], max_workers: int):
    """Execute items in parallel with progress tracking."""
    start_time = time.time()
    
    # Create progress bar if tqdm is available
    if TQDM_AVAILABLE:
        pbar = tqdm(total=len(item_scripts), desc="Checking items", unit="item",
                   bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {
            executor.submit(run_check_item, script): item_id
            for item_id, script in item_scripts
        }
        
        # Process results as they complete
        for future in as_completed(future_to_item):
            item_id = future_to_item[future]
            try:
                result_item, success = future.result()
                
                if TQDM_AVAILABLE:
                    pbar.update(1)
                    pbar.set_postfix_str(f"✓ {result_item}")
                else:
                    completed = len(item_scripts) - len([f for f in future_to_item if not f.done()])
                    print(f"[INFO] [{completed}/{len(item_scripts)}] ✓ {result_item} completed")
                    
            except Exception as e:
                if TQDM_AVAILABLE:
                    pbar.update(1)
                    pbar.set_postfix_str(f"✗ {item_id} (error)")
                else:
                    print(f"[ERROR] Item {item_id} failed: {e}")
    
    if TQDM_AVAILABLE:
        pbar.close()
    
    total_time = time.time() - start_time
    print(f"[INFO] All items completed in {total_time:.1f}s (avg: {total_time/len(item_scripts):.1f}s per item)")

def parse_args():
    p = argparse.ArgumentParser(description="Run synthesis check items and produce structured YAML summary.")
    p.add_argument("-root", default="..", help="Root CheckList directory")
    p.add_argument("-stage", default="Initial", help="Stage name (default: Initial)")
    p.add_argument("-check_module", default=DEFAULT_MODULE, help="Check module name")
    p.add_argument("-check_item", nargs="*", help="Specific check items (override config)")
    p.add_argument("--serial", action="store_true", help="Force serial execution of items")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_checks(root=args.root,
               stage=args.stage,
               check_module=args.check_module,
               check_items=args.check_item,
               parallel=not args.serial)
    # Exit code is handled by run_checks() via sys.exit()
