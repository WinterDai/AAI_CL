"""
L6: Report Generator - Log Format Generator
Plan.txt Section 2, Layer 6
"""

from typing import Dict, Any, List
from pathlib import Path


def generate_log_file(
    l5_output: Dict[str, Any],
    type_id: int,
    item_id: str,
    item_desc: str,
    output_path: Path
) -> None:
    """
    生成Log格式报告 (详细格式)
    
    输入:
        l5_output: L5过滤后的输出
        type_id: 1-4
        item_id: Checker ID
        item_desc: Checker描述
        output_path: 输出文件路径
        
    输出:
        无（写入文件）
        
    Log格式:
    - Header: Checker ID和描述
    - Status: PASS/FAIL
    - Found items详细列表
    - Missing items详细列表
    - Extra items详细列表 (Type 2/3)
    - Waived items详细列表 (Type 3/4)
    - Unused waivers列表 (Type 3/4)
    """
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append(f"Checker: {item_id}")
    lines.append(f"Description: {item_desc}")
    lines.append("=" * 80)
    lines.append("")
    
    # Status
    status = l5_output.get('status', 'UNKNOWN')
    lines.append(f"Status: {status}")
    lines.append("")
    
    # Found items
    found_items = l5_output.get('found_items', [])
    if found_items:
        lines.append(f"Found Items ({len(found_items)}):")
        lines.append("-" * 80)
        for idx, item in enumerate(found_items, 1):
            lines.extend(_format_item_detail(item, idx))
        lines.append("")
    
    # Missing items
    missing_items = l5_output.get('missing_items', [])
    if missing_items:
        lines.append(f"Missing Items ({len(missing_items)}):")
        lines.append("-" * 80)
        for idx, item in enumerate(missing_items, 1):
            lines.extend(_format_item_detail(item, idx))
        lines.append("")
    
    # Extra items (Type 2/3 only)
    extra_items = l5_output.get('extra_items', [])
    if extra_items:
        lines.append(f"Extra Items ({len(extra_items)}):")
        lines.append("-" * 80)
        for idx, item in enumerate(extra_items, 1):
            lines.extend(_format_item_detail(item, idx))
        lines.append("")
    
    # Waived items (Type 3/4 only)
    waived = l5_output.get('waived', [])
    if waived:
        lines.append(f"Waived Items ({len(waived)}):")
        lines.append("-" * 80)
        for idx, item in enumerate(waived, 1):
            lines.extend(_format_waived_item(item, idx))
        lines.append("")
    
    # Unused waivers (Type 3/4 only)
    unused_waivers = l5_output.get('unused_waivers', [])
    if unused_waivers:
        lines.append(f"Unused Waivers ({len(unused_waivers)}):")
        lines.append("-" * 80)
        for idx, waiver in enumerate(unused_waivers, 1):
            lines.append(f"  [{idx}] Pattern: {waiver.get('pattern', 'N/A')}")
            lines.append(f"      Reason: {waiver.get('reason', 'N/A')}")
        lines.append("")
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _format_item_detail(item: Dict[str, Any], index: int) -> List[str]:
    """
    格式化单个item的详细信息
    
    输出字段:
    - Index
    - Description
    - Value/Expected
    - Source File
    - Line Number
    - Matched Content
    - Parsed Fields
    - Searched Files (for missing items)
    """
    lines = []
    lines.append(f"  [{index}]")
    
    # Description
    if 'description' in item:
        lines.append(f"      Description: {item['description']}")
    
    # Value or Expected
    if 'value' in item:
        lines.append(f"      Value: {item['value']}")
    if 'expected' in item:
        lines.append(f"      Expected: {item['expected']}")
    
    # Source info
    if 'source_file' in item:
        source = item['source_file'] or "(ghost)"
        lines.append(f"      Source File: {source}")
    
    if 'line_number' in item:
        line_num = item['line_number'] if item['line_number'] is not None else "N/A"
        lines.append(f"      Line Number: {line_num}")
    
    # Matched content
    if 'matched_content' in item and item['matched_content']:
        lines.append(f"      Matched Content: {item['matched_content']}")
    
    # Parsed fields
    if 'parsed_fields' in item and item['parsed_fields']:
        lines.append(f"      Parsed Fields: {item['parsed_fields']}")
    
    # Searched files (for missing items)
    if 'searched_files' in item:
        files = item['searched_files']
        if files:
            lines.append(f"      Searched Files: {len(files)} file(s)")
            for f in files[:3]:  # Show first 3
                lines.append(f"        - {f}")
            if len(files) > 3:
                lines.append(f"        ... and {len(files) - 3} more")
    
    return lines


def _format_waived_item(item: Dict[str, Any], index: int) -> List[str]:
    """
    格式化waived item
    
    额外字段:
    - Waiver Pattern
    - Waiver Reason
    - Tag
    """
    lines = _format_item_detail(item, index)
    
    # Add waiver-specific fields
    if 'waiver_pattern' in item:
        lines.append(f"      Waiver Pattern: {item['waiver_pattern']}")
    if 'waiver_reason' in item:
        lines.append(f"      Waiver Reason: {item['waiver_reason']}")
    if 'tag' in item:
        lines.append(f"      Tag: {item['tag']}")
    
    return lines


def generate_summary_dict(
    l5_output: Dict[str, Any],
    type_id: int,
    item_id: str,
    item_desc: str,
    executed: bool = True
) -> Dict[str, Any]:
    """
    生成Summary字典（用于YAML和Excel）
    
    输出:
        {
            'executed': True,
            'status': 'PASS',
            'description': 'xxx',
            'failures': [...],  # missing + extra (severity != INFO)
            'warnings': [...]   # missing + extra (severity == INFO)
        }
    """
    status = l5_output.get('status', 'FAIL')
    
    # Collect failures and warnings
    failures = []
    warnings = []
    
    # Process missing items
    for item in l5_output.get('missing_items', []):
        if item.get('severity') == 'INFO':
            warnings.append(_summarize_violation(item, kind='MISSING'))
        else:
            failures.append(_summarize_violation(item, kind='MISSING'))
    
    # Process extra items
    for item in l5_output.get('extra_items', []):
        if item.get('severity') == 'INFO':
            warnings.append(_summarize_violation(item, kind='EXTRA'))
        else:
            failures.append(_summarize_violation(item, kind='EXTRA'))
    
    return {
        'executed': executed,
        'status': status,
        'description': item_desc,
        'failures': failures,
        'warnings': warnings
    }


def _summarize_violation(item: Dict[str, Any], kind: str) -> Dict[str, Any]:
    """
    汇总单个violation为简化格式
    
    输出:
        {
            'kind': 'MISSING' | 'EXTRA',
            'detail': str,
            'source_file': str,
            'line_number': int | None
        }
    """
    # Build detail string
    if 'expected' in item:
        detail = f"Expected: {item['expected']}"
    elif 'value' in item:
        detail = f"Value: {item['value']}"
    else:
        detail = str(item.get('description', 'Unknown'))
    
    return {
        'kind': kind,
        'detail': detail,
        'source_file': item.get('source_file', ''),
        'line_number': item.get('line_number')
    }
