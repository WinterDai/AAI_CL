"""
L6: YAML Summary Generator
"""

import yaml
from typing import Dict, Any, List
from pathlib import Path


def generate_summary_yaml(
    summary_dict: Dict[str, Any],
    item_id: str,
    output_path: Path
) -> None:
    """
    生成Summary YAML文件
    
    输入:
        summary_dict: generate_summary_dict的输出
        item_id: Checker ID
        output_path: 输出YAML路径
        
    格式:
        items:
          - id: IMP-10-0-0-00
            executed: true
            status: PASS
            description: "..."
            failures: [...]
            warnings: [...]
    """
    yaml_content = {
        'items': [
            {
                'id': item_id,
                **summary_dict
            }
        ]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def append_to_summary_yaml(
    summary_dict: Dict[str, Any],
    item_id: str,
    yaml_path: Path
) -> None:
    """
    追加item到已存在的Summary YAML
    
    用于批量生成多个checker的汇总
    """
    # Load existing YAML
    if yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f) or {}
    else:
        yaml_content = {'items': []}
    
    # Append new item
    new_item = {
        'id': item_id,
        **summary_dict
    }
    yaml_content.setdefault('items', []).append(new_item)
    
    # Write back
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
