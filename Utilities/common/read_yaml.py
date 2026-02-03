################################################################################
# Script Name: read_yaml.py
#
# Purpose:
#   Lightweight safe YAML loading helper returning dict with fallback to {}.
#
# Usage:
#   from read_yaml import safe_read_yaml
#
# Author: yyin
# Date:   2025-10-23
################################################################################
from pathlib import Path
import yaml

# ---read_yaml---
def read_yaml(path):
    path = Path(path).expanduser().resolve()
    if path is None:  
        return None
    if not path.is_file():
        print(f"YAML file not found: {path}")
        return None  
         
    try:
        with open(path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        return yaml_data
    
    except yaml.YAMLError as e:
        #_print_error(f"Failed to parse YAML file '{path}': {e}")
        print(f"Failed to parse YAML file '{path}': {e}")
        return None
    except Exception as e:
        #_print_error(f"An unexpected error occurred while reading file '{path}': {e}")
        print(f"An unexpected error occurred while reading file '{path}': {e}")
        return None