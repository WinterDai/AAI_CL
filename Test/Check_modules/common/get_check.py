################################################################################
# Script Name: get_check.py
#
# Purpose:
#   Provide utilities to read checklist index YAML and return modules/items to execute.
#
# Usage:
#   from get_check import get_check_modules, get_items_for_module
#
# Author: yyin
# Date:   2025-10-23
################################################################################
from pathlib import Path
from typing import Union, List, Optional, Dict
from read_yaml import read_yaml

def get_check_modules(root: Union[str, Path] = "..", 
                      stage: Optional[str] = None) -> Dict[str, List[str]]:
    
    base = Path(root).expanduser().resolve()
    if not stage:
        raise ValueError("Stage must be specified (e.g. 'Initial').")
    config_dir = base / "Project_config" / "prep_config" / stage / "latest"

    # 1. find CheckList_Index.yaml
    index_file = config_dir / "CheckList_Index.yaml"
    if not index_file.exists():
        raise FileNotFoundError(f"CheckList_Index.yaml not found: {index_file}")
    
    index_data = read_yaml(index_file)
    
    # 2. parse and return module names and checklist items
    if not index_data:
        raise ValueError(f"No data found in CheckList_Index.yaml: {index_file}")      

    result = {}
    for module_name, module_content in index_data.items():
        #print(f"Found check module: {module_name}")
        checklist_items = module_content.get("checklist_item", [])
        prompt_items = module_content.get("prompt_item", [])

        #print(f"  with {len(checklist_items)} checklist items.")
        #print(f"  with {len(prompt_items)} prompt items.")

        result[module_name] = [list(item.keys())[0] if isinstance(item, dict) else item for item in checklist_items]

    return result

#if __name__ == "__main__":
    #modules = get_check_modules("..", stage="Initial")
    #for mod, items in modules.items():
        #print(f"\nModule: {mod}")
        #for item in items:
            #print(f"  - {item}")
    #print(f"\nTotal modules found: {len(modules)}")