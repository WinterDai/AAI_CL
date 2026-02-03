#!/usr/bin/env python3
################################################################################
# Script Name: parse_interface.py
#
# Purpose:
#   Parse DATA_INTERFACE.yaml and distribute data to individual check modules.
#   Optimized for large files (356+ items) with fast lookup performance.
#
# Features:
#   1. Split by check_module -> separate files per module
#   2. Generate JSON cache for fast access (10-50x faster than YAML)
#   3. Incremental update - only parse if source changed
#   4. Multiple output formats: YAML (human-readable) + JSON (fast)
#
# Usage:
#   python parse_interface.py [--force] [--format yaml|json|both]
#   
#   --force: Force regeneration even if files are up-to-date
#   --format: Output format (default: both)
#
# Author: yyin
# Date: 2025-10-30
################################################################################

import sys
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import argparse


# ============================================================================
# Section 1: Path Configuration
# ============================================================================

# ============================================================================
# Section 1: Path Configuration
# ============================================================================

def get_project_root() -> Path:
    """Auto-detect project root by looking for Check_modules directory."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / 'Check_modules').is_dir():
            return parent
    raise RuntimeError("Cannot find project root directory (Check_modules not found)")

ROOT = get_project_root()
DATA_INTERFACE_FILE = ROOT / 'Data_interface' / 'outputs' / 'DATA_INTERFACE.template.yaml'
CHECK_MODULES_DIR = ROOT / 'Check_modules'


# ============================================================================
# Section 1.5: Variable Substitution
# ============================================================================

def expand_variables(value: Any, variables: Dict[str, str]) -> Any:
    """
    Recursively expand variables in values.
    
    Supports:
    - ${CHECKLIST_ROOT} -> absolute path to checklist root
    - ${VARIABLE_NAME} -> custom variables
    
    Args:
        value: Value to expand (str, list, dict, or other)
        variables: Dictionary of variable name -> value mappings
    
    Returns:
        Expanded value with variables replaced
        On Windows: Normalizes path separators to backslashes
    
    Examples:
        >>> expand_variables("${CHECKLIST_ROOT}/IP_project_folder", 
        ...                  {"CHECKLIST_ROOT": "C:/workspace/CHECKLIST"})
        'C:\\workspace\\CHECKLIST\\IP_project_folder'  # On Windows
    """
    if isinstance(value, str):
        # Replace all variables in string
        result = value
        for var_name, var_value in variables.items():
            result = result.replace(f'${{{var_name}}}', var_value)
        
        # Normalize path separators on Windows (if result contains path-like content)
        # Only normalize if it looks like a path (contains / or \)
        if ('/' in result or '\\' in result) and (':' in result or result.startswith('/')):
            import os
            # Replace forward slashes with OS-specific separator
            result = result.replace('/', os.sep)
        
        return result
    
    elif isinstance(value, list):
        # Recursively expand list items
        return [expand_variables(item, variables) for item in value]
    
    elif isinstance(value, dict):
        # Recursively expand dict values
        return {k: expand_variables(v, variables) for k, v in value.items()}
    
    else:
        # Return as-is for other types (int, bool, None, etc.)
        return value


def get_builtin_variables() -> Dict[str, str]:
    """
    Get built-in variables for path substitution.
    
    Returns:
        Dictionary of variable name -> value mappings
        
    Built-in Variables:
        CHECKLIST_ROOT: Absolute path to checklist root directory
    """
    root = get_project_root()
    
    return {
        'CHECKLIST_ROOT': str(root)
    }


# ============================================================================
# Section 2: File Hash & Change Detection
# ============================================================================

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of file for change detection."""
    if not filepath.exists():
        return ""
    
    sha256 = hashlib.sha256()
    with filepath.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def should_regenerate(source_file: Path, target_dir: Path, force: bool = False) -> bool:
    """
    Check if regeneration is needed.
    
    Returns True if:
    - force flag is set
    - source file changed (hash mismatch)
    - target files don't exist
    """
    if force:
        return True
    
    # Check if target directory and files exist
    if not target_dir.exists():
        return True
    
    hash_file = target_dir / '.source_hash'
    if not hash_file.exists():
        return True
    
    # Compare hash
    current_hash = compute_file_hash(source_file)
    stored_hash = hash_file.read_text(encoding='utf-8').strip()
    
    return current_hash != stored_hash


