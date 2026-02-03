################################################################################
# Script Name: log_generator.py
#
# Purpose:
#   Aggregate per-module *.log files into a single CheckList.log for overview.
#
# Usage:
#   from log_generator import log_generator
#   log_generator(Path(root), ["5.0_SYNTHESIS_CHECK"])  # writes CheckList.log in CWD
#
# Author: yyin
# Date:   2025-10-23
################################################################################
from pathlib import Path
from typing import List, Optional

def log_generator(root: Path,
                  modules: List[str],
                  output_file: Optional[Path] = None) -> Path:
    """
    Aggregate all .log files under each module's logs/ directory into one file.

    root: Root of the CheckList (the -root argument used when running checks)
    modules: List of module names that were executed
    output_file: Optional explicit output path (default: ./CheckList.log in CWD)

    Returns the path to the aggregated log file.
    """
    if output_file is None:
        output_file = Path.cwd() / "CheckList.log"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8", errors="ignore") as out:
        out.write("===== CheckList Aggregated Log =====\n")
        out.write(f"Root: {root}\n")
        out.write(f"Modules: {', '.join(modules)}\n\n")

        any_logs = False
        for module in modules:
            logs_dir = root / "Check_modules" / module / "logs"
            if not logs_dir.is_dir():
                continue
            log_files = sorted(logs_dir.glob("*.log"))
            if not log_files:
                continue
            out.write(f"\n===== Module: {module} =====\n")
            for lf in log_files:
                out.write(f"\n--- {lf.name} ---\n")
                try:
                    with lf.open("r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            out.write(line)
                except Exception as e:
                    out.write(f"[ERROR] Could not read {lf}: {e}\n")
                any_logs = True

        if not any_logs:
            out.write("No log files found for the given modules.\n")

    return output_file