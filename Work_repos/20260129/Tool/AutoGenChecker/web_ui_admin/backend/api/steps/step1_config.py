"""
Step 1: Configuration Management
Corresponds to CLI's configuration loading and validation.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml
import glob

router = APIRouter()

# Get CHECKLIST root directory
CHECKLIST_ROOT = Path(os.environ.get(
    "CHECKLIST_ROOT",
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent / "CHECKLIST"
))

CHECK_MODULES_DIR = CHECKLIST_ROOT / "Check_modules"


class ModuleInfo(BaseModel):
    """Module information model."""
    module_id: str
    module_name: str
    item_count: int
    items: List[str]


class ItemDetail(BaseModel):
    """Item detail model."""
    item_id: str
    module: str
    description: str
    requirements: Dict[str, Any]
    input_files: List[str]
    waivers: Dict[str, Any]
    yaml_path: str


class YamlUpdateRequest(BaseModel):
    """YAML update request model."""
    yaml_content: str


def expand_checklist_root(text: str) -> str:
    """Expand ${CHECKLIST_ROOT} variable in text."""
    if not text:
        return text
    return text.replace("${CHECKLIST_ROOT}", str(CHECKLIST_ROOT))


def expand_file_patterns(patterns: List[str]) -> List[str]:
    """Expand glob patterns and ${CHECKLIST_ROOT} in file paths."""
    expanded_files = []
    for pattern in patterns:
        # Expand CHECKLIST_ROOT variable
        expanded_pattern = expand_checklist_root(pattern)
        
        # Glob expansion
        matched_files = glob.glob(expanded_pattern, recursive=True)
        if matched_files:
            expanded_files.extend(matched_files)
        else:
            # Keep original if no match (might be a reference file)
            expanded_files.append(expanded_pattern)
    
    return expanded_files


@router.get("/modules", response_model=List[ModuleInfo])
async def list_modules():
    """List all available checker modules."""
    if not CHECK_MODULES_DIR.exists():
        raise HTTPException(status_code=404, detail=f"Check_modules directory not found: {CHECK_MODULES_DIR}")
    
    modules = []
    
    for module_dir in sorted(CHECK_MODULES_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name == "common":
            continue
        
        # Find all YAML files in inputs/items/
        items_dir = module_dir / "inputs" / "items"
        items = []
        
        if items_dir.exists():
            yaml_files = list(items_dir.glob("*.yaml")) + list(items_dir.glob("*.yml"))
            items = [f.stem for f in yaml_files]
        
        modules.append(ModuleInfo(
            module_id=module_dir.name,
            module_name=module_dir.name.replace("_", " ").title(),
            item_count=len(items),
            items=items
        ))
    
    return modules


@router.get("/modules/{module_id}/items/{item_id}", response_model=ItemDetail)
async def get_item_detail(module_id: str, item_id: str):
    """Get detailed information for a specific item."""
    module_dir = CHECK_MODULES_DIR / module_id
    
    if not module_dir.exists():
        raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")
    
    # Try to find YAML file
    items_dir = module_dir / "inputs" / "items"
    yaml_path = items_dir / f"{item_id}.yaml"
    
    if not yaml_path.exists():
        yaml_path = items_dir / f"{item_id}.yml"
    
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail=f"Item YAML not found: {item_id}")
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        # Extract data with defaults - keep original format without expansion
        description = yaml_data.get("description", "No description")
        requirements = yaml_data.get("requirements", {"value": "N/A", "pattern_items": []})
        input_files = yaml_data.get("input_files", [])  # Keep original paths with ${CHECKLIST_ROOT}
        waivers = yaml_data.get("waivers", {"value": "N/A", "waive_items": []})
        
        # NOTE: Do NOT expand input_files here - keep ${CHECKLIST_ROOT} variable format
        # The checker will expand them at runtime using parse_interface.py
        
        return ItemDetail(
            item_id=item_id,
            module=module_id,
            description=description,
            requirements=requirements,
            input_files=input_files,  # Keep original format
            waivers=waivers,
            yaml_path=str(yaml_path)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading YAML: {str(e)}")


@router.put("/modules/{module_id}/items/{item_id}")
async def update_item_yaml(module_id: str, item_id: str, request: YamlUpdateRequest):
    """Update YAML file content for a specific item."""
    module_dir = CHECK_MODULES_DIR / module_id
    
    if not module_dir.exists():
        raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")
    
    # Find YAML file
    items_dir = module_dir / "inputs" / "items"
    yaml_path = items_dir / f"{item_id}.yaml"
    
    if not yaml_path.exists():
        yaml_path = items_dir / f"{item_id}.yml"
    
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail=f"Item YAML not found: {item_id}")
    
    try:
        # Parse the YAML content to validate it
        yaml_data = yaml.safe_load(request.yaml_content)
        
        # Write back to file
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(request.yaml_content)
        
        return {
            "status": "success",
            "message": f"YAML file updated: {yaml_path}",
            "item_id": item_id,
            "module": module_id
        }
    
    except yaml.YAMLError as e:
        error_msg = str(e)
        # Provide helpful hints for common errors
        if "mapping values are not allowed" in error_msg:
            error_msg += "\n\n💡 提示：description字段中包含冒号(:)时需要加引号\n例如：description: \"Block name (e.g: cdn_hs_phy_data_slice)\""
        raise HTTPException(status_code=400, detail=f"YAML格式错误: {error_msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving YAML: {str(e)}")


@router.get("/checklist-root")
async def get_checklist_root():
    """Get CHECKLIST root directory path."""
    return {
        "checklist_root": str(CHECKLIST_ROOT),
        "check_modules_dir": str(CHECK_MODULES_DIR),
        "exists": CHECK_MODULES_DIR.exists()
    }


@router.get("/modules/{module_id}/items/{item_id}/resume-status")
async def get_resume_status(module_id: str, item_id: str):
    """
    Get resume status for an item.
    
    Returns information about which steps can be resumed from,
    based on existing cached files (config, file_analysis, readme, code).
    
    This matches CLI's _load_cached_data() functionality.
    """
    try:
        from .resume_manager import get_resume_manager
        
        manager = get_resume_manager(module_id, item_id)
        status = manager.get_resume_status()
        
        return {
            "status": "success",
            **status
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "module": module_id,
            "item_id": item_id,
            "can_resume": {i: i == 1 for i in range(1, 10)},
            "suggested_resume_step": 1,
        }