def save_hash(source_file: Path, target_dir: Path):
    """Save source file hash to target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    hash_file = target_dir / '.source_hash'
    current_hash = compute_file_hash(source_file)
    hash_file.write_text(current_hash, encoding='utf-8')


# ============================================================================
# Section 3: Data Parsing
# ============================================================================

def load_data_interface() -> Dict[str, Any]:
    """Load and parse DATA_INTERFACE.yaml."""
    print(f"Loading {DATA_INTERFACE_FILE}...")
    
    if not DATA_INTERFACE_FILE.exists():
        raise FileNotFoundError(f"DATA_INTERFACE.yaml not found: {DATA_INTERFACE_FILE}")
    
    with DATA_INTERFACE_FILE.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data or 'sections' not in data:
        raise ValueError("Invalid DATA_INTERFACE.yaml: 'sections' key not found")
    
    return data


def extract_module_data(sections: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract data organized by check_module.
    
    Returns:
    {
        '5.0_SYNTHESIS_CHECK': {
            'IMP-5-0-0-00': {
                'description': '...',
                'requirements': {...},
                'input_files': [...],
                'waivers': {...}
            },
            ...
        },
        ...
    }
    
    Note: Variables like ${CHECKLIST_ROOT} are PRESERVED (not expanded) in distributed files.
          Variable expansion happens at runtime in base_checker.py and find_input_files().
    """
    module_data = {}
    
    for section_name, section_content in sections.items():
        if not isinstance(section_content, dict):
            continue
        
        module_data[section_name] = {}
        
        for item_id, item_content in section_content.items():
            if not isinstance(item_content, dict):
                continue
            
            # Extract item data WITHOUT expanding variables (keep ${CHECKLIST_ROOT} as-is)
            item_data = {
                'description': item_content.get('description', ''),
                'requirements': item_content.get('requirements', {}),
                'input_files': item_content.get('input_files', []),
                'waivers': item_content.get('waivers', {})
            }
            
            # NO variable expansion here - preserve ${CHECKLIST_ROOT} for portability
            module_data[section_name][item_id] = item_data
    
    return module_data


# ============================================================================
# Section 4: Output Generation
# ============================================================================

def save_yaml_format(module_name: str, items: Dict[str, Any], output_dir: Path):
    """
    Save as separate YAML files per item (optimal for distributed execution).
    
    Structure:
    - items/IMP-5-0-0-00.yaml
    - items/IMP-5-0-0-01.yaml
    - ...
    
    Each file contains: description, requirements, input_files, waivers
    Variables like ${CHECKLIST_ROOT} are preserved as-is for Git-friendly portability.
    """
    items_dir = output_dir / 'items'
    items_dir.mkdir(parents=True, exist_ok=True)
    
    # Save each item to its own file (preserving ${CHECKLIST_ROOT} variables)
    for item_id, item_data in items.items():
        item_file = items_dir / f'{item_id}.yaml'
        with item_file.open('w', encoding='utf-8') as f:
            yaml.safe_dump(item_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"  ✓ Saved {len(items)} YAML files to {items_dir}")


