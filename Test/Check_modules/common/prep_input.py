################################################################################
# Script Name: prep_input.py
#
# Purpose:
#   Prepare input directories, copy or stage configuration collateral before checks run.
#
# Usage:
#   python prep_input.py -root <ROOT> -stage <STAGE>
#
# Author: yyin
# Date:   2025-10-23
################################################################################
from pathlib import Path
from typing import Union, List, Optional, Iterable
from get_path import get_inputs_path
from get_check import get_check_modules

def link_input_path(root: Union[str, Path] = "..",
                    stage: Optional[str] = None,
                    check_module: Union[str, Iterable[str]] = None) -> List[str]:

    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        raise NotADirectoryError(f"CheckList directory not found: {base}")
    
    if check_module is None:
        modules = get_check_modules(base, stage)
        if not modules:
            raise ValueError("No check modules found in CheckList directory.")
        
    elif isinstance(check_module, str):
        modules = [check_module]
    else:
        modules = list(check_module)


    linked_paths: List[str] = []
    
    for check_module in modules:
        output_dir = base / "Check_modules" / check_module / "inputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        input_paths = get_inputs_path(root, stage, check_module)

        if not output_dir.is_dir():
            raise NotADirectoryError(f"Check_modules directory not found: {output_dir}")

    for p in input_paths:
            src = Path(p).expanduser().resolve()

            if not src.exists():
                print(f"Warning: Input not found: {src}")
                continue


            dest = output_dir / src.name
            # If destination already exists:
            if dest.exists():
                # If it's the same kind of link pointing to same target, keep it
                if dest.is_symlink():
                    try:
                        if dest.resolve() == src:
                            linked_paths.append(str(dest))
                            continue  # reuse existing symlink
                        else:
                            dest.unlink()  # different target, replace
                    except Exception:
                        dest.unlink()  # broken link, replace
                else:
                    # If it's a directory or regular file, don't overwrite; skip linking to avoid exception.
                    # User may have copied resources manually.
                    linked_paths.append(str(dest))
                    continue
            try:
                dest.symlink_to(src)
            except OSError:
                # Windows may require admin for symlink; fallback to copy for files.
                try:
                    import shutil
                    if src.is_file():
                        shutil.copy2(src, dest)
                    elif src.is_dir():
                        shutil.copytree(src, dest)
                except Exception as e:
                    print(f"Warning: Could not link or copy {src} -> {dest}: {e}")
            linked_paths.append(str(dest))

    return linked_paths

#if __name__ == "__main__":
    #print("\n".join(link_input_path("..", stage="Initial", check_module="5.0_SYNTHESIS_CHECK")))
    #print("\n".join(link_input_path("..", stage="Initial")))