################################################################################
# Script Name: config_reader.py
#
# Purpose:
#   Provide unified discovery and parsing helpers for design_config.yaml and waive.yaml.
#   Also map list values to line numbers for precise referencing in reports.
#
# Usage:
#   from config_reader import find_design_config, read_design_config,
#       find_waive_config, read_waive_config, get_config_line_map, detect_project_root
#
# Author: yyin
# Date:   2025-10-23
################################################################################
"""Common configuration file reader for design_config.yaml and waive.yaml

This module provides unified functions to find and read configuration files
used across different checkers. It handles:
1. Finding design_config.yaml in standard locations
2. Finding waive.yaml in standard locations
3. Reading and parsing YAML files with proper error handling
4. Extracting line numbers for specific configuration items

Usage:
    from common.config_reader import (
        find_design_config, read_design_config,
        find_waive_config, read_waive_config,
        get_config_line_map, detect_project_root
    )
    
    # Detect project root
    root = detect_project_root(Path(__file__).parent)
    
    # Read design config
    design_data = read_design_config(root, check_module="5.0_SYNTHESIS_CHECK")
    
    # Read waiver config
    waive_data = read_waive_config(root, check_module="5.0_SYNTHESIS_CHECK")
    
    # Get line numbers for any list items in config
    line_map = get_config_line_map(config_path, "stdcell_list")
    line_map = get_config_line_map(config_path, "dont_use_cells")
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union, Callable
import yaml


def find_design_config(
    root: Union[str, Path],
    check_module: Optional[str] = None,
    log_func: Optional[Callable[[str], None]] = None
) -> Optional[Path]:
    """
    Find design_config.yaml in standard locations.
    
    Args:
        root: Project root directory
        check_module: Specific check module name (e.g., "5.0_SYNTHESIS_CHECK")
        log_func: Optional logging function for errors/warnings
    
    Returns:
        Path to design_config.yaml if found, None otherwise
    
    Search order:
        1. Check_modules/<check_module>/inputs/design_config.yaml
        2. Project_config/prep_config/Initial/latest/design_config.yaml
        3. Project_config/prep_config/Initial/V1/design_config.yaml
    """
    root = Path(root).expanduser().resolve()
    
    candidates = []
    
    # Module-specific location
    if check_module:
        candidates.append(
            root / 'Check_modules' / check_module / 'inputs' / 'design_config.yaml'
        )
    
    # Project-wide locations
    candidates.extend([
        root / 'Project_config' / 'prep_config' / 'Initial' / 'latest' / 'design_config.yaml',
        root / 'Project_config' / 'prep_config' / 'Initial' / 'V1' / 'design_config.yaml'
    ])
    
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    
    # Log error if not found
    if log_func:
        log_func(f"design_config.yaml not found in any standard location")
    
    return None


def find_waive_config(
    root: Union[str, Path],
    check_module: Optional[str] = None,
    log_func: Optional[Callable[[str], None]] = None
) -> Optional[Path]:
    """
    Find waive.yaml in standard locations.
    
    Args:
        root: Project root directory
        check_module: Specific check module name (e.g., "5.0_SYNTHESIS_CHECK")
        log_func: Optional logging function for errors/warnings
    
    Returns:
        Path to waive.yaml if found, None otherwise
    
    Search order:
        1. Check_modules/<check_module>/inputs/waive.yaml
        2. Waiver_config/<check_module>/waive.yaml
    """
    root = Path(root).expanduser().resolve()
    
    candidates = []
    
    # Module-specific locations
    if check_module:
        candidates.extend([
            root / 'Check_modules' / check_module / 'inputs' / 'waive.yaml',
            root / 'Waiver_config' / check_module / 'waive.yaml'
        ])
    
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    
    # Waiver file is optional, so just log a warning
    if log_func:
        log_func(f"waive.yaml not found (optional)")
    
    return None


def read_design_config(
    root: Union[str, Path],
    check_module: Optional[str] = None,
    log_func: Optional[Callable[[str], None]] = None
) -> Optional[dict]:
    """
    Read and parse design_config.yaml.
    
    Args:
        root: Project root directory
        check_module: Specific check module name
        log_func: Optional logging function for errors
    
    Returns:
        Parsed YAML data as dictionary, or None if error
    """
    config_path = find_design_config(root, check_module, log_func)
    if not config_path:
        return None
    
    try:
        with config_path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        if log_func:
            log_func(f'Failed to parse YAML "{config_path}": {e}')
    except Exception as e:
        if log_func:
            log_func(f'Error reading design_config.yaml: {e}')
    
    return None


def read_waive_config(
    root: Union[str, Path],
    check_module: Optional[str] = None,
    log_func: Optional[Callable[[str], None]] = None
) -> Optional[dict]:
    """
    Read and parse waive.yaml.
    
    Args:
        root: Project root directory
        check_module: Specific check module name
        log_func: Optional logging function for errors
    
    Returns:
        Parsed YAML data as dictionary, or None if error
    """
    waive_path = find_waive_config(root, check_module, log_func)
    if not waive_path:
        return None
    
    try:
        with waive_path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        if log_func:
            log_func(f'Failed to parse YAML "{waive_path}": {e}')
    except Exception as e:
        if log_func:
            log_func(f'Error reading waive.yaml: {e}')
    
    return None


def get_config_line_map(
    config_path: Union[str, Path],
    list_key: str,
    comment_char: str = '#'
) -> Dict[str, int]:
    """
    Extract line numbers for items in a YAML list.
    
    Args:
        config_path: Path to YAML configuration file
        list_key: The key name of the list (e.g., "stdcell_list", "dont_use_cells")
        comment_char: Character used for comments (default: '#')
    
    Returns:
        Dictionary mapping item value to line number
    
    Example:
        # YAML file content:
        stdcell_list:
          - lib1  # line 2
          - lib2  # line 3
        
        # Result:
        {'lib1': 2, 'lib2': 3}
    """
    config_path = Path(config_path).expanduser().resolve()
    line_map: Dict[str, int] = {}
    
    if not config_path.is_file():
        return line_map
    
    try:
        with config_path.open('r', encoding='utf-8') as f:
            in_section = False
            for line_num, line in enumerate(f, 1):
                stripped = line.strip()
                
                # Skip empty lines and full-line comments
                if not stripped or stripped.startswith(comment_char):
                    continue
                
                # Check for section start
                if f'{list_key}:' in line:
                    in_section = True
                    # Handle inline empty list: "key: []"
                    if stripped.endswith('[]'):
                        in_section = False
                    continue
                
                if in_section:
                    # Check if we've left the list section
                    # (non-indented line or different key)
                    if stripped and not line.startswith((' ', '\t')):
                        break
                    
                    # Parse list item: "- item_value" or "  - item_value"
                    if stripped.startswith('-'):
                        # Extract item value, removing comments
                        item_line = stripped.lstrip('- ').strip()
                        
                        # Remove inline comments
                        if ';' in item_line:
                            item_value = item_line.split(';', 1)[0].strip()
                        elif comment_char in item_line:
                            item_value = item_line.split(comment_char, 1)[0].strip()
                        else:
                            item_value = item_line
                        
                        # Remove quotes if present
                        item_value = item_value.strip('"').strip("'")
                        
                        if item_value:
                            line_map[item_value] = line_num
    
    except Exception:
        pass
    
    return line_map


def detect_project_root(start_path: Union[str, Path], max_levels: int = 10) -> Path:
    """
    Detect project root by searching for Check_modules directory.
    
    Args:
        start_path: Starting directory (usually __file__ parent)
        max_levels: Maximum levels to search upward
    
    Returns:
        Path to project root
    """
    current = Path(start_path).expanduser().resolve()
    
    for _ in range(max_levels):
        # Check for characteristic project directories
        if (current / 'Check_modules').is_dir() or \
           ((current / 'Check_modules').is_dir() and (current / 'Project_config').is_dir()):
            return current
        
        # Move up one level
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent
    
    # Return original path if not found
    return Path(start_path).expanduser().resolve()


# Convenience aliases for backward compatibility
def find_rule_yaml(root: Union[str, Path]) -> Optional[Path]:
    """Alias for find_design_config (backward compatibility)."""
    return find_design_config(root)


def read_rule_yaml(root: Union[str, Path]) -> Optional[dict]:
    """Alias for read_design_config (backward compatibility)."""
    return read_design_config(root)


def find_waiver_yaml(root: Union[str, Path]) -> Optional[Path]:
    """Alias for find_waive_config (backward compatibility)."""
    return find_waive_config(root)


def read_waiver_yaml(root: Union[str, Path]) -> Optional[dict]:
    """Alias for read_waive_config (backward compatibility)."""
    return read_waive_config(root)
