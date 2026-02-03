#!/usr/bin/env python3

"""
Generate IP Signoff Dashboard HTML.

This script creates a comprehensive signoff-focused dashboard with:
- Tab 1: Dashboard (Executive Summary with status, metrics, charts)
- Tab 2: Issues (Failures, Warnings, Waivers tables)
- Tab 3: Details (Section-by-section accordion view)

Usage:
    python3 visualize_signoff.py [--stage STAGE] [--root ROOT] [--work-dir WORK_DIR]
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from collections import defaultdict

import yaml


# Color scheme
COLORS = {
    'pass': '#4caf50',      # Green
    'fail': '#ef5350',      # Red
    'warn': '#ff9800',      # Orange
    'pending': '#9e9e9e',   # Gray
    'waiver': '#2196f3',    # Blue
    'info': '#00bcd4',      # Cyan
}

# Module categories for filtering
# Category mapping based on module number prefix (智能分类规则)
CATEGORY_RULES = {
    '1': 'Configuration',
    '2': 'Configuration',
    '3': 'Configuration',
    '4': 'Configuration',
    '5': 'Synthesis',
    '6': 'Verification',
    '7': 'Physical',
    '8': 'Physical',
    '9': 'Physical',
    '10': 'Timing',
    '11': 'Power',
    '12': 'Physical',
    '13': 'Verification',
    '14': 'Signoff',
    '15': 'Signoff',
    '16': 'Signoff',
    '17': 'Final Data',
}

def get_module_category(module_name):
    """Get category for a module based on its number prefix.
    
    Supports modules with sub-versions (e.g., 11.0, 11.1, 11.2).
    All sub-versions are automatically grouped under the same category.
    
    Examples:
        '11.0_POWER_EMIR_CHECK' -> 'Power'
        '11.1_POWER_EMIR_CHECK' -> 'Power'
        '10.2_STA_DCD_CHECK' -> 'Timing'
    """
    try:
        # Extract main number from module name (e.g., "11.0_POWER" -> "11")
        prefix = module_name.split('_')[0]  # "11.0" or "11.1"
        main_num = prefix.split('.')[0]     # "11"
        return CATEGORY_RULES.get(main_num, 'Other')
    except Exception:
        return 'Other'


def module_sort_key(name: str) -> Tuple[Any, ...]:
    """Return a tuple usable as sort key prioritizing numeric prefixes."""
    prefix = name.split("_", 1)[0]
    numeric_parts: List[int] = []
    for token in re.split(r"[.\-]", prefix):
        if not token:
            continue
        if token.isdigit():
            numeric_parts.append(int(token))
            continue
        match = re.match(r"(\d+)", token)
        if match:
            numeric_parts.append(int(match.group(1)))
        else:
            break

    if numeric_parts:
        return (*numeric_parts, name)
    return (float("inf"), name)


def parse_checklist(root: Path, stage: str) -> Dict[str, List[Tuple[str, str]]]:
    """Parse stage checklist YAML for module/item ordering."""
    path = root / "Project_config" / "prep_config" / stage / "latest" / "CheckList_Index.yaml"
    if not path.is_file():
        return {}

    module_re = re.compile(r"^(\d+\.[^:]+):\s*$")
    item_re = re.compile(r"^\s*-\s*([A-Z0-9-]+):")

    current: str | None = None
    result: Dict[str, List[Tuple[str, str]]] = {}

    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        module_match = module_re.match(raw_line)
        if module_match:
            current = module_match.group(1)
            result.setdefault(current, [])
            continue

        if not current:
            continue

        if "checklist_item:" in raw_line:
            continue

        item_match = item_re.match(raw_line)
        if item_match:
            item_id = item_match.group(1)
            comment = ""
            hash_idx = raw_line.find("#")
            if hash_idx != -1:
                comment = raw_line[hash_idx + 1:].strip()
            result[current].append((item_id, comment))

    return result


# ==================== PREVIEW MODE FUNCTIONS ====================

def load_pending_waivers(waiver_file: Path) -> List[Dict[str, Any]]:
    """Load pending waivers from YAML file for preview mode."""
    if not waiver_file.exists():
        print(f"[WARNING] Waiver file not found: {waiver_file}")
        return []
    
    try:
        with open(waiver_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        waivers = data.get('pending_waivers', [])
        print(f"[INFO] Loaded {len(waivers)} pending waivers from {waiver_file}")
        return waivers
    except Exception as e:
        print(f"[ERROR] Failed to load pending waivers: {e}")
        return []


def load_pending_changes(changes_file: Path) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load unified pending changes (waivers + skips) from YAML file.
    
    Returns:
        tuple: (waivers, skips) - Two lists of dictionaries
    """
    if not changes_file.exists():
        print(f"[WARNING] Changes file not found: {changes_file}")
        return [], []
    
    try:
        with open(changes_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        print(f"[DEBUG] YAML file loaded, root keys: {list(data.keys()) if data else 'None'}")
        
        waivers = data.get('pending_waivers', [])
        skips = data.get('pending_skips', [])
        
        # Additional validation - check if the lists contain actual data
        if waivers and len(waivers) > 0:
            print(f"[DEBUG] First waiver keys: {list(waivers[0].keys())}")
            print(f"[DEBUG] First waiver sample: module={waivers[0].get('module')}, item_id={waivers[0].get('item_id')}")
        
        if skips and len(skips) > 0:
            print(f"[DEBUG] First skip keys: {list(skips[0].keys())}")
        
        print(f"[INFO] Loaded unified changes from {changes_file}")
        print(f"[INFO]   - {len(waivers)} pending waivers")
        print(f"[INFO]   - {len(skips)} pending skips")
        
        return waivers, skips
    except Exception as e:
        print(f"[ERROR] Failed to load pending changes: {e}")
        import traceback
        traceback.print_exc()
        return [], []


def scan_results_files(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan Work/Results directory for result files (.xlsx, .csv, .yaml).
    Returns list of file info dictionaries with base64 encoded content.
    
    Returns:
        List[Dict]: Each dict contains:
            - name: filename
            - path: relative path
            - size: file size in bytes
            - size_str: human-readable size
            - modified: modification timestamp
            - extension: file extension
            - base64: base64 encoded content
            - preview_available: whether preview is supported
    """
    import base64
    import os
    from datetime import datetime
    
    supported_files = ['.xlsx', '.csv', '.yaml', '.yml']
    max_preview_size = 2 * 1024 * 1024  # 2MB limit for preview
    
    files_info = []
    
    if not results_dir.exists():
        print(f"[WARNING] Results directory not found: {results_dir}")
        return files_info
    
    try:
        # Use rglob to recursively scan for files
        for file_path in results_dir.rglob('*'):
            # Skip files in tmp or temporary directories
            if 'tmp' in file_path.parts or 'temp' in file_path.parts:
                continue
            
            if file_path.is_file() and file_path.suffix.lower() in supported_files:
                try:
                    # Get file stats
                    stat = file_path.stat()
                    size_bytes = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Human-readable size
                    if size_bytes < 1024:
                        size_str = f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        size_str = f"{size_bytes / 1024:.1f} KB"
                    else:
                        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                    
                    # Read and encode file
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        base64_content = base64.b64encode(content).decode('utf-8')
                    
                    # Determine if preview is available
                    preview_available = (
                        file_path.suffix.lower() in ['.xlsx', '.csv'] and 
                        size_bytes < max_preview_size
                    )
                    
                    # Get relative path from Results directory for better display
                    try:
                        rel_path = file_path.relative_to(results_dir)
                        display_path = str(rel_path.parent / rel_path.name) if rel_path.parent != Path('.') else rel_path.name
                    except ValueError:
                        display_path = file_path.name
                    
                    # Add description based on filename and location
                    description = ""
                    if file_path.name == "Origin.xlsx":
                        description = "Main checklist with all module results"
                    elif file_path.name == "Summary.xlsx":
                        description = "Summary of all check results"
                    elif "waiver" in file_path.name.lower():
                        description = "Waiver records"
                    elif "skip" in file_path.name.lower():
                        description = "Skipped check records"
                    elif "pending" in file_path.name.lower():
                        description = "Pending changes data"
                    else:
                        # For module-specific files, extract module name from path
                        parent_name = file_path.parent.name
                        if parent_name != "Results":
                            description = f"Module: {parent_name}"
                    
                    files_info.append({
                        'name': file_path.name,
                        'path': str(file_path.relative_to(results_dir.parent.parent)),
                        'display_path': display_path,
                        'size': size_bytes,
                        'size_str': size_str,
                        'modified': modified.strftime('%Y-%m-%d %H:%M:%S'),
                        'extension': file_path.suffix.lower(),
                        'base64': base64_content,
                        'preview_available': preview_available,
                        'description': description
                    })
                    
                    print(f"[INFO] Scanned file: {display_path} ({size_str})")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to process file {file_path.name}: {e}")
                    continue
        
        # Custom sorting function
        def sort_key(file_info):
            """
            Optimized sort order:
            1. Excel files in Results root directory (priority 0)
               - Summary.xlsx first
               - Origin.xlsx second
               - Other root xlsx files sorted alphabetically
            2. Module checker Excel files by module number (priority 1)
               - e.g., 1.0_LIBRARY_CHECK.xlsx, 5.0_SYNTHESIS_CHECK.xlsx
            3. Other files (YAML, CSV, etc.) (priority 2)
            """
            name = file_info['name']
            display_path = file_info['display_path']
            extension = file_info['extension']
            
            import re
            
            # Check if file is in Results root directory (no subdirectory)
            # display_path will be just filename if it's in root
            is_root_file = '\\' not in display_path and '/' not in display_path
            
            # Priority 0: Excel files in Results root directory
            if is_root_file and extension == '.xlsx':
                # Summary.xlsx first
                if name == "Summary.xlsx":
                    return (0, 0, 0, name)
                # Origin.xlsx second
                elif name == "Origin.xlsx":
                    return (0, 0, 1, name)
                # Other root xlsx files
                else:
                    return (0, 0, 2, name)
            
            # Priority 1: Module checker Excel files (in subdirectories)
            if not is_root_file and extension == '.xlsx':
                # Extract module number from path like "5.0_SYNTHESIS_CHECK/5.0_SYNTHESIS_CHECK.xlsx"
                module_match = re.search(r'(\d+\.\d+)_', display_path)
                if module_match:
                    module_num = float(module_match.group(1))
                    return (1, module_num, 0, name)
            
            # Priority 2: Other files (YAML, CSV, etc.)
            return (2, 0, 0, name)
        
        files_info.sort(key=sort_key)
        
        print(f"[INFO] Total {len(files_info)} result files found")
        
    except Exception as e:
        print(f"[ERROR] Failed to scan results directory: {e}")
    
    return files_info


def apply_waivers_to_modules(
    modules: List[Dict[str, Any]], 
    waivers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply pending waivers to module data before generating HTML.
    
    Logic:
    - Find the target item in the module
    - If waiver.failure_index == -1: mark all failures as waived, set item status to 'pass'
    - Otherwise: mark specific failure as waived
    - If all failures are waived: set item status to 'pass'
    - Recalculate module statistics
    """
    import copy
    modules_copy = copy.deepcopy(modules)
    
    # Group waivers by module and item for efficient lookup
    # Support both YAML keys (module, item_id) and potential JavaScript keys (moduleName, itemId)
    waiver_map = {}
    for waiver in waivers:
        # Try both naming conventions
        module_key = waiver.get('module') or waiver.get('moduleName', '')
        item_key = waiver.get('item_id') or waiver.get('itemId', '')
        key = (module_key, item_key)
        if key not in waiver_map:
            waiver_map[key] = []
        waiver_map[key].append(waiver)
    
    print(f"[INFO] Applying {len(waivers)} waivers to modules...")
    print(f"[DEBUG] Waiver map keys: {list(waiver_map.keys())[:5]}")  # Show first 5 keys for debugging
    applied_count = 0
    
    # Apply waivers
    for module in modules_copy:
        module_name = module['name']
        
        for item in module.get('items', []):
            item_id = item['id']
            key = (module_name, item_id)
            
            if key not in waiver_map:
                continue
            
            # Apply waivers to this item
            item_waivers = waiver_map[key]
            
            if not item.get('failures'):
                continue
            
            # Mark failures as waived
            for waiver in item_waivers:
                # Support both naming conventions for failure_index
                failure_idx = waiver.get('failure_index')
                if failure_idx is None:
                    failure_idx = waiver.get('failureIndex', -1)
                
                if failure_idx == -1:
                    # Waive all failures
                    for failure in item['failures']:
                        failure['waived'] = True
                        failure['waiver_comment'] = waiver.get('comment', 'Pending waiver')
                        failure['waiver_timestamp'] = waiver.get('timestamp', '')
                    applied_count += 1
                else:
                    # Waive specific failure
                    idx = failure_idx
                    if 0 <= idx < len(item['failures']):
                        item['failures'][idx]['waived'] = True
                        item['failures'][idx]['waiver_comment'] = waiver.get('comment', 'Pending waiver')
                        item['failures'][idx]['waiver_timestamp'] = waiver.get('timestamp', '')
                        applied_count += 1
            
            # Check if all failures are now waived
            all_waived = all(f.get('waived', False) for f in item['failures'])
            if all_waived and len(item['failures']) > 0:
                item['status'] = 'pass'
                item['waiver_applied'] = True  # Mark for display
        
        # Recalculate module statistics
        total = len(module.get('items', []))
        pass_count = sum(1 for item in module.get('items', []) if item.get('status') == 'pass')
        fail_count = sum(1 for item in module.get('items', []) if item.get('status') == 'fail')
        pending = sum(1 for item in module.get('items', []) 
                     if item.get('status') in ['pending', 'na', 'N/A', 'not_started'])
        executed = pass_count + fail_count
        
        module['stats'] = {
            'total': total,
            'executed': executed,
            'pass': pass_count,
            'fail': fail_count,
            'pending': pending,
            'pass_rate': round(pass_count / total * 100, 1) if total > 0 else 0,
            'execution_rate': round(executed / total * 100, 1) if total > 0 else 0
        }
        
        # Update overall module status
        if fail_count == 0 and executed == total:
            module['overall_status'] = 'ready'
        elif fail_count > 0:
            module['overall_status'] = 'needs_attention'
        else:
            module['overall_status'] = 'in_progress'
    
    print(f"[INFO] Applied {applied_count} waivers successfully")
    return modules_copy


def apply_skips_to_modules(modules: List[Dict[str, Any]], skips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply skip entries to modules, completely removing skipped modules and items.
    
    Skip logic:
    - Skipped items are COMPLETELY REMOVED from display and statistics
    - If item_id is null: remove entire module from list
    - If item_id is specified: remove specific item from module
    
    Args:
        modules: List of module dictionaries
        skips: List of skip dictionaries with keys: module, item_id, reason
        
    Returns:
        Filtered list of modules with skipped items/modules completely removed
    """
    import copy
    
    if not skips:
        print("[INFO] No skips to apply")
        return modules
    
    print(f"[INFO] Processing {len(skips)} skip entries...")
    
    # Build skip sets for fast lookup
    module_full_skip = set()  # Modules to skip entirely
    item_skip_map = {}  # module_name -> set(item_ids to skip)
    
    for skip in skips:
        module_name = skip.get('module')
        item_id = skip.get('item_id')
        
        if not module_name:
            continue
        
        if item_id is None or item_id == 'null' or item_id == '':
            # Skip entire module
            module_full_skip.add(module_name)
            print(f"  - Will skip entire module: {module_name}")
        else:
            # Skip specific item
            if module_name not in item_skip_map:
                item_skip_map[module_name] = set()
            item_skip_map[module_name].add(item_id)
    
    # Filter modules and items
    filtered_modules = []
    skipped_module_count = 0
    skipped_item_count = 0
    
    for module in modules:
        module_name = module.get('name', '')
        
        # Check if entire module should be skipped
        if module_name in module_full_skip:
            skipped_module_count += 1
            skipped_item_count += len(module.get('items', []))
            print(f"  - Skipped entire module: {module_name}")
            continue  # Don't add this module to filtered list
        
        # Check if specific items need to be skipped
        if module_name in item_skip_map:
            module_copy = copy.deepcopy(module)
            items_to_skip = item_skip_map[module_name]
            
            if 'items' in module_copy:
                # Filter out skipped items
                original_count = len(module_copy['items'])
                module_copy['items'] = [
                    item for item in module_copy['items']
                    if item.get('id') not in items_to_skip
                ]
                skipped_items = original_count - len(module_copy['items'])
                skipped_item_count += skipped_items
                
                if skipped_items > 0:
                    print(f"  - Skipped {skipped_items} items in module: {module_name}")
                
                # If no items left after filtering, skip the module entirely
                if len(module_copy['items']) == 0:
                    print(f"  - Module {module_name} has no items left, removing module")
                    skipped_module_count += 1
                    continue
                
                # Recalculate module statistics based on remaining items
                all_items = module_copy['items']
                total = len(all_items)
                pass_count = sum(1 for item in all_items if item.get('status') == 'pass')
                fail_count = sum(1 for item in all_items if item.get('status') == 'fail')
                pending = sum(1 for item in all_items 
                             if item.get('status') in ['pending', 'na', 'N/A', 'not_started'])
                executed = pass_count + fail_count
                
                module_copy['stats'] = {
                    'total': total,
                    'executed': executed,
                    'pass': pass_count,
                    'fail': fail_count,
                    'pending': pending,
                    'pass_rate': round(pass_count / executed * 100, 1) if executed > 0 else 0,
                    'execution_rate': round(executed / total * 100, 1) if total > 0 else 0
                }
                
                # Update overall module status
                if fail_count == 0 and executed == total:
                    module_copy['overall_status'] = 'ready'
                elif fail_count > 0:
                    module_copy['overall_status'] = 'needs_attention'
                else:
                    module_copy['overall_status'] = 'in_progress'
            
            filtered_modules.append(module_copy)
        else:
            # No skips for this module, keep as is
            filtered_modules.append(module)
    
    print(f"[INFO] Completely removed {skipped_module_count} modules and {skipped_item_count} items")
    return filtered_modules


def generate_preview_header(waiver_count: int, skip_count: int, timestamp: str) -> str:
    """Generate special header for preview mode."""
    changes_text = []
    if waiver_count > 0:
        changes_text.append(f"<strong>{waiver_count}</strong> waiver(s)")
    if skip_count > 0:
        changes_text.append(f"<strong>{skip_count}</strong> skip(s)")
    
    changes_summary = " and ".join(changes_text) if changes_text else "no changes"
    
    return f"""
<!-- PREVIEW MODE BANNER -->
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; padding: 20px; margin: -20px -20px 20px -20px; 
            border-radius: 8px 8px 0 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
    <div style='display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;'>
        <div>
            <h2 style='margin: 0; font-size: 24px; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;'>
                🔍 PREVIEW MODE
            </h2>
            <p style='margin: 8px 0 0 0; font-size: 14px; opacity: 0.9;'>
                This is a temporary preview with {changes_summary} applied.
                <br>Generated: {timestamp}
            </p>
        </div>
        <div>
            <button onclick='closePreview()' 
                    style='background: rgba(255,255,255,0.2); 
                           border: 2px solid white; 
                           color: white; 
                           padding: 10px 20px; 
                           border-radius: 6px; 
                           cursor: pointer; 
                           font-weight: 600;
                           font-size: 16px;
                           transition: all 0.2s;'
                    onmouseover='this.style.background="rgba(255,255,255,0.3)"'
                    onmouseout='this.style.background="rgba(255,255,255,0.2)"'>
                ✕ Close Preview
            </button>
        </div>
    </div>
</div>
"""


def load_summary(root: Path, module: str) -> Dict[str, Any]:
    """Load module summary YAML."""
    summary_path = root / "Check_modules" / module / "outputs" / f"{module}.yaml"
    if not summary_path.is_file():
        return {}
    try:
        return yaml.safe_load(summary_path.read_text()) or {}
    except Exception:
        return {}


def is_waiver_placeholder(item_id: str) -> bool:
    """Check if item_id is a waiver placeholder."""
    pattern = r'^[A-Z]+-\d+-\d+-\d+-\d+-(INFO\d+|WARN\d+)$'
    return re.match(pattern, item_id) is not None


def categorize_section(module_name: str) -> str:
    """Categorize section into major groups."""
    return get_module_category(module_name)


def build_module_data(
    module: str,
    ordered: List[Tuple[str, str]],
    summary: Dict[str, Any],
    fallback_stage: str,
    root: Path = None,
) -> Dict[str, Any]:
    """Build complete data structure for a module."""
    items_summary = summary.get("check_items", {}) if isinstance(summary, dict) else {}
    
    # Filter out waiver placeholders from ordered list
    ordered_filtered = [(item_id, desc) for item_id, desc in ordered if not is_waiver_placeholder(item_id)]
    seen = {item_id for item_id, _ in ordered_filtered}
    merged = list(ordered_filtered)
    
    # Add items from summary not in checklist
    for item_id, data in (items_summary or {}).items():
        if is_waiver_placeholder(item_id):
            continue
        if item_id not in seen:
            desc = ""
            if isinstance(data, dict):
                desc = data.get("description") or ""
            merged.append((item_id, desc))

    item_payload: List[Dict[str, Any]] = []
    for item_id, checklist_desc in merged:
        data = items_summary.get(item_id, {}) if isinstance(items_summary, dict) else {}
        status = (data.get("status") or "no_check") if isinstance(data, dict) else "no_check"
        status = status.lower()
        if status not in ["pass", "fail", "no_check"]:
            status = "no_check"
        
        executed = bool(data.get("executed")) and status != "no_check" if isinstance(data, dict) else False
        
        # Force pending if not executed
        if not executed:
            status = "no_check"
        
        occurrence = data.get("occurrence") if isinstance(data, dict) else None
        description = ""
        if isinstance(data, dict):
            description = data.get("description") or ""
        description = description or checklist_desc or ""
        
        # Extract failures, warnings, infos
        failures = []
        warnings = []
        infos = []
        waivers = []
        approved_waivers = []
        waived_as_info_items = []
        approved_waiver_count = 0
        
        if isinstance(data, dict):
            # Failures
            fail_data = data.get("failures")
            if fail_data and isinstance(fail_data, list):
                for f in fail_data:
                    if isinstance(f, dict) and set(f.keys()) != {"occurrence"}:
                        filtered = {k: v for k, v in f.items() 
                                   if k not in ("index", "occurrence") and v not in (None, "")}
                        if filtered:
                            failures.append(filtered)
            
            # Warnings
            warn_data = data.get("warn") or data.get("warnings")
            if warn_data and isinstance(warn_data, list):
                for w in warn_data:
                    if isinstance(w, dict):
                        detail = w.get("detail", "")
                        reason = w.get("reason", "")
                        if detail or reason:
                            # Hide "N/A" detail prefix
                            detail_str = str(detail).strip() if detail else ""
                            if detail_str.upper() in ("N/A", "N/A:"):
                                warnings.append(reason)
                            elif detail and reason:
                                warnings.append(f"{detail}: {reason}")
                            else:
                                warnings.append(detail or reason)
                    else:
                        warnings.append(str(w))
            elif warn_data:
                warnings.append(str(warn_data))
            
            # Infos (separate waiver vs non-waiver)
            # New logic: [WAIVER] items are approved waivers, [WAIVED_AS_INFO] should follow waivers
            info_data = data.get("info") or data.get("infos")
            
            if info_data and isinstance(info_data, list):
                # First pass: collect approved waivers and WAIVED_AS_INFO items
                regular_infos = []
                
                for info in info_data:
                    if isinstance(info, dict):
                        detail = info.get("detail", "")
                        reason = info.get("reason", "")
                        source_file = info.get("source_file", "")
                        
                        if detail or reason:
                            # Build info string - hide "N/A" detail prefix
                            detail_str = str(detail).strip() if detail else ""
                            if detail_str.upper() in ("N/A", "N/A:"):
                                # If detail is just "N/A", only show reason
                                info_str = reason
                            elif detail and reason:
                                # Both detail and reason exist, show both
                                info_str = f"{detail}: {reason}"
                            else:
                                # Only one exists
                                info_str = detail or reason
                            
                            # Check if it's an approved waiver [WAIVER]
                            if "[WAIVER]" in reason or "[WAIVED]" in reason:
                                # Remove the [WAIVER]/[WAIVED] tags from display
                                clean_str = info_str.replace("[WAIVER]", "").replace("[WAIVED]", "").strip()
                                approved_waivers.append(clean_str)
                                approved_waiver_count += 1  # Count approved waivers
                            # Check if it's a WAIVED_AS_INFO item
                            elif "[WAIVED_AS_INFO]" in reason:
                                # Remove the [WAIVED_AS_INFO] tag from display
                                clean_str = info_str.replace("[WAIVED_AS_INFO]", "").strip()
                                waived_as_info_items.append(clean_str)
                            # Legacy waive.yaml check
                            elif "waive.yaml" in source_file.lower():
                                approved_waivers.append(info_str)
                                approved_waiver_count += 1  # Count legacy waivers
                            # Regular info items (only if not WAIVED_AS_INFO)
                            else:
                                regular_infos.append(info_str)
                
                # Combine waivers: approved waivers + WAIVED_AS_INFO items
                waivers = approved_waivers + waived_as_info_items
                
                # Infos only contain regular (non-waived) information
                infos = regular_infos
            elif info_data:
                infos.append(str(info_data))
        
        # Calculate actual occurrence based on prompts count
        # Priority: failures > warnings > infos (excluding waivers)
        actual_occurrence = 0
        if failures:
            actual_occurrence = len(failures)
        elif warnings:
            actual_occurrence = len(warnings)
        elif infos:
            actual_occurrence = len(infos)
        
        # Use actual_occurrence instead of the occurrence field from YAML
        item_payload.append({
            "id": item_id,
            "status": status,
            "executed": executed,
            "occurrence": actual_occurrence,
            "description": description,
            "failures": failures,
            "warnings": warnings,
            "infos": infos,
            "waivers": waivers,
            "approved_waivers": approved_waivers,  # Separate field for [WAIVED] items
            "waived_as_info": waived_as_info_items,  # Separate field for [WAIVED_AS_INFO] items
            "approved_waiver_count": approved_waiver_count,  # Track count for statistics
        })

    # Calculate statistics
    total = len(item_payload)
    executed_count = sum(1 for item in item_payload if item["executed"])
    pass_count = sum(1 for item in item_payload if item["status"] == "pass")
    fail_count = sum(1 for item in item_payload if item["status"] == "fail" and item["executed"])
    pending = max(total - executed_count, 0)
    
    # Determine module status
    if total == 0:
        state = "pending"
    elif executed_count == 0:
        state = "pending"
    elif fail_count > 0:
        state = "fail"
    elif pending > 0:
        state = "partial"
    else:
        state = "pass"
    
    # Calculate overall_status based on execution and failures
    # Logic: fail_count == 0 and executed == total: 'ready'
    #        fail_count > 0: 'needs_attention'
    #        else: 'in_progress'
    if fail_count == 0 and executed_count == total:
        overall_status = 'ready'
    elif fail_count > 0:
        overall_status = 'needs_attention'
    elif executed_count > 0:
        overall_status = 'in_progress'
    else:
        overall_status = 'pending'

    return {
        "name": module,
        "category": categorize_section(module),
        "stage": (summary or {}).get("stage", fallback_stage),
        "status": state,
        "overall_status": overall_status,
        "stats": {
            "total": total,
            "executed": executed_count,
            "pass": pass_count,
            "fail": fail_count,
            "pending": pending,
        },
        "items": item_payload,
    }


def build_module_dataset(
    root: Path, 
    stage: str, 
    checklist: Dict[str, List[Tuple[str, str]]]
) -> List[Dict[str, Any]]:
    """Build complete dataset for all modules."""
    dataset: List[Dict[str, Any]] = []
    for module, ordered in checklist.items():
        summary = load_summary(root, module)
        module_data = build_module_data(module, ordered, summary, stage, root)
        # Filter out empty sections (no items or no executed items)
        if module_data["stats"]["total"] > 0:
            dataset.append(module_data)
    dataset.sort(key=lambda entry: module_sort_key(entry["name"]))
    return dataset


def calculate_overall_stats(modules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall statistics across all modules."""
    total = sum(m["stats"]["total"] for m in modules)
    executed = sum(m["stats"]["executed"] for m in modules)
    pass_count = sum(m["stats"]["pass"] for m in modules)
    fail_count = sum(m["stats"]["fail"] for m in modules)
    pending = sum(m["stats"]["pending"] for m in modules)
    
    # Count waivers - only count items with approved waivers
    # Note: [WAIVED_AS_INFO] items are displayed with waivers but not counted separately
    waiver_items = set()
    for m in modules:
        for item in m["items"]:
            # Use the approved_waiver_count field that was added during item parsing
            if item.get("approved_waiver_count", 0) > 0:
                waiver_items.add(f"{m['name']}::{item['id']}")
            # Count pending waivers (identified by waiver_applied flag)
            elif item.get("waiver_applied"):
                waiver_items.add(f"{m['name']}::{item['id']}")
    waiver_count = len(waiver_items)
    
    # Determine overall status
    execution_rate = (executed / total * 100) if total > 0 else 0
    if total == 0:
        overall_status = "unknown"
    elif fail_count > 0:
        # Has critical issues - needs attention
        overall_status = "needs_attention"
    elif execution_rate < 100:
        # No critical issues but checks not complete - in progress
        overall_status = "in_progress"
    else:
        # No critical issues and all checks complete - ready for signoff
        overall_status = "ready"
    
    return {
        "total": total,
        "executed": executed,
        "pass": pass_count,
        "fail": fail_count,
        "pending": pending,
        "waiver": waiver_count,
        "pass_rate": round(pass_count / executed * 100, 1) if executed > 0 else 0,
        "execution_rate": round(executed / total * 100, 1) if total > 0 else 0,
        "overall_status": overall_status,
    }


def collect_all_issues(modules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Collect all failures, warnings, and waivers across modules."""
    failures = []
    warnings = []
    waivers = []
    approved_waivers = []
    waived_as_info = []
    
    for module in modules:
        for item in module["items"]:
            # Failures
            if item["status"] == "fail" and item["executed"]:
                for failure in item.get("failures", []):
                    failures.append({
                        "section": module["name"],
                        "item_id": item["id"],
                        "description": item["description"],
                        "details": failure,
                        "occurrence": item["occurrence"],
                    })
            
            # Warnings
            for warning in item.get("warnings", []):
                warnings.append({
                    "section": module["name"],
                    "item_id": item["id"],
                    "description": item["description"],
                    "warning": warning,
                })
            
            # Waivers (legacy combined list for backward compatibility)
            for waiver in item.get("waivers", []):
                waivers.append({
                    "section": module["name"],
                    "item_id": item["id"],
                    "description": item["description"],
                    "waiver": waiver,
                })
            
            # Approved waivers (separate list)
            for waiver in item.get("approved_waivers", []):
                approved_waivers.append({
                    "section": module["name"],
                    "item_id": item["id"],
                    "description": item["description"],
                    "waiver": waiver,
                })
            
            # Waived as info (separate list)
            for waiver in item.get("waived_as_info", []):
                waived_as_info.append({
                    "section": module["name"],
                    "item_id": item["id"],
                    "description": item["description"],
                    "waiver": waiver,
                })
    
    return {
        "failures": failures,
        "warnings": warnings,
        "waivers": waivers,
        "approved_waivers": approved_waivers,
        "waived_as_info": waived_as_info,
    }


def generate_html(
    root: Path, 
    stage: str, 
    checklist: Dict[str, List[Tuple[str, str]]],
    preview_waivers: List[Dict[str, Any]] = None,
    preview_skips: List[Dict[str, Any]] = None
) -> str:
    """Generate complete HTML dashboard with optional preview changes."""
    modules = build_module_dataset(root, stage, checklist)
    
    # Scan result files from Work/Results directory
    results_dir = root / 'Work' / 'Results'
    files_info = scan_results_files(results_dir)
    results_content = generate_results_content(files_info)
    
    # Apply preview changes (waivers and skips) if in preview mode
    has_waivers = preview_waivers is not None and len(preview_waivers) > 0
    has_skips = preview_skips is not None and len(preview_skips) > 0
    is_preview = has_waivers or has_skips
    
    # Debug output for preview mode detection
    print(f"[DEBUG] Preview mode detection:")
    print(f"  - preview_waivers: {type(preview_waivers)} with {len(preview_waivers) if preview_waivers else 0} items")
    print(f"  - preview_skips: {type(preview_skips)} with {len(preview_skips) if preview_skips else 0} items")
    print(f"  - has_waivers: {has_waivers}")
    print(f"  - has_skips: {has_skips}")
    print(f"  - is_preview: {is_preview}")
    
    if has_waivers:
        print(f"[INFO] Preview mode: applying {len(preview_waivers)} waivers to module data")
        print(f"[DEBUG] Sample waiver keys: {list(preview_waivers[0].keys()) if preview_waivers else 'N/A'}")
        modules = apply_waivers_to_modules(modules, preview_waivers)
    
    if has_skips:
        print(f"[INFO] Preview mode: applying {len(preview_skips)} skips to module data")
        print(f"[DEBUG] Sample skip keys: {list(preview_skips[0].keys()) if preview_skips else 'N/A'}")
        modules = apply_skips_to_modules(modules, preview_skips)
    
    print(f"[DEBUG] Calculating overall stats for {len(modules)} modules...")
    overall_stats = calculate_overall_stats(modules)
    print(f"[DEBUG] Overall stats calculated - waiver count: {overall_stats.get('waiver', 0)}")
    issues = collect_all_issues(modules)
    
    # Serialize data for JavaScript
    modules_json = json.dumps(modules, ensure_ascii=False).replace("</", "<\\/")
    overall_json = json.dumps(overall_stats, ensure_ascii=False).replace("</", "<\\/")
    issues_json = json.dumps(issues, ensure_ascii=False).replace("</", "<\\/")
    
    # Prepare files data for JavaScript (create lookup dictionary by file ID)
    files_data_dict = {}
    for file_info in files_info:
        file_id = file_info['name'].replace('.', '_').replace(' ', '_')
        files_data_dict[file_id] = {
            'name': file_info['name'],
            'base64': file_info['base64'],
            'preview_available': file_info['preview_available']
        }
    files_data_js = "const RESULT_FILES = " + json.dumps(files_data_dict, ensure_ascii=False).replace("</", "<\\/") + ";"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if local SheetJS library exists
    # Library is located in Check_modules/common/libs/ (same directory as this script)
    script_dir = Path(__file__).parent
    local_sheetjs_path = script_dir / 'libs' / 'xlsx.full.min.js'
    sheetjs_script = ""
    if local_sheetjs_path.exists():
        print(f"[INFO] Using local SheetJS library: {local_sheetjs_path}")
        try:
            with open(local_sheetjs_path, 'r', encoding='utf-8') as f:
                sheetjs_content = f.read()
            sheetjs_script = f"<script>{sheetjs_content}</script>"
        except Exception as e:
            print(f"[WARNING] Failed to load local SheetJS library: {e}")
            print(f"[INFO] Falling back to CDN")
            sheetjs_script = "<script src='https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js'></script>"
    else:
        print(f"[INFO] Local SheetJS library not found at {local_sheetjs_path}, using CDN")
        sheetjs_script = "<script src='https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js'></script>"
    
    html_content = f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1.0'/>
<title>{'[PREVIEW] ' if is_preview else ''}IP Signoff Dashboard</title>
<!-- SheetJS library for Excel/CSV preview -->
{sheetjs_script}
<style>
{generate_css()}
</style>
</head>
<body>
"""
    
    # Add preview header if in preview mode
    if is_preview:
        waiver_cnt = len(preview_waivers) if preview_waivers else 0
        skip_cnt = len(preview_skips) if preview_skips else 0
        html_content += generate_preview_header(waiver_cnt, skip_cnt, timestamp)
    
    html_content += f"""
{generate_header(stage, timestamp)}

<!-- Review Mode Banner (hidden by default, shown when Review Mode is active) -->
<div id='review-mode-banner' class='review-mode-banner' style='display: none;'>
    <div style='display: flex; align-items: center; justify-content: center; gap: 12px;'>
        <span style='font-size: 1.5rem;'>📝</span>
        <div>
            <strong style='font-size: 1.1rem;'>Review Mode Active</strong>
            <div style='opacity: 0.9; font-size: 0.9rem; margin-top: 4px;'>
                You can now Waive failed items and Skip not-started items. Click the toggle button to exit.
            </div>
        </div>
    </div>
</div>

{generate_tabs()}

<!-- Waiver Modal Overlay -->
<div id='waiver-modal-overlay' class='waiver-modal-overlay'>
    <div class='waiver-modal'>
        <div class='waiver-modal-header'>
            <h2 class='waiver-modal-title'>Add Waiver</h2>
            <button class='waiver-modal-close' onclick='closeWaiverModal()'>×</button>
        </div>
        <div class='waiver-modal-body'>
            <div class='waiver-info-section'>
                <div class='waiver-info-label'>Module</div>
                <div class='waiver-info-value' id='waiver-module-name'></div>
            </div>
            <div class='waiver-info-section'>
                <div class='waiver-info-label'>Item ID</div>
                <div class='waiver-info-value' id='waiver-item-id'></div>
            </div>
            <div class='waiver-info-section'>
                <div class='waiver-info-label'>Description</div>
                <div class='waiver-info-value' id='waiver-item-desc'></div>
            </div>
            <div class='waiver-info-section' id='waiver-failure-section'>
                <div class='waiver-info-label'>Failure Detail</div>
                <div class='waiver-info-value' id='waiver-failure-detail'></div>
            </div>
            <div class='waiver-comment-section'>
                <label class='waiver-comment-label'>Comment (optional):</label>
                <textarea id='waiver-comment-input' class='waiver-comment-input' rows='4' placeholder='Enter reason for waiving this failure...'></textarea>
            </div>
        </div>
        <div class='waiver-modal-footer'>
            <button class='waiver-modal-btn waiver-cancel-btn' onclick='closeWaiverModal()'>Cancel</button>
            <button class='waiver-modal-btn waiver-confirm-btn' onclick='confirmWaiver()'>Confirm Waiver</button>
        </div>
    </div>
</div>

<!-- Unwaiver Modal Overlay -->
<div id='unwaiver-modal-overlay' class='waiver-modal-overlay'>
    <div class='waiver-modal'>
        <div class='waiver-modal-header'>
            <h2 class='waiver-modal-title'>Remove Waiver</h2>
            <button class='waiver-modal-close' onclick='closeUnwaiverModal()'>×</button>
        </div>
        <div class='waiver-modal-body'>
            <div class='waiver-info-section'>
                <div class='waiver-info-label'>Module</div>
                <div class='waiver-info-value' id='unwaiver-module-name'></div>
            </div>
            <div class='waiver-info-section'>
                <div class='waiver-info-label'>Item ID</div>
                <div class='waiver-info-value' id='unwaiver-item-id'></div>
            </div>
            <div class='waiver-info-section'>
                <div class='waiver-info-label'>Description</div>
                <div class='waiver-info-value' id='unwaiver-item-desc'></div>
            </div>
            <div class='waiver-info-section' id='unwaiver-failure-section'>
                <div class='waiver-info-label'>Failure Detail</div>
                <div class='waiver-info-value' id='unwaiver-failure-detail'></div>
            </div>
            <div class='waiver-info-section' style='background: #fef3c7; border-left: 4px solid #f59e0b; padding: 0.75rem;'>
                <div class='waiver-info-label' style='color: #92400e;'>Current Comment</div>
                <div class='waiver-info-value' id='unwaiver-current-comment' style='color: #78350f; font-style: italic;'></div>
            </div>
            <div class='waiver-warning-section' style='margin-top: 1rem; padding: 1rem; background: #fee2e2; border-radius: 8px; border-left: 4px solid #ef4444;'>
                <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;'>
                    <span style='font-size: 1.5rem;'>⚠️</span>
                    <strong style='color: #991b1b;'>Warning</strong>
                </div>
                <div style='color: #7f1d1d; font-size: 0.9rem;'>
                    Removing this waiver will restore the failure status. This action cannot be undone.
                </div>
            </div>
        </div>
        <div class='waiver-modal-footer'>
            <button class='waiver-modal-btn waiver-cancel-btn' onclick='closeUnwaiverModal()'>Cancel</button>
            <button class='waiver-modal-btn waiver-confirm-btn' style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); border-color: #ef4444;' 
                    onmouseover='this.style.background="linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)";' 
                    onmouseout='this.style.background="linear-gradient(135deg, #ef4444 0%, #dc2626 100%)";'
                    onclick='confirmUnwaiver()'>Remove Waiver</button>
        </div>
    </div>
</div>

<!-- Skip Module/Item Modal -->
<div id='skip-modal-overlay' class='waiver-modal-overlay'>
    <div class='waiver-modal' style='max-width: 500px;'>
        <div class='waiver-modal-header' style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);'>
            <h2 class='waiver-modal-title'>⏭️ Skip Confirmation</h2>
            <button class='waiver-modal-close' onclick='closeSkipModal()'>×</button>
        </div>
        <div class='waiver-modal-body'>
            <div class='waiver-info-grid'>
                <div class='waiver-info-item'>
                    <div class='waiver-info-label'>Module:</div>
                    <div class='waiver-info-value' id='skip-module-name'></div>
                </div>
                <div class='waiver-info-item' id='skip-item-info' style='display:none;'>
                    <div class='waiver-info-label'>Item ID:</div>
                    <div class='waiver-info-value' id='skip-item-id'></div>
                </div>
            </div>
            <div class='waiver-form-group'>
                <label class='waiver-label' for='skip-reason-input'>
                    Skip Reason (optional):
                </label>
                <textarea id='skip-reason-input' 
                          class='waiver-textarea' 
                          rows='3' 
                          placeholder='Optional: Provide a reason for skipping (not required)'
                          style='border-color: #f59e0b;'
                          onfocus='this.style.borderColor="#d97706"; this.style.boxShadow="0 0 0 3px rgba(245, 158, 11, 0.1)";'
                          onblur='this.style.borderColor="#f59e0b"; this.style.boxShadow="none";'></textarea>
            </div>
            <div style='background: #fffbeb; border: 1px solid #fcd34d; border-radius: 6px; padding: 12px; margin-top: 12px;'>
                <div style='font-size: 0.9rem; color: #78350f; font-weight: 600; margin-bottom: 6px;'>⚠️ Note:</div>
                <div style='font-size: 0.85rem; color: #92400e; line-height: 1.5;'>
                    Skipped items will be hidden from the dashboard. You can export skips to track what was skipped.
                </div>
            </div>
        </div>
        <div class='waiver-modal-footer'>
            <button class='waiver-modal-btn waiver-cancel-btn' onclick='closeSkipModal()'>Cancel</button>
            <button class='waiver-modal-btn waiver-confirm-btn' 
                    style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); border-color: #f59e0b;' 
                    onmouseover='this.style.background="linear-gradient(135deg, #d97706 0%, #b45309 100%)";' 
                    onmouseout='this.style.background="linear-gradient(135deg, #f59e0b 0%, #d97706 100%)";'
                    onclick='confirmSkip()'>Skip</button>
        </div>
    </div>
</div>

<!-- Unskip Modal -->
<div id='unskip-modal-overlay' class='waiver-modal-overlay'>
    <div class='waiver-modal'>
        <div class='waiver-modal-header'>
            <h2 class='waiver-modal-title'>Remove Skip</h2>
            <button class='waiver-modal-close' onclick='closeUnskipModal()'>×</button>
        </div>
        <div class='waiver-modal-body'>
            <div class='waiver-modal-field'>
                <div class='waiver-modal-label'>Module:</div>
                <div class='waiver-modal-value' id='unskip-module-name'></div>
            </div>
            <div class='waiver-modal-field' id='unskip-item-info'>
                <div class='waiver-modal-label'>Item:</div>
                <div class='waiver-modal-value' id='unskip-item-id'></div>
            </div>
            <div class='waiver-modal-field'>
                <div class='waiver-modal-label'>Current Reason:</div>
                <div class='waiver-modal-value' id='unskip-current-reason' style='font-style: italic; color: #666;'></div>
            </div>
            <div style='margin-top: 16px; padding: 12px; background: #fff3cd; border-left: 4px solid #f97316; border-radius: 4px;'>
                <strong style='color: #f97316;'>⚠ Confirmation:</strong>
                <p style='margin: 8px 0 0 0; color: #666;'>Are you sure you want to remove this skip? The item will return to its original state.</p>
            </div>
        </div>
        <div class='waiver-modal-footer'>
            <button class='waiver-modal-btn waiver-cancel-btn' onclick='closeUnskipModal()'>Cancel</button>
            <button class='waiver-modal-btn waiver-confirm-btn' 
                    style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); border-color: #f59e0b;' 
                    onmouseover='this.style.background="linear-gradient(135deg, #d97706 0%, #b45309 100%)";' 
                    onmouseout='this.style.background="linear-gradient(135deg, #f59e0b 0%, #d97706 100%)";'
                    onclick='confirmUnskip()'>Remove Skip</button>
        </div>
    </div>
</div>

<!-- Generic Message Modal -->
<div id='message-modal-overlay' class='waiver-modal-overlay'>
    <div class='waiver-modal'>
        <div class='waiver-modal-header'>
            <h2 class='waiver-modal-title' id='message-modal-title'>Message</h2>
            <button class='waiver-modal-close' onclick='closeMessageModal()'>×</button>
        </div>
        <div class='waiver-modal-body'>
            <div id='message-modal-content' style='white-space: pre-wrap; line-height: 1.6;'></div>
        </div>
        <div class='waiver-modal-footer'>
            <button class='waiver-modal-btn waiver-confirm-btn' onclick='closeMessageModal()'>OK</button>
        </div>
    </div>
</div>

<div class='container'>
    <div id='dashboard-tab' class='tab-content active'>
        {generate_dashboard_content(modules)}
    </div>
    <div id='details-tab' class='tab-content'>
        {generate_details_content()}
    </div>
    <div id='waivers-tab' class='tab-content'>
        {generate_waivers_content()}
    </div>
    <div id='results-tab' class='tab-content'>
        {results_content}
    </div>
</div>

<!-- File Preview Modal -->
<div id='file-preview-modal' style='display:none;'>
    <div class='preview-modal-content'>
        <div class='preview-modal-header'>
            <h3 id='preview-filename'>File Preview</h3>
            <button class='preview-modal-close' onclick='closePreviewModal()'>×</button>
        </div>
        <div class='preview-modal-body' id='preview-content'>
            <!-- Preview content will be populated here -->
        </div>
        <div class='preview-modal-footer'>
            <button id='preview-download-btn' class='file-action-btn download-btn'>
                <svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor'>
                    <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4'/>
                </svg>
                Download Original
            </button>
        </div>
    </div>
</div>

<!-- Back to Top Button -->
<button id='back-to-top' title='Back to Top' aria-label='Back to Top'>
    ↑
</button>

<script>
let MODULES_DATA = {modules_json};
let OVERALL_STATS = {overall_json};
let ISSUES_DATA = {issues_json};
const IS_PREVIEW_MODE = {str(is_preview).lower()};

// Debug log for IS_PREVIEW_MODE
console.log('========================================');
console.log('🚀 Dashboard Initialization');
console.log('========================================');
console.log('IS_PREVIEW_MODE:', IS_PREVIEW_MODE);
console.log('OVERALL_STATS.waiver:', OVERALL_STATS.waiver);
console.log('MODULES_DATA length:', MODULES_DATA.length);
console.log('========================================');

// Result files data with base64 content
{files_data_js}

{generate_javascript()}
</script>
</body>
</html>
"""
    
    return html_content


def generate_css() -> str:
    """Generate CSS styling."""
    return """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: #f5f7fa;
    color: #2c3e50;
    line-height: 1.6;
}

/* Header */
.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.header-content {
    max-width: 1600px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
}
.header-left {
    flex: 0 0 auto;
}
.header-right {
    flex: 1 1 auto;
    display: flex;
    justify-content: flex-end;
}
.header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.header-meta {
    opacity: 0.95;
    font-size: 0.9rem;
}

/* Tabs */
.tabs {
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}
.tabs-container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    gap: 0;
}
.tab-button {
    flex: 1;
    padding: 1rem 1.5rem;
    border: none;
    background: white;
    color: #64748b;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    border-bottom: 3px solid transparent;
}
.tab-button:hover {
    background: #f8fafc;
    color: #475569;
}
.tab-button.active {
    color: #667eea;
    border-bottom-color: #667eea;
    background: #f8fafc;
}

/* Sub-tabs for Waivers */
.sub-tabs {
    background: white;
    border-radius: 12px;
    padding: 0.5rem 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.sub-tabs .tab-button[data-subtab]:hover {
    color: #667eea;
    border-bottom-color: #e0e7ff;
}
.sub-tabs .tab-button[data-subtab].active {
    color: #667eea;
    border-bottom-color: #667eea;
}
.subtab-content {
    display: none;
}
.subtab-content.active {
    display: block;
}

/* Container */
.container {
    max-width: 1400px;
    margin: 2rem auto;
    padding: 0 1rem;
}

/* Tab Content */
.tab-content {
    display: none;
}
.tab-content.active {
    display: block;
    animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Executive Summary */
.executive-summary {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.07);
}

/* Compact Status Indicator (horizontal layout with filter) */
.status-indicator-compact {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1.25rem;
    border-radius: 12px;
    background: white;
    border: 2px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.status-indicator-compact::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: #cbd5e1;
    transition: all 0.3s ease;
}
.status-indicator-compact:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
.status-indicator-compact.ready {
    background: white;
    border-color: #e2e8f0;
    max-width: 280px;
    padding: 0.6rem 1.5rem;
}
.status-indicator-compact.ready::before {
    background: linear-gradient(180deg, #10b981 0%, #059669 100%);
}
.status-indicator-compact.ready .status-icon-wrapper {
    background: transparent;
    box-shadow: none;
    width: 24px;
    height: 24px;
}
.status-indicator-compact.in-progress {
    background: white;
    border-color: #e2e8f0;
    max-width: 280px;
    padding: 0.6rem 1.5rem;
}
.status-indicator-compact.in-progress::before {
    background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
}
.status-indicator-compact.in-progress .status-icon-wrapper {
    background: transparent;
    box-shadow: none;
    width: 24px;
    height: 24px;
}
.status-indicator-compact.needs-attention {
    background: white;
    border-color: #e2e8f0;
    max-width: 280px;
    padding: 0.6rem 1.5rem;
}
.status-indicator-compact.needs-attention::before {
    background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
}
.status-indicator-compact.needs-attention .status-icon-wrapper {
    background: transparent;
    box-shadow: none;
    width: 24px;
    height: 24px;
}
.status-indicator-compact .status-icon-wrapper {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 1.25rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    transition: all 0.3s ease;
}
.status-indicator-compact:hover .status-icon-wrapper {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.status-indicator-compact .status-content {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}
.status-indicator-compact .status-text {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #1e293b;
    line-height: 1.2;
}
.status-indicator-compact .status-subtext {
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    line-height: 1.2;
}

/* Metrics Cards */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
}
.metric-card {
    background: white;
    border-radius: 10px;
    padding: 1.125rem 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    text-align: center;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(0,0,0,0.04);
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--card-color, #cbd5e1);
    opacity: 0.8;
}
.metric-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(0,0,0,0.1);
}
.metric-card:hover::before {
    opacity: 1;
}
.metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
    transition: color 0.2s;
}
.metric-value {
    font-size: 1.875rem;
    font-weight: 700;
    margin-bottom: 0.375rem;
    transition: color 0.2s;
}
.metric-value.pass { color: #4caf50; }
.metric-value.fail { color: #ef5350; }
.metric-value.pending { color: #9e9e9e; }
.metric-value.waiver { color: #2196f3; }
.metric-subtext {
    font-size: 0.75rem;
    font-weight: 500;
    transition: color 0.2s;
}
.metric-icon {
    display: inline-block;
    width: 1.1em;
    height: 1.1em;
    line-height: 1.1em;
    text-align: center;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    margin-left: 0.25rem;
    font-style: normal;
    font-weight: bold;
    font-size: 0.9em;
}

/* Progress Bars */
.progress-section {
    background: white;
    border-radius: 12px;
    padding: 1.75rem 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    border: 1px solid rgba(0,0,0,0.05);
}
.section-title {
    font-size: 1.125rem;
    font-weight: 700;
    margin-bottom: 1.25rem;
    color: #1e293b;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #f1f5f9;
}
.progress-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}
.progress-item:last-child {
    margin-bottom: 0;
}
.progress-label {
    min-width: 120px;
    flex-shrink: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: #1e293b;
}
.progress-bar-container {
    flex: 1;
    position: relative;
}
.progress-bar-bg {
    height: 20px;
    background: #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
}
.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #4caf50 0%, #66bb6a 100%);
    transition: width 0.6s ease, background 0.3s ease;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 8px;
    border-radius: 10px;
}
.progress-bar-fill::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(180deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 100%);
    pointer-events: none;
    border-radius: 10px;
}
.progress-percentage {
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    z-index: 1;
}
.progress-stats {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    white-space: nowrap;
    z-index: 1;
}

/* Module Cards */
#module-cards-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}
.module-card {
    background: white;
    border-radius: 10px;
    padding: 1.125rem 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border-left: 3px solid #667eea;
    transition: all 0.25s ease;
    cursor: pointer;
    border: 1px solid rgba(0,0,0,0.04);
    border-left: 3px solid #667eea;
}
.module-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.module-card.status-pass {
    border-left-color: #4caf50;
}
.module-card.status-fail {
    border-left-color: #ef5350;
}
.module-card.status-partial {
    border-left-color: #ff9800;
}
.module-card.status-in_progress {
    border-left-color: #f97316;
}
.module-card.status-pending {
    border-left-color: #9e9e9e;
}
.module-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.625rem;
}
.module-card-name {
    font-weight: 700;
    font-size: 0.875rem;
    color: #1e293b;
    line-height: 1.3;
}
.module-card-status {
    padding: 0.2rem 0.5rem;
    border-radius: 8px;
    font-size: 0.625rem;
    font-weight: 600;
    text-transform: uppercase;
    white-space: nowrap;
    letter-spacing: -0.02em;
    line-height: 1.2;
    flex-shrink: 0;
}
.module-card-status.pass {
    background: #e8f5e9;
    color: #2e7d32;
}
.module-card-status.fail {
    background: #ffebee;
    color: #c62828;
}
.module-card-status.partial {
    background: #fff3e0;
    color: #e65100;
}
.module-card-status.in_progress {
    background: #fff7ed;
    color: #ea580c;
    font-size: 0.5625rem;
    padding: 0.2rem 0.4rem;
    letter-spacing: -0.03em;
}
.module-card-status.pending {
    background: #f5f5f5;
    color: #616161;
    font-size: 0.5625rem;
    padding: 0.2rem 0.45rem;
}
.module-card-stats {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    margin-top: 0.625rem;
    padding-top: 0.625rem;
    border-top: 1px solid #e2e8f0;
}
.module-card-stat {
    flex: 1;
    text-align: center;
}
.module-card-stat-value {
    font-size: 1.125rem;
    font-weight: 700;
    color: #1e293b;
}
.module-card-stat-label {
    font-size: 0.6875rem;
    color: #64748b;
    margin-top: 0.25rem;
}

/* Charts */
.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 1.25rem;
    margin-bottom: 1.5rem;
}
.chart-card {
    background: white;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border: 1px solid rgba(0,0,0,0.04);
}
.chart-title {
    font-size: 0.9375rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-align: center;
    color: #1e293b;
}
.chart-container {
    position: relative;
    height: 280px;
}

/* Tables */
.table-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.07);
}
.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}
.table-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
}
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
}
.badge.fail { background: #ffebee; color: #c62828; }
.badge.warn { background: #fff3e0; color: #e65100; }
.badge.waiver { background: #e3f2fd; color: #1565c0; }

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}
thead th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 0.75rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 3px solid #5568d3;
    position: sticky;
    top: 0;
    z-index: 10;
}
/* Waivers table - match Details table header style */
#approved-waivers-table table thead th {
    background: #f5f5f5 !important;
    color: #111827 !important;
    padding: 12px 10px !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #d1d5db !important;
    font-size: 13px !important;
    letter-spacing: 0.5px !important;
}
/* Chart stats table - override global styles */
.chart-stats-table thead th {
    background: #f8fafc !important;
    color: #64748b !important;
    padding: 0.75rem 0 !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    border-bottom: 1px solid #e2e8f0 !important;
    position: static !important;
}
tbody td {
    padding: 0.75rem;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
}
tbody tr:nth-child(even) {
    background: #f8fafc;
}
tbody tr:hover {
    background: #ede9fe;
    transition: background 0.2s ease;
}
.section-cell {
    font-weight: 600;
    color: #667eea;
}

/* Collapsible Table Rows */
.table-row-header {
    cursor: pointer;
    user-select: none;
    transition: background 0.2s ease;
}
.table-row-header:hover {
    background: #f1f5f9 !important;
}
.table-row-header.collapsed {
    border-bottom: 2px solid #e2e8f0;
}
.expand-icon {
    display: inline-block;
    width: 20px;
    height: 20px;
    line-height: 18px;
    text-align: center;
    border-radius: 4px;
    background: #e2e8f0;
    color: #475569;
    font-weight: 700;
    font-size: 0.9rem;
    margin-right: 0.5rem;
    transition: all 0.2s ease;
    vertical-align: middle;
}
.table-row-header:hover .expand-icon {
    background: #667eea;
    color: white;
}
.table-row-header.collapsed .expand-icon {
    transform: rotate(-90deg);
}
.detail-row {
    display: table-row;
    transition: opacity 0.2s ease;
}
.detail-row.collapsed {
    display: none;
}
.item-summary {
    font-size: 0.85rem;
    color: #64748b;
    font-style: italic;
    margin-left: 0.5rem;
}

/* Accordion */
.accordion {
    background: white;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid rgba(0,0,0,0.04);
}
.accordion-header {
    padding: 0.875rem 1rem;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: white;
    transition: background 0.2s ease;
    border-bottom: 1px solid #e2e8f0;
}
.accordion-header:hover {
    background: #f8fafc;
}
.accordion-title {
    font-size: 0.9375rem;
    font-weight: 700;
    color: #1e293b;
}
.accordion-stats {
    font-size: 0.75rem;
    color: #64748b;
}
.accordion-icon {
    font-size: 1.125rem;
    color: #94a3b8;
    transition: transform 0.3s ease;
}
.accordion-header.active .accordion-icon {
    transform: rotate(180deg);
}
.accordion-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}
.accordion-content.active {
    max-height: 5000px;
}
.accordion-body {
    padding: 1rem;
    background: #f8fafc;
}

/* Item Cards */
.item-card {
    background: white;
    border-radius: 8px;
    padding: 0.75rem 0.875rem;
    margin-bottom: 0.625rem;
    border-left: 3px solid #e2e8f0;
}
.item-card.pass { border-left-color: #4caf50; }
.item-card.fail { border-left-color: #ef5350; }
.item-card.pending { border-left-color: #9e9e9e; }
.item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.item-id {
    font-weight: 600;
    font-size: 0.8125rem;
    color: #1e293b;
}
.item-badge {
    padding: 0.2rem 0.625rem;
    border-radius: 10px;
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
}
.item-badge.pass { background: #d0f0d7; color: #1b5e20; }
.item-badge.fail { background: #ffcdd2; color: #b71c1c; }
.item-badge.pending { background: #f5f5f5; color: #757575; }
.item-description {
    font-size: 0.8125rem;
    color: #475569;
    margin-bottom: 0.4rem;
}
.item-details {
    font-size: 0.75rem;
    color: #64748b;
}

/* Module Details Table */
.module-table {
    background: white;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.75rem;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.module-table-header {
    padding: 0.875rem 1rem;
    background: #f8f9fa;
    cursor: pointer;
    user-select: none;
    transition: all 0.2s ease;
    border-bottom: 2px solid #dee2e6;
}
.module-table-header:hover {
    background: #e9ecef;
}
.module-table-header .header-content {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    flex-wrap: wrap;
}
.module-table-header .collapse-icon {
    font-size: 0.875rem;
    color: #495057;
    transition: transform 0.3s ease;
    display: inline-block;
}
.module-table-header.expanded .collapse-icon {
    transform: rotate(90deg);
}
.module-table-header h3 {
    margin: 0;
    color: #212529;
    font-size: 0.9375rem;
    font-weight: 700;
}
.module-table-stage {
    color: #6c757d;
    font-size: 0.75rem;
    font-weight: 500;
}
.module-table-stats {
    margin-left: auto;
    display: flex;
    gap: 1.125rem;
    color: #6c757d;
    font-size: 0.8125rem;
}
.module-table-stats strong {
    font-weight: 700;
}
.module-table-stats .stat-total strong {
    color: #212529;
}
.module-table-stats .stat-executed strong {
    color: #0d6efd;
}
.module-table-stats .stat-pass strong {
    color: #28a745;
}
.module-table-stats .stat-fail strong {
    color: #dc3545;
}
.module-table-stats .stat-pending strong {
    color: #6c757d;
}
.table-content {
    overflow-x: auto;
}
.detail-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    table-layout: fixed;
}
.detail-table thead th:nth-child(1) { width: 110px; }
.detail-table thead th:nth-child(2) { width: 80px; }
.detail-table thead th:nth-child(3) { width: 80px; }
.detail-table thead th:nth-child(4) { width: 100px; }
.detail-table thead th:nth-child(5) { width: 22%; }
.detail-table thead th:nth-child(6) { width: 18%; }
.detail-table thead th:nth-child(7) { width: 22%; }
.detail-table thead th:nth-child(8) { width: 18%; }
.detail-table thead {
    background: #f5f5f5 !important;
    position: sticky;
    top: 0;
    z-index: 10;
    border-bottom: 2px solid #d1d5db;
}
.detail-table thead th {
    padding: 12px 10px;
    text-align: left;
    font-weight: 700;
    color: #111827 !important;
    background: #f5f5f5 !important;
    border-bottom: none;
    font-size: 13px;
    letter-spacing: 0.5px;
}
.detail-table tbody tr {
    border-bottom: 1px solid #e5e7eb;
    transition: background 0.15s ease;
    border-left: 4px solid transparent;
}
.detail-table tbody tr:hover {
    background: #f9fafb;
}
.detail-table tbody tr.status-fail {
    border-left-color: #ef4444;
}
.detail-table tbody tr.status-warning {
    border-left-color: #f59e0b;
}
.detail-table tbody tr.status-pass {
    border-left-color: #10b981;
}
.detail-table tbody td {
    padding: 12px 10px;
    color: #374151;
    vertical-align: top;
    line-height: 1.5;
    word-wrap: break-word;
    font-size: 13px;
}
.detail-table tbody td:first-child {
    font-family: 'Consolas', 'Monaco', monospace;
    font-weight: 600;
    color: #2563eb;
    font-size: 12px;
}
.status-pass {
    background: #ffffff;
}
.status-fail {
    background: #fff5f5;
}
.status-warning {
    background: #fffbeb;
}
.status-no_check {
    background: #ffffff;
}
.table-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.table-badge.badge-pass {
    background: #d0f0d7;
    color: #1b5e20;
}
.table-badge.badge-fail {
    background: #ffcdd2;
    color: #b71c1c;
}
.table-badge.badge-warning {
    background: #fef3c7;
    color: #92400e;
}
.table-badge.badge-no_check {
    background: #f8f9fa;
    color: #9aa0a6;
}
.waiver-block {
    padding: 2px 0;
}
.waiver-item {
    margin: 3px 0;
    padding: 6px 10px;
    background: #e3f2fd;
    border-left: 3px solid #2196f3;
    border-radius: 4px;
    font-size: 11px;
    line-height: 1.6;
    color: #0d47a1;
}
.waiver-item strong {
    color: #1565c0;
    font-weight: 700;
}
.prompt-fail-block {
    margin: 2px 0;
    padding: 4px 8px;
    background: #ffebee;
    border-left: 4px solid #c62828;
    border-radius: 5px;
}
.prompt-fail-block .prompt-item {
    margin: 4px 0;
    padding: 6px 10px;
    background: #ffcdd2;
    color: #b71c1c;
    border-radius: 4px;
    font-size: 11px;
    line-height: 1.6;
}
.prompt-fail-block .prompt-item strong {
    color: #c62828;
    font-weight: 700;
}
.prompt-warn-block {
    margin: 2px 0;
    padding: 4px 8px;
    background: #fff8e1;
    border-left: 4px solid #f57c00;
    border-radius: 5px;
}
.prompt-warn-block .prompt-item {
    margin: 4px 0;
    padding: 6px 10px;
    background: #ffe0b2;
    color: #e65100;
    border-radius: 4px;
    font-size: 11px;
    line-height: 1.6;
}
.prompt-warn-block .prompt-item strong {
    color: #e65100;
    font-weight: 700;
}
.prompt-info-block {
    margin: 2px 0;
    padding: 4px 8px;
    background: #e8f5e9;
    border-left: 4px solid #2e7d32;
    border-radius: 5px;
}
.prompt-info-block .prompt-item {
    margin: 4px 0;
    padding: 6px 10px;
    background: #c8e6c9;
    color: #1b5e20;
    border-radius: 4px;
    font-size: 11px;
    line-height: 1.6;
}
.prompt-info-block .prompt-item strong {
    color: #1b5e20;
    font-weight: 700;
}
.collapsible-cell {
    cursor: pointer;
    position: relative;
    transition: all 0.3s ease;
}
.collapsible-cell.collapsed {
    max-height: 80px;
    overflow: hidden;
}
.collapsible-cell.collapsed::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 30px;
    background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.95));
    pointer-events: none;
}
.collapsible-cell.expanded {
    max-height: none;
}
.collapsible-cell:hover {
    background: rgba(33,150,243,0.05);
    border-radius: 4px;
}

/* Modal styles */
.detail-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    z-index: 9999;
    justify-content: center;
    align-items: center;
    animation: fadeIn 0.2s ease;
}
.detail-modal.active {
    display: flex;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.modal-content {
    background: #ffffff;
    border-radius: 16px;
    max-width: 900px;
    max-height: 85vh;
    width: 90%;
    overflow: auto;
    padding: 28px 32px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    animation: slideUp 0.2s ease;
}
@keyframes slideUp {
    from { 
        transform: translateY(30px);
        opacity: 0;
    }
    to { 
        transform: translateY(0);
        opacity: 1;
    }
}
.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e5e7eb;
}
.modal-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
}
.modal-close {
    font-size: 2rem;
    line-height: 1;
    cursor: pointer;
    background: none;
    border: none;
    color: #64748b;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    transition: all 0.2s;
}
.modal-close:hover {
    background: #f1f5f9;
    color: #1e293b;
}
.modal-body {
    font-size: 13px;
    line-height: 1.6;
    color: #334155;
}

/* Waiver Features */
.waive-btn {
    padding: 4px 10px;
    margin-left: 8px;
    font-size: 11px;
    font-weight: 600;
    border: 1px solid #3b82f6;
    background: white;
    color: #3b82f6;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}
.waive-btn:hover {
    background: #3b82f6;
    color: white;
}
.pending-changes-bar-legacy {
    background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
    border: 2px solid #fb923c;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    display: none;
    align-items: center;
    gap: 0.75rem;
    box-shadow: 0 2px 8px rgba(251, 146, 60, 0.2);
    white-space: nowrap;
    transition: opacity 0.3s ease, transform 0.3s ease;
}
.pending-count-badge {
    background: #ea580c;
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 700;
    margin-left: 8px;
}
.preview-mode-indicator {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    border: 2px solid #3b82f6;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    text-align: center;
    font-weight: 700;
    color: #1e40af;
}

/* Responsive */
@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
    .charts-grid {
        grid-template-columns: 1fr;
    }
    .tabs-container {
        flex-direction: column;
    }
}

/* Utilities */
.text-center { text-align: center; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
.mt-2 { margin-top: 1rem; }

/* Waive Button Styles */
.waive-button {
    margin-left: 8px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}
.waive-button:hover {
    background: #2563eb;
    transform: translateY(-1px);
}
.waive-all-button {
    margin-left: 8px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
    background: #8b5cf6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}
.waive-all-button:hover {
    background: #7c3aed;
    transform: translateY(-1px);
}
/* Skip Button Styles */
.skip-button {
    margin-top: 4px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    background: #f59e0b;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}
.skip-button:hover {
    background: #d97706;
    transform: translateY(-1px);
}
.skip-module-button {
    margin-left: 12px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 600;
    background: #f59e0b;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}
.skip-module-button:hover {
    background: #d97706;
    transform: translateY(-1px);
}

/* Unified Pending Changes Control Bar */
.pending-changes-bar {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 2px solid #f59e0b;
    border-radius: 8px;
    padding: 6px 12px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
    flex-wrap: wrap;
    gap: 8px;
}
.pending-changes-info {
    display: flex;
    align-items: center;
    gap: 8px;
}
.pending-changes-count {
    font-size: 16px;
    font-weight: 700;
    color: #d97706;
}
.pending-changes-label {
    font-size: 12px;
    color: #92400e;
    font-weight: 600;
    white-space: nowrap;
}
.pending-changes-actions {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    flex-wrap: nowrap;
}
/* Waiver Modal Overlay */
.waiver-modal-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: 9999;
    animation: fadeIn 0.2s ease;
    /* Always apply flexbox centering properties */
    align-items: center;
    justify-content: center;
}
.waiver-modal-overlay.active {
    display: flex;
}
.waiver-modal {
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 600px;
    width: 90%;
    max-height: 85vh;
    overflow-y: auto;
    animation: slideIn 0.3s ease;
}
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-20px) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.waiver-modal-header {
    padding: 1.5rem 2rem;
    border-bottom: 2px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px 12px 0 0;
}
.waiver-modal-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: white;
    margin: 0;
}
.waiver-modal-close {
    font-size: 2rem;
    line-height: 1;
    cursor: pointer;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    transition: all 0.2s;
}
.waiver-modal-close:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: rotate(90deg);
}
.waiver-modal-body {
    padding: 2rem;
}
.waiver-info-section {
    margin-bottom: 1.5rem;
    padding: 1rem 1.25rem;
    background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);
    border-radius: 8px;
    border-left: 4px solid #3b82f6;
}
.waiver-info-label {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 0.5rem;
}
.waiver-info-value {
    font-size: 14px;
    color: #1e293b;
    line-height: 1.6;
    font-weight: 500;
}
.waiver-comment-section {
    margin-bottom: 1rem;
}
.waiver-comment-label {
    font-size: 14px;
    font-weight: 600;
    color: #334155;
    margin-bottom: 0.75rem;
    display: block;
}
.waiver-comment-input {
    width: 100%;
    padding: 0.875rem;
    border: 2px solid #cbd5e1;
    border-radius: 8px;
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    min-height: 100px;
    transition: all 0.2s;
}
.waiver-comment-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.waiver-modal-footer {
    padding: 1.25rem 2rem;
    border-top: 2px solid #e5e7eb;
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    background: #f8fafc;
    border-radius: 0 0 12px 12px;
    /* Sticky footer to keep buttons visible */
    position: sticky;
    bottom: 0;
    z-index: 10;
}
.waiver-modal-btn {
    padding: 0.75rem 1.75rem;
    font-size: 14px;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
}
.waiver-cancel-btn {
    background: white;
    color: #64748b;
    border: 2px solid #cbd5e1;
}
.waiver-cancel-btn:hover {
    background: #f1f5f9;
    color: #475569;
    border-color: #94a3b8;
}
.waiver-confirm-btn {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}
.waiver-confirm-btn:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    transform: translateY(-1px);
}

/* Back to Top Button */
#back-to-top {
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50%;
    font-size: 24px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    z-index: 999;
    display: flex;
    align-items: center;
    justify-content: center;
}
#back-to-top.show {
    opacity: 1;
    visibility: visible;
}
#back-to-top:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.6);
    transform: translateY(-3px);
}
#back-to-top:active {
    transform: translateY(-1px);
}

/* ==================== REVIEW MODE STYLES ==================== */
/* Review Mode Banner */
.review-mode-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px 24px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Default: Hide all action buttons (Waive/Skip) */
.waive-button,
.skip-button,
.waive-all-button,
.skip-module-button {
    display: none !important;
}

/* Review Mode Active: Show all action buttons */
body.review-mode-active .waive-button,
body.review-mode-active .skip-button,
body.review-mode-active .waive-all-button,
body.review-mode-active .skip-module-button {
    display: inline-block !important;
}

/* Always show already-actioned buttons (green state) regardless of Review Mode */
.waived-button,
.skipped-button {
    display: inline-block !important;
}

/* Review Mode Active: Add visual indication to module cards */
body.review-mode-active .module-card {
    border-left: 4px solid #667eea;
    background: linear-gradient(to right, rgba(102, 126, 234, 0.03), transparent);
    transition: all 0.3s ease;
}

/* Review Mode Toggle Button Hover Effects */
#review-mode-toggle {
    position: relative;
    overflow: hidden;
}

#review-mode-toggle::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(102, 126, 234, 0.2);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

#review-mode-toggle:active::before {
    width: 300px;
    height: 300px;
}

/* ==================== RESULTS TAB STYLES ==================== */
.results-section {
    margin-bottom: 2rem;
}

.file-card {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.file-card:hover {
    border-color: #6366f1;
    box-shadow: 0 4px 12px rgba(99,102,241,0.15);
    transform: translateY(-2px);
}

.file-card-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
}

.file-icon {
    font-size: 2rem;
    line-height: 1;
    flex-shrink: 0;
}

.file-info {
    flex: 1;
    min-width: 0;
}

.file-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.25rem;
    word-break: break-word;
}

.file-description {
    color: #64748b;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

.file-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    font-size: 0.85rem;
    color: #94a3b8;
}

.file-size {
    font-weight: 600;
    color: #6366f1;
}

.file-date {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.file-card-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.file-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    border: 2px solid;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.preview-btn {
    background: white;
    color: #6366f1;
    border-color: #6366f1;
}

.preview-btn:hover:not(:disabled) {
    background: #6366f1;
    color: white;
}

.preview-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.download-btn {
    background: #10b981;
    color: white;
    border-color: #10b981;
}

.download-btn:hover {
    background: #059669;
    border-color: #059669;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(16,185,129,0.3);
}

/* File Preview Modal */
#file-preview-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.7);
    z-index: 10000;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

.preview-modal-content {
    background: white;
    border-radius: 16px;
    max-width: 90vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
}

.preview-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 2px solid #e2e8f0;
    gap: 1rem;
}

.preview-modal-header h3 {
    margin: 0;
    color: #1e293b;
    font-size: 1.25rem;
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.preview-modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #64748b;
    cursor: pointer;
    padding: 0.25rem;
    line-height: 1;
    transition: color 0.2s;
    flex-shrink: 0;
}

.preview-modal-close:hover {
    color: #ef4444;
}

.preview-modal-body {
    padding: 1.5rem;
    overflow: auto;
    flex: 1;
}

.preview-modal-footer {
    padding: 1rem 1.5rem;
    border-top: 2px solid #e2e8f0;
    display: flex;
    justify-content: flex-end;
}

/* Preview table styles */
.preview-table,
#preview-content table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.preview-table th,
#preview-content table th {
    background: #f8fafc;
    color: #475569;
    font-weight: 600;
    padding: 0.75rem;
    text-align: left;
    border: 1px solid #e2e8f0;
    position: sticky;
    top: 0;
    z-index: 10;
}

.preview-table td,
#preview-content table td {
    padding: 0.75rem;
    border: 1px solid #e2e8f0;
    color: #334155;
}

.preview-table tr:hover,
#preview-content table tr:hover {
    background: #f8fafc;
}
"""


def generate_header(stage: str, timestamp: str) -> str:
    """Generate page header."""
    return f"""
<div class='header'>
    <div class='header-content'>
        <div class='header-left'>
            <h1>📊 IP Signoff Checklist Dashboard</h1>
            <div class='header-meta'>
                Stage: <strong>{html.escape(stage)}</strong> | 
                Generated: <strong>{html.escape(timestamp)}</strong>
            </div>
        </div>
        <div class='header-right'>
            <!-- Review Mode Toggle Button -->
            <button id='review-mode-toggle' 
                    onclick='toggleReviewMode()'
                    style='padding:10px 20px; margin-right:16px; font-size:14px; font-weight:600; 
                           border:2px solid #6b7280; background:white; color:#6b7280; 
                           border-radius:8px; cursor:pointer; transition:all 0.3s;
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1);'
                    onmouseover='if(!REVIEW_MODE_ENABLED) {{ this.style.background="&#35;f3f4f6"; this.style.borderColor="&#35;4b5563"; }}'
                    onmouseout='if(!REVIEW_MODE_ENABLED) {{ this.style.background="white"; this.style.borderColor="&#35;6b7280"; }}'
                    title='Toggle Review Mode to show/hide Waive and Skip buttons'>
                <span id='review-mode-icon'>🔍</span>
                <span id='review-mode-text'>Enable Review Mode</span>
            </button>
            
            <!-- Unified Pending Changes Control Bar (hidden by default, shown when changes exist) -->
            <div id='pending-changes-bar' class='pending-changes-bar' style='display: none;'>
                <div class='pending-changes-info'>
                    <span class='pending-changes-count' id='pending-count'>0</span>
                    <span class='pending-changes-label' id='pending-label'>Pending Changes</span>
                </div>
                <div class='pending-changes-actions' id='pending-changes-actions'>
                    <button onclick='enterPreviewMode()' 
                            style='padding:8px 16px; font-size:14px; font-weight:600; 
                                   border:2px solid #8b5cf6; background:#8b5cf6; color:white; 
                                   border-radius:6px; cursor:pointer; transition:all 0.2s;
                                   box-shadow: 0 2px 4px rgba(139,92,246,0.3);'
                            onmouseover='this.style.background="&#35;7c3aed"; this.style.boxShadow="0 4px 8px rgba(139,92,246,0.4)";'
                            onmouseout='this.style.background="&#35;8b5cf6"; this.style.boxShadow="0 2px 4px rgba(139,92,246,0.3)";'
                            title='Open preview in new window to see changes applied'>
                        �️ Enter Preview
                    </button>
                    <button onclick='exportPendingChangesYAML()' 
                            style='padding:8px 16px; font-size:14px; font-weight:600; 
                                   border:2px solid #10b981; background:white; color:#10b981; 
                                   border-radius:6px; cursor:pointer; transition:all 0.2s;'
                            onmouseover='this.style.background="&#35;10b981"; this.style.color="white";'
                            onmouseout='this.style.background="white"; this.style.color="&#35;10b981";'
                            title='Export pending changes to YAML file'>
                        📄 Export YAML
                    </button>
                    <button onclick='exportPendingChangesExcel()' 
                            style='padding:8px 16px; font-size:14px; font-weight:600; 
                                   border:2px solid #10b981; background:white; color:#10b981; 
                                   border-radius:6px; cursor:pointer; transition:all 0.2s;'
                            onmouseover='this.style.background="&#35;10b981"; this.style.color="white";'
                            onmouseout='this.style.background="white"; this.style.color="&#35;10b981";'
                            title='Export pending changes to Excel file'>
                        📊 Export Excel
                    </button>
                    <button onclick='refreshCacheWithPlatformSupport()' 
                            style='padding:8px 16px; font-size:14px; font-weight:600; 
                                   border:2px solid #6366f1; background:white; color:#6366f1; 
                                   border-radius:6px; cursor:pointer; transition:all 0.2s;'
                            onmouseover='this.style.background="&#35;6366f1"; this.style.color="white";'
                            onmouseout='this.style.background="white"; this.style.color="&#35;6366f1";'
                            title='Clear localStorage and refresh the dashboard (platform-aware)'>
                        🔄 Refresh Cache
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>
"""


def generate_tabs() -> str:
    """Generate tab navigation."""
    return """
<div class='tabs'>
    <div class='tabs-container'>
        <button class='tab-button active' data-tab='dashboard'>Dashboard</button>
        <button class='tab-button' data-tab='details'>Details</button>
        <button class='tab-button' data-tab='waivers'>Waivers</button>
        <button class='tab-button' data-tab='results'>Results</button>
    </div>
</div>
"""


def generate_dashboard_content(modules: List[Dict[str, Any]]) -> str:
    """Generate dashboard tab content with dynamic category filter options.
    
    Args:
        modules: List of module data dictionaries with 'category' field
        
    Returns:
        HTML string for dashboard content
    """
    # Collect available categories from actual module data
    available_categories = set()
    for module in modules:
        category = module.get('category', 'Other')
        if category and category != 'Other':
            available_categories.add(category)
    
    # Sort categories in predefined order
    category_order = ['Configuration', 'Synthesis', 'Verification', 'Physical', 
                      'Timing', 'Power', 'Signoff', 'Final Data']
    sorted_categories = [c for c in category_order if c in available_categories]
    
    # Add 'Other' if there are any uncategorized modules
    if any(m.get('category') == 'Other' for m in modules):
        sorted_categories.append('Other')
    
    # Generate category filter options HTML
    category_options_html = '<option value=\'all\'>All Categories</option>\n'
    for category in sorted_categories:
        category_options_html += f'            <option value=\'{category}\'>{category}</option>\n'
    
    return f"""
<div style='display:flex; justify-content:space-between; align-items:center; gap:2rem; margin-bottom:1.5rem;'>
    <div id='status-indicator' class='status-indicator-compact'>
        <div class='status-icon-wrapper'>
            <span id='status-icon'>⏳</span>
        </div>
        <div class='status-content'>
            <div class='status-text' id='status-text'>Loading...</div>
            <div class='status-subtext' id='status-subtext'>Please wait</div>
        </div>
    </div>
    
    <label style='display:flex; align-items:center; gap:0.75rem; cursor:pointer; font-weight:500; color:#4a5568; white-space:nowrap;'>
        <span>Filter by Category:</span>
        <select id='category-filter' style='padding:0.5rem 2rem 0.5rem 0.75rem; border:2px solid #cbd5e1; border-radius:8px; cursor:pointer; font-weight:500; background:white; color:#475569; transition:border-color 0.2s;' 
                onmouseover='this.style.borderColor="#6366f1"' onmouseout='this.style.borderColor="#cbd5e1"'>
            {category_options_html.rstrip()}
        </select>
    </label>
</div>

<div class='executive-summary'>
    <div class='metrics-grid' id='metrics-grid'>
        <!-- Metrics will be populated by JavaScript -->
    </div>
</div>

<div class='progress-section'>
    <h2 class='section-title'>Progress by Category</h2>
    <div id='category-progress'>
        <!-- Progress bars will be populated by JavaScript -->
    </div>
</div>

<div class='charts-grid' style='margin-bottom:2rem;'>
    <div class='chart-card'>
        <h3 class='chart-title'>Module Status Distribution</h3>
        <div class='chart-container' id='sectionChart'></div>
    </div>
    <div class='chart-card'>
        <h3 class='chart-title'>Check Items Progress</h3>
        <div class='chart-container' id='progressChart'></div>
    </div>
</div>

<div class='progress-section' id='module-status-section'>
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;'>
        <h2 class='section-title' style='margin-bottom:0;'>Module Status</h2>
        <div style='display:flex; align-items:center; gap:0.5rem;'>
            <label style='font-weight:500; color:#4a5568;'>Sort by:</label>
            <select id='module-sort' style='padding:0.5rem 2rem 0.5rem 0.75rem; border:2px solid #667eea; border-radius:6px; cursor:pointer; font-weight:500; background:white; color:#4a5568;'>
                <option value='name'>Name</option>
                <option value='status'>Status</option>
                <option value='pass-rate'>Pass Rate</option>
                <option value='execution-rate'>Execution Rate</option>
            </select>
        </div>
    </div>
    <div id='module-cards-container' style='min-height:200px;'>
        <!-- Module cards will be populated by JavaScript -->
    </div>
</div>
"""


def generate_waivers_content() -> str:
    """Generate waivers tab content."""
    return """
<!-- Waivers Sub-tabs -->
<div class='sub-tabs' style='margin-bottom:2rem;'>
    <div class='tabs-container' style='border-bottom:2px solid #e2e8f0;'>
        <button class='tab-button active' data-subtab='approved' 
                style='padding:0.75rem 1.5rem; margin-right:0.5rem; border:none; background:transparent; cursor:pointer; font-weight:600; color:#64748b; border-bottom:3px solid transparent; transition:all 0.3s;'>
            ✓ Approved
        </button>
        <button class='tab-button' data-subtab='pending' 
                style='padding:0.75rem 1.5rem; border:none; background:transparent; cursor:pointer; font-weight:600; color:#64748b; border-bottom:3px solid transparent; transition:all 0.3s;'>
            ⏳ Pending
        </button>
    </div>
</div>

<!-- Approved Waivers Content -->
<div id='approved-waivers-content' class='subtab-content' style='display:block;'>
    <div class='table-card'>
        <div class='table-header'>
            <h2 class='table-title'>✓ Approved Waivers</h2>
            <span class='badge waiver' id='approved-waiver-count'>0</span>
        </div>
        <div class='search-box' style='margin-bottom:1rem;'>
            <input type='text' id='approved-waivers-search' placeholder='🔍 Search approved waivers...' 
                   style='width:100%; padding:0.75rem 1rem; border:2px solid #e2e8f0; border-radius:8px; font-size:0.95rem; transition:border-color 0.3s;'
                   onfocus='this.style.borderColor="#667eea"' onblur='this.style.borderColor="#e2e8f0"'>
        </div>
        <div id='approved-waivers-table'>
            <!-- Table will be populated by JavaScript -->
        </div>
    </div>
</div>

<!-- Pending Waivers Content -->
<div id='pending-waivers-content' class='subtab-content' style='display:none;'>
    <div class='table-card'>
        <div class='table-header'>
            <h2 class='table-title'>⏳ Pending Waivers</h2>
            <span class='badge pending' id='pending-waiver-count'>0</span>
        </div>
        <div class='search-box' style='margin-bottom:1rem;'>
            <input type='text' id='pending-waivers-search' placeholder='🔍 Search pending waivers...' 
                   style='width:100%; padding:0.75rem 1rem; border:2px solid #e2e8f0; border-radius:8px; font-size:0.95rem; transition:border-color 0.3s;'
                   onfocus='this.style.borderColor="#9333ea"' onblur='this.style.borderColor="#e2e8f0"'>
        </div>
        <div id='pending-waivers-table'>
            <!- Table will be populated by JavaScript -->
        </div>
    </div>
</div>
"""


def generate_details_content() -> str:
    """Generate details tab content."""
    return """
<!-- Module Quick Navigation Cards -->
<div id='module-quick-nav' style='margin-bottom:2rem;'>
    <h2 class='section-title' style='margin-bottom:1rem;'>📑 Module Quick Navigation</h2>
    <div id='module-nav-cards' style='display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:0.75rem;'>
        <!-- Module nav cards will be populated by JavaScript -->
    </div>
</div>

<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;'>
    <h2 class='section-title' style='margin-bottom:0;'>📋 Module Item Details</h2>
    <div style='display:flex; align-items:center; gap:1rem; flex-wrap:wrap; margin-left:auto;'>
        <label style='display:flex; align-items:center; gap:0.5rem; cursor:pointer; font-weight:500; color:#4a5568;'>
            <input type='checkbox' id='show-problems-only' style='width:18px; height:18px; cursor:pointer;'>
            <span style='display:flex; align-items:center; gap:0.3rem;'><svg width='16' height='16' viewBox='0 0 16 16' style='display:inline-block;'><path d='M8 2 L15 14 L1 14 Z' fill='#ef4444' stroke='#dc2626' stroke-width='0.8'/><path d='M7.5 6 L8.5 6 L8.5 10 L7.5 10 Z' fill='white'/><circle cx='8' cy='12' r='0.6' fill='white'/></svg>Problems</span>
        </label>
        <label style='display:flex; align-items:center; gap:0.5rem; cursor:pointer; font-weight:500; color:#4a5568;'>
            <input type='checkbox' id='show-warnings-only' style='width:18px; height:18px; cursor:pointer;'>
            <span>⚠️ Warns</span>
        </label>
        <div class='accordion-controls'>
            <button id='toggle-all-sections-btn' style='padding:0.5rem 1rem; border:2px solid #667eea; background:white; color:#667eea; border-radius:6px; cursor:pointer; font-weight:600; transition:all 0.3s;' 
                    onmouseover='this.style.background="#667eea"; this.style.color="white"' 
                    onmouseout='this.style.background="white"; this.style.color="#667eea"'>
                <span id='toggle-icon'>▼</span> <span id='toggle-text'>Expand</span>
            </button>
        </div>
    </div>
</div>
<div id='module-details-list'>
    <!-- Module tables will be populated by JavaScript -->
</div>
"""


def generate_results_content(files_info: List[Dict[str, Any]]) -> str:
    """Generate results tab content with file download/preview cards."""
    if not files_info:
        return """
<div style='text-align:center; padding:3rem; color:#64748b;'>
    <svg width='64' height='64' viewBox='0 0 24 24' fill='none' stroke='currentColor' style='margin:0 auto 1rem;'>
        <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'/>
    </svg>
    <h3 style='color:#475569; margin-bottom:0.5rem;'>No Result Files Found</h3>
    <p style='color:#94a3b8;'>Run the checklist automation to generate result files.</p>
</div>
"""
    
    html = "<div style='max-width:1200px; margin:0 auto;'>\n"
    html += "<h2 class='section-title' style='margin-bottom:1.5rem;'>📊 Checklist Result Files</h2>\n"
    
    # Group files by type
    xlsx_files = [f for f in files_info if f['extension'] == '.xlsx']
    csv_files = [f for f in files_info if f['extension'] == '.csv']
    yaml_files = [f for f in files_info if f['extension'] in ['.yaml', '.yml']]
    
    # Excel files section
    if xlsx_files:
        html += "<div class='results-section'>\n"
        html += "<h3 style='color:#6366f1; margin-bottom:1rem; font-size:1.1rem; font-weight:600;'>📄 Excel Reports</h3>\n"
        for file in xlsx_files:
            html += generate_file_card(file)
        html += "</div>\n"
    
    # CSV files section
    if csv_files:
        html += "<div class='results-section' style='margin-top:2rem;'>\n"
        html += "<h3 style='color:#10b981; margin-bottom:1rem; font-size:1.1rem; font-weight:600;'>📋 CSV Data Files</h3>\n"
        for file in csv_files:
            html += generate_file_card(file)
        html += "</div>\n"
    
    # YAML files section
    if yaml_files:
        html += "<div class='results-section' style='margin-top:2rem;'>\n"
        html += "<h3 style='color:#8b5cf6; margin-bottom:1rem; font-size:1.1rem; font-weight:600;'>⚙️ Configuration Files</h3>\n"
        for file in yaml_files:
            html += generate_file_card(file)
        html += "</div>\n"
    
    html += "</div>\n"
    return html


def generate_file_card(file_info: Dict[str, Any]) -> str:
    """Generate a single file card with preview and download buttons."""
    name = file_info['name']
    size_str = file_info['size_str']
    modified = file_info['modified']
    description = file_info['description']
    preview_available = file_info['preview_available']
    display_path = file_info.get('display_path', name)  # Use display_path for subdirectory files
    file_id = name.replace('.', '_').replace(' ', '_')
    
    # Preview button
    if preview_available:
        preview_btn = f"""
        <button class='file-action-btn preview-btn' onclick='previewFile("{file_id}")' 
                title='Preview file content in browser'>
            <svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor'>
                <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M15 12a3 3 0 11-6 0 3 3 0 016 0z'/>
                <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z'/>
            </svg>
            Preview
        </button>
        """
    else:
        preview_btn = """
        <button class='file-action-btn preview-btn' disabled 
                title='File too large for preview' style='opacity:0.5; cursor:not-allowed;'>
            <svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor'>
                <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21'/>
            </svg>
            Too Large
        </button>
        """
    
    # Download button
    download_btn = f"""
    <button class='file-action-btn download-btn' onclick='downloadFile("{file_id}")' 
            title='Download original file'>
        <svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor'>
            <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4'/>
        </svg>
        Download
    </button>
    """
    
    return f"""
<div class='file-card' data-file-id='{file_id}'>
    <div class='file-card-header'>
        <div class='file-icon'>📄</div>
        <div class='file-info'>
            <div class='file-name'>{display_path}</div>
            {f"<div class='file-description'>{description}</div>" if description else ""}
            <div class='file-meta'>
                <span class='file-size'>{size_str}</span>
                <span class='file-date'>Modified: {modified}</span>
            </div>
        </div>
    </div>
    <div class='file-card-actions'>
        {preview_btn}
        {download_btn}
    </div>
</div>
"""


def generate_javascript() -> str:
    """Generate JavaScript code."""
    return """
// ==================== DASHBOARD JAVASCRIPT ====================

// ==================== REVIEW MODE SYSTEM ====================
// Review Mode state - controls visibility of Waive/Skip buttons
let REVIEW_MODE_ENABLED = false;

// ==================== UNIFIED WAIVE/SKIP SYSTEM ====================
// Unified pending changes storage (waivers + skips)
let PENDING_CHANGES = [];

// Cache version - increment this when data structure changes
const CHANGES_CACHE_VERSION = '2.0';
const CACHE_EXPIRY_DAYS = 7; // Auto-expire changes after 7 days

// Check if this is preview mode and load preview data if needed
function checkAndLoadPreviewMode() {
    // Check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const isPreview = urlParams.get('preview') === 'true';
    
    if (isPreview) {
        console.log('[Preview] Preview mode detected - loading data from sessionStorage');
        try {
            const previewModules = sessionStorage.getItem('preview_modules_data');
            const previewStats = sessionStorage.getItem('preview_overall_stats');
            const previewIssues = sessionStorage.getItem('preview_issues_data');
            const previewPendingChanges = sessionStorage.getItem('preview_pending_changes');
            
            if (previewModules && previewStats) {
                // Replace global data with preview data
                MODULES_DATA = JSON.parse(previewModules);
                OVERALL_STATS = JSON.parse(previewStats);
                if (previewIssues) {
                    ISSUES_DATA = JSON.parse(previewIssues);
                }
                if (previewPendingChanges) {
                    PENDING_CHANGES = JSON.parse(previewPendingChanges);
                }
                
                console.log('[Preview] Preview data loaded successfully');
                console.log('[Preview] Modules:', MODULES_DATA.length);
                console.log('[Preview] Stats:', OVERALL_STATS);
                console.log('[Preview] Pending changes:', PENDING_CHANGES.length);
                
                // Set preview mode flag for runtime detection
                // (This may already be set by enterPreviewMode, but ensure it's set)
                if (sessionStorage.getItem('previewModeActive') !== 'true') {
                    sessionStorage.setItem('previewModeActive', 'true');
                    console.log('[Preview] previewModeActive flag set to: true');
                }
                
                // Add preview indicator to header
                const header = document.querySelector('.header h1');
                if (header) {
                    header.innerHTML += ' <span style="background:#f093fb; padding:4px 12px; border-radius:4px; font-size:0.8em; margin-left:10px;">PREVIEW MODE</span>';
                }
                
                // Completely replace header-right content in preview mode
                const headerRight = document.querySelector('.header-right');
                if (headerRight) {
                    // Clear all existing content
                    headerRight.innerHTML = '';
                    
                    // Create exit button with improved design
                    const exitBtn = document.createElement('button');
                    exitBtn.innerHTML = '✖️ Exit Preview Mode';
                    exitBtn.onclick = function() { window.close(); };
                    exitBtn.style.cssText = `
                        padding: 10px 24px;
                        font-size: 14px;
                        font-weight: 600;
                        border: 2px solid #ef4444;
                        background: linear-gradient(135deg, #fee2e2 0%, #ffffff 100%);
                        color: #dc2626;
                        border-radius: 8px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
                    `;
                    exitBtn.onmouseover = function() {
                        this.style.background = 'linear-gradient(135deg, #fecaca 0%, #fee2e2 100%)';
                        this.style.boxShadow = '0 4px 12px rgba(239, 68, 68, 0.3)';
                        this.style.transform = 'translateY(-1px)';
                    };
                    exitBtn.onmouseout = function() {
                        this.style.background = 'linear-gradient(135deg, #fee2e2 0%, #ffffff 100%)';
                        this.style.boxShadow = '0 2px 8px rgba(239, 68, 68, 0.2)';
                        this.style.transform = 'translateY(0)';
                    };
                    exitBtn.title = 'Close preview window and return to main dashboard';
                    headerRight.appendChild(exitBtn);
                }
                
                return true;
            } else {
                console.warn('[Preview] Preview data not found in sessionStorage');
            }
        } catch (e) {
            console.error('[Preview] Error loading preview data:', e);
        }
    }
    return false;
}

// Load changes from localStorage with version control and auto-cleanup
function loadChanges() {
    try {
        // Check cache version
        const cacheVersion = localStorage.getItem('changes_cache_version');
        if (cacheVersion !== CHANGES_CACHE_VERSION) {
            console.log('[Cache] Version mismatch. Clearing old cache. Old:', cacheVersion, 'New:', CHANGES_CACHE_VERSION);
            localStorage.removeItem('pending_changes');
            localStorage.setItem('changes_cache_version', CHANGES_CACHE_VERSION);
            PENDING_CHANGES = [];
            return;
        }
        
        const stored = localStorage.getItem('pending_changes');
        if (stored) {
            const allChanges = JSON.parse(stored);
            
            // Filter out expired changes
            const now = new Date();
            const validChanges = allChanges.filter(c => {
                if (!c.timestamp) return true; // Keep changes without timestamp for safety
                const changeDate = new Date(c.timestamp);
                const daysDiff = (now - changeDate) / (1000 * 60 * 60 * 24);
                return daysDiff < CACHE_EXPIRY_DAYS;
            });
            
            const expiredCount = allChanges.length - validChanges.length;
            if (expiredCount > 0) {
                console.log('[Cache] Removed', expiredCount, 'expired change(s)');
            }
            
            PENDING_CHANGES = validChanges;
            
            // Save cleaned data back
            if (expiredCount > 0) {
                saveChanges();
            }
            
            console.log('[Cache] Loaded', PENDING_CHANGES.length, 'valid pending change(s)',
                '(' + PENDING_CHANGES.filter(c => c.type === 'waive').length + ' waivers,',
                PENDING_CHANGES.filter(c => c.type === 'skip').length + ' skips)');
        }
    } catch (e) {
        console.error('[Cache] Error loading changes:', e);
        PENDING_CHANGES = [];
    }
}

// Save changes to localStorage
function saveChanges() {
    try {
        localStorage.setItem('pending_changes', JSON.stringify(PENDING_CHANGES));
        localStorage.setItem('changes_cache_version', CHANGES_CACHE_VERSION);
        const waiverCount = PENDING_CHANGES.filter(c => c.type === 'waive').length;
        const skipCount = PENDING_CHANGES.filter(c => c.type === 'skip').length;
        console.log('[Cache] Saved', PENDING_CHANGES.length, 'pending change(s)',
            '(' + waiverCount + ' waivers, ' + skipCount + ' skips)');
    } catch (e) {
        console.error('[Cache] Error saving changes:', e);
    }
}

// ==================== PREVIEW MODE: DATA TRANSFORMATION FUNCTIONS ====================

// Deep clone data to avoid reference issues
function deepCloneData(data) {
    return JSON.parse(JSON.stringify(data));
}

// Recalculate module statistics
function recalculateModuleStats(module) {
    const total = (module.items || []).length;
    const passCount = (module.items || []).filter(item => item.status === 'pass').length;
    const failCount = (module.items || []).filter(item => item.status === 'fail').length;
    const pending = (module.items || []).filter(item => 
        ['pending', 'na', 'N/A', 'not_started'].includes(item.status)
    ).length;
    const executed = passCount + failCount;
    
    module.stats = {
        total: total,
        executed: executed,
        pass: passCount,
        fail: failCount,
        pending: pending,
        pass_rate: total > 0 ? Math.round(passCount / total * 100 * 10) / 10 : 0,
        execution_rate: total > 0 ? Math.round(executed / total * 100 * 10) / 10 : 0
    };
    
    // Update overall module status
    if (failCount === 0 && executed === total) {
        module.overall_status = 'ready';
    } else if (failCount > 0) {
        module.overall_status = 'needs_attention';
    } else {
        module.overall_status = 'in_progress';
    }
}

// Recalculate overall statistics
function recalculateOverallStats(modules) {
    const totalModules = modules.length;
    let totalItems = 0;
    let totalPass = 0;
    let totalFail = 0;
    let totalPending = 0;
    let modulesReady = 0;
    let modulesNeedsAttention = 0;
    
    modules.forEach(module => {
        totalItems += module.stats.total;
        totalPass += module.stats.pass;
        totalFail += module.stats.fail;
        totalPending += module.stats.pending;
        
        if (module.overall_status === 'ready') modulesReady++;
        if (module.overall_status === 'needs_attention') modulesNeedsAttention++;
    });
    
    // Count unique waived items (not waiver records)
    // In Preview Mode: combine original waivers from YAML + new waivers from PENDING_CHANGES
    console.log('============================================');
    console.log('[recalculateOverallStats] 🔍 Waiver Calculation Debug');
    console.log('============================================');
    
    let totalWaiver = 0;
    const waivedItems = new Set();
    
    // 1. Count original waivers from YAML data (items with waivers array)
    console.log('[Recalc] Step 1: Counting original waivers from YAML data');
    console.log('[Recalc] Total modules:', modules.length);
    
    let yamlWaiverCount = 0;
    modules.forEach(m => {
        m.items.forEach(item => {
            if (item.waivers && Array.isArray(item.waivers) && item.waivers.length > 0) {
                const itemKey = m.name + '::' + item.id;
                console.log(`[Recalc YAML] Found: ${itemKey} (${item.waivers.length} waiver records)`);
                waivedItems.add(itemKey);
                yamlWaiverCount++;
            }
        });
    });
    console.log(`[Recalc] ✓ YAML: ${yamlWaiverCount} items with waivers, ${waivedItems.size} unique in Set`);
    console.log('[Recalc] Current Set:', Array.from(waivedItems));
    
    // 2. Add new waivers from PENDING_CHANGES (user's manual additions)
    console.log('[Recalc] Step 2: Adding pending waivers from PENDING_CHANGES');
    console.log('[Recalc] PENDING_CHANGES exists?', typeof PENDING_CHANGES !== 'undefined');
    console.log('[Recalc] PENDING_CHANGES length:', typeof PENDING_CHANGES !== 'undefined' ? PENDING_CHANGES.length : 'N/A');
    
    if (typeof PENDING_CHANGES !== 'undefined') {
        const waiveChanges = PENDING_CHANGES.filter(change => change.type === 'waive');
        console.log(`[Recalc] ✓ Found ${waiveChanges.length} waive-type changes`);
        
        let pendingAdded = 0;
        waiveChanges.forEach(waiver => {
            const itemKey = waiver.moduleName + '::' + waiver.itemId;
            const alreadyExists = waivedItems.has(itemKey);
            console.log(`[Recalc PENDING] ${itemKey} - Already exists? ${alreadyExists}`);
            waivedItems.add(itemKey);
            if (!alreadyExists) pendingAdded++;
        });
        console.log(`[Recalc] ✓ PENDING: ${waiveChanges.length} total, ${pendingAdded} new unique items added`);
    } else {
        console.log('[Recalc] ⚠ PENDING_CHANGES not available');
    }
    
    totalWaiver = waivedItems.size;
    console.log('============================================');
    console.log(`[Recalc] 📊 FINAL: ${totalWaiver} unique waived items (YAML + PENDING)`);
    console.log('[Recalc] Final Set:', Array.from(waivedItems));
    console.log('============================================');
    
    const totalExecuted = totalPass + totalFail;
    
    // Return field names matching OVERALL_STATS format (without underscores)
    return {
        total: totalItems,
        executed: totalExecuted,
        pass: totalPass,
        fail: totalFail,
        pending: totalPending,
        waiver: totalWaiver,
        pass_rate: totalItems > 0 ? Math.round(totalPass / totalItems * 100 * 10) / 10 : 0,
        execution_rate: totalItems > 0 ? Math.round(totalExecuted / totalItems * 100 * 10) / 10 : 0,
        overall_status: modulesReady > 0 ? 'ready' : (modulesNeedsAttention > 0 ? 'needs_attention' : 'unknown')
    };
}

// ==================== PREVIEW MODE: APPLY WAIVERS ====================

function applyWaiversToModules(modules, waivers) {
    const modulesCopy = deepCloneData(modules);
    
    // Group waivers by module and item for efficient lookup
    const waiverMap = {};
    waivers.forEach(waiver => {
        const key = waiver.moduleName + '::' + waiver.itemId;
        if (!waiverMap[key]) waiverMap[key] = [];
        waiverMap[key].push(waiver);
    });
    
    console.log('[Preview] Applying', waivers.length, 'waiver(s) to modules...');
    let appliedCount = 0;
    
    // Apply waivers to each module
    modulesCopy.forEach(module => {
        const moduleName = module.name;
        
        (module.items || []).forEach(item => {
            const key = moduleName + '::' + item.id;
            if (!waiverMap[key]) return;
            
            const itemWaivers = waiverMap[key];
            if (!item.failures || item.failures.length === 0) return;
            
            // Mark failures as waived
            itemWaivers.forEach(waiver => {
                if (waiver.failureIndex === -1) {
                    // Waive all failures
                    item.failures.forEach(failure => {
                        failure.waived = true;
                        failure.waiver_comment = waiver.comment || 'Pending waiver';
                        failure.waiver_timestamp = waiver.timestamp || '';
                    });
                    appliedCount++;
                } else {
                    // Waive specific failure
                    const idx = waiver.failureIndex;
                    if (idx >= 0 && idx < item.failures.length) {
                        item.failures[idx].waived = true;
                        item.failures[idx].waiver_comment = waiver.comment || 'Pending waiver';
                        item.failures[idx].waiver_timestamp = waiver.timestamp || '';
                        appliedCount++;
                    }
                }
            });
            
            // Check if all failures are waived
            const allWaived = item.failures.every(f => f.waived);
            if (allWaived && item.failures.length > 0) {
                item.status = 'pass';
                item.waiver_applied = true;
            }
        });
        
        // Recalculate module statistics
        recalculateModuleStats(module);
    });
    
    console.log('[Preview] Applied', appliedCount, 'waiver(s) successfully');
    return modulesCopy;
}

// ==================== PREVIEW MODE: APPLY SKIPS ====================

function applySkipsToModules(modules, skips) {
    if (!skips || skips.length === 0) {
        console.log('[Preview] No skips to apply');
        return modules;
    }
    
    console.log('[Preview] Processing', skips.length, 'skip entries...');
    
    // Build skip sets for fast lookup
    const moduleFullSkip = new Set();
    const itemSkipMap = {};
    
    skips.forEach(skip => {
        const moduleName = skip.moduleName;
        const itemId = skip.itemId;
        
        if (!moduleName) return;
        
        if (!itemId || itemId === 'null' || itemId === '') {
            // Skip entire module
            moduleFullSkip.add(moduleName);
            console.log('[Preview] Will skip entire module:', moduleName);
        } else {
            // Skip specific item
            if (!itemSkipMap[moduleName]) {
                itemSkipMap[moduleName] = new Set();
            }
            itemSkipMap[moduleName].add(itemId);
        }
    });
    
    // Filter modules and items
    const filteredModules = [];
    let skippedModuleCount = 0;
    let skippedItemCount = 0;
    
    modules.forEach(module => {
        const moduleName = module.name;
        
        // Skip entire module?
        if (moduleFullSkip.has(moduleName)) {
            skippedModuleCount++;
            return;
        }
        
        // Clone module before modifying
        const moduleCopy = deepCloneData(module);
        
        // Filter items within module
        if (itemSkipMap[moduleName]) {
            const originalItemCount = (moduleCopy.items || []).length;
            moduleCopy.items = (moduleCopy.items || []).filter(item => {
                if (itemSkipMap[moduleName].has(item.id)) {
                    skippedItemCount++;
                    return false;
                }
                return true;
            });
            
            // Recalculate stats after filtering
            if (moduleCopy.items.length !== originalItemCount) {
                recalculateModuleStats(moduleCopy);
            }
        }
        
        filteredModules.push(moduleCopy);
    });
    
    console.log('[Preview] Skipped', skippedModuleCount, 'module(s),', skippedItemCount, 'item(s)');
    return filteredModules;
}

// ==================== PREVIEW MODE: OPEN IN NEW WINDOW ====================

function enterPreviewMode() {
    if (PENDING_CHANGES.length === 0) {
        showMessageModal('Preview Mode', 'No pending changes to preview.\\n\\nPlease add some waivers or skips first.');
        return;
    }
    
    console.log('[Preview] Preparing preview data...');
    
    // Separate waivers and skips
    const waivers = PENDING_CHANGES.filter(c => c.type === 'waive');
    const skips = PENDING_CHANGES.filter(c => c.type === 'skip');
    
    console.log('[Preview] Applying', waivers.length, 'waiver(s),', skips.length, 'skip(s)');
    
    // Apply changes to cloned data
    let previewData = deepCloneData(MODULES_DATA);
    previewData = applyWaiversToModules(previewData, waivers);
    previewData = applySkipsToModules(previewData, skips);
    const previewStats = recalculateOverallStats(previewData);
    
    // Store preview data in sessionStorage for the new window
    try {
        sessionStorage.setItem('preview_modules_data', JSON.stringify(previewData));
        sessionStorage.setItem('preview_overall_stats', JSON.stringify(previewStats));
        sessionStorage.setItem('preview_issues_data', JSON.stringify(ISSUES_DATA));
        sessionStorage.setItem('preview_pending_changes', JSON.stringify(PENDING_CHANGES));
        sessionStorage.setItem('preview_timestamp', new Date().toISOString());
        sessionStorage.setItem('previewModeActive', 'true');  // Set preview mode flag
        
        console.log('[Preview] Data saved to sessionStorage');
        console.log('[Preview] previewModeActive flag set to: true');
        
        // Get current page path
        const currentPath = window.location.pathname;
        const currentDir = currentPath.substring(0, currentPath.lastIndexOf('/'));
        
        // Open preview in new window (same HTML file, but will detect preview mode)
        const previewUrl = window.location.href.split('?')[0] + '?preview=true&t=' + Date.now();
        const previewWindow = window.open(previewUrl, '_blank');
        
        if (!previewWindow) {
            showMessageModal('Preview Mode', 'Pop-up blocked! Please allow pop-ups for this site and try again.');
        } else {
            console.log('[Preview] Preview window opened successfully');
        }
    } catch (e) {
        console.error('[Preview] Error saving to sessionStorage:', e);
        showMessageModal('Preview Mode', 'Error preparing preview data. Please try again.');
    }
}

// Clear cache (for manual cleanup)
// DISABLED: This function had issues with page reload. Use Refresh Cache button instead.
// function clearChangesCache() {
//     if (PENDING_CHANGES.length === 0) {
//         showMessageModal('Clear All', 'No pending changes to clear.');
//         return;
//     }
//     
//     const waiverCount = PENDING_CHANGES.filter(c => c.type === 'waive').length;
//     const skipCount = PENDING_CHANGES.filter(c => c.type === 'skip').length;
//     let message = 'Are you sure you want to clear all ' + PENDING_CHANGES.length + ' pending change(s)?\\n';
//     message += '(' + waiverCount + ' waivers, ' + skipCount + ' skips)\\n\\n';
//     message += 'This action cannot be undone.';
//     
//     // Create custom confirmation dialog with manual button handling
//     const overlay = document.getElementById('message-modal-overlay');
//     const titleEl = document.getElementById('message-modal-title');
//     const contentEl = document.getElementById('message-modal-content');
//     const footerEl = overlay.querySelector('.waiver-modal-footer');
//     
//     // Set title and content
//     titleEl.textContent = 'Clear All';
//     contentEl.textContent = message;
//     
//     // Clear existing buttons
//     footerEl.innerHTML = '';
//     
//     // Create Cancel button
//     const cancelBtn = document.createElement('button');
//     cancelBtn.className = 'waiver-modal-btn waiver-cancel-btn';
//     cancelBtn.textContent = 'Cancel';
//     cancelBtn.onclick = () => {
//         console.log('[Clear All] Cancelled');
//         closeMessageModal();
//     };
//     footerEl.appendChild(cancelBtn);
//     
//     // Create Clear All button
//     const clearBtn = document.createElement('button');
//     clearBtn.className = 'waiver-modal-btn waiver-confirm-btn';
//     clearBtn.textContent = 'Clear All';
//     clearBtn.id = 'clear-all-confirm-btn';
//     
//     console.log('[Clear All] Creating Clear All button');
//     
//     // Use addEventListener for more reliable event binding
//     clearBtn.addEventListener('click', function(e) {
//         console.log('[Clear All] ============ BUTTON CLICKED ============');
//         console.log('[Clear All] Event:', e);
//         console.log('[Clear All] Current PENDING_CHANGES:', PENDING_CHANGES.length);
//         
//         e.preventDefault();
//         e.stopPropagation();
//         
//         // Clear data
//         PENDING_CHANGES = [];
//         localStorage.removeItem('pending_changes');
//         localStorage.removeItem('changes_cache_version');
//         
//         console.log('[Clear All] Data cleared from localStorage');
//         console.log('[Clear All] Attempting page reload...');
//         
//         // Try multiple reload methods
//         try {
//             console.log('[Clear All] Method 1: window.location.reload(true)');
//             window.location.reload(true);
//         } catch (err1) {
//             console.error('[Clear All] Method 1 failed:', err1);
//             try {
//                 console.log('[Clear All] Method 2: window.location.href assignment');
//                 window.location.href = window.location.href;
//             } catch (err2) {
//                 console.error('[Clear All] Method 2 failed:', err2);
//                 alert('Failed to reload page. Please refresh manually (F5)');
//             }
//         }
//     }, false);
//     
//     footerEl.appendChild(clearBtn);
//     
//     console.log('[Clear All] Button appended to footer');
//     console.log('[Clear All] Footer element:', footerEl);
//     console.log('[Clear All] Button element:', clearBtn);
//     
//     // Show modal
//     overlay.style.display = 'flex';
//     
//     console.log('[Clear All] Modal displayed');
// }

// ==================== REVIEW MODE FUNCTIONS ====================
/**
 * Toggle Review Mode - Show/hide Waive and Skip buttons
 */
function toggleReviewMode() {
    REVIEW_MODE_ENABLED = !REVIEW_MODE_ENABLED;
    
    console.log('[Review Mode]', REVIEW_MODE_ENABLED ? 'Activated' : 'Deactivated');
    
    // Update UI
    updateReviewModeUI();
}

/**
 * Update Review Mode UI elements
 */
function updateReviewModeUI() {
    const body = document.body;
    const banner = document.getElementById('review-mode-banner');
    const toggleButton = document.getElementById('review-mode-toggle');
    const icon = document.getElementById('review-mode-icon');
    const text = document.getElementById('review-mode-text');
    
    if (REVIEW_MODE_ENABLED) {
        // Add review-mode-active class to body for CSS control
        body.classList.add('review-mode-active');
        
        // Show banner
        if (banner) {
            banner.style.display = 'block';
        }
        
        // Update toggle button to active state
        if (toggleButton) {
            toggleButton.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            toggleButton.style.color = 'white';
            toggleButton.style.borderColor = '#667eea';
            toggleButton.style.boxShadow = '0 4px 6px rgba(102, 126, 234, 0.4)';
        }
        if (icon) icon.textContent = '📝';
        if (text) text.textContent = 'Review Mode Active';
        
    } else {
        // Remove review-mode-active class
        body.classList.remove('review-mode-active');
        
        // Hide banner
        if (banner) {
            banner.style.display = 'none';
        }
        
        // Update toggle button to inactive state
        if (toggleButton) {
            toggleButton.style.background = 'white';
            toggleButton.style.color = '#6b7280';
            toggleButton.style.borderColor = '#6b7280';
            toggleButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        }
        if (icon) icon.textContent = '🔍';
        if (text) text.textContent = 'Enable Review Mode';
    }
}

// ==================== PREVIEW MODE - YAML EXPORT ====================
// Generate unified YAML format string from pending changes (waivers + skips)
function generateUnifiedYAML() {
    // Escape special characters in strings
    const escapeYAML = (str) => {
        if (!str) return '""';
        // Replace quotes and newlines
        str = String(str).replace(/\\\\/g, '\\\\\\\\').replace(/"/g, '\\\\"').replace(/\\n/g, ' ').replace(/\\r/g, '');
        return '"' + str + '"';
    };
    
    let yaml = '';
    
    // Separate waivers and skips
    const waivers = PENDING_CHANGES.filter(c => c.type === 'waive');
    const skips = PENDING_CHANGES.filter(c => c.type === 'skip');
    
    // Export waivers section
    yaml += 'pending_waivers:\\n';
    if (waivers.length > 0) {
        waivers.forEach(w => {
            yaml += '  - id: ' + w.id + '\\n';
            yaml += '    module: ' + w.moduleName + '\\n';
            yaml += '    item_id: ' + w.itemId + '\\n';
            yaml += '    item_description: ' + escapeYAML(w.itemDesc) + '\\n';
            yaml += '    failure_index: ' + w.failureIndex + '\\n';
            yaml += '    failure_detail: ' + escapeYAML(w.failureDetail) + '\\n';
            yaml += '    comment: ' + escapeYAML(w.comment) + '\\n';
            yaml += '    timestamp: ' + escapeYAML(w.timestamp) + '\\n';
        });
    } else {
        yaml += '  []\\n';
    }
    
    yaml += '\\n';
    
    // Export skips section
    yaml += 'pending_skips:\\n';
    if (skips.length > 0) {
        skips.forEach(s => {
            yaml += '  - id: ' + s.id + '\\n';
            yaml += '    module: ' + s.module + '\\n';
            if (s.item_id) {
                yaml += '    item_id: ' + s.item_id + '\\n';
            } else {
                yaml += '    item_id: null  # Skip entire module\\n';
            }
            yaml += '    reason: ' + escapeYAML(s.reason) + '\\n';
            yaml += '    timestamp: ' + escapeYAML(s.timestamp) + '\\n';
        });
    } else {
        yaml += '  []\\n';
    }
    
    return yaml;
}

// Save unified YAML to file
function saveUnifiedYAML(filename) {
    const yaml = generateUnifiedYAML();
    const blob = new Blob([yaml], { type: 'text/yaml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    console.log('[Preview] Unified YAML file downloaded:', filename);
}

// Platform-aware refresh cache function
function refreshCacheWithPlatformSupport() {
    console.log('[Refresh Cache] Starting platform-aware cache refresh...');
    
    // Detect platform
    const userAgent = navigator.userAgent.toLowerCase();
    const platform = navigator.platform.toLowerCase();
    const isWindows = platform.includes('win') || userAgent.includes('windows');
    
    console.log('[Refresh Cache] UserAgent:', userAgent);
    console.log('[Refresh Cache] Platform:', platform);
    console.log('[Refresh Cache] Detected Windows:', isWindows);
    
    if (isWindows) {
        // Windows-specific: Clear localStorage then simple reload
        console.log('[Refresh Cache] Using Windows branch: localStorage.clear() + location.reload()');
        localStorage.clear();
        console.log('[Refresh Cache] localStorage cleared');
        location.reload();
    } else {
        // Linux/Unix: Keep original behavior (just reload, no localStorage.clear)
        console.log('[Refresh Cache] Using Linux/Unix branch: location.reload() only');
        location.reload();
    }
}

// ==================== FILE PREVIEW AND DOWNLOAD ====================
// Note: RESULT_FILES is defined in the main script tag with file data from Python

// Download file from base64
function downloadFile(fileId) {
    console.log('[Download] Downloading file:', fileId);
    
    const fileData = RESULT_FILES[fileId];
    if (!fileData) {
        console.error('[Download] File data not found:', fileId);
        alert('Error: File data not found');
        return;
    }
    
    try {
        // Decode base64 to binary
        const binaryString = atob(fileData.base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Determine MIME type
        let mimeType = 'application/octet-stream';
        if (fileData.name.endsWith('.xlsx')) {
            mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        } else if (fileData.name.endsWith('.csv')) {
            mimeType = 'text/csv';
        } else if (fileData.name.endsWith('.yaml') || fileData.name.endsWith('.yml')) {
            mimeType = 'text/yaml';
        }
        
        // Create blob and download
        const blob = new Blob([bytes], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileData.name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('[Download] File downloaded successfully:', fileData.name);
    } catch (err) {
        console.error('[Download] Error downloading file:', err);
        alert('Error downloading file: ' + err.message);
    }
}

// Preview file content
function previewFile(fileId) {
    console.log('[Preview] Previewing file:', fileId);
    
    const fileData = RESULT_FILES[fileId];
    if (!fileData) {
        console.error('[Preview] File data not found:', fileId);
        alert('Error: File data not found');
        return;
    }
    
    if (!fileData.preview_available) {
        alert('Preview not available for this file (too large or unsupported format).\\nPlease download the file instead.');
        return;
    }
    
    try {
        // Decode base64 to binary
        const binaryString = atob(fileData.base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        let htmlContent = '';
        
        if (fileData.name.endsWith('.xlsx')) {
            // Parse Excel file with SheetJS
            const workbook = XLSX.read(bytes, { type: 'array' });
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            
            // Convert to HTML table
            const htmlTable = XLSX.utils.sheet_to_html(worksheet, { 
                header: '', 
                footer: ''
            });
            
            // Count rows for limit warning
            const range = XLSX.utils.decode_range(worksheet['!ref']);
            const rowCount = range.e.r - range.s.r + 1;
            const limitWarning = rowCount > 1000 ? 
                `<div style="background:#fef3c7; color:#92400e; padding:0.75rem; border-radius:6px; margin-bottom:1rem; border-left:4px solid #f59e0b;">
                    ⚠️ <strong>Large file:</strong> Showing first 1000 rows only. Total rows: ${rowCount}. Download for full content.
                </div>` : '';
            
            htmlContent = `
                <div style="margin-bottom:1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <h3 style="margin:0; color:#1e293b;">Sheet: ${firstSheetName}</h3>
                        <span style="color:#64748b; font-size:0.9rem;">${rowCount} rows × ${range.e.c - range.s.c + 1} columns</span>
                    </div>
                    ${limitWarning}
                </div>
                <div style="max-height:500px; overflow:auto; border:1px solid #e2e8f0; border-radius:6px;">
                    ${htmlTable}
                </div>
            `;
            
        } else if (fileData.name.endsWith('.csv')) {
            // Parse CSV file
            const text = new TextDecoder().decode(bytes);
            const lines = text.split('\\n').slice(0, 1001); // Limit to 1000 rows
            const limitWarning = text.split('\\n').length > 1001 ? 
                `<div style="background:#fef3c7; color:#92400e; padding:0.75rem; border-radius:6px; margin-bottom:1rem; border-left:4px solid #f59e0b;">
                    ⚠️ <strong>Large file:</strong> Showing first 1000 rows only. Download for full content.
                </div>` : '';
            
            let tableHtml = '<table class="preview-table"><thead><tr>';
            const headers = lines[0].split(',');
            headers.forEach(h => {
                tableHtml += `<th>${h.trim()}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';
            
            for (let i = 1; i < lines.length; i++) {
                if (lines[i].trim()) {
                    tableHtml += '<tr>';
                    const cells = lines[i].split(',');
                    cells.forEach(c => {
                        tableHtml += `<td>${c.trim()}</td>`;
                    });
                    tableHtml += '</tr>';
                }
            }
            tableHtml += '</tbody></table>';
            
            htmlContent = `
                ${limitWarning}
                <div style="max-height:500px; overflow:auto; border:1px solid #e2e8f0; border-radius:6px;">
                    ${tableHtml}
                </div>
            `;
        } else {
            alert('Preview not supported for this file type');
            return;
        }
        
        // Show preview modal
        showPreviewModal(fileData.name, htmlContent, fileId);
        
    } catch (err) {
        console.error('[Preview] Error previewing file:', err);
        alert('Error previewing file: ' + err.message);
    }
}

// Show preview modal
function showPreviewModal(filename, htmlContent, fileId) {
    const modal = document.getElementById('file-preview-modal');
    if (!modal) {
        console.error('[Preview] Modal element not found');
        return;
    }
    
    document.getElementById('preview-filename').textContent = filename;
    document.getElementById('preview-content').innerHTML = htmlContent;
    document.getElementById('preview-download-btn').onclick = () => downloadFile(fileId);
    
    modal.style.display = 'flex';
    
    // Close on escape key
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closePreviewModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

// Close preview modal
function closePreviewModal() {
    const modal = document.getElementById('file-preview-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Apply unified preview mode - Plan C: One-click script generation
function generatePreviewFiles() {
    if (PENDING_CHANGES.length === 0) {
        showMessageModal('Generate Preview Files', 'No pending changes to export.\\n\\nPlease add some waivers or skips first.');
        return;
    }
    
    // Generate timestamp for unique filenames (consistent format for run_preview.csh)
    const now = new Date();
    const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');  // YYYYMMDD format
    
    const waiverCount = PENDING_CHANGES.filter(c => c.type === 'waive').length;
    const skipCount = PENDING_CHANGES.filter(c => c.type === 'skip').length;
    
    // Consistent naming convention:
    // - pending_changes_preview_YYYYMMDD.yaml  (unified format)
    // - signoff_preview_YYYYMMDD.html
    // - generate_preview_YYYYMMDD.sh
    const yamlFilename = 'pending_changes_preview_' + dateStr + '.yaml';
    const htmlFilename = 'signoff_preview_' + dateStr + '.html';
    const scriptFilename = 'generate_preview_' + dateStr + '.sh';
    
    // Export unified changes to YAML file
    saveUnifiedYAML(yamlFilename);
    
    // Detect CHECKLIST root directory from current path
    const currentPath = window.location.pathname;
    let checklistRoot = '/home/wentao/AAI/AAI_CHECK_LIST/CHECKLIST';  // Default
    
    // Try to extract from path
    const match = currentPath.match(/(.+\\/CHECKLIST)\\/Work\\/Reports/);
    if (match) {
        checklistRoot = match[1];
    }
    
    // Generate one-click shell script (for csh users, generate csh syntax)
    const scriptContent = `#!/bin/csh -f
# Auto-generated unified preview script
# Generated: ${now.toISOString()}
# Changes: ${PENDING_CHANGES.length} total (${waiverCount} waivers, ${skipCount} skips)

echo "========================================="
echo "Preview Generation Script"
echo "========================================="
echo ""

# Change to CHECKLIST directory
cd ${checklistRoot}
if ( $? != 0 ) then
    echo "❌ Error: Failed to change to CHECKLIST directory"
    exit 1
endif

echo "✓ Changed to CHECKLIST directory"
echo ""

# Clean up old preview files to ensure fresh generation
echo "🧹 Cleaning up old preview files..."
if ( -f Work/tmp/pending_changes.yaml ) then
    rm -f Work/tmp/pending_changes.yaml
    echo "✓ Removed old pending_changes.yaml from tmp"
endif
if ( -f Work/Reports/${htmlFilename} ) then
    rm -f Work/Reports/${htmlFilename}
    echo "✓ Removed old ${htmlFilename}"
endif
echo ""

# Check if YAML file exists (support both Downloads and Work/tmp)
set yaml_source = ""
if ( -f ~/Downloads/${yamlFilename} ) then
    set yaml_source = ~/Downloads/${yamlFilename}
else if ( -f Work/tmp/${yamlFilename} ) then
    set yaml_source = Work/tmp/${yamlFilename}
endif

if ( "$yaml_source" == "" ) then
    echo "❌ Error: YAML file not found"
    echo "   Checked locations:"
    echo "     • ~/Downloads/${yamlFilename}"
    echo "     • Work/tmp/${yamlFilename}"
    exit 1
endif

echo "✓ Found YAML file: $yaml_source"
echo ""

# Create Work/tmp directory if not exists
if ( ! -d Work/tmp ) then
    mkdir -p Work/tmp
    echo "✓ Created Work/tmp directory"
endif

# Copy YAML to Work/tmp (force overwrite) - keep preview files in tmp, not Results
set yaml_dest = Work/tmp/pending_changes.yaml
\\cp -f "$yaml_source" "$yaml_dest"
if ( $? != 0 ) then
    echo "❌ Error: Failed to copy YAML file"
    exit 1
endif

echo "✓ YAML saved to: $yaml_dest"
echo ""

# Generate preview HTML
echo "⏳ Generating preview HTML with unified changes..."
python3 Check_modules/common/visualize_signoff.py \\
    --root . \\
    --work-dir Work \\
    --preview-changes "$yaml_dest" \\
    --output ${htmlFilename}

if ( $? != 0 ) then
    echo "❌ Error: Failed to generate preview HTML"
    exit 1
endif

echo ""
echo "✅ Preview HTML generated successfully!"
echo "   Location: ${checklistRoot}/Work/Reports/${htmlFilename}"
echo ""

# Open in Firefox (use absolute path)
set html_path = "${checklistRoot}/Work/Reports/${htmlFilename}"
if ( -f "$html_path" ) then
    echo "🌐 Opening preview in Firefox..."
    /grid/common/pkgs/firefox/latest/firefox "$html_path" &
    echo "✓ Firefox launched"
else
    echo "⚠️  Warning: HTML file not found at $html_path"
endif

echo ""
echo "========================================="
echo "Preview generation completed!"
echo "========================================="
`;
    
    // Download shell script
    const scriptBlob = new Blob([scriptContent], { type: 'text/x-sh' });
    const scriptUrl = URL.createObjectURL(scriptBlob);
    const scriptLink = document.createElement('a');
    scriptLink.href = scriptUrl;
    scriptLink.download = scriptFilename;
    document.body.appendChild(scriptLink);
    scriptLink.click();
    document.body.removeChild(scriptLink);
    URL.revokeObjectURL(scriptUrl);
    
    console.log('[Preview] Script file downloaded:', scriptFilename);
    
    // Show simplified instructions
    const instructions = `✅ Files Downloaded to ~/Downloads/

📦 Files: ${yamlFilename} + ${scriptFilename}

⚠️  Note: Multiple previews today? New files replace old ones automatically.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
� RECOMMENDED: One-Click Method
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    cd /path/to/CHECKLIST/Work
    ./run_preview.csh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️  Alternative: Manual Method
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    cd ~/Downloads
    chmod +x ${scriptFilename}
    ./${scriptFilename}`;
    
    showMessageModal('Generate Preview', instructions);
    
    // Also copy the execution commands to clipboard for convenience
    const clipboardText = `# Method 1 (Recommended):
cd /path/to/CHECKLIST
./Work/run_preview.csh

# Method 2 (Manual):
cd ~/Downloads
chmod +x ${scriptFilename}
./${scriptFilename}`;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(clipboardText).then(() => {
            console.log('[Preview] Execution commands copied to clipboard');
        }).catch(err => {
            console.error('[Preview] Failed to copy to clipboard:', err);
        });
    }
}

// ==================== GENERIC MESSAGE MODAL ====================
/**
 * Show a generic message modal with customizable title, message, and buttons
 * @param {string} title - Modal title
 * @param {string} message - Modal message content (supports line breaks with \n)
 * @param {Array} buttons - Optional array of button objects: [{text: 'OK', action: function, isPrimary: true}]
 *                         If not provided, defaults to single OK button
 */
function showMessageModal(title, message, buttons) {
    const overlay = document.getElementById('message-modal-overlay');
    const titleEl = document.getElementById('message-modal-title');
    const contentEl = document.getElementById('message-modal-content');
    const footerEl = overlay.querySelector('.waiver-modal-footer');
    
    // Set title and content
    titleEl.textContent = title || 'Message';
    contentEl.textContent = message || '';
    
    // Clear existing buttons
    footerEl.innerHTML = '';
    
    // Create buttons
    if (!buttons || buttons.length === 0) {
        // Default OK button
        const okBtn = document.createElement('button');
        okBtn.className = 'waiver-modal-btn waiver-confirm-btn';
        okBtn.textContent = 'OK';
        okBtn.onclick = closeMessageModal;
        footerEl.appendChild(okBtn);
    } else {
        // Custom buttons
        buttons.forEach(btnConfig => {
            const btn = document.createElement('button');
            btn.className = btnConfig.isPrimary !== false ? 
                'waiver-modal-btn waiver-confirm-btn' : 
                'waiver-modal-btn waiver-cancel-btn';
            btn.textContent = btnConfig.text || 'OK';
            btn.onclick = (e) => {
                console.log('[Modal] Button clicked:', btnConfig.text);
                console.log('[Modal] Event:', e);
                console.log('[Modal] Has action:', !!btnConfig.action);
                
                e.stopPropagation();  // Prevent event bubbling
                e.preventDefault();   // Prevent default button behavior
                
                // Execute action first if defined
                if (btnConfig.action) {
                    console.log('[Modal] Executing action...');
                    try {
                        btnConfig.action();
                        console.log('[Modal] Action executed successfully');
                    } catch (err) {
                        console.error('[Modal] Action execution failed:', err);
                        closeMessageModal();
                    }
                    // Note: If action has location.reload(), modal will close automatically
                    // when page refreshes
                } else {
                    // Only close modal if no action (for Cancel button)
                    console.log('[Modal] No action, closing modal');
                    closeMessageModal();
                }
            };
            footerEl.appendChild(btn);
        });
    }
    
    // Show modal
    overlay.style.display = 'flex';
    
    // Add ESC key handler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeMessageModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

function closeMessageModal() {
    const overlay = document.getElementById('message-modal-overlay');
    overlay.style.display = 'none';
}

// Close message modal when clicking on overlay
document.addEventListener('DOMContentLoaded', () => {
    const messageOverlay = document.getElementById('message-modal-overlay');
    if (messageOverlay) {
        messageOverlay.addEventListener('click', (e) => {
            if (e.target === messageOverlay) {
                closeMessageModal();
            }
        });
    }
});

// ==================== MODAL WAIVER UI ====================
// Current waiver context for modal
let CURRENT_WAIVER_CONTEXT = null;

// Open waiver modal from button click
function openWaiverModalFromButton(button) {
    const moduleName = button.dataset.module || '';
    const itemId = button.dataset.item || '';
    const itemDesc = button.dataset.desc || '';
    const failureIndex = parseInt(button.dataset.index) || 0;
    const failureDetail = button.dataset.failure || '';
    
    openWaiverModal(moduleName, itemId, itemDesc, failureIndex, failureDetail, button);
}

// Open waiver modal with provided data
function openWaiverModal(moduleName, itemId, itemDesc, failureIndex, failureDetail, sourceButton) {
    // Store context for later use
    CURRENT_WAIVER_CONTEXT = {
        moduleName: moduleName,
        itemId: itemId,
        itemDesc: itemDesc,
        failureIndex: failureIndex,
        failureDetail: failureDetail,
        sourceButton: sourceButton || null
    };
    
    // Populate modal fields
    document.getElementById('waiver-module-name').textContent = moduleName;
    document.getElementById('waiver-item-id').textContent = itemId;
    document.getElementById('waiver-item-desc').textContent = itemDesc;
    
    // Show or hide failure detail section based on failureIndex
    const failureSection = document.getElementById('waiver-failure-section');
    if (failureIndex === -1) {
        // "Waive All" mode - hide individual failure detail
        failureSection.style.display = 'none';
    } else {
        // Individual failure mode - show failure detail
        failureSection.style.display = 'block';
        document.getElementById('waiver-failure-detail').textContent = failureDetail;
    }
    
    // Clear comment input
    document.getElementById('waiver-comment-input').value = '';
    
    // Show modal
    document.getElementById('waiver-modal-overlay').classList.add('active');
    
    // Focus on comment input
    setTimeout(() => {
        document.getElementById('waiver-comment-input').focus();
    }, 100);
}

// Close waiver modal
function closeWaiverModal() {
    document.getElementById('waiver-modal-overlay').classList.remove('active');
    CURRENT_WAIVER_CONTEXT = null;
}

// Confirm waiver from modal
function confirmWaiver() {
    if (!CURRENT_WAIVER_CONTEXT) {
        console.error('No waiver context available');
        return;
    }
    
    const comment = document.getElementById('waiver-comment-input').value.trim();
    
    if (CURRENT_WAIVER_CONTEXT.failureIndex === -1) {
        // "Waive All" mode
        waiveAllFailuresFromModal(comment);
    } else {
        // Single failure mode
        waiveSingleFailureFromModal(comment);
    }
}

// Waive single failure from modal
function waiveSingleFailureFromModal(comment) {
    const ctx = CURRENT_WAIVER_CONTEXT;
    
    // Check if already waived
    const existing = PENDING_CHANGES.find(w => 
        w.moduleName === ctx.moduleName && 
        w.itemId === ctx.itemId && 
        w.failureIndex === ctx.failureIndex
    );
    
    if (existing) {
        showMessageModal('Add Waiver', 'This failure is already waived.');
        closeWaiverModal();
        return;
    }
    
    // Create waiver object
    const waiver = {
        type: 'waive',
        id: 'waiver_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
        moduleName: ctx.moduleName,
        itemId: ctx.itemId,
        itemDesc: ctx.itemDesc,
        failureIndex: ctx.failureIndex,
        failureDetail: ctx.failureDetail,
        comment: comment || '(No comment provided)',
        timestamp: new Date().toISOString()
    };
    
    // Add to pending changes
    PENDING_CHANGES.push(waiver);
    saveChanges();
    
    // Update button if available
    if (ctx.sourceButton) {
        ctx.sourceButton.textContent = 'Waived ✓';
        ctx.sourceButton.style.background = '#10b981';
        ctx.sourceButton.style.borderColor = '#10b981';
        ctx.sourceButton.style.color = 'white';
        // Change onclick to unwaive function
        ctx.sourceButton.onclick = function(e) {
            e.stopPropagation();
            openUnwaiverModal(ctx.moduleName, ctx.itemId, ctx.failureIndex, waiver, this);
        };
    }
    
    // Update control bar
    updatePendingWaiversBar();
    
    // Update "Waive All" button if needed
    updateWaiveAllButton(ctx.moduleName, ctx.itemId);
    
    // Close modal
    closeWaiverModal();
}

// Waive all failures from modal
function waiveAllFailuresFromModal(comment) {
    const ctx = CURRENT_WAIVER_CONTEXT;
    
    // Find all failure buttons for this item
    const itemFailures = [];
    document.querySelectorAll('.waive-button').forEach(btn => {
        const btnModule = btn.dataset.module;
        const btnItemId = btn.dataset.item;
        if (btnModule === ctx.moduleName && btnItemId === ctx.itemId) {
            itemFailures.push({
                button: btn,
                index: parseInt(btn.dataset.index) || 0,
                detail: btn.dataset.failure || ''
            });
        }
    });
    
    // Waive each failure
    let waivedCount = 0;
    itemFailures.forEach(({ button: btn, index, detail }) => {
        // Check if already waived
        const existing = PENDING_CHANGES.find(w => 
            w.moduleName === ctx.moduleName && 
            w.itemId === ctx.itemId && 
            w.failureIndex === index
        );
        
        if (!existing) {
            const waiver = {
                type: 'waive',
                id: 'waiver_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                moduleName: ctx.moduleName,
                itemId: ctx.itemId,
                itemDesc: ctx.itemDesc,
                failureIndex: index,
                failureDetail: detail,
                comment: comment || '(No comment provided)',
                timestamp: new Date().toISOString()
            };
            
            PENDING_CHANGES.push(waiver);
            
            // Update button - make it clickable for unwaive
            btn.textContent = 'Waived ✓';
            btn.style.background = '#10b981';
            btn.style.borderColor = '#10b981';
            btn.style.color = 'white';
            btn.onclick = function(e) {
                e.stopPropagation();
                openUnwaiverModal(ctx.moduleName, ctx.itemId, index, waiver, this);
            };
            
            waivedCount++;
        }
    });
    
    if (waivedCount > 0) {
        saveChanges();
        updatePendingWaiversBar();
        
        // Update the "Waive All" button if available
        if (ctx.sourceButton) {
            ctx.sourceButton.textContent = 'All Waived ✓';
            ctx.sourceButton.style.background = '#10b981';
            ctx.sourceButton.style.borderColor = '#10b981';
            ctx.sourceButton.style.color = 'white';
            ctx.sourceButton.onclick = function(e) {
                e.stopPropagation();
                openUnwaiverAllModal(ctx.moduleName, ctx.itemId, this);
            };
        }
    }
    
    // Close modal
    closeWaiverModal();
}

// ==================== UNWAIVE (CANCEL WAIVER) FUNCTIONS ====================
// Current unwaiver context
let CURRENT_UNWAIVER_CONTEXT = null;

// Open unwaiver confirmation modal for single failure
function openUnwaiverModal(moduleName, itemId, failureIndex, waiver, sourceButton) {
    // Store context
    CURRENT_UNWAIVER_CONTEXT = {
        moduleName: moduleName,
        itemId: itemId,
        itemDesc: waiver.itemDesc || '',
        failureIndex: failureIndex,
        failureDetail: waiver.failureDetail || '',
        comment: waiver.comment || '(No comment provided)',
        sourceButton: sourceButton,
        isMultiple: false
    };
    
    // Populate modal fields
    document.getElementById('unwaiver-module-name').textContent = moduleName;
    document.getElementById('unwaiver-item-id').textContent = itemId;
    document.getElementById('unwaiver-item-desc').textContent = waiver.itemDesc || '';
    document.getElementById('unwaiver-current-comment').textContent = waiver.comment || '(No comment provided)';
    
    // Show or hide failure detail section
    const failureSection = document.getElementById('unwaiver-failure-section');
    if (failureIndex === -1) {
        failureSection.style.display = 'none';
    } else {
        failureSection.style.display = 'block';
        document.getElementById('unwaiver-failure-detail').textContent = waiver.failureDetail || '';
    }
    
    // Show modal
    document.getElementById('unwaiver-modal-overlay').classList.add('active');
}

// Open unwaiver confirmation modal for all failures
function openUnwaiverAllModal(moduleName, itemId, sourceButton) {
    // Find all waived failures for this item
    const waivedFailures = PENDING_CHANGES.filter(w => 
        w.moduleName === moduleName && w.itemId === itemId
    );
    
    if (waivedFailures.length === 0) {
        showMessageModal('Remove Waiver', 'No waivers found for this item.');
        return;
    }
    
    // Get first waiver for item info
    const firstWaiver = waivedFailures[0];
    
    // Store context
    CURRENT_UNWAIVER_CONTEXT = {
        moduleName: moduleName,
        itemId: itemId,
        itemDesc: firstWaiver.itemDesc || '',
        failureIndex: -1, // -1 indicates all failures
        failureDetail: `All ${waivedFailures.length} failure(s)`,
        comment: `${waivedFailures.length} waiver(s) will be removed`,
        sourceButton: sourceButton,
        isMultiple: true,
        waiverCount: waivedFailures.length
    };
    
    // Populate modal fields
    document.getElementById('unwaiver-module-name').textContent = moduleName;
    document.getElementById('unwaiver-item-id').textContent = itemId;
    document.getElementById('unwaiver-item-desc').textContent = firstWaiver.itemDesc || '';
    document.getElementById('unwaiver-current-comment').textContent = `${waivedFailures.length} waiver(s) will be removed`;
    
    // Hide failure detail section for "all"
    document.getElementById('unwaiver-failure-section').style.display = 'none';
    
    // Show modal
    document.getElementById('unwaiver-modal-overlay').classList.add('active');
}

// Update "Waive All" button state after single waive/unwaive
function updateWaiveAllButton(moduleName, itemId) {
    document.querySelectorAll('.waive-all-button').forEach(btn => {
        if (btn.dataset.module === moduleName && btn.dataset.item === itemId) {
            // Find all failures for this item
            const itemFailures = Array.from(document.querySelectorAll('.waive-button')).filter(b => {
                return b.dataset.module === moduleName && b.dataset.item === itemId;
            });
            
            // Check if all failures are waived
            const waivedFailures = itemFailures.filter(b => b.textContent.includes('Waived'));
            const allWaived = waivedFailures.length === itemFailures.length && itemFailures.length > 0;
            
            if (allWaived) {
                // All waived - show "All Waived ✓" button
                btn.textContent = 'All Waived ✓';
                btn.style.background = '#10b981';
                btn.style.borderColor = '#10b981';
                btn.style.color = 'white';
                btn.onclick = function(e) {
                    e.stopPropagation();
                    openUnwaiverAllModal(moduleName, itemId, this);
                };
            } else {
                // Not all waived - show "Waive All" button
                btn.textContent = 'Waive All';
                btn.style.background = 'white';
                btn.style.borderColor = '#3b82f6';
                btn.style.color = '#3b82f6';
                btn.onclick = function(e) {
                    e.stopPropagation();
                    openWaiverModalFromButton(this);
                };
            }
        }
    });
}

// Close unwaiver modal
function closeUnwaiverModal() {
    document.getElementById('unwaiver-modal-overlay').classList.remove('active');
    CURRENT_UNWAIVER_CONTEXT = null;
}

// ==================== SKIP SYSTEM ====================
// Skip context
let CURRENT_SKIP_CONTEXT = null;
let CURRENT_UNSKIP_CONTEXT = null;

// Open skip modal from button click
function openSkipModalFromButton(button) {
    const moduleName = button.getAttribute('data-module');
    const itemId = button.getAttribute('data-item');
    openSkipModal(moduleName, itemId, button);
}

// Open skip modal
function openSkipModal(moduleName, itemId, sourceButton = null) {
    // Check if already skipped - if so, open unskip modal instead
    const existingSkip = PENDING_CHANGES.find(c => 
        c.action === 'skip' && 
        c.module === moduleName && 
        c.item_id === itemId
    );
    
    if (existingSkip) {
        openUnskipModal(moduleName, itemId, existingSkip.reason, sourceButton);
        return;
    }
    
    // Store context
    CURRENT_SKIP_CONTEXT = {
        module: moduleName,
        item_id: itemId,
        isModule: itemId === null,
        sourceButton: sourceButton
    };
    
    // Populate modal fields
    document.getElementById('skip-module-name').textContent = moduleName;
    
    // Show/hide item ID field
    const itemInfo = document.getElementById('skip-item-info');
    if (itemId) {
        document.getElementById('skip-item-id').textContent = itemId;
        itemInfo.style.display = 'flex';
    } else {
        itemInfo.style.display = 'none';
    }
    
    // Clear reason input
    document.getElementById('skip-reason-input').value = '';
    
    // Show modal
    document.getElementById('skip-modal-overlay').classList.add('active');
}

// Close skip modal
function closeSkipModal() {
    document.getElementById('skip-modal-overlay').classList.remove('active');
    CURRENT_SKIP_CONTEXT = null;
}

// Confirm skip action
function confirmSkip() {
    if (!CURRENT_SKIP_CONTEXT) {
        console.error('No skip context available');
        return;
    }
    
    const reason = document.getElementById('skip-reason-input').value.trim();
    
    // Reason is optional - no validation required
    
    // Check if already skipped
    const existing = PENDING_CHANGES.find(c => 
        c.type === 'skip' &&
        c.module === CURRENT_SKIP_CONTEXT.module &&
        c.item_id === CURRENT_SKIP_CONTEXT.item_id
    );
    
    if (existing) {
        showMessageModal('Already Skipped', 'This module/item is already in the skip list.');
        return;
    }
    
    // Create skip object (use moduleName/itemId to match applySkipsToModules expectations)
    const skip = {
        type: 'skip',
        id: 'skip_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
        moduleName: CURRENT_SKIP_CONTEXT.module,  // Changed from 'module' to 'moduleName'
        itemId: CURRENT_SKIP_CONTEXT.item_id,     // Changed from 'item_id' to 'itemId'
        reason: reason || '(No reason provided)',  // Use default if empty
        timestamp: new Date().toISOString(),
        isModule: CURRENT_SKIP_CONTEXT.isModule
    };
    
    // Add to pending changes
    PENDING_CHANGES.push(skip);
    saveChanges();
    
    // Update the button if we have a reference
    if (CURRENT_SKIP_CONTEXT.sourceButton) {
        const btn = CURRENT_SKIP_CONTEXT.sourceButton;
        btn.textContent = 'Skipped ✓';
        btn.style.background = '#10b981';
        btn.style.color = 'white';
        btn.classList.remove('skip-btn');
        btn.classList.add('skipped-btn');
        
        // Update onclick to open unskip modal
        const moduleName = CURRENT_SKIP_CONTEXT.module;
        const itemId = CURRENT_SKIP_CONTEXT.item_id;
        btn.onclick = (e) => {
            e.stopPropagation();
            openUnskipModal(moduleName, itemId, reason, btn);
        };
    }
    
    // Update control bar
    updatePendingChangesBar();
    
    // Close modal
    closeSkipModal();
    
    console.log('[Skip] Added:', skip);
}

// Open unskip modal
function openUnskipModal(moduleName, itemId, currentReason, sourceButton = null) {
    // Store context
    CURRENT_UNSKIP_CONTEXT = {
        module: moduleName,
        item_id: itemId,
        reason: currentReason,
        sourceButton: sourceButton
    };
    
    // Populate modal
    document.getElementById('unskip-module-name').textContent = moduleName;
    
    if (itemId) {
        document.getElementById('unskip-item-id').textContent = itemId;
        document.getElementById('unskip-item-info').style.display = 'flex';
    } else {
        document.getElementById('unskip-item-info').style.display = 'none';
    }
    
    document.getElementById('unskip-current-reason').textContent = currentReason || '(No reason provided)';
    
    // Show modal
    document.getElementById('unskip-modal-overlay').classList.add('active');
}

// Confirm unskip action
function confirmUnskip() {
    if (!CURRENT_UNSKIP_CONTEXT) {
        console.error('No unskip context available');
        return;
    }
    
    const ctx = CURRENT_UNSKIP_CONTEXT;
    
    // Remove the skip from pending changes
    PENDING_CHANGES = PENDING_CHANGES.filter(c => 
        !(c.action === 'skip' && 
          c.module === ctx.module && 
          c.item_id === ctx.item_id)
    );
    saveChanges();
    
    // Update the button if we have a reference
    if (ctx.sourceButton) {
        const btn = ctx.sourceButton;
        btn.textContent = 'Skip';
        btn.style.background = '#f97316';
        btn.style.color = 'white';
        btn.classList.remove('skipped-btn');
        btn.classList.add('skip-btn');
        
        // Restore original onclick
        btn.onclick = (e) => {
            e.stopPropagation();
            openSkipModalFromButton(btn);
        };
    }
    
    // Update control bar
    updatePendingChangesBar();
    
    // Close modal
    closeUnskipModal();
    
    console.log('[Unskip] Removed skip for:', ctx.module, ctx.item_id);
}

// Close unskip modal
function closeUnskipModal() {
    document.getElementById('unskip-modal-overlay').classList.remove('active');
    CURRENT_UNSKIP_CONTEXT = null;
}

// Confirm unwaiver action
function confirmUnwaiver() {
    if (!CURRENT_UNWAIVER_CONTEXT) {
        console.error('No unwaiver context available');
        return;
    }
    
    const ctx = CURRENT_UNWAIVER_CONTEXT;
    
    if (ctx.isMultiple) {
        // Remove all waivers for this item
        PENDING_CHANGES = PENDING_CHANGES.filter(w => 
            !(w.moduleName === ctx.moduleName && w.itemId === ctx.itemId)
        );
        saveChanges();
        
        // Restore all waive buttons for this item
        document.querySelectorAll('.waive-button').forEach(btn => {
            if (btn.dataset.module === ctx.moduleName && btn.dataset.item === ctx.itemId) {
                btn.textContent = 'Waive';
                btn.style.background = 'white';
                btn.style.borderColor = '#3b82f6';
                btn.style.color = '#3b82f6';
                btn.onclick = function(e) {
                    e.stopPropagation();
                    openWaiverModalFromButton(this);
                };
            }
        });
        
        // Restore "Waive All" button
        if (ctx.sourceButton) {
            ctx.sourceButton.textContent = 'Waive All';
            ctx.sourceButton.style.background = 'white';
            ctx.sourceButton.style.borderColor = '#3b82f6';
            ctx.sourceButton.style.color = '#3b82f6';
            ctx.sourceButton.onclick = function(e) {
                e.stopPropagation();
                openWaiverModalFromButton(this);
            };
        }
    } else {
        // Remove single waiver
        const index = PENDING_CHANGES.findIndex(w => 
            w.moduleName === ctx.moduleName && 
            w.itemId === ctx.itemId && 
            w.failureIndex === ctx.failureIndex
        );
        
        if (index !== -1) {
            PENDING_CHANGES.splice(index, 1);
            saveChanges();
            
            // Restore button to original state
            if (ctx.sourceButton) {
                ctx.sourceButton.textContent = 'Waive';
                ctx.sourceButton.style.background = 'white';
                ctx.sourceButton.style.borderColor = '#3b82f6';
                ctx.sourceButton.style.color = '#3b82f6';
                ctx.sourceButton.onclick = function(e) {
                    e.stopPropagation();
                    openWaiverModalFromButton(this);
                };
            }
            
            // Update "Waive All" button if needed
            updateWaiveAllButton(ctx.moduleName, ctx.itemId);
        }
    }
    
    // Update control bar
    updatePendingWaiversBar();
    
    // Close modal
    closeUnwaiverModal();
}

// Close modal on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (CURRENT_WAIVER_CONTEXT) {
            closeWaiverModal();
        }
        if (CURRENT_UNWAIVER_CONTEXT) {
            closeUnwaiverModal();
        }
    }
});

// Close modal on overlay click (click outside modal)
document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'waiver-modal-overlay') {
        closeWaiverModal();
    }
    if (e.target && e.target.id === 'unwaiver-modal-overlay') {
        closeUnwaiverModal();
    }
});

// ==================== OLD WAIVER FUNCTIONS (Kept for compatibility) ====================
// Waive a single failure
function waiveFailure(button) {
    const data = JSON.parse(button.getAttribute('data-waiver'));
    const comment = prompt('Enter waiver comment (optional):', '');
    
    if (comment === null) return; // User cancelled
    
    // Create waiver object (comment is now optional)
    const waiver = {
        type: 'waive',
        id: 'waiver_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
        moduleName: data.module,
        itemId: data.itemId,
        itemDesc: data.itemDesc,
        failureIndex: data.failureIdx,
        failureDetail: data.failureText,
        comment: comment ? comment.trim() : '(No comment provided)',
        timestamp: new Date().toISOString()
    };
    
    // Check if already waived
    const existing = PENDING_CHANGES.find(w => 
        w.moduleName === waiver.moduleName && 
        w.itemId === waiver.itemId && 
        w.failureIndex === waiver.failureIndex
    );
    
    if (existing) {
        showMessageModal('Add Waiver', 'This failure is already waived.');
        return;
    }
    
    // Add to pending waivers
    PENDING_CHANGES.push(waiver);
    saveChanges();
    
    // Update button
    button.textContent = 'Waived ✓';
    button.disabled = true;
    button.style.background = '#10b981';
    
    // Update control bar
    updatePendingWaiversBar();
}

// Waive all failures for an item
function waiveAllFailures(button) {
    const data = JSON.parse(button.getAttribute('data-waiver'));
    
    if (!confirm('Are you sure you want to waive all ' + data.failureText + ' for item ' + data.itemId + '?')) {
        return;
    }
    
    const comment = prompt('Enter waiver comment for all failures (optional):', '');
    
    if (comment === null) return; // User cancelled
    
    // Find all failure buttons for this item
    const itemFailures = [];
    document.querySelectorAll('.waive-button').forEach(btn => {
        const btnData = JSON.parse(btn.getAttribute('data-waiver'));
        if (btnData.module === data.module && btnData.itemId === data.itemId) {
            itemFailures.push({ button: btn, data: btnData });
        }
    });
    
    // Waive each failure
    let waivedCount = 0;
    itemFailures.forEach(({ button: btn, data: btnData }) => {
        // Check if already waived
        const existing = PENDING_CHANGES.find(w => 
            w.moduleName === btnData.module && 
            w.itemId === btnData.itemId && 
            w.failureIndex === btnData.failureIdx
        );
        
        if (!existing) {
            const waiver = {
                type: 'waive',
                id: 'waiver_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                moduleName: btnData.module,
                itemId: btnData.itemId,
                itemDesc: btnData.itemDesc,
                failureIndex: btnData.failureIdx,
                failureDetail: btnData.failureText,
                comment: comment ? comment.trim() : '(No comment provided)',
                timestamp: new Date().toISOString()
            };
            
            PENDING_CHANGES.push(waiver);
            
            // Update button
            btn.textContent = 'Waived ✓';
            btn.disabled = true;
            btn.style.background = '#10b981';
            
            waivedCount++;
        }
    });
    
    if (waivedCount > 0) {
        saveChanges();
        updatePendingWaiversBar();
        
        // Update the "Waive All" button
        button.textContent = 'All Waived ✓';
        button.disabled = true;
        button.style.background = '#10b981';
    }
}

// Initialize waivers on page load
function initWaivers() {
    console.log('[initWaivers] Starting initialization...');
    loadChanges();
    console.log('[initWaivers] Loaded waivers:', PENDING_CHANGES.length);
    
    // Update UI for already waived items
    const waiverButtons = document.querySelectorAll('.waive-button');
    console.log('[initWaivers] Found', waiverButtons.length, 'waiver buttons');
    
    waiverButtons.forEach(btn => {
        // Check if button uses new modal system (has data-module attribute)
        const hasDataAttributes = btn.hasAttribute('data-module');
        
        if (hasDataAttributes) {
            // New modal system
            const moduleName = btn.dataset.module || '';
            const itemId = btn.dataset.item || '';
            const failureIndex = parseInt(btn.dataset.index) || 0;
            
            const existing = PENDING_CHANGES.find(w => 
                w.moduleName === moduleName && 
                w.itemId === itemId && 
                w.failureIndex === failureIndex
            );
            
            if (existing) {
                btn.textContent = 'Waived ✓';
                btn.style.background = '#10b981';
                btn.style.borderColor = '#10b981';
                btn.style.color = 'white';
                // Change onclick to unwaive function
                btn.onclick = function(e) {
                    e.stopPropagation();
                    openUnwaiverModal(moduleName, itemId, failureIndex, existing, this);
                };
            }
        } else {
            // Old system (fallback)
            const data = JSON.parse(btn.getAttribute('data-waiver'));
            const existing = PENDING_CHANGES.find(w => 
                w.moduleName === data.module && 
                w.itemId === data.itemId && 
                w.failureIndex === data.failureIdx
            );
            
            if (existing) {
                btn.textContent = 'Waived ✓';
                btn.disabled = true;
                btn.style.background = '#10b981';
            }
        }
    });
    
    // Update "Waive All" buttons based on waived failures
    document.querySelectorAll('.waive-all-btn').forEach(btn => {
        // Check if button uses new modal system
        const hasDataAttributes = btn.hasAttribute('data-module');
        
        if (hasDataAttributes) {
            // New modal system
            const moduleName = btn.dataset.module || '';
            const itemId = btn.dataset.item || '';
            
            // Find all failures for this item
            const itemFailures = Array.from(document.querySelectorAll('.waive-button')).filter(b => {
                return b.dataset.module === moduleName && b.dataset.item === itemId;
            });
            
            // Check if all failures are waived
            const waivedFailures = itemFailures.filter(b => b.textContent.includes('Waived'));
            const allWaived = waivedFailures.length === itemFailures.length && itemFailures.length > 0;
            
            if (allWaived) {
                btn.textContent = 'All Waived ✓';
                btn.style.background = '#10b981';
                btn.style.borderColor = '#10b981';
                btn.style.color = 'white';
                // Change onclick to unwaive all
                btn.onclick = function(e) {
                    e.stopPropagation();
                    openUnwaiverAllModal(moduleName, itemId, this);
                };
            }
        } else {
            // Old system (fallback)
            const data = JSON.parse(btn.getAttribute('data-waiver'));
            
            const itemFailures = Array.from(document.querySelectorAll('.waive-button')).filter(b => {
                const btnData = JSON.parse(b.getAttribute('data-waiver'));
                return btnData.module === data.module && btnData.itemId === data.itemId;
            });
            
            const allWaived = itemFailures.every(b => b.disabled);
            
            if (allWaived && itemFailures.length > 0) {
                btn.textContent = 'All Waived ✓';
                btn.disabled = true;
                btn.style.background = '#10b981';
            }
        }
    });
    
    // Update control bar
    updatePendingWaiversBar();
}

// Update unified pending changes control bar
function updatePendingChangesBar() {
    const bar = document.getElementById('pending-changes-bar');
    const countEl = document.getElementById('pending-count');
    const labelEl = document.getElementById('pending-label');
    
    // Null check - elements might not be rendered yet
    if (!bar || !countEl || !labelEl) {
        console.warn('[updatePendingChangesBar] Control bar elements not found, skipping update');
        return;
    }
    
    if (PENDING_CHANGES.length > 0) {
        // Show the control bar
        bar.style.display = 'flex';
        
        // Count waivers and skips
        const waiverCount = PENDING_CHANGES.filter(c => c.type === 'waive').length;
        const skipCount = PENDING_CHANGES.filter(c => c.type === 'skip').length;
        
        // Update count and label
        countEl.textContent = PENDING_CHANGES.length;
        labelEl.textContent = waiverCount + ' Waivers, ' + skipCount + ' Skips';
        
        // Add cache info to title for debugging
        const oldestChange = PENDING_CHANGES.reduce((oldest, c) => {
            return (!oldest || new Date(c.timestamp) < new Date(oldest.timestamp)) ? c : oldest;
        }, null);
        
        if (oldestChange && oldestChange.timestamp) {
            const age = Math.floor((new Date() - new Date(oldestChange.timestamp)) / (1000 * 60 * 60 * 24));
            countEl.title = 'Oldest change: ' + age + ' day(s) ago\\nCache expires after ' + CACHE_EXPIRY_DAYS + ' days';
        }
    } else {
        // Hide the control bar when no changes
        bar.style.display = 'none';
    }
}

// Backward compatibility alias
function updatePendingWaiversBar() {
    updatePendingChangesBar();
}

// ==================== GENERATE PREVIEW HTML (PLAN B) ====================

// Generate pending waivers YAML content
function generateWaiversYAML() {
    let yaml = 'pending_waivers:\\n';
    PENDING_CHANGES.forEach(w => {
        // Clean up strings for YAML (remove newlines, escape quotes)
        const cleanStr = (str) => {
            return str.replace(/\\n/g, ' ').replace(/\\r/g, ' ').replace(/"/g, '\\\\"');
        };
        
        yaml += '  - id: ' + w.id + '\\n';
        yaml += '    module: ' + w.moduleName + '\\n';
        yaml += '    item_id: ' + w.itemId + '\\n';
        yaml += '    item_description: "' + cleanStr(w.itemDesc) + '"\\n';
        yaml += '    failure_index: ' + w.failureIndex + '\\n';
        yaml += '    failure_detail: "' + cleanStr(w.failureDetail) + '"\\n';
        yaml += '    comment: "' + cleanStr(w.comment) + '"\\n';
        yaml += '    timestamp: "' + w.timestamp + '"\\n';
    });
    return yaml;
}

// Generate preview HTML with instructions
function generatePreviewHTML() {
    if (PENDING_CHANGES.length === 0) {
        showMessageModal('Generate Preview', 'No pending changes to preview.\\n\\nPlease add waivers or skips first by clicking the "Waive" or "Skip" buttons in the Details tab.');
        return;
    }
    
    // Generate timestamp for unique filenames (only date, no time)
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
    
    // File name changed from pending_waivers to pending_changes (supports waiver + skip)
    const yamlFilename = 'pending_changes_preview_' + dateStr + '.yaml';
    const htmlFilename = 'signoff_preview_' + dateStr + '.html';
    
    // Save unified YAML file (contains both waivers and skips)
    const yaml = generateUnifiedYAML();
    const blob = new Blob([yaml], { type: 'text/yaml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = yamlFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Construct the command using --preview-changes (unified format)
    const command = 'python3 Check_modules/common/visualize_signoff.py --root . --work-dir Work --preview-changes ~/Downloads/' + yamlFilename + ' --output ' + htmlFilename;
    
    // Count waivers and skips for the instructions
    const waiverCount = PENDING_CHANGES.filter(c => c.type === 'waive').length;
    const skipCount = PENDING_CHANGES.filter(c => c.type === 'skip').length;
    
    // Show instructions
    const instructions = `╔═══════════════════════════════════════════════════════╗
║     🔍 GENERATE PREVIEW DASHBOARD - INSTRUCTIONS      ║
╚═══════════════════════════════════════════════════════╝

✅ Step 1: Unified YAML file downloaded
   File: ${yamlFilename}
   Location: ~/Downloads/
   Contents: ${waiverCount} waivers, ${skipCount} skips

📝 Step 2: Run the following command in terminal:

   cd /home/wentao/AAI/AAI_CHECK_LIST/CHECKLIST

   ${command}

📂 Step 3: Open the generated preview HTML:
   File: Work/Reports/${htmlFilename}

💡 Tip: The command has been copied to your clipboard!

Click OK to continue.`;
    
    showMessageModal('Generate Preview', instructions);
    
    // Copy command to clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(command).then(() => {
            console.log('[generatePreviewHTML] Command copied to clipboard');
        }).catch(err => {
            console.error('[generatePreviewHTML] Failed to copy to clipboard:', err);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = command;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            console.log('[generatePreviewHTML] Command copied to clipboard (fallback)');
        } catch (err) {
            console.error('[generatePreviewHTML] Failed to copy to clipboard (fallback):', err);
        }
        document.body.removeChild(textArea);
    }
}

// ==================== EXPORT FUNCTIONS ====================

// Export unified pending changes to YAML
function exportPendingChangesYAML() {
    if (PENDING_CHANGES.length === 0) {
        showMessageModal('Export YAML', 'No pending changes to export.');
        return;
    }
    
    const yaml = generateUnifiedYAML();
    
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pending_changes_' + new Date().toISOString().split('T')[0] + '.yaml';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Export unified pending changes to Excel (CSV)
function exportPendingChangesExcel() {
    if (PENDING_CHANGES.length === 0) {
        showMessageModal('Export Excel', 'No pending changes to export.');
        return;
    }
    
    // CSV header with Type column
    let csv = 'Type,ID,Module,Item ID,Details,Reason/Comment,Timestamp' + '\\n';
    
    PENDING_CHANGES.forEach(c => {
        if (c.type === 'waive') {
            const row = [
                'Waiver',
                c.id,
                c.moduleName,
                c.itemId,
                '"' + c.itemDesc.replace(/"/g, '""').replace(/\\n/g, ' ').replace(/\\r/g, ' ') + '"',
                '"' + c.comment.replace(/"/g, '""').replace(/\\n/g, ' ').replace(/\\r/g, ' ') + '"',
                c.timestamp
            ];
            csv += row.join(',') + '\\n';
        } else if (c.type === 'skip') {
            const row = [
                'Skip',
                c.id,
                c.module,
                c.item_id || 'ENTIRE_MODULE',
                c.item_id ? '"Individual Item"' : '"Full Module Skip"',
                '"' + c.reason.replace(/"/g, '""').replace(/\\n/g, ' ').replace(/\\r/g, ' ') + '"',
                c.timestamp
            ];
            csv += row.join(',') + '\\n';
        }
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pending_changes_' + new Date().toISOString().split('T')[0] + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Clear all pending changes (waivers + skips)
function clearAllPendingChanges() {
    if (PENDING_CHANGES.length === 0) {
        showMessageModal('Clear All', 'No pending changes to clear.');
        return;
    }
    
    const waiverCount = PENDING_CHANGES.filter(c => c.type === 'waive').length;
    const skipCount = PENDING_CHANGES.filter(c => c.type === 'skip').length;
    const message = 'Are you sure you want to clear all ' + PENDING_CHANGES.length + ' pending change(s)?\\n' +
        '(' + waiverCount + ' waivers, ' + skipCount + ' skips)';
    
    showMessageModal(
        'Clear All',
        message,
        [
            {text: 'Cancel', isPrimary: false, action: null},
            {text: 'Clear All', isPrimary: true, action: () => {
                PENDING_CHANGES = [];
                saveChanges();
                
                // Reset all waive buttons
                document.querySelectorAll('.waive-btn[disabled]').forEach(btn => {
                    btn.textContent = 'Waive';
                    btn.disabled = false;
                    btn.style.background = '#3b82f6';
                });
                
                // Reset all "Waive All" buttons
                document.querySelectorAll('.waive-all-btn[disabled]').forEach(btn => {
                    btn.textContent = 'Waive All';
                    btn.disabled = false;
                    btn.style.background = '#8b5cf6';
                });
                
                // Reset all skip buttons (if exists)
                document.querySelectorAll('.skip-module-btn[disabled]').forEach(btn => {
                    btn.textContent = 'Skip Module';
                    btn.disabled = false;
                });
                
                updatePendingChangesBar();
                exitPreviewMode();
                
                showMessageModal('Clear All', 'All pending changes have been cleared.');
            }}
        ]
    );
}

// Tab switching
document.querySelectorAll('.tab-button[data-tab]').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        
        // Update buttons
        document.querySelectorAll('.tab-button[data-tab]').forEach(b => b.classList.remove('active'));
        button.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tabName + '-tab').classList.add('active');
        
        // Setup collapsible cells when Details tab is activated
        if (tabName === 'details') {
            console.log('Details tab activated, populating module nav cards and setting up collapsible cells...');
            setTimeout(() => {
                populateModuleNavCards();
                setupCollapsibleCells();
            }, 100);
        }
        
        // Setup approved waivers table when Waivers tab is activated
        if (tabName === 'waivers') {
            console.log('Waivers tab activated, populating both approved and pending waivers...');
            setTimeout(() => {
                populateApprovedWaiversTable();
                populatePendingWaiversTable();  // Also populate pending to show count badge
            }, 100);
        }
    });
});

// Sub-tab switching for Waivers
document.querySelectorAll('.tab-button[data-subtab]').forEach(button => {
    button.addEventListener('click', () => {
        const subtabName = button.dataset.subtab;
        
        // Update sub-tab buttons
        document.querySelectorAll('.tab-button[data-subtab]').forEach(b => b.classList.remove('active'));
        button.classList.add('active');
        
        // Update sub-tab content
        document.querySelectorAll('.subtab-content').forEach(c => c.style.display = 'none');
        const targetContent = document.getElementById(subtabName + '-waivers-content');
        if (targetContent) {
            targetContent.style.display = 'block';
        }
        
        // Populate pending waivers table when switching to pending tab
        if (subtabName === 'pending') {
            console.log('Pending waivers tab activated, populating table...');
            populatePendingWaiversTable();
        }
    });
});

// Initialize dashboard
function initDashboard() {
    console.log('Initializing dashboard...');
    
    // Load PENDING_CHANGES FIRST before any stats calculation
    console.log('- Loading pending changes from localStorage');
    loadChanges();
    console.log('- Loaded', PENDING_CHANGES.length, 'pending changes');
    
    // Setup event listeners FIRST, before any rendering
    console.log('- Setting up category filter');
    setupCategoryFilter();
    console.log('- Setting up module sort');
    setupModuleSort();
    
    console.log('- Updating quick stats cards');
    updateQuickStatsCards();
    
    // Apply initial category filter to ensure correct status calculation
    // In Preview Mode, use preloaded OVERALL_STATS (already recalculated with waivers)
    // In Normal Mode, recalculate stats from filtered modules
    const categoryFilter = document.getElementById('category-filter');
    const initialCategory = categoryFilter ? categoryFilter.value : 'all';
    console.log('- Applying initial category filter:', initialCategory);
    
    // Runtime detection: Check if we're in Preview Mode (sessionStorage flag)
    const isRuntimePreviewMode = sessionStorage.getItem('previewModeActive') === 'true';
    const effectivePreviewMode = IS_PREVIEW_MODE || isRuntimePreviewMode;
    
    console.log('[Preview Detection] IS_PREVIEW_MODE (compile-time):', IS_PREVIEW_MODE);
    console.log('[Preview Detection] isRuntimePreviewMode (sessionStorage):', isRuntimePreviewMode);
    console.log('[Preview Detection] effectivePreviewMode (final):', effectivePreviewMode);
    
    if (effectivePreviewMode) {
        console.log('========================================');
        console.log('🔍 [initDashboard] PREVIEW MODE ACTIVE');
        console.log('========================================');
        console.log('[Preview] Using preloaded OVERALL_STATS for initial display');
        console.log('[Preview] OVERALL_STATS:', OVERALL_STATS);
        console.log('[Preview] OVERALL_STATS.waiver:', OVERALL_STATS.waiver);
        console.log('[Preview] PENDING_CHANGES length:', typeof PENDING_CHANGES !== 'undefined' ? PENDING_CHANGES.length : 'N/A');
        
        // In preview mode, apply the filter
        const filteredModules = initialCategory === 'all' 
            ? MODULES_DATA 
            : MODULES_DATA.filter(m => m.category === initialCategory);
        
        console.log('[Preview] Filtered modules count:', filteredModules.length);
        
        // Recalculate stats to ensure overall_status is computed correctly
        // This uses effectivePreviewMode detection internally for waiver counting
        const stats = calculateFilteredStats(filteredModules);
        console.log('[Preview] Recalculated stats with overall_status:', stats);
        
        // Use recalculated stats (has correct waiver count AND overall_status)
        updateStatusIndicatorFiltered(stats);
        updateMetricsFiltered(stats, filteredModules);
        updateCategoryProgressFiltered(filteredModules, initialCategory);
        const sortSelect = document.getElementById('module-sort');
        const sortBy = sortSelect ? sortSelect.value : 'name';
        updateModuleCardsFiltered(filteredModules, sortBy);
        createChartsFiltered(filteredModules);
        
        console.log('========================================');
        console.log('[Preview] ✅ Initial display complete');
        console.log('========================================');
    } else {
        console.log('[Normal Mode] Recalculating everything via applyCategoryFilter');
        // Normal mode: recalculate everything
        applyCategoryFilter(initialCategory);
    }
    
    console.log('Dashboard initialization complete');
}

// ==================== DEVELOPER TESTING FUNCTIONS ====================
// 测试函数：在Console中注入测试waiver数据
window.injectTestWaivers = function(count = 3) {
    console.log('[TEST] Injecting', count, 'test waivers...');
    
    // Get first few modules
    const modules = MODULES_DATA.slice(0, Math.min(count, MODULES_DATA.length));
    
    modules.forEach((module, idx) => {
        const testWaiver = {
            type: 'waive',
            moduleName: module.name,
            itemId: `TEST_ITEM_${idx + 1}`,
            failureIndex: 0,
            timestamp: new Date().toISOString(),
            reason: `Test waiver ${idx + 1} for development`,
            reviewer: 'Developer'
        };
        
        PENDING_CHANGES.push(testWaiver);
    });
    
    saveChanges();
    console.log('[TEST] Injected', count, 'test waivers');
    console.log('[TEST] Current PENDING_CHANGES length:', PENDING_CHANGES.length);
    console.log('[TEST] Refreshing dashboard...');
    
    // Refresh dashboard
    const categoryFilter = document.getElementById('category-filter');
    const currentCategory = categoryFilter ? categoryFilter.value : 'all';
    applyCategoryFilter(currentCategory);
    
    console.log('[TEST] ✅ Dashboard refreshed! Check Waivers count in metrics.');
};

// 测试函数：清空所有pending changes
window.clearAllChanges = function() {
    console.log('[TEST] Clearing all pending changes...');
    PENDING_CHANGES = [];
    saveChanges();
    console.log('[TEST] Cleared. Refreshing dashboard...');
    
    const categoryFilter = document.getElementById('category-filter');
    const currentCategory = categoryFilter ? categoryFilter.value : 'all';
    applyCategoryFilter(currentCategory);
    
    console.log('[TEST] ✅ Dashboard refreshed! Waivers count should be 0.');
};

console.log('');
console.log('🔧 Developer Testing Functions Available:');
console.log('  - injectTestWaivers(count)  : Inject test waiver data (default: 3)');
console.log('  - clearAllChanges()         : Clear all waivers and skips');
console.log('');

// Update quick stats cards
function updateQuickStatsCards() {
    console.log('[updateQuickStatsCards] Called');
    const container = document.getElementById('quick-stats-cards');
    if (!container) {
        console.error('[updateQuickStatsCards] Container not found!');
        return;
    }
    
    const stats = OVERALL_STATS;
    console.log('[updateQuickStatsCards] OVERALL_STATS:', stats);
    const totalModules = MODULES_DATA.length;
    const completedModules = MODULES_DATA.filter(m => m.status === 'pass').length;
    const criticalIssues = stats.fail;
    const completionPct = stats.total > 0 ? Math.round(stats.executed / stats.total * 100) : 0;
    
    console.log('[updateQuickStatsCards] Critical Issues:', criticalIssues, 'Pass Rate:', stats.pass_rate);
    
    container.innerHTML = `
        <div class='metric-card' style='background:#6366f1; color:white; box-shadow: 0 2px 8px rgba(99,102,241,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Total Checks</div>
            <div class='metric-value' style='color:white;'>${stats.total}</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>${totalModules} modules</div>
        </div>
        <div class='metric-card' style='background:#10b981; color:white; box-shadow: 0 2px 8px rgba(16,185,129,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Completion Rate</div>
            <div class='metric-value' style='color:white;'>${completionPct}%</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>${stats.executed}/${stats.total} executed</div>
        </div>
        <div class='metric-card' style='background:#ef4444; color:white; box-shadow: 0 2px 8px rgba(239,68,68,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Critical Issues</div>
            <div class='metric-value' style='color:white;'>${criticalIssues}</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>Must be resolved</div>
        </div>
        <div class='metric-card' style='background:#3b82f6; color:white; box-shadow: 0 2px 8px rgba(59,130,246,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Modules Complete</div>
            <div class='metric-value' style='color:white;'>${completedModules}</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>of ${totalModules} modules</div>
        </div>
    `;
}

function updateQuickStatsCardsFiltered(modules, stats) {
    const container = document.getElementById('quick-stats-cards');
    if (!container) return;
    
    const totalModules = modules.length;
    const completedModules = modules.filter(m => m.status === 'pass').length;
    const criticalIssues = stats.fail;
    const completionPct = stats.total > 0 ? Math.round(stats.executed / stats.total * 100) : 0;
    
    container.innerHTML = `
        <div class='metric-card' style='background:#6366f1; color:white; box-shadow: 0 2px 8px rgba(99,102,241,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Total Checks</div>
            <div class='metric-value' style='color:white;'>${stats.total}</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>${totalModules} modules</div>
        </div>
        <div class='metric-card' style='background:#10b981; color:white; box-shadow: 0 2px 8px rgba(16,185,129,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Completion Rate</div>
            <div class='metric-value' style='color:white;'>${completionPct}%</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>${stats.executed}/${stats.total} executed</div>
        </div>
        <div class='metric-card' style='background:#ef4444; color:white; box-shadow: 0 2px 8px rgba(239,68,68,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Critical Issues</div>
            <div class='metric-value' style='color:white;'>${criticalIssues}</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>Must be resolved</div>
        </div>
        <div class='metric-card' style='background:#3b82f6; color:white; box-shadow: 0 2px 8px rgba(59,130,246,0.2);'>
            <div class='metric-label' style='color:rgba(255,255,255,0.9);'>Modules Complete</div>
            <div class='metric-value' style='color:white;'>${completedModules}</div>
            <div class='metric-subtext' style='color:rgba(255,255,255,0.8);'>of ${totalModules} modules</div>
        </div>
    `;
}

// Setup category filter
function setupCategoryFilter() {
    const filterSelect = document.getElementById('category-filter');
    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            const selectedCategory = e.target.value;
            applyCategoryFilter(selectedCategory);
        });
    }
}

// Apply category filter (recompute everything with filtered data)
function applyCategoryFilter(category) {
    // Filter modules
    const filteredModules = category === 'all' 
        ? MODULES_DATA 
        : MODULES_DATA.filter(m => m.category === category);
    
    // Recalculate overall stats from filtered modules
    const filteredStats = calculateFilteredStats(filteredModules);
    
    // Update status indicator
    updateStatusIndicatorFiltered(filteredStats);
    
    // Update metrics
    updateMetricsFiltered(filteredStats, filteredModules);
    
    // Update category progress (only show selected category or all)
    updateCategoryProgressFiltered(filteredModules, category);
    
    // Update module cards with current sort
    const sortSelect = document.getElementById('module-sort');
    const sortBy = sortSelect ? sortSelect.value : 'name';
    updateModuleCardsFiltered(filteredModules, sortBy);
    
    // Update charts
    createChartsFiltered(filteredModules);
}

function calculateFilteredStats(modules) {
    console.log('=== [calculateFilteredStats] CALLED ===');
    console.log('[calculateFilteredStats] IS_PREVIEW_MODE:', IS_PREVIEW_MODE);
    console.log('[calculateFilteredStats] Number of modules:', modules.length);
    
    // Runtime detection: Check if we're in Preview Mode
    const isRuntimePreviewMode = sessionStorage.getItem('previewModeActive') === 'true';
    const effectivePreviewMode = IS_PREVIEW_MODE || isRuntimePreviewMode;
    
    console.log('[calculateFilteredStats] IS_PREVIEW_MODE (compile-time):', IS_PREVIEW_MODE);
    console.log('[calculateFilteredStats] isRuntimePreviewMode (sessionStorage):', isRuntimePreviewMode);
    console.log('[calculateFilteredStats] effectivePreviewMode (final):', effectivePreviewMode);
    
    // Note: modules already have skipped items filtered out, so stats are based on remaining items only
    const total = modules.reduce((sum, m) => sum + m.stats.total, 0);
    const executed = modules.reduce((sum, m) => sum + m.stats.executed, 0);
    const pass = modules.reduce((sum, m) => sum + m.stats.pass, 0);
    const fail = modules.reduce((sum, m) => sum + m.stats.fail, 0);
    const pending = modules.reduce((sum, m) => sum + m.stats.pending, 0);
    
    console.log('[calculateFilteredStats] Basic stats - total:', total, 'executed:', executed, 'pass:', pass, 'fail:', fail, 'pending:', pending);
    
    // Calculate waiver count based on mode
    let waiver = 0;
    
    if (effectivePreviewMode) {
        // Preview Mode: Count unique waived items from BOTH sources
        // 1. Existing waivers from YAML data
        // 2. New waivers from PENDING_CHANGES (user's manual additions)
        console.log('============================================');
        console.log('[calculateFilteredStats] 🔍 PREVIEW MODE - Waiver Calculation Debug');
        console.log('============================================');
        
        const waivedItems = new Set();
        const moduleNames = new Set(modules.map(m => m.name));
        
        console.log('[Preview] Step 1: Counting existing waivers from YAML data');
        console.log('[Preview] Modules being checked:', modules.length);
        console.log('[Preview] Module names:', Array.from(moduleNames).join(', '));
        
        // First, add existing waivers from YAML data
        let yamlWaiverCount = 0;
        modules.forEach(m => {
            m.items.forEach(item => {
                if (item.waivers && Array.isArray(item.waivers) && item.waivers.length > 0) {
                    const itemKey = m.name + '::' + item.id;
                    console.log(`[Preview YAML] Found waiver: ${itemKey} (${item.waivers.length} waiver records)`);
                    waivedItems.add(itemKey);
                    yamlWaiverCount++;
                }
            });
        });
        console.log(`[Preview] ✓ YAML waivers: ${yamlWaiverCount} items with waivers, ${waivedItems.size} unique items in Set`);
        console.log('[Preview] Current waived items in Set:', Array.from(waivedItems));
        
        // Then, add new waivers from PENDING_CHANGES
        console.log('[Preview] Step 2: Counting pending waivers from PENDING_CHANGES');
        console.log('[Preview] PENDING_CHANGES exists?', typeof PENDING_CHANGES !== 'undefined');
        console.log('[Preview] PENDING_CHANGES length:', typeof PENDING_CHANGES !== 'undefined' ? PENDING_CHANGES.length : 'N/A');
        
        if (typeof PENDING_CHANGES !== 'undefined' && PENDING_CHANGES.length > 0) {
            console.log('[Preview] PENDING_CHANGES content (first 5):', PENDING_CHANGES.slice(0, 5));
            const waiveChanges = PENDING_CHANGES.filter(change => change.type === 'waive');
            console.log(`[Preview] ✓ Found ${waiveChanges.length} waive-type changes in PENDING_CHANGES`);
            
            let pendingWaiverCount = 0;
            let pendingWaiverAdded = 0;
            waiveChanges.forEach(w => {
                pendingWaiverCount++;
                const hasModule = moduleNames.has(w.moduleName);
                const itemKey = w.moduleName + '::' + w.itemId;
                const alreadyExists = waivedItems.has(itemKey);
                
                console.log(`[Preview PENDING] Waiver ${pendingWaiverCount}: ${itemKey}`);
                console.log(`  - Module in filter? ${hasModule}`);
                console.log(`  - Already in Set? ${alreadyExists}`);
                
                // Only count waivers for modules in current filter
                if (hasModule) {
                    waivedItems.add(itemKey);
                    if (!alreadyExists) {
                        pendingWaiverAdded++;
                        console.log(`  - ✓ Added to Set (new item)`);
                    } else {
                        console.log(`  - ⚠ Not added (duplicate, already has YAML waiver)`);
                    }
                } else {
                    console.log(`  - ✗ Skipped (module not in current filter)`);
                }
            });
            console.log(`[Preview] ✓ PENDING waivers: ${pendingWaiverCount} total, ${pendingWaiverAdded} new unique items added`);
        } else {
            console.log('[Preview] ⚠ No PENDING_CHANGES available');
        }
        
        waiver = waivedItems.size;
        console.log('============================================');
        console.log(`[Preview] 📊 FINAL RESULT: ${waiver} unique waived items`);
        console.log('[Preview] Final Set contents:', Array.from(waivedItems));
        console.log('============================================');
    } else {
        // Normal Mode: Count unique waived items from YAML data only
        console.log('[calculateFilteredStats] Normal mode - counting unique items from YAML');
        const waivedItems = new Set();
        modules.forEach(m => {
            m.items.forEach(item => {
                if (item.waivers && Array.isArray(item.waivers) && item.waivers.length > 0) {
                    waivedItems.add(m.name + '::' + item.id);
                }
            });
        });
        waiver = waivedItems.size;
        console.log('[calculateFilteredStats] Normal mode unique waived items:', waiver);
    }
    
    const pass_rate = executed > 0 ? Math.round(pass / executed * 100 * 10) / 10 : 0;
    const execution_rate = total > 0 ? Math.round(executed / total * 100 * 10) / 10 : 0;
    
    let overall_status = 'unknown';
    if (total === 0) {
        overall_status = 'unknown';
    } else if (fail > 0) {
        // Has critical issues - needs attention
        overall_status = 'needs_attention';
    } else if (execution_rate < 100) {
        // No critical issues but checks not complete - in progress
        overall_status = 'in_progress';
    } else {
        // No critical issues and all checks complete - ready for signoff
        overall_status = 'ready';
    }
    
    return {total, executed, pass, fail, pending, waiver, pass_rate, execution_rate, overall_status};
}

function updateStatusIndicatorFiltered(stats) {
    const indicator = document.getElementById('status-indicator');
    const status = stats.overall_status;
    
    let icon, text, subtext, className;
    
    if (status === 'ready') {
        icon = `<svg width='24' height='24' viewBox='0 0 24 24' style='display:block;'>
            <circle cx='12' cy='12' r='10' fill='#10b981' stroke='#059669' stroke-width='1.2'/>
            <path d='M7 12 L10.5 15.5 L17 9' stroke='white' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/>
        </svg>`;
        text = 'READY FOR SIGNOFF';
        subtext = 'All checks passed';
        className = 'ready';
    } else if (status === 'in_progress') {
        icon = `<svg width='24' height='24' viewBox='0 0 24 24' style='display:block;'>
            <circle cx='12' cy='12' r='10' fill='#3b82f6' stroke='#2563eb' stroke-width='1.2'/>
            <circle cx='12' cy='12' r='3' fill='white'/>
            <path d='M12 7 L12 12' stroke='white' stroke-width='2' stroke-linecap='round'/>
        </svg>`;
        text = 'CHECKS IN PROGRESS';
        subtext = 'No critical issues yet';
        className = 'in-progress';
    } else if (status === 'needs_attention') {
        icon = `<svg width='24' height='24' viewBox='0 0 24 24' style='display:block;'>
            <path d='M12 3 L22.5 21 L1.5 21 Z' fill='#ef4444' stroke='#dc2626' stroke-width='1.2'/>
            <path d='M11.25 9 L12.75 9 L12.75 15 L11.25 15 Z' fill='white'/>
            <circle cx='12' cy='18' r='0.9' fill='white'/>
        </svg>`;
        text = 'NEEDS ATTENTION';
        subtext = 'Some checks failed';
        className = 'needs-attention';
    } else {
        icon = '○';
        text = 'NOT STARTED';
        subtext = 'No checks executed';
        className = 'in-progress';
    }
    
    indicator.className = `status-indicator-compact ${className}`;
    indicator.innerHTML = `
        <div class='status-icon-wrapper'>
            <span id='status-icon'>${icon}</span>
        </div>
        <div class='status-content'>
            <div class='status-text' id='status-text'>${text}</div>
            <div class='status-subtext' id='status-subtext' style='${className === 'needs-attention' ? 'color:#ef4444; font-weight:600;' : ''}'>${subtext}</div>
        </div>
    `;
}

// Determine Pass Rate card color based on pass rate and execution rate
function getPassRateColor(passRate, executionRate, totalPassed, totalExecuted, totalItems) {
    const redThreshold = 10;  // Red threshold at 10%
    
    // Rule 4: All passed - only when 100% pass AND all items are executed AND passed
    // This means: passRate === 100% AND executionRate === 100% AND pass === total
    if (passRate === 100 && executionRate === 100 && totalPassed === totalItems) {
        return {
            main: '#10b981',      // Green - perfect completion
            secondary: '#059669',
            light: '#34d399'
        };
    }
    
    // Rule 3: Pass rate equals execution rate (in progress, no failures yet)
    // Color matches Check Execution Rate (purple)
    if (passRate === executionRate) {
        return {
            main: '#6366f1',      // Purple - same as execution rate
            secondary: '#4f46e5',
            light: '#818cf8'
        };
    }
    
    // Rule 2: Pass rate >= 10% but < execution rate (some failures, marked as orange)
    if (passRate >= redThreshold && passRate < executionRate) {
        return {
            main: '#f59e0b',      // Orange - has failures but acceptable
            secondary: '#d97706',
            light: '#fbbf24'
        };
    }
    
    // Rule 1: Pass rate < 10% (critical, marked as red)
    return {
        main: '#ef4444',      // Red - critical failure rate
        secondary: '#dc2626',
        light: '#f87171'
    };
}

// Determine category progress bar color
function getCategoryProgressColor(passRate, executionRate, totalPassed, totalExecuted, totalItems) {
    const redThreshold = 10;  // Red threshold at 10%
    
    // Same logic as Pass Rate card
    // Rule 4: All passed - only when 100% pass AND all items executed AND passed
    if (passRate === 100 && executionRate === 100 && totalPassed === totalItems) {
        return '#10b981';  // Green - perfect completion
    }
    
    // Rule 3: Pass rate equals execution rate (matches Check Execution Rate color)
    if (passRate === executionRate) {
        return '#6366f1';  // Purple - same as execution rate
    }
    
    // Rule 2: Pass rate >= 10% but < execution rate (some failures)
    if (passRate >= redThreshold && passRate < executionRate) {
        return '#f59e0b';  // Orange - has failures but acceptable
    }
    
    // Rule 1: Pass rate < 10% (critical)
    return '#ef4444';  // Red - critical failure rate
}

function updateMetricsFiltered(stats, modules) {
    console.log('📊 [updateMetricsFiltered] Called with stats:', stats);
    console.log('📊 [updateMetricsFiltered] Waiver count in stats:', stats.waiver);
    console.log('📊 [updateMetricsFiltered] IS_PREVIEW_MODE:', IS_PREVIEW_MODE);
    
    const grid = document.getElementById('metrics-grid');
    const totalModules = modules.length;
    const executedModules = modules.filter(m => m.stats.executed > 0).length;
    const completedModules = modules.filter(m => m.status === 'pass').length;
    const executionRate = stats.total > 0 ? Math.round(stats.executed / stats.total * 100) : 0;
    const passRate = stats.total > 0 ? Math.round(stats.pass / stats.total * 100) : 0;
    
    // Get dynamic color for Pass Rate card
    const passRateColors = getPassRateColor(passRate, executionRate, stats.pass, stats.executed, stats.total);
    
    grid.innerHTML = `
        <div class='metric-card' style='--card-color:#6366f1;'>
            <div class='metric-label' style='color:#6366f1;'>Check Execution Rate</div>
            <div class='metric-value' style='color:#4f46e5;'>${executionRate}%</div>
            <div class='metric-subtext' style='color:#818cf8;'>${stats.executed}/${stats.total} items executed</div>
        </div>
        <div class='metric-card' style='--card-color:${passRateColors.main};'>
            <div class='metric-label' style='color:${passRateColors.main};'>PASS RATE</div>
            <div class='metric-value' style='color:${passRateColors.secondary};'>${passRate}%</div>
            <div class='metric-subtext' style='color:${passRateColors.light};'>${stats.pass}/${stats.total} items passed</div>
        </div>
        <div class='metric-card' style='--card-color:#ef4444;'>
            <div class='metric-label' style='color:#ef4444;'>Critical Issues <i class='metric-icon' style='background:rgba(239,68,68,0.15); color:#dc2626;'>⚠</i></div>
            <div class='metric-value' style='color:#dc2626;'>${stats.fail}</div>
            <div class='metric-subtext' style='color:#f87171;'>Require immediate action</div>
        </div>
        <div class='metric-card' style='--card-color:#3b82f6;'>
            <div class='metric-label' style='color:#3b82f6;'>Waivers <i class='metric-icon' style='background:rgba(59,130,246,0.15); color:#2563eb;'>✓</i></div>
            <div class='metric-value' style='color:#2563eb;'>${stats.waiver}</div>
            <div class='metric-subtext' style='color:#60a5fa;'>Approved exceptions</div>
        </div>
    `;
}

function updateCategoryProgressFiltered(modules, category) {
    const container = document.getElementById('category-progress');
    const categories = {};
    
    // Group by category
    modules.forEach(module => {
        const cat = module.category;
        if (!categories[cat]) {
            categories[cat] = {total: 0, executed: 0, pass: 0, fail: 0};
        }
        categories[cat].total += module.stats.total;
        categories[cat].executed += module.stats.executed;
        categories[cat].pass += module.stats.pass;
        categories[cat].fail += module.stats.fail;
    });
    
    // Generate progress bars
    let html = '';
    for (const [cat, stats] of Object.entries(categories)) {
        const percentage = stats.total > 0 ? Math.round(stats.pass / stats.total * 100) : 0;
        const executionRate = stats.total > 0 ? Math.round(stats.executed / stats.total * 100) : 0;
        const barColor = getCategoryProgressColor(percentage, executionRate, stats.pass, stats.executed, stats.total);
        
        // 只有当进度大于8%时才在进度条内显示百分比
        const showPercentage = percentage > 8;
        const percentageHtml = showPercentage ? `<span class='progress-percentage'>${percentage}%</span>` : '';
        
        html += `
            <div class='progress-item'>
                <div class='progress-label'>${cat}</div>
                <div class='progress-bar-container'>
                    <div class='progress-bar-bg'>
                        <div class='progress-bar-fill' style='width: ${percentage}%; background: ${barColor};'>
                            ${percentageHtml}
                        </div>
                    </div>
                    <div class='progress-stats'>${stats.pass}/${stats.total}</div>
                </div>
            </div>
        `;
    }
    
    if (html) {
        container.innerHTML = html;
    } else {
        container.innerHTML = `
            <div style='text-align:center; padding:2rem; color:#64748b;'>
                <div style='font-size:2rem; margin-bottom:0.5rem;'>📊</div>
                <p>No data available for selected category</p>
            </div>
        `;
    }
}

// CSS-based chart rendering (no Chart.js dependency)
function createChartsFiltered(modules) {
    console.log('Creating filtered charts (CSS version)...');
    createSectionChartFiltered(modules);
    createProgressChartFiltered(modules);
    console.log('Filtered charts created');
}

function createSectionChartFiltered(modules) {
    const container = document.getElementById('sectionChart');
    if (!container) return;
    
    console.log('[createSectionChartFiltered] Called with', modules.length, 'modules');
    
    // Runtime detection: Check if we're in Preview Mode
    const isRuntimePreviewMode = sessionStorage.getItem('previewModeActive') === 'true';
    const effectivePreviewMode = IS_PREVIEW_MODE || isRuntimePreviewMode;
    
    console.log('[createSectionChartFiltered] Preview mode:', effectivePreviewMode);
    console.log('[createSectionChartFiltered] PENDING_CHANGES:', typeof PENDING_CHANGES !== 'undefined' ? PENDING_CHANGES.length : 'undefined');
    
    const statusCounts = { pass: 0, partial: 0, fail: 0, in_progress: 0, pending: 0 };
    modules.forEach(module => {
        let effectiveStatus;
        
        // Debug: log first module's overall_status
        if (modules.indexOf(module) === 0) {
            console.log('[First Module Debug]', module.name, 'overall_status:', module.overall_status, 'stats:', module.stats);
        }
        
        // Map module.overall_status to chart status (non-preview mode)
        // overall_status values: 'ready', 'needs_attention', 'in_progress'
        // chart status values: 'pass', 'fail', 'in_progress', 'pending'
        if (module.overall_status === 'ready') {
            effectiveStatus = 'pass';
        } else if (module.overall_status === 'needs_attention') {
            effectiveStatus = 'fail';
        } else if (module.overall_status === 'in_progress') {
            effectiveStatus = 'in_progress';
        } else {
            effectiveStatus = 'pending';
        }
        
        // In preview mode, recalculate module status based on pending waivers
        if (effectivePreviewMode && typeof PENDING_CHANGES !== 'undefined' && PENDING_CHANGES.length > 0) {
            // Count stats for this module with waivers applied
            let totalCount = module.items.length;
            let executedCount = 0;
            let passCount = 0;
            let failCount = 0;
            
            module.items.forEach(item => {
                if (item.executed) {
                    executedCount++;
                }
                if (item.status === 'pass') {
                    passCount++;
                } else if (item.status === 'fail' && item.executed && item.failures && item.failures.length > 0) {
                    // Check if all failures for this item are waived
                    const allFailuresWaived = item.failures.every((failure, failIdx) => {
                        return PENDING_CHANGES.some(change => 
                            change.type === 'waive' &&
                            change.moduleName === module.name &&
                            change.itemId === item.id &&
                            (change.failureIndex === failIdx || change.failureIndex === -1)
                        );
                    });
                    
                    if (!allFailuresWaived) {
                        failCount++;
                    }
                }
            });
            
            // Determine status based on Python logic (lines 472-477 in visualize_signoff.py):
            // if fail_count == 0 and executed == total: status = 'ready' (pass)
            // elif fail_count > 0: status = 'needs_attention' (fail)
            // else: status = 'in_progress'
            if (failCount > 0) {
                effectiveStatus = 'fail';
            } else if (executedCount === totalCount) {
                effectiveStatus = 'pass';
            } else if (executedCount > 0) {
                effectiveStatus = 'in_progress';
            } else {
                effectiveStatus = 'pending';
            }
            
            console.log('[Module]', module.name, '- total:', totalCount, 'executed:', executedCount, 'pass:', passCount, 'fail:', failCount, 'status:', module.status, '->', effectiveStatus);
        }
        
        statusCounts[effectiveStatus] = (statusCounts[effectiveStatus] || 0) + 1;
    });
    
    console.log('[createSectionChartFiltered] Final counts:', statusCounts);
    
    const total = modules.length;
    if (total === 0) {
        container.innerHTML = '<div style="text-align:center; padding:3rem; color:#64748b;">No modules to display</div>';
        return;
    }
    
    const passPercent = Math.round((statusCounts.pass / total) * 100);
    const partialPercent = Math.round((statusCounts.partial / total) * 100);
    const failPercent = Math.round((statusCounts.fail / total) * 100);
    const inProgressPercent = Math.round((statusCounts.in_progress / total) * 100);
    const pendingPercent = 100 - passPercent - partialPercent - failPercent - inProgressPercent;
    
    container.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:center; gap:2.5rem; padding:2rem; min-height:280px;">
            <div style="position:relative; width:160px; height:160px; flex-shrink:0;">
                <svg width="160" height="160" style="transform:rotate(-90deg);">
                    ${statusCounts.pass > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#10b981" stroke-width="32" stroke-dasharray="${(statusCounts.pass/total)*188.4} 188.4" stroke-dashoffset="0"/>` : ''}
                    ${statusCounts.partial > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#f59e0b" stroke-width="32" stroke-dasharray="${(statusCounts.partial/total)*188.4} 188.4" stroke-dashoffset="${-(statusCounts.pass/total)*188.4}"/>` : ''}
                    ${statusCounts.fail > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#ef4444" stroke-width="32" stroke-dasharray="${(statusCounts.fail/total)*188.4} 188.4" stroke-dashoffset="${-((statusCounts.pass+statusCounts.partial)/total)*188.4}"/>` : ''}
                    ${statusCounts.in_progress > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#f97316" stroke-width="32" stroke-dasharray="${(statusCounts.in_progress/total)*188.4} 188.4" stroke-dashoffset="${-((statusCounts.pass+statusCounts.partial+statusCounts.fail)/total)*188.4}"/>` : ''}
                    ${statusCounts.pending > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#cbd5e1" stroke-width="32" stroke-dasharray="${(statusCounts.pending/total)*188.4} 188.4" stroke-dashoffset="${-((statusCounts.pass+statusCounts.partial+statusCounts.fail+statusCounts.in_progress)/total)*188.4}"/>` : ''}
                    <circle cx="80" cy="80" r="44" fill="white"/>
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;">
                    <div style="font-size:2.2rem; font-weight:700; color:#0f172a;">${total}</div>
                    <div style="font-size:0.75rem; color:#64748b; font-weight:600; letter-spacing:0.05em;">MODULES</div>
                </div>
            </div>
            <div style="flex:1; min-width:200px;">
                <table class="chart-stats-table" style="width:100%; border-collapse:collapse;">
                    <thead style="background:#f8fafc !important;"><tr style="background:#f8fafc !important; border-bottom:1px solid #e2e8f0;">
                        <th style="text-align:left; padding:0.5rem 0; color:#64748b !important; font-size:0.6875rem; font-weight:500; text-transform:uppercase; letter-spacing:0.03em; background:#f8fafc !important;">STATUS</th>
                        <th style="text-align:right; padding:0.5rem 0; color:#64748b !important; font-size:0.6875rem; font-weight:500; text-transform:uppercase; letter-spacing:0.03em; background:#f8fafc !important;">COUNT</th>
                        <th style="text-align:right; padding:0.5rem 0; color:#64748b !important; font-size:0.6875rem; font-weight:500; text-transform:uppercase; letter-spacing:0.03em; background:#f8fafc !important;">PERCENT</th>
                    </tr></thead>
                    <tbody>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:0.4rem 0;"><div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:#10b981; border-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.1);"></div><span style="color:#0f172a; font-size:0.8125rem; font-weight:600;">Pass</span></div></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${statusCounts.pass}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:600;">${passPercent}%</td></tr>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:0.4rem 0;"><div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:#ef4444; border-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.1);"></div><span style="color:#0f172a; font-size:0.8125rem; font-weight:600;">Failed</span></div></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${statusCounts.fail}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:600;">${failPercent}%</td></tr>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:0.4rem 0;"><div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:#f97316; border-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.1);"></div><span style="color:#0f172a; font-size:0.8125rem; font-weight:600;">In Progress</span></div></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${statusCounts.in_progress}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:600;">${inProgressPercent}%</td></tr>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:0.4rem 0;"><div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:#94a3b8; border-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.1);"></div><span style="color:#0f172a; font-size:0.8125rem; font-weight:600;">Not Started</span></div></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${statusCounts.pending}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:600;">${pendingPercent}%</td></tr>
                        <tr style="border-top:2px solid #cbd5e1;"><td style="padding:0.4rem 0;"><span style="color:#64748b; font-size:0.8125rem; font-weight:700; text-transform:uppercase; letter-spacing:0.03em;">Total</span></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${total}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:700;">100%</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function createProgressChartFiltered(modules) {
    const container = document.getElementById('progressChart');
    if (!container) return;
    
    const total = modules.reduce((sum, m) => sum + m.stats.total, 0);
    const pass = modules.reduce((sum, m) => sum + m.stats.pass, 0);
    const fail = modules.reduce((sum, m) => sum + m.stats.fail, 0);
    const pending = modules.reduce((sum, m) => sum + m.stats.pending, 0);
    
    if (total === 0) {
        container.innerHTML = '<div style="text-align:center; padding:3rem; color:#64748b;">No items to display</div>';
        return;
    }
    
    const passPercent = Math.round((pass / total) * 100);
    const failPercent = Math.round((fail / total) * 100);
    const pendingPercent = 100 - passPercent - failPercent;
    
    container.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:center; gap:2.5rem; padding:2rem; min-height:280px;">
            <div style="position:relative; width:160px; height:160px; flex-shrink:0;">
                <svg width="160" height="160" style="transform:rotate(-90deg);">
                    ${pass > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#10b981" stroke-width="32" stroke-dasharray="${(pass/total)*188.4} 188.4" stroke-dashoffset="0"/>` : ''}
                    ${fail > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#ef4444" stroke-width="32" stroke-dasharray="${(fail/total)*188.4} 188.4" stroke-dashoffset="${-(pass/total)*188.4}"/>` : ''}
                    ${pending > 0 ? `<circle cx="80" cy="80" r="60" fill="none" stroke="#cbd5e1" stroke-width="32" stroke-dasharray="${(pending/total)*188.4} 188.4" stroke-dashoffset="${-((pass+fail)/total)*188.4}"/>` : ''}
                    <circle cx="80" cy="80" r="44" fill="white"/>
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;">
                    <div style="font-size:2.2rem; font-weight:700; color:#0f172a;">${passPercent}%</div>
                    <div style="font-size:0.75rem; color:#64748b; font-weight:600; letter-spacing:0.05em;">PASS RATE</div>
                </div>
            </div>
            <div style="flex:1; min-width:200px;">
                <table class="chart-stats-table" style="width:100%; border-collapse:collapse;">
                    <thead style="background:#f8fafc !important;"><tr style="background:#f8fafc !important; border-bottom:1px solid #e2e8f0;">
                        <th style="text-align:left; padding:0.5rem 0; color:#64748b !important; font-size:0.6875rem; font-weight:500; text-transform:uppercase; letter-spacing:0.03em; background:#f8fafc !important;">STATUS</th>
                        <th style="text-align:right; padding:0.5rem 0; color:#64748b !important; font-size:0.6875rem; font-weight:500; text-transform:uppercase; letter-spacing:0.03em; background:#f8fafc !important;">COUNT</th>
                        <th style="text-align:right; padding:0.5rem 0; color:#64748b !important; font-size:0.6875rem; font-weight:500; text-transform:uppercase; letter-spacing:0.03em; background:#f8fafc !important;">PERCENT</th>
                    </tr></thead>
                    <tbody>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:0.4rem 0;"><div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:#10b981; border-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.1);"></div><span style="color:#0f172a; font-size:0.8125rem; font-weight:600;">Pass</span></div></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${pass}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:600;">${passPercent}%</td></tr>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:0.4rem 0;"><div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:#ef4444; border-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.1);"></div><span style="color:#0f172a; font-size:0.8125rem; font-weight:600;">Fail</span></div></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${fail}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:600;">${failPercent}%</td></tr>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:0.4rem 0;"><div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:#94a3b8; border-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.1);"></div><span style="color:#0f172a; font-size:0.8125rem; font-weight:600;">Pending</span></div></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${pending}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:600;">${pendingPercent}%</td></tr>
                        <tr style="border-top:2px solid #cbd5e1;"><td style="padding:0.4rem 0;"><span style="color:#64748b; font-size:0.8125rem; font-weight:700; text-transform:uppercase; letter-spacing:0.03em;">Total</span></td><td style="text-align:right; padding:0.4rem 0; color:#0f172a; font-size:0.875rem; font-weight:700;">${total}</td><td style="text-align:right; padding:0.4rem 0; color:#475569; font-size:0.8125rem; font-weight:700;">100%</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function updateStatusIndicator() {
    const indicator = document.getElementById('status-indicator');
    const status = OVERALL_STATS.overall_status;
    
    let icon, text, subtext, className;
    
    if (status === 'ready') {
        icon = `<svg width='24' height='24' viewBox='0 0 24 24' style='display:block;'>
            <circle cx='12' cy='12' r='10' fill='#10b981' stroke='#059669' stroke-width='1.2'/>
            <path d='M7 12 L10.5 15.5 L17 9' stroke='white' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/>
        </svg>`;
        text = 'READY FOR SIGNOFF';
        subtext = 'All checks passed';
        className = 'ready';
    } else if (status === 'in_progress') {
        icon = `<svg width='24' height='24' viewBox='0 0 24 24' style='display:block;'>
            <circle cx='12' cy='12' r='10' fill='#3b82f6' stroke='#2563eb' stroke-width='1.2'/>
            <circle cx='12' cy='12' r='3' fill='white'/>
            <path d='M12 7 L12 12' stroke='white' stroke-width='2' stroke-linecap='round'/>
        </svg>`;
        text = 'CHECKS IN PROGRESS';
        subtext = 'No critical issues yet';
        className = 'in-progress';
    } else if (status === 'needs_attention') {
        icon = `<svg width='24' height='24' viewBox='0 0 24 24' style='display:block;'>
            <path d='M12 3 L22.5 21 L1.5 21 Z' fill='#ef4444' stroke='#dc2626' stroke-width='1.2'/>
            <path d='M11.25 9 L12.75 9 L12.75 15 L11.25 15 Z' fill='white'/>
            <circle cx='12' cy='18' r='0.9' fill='white'/>
        </svg>`;
        text = 'NEEDS ATTENTION';
        subtext = 'Some checks failed';
        className = 'needs-attention';
    } else {
        icon = '○';
        text = 'NOT STARTED';
        subtext = 'No checks executed';
        className = 'in-progress';
    }
    
    indicator.className = `status-indicator-compact ${className}`;
    indicator.innerHTML = `
        <div class='status-icon-wrapper'>
            <span id='status-icon'>${icon}</span>
        </div>
        <div class='status-content'>
            <div class='status-text' id='status-text'>${text}</div>
            <div class='status-subtext' id='status-subtext' style='${className === 'needs-attention' ? 'color:#ef4444; font-weight:600;' : ''}'>${subtext}</div>
        </div>
    `;
}

function updateMetrics() {
    console.log('[updateMetrics] Called');
    const grid = document.getElementById('metrics-grid');
    if (!grid) {
        console.error('[updateMetrics] metrics-grid not found!');
        return;
    }
    const stats = OVERALL_STATS;
    console.log('[updateMetrics] Stats:', stats);
    const totalModules = MODULES_DATA.length;
    const executedModules = MODULES_DATA.filter(m => m.stats.executed > 0).length;
    const completedModules = MODULES_DATA.filter(m => m.status === 'pass').length;
    const executionRate = stats.total > 0 ? Math.round(stats.executed / stats.total * 100) : 0;
    const passRate = stats.total > 0 ? Math.round(stats.pass / stats.total * 100) : 0;
    
    console.log('[updateMetrics] Rendering - Pass:', stats.pass, 'Fail:', stats.fail, 'Waiver:', stats.waiver);
    
    // Get dynamic color for Pass Rate card
    const passRateColors = getPassRateColor(passRate, executionRate, stats.pass, stats.executed, stats.total);
    
    grid.innerHTML = `
        <div class='metric-card' style='--card-color:#6366f1;'>
            <div class='metric-label' style='color:#6366f1;'>Check Execution Rate</div>
            <div class='metric-value' style='color:#4f46e5;'>${executionRate}%</div>
            <div class='metric-subtext' style='color:#818cf8;'>${stats.executed}/${stats.total} items executed</div>
        </div>
        <div class='metric-card' style='--card-color:${passRateColors.main};'>
            <div class='metric-label' style='color:${passRateColors.main};'>PASS RATE</div>
            <div class='metric-value' style='color:${passRateColors.secondary};'>${passRate}%</div>
            <div class='metric-subtext' style='color:${passRateColors.light};'>${stats.pass}/${stats.total} items passed</div>
        </div>
        <div class='metric-card' style='--card-color:#ef4444;'>
            <div class='metric-label' style='color:#ef4444;'>Critical Issues <i class='metric-icon' style='background:rgba(239,68,68,0.15); color:#dc2626;' title='Failures that must be resolved'>⚠</i></div>
            <div class='metric-value' style='color:#dc2626;' id='fail-count'>${stats.fail}</div>
            <div class='metric-subtext' style='color:#f87171;'>Require immediate action</div>
        </div>
        <div class='metric-card' style='--card-color:#3b82f6;'>
            <div class='metric-label' style='color:#3b82f6;'>Waivers <i class='metric-icon' style='background:rgba(59,130,246,0.15); color:#2563eb;' title='Approved exceptions with documented justification'>✓</i></div>
            <div class='metric-value' style='color:#2563eb;'>${stats.waiver}</div>
            <div class='metric-subtext' style='color:#60a5fa;'>Approved exceptions</div>
        </div>
    `;
}

function updateCategoryProgress() {
    const container = document.getElementById('category-progress');
    const categories = {};
    
    // Group by category
    MODULES_DATA.forEach(module => {
        const cat = module.category;
        if (!categories[cat]) {
            categories[cat] = { total: 0, executed: 0, pass: 0 };
        }
        categories[cat].total += module.stats.total;
        categories[cat].executed += module.stats.executed;
        categories[cat].pass += module.stats.pass;
    });
    
    let html = '';
    Object.keys(categories).sort().forEach(cat => {
        const stats = categories[cat];
        const percentage = stats.total > 0 ? Math.round(stats.pass / stats.total * 100) : 0;
        const executionRate = stats.total > 0 ? Math.round(stats.executed / stats.total * 100) : 0;
        const barColor = getCategoryProgressColor(percentage, executionRate, stats.pass, stats.executed, stats.total);
        
        html += `
            <div class='progress-item'>
                <div class='progress-label'>
                    <span><strong>${cat}</strong></span>
                    <span>${stats.pass} / ${stats.total} (${percentage}%)</span>
                </div>
                <div class='progress-bar-bg'>
                    <div class='progress-bar-fill' style='width: ${percentage}%; background: ${barColor};'>${percentage}%</div>
                </div>
            </div>
        `;
    });
    
    if (html) {
        container.innerHTML = html;
    } else {
        container.innerHTML = `
            <div style='text-align:center; padding:2rem; color:#64748b;'>
                <div style='font-size:2rem; margin-bottom:0.5rem;'>📊</div>
                <p>No category data available</p>
            </div>
        `;
    }
}

// Update module cards
function updateModuleCards(sortBy) {
    console.log('updateModuleCards called with sortBy:', sortBy);
    updateModuleCardsFiltered(MODULES_DATA, sortBy);
}

function updateModuleCardsFiltered(modules, sortBy) {
    try {
        console.log('=== updateModuleCardsFiltered START ===');
        console.log('sortBy:', sortBy);
        console.log('Input modules count:', modules.length);
        console.log('First 3 module names:', modules.slice(0, 3).map(m => m.name));
        
        const container = document.getElementById('module-cards-container');
        if (!container) {
            console.error('Module cards container not found!');
            return;
        }
        
        console.log('Container found, starting sort...');
        
        // Sort modules
        const sortedModules = [...modules].sort((a, b) => {
        switch(sortBy) {
            case 'name':
                // Extract version numbers for natural sorting (1.0, 2.0, ..., 10.0, 11.0)
                const extractVersion = (name) => {
                    const match = name.match(/^(\d+)\.(\d+)/);
                    if (match) {
                        return parseFloat(match[1] + '.' + match[2]);
                    }
                    return name;
                };
                const aVer = extractVersion(a.name);
                const bVer = extractVersion(b.name);
                
                // If both are numbers, compare numerically
                if (typeof aVer === 'number' && typeof bVer === 'number') {
                    return aVer - bVer;
                }
                // Fallback to string comparison
                return a.name.localeCompare(b.name);
            case 'status':
                const statusOrder = {pass: 0, partial: 1, fail: 2, pending: 3};
                return statusOrder[a.status] - statusOrder[b.status];
            case 'pass-rate':
                const aRate = a.stats.total > 0 ? a.stats.pass / a.stats.total : 0;
                const bRate = b.stats.total > 0 ? b.stats.pass / b.stats.total : 0;
                return bRate - aRate; // Descending
            case 'execution-rate':
                const aExec = a.stats.total > 0 ? a.stats.executed / a.stats.total : 0;
                const bExec = b.stats.total > 0 ? b.stats.executed / b.stats.total : 0;
                return bExec - aExec; // Descending
            default:
                return 0;
        }
    });
    
    // Debug: Show first 5 modules after sorting
    console.log('First 5 modules after sorting by', sortBy + ':');
    sortedModules.slice(0, 5).forEach((m, i) => {
        const execRate = m.stats.total > 0 ? (m.stats.executed / m.stats.total * 100).toFixed(1) : 0;
        console.log(`  ${i+1}. ${m.name} - Exec: ${execRate}%, Status: ${m.status}`);
    });
    
    // Generate cards
    let html = '';
    
    // Check if in preview mode
    const isRuntimePreviewMode = sessionStorage.getItem('previewModeActive') === 'true';
    const effectivePreviewMode = IS_PREVIEW_MODE || isRuntimePreviewMode;
    
    sortedModules.forEach(module => {
        const stats = module.stats;
        const passRate = stats.total > 0 ? Math.round(stats.pass / stats.total * 100) : 0;
        const execRate = stats.total > 0 ? Math.round(stats.executed / stats.total * 100) : 0;
        
        // Determine effective overall_status
        let effectiveOverallStatus = module.overall_status;
        
        // In preview mode, recalculate overall_status based on pending waivers
        if (effectivePreviewMode && typeof PENDING_CHANGES !== 'undefined' && PENDING_CHANGES.length > 0) {
            // Count active failures (non-waived)
            let activeFailCount = 0;
            module.items.forEach(item => {
                if (item.status === 'fail' && item.executed && item.failures && item.failures.length > 0) {
                    const allFailuresWaived = item.failures.every((failure, failIdx) => {
                        return PENDING_CHANGES.some(change => 
                            change.type === 'waive' &&
                            change.moduleName === module.name &&
                            change.itemId === item.id &&
                            (change.failureIndex === failIdx || change.failureIndex === -1)
                        );
                    });
                    if (!allFailuresWaived) {
                        activeFailCount++;
                    }
                }
            });
            
            // Recalculate overall_status based on same logic as Python (lines 838-846)
            const totalCount = module.items.length;
            const executedCount = module.items.filter(i => i.executed).length;
            
            if (activeFailCount > 0) {
                effectiveOverallStatus = 'needs_attention';
            } else if (executedCount === totalCount) {
                effectiveOverallStatus = 'ready';
            } else if (executedCount > 0) {
                effectiveOverallStatus = 'in_progress';
            } else {
                effectiveOverallStatus = 'pending';
            }
        }
        
        // Use effective overall_status for display (ready, needs_attention, in_progress, pending)
        const statusLabel = effectiveOverallStatus === 'ready' ? 'PASS' : 
                           effectiveOverallStatus === 'needs_attention' ? 'FAIL' :
                           effectiveOverallStatus === 'in_progress' ? 'IN PROGRESS' : 'PENDING';
        
        // Map overall_status to CSS class (pass, fail, in_progress, pending)
        const statusClass = effectiveOverallStatus === 'ready' ? 'pass' : 
                           effectiveOverallStatus === 'needs_attention' ? 'fail' :
                           effectiveOverallStatus === 'in_progress' ? 'in_progress' : 'pending';
        
        // Check if module can be skipped (only modules with no executed items)
        const canSkip = stats.executed === 0;
        // Skip Module button removed from status cards - only shown in details
        
        html += `
            <div class='module-card status-${statusClass}'>
                <div class='module-card-header'>
                    <div class='module-card-name'>${module.name}</div>
                    <div style='display:flex; align-items:center; gap:8px;'>
                        <div class='module-card-status ${statusClass}'>${statusLabel}</div>
                    </div>
                </div>
                <div style='font-size:0.85rem; color:#64748b; margin-bottom:0.5rem;'>
                    ${module.category}
                </div>
                <div class='module-card-stats'>
                    <div class='module-card-stat'>
                        <div class='module-card-stat-value'>${passRate}%</div>
                        <div class='module-card-stat-label'>Pass Rate</div>
                    </div>
                    <div class='module-card-stat'>
                        <div class='module-card-stat-value'>${execRate}%</div>
                        <div class='module-card-stat-label'>Executed</div>
                    </div>
                    <div class='module-card-stat'>
                        <div class='module-card-stat-value' style='color:#ef5350;'>${stats.fail}</div>
                        <div class='module-card-stat-label'>Failures</div>
                    </div>
                </div>
            </div>
        `;
    });
    
        console.log('Generated HTML length:', html.length);
        console.log('Number of cards generated:', sortedModules.length);
        console.log('First 200 chars of HTML:', html.substring(0, 200));
        
        if (html) {
            console.log('Starting DOM update...');
            
            // Method 1: Remove all children manually (more reliable than innerHTML)
            while (container.firstChild) {
                container.removeChild(container.firstChild);
            }
            console.log('Container cleared');
            
            // Force style recalculation
            const computedStyle = window.getComputedStyle(container);
            void computedStyle.display;
            console.log('Style recalculated');
            
            // Force layout
            void container.offsetWidth;
            void container.offsetHeight;
            void container.getBoundingClientRect();
            console.log('Layout forced');
            
            // Create a temporary container
            const temp = document.createElement('div');
            temp.innerHTML = html;
            console.log('Temp container created with', temp.children.length, 'children');
            
            // Move all children from temp to actual container
            while (temp.firstChild) {
                container.appendChild(temp.firstChild);
            }
            console.log('Children moved to container');
            
            // Force another layout
            void container.offsetWidth;
            void container.offsetHeight;
            
            // Force repaint by toggling a style
            container.style.display = 'none';
            void container.offsetHeight;
            container.style.display = 'grid';
            
            console.log('Module cards HTML set successfully');
            console.log('Container children count:', container.children.length);
            console.log('Container scrollHeight:', container.scrollHeight);
            console.log('Container clientHeight:', container.clientHeight);
        } else {
            console.log('No HTML generated - showing empty state');
            // Show friendly empty state
            container.innerHTML = `
                <div style='grid-column:1/-1; text-align:center; padding:3rem; background:white; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.07);'>
                    <div style='font-size:3rem; margin-bottom:1rem;'>🔍</div>
                    <h3 style='color:#1e293b; margin-bottom:0.5rem;'>No Modules Match Filter</h3>
                    <p style='color:#64748b; font-size:0.95rem;'>
                        Try selecting a different category or check "All Categories"
                    </p>
                </div>
            `;
        }
        
        console.log('=== updateModuleCardsFiltered END ===');
    } catch (error) {
        console.error('❌ ERROR in updateModuleCardsFiltered:', error);
        console.error('Error stack:', error.stack);
        
        // Show error message to user
        const container = document.getElementById('module-cards-container');
        if (container) {
            container.innerHTML = `
                <div style='grid-column:1/-1; text-align:center; padding:3rem; background:#fee; border:2px solid #f00; border-radius:12px;'>
                    <div style='font-size:3rem; margin-bottom:1rem;'>⚠️</div>
                    <h3 style='color:#c00; margin-bottom:0.5rem;'>Error Updating Module Cards</h3>
                    <p style='color:#666; font-size:0.95rem;'>${error.message}</p>
                    <p style='color:#999; font-size:0.85rem; font-family:monospace; margin-top:1rem;'>Check console for details</p>
                </div>
            `;
        }
    }
}

// Setup module sort
function setupModuleSort() {
    const sortSelect = document.getElementById('module-sort');
    if (sortSelect) {
        console.log('Module sort dropdown found, current value:', sortSelect.value);
        sortSelect.addEventListener('change', (e) => {
            try {
                const sortBy = e.target.value;
                console.log('=== Sort changed to:', sortBy, '===');
                console.log('Event triggered at:', Date.now());
                
                const categoryFilter = document.getElementById('category-filter');
                const category = categoryFilter ? categoryFilter.value : 'all';
                console.log('Current category filter:', category);
                
                // Get container reference
                const container = document.getElementById('module-cards-container');
                console.log('Container before update:', container.children.length, 'children');
                
                // Multiple animation frames for maximum compatibility
                requestAnimationFrame(() => {
                    console.log('Frame 1: Starting update');
                    
                    requestAnimationFrame(() => {
                        console.log('Frame 2: Executing update');
                        
                        if (category === 'all') {
                            updateModuleCards(sortBy);
                        } else {
                            const filteredModules = MODULES_DATA.filter(m => m.category === category);
                            updateModuleCardsFiltered(filteredModules, sortBy);
                        }
                        
                        requestAnimationFrame(() => {
                            console.log('Frame 3: Post-update');
                            console.log('Container after update:', container.children.length, 'children');
                            
                            // Force visibility check
                            const firstCard = container.querySelector('.module-card');
                            if (firstCard) {
                                console.log('First card visible:', firstCard.offsetHeight > 0);
                                console.log('First card name:', firstCard.querySelector('.module-card-name')?.textContent);
                            }
                            
                            requestAnimationFrame(() => {
                                console.log('Frame 4: Final render check');
                                console.log('Sort change completed and rendered successfully');
                                
                                // Scroll to module section to show the update
                                const moduleSection = document.getElementById('module-status-section');
                                if (moduleSection) {
                                    moduleSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                                }
                            });
                        });
                    });
                });
            } catch (error) {
                console.error('❌ ERROR in sort change handler:', error);
                console.error('Error stack:', error.stack);
                showMessageModal('Sort Error', 'Error updating sort: ' + error.message + '\\n\\nCheck console for details.');
            }
        });
        console.log('Module sort event listener attached successfully');
    } else {
        console.error('Module sort dropdown NOT found!');
    }
}

function createCharts() {
    console.log('Creating charts (pure CSS version)...');
    createSectionChart();
    createProgressChart();
    console.log('Charts created');
}

function createSectionChart() {
    console.log('Creating section chart (CSS version)...');
    const container = document.getElementById('sectionChart');
    if (!container) {
        console.error('Section chart container not found!');
        return;
    }
    
    const statusCounts = { pass: 0, partial: 0, fail: 0, pending: 0 };
    MODULES_DATA.forEach(module => {
        statusCounts[module.status] = (statusCounts[module.status] || 0) + 1;
    });
    console.log('Status counts:', statusCounts);
    
    const total = MODULES_DATA.length;
    const passPercent = Math.round((statusCounts.pass / total) * 100);
    const partialPercent = Math.round((statusCounts.partial / total) * 100);
    const failPercent = Math.round((statusCounts.fail / total) * 100);
    const pendingPercent = 100 - passPercent - partialPercent - failPercent;
    
    container.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:center; gap:2.5rem; padding:2rem; min-height:280px;">
            <!-- Left: Ring Chart -->
            <div style="position:relative; width:160px; height:160px; flex-shrink:0;">
                <svg width="160" height="160" style="transform:rotate(-90deg);">
                    ${statusCounts.pass > 0 ? `
                    <circle cx="80" cy="80" r="60" fill="none" stroke="#10b981" stroke-width="32"
                            stroke-dasharray="${(statusCounts.pass/total)*188.4} 188.4"
                            stroke-dashoffset="0"/>
                    ` : ''}
                    ${statusCounts.partial > 0 ? `
                    <circle cx="80" cy="80" r="60" fill="none" stroke="#f59e0b" stroke-width="32"
                            stroke-dasharray="${(statusCounts.partial/total)*188.4} 188.4"
                            stroke-dashoffset="${-(statusCounts.pass/total)*188.4}"/>
                    ` : ''}
                    ${statusCounts.fail > 0 ? `
                    <circle cx="80" cy="80" r="60" fill="none" stroke="#ef4444" stroke-width="32"
                            stroke-dasharray="${(statusCounts.fail/total)*188.4} 188.4"
                            stroke-dashoffset="${-((statusCounts.pass+statusCounts.partial)/total)*188.4}"/>
                    ` : ''}
                    ${statusCounts.pending > 0 ? `
                    <circle cx="80" cy="80" r="60" fill="none" stroke="#cbd5e1" stroke-width="32"
                            stroke-dasharray="${(statusCounts.pending/total)*188.4} 188.4"
                            stroke-dashoffset="${-((statusCounts.pass+statusCounts.partial+statusCounts.fail)/total)*188.4}"/>
                    ` : ''}
                    <circle cx="80" cy="80" r="44" fill="white"/>
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;">
                    <div style="font-size:2.2rem; font-weight:700; color:#0f172a;">${total}</div>
                    <div style="font-size:0.8rem; color:#64748b; font-weight:600; letter-spacing:0.05em;">MODULES</div>
                </div>
            </div>
            
            <!-- Right: Stats Table -->
            <div style="flex:1; min-width:220px;">
                <table class="chart-stats-table" style="width:100%; border-collapse:collapse; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
                    <thead style="background:#f8fafc !important;">
                        <tr style="background:#f8fafc !important; border-bottom:1px solid #e2e8f0;">
                            <th style="text-align:left; padding:0.75rem 0; color:#64748b !important; font-size:0.75rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; background:#f8fafc !important;">STATUS</th>
                            <th style="text-align:right; padding:0.75rem 0; color:#64748b !important; font-size:0.75rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; background:#f8fafc !important;">COUNT</th>
                            <th style="text-align:right; padding:0.75rem 0; color:#64748b !important; font-size:0.75rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; background:#f8fafc !important;">PERCENT</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom:1px solid #e2e8f0;">
                            <td style="padding:0.85rem 0;">
                                <div style="display:flex; align-items:center; gap:0.6rem;">
                                    <div style="width:14px; height:14px; background:#10b981; border-radius:3px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"></div>
                                    <span style="color:#0f172a; font-size:0.95rem; font-weight:600;">Pass</span>
                                </div>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${statusCounts.pass}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:600;">${passPercent}%</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e2e8f0;">
                            <td style="padding:0.85rem 0;">
                                <div style="display:flex; align-items:center; gap:0.6rem;">
                                    <div style="width:14px; height:14px; background:#ef4444; border-radius:3px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"></div>
                                    <span style="color:#0f172a; font-size:0.95rem; font-weight:600;">Failed</span>
                                </div>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${statusCounts.fail}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:600;">${failPercent}%</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e2e8f0;">
                            <td style="padding:0.85rem 0;">
                                <div style="display:flex; align-items:center; gap:0.6rem;">
                                    <div style="width:14px; height:14px; background:#94a3b8; border-radius:3px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"></div>
                                    <span style="color:#0f172a; font-size:0.95rem; font-weight:600;">Not Started</span>
                                </div>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${statusCounts.pending}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:600;">${pendingPercent}%</td>
                        </tr>
                        <tr style="border-top:2px solid #cbd5e1;">
                            <td style="padding:0.85rem 0;">
                                <span style="color:#64748b; font-size:0.9rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Total</span>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${total}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:700;">100%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    console.log('Section chart created successfully (CSS version)');
}

function createProgressChart() {
    console.log('Creating progress chart (CSS version)...');
    const container = document.getElementById('progressChart');
    if (!container) {
        console.error('Progress chart container not found!');
        return;
    }
    console.log('Overall stats:', OVERALL_STATS);
    
    const total = OVERALL_STATS.total;
    const passPercent = total > 0 ? Math.round((OVERALL_STATS.pass / total) * 100) : 0;
    const failPercent = total > 0 ? Math.round((OVERALL_STATS.fail / total) * 100) : 0;
    const pendingPercent = total > 0 ? 100 - passPercent - failPercent : 0;
    
    const circumference = 251.2; // 2 * PI * 40 (radius)
    
    // Build legend - only show non-zero items
    let legendHTML = '';
    const legendItems = [];
    
    if (OVERALL_STATS.pass > 0) {
        legendItems.push(`
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="width:16px; height:16px; background:#4caf50; border-radius:3px;"></div>
                <span style="font-size:0.9rem; color:#1e293b; font-weight:500;">Pass: ${OVERALL_STATS.pass} (${passPercent}%)</span>
            </div>
        `);
    }
    if (OVERALL_STATS.fail > 0) {
        legendItems.push(`
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="width:16px; height:16px; background:#ef5350; border-radius:3px;"></div>
                <span style="font-size:0.9rem; color:#1e293b; font-weight:500;">Fail: ${OVERALL_STATS.fail} (${failPercent}%)</span>
            </div>
        `);
    }
    if (OVERALL_STATS.pending > 0) {
        legendItems.push(`
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="width:16px; height:16px; background:#9e9e9e; border-radius:3px;"></div>
                <span style="font-size:0.9rem; color:#1e293b; font-weight:500;">Pending: ${OVERALL_STATS.pending} (${pendingPercent}%)</span>
            </div>
        `);
    }
    
    legendHTML = legendItems.length > 0 ? legendItems.join('') : 
        '<div style="color:#64748b; font-size:0.9rem;">No data</div>';
    
    container.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:center; gap:2.5rem; padding:2rem; min-height:280px;">
            <!-- Left: Ring Chart -->
            <div style="position:relative; width:160px; height:160px; flex-shrink:0;">
                <svg width="160" height="160" style="transform:rotate(-90deg);">
                    ${OVERALL_STATS.pass > 0 ? `
                    <circle cx="80" cy="80" r="60" fill="none" stroke="#10b981" stroke-width="32"
                            stroke-dasharray="${(OVERALL_STATS.pass/total)*188.4} 188.4"
                            stroke-dashoffset="0"/>
                    ` : ''}
                    ${OVERALL_STATS.fail > 0 ? `
                    <circle cx="80" cy="80" r="60" fill="none" stroke="#ef4444" stroke-width="32"
                            stroke-dasharray="${(OVERALL_STATS.fail/total)*188.4} 188.4"
                            stroke-dashoffset="${-(OVERALL_STATS.pass/total)*188.4}"/>
                    ` : ''}
                    ${OVERALL_STATS.pending > 0 ? `
                    <circle cx="80" cy="80" r="60" fill="none" stroke="#cbd5e1" stroke-width="32"
                            stroke-dasharray="${(OVERALL_STATS.pending/total)*188.4} 188.4"
                            stroke-dashoffset="${-((OVERALL_STATS.pass+OVERALL_STATS.fail)/total)*188.4}"/>
                    ` : ''}
                    <circle cx="80" cy="80" r="44" fill="white"/>
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;">
                    <div style="font-size:2.2rem; font-weight:700; color:#0f172a;">${passPercent}%</div>
                    <div style="font-size:0.75rem; color:#64748b; font-weight:600; letter-spacing:0.05em;">PASS RATE</div>
                </div>
            </div>
            
            <!-- Right: Stats Table -->
            <div style="flex:1; min-width:220px;">
                <table class="chart-stats-table" style="width:100%; border-collapse:collapse; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
                    <thead style="background:#f8fafc !important;">
                        <tr style="background:#f8fafc !important; border-bottom:1px solid #e2e8f0;">
                            <th style="text-align:left; padding:0.75rem 0; color:#64748b !important; font-size:0.75rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; background:#f8fafc !important;">STATUS</th>
                            <th style="text-align:right; padding:0.75rem 0; color:#64748b !important; font-size:0.75rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; background:#f8fafc !important;">COUNT</th>
                            <th style="text-align:right; padding:0.75rem 0; color:#64748b !important; font-size:0.75rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; background:#f8fafc !important;">PERCENT</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom:1px solid #e2e8f0;">
                            <td style="padding:0.85rem 0;">
                                <div style="display:flex; align-items:center; gap:0.6rem;">
                                    <div style="width:14px; height:14px; background:#10b981; border-radius:3px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"></div>
                                    <span style="color:#0f172a; font-size:0.95rem; font-weight:600;">Pass</span>
                                </div>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${OVERALL_STATS.pass}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:600;">${passPercent}%</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e2e8f0;">
                            <td style="padding:0.85rem 0;">
                                <div style="display:flex; align-items:center; gap:0.6rem;">
                                    <div style="width:14px; height:14px; background:#ef4444; border-radius:3px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"></div>
                                    <span style="color:#0f172a; font-size:0.95rem; font-weight:600;">Fail</span>
                                </div>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${OVERALL_STATS.fail}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:600;">${failPercent}%</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e2e8f0;">
                            <td style="padding:0.85rem 0;">
                                <div style="display:flex; align-items:center; gap:0.6rem;">
                                    <div style="width:14px; height:14px; background:#94a3b8; border-radius:3px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"></div>
                                    <span style="color:#0f172a; font-size:0.95rem; font-weight:600;">Pending</span>
                                </div>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${OVERALL_STATS.pending}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:600;">${pendingPercent}%</td>
                        </tr>
                        <tr style="border-top:2px solid #cbd5e1;">
                            <td style="padding:0.85rem 0;">
                                <span style="color:#64748b; font-size:0.9rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Total</span>
                            </td>
                            <td style="text-align:right; padding:0.85rem 0; color:#0f172a; font-size:1rem; font-weight:700;">${total}</td>
                            <td style="text-align:right; padding:0.85rem 0; color:#475569; font-size:0.95rem; font-weight:700;">100%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    console.log('Progress chart created successfully (CSS version)');
}

// Initialize issues tab
function initIssues() {
    console.log('Initializing issues tab...');
    console.log('ISSUES_DATA:', ISSUES_DATA);
    populateItemDistribution();
    console.log('Item distribution populated');
    populateFailuresTable();
    console.log('Failures table populated');
    populateWarningsTable();
    console.log('Warnings table populated');
    populateWaiversTable();
    console.log('Waivers table populated');
    setupSearchFunctionality();
    console.log('Search functionality set up');
    makeTablesSortable();
    console.log('Tables made sortable');
}

// Setup search functionality for all tables
function setupSearchFunctionality() {
    // Failures search
    const failuresSearch = document.getElementById('failures-search');
    if (failuresSearch) {
        failuresSearch.addEventListener('input', (e) => {
            filterTable('failures-table', e.target.value);
        });
    }
    
    // Warnings search
    const warningsSearch = document.getElementById('warnings-search');
    if (warningsSearch) {
        warningsSearch.addEventListener('input', (e) => {
            filterTable('warnings-table', e.target.value);
        });
    }
    
    // Waivers search
    const waiversSearch = document.getElementById('waivers-search');
    if (waiversSearch) {
        waiversSearch.addEventListener('input', (e) => {
            filterTable('waivers-table', e.target.value);
        });
    }
}

// Filter table rows based on search query
function filterTable(tableId, query) {
    const container = document.getElementById(tableId);
    const table = container.querySelector('table');
    
    if (!table) return; // No table exists (empty state)
    
    const rows = table.querySelectorAll('tbody tr');
    const searchText = query.toLowerCase().trim();
    
    let visibleCount = 0;
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (searchText === '' || text.includes(searchText)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Show "no results" message if needed
    const existingMsg = container.querySelector('.no-results-message');
    if (existingMsg) {
        existingMsg.remove();
    }
    
    if (visibleCount === 0 && searchText !== '') {
        const noResultsMsg = document.createElement('div');
        noResultsMsg.className = 'no-results-message';
        noResultsMsg.style.cssText = 'text-align:center; padding:2rem; color:#64748b; background:#f8fafc; border-radius:8px; margin-top:1rem;';
        noResultsMsg.innerHTML = `
            <div style="font-size:2rem; margin-bottom:0.5rem;">🔍</div>
            <p style="font-size:1.1rem; font-weight:600; margin-bottom:0.25rem;">No matching results found</p>
            <p style="font-size:0.9rem;">Try different keywords</p>
        `;
        container.appendChild(noResultsMsg);
    }
}

// Make all tables sortable
function makeTablesSortable() {
    const tableContainers = ['failures-table', 'warnings-table', 'waivers-table'];
    
    tableContainers.forEach(containerId => {
        const container = document.getElementById(containerId);
        const table = container.querySelector('table');
        
        if (!table) return; // No table exists (empty state)
        
        const headers = table.querySelectorAll('thead th');
        headers.forEach((header, columnIndex) => {
            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            header.title = 'Click to sort';
            header.innerHTML += ' <span style="opacity:0.5; font-size:0.8em;">⇅</span>';
            
            let ascending = true;
            header.addEventListener('click', () => {
                sortTable(table, columnIndex, ascending);
                ascending = !ascending;
                
                // Update sort indicator
                headers.forEach((h, idx) => {
                    const indicator = h.querySelector('span');
                    if (idx === columnIndex) {
                        indicator.textContent = ascending ? '⇅' : (ascending ? '▲' : '▼');
                        indicator.style.opacity = '1';
                    } else {
                        indicator.textContent = '⇅';
                        indicator.style.opacity = '0.5';
                    }
                });
            });
        });
    });
}

// Sort table by column
function sortTable(table, columnIndex, ascending) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return ascending ? 
            aValue.localeCompare(bValue, 'zh-CN') : 
            bValue.localeCompare(aValue, 'zh-CN');
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// Populate Item ID Distribution Overview
function populateItemDistribution() {
    const container = document.getElementById('item-distribution-grid');
    if (!container) return;
    
    // Collect all unique item IDs across all issue types
    const itemIdStats = {};
    
    // Process failures
    ISSUES_DATA.failures.forEach(f => {
        const key = f.item_id;
        if (!itemIdStats[key]) {
            itemIdStats[key] = { failures: 0, warnings: 0, waivers: 0 };
        }
        itemIdStats[key].failures += 1;
    });
    
    // Process warnings
    ISSUES_DATA.warnings.forEach(w => {
        const key = w.item_id;
        if (!itemIdStats[key]) {
            itemIdStats[key] = { failures: 0, warnings: 0, waivers: 0 };
        }
        itemIdStats[key].warnings += 1;
    });
    
    // Process waivers
    ISSUES_DATA.waivers.forEach(w => {
        const key = w.item_id;
        if (!itemIdStats[key]) {
            itemIdStats[key] = { failures: 0, warnings: 0, waivers: 0 };
        }
        itemIdStats[key].waivers += 1;
    });
    
    // Sort by total issues (descending)
    const sortedItems = Object.entries(itemIdStats)
        .map(([id, stats]) => ({
            id,
            ...stats,
            total: stats.failures + stats.warnings + stats.waivers
        }))
        .sort((a, b) => b.total - a.total);
    
    if (sortedItems.length === 0) {
        container.innerHTML = `
            <div style='text-align:center; padding:2rem; color:#64748b;'>
                <div style='font-size:3rem; margin-bottom:0.5rem;'>✨</div>
                <p style='font-size:1.1rem; font-weight:600;'>No Issues Found</p>
                <p style='font-size:0.9rem; opacity:0.8;'>All items have passed checks</p>
            </div>
        `;
        return;
    }
    
    // Create table
    let html = `
        <table style='width:100%; border-collapse:collapse; background:white; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.1);'>
            <thead>
                <tr style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);'>
                    <th style='padding:0.75rem 1rem; text-align:left; color:white; font-weight:600; font-size:0.9rem;'>Item ID</th>
                    <th style='padding:0.75rem 1rem; text-align:center; color:white; font-weight:600; font-size:0.9rem;'>🔴 Failures</th>
                    <th style='padding:0.75rem 1rem; text-align:center; color:white; font-weight:600; font-size:0.9rem;'>⚠️ Warnings</th>
                    <th style='padding:0.75rem 1rem; text-align:center; color:white; font-weight:600; font-size:0.9rem;'>📋 Waivers</th>
                    <th style='padding:0.75rem 1rem; text-align:center; color:white; font-weight:600; font-size:0.9rem;'>Total</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    sortedItems.forEach((item, idx) => {
        const rowBg = idx % 2 === 0 ? '#ffffff' : '#f8fafc';
        html += `
            <tr style='background:${rowBg}; transition:background 0.2s;' 
                onmouseover='this.style.background="#f1f5f9"'
                onmouseout='this.style.background="${rowBg}"'>
                <td style='padding:0.75rem 1rem; font-family:monospace; font-weight:600; color:#1e293b; border-bottom:1px solid #e2e8f0;'>${item.id}</td>
                <td style='padding:0.75rem 1rem; text-align:center; font-weight:700; color:#ef4444; border-bottom:1px solid #e2e8f0;'>${item.failures || '-'}</td>
                <td style='padding:0.75rem 1rem; text-align:center; font-weight:700; color:#f59e0b; border-bottom:1px solid #e2e8f0;'>${item.warnings || '-'}</td>
                <td style='padding:0.75rem 1rem; text-align:center; font-weight:700; color:#3b82f6; border-bottom:1px solid #e2e8f0;'>${item.waivers || '-'}</td>
                <td style='padding:0.75rem 1rem; text-align:center; font-weight:700; color:#475569; border-bottom:1px solid #e2e8f0;'>${item.total}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

// Close preview window
function closePreview() {
    // Try multiple methods to close the window
    // Method 1: Try window.close() (works if opened by script)
    if (window.close()) {
        return;
    }
    
    // Method 2: Try to close with opener
    if (window.opener) {
        window.close();
        return;
    }
    
    // Method 3: For Firefox, use about:blank
    try {
        window.location.href = 'about:blank';
        window.close();
    } catch (e) {
        // Method 4: If all else fails, show message
        showMessageModal('Close Preview', 'Please close this tab manually (Ctrl+W or Cmd+W)');
    }
}

// Toggle collapsible table group
function toggleTableGroup(groupId) {
    const headerRow = document.querySelector(`.table-row-header[data-group="${groupId}"]`);
    const detailRows = document.querySelectorAll(`.detail-row[data-group="${groupId}"]`);
    
    if (headerRow) {
        headerRow.classList.toggle('collapsed');
    }
    
    detailRows.forEach(row => {
        row.classList.toggle('collapsed');
    });
}

function populateFailuresTable() {
    console.log('Populating failures table...');
    const container = document.getElementById('failures-table');
    console.log('failures-table container:', container);
    const failures = ISSUES_DATA.failures;
    console.log('failures count:', failures.length);
    
    const countElement = document.getElementById('fail-count');
    console.log('fail-count element:', countElement);
    if (countElement) {
        countElement.textContent = failures.length;
    } else {
        console.error('fail-count element not found!');
    }
    
    if (failures.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:4rem 2rem; background:linear-gradient(135deg, #d4f4dd 0%, #b9f5d0 100%); border-radius:12px; border:2px solid #4caf50;">
                <div style="font-size:4rem; margin-bottom:1rem;">🎉</div>
                <h3 style="color:#2e7d32; font-size:1.5rem; margin-bottom:0.5rem; font-weight:700;">Excellent!</h3>
                <p style="color:#558b5c; font-size:1.1rem;">All checks passed, no failures found</p>
                <p style="color:#558b5c; font-size:0.9rem; margin-top:1rem; opacity:0.8;">✓ All required checks completed and passed</p>
            </div>
        `;
        return;
    }
    
    // Group failures by item_id for better display
    const groupedFailures = {};
    failures.forEach(f => {
        const key = `${f.section}::${f.item_id}`;
        if (!groupedFailures[key]) {
            groupedFailures[key] = {
                section: f.section,
                item_id: f.item_id,
                description: f.description,
                failures: [],
                total_count: 0
            };
        }
        groupedFailures[key].failures.push(f.details);
        // Add occurrence count (default to 1 if not specified)
        groupedFailures[key].total_count += (f.occurrence || 1);
    });
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th style="width:40px;"></th>
                    <th>Section</th>
                    <th>Item ID</th>
                    <th>Description</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let groupIndex = 0;
    Object.values(groupedFailures).forEach(group => {
        const failureCount = group.failures.length;
        const groupId = `failure-group-${groupIndex}`;
        
        // Summary of first failure for preview
        const firstFailure = group.failures[0];
        let previewText = '';
        if (firstFailure.detail) {
            previewText = firstFailure.detail;
        } else {
            const firstEntry = Object.entries(firstFailure).find(([k, v]) => k !== 'occurrence' && v);
            if (firstEntry) previewText = String(firstEntry[1]).substring(0, 50);
        }
        
        // Header row (always visible, clickable)
        html += `
            <tr class='table-row-header collapsed' data-group='${groupId}' onclick='toggleTableGroup("${groupId}")'>
                <td style="text-align:center;">
                    <span class='expand-icon'>▼</span>
                </td>
                <td class='section-cell'>${group.section}</td>
                <td style="font-family:monospace; font-weight:600;">${group.item_id}</td>
                <td>
                    ${group.description}
                    <span class='item-summary'>${previewText ? '— ' + previewText + (previewText.length >= 50 ? '...' : '') : ''}</span>
                </td>
                <td style="text-align:center; font-weight:700; color:#ef5350;">${group.total_count}</td>
            </tr>
        `;
        
        // Detail rows (hidden by default)
        group.failures.forEach((failure, idx) => {
            const detailsStr = Object.entries(failure)
                .filter(([k, v]) => k !== 'occurrence' && v !== undefined && v !== null)
                .map(([k, v]) => {
                    if (k === 'detail') return `<strong>${v}</strong>`;
                    if (k === 'reason') return `<em style="color:#64748b;">${v}</em>`;
                    if (k === 'index') return `#${v}`;
                    return `${k}: ${v}`;
                })
                .join('<br>');
            
            html += `
                <tr class='detail-row collapsed' data-group='${groupId}'>
                    <td></td>
                    <td colspan='4' style="font-size:0.9rem; line-height:1.6; padding-left:2.5rem; background:#fef2f2;">
                        <strong style="color:#dc2626;">Detail ${idx + 1}:</strong><br>
                        ${detailsStr}
                    </td>
                </tr>
            `;
        });
        
        groupIndex++;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function populateWarningsTable() {
    const container = document.getElementById('warnings-table');
    const warnings = ISSUES_DATA.warnings;
    
    document.getElementById('warn-count').textContent = warnings.length;
    
    if (warnings.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:4rem 2rem; background:linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-radius:12px; border:2px solid #f59e0b;">
                <div style="font-size:4rem; margin-bottom:1rem;">✨</div>
                <h3 style="color:#d97706; font-size:1.5rem; margin-bottom:0.5rem; font-weight:700;">Perfect!</h3>
                <p style="color:#d97706; font-size:1.1rem;">No warnings that need attention</p>
                <p style="color:#d97706; font-size:0.9rem; margin-top:1rem; opacity:0.8;">✓ All check results are good</p>
            </div>
        `;
        return;
    }
    
    // Group warnings by item_id (similar to failures)
    const groupedWarnings = {};
    warnings.forEach(w => {
        const key = `${w.section}::${w.item_id}`;
        if (!groupedWarnings[key]) {
            groupedWarnings[key] = {
                section: w.section,
                item_id: w.item_id,
                description: w.description,
                warnings: [],
                total_count: 1
            };
        } else {
            groupedWarnings[key].total_count += 1;
        }
        groupedWarnings[key].warnings.push({
            warning: w.warning,
            details: w.details || {}
        });
    });
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th style="width:40px;"></th>
                    <th>Section</th>
                    <th>Item ID</th>
                    <th>Description</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let groupIndex = 0;
    Object.values(groupedWarnings).forEach(group => {
        const warningCount = group.warnings.length;
        const groupId = `warning-group-${groupIndex}`;
        
        // Preview of first warning
        const firstWarning = group.warnings[0];
        const previewText = firstWarning.warning ? firstWarning.warning.substring(0, 50) : '';
        
        // Header row (always visible, clickable)
        html += `
            <tr class='table-row-header collapsed' data-group='${groupId}' onclick='toggleTableGroup("${groupId}")'>
                <td style="text-align:center;">
                    <span class='expand-icon'>▼</span>
                </td>
                <td class='section-cell'>${group.section}</td>
                <td style="font-family:monospace; font-weight:600;">${group.item_id}</td>
                <td>
                    ${group.description}
                    <span class='item-summary'>${previewText ? '— ' + previewText + (previewText.length >= 50 ? '...' : '') : ''}</span>
                </td>
                <td style="text-align:center; font-weight:700; color:#d97706;">${group.total_count}</td>
            </tr>
        `;
        
        // Detail rows (hidden by default)
        group.warnings.forEach((warning, idx) => {
            let detailsStr = `<strong>${warning.warning}</strong>`;
            if (warning.details && Object.keys(warning.details).length > 0) {
                const detailsParts = Object.entries(warning.details)
                    .filter(([k, v]) => v !== undefined && v !== null)
                    .map(([k, v]) => `${k}: ${v}`);
                if (detailsParts.length > 0) {
                    detailsStr += '<br><em style="color:#64748b;">' + detailsParts.join(', ') + '</em>';
                }
            }
            
            html += `
                <tr class='detail-row collapsed' data-group='${groupId}'>
                    <td></td>
                    <td colspan='4' style="font-size:0.9rem; line-height:1.6; padding-left:2.5rem; background:#fffbeb;">
                        <strong style="color:#d97706;">Warning ${idx + 1}:</strong><br>
                        ${detailsStr}
                    </td>
                </tr>
            `;
        });
        
        groupIndex++;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function populateWaiversTable() {
    const container = document.getElementById('waivers-table');
    const waivers = ISSUES_DATA.waivers;
    
    document.getElementById('waiver-count').textContent = waivers.length;
    
    if (waivers.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:4rem 2rem; background:linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius:12px; border:2px solid #3b82f6;">
                <div style="font-size:4rem; margin-bottom:1rem;">📋</div>
                <h3 style="color:#2563eb; font-size:1.5rem; margin-bottom:0.5rem; font-weight:700;">No Waivers</h3>
                <p style="color:#2563eb; font-size:1.1rem;">No waivers are currently defined</p>
                <p style="color:#2563eb; font-size:0.9rem; margin-top:1rem; opacity:0.8;">All checks executed per standard procedures</p>
            </div>
        `;
        return;
    }
    
    // Group waivers by item_id (similar to failures)
    const groupedWaivers = {};
    waivers.forEach(w => {
        const key = `${w.section}::${w.item_id}`;
        if (!groupedWaivers[key]) {
            groupedWaivers[key] = {
                section: w.section,
                item_id: w.item_id,
                description: w.description,
                waivers: [],
                total_count: 1
            };
        } else {
            groupedWaivers[key].total_count += 1;
        }
        groupedWaivers[key].waivers.push({
            waiver: w.waiver,
            reason: w.reason || '',
            details: w.details || {}
        });
    });
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th style="width:40px;"></th>
                    <th>Section</th>
                    <th>Item ID</th>
                    <th>Description</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let groupIndex = 0;
    Object.values(groupedWaivers).forEach(group => {
        const groupId = `waiver-group-${groupIndex}`;
        const previewText = group.waivers[0].waiver.substring(0, 50);
        
        // Header row (always visible)
        html += `
            <tr class='table-row-header collapsed' data-group='${groupId}' onclick='toggleTableGroup("${groupId}")'>
                <td style="text-align:center;">
                    <span class='expand-icon'>▼</span>
                </td>
                <td class='section-cell'>${group.section}</td>
                <td style="font-family:monospace; font-weight:600;">${group.item_id}</td>
                <td>
                    ${group.description}
                    <span class='item-summary'>${previewText ? '— ' + previewText + '...' : ''}</span>
                </td>
                <td style="text-align:center; font-weight:700; color:#2563eb;">${group.total_count}</td>
            </tr>
        `;
        
        // Detail rows (hidden by default)
        group.waivers.forEach((waiver, idx) => {
            let detailsStr = `<strong>${waiver.waiver}</strong>`;
            if (waiver.reason) {
                detailsStr += `<br><em style="color:#64748b;">Reason: ${waiver.reason}</em>`;
            }
            if (waiver.details && Object.keys(waiver.details).length > 0) {
                const detailsParts = Object.entries(waiver.details)
                    .filter(([k, v]) => v !== undefined && v !== null)
                    .map(([k, v]) => `${k}: ${v}`);
                if (detailsParts.length > 0) {
                    detailsStr += '<br><span style="color:#64748b; font-size:0.85rem;">' + detailsParts.join(', ') + '</span>';
                }
            }
            
            html += `
                <tr class='detail-row collapsed' data-group='${groupId}'>
                    <td></td>
                    <td colspan='4' style="font-size:0.9rem; line-height:1.6; padding-left:2.5rem; background:#eff6ff;">
                        <strong style="color:#2563eb;">Waiver ${idx + 1}:</strong><br>
                        ${detailsStr}
                    </td>
                </tr>
            `;
        });
        
        groupIndex++;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// Populate approved waivers table (for Waivers tab)
// Natural sorting function for item IDs (handles formats like IMP-1-0-0-00, IMP-10-0-0-00)
function naturalSortItemId(a, b) {
    // Split item IDs into parts separated by dashes
    const aParts = a.split('-');
    const bParts = b.split('-');
    
    // Compare each part numerically if possible, otherwise alphabetically
    for (let i = 0; i < Math.min(aParts.length, bParts.length); i++) {
        const aNum = parseInt(aParts[i]);
        const bNum = parseInt(bParts[i]);
        
        // Both are numbers - compare numerically
        if (!isNaN(aNum) && !isNaN(bNum)) {
            if (aNum !== bNum) return aNum - bNum;
        } else {
            // At least one is not a number - compare alphabetically
            if (aParts[i] !== bParts[i]) {
                return aParts[i].localeCompare(bParts[i]);
            }
        }
    }
    
    // If all parts are equal, shorter ID comes first
    return aParts.length - bParts.length;
}

function populateApprovedWaiversTable() {
    const container = document.getElementById('approved-waivers-table');
    const approvedWaivers = ISSUES_DATA.approved_waivers || [];
    const waivedAsInfo = ISSUES_DATA.waived_as_info || [];
    
    // Group waivers by item_id first to count unique items
    const uniqueItems = new Set();
    approvedWaivers.forEach(w => {
        uniqueItems.add(`${w.section}::${w.item_id}`);
    });
    waivedAsInfo.forEach(w => {
        uniqueItems.add(`${w.section}::${w.item_id}`);
    });
    
    // Set count to number of unique items, not total count
    const approvedCount = uniqueItems.size;
    document.getElementById('approved-waiver-count').textContent = approvedCount;
    
    // Update sub-tab button with count
    const approvedTabBtn = document.querySelector('.tab-button[data-subtab="approved"]');
    if (approvedTabBtn) {
        approvedTabBtn.innerHTML = `✓ Approved <span style="background:#e3f2fd; color:#1565c0; padding:2px 8px; border-radius:12px; font-size:0.85em; margin-left:4px;">${approvedCount}</span>`;
    }
    
    if (approvedWaivers.length === 0 && waivedAsInfo.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:4rem 2rem; background:linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius:12px; border:2px solid #3b82f6;">
                <div style="font-size:4rem; margin-bottom:1rem;">📋</div>
                <h3 style="color:#2563eb; font-size:1.5rem; margin-bottom:0.5rem; font-weight:700;">No Approved Waivers</h3>
                <p style="color:#2563eb; font-size:1.1rem;">No waivers are currently approved in the database</p>
                <p style="color:#2563eb; font-size:0.9rem; margin-top:1rem; opacity:0.8;">All checks executed per standard procedures</p>
            </div>
        `;
        return;
    }
    
    // Group waivers by item_id (separately tracking approved and info waivers)
    const groupedWaivers = {};
    
    // Process approved waivers
    approvedWaivers.forEach(w => {
        const key = `${w.section}::${w.item_id}`;
        if (!groupedWaivers[key]) {
            groupedWaivers[key] = {
                section: w.section,
                item_id: w.item_id,
                description: w.description,
                approvedWaivers: [],
                infoWaivers: []
            };
        }
        groupedWaivers[key].approvedWaivers.push({
            waiver: w.waiver,
            reason: w.reason || '',
            details: w.details || {}
        });
    });
    
    // Process waived as info
    waivedAsInfo.forEach(w => {
        const key = `${w.section}::${w.item_id}`;
        if (!groupedWaivers[key]) {
            groupedWaivers[key] = {
                section: w.section,
                item_id: w.item_id,
                description: w.description,
                approvedWaivers: [],
                infoWaivers: []
            };
        }
        groupedWaivers[key].infoWaivers.push({
            waiver: w.waiver,
            reason: w.reason || '',
            details: w.details || {}
        });
    });
    
    // Convert to array and sort by item_id using natural sorting
    const sortedGroups = Object.values(groupedWaivers).sort((a, b) => {
        return naturalSortItemId(a.item_id, b.item_id);
    });
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th style="width:40px;"></th>
                    <th>Section</th>
                    <th>Item ID</th>
                    <th>Description</th>
                    <th>Waiver Info</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let groupIndex = 0;
    sortedGroups.forEach(group => {
        const groupId = `approved-waiver-group-${groupIndex}`;
        const totalCount = group.approvedWaivers.length + group.infoWaivers.length;
        const firstWaiver = group.approvedWaivers[0] || group.infoWaivers[0];
        const previewText = firstWaiver ? firstWaiver.waiver.substring(0, 50) : '';
        
        // Header row (always visible)
        html += `
            <tr class='table-row-header collapsed' data-group='${groupId}' onclick='toggleTableGroup("${groupId}")'>
                <td style="text-align:center;">
                    <span class='expand-icon'>▼</span>
                </td>
                <td class='section-cell'>${group.section}</td>
                <td style="font-family:monospace; font-weight:600;">${group.item_id}</td>
                <td>${group.description}</td>
                <td>
                    <span class='item-summary'>${previewText ? previewText + '...' : ''}</span>
                </td>
                <td style="text-align:center; font-weight:700; color:#2563eb;">${totalCount}</td>
            </tr>
        `;
        
        // Detail rows (hidden by default) - Approved waivers
        // If only 1 approved waiver: no number
        // If multiple (>1) approved waivers: add numbers
        if (group.approvedWaivers.length === 1) {
            // Single approved waiver - no number
            const waiver = group.approvedWaivers[0];
            let detailsStr = `<strong>${waiver.waiver}</strong>`;
            if (waiver.reason) {
                detailsStr += `<br><em style="color:#64748b;">Reason: ${waiver.reason}</em>`;
            }
            if (waiver.details && Object.keys(waiver.details).length > 0) {
                const detailsParts = Object.entries(waiver.details)
                    .filter(([k, v]) => v !== undefined && v !== null)
                    .map(([k, v]) => `${k}: ${v}`);
                if (detailsParts.length > 0) {
                    detailsStr += '<br><span style="color:#64748b; font-size:0.85rem;">' + detailsParts.join(', ') + '</span>';
                }
            }
            
            html += `
                <tr class='detail-row collapsed' data-group='${groupId}'>
                    <td></td>
                    <td colspan='5' style="font-size:0.9rem; line-height:1.6; padding-left:2.5rem; background:#eff6ff;">
                        ${detailsStr}
                    </td>
                </tr>
            `;
        } else {
            // Multiple approved waivers - add numbers
            group.approvedWaivers.forEach((waiver, idx) => {
                let detailsStr = `<strong>${waiver.waiver}</strong>`;
                if (waiver.reason) {
                    detailsStr += `<br><em style="color:#64748b;">Reason: ${waiver.reason}</em>`;
                }
                if (waiver.details && Object.keys(waiver.details).length > 0) {
                    const detailsParts = Object.entries(waiver.details)
                        .filter(([k, v]) => v !== undefined && v !== null)
                        .map(([k, v]) => `${k}: ${v}`);
                    if (detailsParts.length > 0) {
                        detailsStr += '<br><span style="color:#64748b; font-size:0.85rem;">' + detailsParts.join(', ') + '</span>';
                    }
                }
                
                html += `
                    <tr class='detail-row collapsed' data-group='${groupId}'>
                        <td></td>
                        <td colspan='5' style="font-size:0.9rem; line-height:1.6; padding-left:2.5rem; background:#eff6ff;">
                            <strong style="color:#2563eb;">${idx + 1}.</strong><br>
                            ${detailsStr}
                        </td>
                    </tr>
                `;
            });
        }
        
        // Detail rows for info waivers WITH numbers
        group.infoWaivers.forEach((waiver, idx) => {
            let detailsStr = `<strong>${waiver.waiver}</strong>`;
            if (waiver.reason) {
                detailsStr += `<br><em style="color:#64748b;">Reason: ${waiver.reason}</em>`;
            }
            if (waiver.details && Object.keys(waiver.details).length > 0) {
                const detailsParts = Object.entries(waiver.details)
                    .filter(([k, v]) => v !== undefined && v !== null)
                    .map(([k, v]) => `${k}: ${v}`);
                if (detailsParts.length > 0) {
                    detailsStr += '<br><span style="color:#64748b; font-size:0.85rem;">' + detailsParts.join(', ') + '</span>';
                }
            }
            
            html += `
                <tr class='detail-row collapsed' data-group='${groupId}'>
                    <td></td>
                    <td colspan='5' style="font-size:0.9rem; line-height:1.6; padding-left:2.5rem; background:#eff6ff;">
                        <strong style="color:#2563eb;">${idx + 1}.</strong><br>
                        ${detailsStr}
                    </td>
                </tr>
            `;
        });
        
        groupIndex++;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
    
    // Setup search filtering
    const searchInput = document.getElementById('approved-waivers-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = container.querySelectorAll('tr.table-row-header');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const shouldShow = text.includes(searchTerm);
                row.style.display = shouldShow ? '' : 'none';
                
                // Also hide/show associated detail rows
                const groupId = row.dataset.group;
                const detailRows = container.querySelectorAll(`tr.detail-row[data-group="${groupId}"]`);
                detailRows.forEach(dr => {
                    dr.style.display = shouldShow ? '' : 'none';
                });
            });
        });
    }
}

// Populate pending waivers table (for Waivers tab)
function populatePendingWaiversTable() {
    const container = document.getElementById('pending-waivers-table');
    
    // Collect pending waivers from all modules
    const pendingWaivers = [];
    MODULES_DATA.forEach(module => {
        module.items.forEach(item => {
            // Check if item has pending waivers (waiver_applied flag)
            if (item.waiver_applied && item.failures) {
                item.failures.forEach((failure, idx) => {
                    if (failure.waived) {
                        pendingWaivers.push({
                            section: module.name,
                            item_id: item.id,
                            description: item.description,
                            failure_index: idx,
                            failure_detail: failure,
                            waiver_comment: failure.waiver_comment || '',
                            waiver_timestamp: failure.waiver_timestamp || ''
                        });
                    }
                });
            }
        });
    });
    
    // Update count
    const pendingCount = pendingWaivers.length;
    document.getElementById('pending-waiver-count').textContent = pendingCount;
    
    // Update sub-tab button with count
    const pendingTabBtn = document.querySelector('.tab-button[data-subtab="pending"]');
    if (pendingTabBtn) {
        pendingTabBtn.innerHTML = `⏳ Pending <span style="background:#f3e8ff; color:#9333ea; padding:2px 8px; border-radius:12px; font-size:0.85em; margin-left:4px;">${pendingCount}</span>`;
    }
    
    if (pendingWaivers.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:4rem 2rem; background:linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); border-radius:12px; border:2px solid #9333ea;">
                <div style="font-size:4rem; margin-bottom:1rem;">✓</div>
                <h3 style="color:#9333ea; font-size:1.5rem; margin-bottom:0.5rem; font-weight:700;">No Pending Waivers</h3>
                <p style="color:#9333ea; font-size:1.1rem;">All waivers have been approved or none are pending</p>
                <p style="color:#9333ea; font-size:0.9rem; margin-top:1rem; opacity:0.8;">Use "Waive" buttons in Details tab to add pending waivers</p>
            </div>
        `;
        return;
    }
    
    // Group pending waivers by item_id (similar to approved waivers)
    const groupedWaivers = {};
    pendingWaivers.forEach(w => {
        const key = `${w.section}::${w.item_id}`;
        if (!groupedWaivers[key]) {
            groupedWaivers[key] = {
                section: w.section,
                item_id: w.item_id,
                description: w.description,
                waivers: [],
                total_count: 0
            };
        }
        groupedWaivers[key].total_count += 1;
        groupedWaivers[key].waivers.push({
            comment: w.waiver_comment,
            timestamp: w.waiver_timestamp,
            failure_detail: w.failure_detail
        });
    });
    
    // Convert to array and sort by item_id using natural sorting
    const sortedGroups = Object.values(groupedWaivers).sort((a, b) => {
        return naturalSortItemId(a.item_id, b.item_id);
    });
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th style="width:40px;"></th>
                    <th>Section</th>
                    <th>Item ID</th>
                    <th>Description</th>
                    <th>Waiver Info</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let groupIndex = 0;
    sortedGroups.forEach(group => {
        const groupId = `pending-waiver-group-${groupIndex}`;
        const previewText = group.waivers[0].comment.substring(0, 50);
        
        // Header row (always visible)
        html += `
            <tr class='table-row-header collapsed' data-group='${groupId}' onclick='toggleTableGroup("${groupId}")'>
                <td style="text-align:center;">
                    <span class='expand-icon'>▼</span>
                </td>
                <td class='section-cell'>${group.section}</td>
                <td style="font-family:monospace; font-weight:600; color:#9333ea;">${group.item_id}</td>
                <td>${group.description}</td>
                <td>
                    <span class='item-summary' style='color:#9333ea;'>[Pending] ${previewText ? previewText + '...' : ''}</span>
                </td>
                <td style="text-align:center; font-weight:700; color:#9333ea;">${group.total_count}</td>
            </tr>
        `;
        
        // Detail rows (hidden by default)
        group.waivers.forEach((waiver, idx) => {
            let detailsStr = `<strong style='color:#9333ea;'>[Pending]</strong> ${waiver.comment}`;
            if (waiver.timestamp) {
                detailsStr += `<br><em style="color:#a855f7; font-size:0.9rem;">Timestamp: ${waiver.timestamp}</em>`;
            }
            if (waiver.failure_detail && typeof waiver.failure_detail === 'object') {
                const failureText = Object.entries(waiver.failure_detail)
                    .filter(([k, v]) => k !== 'waived' && k !== 'waiver_comment' && k !== 'waiver_timestamp' && v !== null && v !== '')
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ');
                if (failureText) {
                    detailsStr += '<br><span style="color:#64748b; font-size:0.85rem;">Failure: ' + failureText + '</span>';
                }
            }
            
            html += `
                <tr class='detail-row collapsed' data-group='${groupId}'>
                    <td></td>
                    <td colspan="5" style="padding:1rem 1.5rem; background:#faf5ff;">${detailsStr}</td>
                </tr>
            `;
        });
        
        groupIndex++;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
    
    // Setup search filtering for pending waivers
    const searchInput = document.getElementById('pending-waivers-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = container.querySelectorAll('tr.table-row-header');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const shouldShow = text.includes(searchTerm);
                row.style.display = shouldShow ? '' : 'none';
                
                // Also hide/show associated detail rows
                const groupId = row.dataset.group;
                const detailRows = container.querySelectorAll(`tr.detail-row[data-group="${groupId}"]`);
                detailRows.forEach(dr => {
                    dr.style.display = shouldShow ? '' : 'none';
                });
            });
        });
    }
}

// Initialize details tab
function initDetails() {
    populateModuleDetailsTables();
    setupModuleDetailsControls();
}

// Setup expand/collapse toggle button
function setupModuleDetailsControls() {
    const toggleBtn = document.getElementById('toggle-all-sections-btn');
    const toggleIcon = document.getElementById('toggle-icon');
    const toggleText = document.getElementById('toggle-text');
    let isExpanded = false;
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            if (isExpanded) {
                // Collapse all
                document.querySelectorAll('.module-table-header.expanded').forEach(header => {
                    header.click();
                });
                toggleIcon.textContent = '▼';
                toggleText.textContent = 'Expand';
                isExpanded = false;
            } else {
                // Expand all
                document.querySelectorAll('.module-table-header').forEach(header => {
                    if (!header.classList.contains('expanded')) {
                        header.click();
                    }
                });
                toggleIcon.textContent = '▲';
                toggleText.textContent = 'Collapse';
                isExpanded = true;
            }
        });
    }
    
    // Function to apply status filters
    function applyStatusFilters() {
        const showProblemsOnly = document.getElementById('show-problems-only')?.checked || false;
        const showWarningsOnly = document.getElementById('show-warnings-only')?.checked || false;
        
        document.querySelectorAll('.module-table').forEach(table => {
            const tbody = table.querySelector('tbody');
            if (!tbody) return;
            
            const rows = tbody.querySelectorAll('tr');
            let visibleCount = 0;
            
            rows.forEach(row => {
                const isFail = row.classList.contains('status-fail');
                const hasWarnings = row.classList.contains('has-warnings');
                
                // If both filters are off, show all rows
                if (!showProblemsOnly && !showWarningsOnly) {
                    row.style.display = '';
                    visibleCount++;
                }
                // If both filters are on, show problems OR warnings
                else if (showProblemsOnly && showWarningsOnly) {
                    if (isFail || hasWarnings) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                }
                // If only problems filter is on
                else if (showProblemsOnly) {
                    if (isFail) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                }
                // If only warnings filter is on
                else if (showWarningsOnly) {
                    if (hasWarnings) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
            
            // Hide entire module if no rows visible when filter is active
            const anyFilterActive = showProblemsOnly || showWarningsOnly;
            table.style.display = (anyFilterActive && visibleCount === 0) ? 'none' : 'block';
        });
    }
    
    // Setup "Show Problems Only" filter
    const problemsOnlyCheckbox = document.getElementById('show-problems-only');
    if (problemsOnlyCheckbox) {
        problemsOnlyCheckbox.addEventListener('change', applyStatusFilters);
    }
    
    // Setup "Show Warning Only" filter
    const warningsOnlyCheckbox = document.getElementById('show-warnings-only');
    if (warningsOnlyCheckbox) {
        warningsOnlyCheckbox.addEventListener('change', applyStatusFilters);
    }
    
    // Setup collapsible cells
    setupCollapsibleCells();
}

function setupCollapsibleCells() {
    const collapsibleCells = document.querySelectorAll('.collapsible-cell');
    console.log(`Found ${collapsibleCells.length} collapsible cells`);
    
    collapsibleCells.forEach(cell => {
        // Skip if already initialized
        if (cell.dataset.initialized === 'true') {
            return;
        }
        cell.dataset.initialized = 'true';
        
        let clickTimer = null;
        let clickCount = 0;
        
        const handleClick = (e) => {
            e.stopPropagation();
            clickCount++;
            
            if (clickCount === 1) {
                // Single click - toggle expand/collapse
                clickTimer = setTimeout(() => {
                    if (cell.classList.contains('collapsed')) {
                        cell.classList.remove('collapsed');
                        cell.classList.add('expanded');
                    } else {
                        cell.classList.remove('expanded');
                        cell.classList.add('collapsed');
                    }
                    clickCount = 0;
                }, 300);
            } else if (clickCount === 2) {
                // Double click - open modal with detail
                clearTimeout(clickTimer);
                clickCount = 0;
                
                // Get cell type and content
                const cellType = cell.dataset.type || 'detail';
                const cellContent = cell.innerHTML;
                
                // Create and show modal
                showDetailModal(cellType, cellContent);
            }
        };
        
        cell.addEventListener('click', handleClick);
    });
}

function showDetailModal(type, content) {
    // Remove existing modal if any
    const existingModal = document.getElementById('detail-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'detail-modal';
    modal.className = 'detail-modal active';
    
    const titleMap = {
        'waiver': 'Waiver Details',
        'prompt': 'Prompt Details',
        'comment': 'Comment Details',
        'detail': 'Details'
    };
    
    modal.innerHTML = `
        <div class='modal-content' id='modal-content'>
            <div class='modal-header'>
                <h3 class='modal-title'>${titleMap[type] || 'Details'}</h3>
                <button class='modal-close' id='modal-close'>&times;</button>
            </div>
            <div class='modal-body'>${content}</div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close handlers
    const closeBtn = modal.querySelector('#modal-close');
    const modalContent = modal.querySelector('#modal-content');
    
    const closeModal = () => {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 200);
    };
    
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    modalContent.addEventListener('dblclick', (e) => {
        e.stopPropagation();
        closeModal();
    });
}

// Populate module navigation cards
function populateModuleNavCards() {
    const container = document.getElementById('module-nav-cards');
    if (!container) return;
    
    // Filter modules that have been executed (at least 1 item executed)
    const executedModules = MODULES_DATA.filter(m => m.stats && m.stats.executed > 0);
    
    // Sort by module name (natural sorting)
    const sortedModules = executedModules.sort((a, b) => {
        const aPrefix = a.name.split('_')[0];
        const bPrefix = b.name.split('_')[0];
        const aNum = parseFloat(aPrefix);
        const bNum = parseFloat(bPrefix);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return aNum - bNum;
        }
        return a.name.localeCompare(b.name);
    });
    
    let html = '';
    sortedModules.forEach(module => {
        const moduleStatus = module.overall_status || module.status || 'pending';
        let statusColor;
        
        switch(moduleStatus) {
            case 'ready':
                statusColor = '#10b981';
                break;
            case 'needs_attention':
            case 'fail':
                statusColor = '#ef4444';
                break;
            case 'in_progress':
            case 'partial':
                statusColor = '#3b82f6';
                break;
            default:
                statusColor = '#9ca3af';
        }
        
        const passRate = module.stats.total > 0 ? Math.round(module.stats.pass / module.stats.total * 100) : 0;
        
        html += `
            <div class='module-nav-card' 
                 data-module='${module.name}' 
                 onclick='scrollToModule("${module.name}")'
                 style='border-left: 4px solid ${statusColor}; 
                        padding: 0.75rem 1rem; 
                        background: white; 
                        border-radius: 8px; 
                        cursor: pointer; 
                        transition: all 0.2s ease;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);'
                 onmouseover='this.style.boxShadow="0 4px 12px rgba(0,0,0,0.15)"; this.style.transform="translateY(-2px)";'
                 onmouseout='this.style.boxShadow="0 2px 4px rgba(0,0,0,0.1)"; this.style.transform="translateY(0)";'>
                <div style='font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;'>
                    ${module.name.replace(/_/g, ' ')}
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #64748b;'>
                    <span>${module.stats.executed}/${module.stats.total} executed</span>
                    <span style='font-weight: 600; color: ${statusColor};'>${passRate}%</span>
                </div>
            </div>
        `;
    });
    
    if (html === '') {
        html = `
            <div style='grid-column: 1 / -1; text-align: center; padding: 2rem; color: #94a3b8;'>
                <p>No modules have been executed yet.</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Scroll to and expand a specific module
function scrollToModule(moduleName) {
    const moduleElement = document.getElementById('detail-' + moduleName);
    if (!moduleElement) return;
    
    const header = moduleElement.querySelector('.module-table-header');
    const tableContent = moduleElement.querySelector('.table-content');
    
    // Expand the module if collapsed
    if (!header.classList.contains('expanded')) {
        header.classList.add('expanded');
        tableContent.style.display = 'block';
    }
    
    // Smooth scroll to module
    moduleElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Add temporary highlight effect
    moduleElement.style.transition = 'background 0.3s ease';
    moduleElement.style.background = '#fef3c7';
    setTimeout(() => {
        moduleElement.style.background = '';
    }, 1500);
}

function populateModuleDetailsTables() {
    const container = document.getElementById('module-details-list');
    let html = '';
    
    MODULES_DATA.forEach(module => {
        html += buildModuleDetailTable(module);
    });
    
    container.innerHTML = html;
    
    // Add click handlers for headers
    document.querySelectorAll('.module-table-header').forEach(header => {
        header.addEventListener('click', () => {
            const tableContent = header.nextElementSibling;
            header.classList.toggle('expanded');
            
            if (header.classList.contains('expanded')) {
                tableContent.style.display = 'block';
            } else {
                tableContent.style.display = 'none';
            }
        });
    });
    
    // Setup collapsible cells after tables are rendered
    setTimeout(setupCollapsibleCells, 100);
}

function buildModuleDetailTable(module) {
    const stats = module.stats;
    const percentage = stats.total > 0 ? Math.round(stats.pass / stats.total * 100) : 0;
    const stage = module.stage || '';
    const stageHtml = stage ? `<span class='module-table-stage'>Stage: ${stage}</span>` : '';
    
    // Set current module name for waiver buttons
    window.CURRENT_MODULE_NAME = module.name;
    
    // Check if this module has been skipped
    const isModuleSkipped = PENDING_CHANGES.some(c => 
        c.type === 'skip' &&
        c.module === module.name &&
        c.item_id === null  // null means entire module
    );
    
    // Determine status color based on overall_status or status
    const moduleStatus = module.overall_status || module.status || 'pending';
    let statusColor;
    
    switch(moduleStatus) {
        case 'ready':
            statusColor = '#10b981';      // Green - all checks passed
            break;
        case 'needs_attention':
        case 'fail':
            statusColor = '#ef4444';      // Red - has failures
            break;
        case 'in_progress':
        case 'partial':
            statusColor = '#3b82f6';      // Blue - partially completed
            break;
        case 'pending':
        default:
            statusColor = '#9ca3af';      // Gray - not started
            break;
    }
    
    // Add "Skip Module" button for pending modules (all items are pending)
    // Hide button if already skipped
    const isPending = module.status === 'pending';
    const escapeHtml = (str) => String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    const skipModuleBtn = (isPending && !isModuleSkipped) ? `
        <button class='skip-module-button' 
                data-module='${escapeHtml(module.name)}'
                data-item=''
                onclick='openSkipModalFromButton(this); event.stopPropagation();'
                title='Skip this entire module'>
            ⏭️ Skip Module
        </button>
    ` : '';
    
    // Add "SKIPPED" status badge if module is skipped
    const skippedBadge = isModuleSkipped ? `
        <span style='background:#10b981; color:white; padding:4px 12px; border-radius:4px; font-size:11px; font-weight:600; margin-left:12px;'>
            ✓ SKIPPED
        </span>
    ` : '';
    
    let rows = '';
    module.items.forEach(item => {
        rows += buildItemRow(item);
    });
    
    if (!rows) {
        rows = `<tr><td colspan='8' style='text-align:center; padding:2rem; color:#64748b;'>No checklist items captured.</td></tr>`;
    }
    
    return `
        <section class='module-table' id='detail-${module.name}' style='margin-bottom:0.75rem; border-radius:10px;'>
            <header class='module-table-header' data-module='${module.name}' role='button' tabindex='0' aria-expanded='false' 
                    style='border-left: 5px solid ${statusColor}; padding: 0.875rem 1rem;'>
                <div class='header-content'>
                    <span class='collapse-icon'>▶</span>
                    <h3>${module.name}</h3>
                    ${stageHtml}
                    ${skippedBadge}
                    ${skipModuleBtn}
                    <span class='module-table-stats'>
                        <span class='stat-total'>Total: <strong>${stats.total}</strong>${stats.skipped > 0 ? ` <span style="color:#9ca3af; font-size:0.85em;">(${stats.skipped} skipped)</span>` : ''}</span>
                        <span class='stat-applicable'>Applicable: <strong>${stats.applicable || stats.total}</strong></span>
                        <span class='stat-executed'>Executed: <strong>${stats.executed}</strong></span>
                        <span class='stat-pass'>Pass: <strong>${stats.pass}</strong></span>
                        <span class='stat-fail'>Fail: <strong>${stats.fail}</strong></span>
                        <span class='stat-pending'>Pending: <strong>${stats.pending}</strong></span>
                    </span>
                </div>
            </header>
            <div class='table-content' style='display:none;'>
                <table class='detail-table'>
                    <thead>
                        <tr>
                            <th>Item ID</th>
                            <th>Status</th>
                            <th>Executed</th>
                            <th>Occurrence</th>
                            <th>Description</th>
                            <th>Waiver</th>
                            <th>Prompts</th>
                            <th>Comments</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        </section>
    `;
}

function buildItemRow(item) {
    const status = item.status || 'no_check';
    const safeStatus = ['pass', 'fail', 'warning', 'no_check'].includes(status) ? status : 'no_check';
    
    // Check if this item has been waived (pending waiver has higher priority)
    const hasPendingWaiver = item.waiver_applied || false;
    
    // Check if this item has been skipped in pending changes
    const isSkipped = PENDING_CHANGES.some(c => 
        c.type === 'skip' &&
        c.module === window.CURRENT_MODULE_NAME &&
        c.item_id === item.id
    );
    
    // Determine display status and label with priority: Waive > Skip > Original
    let displayStatus, statusLabel;
    
    if (hasPendingWaiver) {
        // PRIORITY 1: Waived items always show as WAIVED (green), even if also skipped
        displayStatus = 'pass';  // Green badge
        statusLabel = 'WAIVED';
    } else if (isSkipped) {
        // PRIORITY 2: Skipped items show as SKIPPED (green), only if not waived
        displayStatus = 'pass';  // Green badge
        statusLabel = 'SKIPPED';
    } else {
        // PRIORITY 3: Original status
        displayStatus = safeStatus;
        statusLabel = status.toUpperCase();
    }
    
    // Build Waiver cell with separate handling for approved waivers and info waivers
    let waiverCell = '';
    const approvedWaivers = item.approved_waivers || [];
    const waivedAsInfo = item.waived_as_info || [];
    
    // Show approved waivers
    // If only 1 approved waiver: no number
    // If multiple (>1) approved waivers: add numbers
    if (approvedWaivers.length > 0) {
        waiverCell += `<div class='waiver-block'>`;
        if (approvedWaivers.length === 1) {
            // Single approved waiver - no number
            waiverCell += `<div class='waiver-item'>${approvedWaivers[0]}</div>`;
        } else {
            // Multiple approved waivers - add numbers
            approvedWaivers.forEach((waiver, idx) => {
                waiverCell += `<div class='waiver-item'><strong>${idx + 1}.</strong> ${waiver}</div>`;
            });
        }
        waiverCell += '</div>';
    }
    
    // Show WAIVED_AS_INFO items (always with sequential numbers)
    if (waivedAsInfo.length > 0) {
        if (approvedWaivers.length > 0) {
            // Add small spacing if there were approved waivers above
            waiverCell += `<div style='margin-top: 4px;'></div>`;
        }
        waivedAsInfo.forEach((waiver, idx) => {
            waiverCell += `<div class='waiver-item'><strong>${idx + 1}.</strong> ${waiver}</div>`;
        });
    }
    
    // Show pending waivers if waiver_applied flag is set
    if (hasPendingWaiver) {
        waiverCell += `<div class='waiver-block' style='border-left: 3px solid #9333ea; padding-left: 8px; margin-top: 4px;'>`;
        
        // Get all pending waivers for this item from failures
        const failures = item.failures || [];
        let pendingWaiverCount = 0;
        failures.forEach((failure, idx) => {
            if (failure.waived && failure.waiver_comment) {
                pendingWaiverCount++;
                waiverCell += `<div class='waiver-item' style='color: #9333ea;'>
                    <strong>[Pending]</strong> 
                    ${failure.waiver_comment}
                    ${failure.waiver_timestamp ? ` <em style='font-size: 0.85em; color: #a855f7;'>(${failure.waiver_timestamp})</em>` : ''}
                </div>`;
            }
        });
        
        waiverCell += '</div>';
    }
    
    const waiverCellContent = waiverCell || '&mdash;';
    const waiverCellHtml = waiverCell ? `<div class='collapsible-cell collapsed' data-type='waiver'>${waiverCellContent}</div>` : waiverCellContent;
    
    // Build Prompts cell (from item.failures, item.warnings, item.infos)
    // Note: exclude failures that have been waived (failure.waived === true)
    let promptCell = '';
    
    // Add failures (only non-waived ones)
    const failures = item.failures || [];
    const activeFailures = failures.filter(f => !f.waived);  // Exclude waived failures
    
    if (activeFailures.length > 0) {
        promptCell += `<div class='prompt-fail-block'>`;
        activeFailures.forEach((failure, idx) => {
            let failureText = '';
            if (typeof failure === 'object') {
                const failureDetails = Object.entries(failure)
                    .filter(([k, v]) => v !== null && v !== '' && k !== 'waived' && k !== 'waiver_comment' && k !== 'waiver_timestamp')
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ');
                failureText = failureDetails;
            } else {
                failureText = failure;
            }
            
            if (failureText) {
                // Escape special characters for HTML attributes
                const escapeHtml = (str) => String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                
                // Find original index in full failures array
                const originalIdx = failures.indexOf(failure);
                
                promptCell += `<div class='prompt-item'>
                    <strong>${idx + 1}.</strong> ${failureText}
                    <button class='waive-button' 
                            data-module='${escapeHtml(window.CURRENT_MODULE_NAME || '')}' 
                            data-item='${escapeHtml(item.id || '')}' 
                            data-desc='${escapeHtml(item.description || '')}' 
                            data-index='${originalIdx}' 
                            data-failure='${escapeHtml(failureText)}'
                            onclick='openWaiverModalFromButton(this); event.stopPropagation();'>
                        Waive
                    </button>
                </div>`;
            }
        });
        promptCell += '</div>';
    }
    
    // Add warnings
    const warnings = item.warnings || [];
    if (warnings.length > 0) {
        promptCell += `<div class='prompt-warn-block'>`;
        warnings.forEach((warn, idx) => {
            promptCell += `<div class='prompt-item'><strong>${idx + 1}.</strong> ${warn}</div>`;
        });
        promptCell += '</div>';
    }
    
    // Add infos
    const infos = item.infos || [];
    if (infos.length > 0) {
        promptCell += `<div class='prompt-info-block'>`;
        infos.forEach((info, idx) => {
            promptCell += `<div class='prompt-item'><strong>${idx + 1}.</strong> ${info}</div>`;
        });
        promptCell += '</div>';
    }
    
    const promptCellContent = promptCell || '&mdash;';
    const promptCellHtml = promptCell ? `<div class='collapsible-cell collapsed' data-type='prompt'>${promptCellContent}</div>` : promptCellContent;
    
    // Comments - use empty string as no comments in current data
    const commentsCellHtml = '&mdash;';
    
    const executed = item.executed ? 'Yes' : 'No';
    const occurrence = item.occurrence || 0;
    const description = item.description || '&mdash;';
    
    // Build status cell with optional "Waive All" button or "Skip" button
    let statusCellHtml = `<span class='table-badge badge-${displayStatus}'>${statusLabel}</span>`;
    
    // Add "Waive All" button for items with active (non-waived) failures
    if (displayStatus === 'fail' && activeFailures.length > 0) {
        const escapeHtml = (str) => String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        const allFailuresText = 'All ' + activeFailures.length + ' failure' + (activeFailures.length > 1 ? 's' : '');
        
        statusCellHtml += `<br/><button class='waive-all-button' 
                    data-module='${escapeHtml(window.CURRENT_MODULE_NAME || '')}' 
                    data-item='${escapeHtml(item.id || '')}' 
                    data-desc='${escapeHtml(item.description || '')}' 
                    data-index='-1' 
                    data-failure='${escapeHtml(allFailuresText)}'
                    onclick='openWaiverModalFromButton(this); event.stopPropagation();' 
                    style='margin-top:4px;'>
                Waive All
            </button>`;
    }
    
    // Add "Skip" button for pending items (no_check status) that haven't been waived or skipped
    // Skip button should NOT appear if item is waived (waive has higher priority)
    if (safeStatus === 'no_check' && !hasPendingWaiver && !isSkipped) {
        const escapeHtml = (str) => String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        
        statusCellHtml += `<br/><button class='skip-button' 
                    data-module='${escapeHtml(window.CURRENT_MODULE_NAME || '')}' 
                    data-item='${escapeHtml(item.id || '')}' 
                    data-desc='${escapeHtml(item.description || '')}' 
                    onclick='openSkipModalFromButton(this); event.stopPropagation();'>
                ⏭️ Skip
            </button>`;
    }
    
    // Determine additional classes for filtering
    const hasWarnings = warnings.length > 0;
    const isSkippedItem = item.skipped || isSkipped;
    let additionalClasses = hasWarnings ? ' has-warnings' : '';
    if (isSkippedItem) {
        additionalClasses += ' item-skipped';
    }
    
    // Add skip reason to description if skipped
    let descriptionHtml = description;
    if (isSkippedItem && item.skip_reason) {
        descriptionHtml += `<br/><span style='display:inline-block; margin-top:4px; padding:4px 8px; background:#f3f4f6; color:#6b7280; font-size:11px; border-radius:4px; font-weight:600;'>⏭️ SKIPPED</span>`;
        descriptionHtml += `<br/><span style='color:#9ca3af; font-size:0.9em; font-style:italic;'>Reason: ${item.skip_reason}</span>`;
    }
    
    return `
        <tr class='status-${displayStatus}${additionalClasses}'${isSkippedItem ? " style='opacity:0.5; background:linear-gradient(90deg, transparent 0%, rgba(156,163,175,0.1) 50%, transparent 100%);'" : ""}>
            <td>${item.id}</td>
            <td>${statusCellHtml}</td>
            <td>${executed}</td>
            <td>${occurrence}</td>
            <td>${descriptionHtml}</td>
            <td>${waiverCellHtml}</td>
            <td>${promptCellHtml}</td>
            <td>${commentsCellHtml}</td>
        </tr>
    `;
}

// Initialize all tabs
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== Dashboard Initialization ===');
    
    // Check if this is preview mode and load preview data first
    const isPreviewMode = checkAndLoadPreviewMode();
    
    console.log('Chart.js available:', typeof Chart !== 'undefined');
    console.log('Chart.js version:', typeof Chart !== 'undefined' ? Chart.version : 'NOT LOADED');
    console.log('MODULES_DATA length:', MODULES_DATA.length);
    console.log('OVERALL_STATS:', OVERALL_STATS);
    console.log('ISSUES_DATA failures:', ISSUES_DATA.failures.length);
    console.log('ISSUES_DATA warnings:', ISSUES_DATA.warnings.length);
    console.log('ISSUES_DATA waivers:', ISSUES_DATA.waivers.length);
    console.log('Preview mode:', isPreviewMode);
    
    // Check for empty state
    if (MODULES_DATA.length === 0) {
        console.log('No data found - showing empty state');
        showEmptyState();
    } else {
        console.log('Data found - initializing dashboard');
        try {
            initDashboard();
            console.log('Dashboard initialized successfully');
        } catch (e) {
            console.error('Error initializing dashboard:', e);
        }
        
        try {
            initIssues();
            console.log('Issues tab initialized successfully');
        } catch (e) {
            console.error('Error initializing issues:', e);
        }
        
        try {
            initDetails();
            console.log('Details tab initialized successfully');
        } catch (e) {
            console.error('Error initializing details:', e);
        }
        
        // Initialize waiver system
        try {
            initWaivers();
            console.log('Waiver system initialized successfully');
        } catch (e) {
            console.error('Error initializing waivers:', e);
        }
    }
    
    // Initialize Back to Top button
    initBackToTop();
});

// Back to Top button functionality
function initBackToTop() {
    const backToTopBtn = document.getElementById('back-to-top');
    
    if (!backToTopBtn) {
        console.warn('Back to Top button not found');
        return;
    }
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('show');
        } else {
            backToTopBtn.classList.remove('show');
        }
    });
    
    // Scroll to top when clicked
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    console.log('Back to Top button initialized');
}

// Show empty state with helpful guidance
function showEmptyState() {
    const dashboardTab = document.getElementById('dashboard-tab');
    const issuesTab = document.getElementById('issues-tab');
    const detailsTab = document.getElementById('details-tab');
    
    const emptyStateHTML = `
        <div style='display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:60vh; text-align:center; padding:2rem;'>
            <div style='font-size:5rem; margin-bottom:1rem;'>📋</div>
            <h1 style='font-size:2rem; color:#1e293b; margin-bottom:1rem;'>No Check Data Available</h1>
            <p style='font-size:1.1rem; color:#64748b; max-width:600px; margin-bottom:2rem; line-height:1.6;'>
                It looks like no checks have been executed yet. To get started with the IP Signoff Dashboard:
            </p>
            
            <div style='background:white; border-radius:12px; padding:2rem; max-width:700px; box-shadow:0 4px 6px rgba(0,0,0,0.1); text-align:left;'>
                <h3 style='color:#667eea; margin-bottom:1rem; font-size:1.3rem;'>🚀 Quick Start Guide</h3>
                
                <div style='margin-bottom:1.5rem;'>
                    <div style='display:flex; align-items:start; gap:1rem; margin-bottom:1rem;'>
                        <div style='background:#667eea; color:white; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-weight:700;'>1</div>
                        <div>
                            <strong style='color:#1e293b;'>Run Checklist Tool</strong>
                            <p style='color:#64748b; margin:0.25rem 0 0 0;'>Execute the checklist tool from the <code>Work/</code> directory:</p>
                            <code style='display:block; background:#f1f5f9; padding:0.5rem; border-radius:4px; margin-top:0.5rem; color:#334155;'>cd Work && ./run.csh</code>
                        </div>
                    </div>
                    
                    <div style='display:flex; align-items:start; gap:1rem; margin-bottom:1rem;'>
                        <div style='background:#667eea; color:white; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-weight:700;'>2</div>
                        <div>
                            <strong style='color:#1e293b;'>Verify Check Outputs</strong>
                            <p style='color:#64748b; margin:0.25rem 0 0 0;'>Ensure checks generated YAML files in:</p>
                            <code style='display:block; background:#f1f5f9; padding:0.5rem; border-radius:4px; margin-top:0.5rem; color:#334155;'>Check_modules/*/outputs/*.yaml</code>
                        </div>
                    </div>
                    
                    <div style='display:flex; align-items:start; gap:1rem;'>
                        <div style='background:#667eea; color:white; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-weight:700;'>3</div>
                        <div>
                            <strong style='color:#1e293b;'>Regenerate Dashboard</strong>
                            <p style='color:#64748b; margin:0.25rem 0 0 0;'>Run the dashboard generator again:</p>
                            <code style='display:block; background:#f1f5f9; padding:0.5rem; border-radius:4px; margin-top:0.5rem; color:#334155;'>cd Work && ./visualize_signoff.csh</code>
                        </div>
                    </div>
                </div>
                
                <div style='background:#eff6ff; border-left:4px solid #3b82f6; padding:1rem; border-radius:4px;'>
                    <strong style='color:#1e40af;'>💡 Tip:</strong>
                    <span style='color:#1e40af;'> You can specify a different stage with <code>--stage</code> parameter if needed.</span>
                </div>
            </div>
            
            <div style='margin-top:2rem; color:#94a3b8;'>
                <p>Need help? Check the <code>Work/USAGE.md</code> for detailed documentation.</p>
            </div>
        </div>
    `;
    
    if (dashboardTab) dashboardTab.innerHTML = emptyStateHTML;
    if (issuesTab) issuesTab.innerHTML = emptyStateHTML;
    if (detailsTab) detailsTab.innerHTML = emptyStateHTML;
}
"""


def write_html(work_dir: Path, content: str) -> Path:
    """Write HTML to Work/Reports directory."""
    out_dir = work_dir / "Reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    out_path = out_dir / f"signoff_{stamp}.html"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate IP Signoff Dashboard HTML.")
    parser.add_argument("--root", default=None, help="Root directory (CHECKLIST directory, default: auto-detect from cwd)")
    parser.add_argument("--stage", default="Initial")
    parser.add_argument("--work-dir", default=None, help="Work directory for output (default: current directory)")
    # Preview mode arguments
    parser.add_argument("--preview-waivers", type=str, default=None, 
                       help="Path to pending waivers YAML file for preview mode (legacy)")
    parser.add_argument("--preview-changes", type=str, default=None,
                       help="Path to unified pending changes YAML file (waivers + skips)")
    parser.add_argument("--output", type=str, default=None,
                       help="Custom output filename (default: signoff_<date>.html)")
    args = parser.parse_args()

    # Detect if running from Work directory and auto-adjust to CHECKLIST root
    cwd = Path.cwd().resolve()
    in_work_dir = False
    original_work_dir = None
    
    # Check if we're in Work directory (has ../Check_modules but no ./Check_modules)
    if (cwd.parent / "Check_modules").exists() and not (cwd / "Check_modules").exists():
        if cwd.name == "Work":
            print(f"[INFO] Detected execution from Work directory, adjusting paths automatically")
            in_work_dir = True
            original_work_dir = cwd  # Save the Work directory path before changing
            # Change to parent directory for consistent behavior
            import os
            os.chdir(cwd.parent)
            adjusted_cwd = Path.cwd().resolve()
            print(f"[INFO] Changed directory to CHECKLIST root: {adjusted_cwd}")

    # Determine work directory
    if args.work_dir:
        # If user specified work_dir and we're in Work directory, resolve it from original location
        if in_work_dir and original_work_dir:
            # User passed --work-dir . from Work directory
            if args.work_dir == ".":
                work_dir = original_work_dir
            else:
                work_dir = Path(args.work_dir).resolve()
        else:
            work_dir = Path(args.work_dir).resolve()
    else:
        work_dir = Path.cwd().resolve()
        # If we were in Work directory, work_dir should be the Work subdirectory
        if in_work_dir and original_work_dir:
            work_dir = original_work_dir
    
    # Determine root directory
    if args.root:
        root = Path(args.root).resolve()
    else:
        root_cwd = Path.cwd().resolve()
        if root_cwd.name == "Work":
            root = root_cwd.parent
        else:
            root = root_cwd
            while root != root.parent:
                if (root / "Check_modules").exists() and (root / "Project_config").exists():
                    break
                root = root.parent
            if not (root / "Check_modules").exists():
                print(f"[ERROR] Cannot auto-detect CHECKLIST root directory.")
                print(f"[INFO] Please run from Work/ directory or specify --root")
                return
    
    if not root.exists():
        print(f"[ERROR] Root directory not found: {root}")
        return
    
    print(f"[INFO] Root directory: {root}")
    print(f"[INFO] Work directory: {work_dir}")
    print(f"[INFO] Stage: {args.stage}")
    
    checklist = parse_checklist(root, args.stage)
    if not checklist:
        print(f"[WARN] No checklist found for stage: {args.stage}")
        print(f"[INFO] Generating dashboard with available data...")
    
    # Load pending changes (waivers and skips) if in preview mode
    preview_waivers = None
    preview_skips = None
    
    # Handle unified preview-changes format (preferred)
    if args.preview_changes:
        changes_file = Path(args.preview_changes).resolve()
        if changes_file.exists():
            preview_waivers, preview_skips = load_pending_changes(changes_file)
            print(f"[INFO] Preview mode enabled with {len(preview_waivers)} waivers and {len(preview_skips)} skips")
        else:
            print(f"[WARNING] Changes file not found: {args.preview_changes}")
    
    # Handle legacy preview-waivers format (backward compatibility)
    elif args.preview_waivers:
        waiver_file = Path(args.preview_waivers).resolve()
        if waiver_file.exists():
            preview_waivers = load_pending_waivers(waiver_file)
            preview_skips = []  # No skips in legacy format
            print(f"[INFO] Preview mode enabled with {len(preview_waivers)} pending waivers (legacy format)")
        else:
            print(f"[WARNING] Waiver file not found: {args.preview_waivers}")
    
    # Generate HTML with preview changes applied inside generate_html
    # Pass both waivers and skips to generate_html
    html_doc = generate_html(root, args.stage, checklist, preview_waivers, preview_skips)
    
    # Determine output filename
    if args.output:
        # Custom output filename specified
        out_filename = args.output
        out_dir = work_dir / "Reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / out_filename
        out_path.write_text(html_doc, encoding="utf-8")
    else:
        # Default filename generation
        out_path = write_html(work_dir, html_doc)
    
    # Display preview mode status
    if preview_waivers or preview_skips:
        change_summary = []
        if preview_waivers:
            change_summary.append(f"{len(preview_waivers)} waivers")
        if preview_skips:
            change_summary.append(f"{len(preview_skips)} skips")
        print(f"[INFO] Preview dashboard written: {out_path}")
        print(f"[INFO] Applied changes: {', '.join(change_summary)}")
    else:
        print(f"[INFO] Dashboard written: {out_path}")
    print(f"[INFO] Data source: {root}")


if __name__ == "__main__":
    main()