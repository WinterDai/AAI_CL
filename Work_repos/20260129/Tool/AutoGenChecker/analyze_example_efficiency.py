"""
Analysis: Is CheckerExampleCollector scanning too much?

This script analyzes the performance and relevance issues with the current implementation.
"""

import sys
import time
from pathlib import Path

_parent_dir = Path(__file__).parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

print("\n" + "="*80)
print("ANALYSIS: CheckerExampleCollector Efficiency Issues")
print("="*80 + "\n")

# 1. Count total checkers in workspace
print("1. Counting total checker scripts...")
print("-" * 80)

from utils.paths import discover_project_paths

paths = discover_project_paths()
check_modules_root = paths.workspace_root / "Check_modules"

total_checkers = 0
if check_modules_root.exists():
    for module_dir in check_modules_root.iterdir():
        if module_dir.is_dir() and module_dir.name.lower() != "common":
            scripts_dir = module_dir / "scripts" / "checker"
            if scripts_dir.exists():
                checker_count = len(list(scripts_dir.glob("*.py")))
                if checker_count > 0:
                    print(f"   {module_dir.name}: {checker_count} checkers")
                    total_checkers += checker_count

print(f"\n   => TOTAL: {total_checkers} checker scripts in workspace")

# 2. Measure scanning time
print("\n2. Measuring scan time...")
print("-" * 80)

from context_collectors.checker_examples import CheckerExampleCollector

start_time = time.time()
collector = CheckerExampleCollector(max_examples=3, max_script_chars=1600)
fragments = list(collector.collect())
scan_time = time.time() - start_time

print(f"   => Scanned {total_checkers} checkers in {scan_time:.2f} seconds")
print(f"   => Collected {len(fragments)} examples")
print(f"   => Scan time per checker: {scan_time/max(total_checkers, 1)*1000:.1f}ms")

# 3. Check if examples are relevant
print("\n3. Relevance Analysis...")
print("-" * 80)

# Simulate: developing IMP-15-0-0-01 (ESD module)
target_module = "15.0_ESD_PERC_CHECK"
target_item = "IMP-15-0-0-01"

print(f"   Target: {target_item} in module {target_module}")
print(f"\n   Examples collected:")

relevant_count = 0
for i, frag in enumerate(fragments, 1):
    source_path = Path(frag.source)
    source_module = source_path.parents[2].name  # Get module name
    is_relevant = target_module in source_module
    relevance = "RELEVANT" if is_relevant else "NOT RELEVANT"
    print(f"   {i}. {source_path.name} from {source_module} - {relevance}")
    if is_relevant:
        relevant_count += 1

print(f"\n   => {relevant_count}/{len(fragments)} examples are from the same module")
print(f"   => {len(fragments) - relevant_count}/{len(fragments)} examples are from OTHER modules (noise?)")

# 4. Problems summary
print("\n" + "="*80)
print("PROBLEMS IDENTIFIED")
print("="*80 + "\n")

print("1. PERFORMANCE ISSUE:")
print(f"   - Scans ALL {total_checkers} checkers every time (even if only need 3)")
print(f"   - Takes {scan_time:.2f}s per generation")
print(f"   - No caching mechanism")
print()

print("2. RELEVANCE ISSUE:")
print(f"   - Current selection is RANDOM (first {len(fragments)} found)")
print("   - May select examples from completely different modules")
print("   - No similarity or relevance scoring")
print()

print("3. TOKEN WASTE:")
print("   - Each example uses ~1600 chars")
print(f"   - Total: ~{len(fragments) * 1600} chars for examples")
print("   - If examples are irrelevant, this is wasted context")

# 5. Solutions
print("\n" + "="*80)
print("PROPOSED SOLUTIONS")
print("="*80 + "\n")

print("SOLUTION 1: Smart Example Selection (BEST)")
print("  - Prioritize examples from SAME MODULE")
print("  - Fall back to other modules if not enough examples")
print("  - Use semantic similarity (check description/patterns)")
print()

print("SOLUTION 2: Caching")
print("  - Cache scanned examples on first run")
print("  - Reuse cache for subsequent generations")
print("  - Invalidate only when checker files change")
print()

print("SOLUTION 3: Lazy Loading")
print("  - Don't scan all modules upfront")
print("  - Scan target module first (fast)")
print("  - Only scan other modules if needed")
print()

print("SOLUTION 4: Configurable Selection")
print("  - Add 'same_module_only' parameter")
print("  - Add 'similarity_threshold' parameter")
print("  - Allow manual example selection")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80 + "\n")

print("Implement SOLUTION 1 + 2 + 3 together:")
print()
print("class CheckerExampleCollector:")
print("    def __init__(self,")
print("                 max_examples=3,")
print("                 prefer_same_module=True,  # NEW")
print("                 use_cache=True):          # NEW")
print()
print("    def collect(self, request):")
print("        # 1. Check cache first")
print("        # 2. If prefer_same_module:")
print("        #    - Scan target module only (fast!)")
print("        #    - If enough examples, return immediately")
print("        #    - Otherwise, scan other modules")
print("        # 3. Score examples by relevance")
print("        # 4. Return top N most relevant examples")
print()
print("BENEFITS:")
print("  - 10-100x faster (only scan 1 module usually)")
print("  - Higher relevance (same module examples)")
print("  - Better token efficiency")
print("  - Cached for repeat runs")

print("\n" + "="*80)
