################################################################################
# Script Name: get_path.py
#
# Purpose:
#   Centralize path resolution helpers for project structure (modules, inputs, outputs).
#
# Usage:
#   from get_path import get_module_root, get_inputs_dir, get_outputs_dir, get_reports_dir
#
# Author: yyin
# Date:   2025-10-23
################################################################################
import os
from pathlib import Path
from typing import Sequence, Union, List, Optional



def get_path(root: Union[str, Path] = "..",   # default to current directory
             recursive: bool = True,
             include_ext: Optional[Sequence[str]] = None,
             exclude_ext: Sequence[str] = (),
             relative: bool = False) -> List[str]:
    """
    Collect file paths under a directory.
    """
    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        raise NotADirectoryError(f"CheckList directory not found: {base}")

    incl = set(e.lower() for e in include_ext) if include_ext else None
    excl = set(e.lower() for e in exclude_ext)

    if recursive:
        itr = (p for p in base.rglob("*") if p.is_file())
    else:
        itr = (p for p in base.iterdir() if p.is_file())

    total_paths: List[str] = []
    seen = set()
    for p in itr:
        ext = p.suffix.lower()
        if incl and ext not in incl:
            continue
        if ext in excl:
            continue
        val = str(p.relative_to(base) if relative else p.resolve())
        if val not in seen:
            seen.add(val)
            total_paths.append(val)

    total_paths.sort()
    return total_paths

def get_inputs_path(root: Union[str, Path] = "..",
                    stage: Optional[str] = None,
                    check_module: Optional[str] = None) -> List[str]:
    """
    Build list of input paths:
      1. All immediate subdirectories in .../IP_project_folder/
      2. The two config YAML files under .../Project_config/prep_config/<Stage>/latest/
         (CheckList_Index.yaml, design_config.yaml)
      3. The waiver file .../Waiver_config/5.0_SYNTHESIS/waive.yaml
    Stage is taken from argument, or env vars Stage / STAGE.
    """
    base = Path(root).expanduser().resolve()
    ip_root = base / "IP_project_folder"

    # Determine stage and check_module
    stage_val = stage or os.environ.get("Stage") or os.environ.get("STAGE")
    check_module = check_module  or os.environ.get("CheckModule") or os.environ.get("check_module")
    if not stage_val:
        raise ValueError("Stage not specified and environment variable 'Stage' or 'STAGE' not set")

    config_dir = base / "Project_config" / "prep_config" / stage_val / "latest"
    waiver_file = base / "Waiver_config" / check_module / "waive.yaml"

    input_paths: List[str] = []

    # 1. All subdirectories (only directories) under IP_project_folder
    if ip_root.is_dir():
        for p in sorted(ip_root.iterdir()):
            if p.is_dir():
                input_paths.append(str(p.resolve()))
    else:
        raise NotADirectoryError(f"Missing IP_project_folder directory: {ip_root}")

    # 2. Config YAML files
    for cfg_name in ("CheckList_Index.yaml", "design_config.yaml"):
        cfg_path = config_dir / cfg_name
        if cfg_path.exists():
            input_paths.append(str(cfg_path.resolve()))
        else:
            # Still include non-existing path? Decide to skip; comment below:
            # To include even if missing, uncomment next line:
            # input_paths.append(str(cfg_path))
            pass

    # 3. Waiver file
    if waiver_file.exists():
        input_paths.append(str(waiver_file.resolve()))
    else:
        print(f"Warning: Waiver file not found: {waiver_file}")

    # De-duplicate while preserving order
    seen: set[str] = set()
    deduped: List[str] = []
    for p in input_paths:
        if p not in seen:
            seen.add(p)
            deduped.append(p)

    return deduped

#if __name__ == "__main__":
    #print("\n".join(get_path("..")))
    #print("-----")
    #print("\n".join(get_inputs_path("..", stage="Initial", check_module="5.0_SYNTHESIS_CHECK")))
    #print("-----")
    #print("\n".join(link_input_path("..", stage="Initial", check_module="5.0_SYNTHESIS_CHECK")))