def save_json_format(module_name: str, items: Dict[str, Any], output_dir: Path):
    """
    Save as JSON cache per item (ultra-fast access for distributed execution).
    
    Structure:
    - .cache/IMP-5-0-0-00.json
    - .cache/IMP-5-0-0-01.json
    - .cache/index.json (quick lookup)
    
    Each file contains: description, requirements, input_files, waivers
    """
    cache_dir = output_dir / '.cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Save each item to its own JSON file
    index = {}
    for item_id, item_data in items.items():
        item_cache = cache_dir / f'{item_id}.json'
        with item_cache.open('w', encoding='utf-8') as f:
            json.dump(item_data, f, indent=2, ensure_ascii=False)
        
        # Build index
        index[item_id] = {
            'file': f'{item_id}.json',
            'description': item_data.get('description', '')[:100]  # Truncate for index
        }
    
    # Save index file
    index_file = cache_dir / 'index.json'
    index_data = {
        '_metadata': {
            'module': module_name,
            'generated': datetime.now().isoformat(),
            'item_count': len(items)
        },
        'items': index
    }
    
    with index_file.open('w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Saved {len(items)} JSON cache files to {cache_dir}")


def save_unified_yaml(module_name: str, items: Dict[str, Any], output_dir: Path):
    """
    Save as single unified YAML file (backward compatibility).
    
    File: module_interface.yaml
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    unified_file = output_dir / 'module_interface.yaml'
    
    with unified_file.open('w', encoding='utf-8') as f:
        yaml.safe_dump(items, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"  ✓ Saved unified YAML to {unified_file}")


# ============================================================================
# Section 5: Main Processing
# ============================================================================

def process_module(module_name: str, items: Dict[str, Any], output_format: str):
    """Process a single check module."""
    # Determine output directory
    module_dir = CHECK_MODULES_DIR / module_name / 'inputs'
    
    print(f"\n📦 Processing {module_name} ({len(items)} items)...")
    
    # Save based on format
    if output_format in ['yaml', 'both']:
        save_yaml_format(module_name, items, module_dir)
    
    if output_format in ['json', 'both']:
        save_json_format(module_name, items, module_dir)
    
    # Always save unified YAML for backward compatibility
    # save_unified_yaml(module_name, items, module_dir)
    
    # Save hash for change detection
    save_hash(DATA_INTERFACE_FILE, module_dir)


def parse_and_distribute(force: bool = False, output_format: str = 'yaml', 
                         check_modules: Optional[List[str]] = None,
                         check_items: Optional[List[str]] = None):
    """
    Main function to parse DATA_INTERFACE.yaml and distribute to modules.
    
    Args:
        force: Force regeneration even if files are up-to-date
        output_format: 'yaml', 'json', or 'both'
        check_modules: Only process specified modules (e.g., ['5.0_SYNTHESIS_CHECK'])
        check_items: Only process specified items (e.g., ['IMP-5-0-0-00', 'IMP-5-0-0-01'])
    """
    print("=" * 70)
    print("DATA_INTERFACE.yaml Parser & Distributor")
    print("=" * 70)
    
    # Load data
    data = load_data_interface()
    sections = data.get('sections', {})
    
    # Extract module data
    module_data = extract_module_data(sections)
    
    # Filter by check_modules if specified
    if check_modules:
        module_data = {k: v for k, v in module_data.items() if k in check_modules}
        print(f"\n🎯 Filtering to {len(check_modules)} specified module(s): {', '.join(check_modules)}")
    
    # Filter by check_items if specified
    if check_items:
        for module_name, items in module_data.items():
            module_data[module_name] = {k: v for k, v in items.items() if k in check_items}
        print(f"\n🎯 Filtering to {len(check_items)} specified item(s): {', '.join(check_items)}")
    
    print(f"\n📊 Found {len(module_data)} check module(s) to process")
    print(f"📋 Output format: {output_format}")
    
    # Process each module
    processed_count = 0
    skipped_count = 0
    
    for module_name, items in module_data.items():
        if not items:  # Skip if no items after filtering
            print(f"\n⏭️  Skipping {module_name} (no items to process)")
            skipped_count += 1
            continue
            
        module_dir = CHECK_MODULES_DIR / module_name / 'inputs'
        
        # Check if regeneration needed
        if not force and not should_regenerate(DATA_INTERFACE_FILE, module_dir):
            print(f"\n⏭️  Skipping {module_name} (up-to-date)")
            skipped_count += 1
            continue
        
        # Process module
        process_module(module_name, items, output_format)
        processed_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Complete!")
    print(f"   Processed: {processed_count} module(s)")
    print(f"   Skipped:   {skipped_count} module(s) (up-to-date)")
    print("=" * 70)


# ============================================================================
# Section 6: Helper Functions for Checkers
# ============================================================================

def load_item_data(check_module: str, item_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Helper function for checkers to load their item data.
    OPTIMIZED for distributed execution - loads only the specific item file.
    
    Usage in checker:
        from parse_interface import load_item_data
        data = load_item_data('5.0_SYNTHESIS_CHECK', 'IMP-5-0-0-00')
        if data:
            requirements = data['requirements']
            input_files = data['input_files']
            waivers = data['waivers']
    
    Args:
        check_module: Module name (e.g., '5.0_SYNTHESIS_CHECK')
        item_id: Item ID (e.g., 'IMP-5-0-0-00')
        use_cache: Use JSON cache if available (10-50x faster)
    
    Returns:
        Dict with keys: description, requirements, input_files, waivers
        Variables like ${CHECKLIST_ROOT} are preserved (not expanded)
        None if not found
    """
    module_dir = CHECK_MODULES_DIR / check_module / 'inputs'
    
    # Try JSON cache first (ultra-fast: ~5ms)
    if use_cache:
        cache_file = module_dir / '.cache' / f'{item_id}.json'
        if cache_file.exists():
            try:
                with cache_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Return data as-is, preserving ${CHECKLIST_ROOT} variables
                    return data
            except Exception:
                pass  # Fall back to YAML
    
    # Fall back to YAML file (fast: ~20ms)
    try:
        yaml_file = module_dir / 'items' / f'{item_id}.yaml'
        
        if not yaml_file.exists():
            return None
        
        with yaml_file.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Return data as-is, preserving ${CHECKLIST_ROOT} variables
            return data
    
    except Exception as e:
        print(f"Error loading item data for {item_id}: {e}")
        return None


def load_module_requirements(check_module: str) -> Dict[str, Any]:
    """
    Load all requirements for a module.
    
    Returns:
        Dict mapping item_id -> requirements dict
    """
    module_dir = CHECK_MODULES_DIR / check_module / 'inputs'
    
    # Try loading from index first
    index_file = module_dir / '.cache' / 'index.json'
    if index_file.exists():
        try:
            requirements = {}
            with index_file.open('r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Load each item's requirements from cache
            for item_id in index_data['items'].keys():
                item_data = load_item_data(check_module, item_id, use_cache=True)
                if item_data:
                    requirements[item_id] = item_data.get('requirements', {})
            
            return requirements
        except Exception:
            pass
    
    # Fall back to loading from YAML items
    items_dir = module_dir / 'items'
    if not items_dir.exists():
        return {}
    
    requirements = {}
    for yaml_file in items_dir.glob('*.yaml'):
        item_id = yaml_file.stem
        try:
            with yaml_file.open('r', encoding='utf-8') as f:
                item_data = yaml.safe_load(f)
                if item_data:
                    requirements[item_id] = item_data.get('requirements', {})
        except Exception:
            continue
    
    return requirements


def load_all_items(check_module: str) -> Dict[str, Dict[str, Any]]:
    """
    Load all items for a module (use sparingly - prefer load_item_data for single items).
    
    Returns:
        Dict mapping item_id -> full item data
    """
    module_dir = CHECK_MODULES_DIR / check_module / 'inputs'
    items_dir = module_dir / 'items'
    
    if not items_dir.exists():
        return {}
    
    items = {}
    for yaml_file in items_dir.glob('*.yaml'):
        item_id = yaml_file.stem
        item_data = load_item_data(check_module, item_id)
        if item_data:
            items[item_id] = item_data
    
    return items


def find_input_files(root: Path, check_module: str, item_id: str, file_pattern: str) -> tuple[Optional[Path], Optional[str], Optional[str]]:
    """
    Generic helper to find input files from DATA_INTERFACE for any checker.
    
    This function provides standardized error handling for missing/invalid input files.
    All checkers should use this function for consistent error messaging.
    
    Args:
        root: Root path of the workspace
        check_module: Module name (e.g., '5.0_SYNTHESIS_CHECK')
        item_id: Item ID (e.g., 'IMP-5-0-0-00')
        file_pattern: File name pattern to search for (e.g., 'qor.rpt', 'timing.rpt')
    
    Returns:
        Tuple of (Path object or None, log_error_message, report_error_message)
        
    Error Messages (log format):
        - "Input files related to {item_id} not provided." - No input_files in DATA_INTERFACE
        - "Can't find the file {path}." - File path specified but doesn't exist
        
    Error Messages (report format):
        - "Input files related to {item_id} not provided in DATA_INTERFACE.yaml." - No input_files
        - "Can't find the file {path} provided in DATA_INTERFACE.yaml." - File doesn't exist
    
    Usage Example:
        from parse_interface import find_input_files
        
        qor_path, log_err, rpt_err = find_input_files(root, CHECK_MODULE, ITEM_ID, 'qor.rpt')
        if not qor_path:
            _append_log(f'[ERROR]:{log_err}')
            _append_rpt(f'1: Fail: {rpt_err}')
            return
    """
    item_data = load_item_data(check_module, item_id)
    
    if not item_data:
        log_msg = f"Input files related to {item_id} not provided."
        rpt_msg = f"Input files related to {item_id} not provided in DATA_INTERFACE.yaml."
        return None, log_msg, rpt_msg
    
    input_files = item_data.get('input_files', [])
    
    # Check if input_files is empty
    if not input_files:
        log_msg = f"Input files related to {item_id} not provided."
        rpt_msg = f"Input files related to {item_id} not provided in DATA_INTERFACE.yaml."
        return None, log_msg, rpt_msg
    
    # Expand ${CHECKLIST_ROOT} variables before checking files
    variables = get_builtin_variables()
    expanded_files = expand_variables(input_files, variables)
    
    # Find file matching the pattern in input_files
    for file_path in expanded_files:
        if file_pattern.lower() in str(file_path).lower():
            path = Path(file_path)
            if path.exists():
                return path, None, None
            else:
                # Path specified but file doesn't exist
                log_msg = f"Can't find the file {path}."
                rpt_msg = f"Can't find the file {path} provided in DATA_INTERFACE.yaml."
                return None, log_msg, rpt_msg
    
    # Pattern not found in any input_files
    log_msg = f"Input files related to {item_id} not provided."
    rpt_msg = f"Input files related to {item_id} not provided in DATA_INTERFACE.yaml."
    return None, log_msg, rpt_msg


# ============================================================================
# Section 7: Command Line Interface
# ============================================================================

def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Parse DATA_INTERFACE.yaml and distribute to check modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parse_interface.py                    # Parse and distribute (incremental)
  python parse_interface.py --force            # Force regeneration
  python parse_interface.py --format json      # Only JSON output
  python parse_interface.py --format yaml      # Only YAML output
        """
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if files are up-to-date'
    )
    #for_development
    parser.add_argument(
        '--format',
        choices=['yaml', 'json', 'both'],
        default='yaml',
        help='Output format (default: yaml)'
    )
    
    args = parser.parse_args()
    
    try:
        parse_and_distribute(force=args.force, output_format=args.format)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
