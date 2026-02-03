"""
L4: Waiver Engine - Global and Selective Waiver Logic
Plan.txt Section 3
"""

from typing import Dict, Any, List, Callable, Optional

# Type aliases
AtomBFunc = Callable[[str, str, Optional[Dict], str, str], Dict]


def apply_waiver_rules(
    check_result: Dict[str, Any],
    waive_items: List[str],
    waiver_value: int,
    type_id: int,
    atom_b_func: AtomBFunc
) -> Dict[str, Any]:
    """
    应用waiver规则 (Plan.txt Section 3)
    
    输入:
        check_result: L3输出的check result（包含所有internal keys）
        waive_items: waiver patterns列表
        waiver_value: 0 (global) 或 >0 (selective)
        type_id: 3 或 4
        atom_b_func: Atom B函数
        
    输出:
        Dict - 修改后的check_result（原地修改）
        
    实现细节:
    - waiver_value = 0: Global waiver
    - waiver_value > 0: Selective waiver
    - Type 3: 处理 missing_items + extra_items
    - Type 4: 只处理 missing_items
    """
    # Initialize waived list if not exists
    if 'waived' not in check_result:
        check_result['waived'] = []
    
    if 'unused_waivers' not in check_result:
        check_result['unused_waivers'] = []
    
    if waiver_value == 0:
        # Global waiver
        apply_global_waiver(check_result, waive_items, type_id)
    else:
        # Selective waiver
        apply_selective_waiver(check_result, waive_items, type_id, atom_b_func)
    
    return check_result


def apply_global_waiver(
    check_result: Dict[str, Any],
    waive_items: List[str],
    type_id: int
):
    """
    Global Waiver (waiver.value = 0) - Locked
    
    实现细节:
    - Violations保持在missing/extra中（不删除）
    - 只修改: severity="INFO", tag="[WAIVED_AS_INFO]"
    - 追加waiver comments到每个violation
    - 强制status="PASS"
    - unused_waivers = []
    """
    # Target violations based on type
    violations = []
    if type_id == 4:
        violations = check_result.get('missing_items', [])
    elif type_id == 3:
        violations = check_result.get('missing_items', []) + check_result.get('extra_items', [])
    
    # Modify each violation
    for violation in violations:
        violation['severity'] = 'INFO'
        violation['tag'] = '[WAIVED_AS_INFO]'
    
    # Add waiver comments to waived list (for reporting)
    check_result['waived'] = []
    for item_str in waive_items:
        check_result['waived'].append({
            'waiver_pattern': str(item_str),
            'waiver_reason': "Global Waiver",
            'tag': "[WAIVED_INFO]"
        })
    
    # Force PASS
    check_result['status'] = 'PASS'
    
    # unused_waivers must be empty in global mode
    check_result['unused_waivers'] = []


def apply_selective_waiver(
    check_result: Dict[str, Any],
    waive_items: List[str],
    type_id: int,
    atom_b_func: AtomBFunc
):
    """
    Selective Waiver (waiver.value > 0) - Locked
    
    实现细节:
    - Policy injection: default_match="exact", regex_mode="match"
    - Target: Type 4 (missing only), Type 3 (missing + extra)
    - Violation iteration: missing顺序 → extra顺序
    - N-to-M matching: 一个pattern可匹配多个violations
    - First match wins: 每个violation最多被waive一次
    - MOVE语义: 匹配的violations从missing/extra移到waived
    - Order stability: 剩余violations保持原顺序
    - unused_waivers: 零匹配的patterns
    - Type 4 status: missing为空则PASS，否则FAIL
    """
    # Collect target violations in order
    violations_with_source = []
    
    missing_items = check_result.get('missing_items', [])
    for v in missing_items:
        violations_with_source.append((v, 'missing'))
    
    if type_id == 3:
        extra_items = check_result.get('extra_items', [])
        for v in extra_items:
            violations_with_source.append((v, 'extra'))
    
    # Track matches per pattern
    pattern_match_counts = {str(pattern): 0 for pattern in waive_items}
    waived_list = []
    
    # Mark violations to remove
    violations_to_remove = {'missing': set(), 'extra': set()}
    
    # Match violations with waivers
    for idx, (violation, source) in enumerate(violations_with_source):
        matched_pattern = match_violation_with_waivers(violation, waive_items, atom_b_func)
        
        if matched_pattern:
            # Move to waived
            waived_item = {
                **violation,
                'waiver_pattern': matched_pattern,
                'waiver_reason': "N/A",
                'tag': "[WAIVER]"
            }
            waived_list.append(waived_item)
            
            # Mark for removal
            violations_to_remove[source].add(id(violation))
            
            # Track match
            pattern_match_counts[matched_pattern] += 1
    
    # Remove waived violations (maintain order)
    new_missing = [v for v in missing_items if id(v) not in violations_to_remove['missing']]
    check_result['missing_items'] = new_missing
    
    if type_id == 3:
        extra_items = check_result.get('extra_items', [])
        new_extra = [v for v in extra_items if id(v) not in violations_to_remove['extra']]
        check_result['extra_items'] = new_extra
    
    # Update waived list
    check_result['waived'] = waived_list
    
    # Compute unused_waivers
    unused_waivers = []
    for pattern_str in waive_items:
        if pattern_match_counts[str(pattern_str)] == 0:
            unused_waivers.append({
                'pattern': str(pattern_str),
                'reason': "Not matched"
            })
    check_result['unused_waivers'] = unused_waivers
    
    # Update status for Type 4
    if type_id == 4:
        check_result['status'] = 'PASS' if len(check_result['missing_items']) == 0 else 'FAIL'


def match_violation_with_waivers(
    violation: Dict,
    waive_items: List[str],
    atom_b_func: AtomBFunc
) -> Optional[str]:
    """
    为violation找到第一个匹配的waiver pattern
    
    Violation Text Source (Locked):
    violation_text = v.get("expected") or v.get("value") or v.get("description") or ""
    Framework MUST cast violation_text = str(violation_text)
    
    Policy Injection:
    validate_logic(text=violation_text, pattern=str(waive_pattern),
                   parsed_fields=None, default_match="exact", regex_mode="match")
    
    输入:
        violation: violation字典
        waive_items: waiver patterns列表
        atom_b_func: Atom B函数
        
    输出:
        str | None - 匹配的pattern，或None
    """
    # Extract violation text
    violation_text = (
        violation.get("expected") or 
        violation.get("value") or 
        violation.get("description") or 
        ""
    )
    violation_text = str(violation_text)
    
    # Try each waiver pattern in order
    for waive_pattern in waive_items:
        match_result = atom_b_func(
            text=violation_text,
            pattern=str(waive_pattern),
            parsed_fields=None,
            default_match="exact",
            regex_mode="match"
        )
        
        if match_result.get('is_match'):
            return str(waive_pattern)
    
    return None
