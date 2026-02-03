"""
Workflow Integration API - 集成分发、开发、回收三个核心模块

1. 分发 (Dispatch): 根据username/items创建开发者工作目录
2. 开发 (Development): 当前WebUI的9步生成流程
3. 回收 (Collection): 收集完成的checker核心文件
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import traceback
from pathlib import Path
import shutil
import yaml
import os
from datetime import datetime

router = APIRouter()


# ============================================================================
# Data Models
# ============================================================================

class DispatchRequest(BaseModel):
    """分发请求模型"""
    developer_name: str
    modules: List[str]  # e.g., ["8.0_PHYSICAL_IMPLEMENTATION_CHECK", "11.0_POWER_EMIR_CHECK"]
    items: Optional[List[str]] = None  # Optional: specific item IDs
    include_reference: bool = True  # Include reference module


class CollectRequest(BaseModel):
    """回收请求模型"""
    developer_name: str
    module: str
    item_id: str


class CollectBatchRequest(BaseModel):
    """批量回收请求模型"""
    developer_name: str
    items: List[Dict[str, str]]  # [{"module": "...", "item_id": "..."}]


class ItemStatus(BaseModel):
    """Item状态模型"""
    item_id: str
    module: str
    has_yaml: bool = False
    has_checker: bool = False
    has_readme: bool = False
    has_input_files: bool = False
    is_complete: bool = False
    yaml_path: Optional[str] = None
    checker_path: Optional[str] = None
    readme_path: Optional[str] = None
    input_files: List[str] = []


# ============================================================================
# Helper Functions
# ============================================================================

def get_workspace_root() -> Path:
    """获取workspace根目录"""
    try:
        from utils.paths import discover_project_paths
    except ImportError:
        from AutoGenChecker.utils.paths import discover_project_paths
    
    paths = discover_project_paths()
    return paths.workspace_root


def get_developer_workspace(developer_name: str) -> Path:
    """获取开发者工作目录"""
    workspace_root = get_workspace_root()
    # 开发者workspace在 Mdispatcher/workspaces/ 下
    mdispatcher_dir = workspace_root.parent / "Tool" / "Mdispatcher"
    return mdispatcher_dir / "workspaces" / f"{developer_name}_workspace"


def check_item_status(module: str, item_id: str, workspace_root: Path = None) -> ItemStatus:
    """检查item的完成状态"""
    if workspace_root is None:
        workspace_root = get_workspace_root()
    
    module_dir = workspace_root / "Check_modules" / module
    
    status = ItemStatus(item_id=item_id, module=module)
    
    # Check YAML config
    yaml_path = module_dir / "inputs" / "items" / f"{item_id}.yaml"
    if yaml_path.exists():
        status.has_yaml = True
        status.yaml_path = str(yaml_path.relative_to(workspace_root))
        
        # Parse YAML to get input files
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if config and 'input_files' in config:
                status.input_files = config['input_files']
                status.has_input_files = len(status.input_files) > 0
        except:
            pass
    
    # Check checker script
    checker_path = module_dir / "scripts" / "checker" / f"{item_id}.py"
    if checker_path.exists():
        status.has_checker = True
        status.checker_path = str(checker_path.relative_to(workspace_root))
    
    # Check README
    readme_path = module_dir / "scripts" / "doc" / f"{item_id}_README.md"
    if readme_path.exists():
        status.has_readme = True
        status.readme_path = str(readme_path.relative_to(workspace_root))
    
    # Check if complete (all required files exist)
    status.is_complete = status.has_yaml and status.has_checker and status.has_readme
    
    return status


# ============================================================================
# 1. 分发 (Dispatch) APIs
# ============================================================================

@router.post("/dispatch/create-workspace")
async def create_developer_workspace(request: DispatchRequest):
    """
    创建开发者工作目录
    
    包含:
    - CHECKLIST/ (过滤后的Check_modules + common + Data_interface + Work + doc + IP_project_folder + Project_config)
    - Tool/AutoGenChecker/ (完整)
    - ssg_aai_lego/ (完整)
    """
    try:
        workspace_root = get_workspace_root()
        
        # Import pack_for_developer function
        mdispatcher_dir = workspace_root.parent / "Tool" / "Mdispatcher"
        import sys
        sys.path.insert(0, str(mdispatcher_dir))
        
        from pack_for_developer import pack_for_developer
        
        # Prepare items_by_module if specific items provided
        items_by_module = None
        if request.items:
            items_by_module = {}
            for item_id in request.items:
                # Find module for each item
                for module in request.modules:
                    module_dir = workspace_root / "Check_modules" / module
                    yaml_path = module_dir / "inputs" / "items" / f"{item_id}.yaml"
                    if yaml_path.exists():
                        if module not in items_by_module:
                            items_by_module[module] = []
                        items_by_module[module].append(item_id)
                        break
        
        # Create workspace
        output_dir = mdispatcher_dir / "workspaces"
        output_dir.mkdir(exist_ok=True)
        
        pack_for_developer(
            developer_name=request.developer_name,
            modules=request.modules,
            output_dir=str(output_dir),
            github_workflow=True,
            create_zip=False,
            items_by_module=items_by_module
        )
        
        # Find the created workspace
        workspaces = list(output_dir.glob(f"{request.developer_name}_workspace_*"))
        if workspaces:
            latest_workspace = max(workspaces, key=lambda p: p.stat().st_mtime)
            workspace_path = str(latest_workspace)
        else:
            workspace_path = str(output_dir / f"{request.developer_name}_workspace")
        
        return {
            "status": "success",
            "message": f"Workspace created for {request.developer_name}",
            "workspace_path": workspace_path,
            "modules": request.modules,
            "items_count": len(request.items) if request.items else "all"
        }
        
    except Exception as e:
        error_msg = f"Failed to create workspace: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        return {
            "status": "error",
            "error": error_msg
        }


@router.get("/dispatch/developers")
async def list_developers():
    """获取所有开发者列表（从assignments目录）"""
    try:
        workspace_root = get_workspace_root()
        assignments_dir = workspace_root / "Work" / "assignments"
        
        developers = set()
        if assignments_dir.exists():
            for f in assignments_dir.glob("*.yaml"):
                # Extract developer name from filename: {developer}_{modules}_{timestamp}.yaml
                name = f.stem.split('_')[0]
                if name:
                    developers.add(name)
        
        return {
            "status": "success",
            "developers": sorted(list(developers))
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/dispatch/assignments/{developer_name}")
async def get_developer_assignments(developer_name: str):
    """获取开发者的任务分配"""
    try:
        workspace_root = get_workspace_root()
        assignments_dir = workspace_root / "Work" / "assignments"
        
        assignments = []
        if assignments_dir.exists():
            for f in assignments_dir.glob(f"{developer_name}_*.yaml"):
                with open(f, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    if data:
                        data['filename'] = f.name
                        assignments.append(data)
        
        return {
            "status": "success",
            "developer": developer_name,
            "assignments": assignments
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# 2. 开发状态 (Development Status) APIs
# ============================================================================

@router.get("/development/status/{developer_name}")
async def get_development_status(developer_name: str):
    """获取开发者的开发进度"""
    try:
        workspace_root = get_workspace_root()
        assignments_dir = workspace_root / "Work" / "assignments"
        
        # Load all assignments for this developer
        all_items = []
        for f in assignments_dir.glob(f"{developer_name}_*.yaml"):
            with open(f, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if data and 'items_by_module' in data:
                    for module, items in data['items_by_module'].items():
                        for item_id in items:
                            status = check_item_status(module, item_id, workspace_root)
                            all_items.append(status.dict())
        
        # Calculate statistics
        total = len(all_items)
        completed = sum(1 for item in all_items if item['is_complete'])
        in_progress = sum(1 for item in all_items if item['has_checker'] and not item['is_complete'])
        not_started = total - completed - in_progress
        
        return {
            "status": "success",
            "developer": developer_name,
            "statistics": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "not_started": not_started,
                "progress_percent": round(completed / total * 100, 1) if total > 0 else 0
            },
            "items": all_items
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/development/item-status/{module}/{item_id}")
async def get_item_status(module: str, item_id: str):
    """获取单个item的状态"""
    try:
        status = check_item_status(module, item_id)
        return {
            "status": "success",
            **status.dict()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# 3. 回收 (Collection) APIs
# ============================================================================

@router.post("/collect/item")
async def collect_single_item(request: CollectRequest):
    """
    回收单个item的核心文件
    
    收集:
    - inputs/items/{ITEM_ID}.yaml - 配置文件
    - scripts/checker/{ITEM_ID}.py - Checker脚本
    - scripts/doc/{ITEM_ID}_README.md - 文档
    - input_files中指定的IP_project_folder文件
    """
    try:
        workspace_root = get_workspace_root()
        
        # Check item status
        status = check_item_status(request.module, request.item_id, workspace_root)
        
        if not status.is_complete:
            missing = []
            if not status.has_yaml:
                missing.append("YAML config")
            if not status.has_checker:
                missing.append("Checker script")
            if not status.has_readme:
                missing.append("README")
            
            return {
                "status": "warning",
                "message": f"Item {request.item_id} is incomplete",
                "missing": missing,
                "item_status": status.dict()
            }
        
        # Collect files
        collected_files = []
        module_dir = workspace_root / "Check_modules" / request.module
        
        # Create collection directory
        collect_dir = workspace_root / "Work" / "collected" / request.developer_name / request.module
        collect_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy YAML
        yaml_src = module_dir / "inputs" / "items" / f"{request.item_id}.yaml"
        yaml_dest = collect_dir / "inputs" / "items" / f"{request.item_id}.yaml"
        yaml_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(yaml_src, yaml_dest)
        collected_files.append(str(yaml_dest.relative_to(workspace_root)))
        
        # Copy Checker
        checker_src = module_dir / "scripts" / "checker" / f"{request.item_id}.py"
        checker_dest = collect_dir / "scripts" / "checker" / f"{request.item_id}.py"
        checker_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(checker_src, checker_dest)
        collected_files.append(str(checker_dest.relative_to(workspace_root)))
        
        # Copy README
        readme_src = module_dir / "scripts" / "doc" / f"{request.item_id}_README.md"
        readme_dest = collect_dir / "scripts" / "doc" / f"{request.item_id}_README.md"
        readme_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(readme_src, readme_dest)
        collected_files.append(str(readme_dest.relative_to(workspace_root)))
        
        # Copy input files from IP_project_folder
        input_files_collected = []
        for input_file in status.input_files:
            # Resolve path (may contain ${CHECKLIST_ROOT})
            if '${CHECKLIST_ROOT}' in input_file:
                input_path = Path(input_file.replace('${CHECKLIST_ROOT}', str(workspace_root)))
            else:
                input_path = workspace_root / input_file
            
            if input_path.exists():
                # Determine destination
                if 'IP_project_folder' in str(input_path):
                    rel_path = input_path.relative_to(workspace_root / "IP_project_folder")
                    dest_path = collect_dir / "IP_project_folder" / rel_path
                else:
                    dest_path = collect_dir / "input_files" / input_path.name
                
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(input_path, dest_path)
                input_files_collected.append(str(dest_path.relative_to(workspace_root)))
        
        return {
            "status": "success",
            "message": f"Collected {request.item_id} successfully",
            "item_id": request.item_id,
            "module": request.module,
            "collected_files": collected_files,
            "input_files_collected": input_files_collected,
            "collection_path": str(collect_dir.relative_to(workspace_root))
        }
        
    except Exception as e:
        error_msg = f"Collection failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        return {
            "status": "error",
            "error": error_msg
        }


@router.post("/collect/batch")
async def collect_batch_items(request: CollectBatchRequest):
    """批量回收多个items"""
    try:
        results = {
            "success": [],
            "failed": [],
            "incomplete": []
        }
        
        for item in request.items:
            single_request = CollectRequest(
                developer_name=request.developer_name,
                module=item['module'],
                item_id=item['item_id']
            )
            
            result = await collect_single_item(single_request)
            
            if result['status'] == 'success':
                results['success'].append(item['item_id'])
            elif result['status'] == 'warning':
                results['incomplete'].append({
                    "item_id": item['item_id'],
                    "missing": result.get('missing', [])
                })
            else:
                results['failed'].append({
                    "item_id": item['item_id'],
                    "error": result.get('error', 'Unknown error')
                })
        
        return {
            "status": "success",
            "developer": request.developer_name,
            "results": results,
            "summary": {
                "total": len(request.items),
                "success": len(results['success']),
                "incomplete": len(results['incomplete']),
                "failed": len(results['failed'])
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/collect/preview/{developer_name}")
async def preview_collection(developer_name: str):
    """预览可回收的items"""
    try:
        workspace_root = get_workspace_root()
        assignments_dir = workspace_root / "Work" / "assignments"
        
        items_to_collect = []
        
        # Load all assignments for this developer
        for f in assignments_dir.glob(f"{developer_name}_*.yaml"):
            with open(f, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if data and 'items_by_module' in data:
                    for module, items in data['items_by_module'].items():
                        for item_id in items:
                            status = check_item_status(module, item_id, workspace_root)
                            items_to_collect.append({
                                "module": module,
                                "item_id": item_id,
                                "is_complete": status.is_complete,
                                "has_yaml": status.has_yaml,
                                "has_checker": status.has_checker,
                                "has_readme": status.has_readme,
                                "input_files_count": len(status.input_files)
                            })
        
        complete_count = sum(1 for item in items_to_collect if item['is_complete'])
        
        return {
            "status": "success",
            "developer": developer_name,
            "items": items_to_collect,
            "summary": {
                "total": len(items_to_collect),
                "complete": complete_count,
                "incomplete": len(items_to_collect) - complete_count
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
