"""
L3: Check Assembler - Type 1-4 Logic Implementation
Plan.txt Section 2, Layer 3
"""

from typing import Dict, Any, List, Callable, Set, Optional

# Type aliases for clarity
ParsedItem = Dict[str, Any]
CheckResult = Dict[str, Any]
AtomBFunc = Callable[[str, str, Optional[Dict], str, str], Dict]
AtomCFunc = Callable[[List[Dict]], Dict]


def assemble_check(
    requirements: Dict[str, Any],
    parsed_items_all: List[ParsedItem],
    searched_files: List[str],
    atom_b_func: AtomBFunc,
    atom_c_func: AtomCFunc,
    description: str
) -> CheckResult:
    """
    Check装配主函数 (Plan.txt Section 2, Layer 3)
    
    输入:
        requirements: 规范化后的requirements字典
            {
                'req_value': Union[str, int],
                'waiver_value': Union[str, int],
                'pattern_items': List[str],
                'waive_items': List[str],
                'input_files': List[str],
                'description': str
            }
        parsed_items_all: 所有ParsedItem
        searched_files: 搜索过的文件列表
        atom_b_func: Atom B函数
        atom_c_func: Atom C函数
        description: item描述
        
    输出:
        CheckResult - 包含所有内部状态keys的字典
        
    实现细节:
    - Type 2/3: 使用 requirements['pattern_items'] 作为requirement patterns
    - 所有 found_items/missing_items/extra_items 必须增强 'description' 字段
    - description增强方式: {**item, 'description': description}
    """
    from L0_Config.config_validator import determine_type
    
    req_value = requirements['req_value']
    waiver_value = requirements['waiver_value']
    pattern_items = requirements.get('pattern_items', [])
    
    # Determine type
    type_id = determine_type(req_value, waiver_value)
    
    # Route to appropriate checker
    if type_id in [2, 3]:
        # Pattern path
        result = check_pattern_requirements(
            parsed_items_all=parsed_items_all,
            pattern_items=pattern_items,
            atom_b_func=atom_b_func,
            description=description,
            searched_files=searched_files
        )
    else:  # type_id in [1, 4]
        # Existence path
        result = check_existence_requirements(
            parsed_items_all=parsed_items_all,
            atom_c_func=atom_c_func,
            description=description,
            searched_files=searched_files
        )
    
    return result


def check_pattern_requirements(
    parsed_items_all: List[ParsedItem],
    pattern_items: List[str],
    atom_b_func: AtomBFunc,
    description: str,
    searched_files: List[str]
) -> CheckResult:
    """
    Pattern Check实现 (Plan.txt Section 2, Layer 3 - Type 2/3)
    
    策略: First Unconsumed Match
    - 对每个requirement pattern按顺序
    - 扫描ParsedItems_All（稳定顺序）
    - 第一个匹配且未消费的item → 消费，加入found_items
    - 无匹配 → 生成missing_item（包含ghost字段）
    
    Policy Injection (Locked):
    - default_match="contains"
    - regex_mode="search"
    
    边界情况:
    - pattern_items为空: found=[], missing=[], extra=所有items, status=FAIL
    """
    found_items = []
    missing_items = []
    consumed_indices = set()
    
    # Process each pattern
    for pattern in pattern_items:
        matched_item = consume_first_match(
            parsed_items=parsed_items_all,
            pattern=pattern,
            consumed_indices=consumed_indices,
            atom_b_func=atom_b_func
        )
        
        if matched_item:
            # Add description
            found_item = {**matched_item, 'description': description}
            found_items.append(found_item)
        else:
            # Create ghost missing item
            missing_item = create_ghost_missing_item(
                pattern=pattern,
                description=description,
                searched_files=searched_files
            )
            missing_items.append(missing_item)
    
    # Extra items = unconsumed items
    extra_items = []
    for idx, item in enumerate(parsed_items_all):
        if idx not in consumed_indices:
            extra_item = {**item, 'description': description}
            extra_items.append(extra_item)
    
    # Status
    status = 'PASS' if (len(missing_items) == 0 and len(extra_items) == 0) else 'FAIL'
    
    return {
        'found_items': found_items,
        'missing_items': missing_items,
        'extra_items': extra_items,
        'status': status
    }


def consume_first_match(
    parsed_items: List[ParsedItem],
    pattern: str,
    consumed_indices: Set[int],
    atom_b_func: AtomBFunc
) -> Optional[ParsedItem]:
    """
    First Unconsumed Match策略实现
    
    Policy Injection (Locked):
    - default_match="contains"
    - regex_mode="search"
    """
    for idx, item in enumerate(parsed_items):
        if idx in consumed_indices:
            continue
        
        # Call Atom B
        text = item.get('value', '')
        parsed_fields = item.get('parsed_fields')
        
        match_result = atom_b_func(
            text=text,
            pattern=pattern,
            parsed_fields=parsed_fields,
            default_match="contains",
            regex_mode="search"
        )
        
        if match_result.get('is_match'):
            consumed_indices.add(idx)
            return item
    
    return None


def check_existence_requirements(
    parsed_items_all: List[ParsedItem],
    atom_c_func: AtomCFunc,
    description: str,
    searched_files: List[str]
) -> CheckResult:
    """
    Existence Check实现 (Plan.txt Section 2, Layer 3 - Type 1/4)
    
    流程:
    1. 调用Atom C检查existence
    2. 如果is_match=True:
       - found_items = evidence (增强description)
       - missing_items = []
       - status = PASS
    3. 如果is_match=False:
       - found_items = []
       - missing_items = [1个ghost record]
       - expected = "Existence check failed"
       - status = FAIL
    """
    # Call Atom C
    atom_c_result = atom_c_func(parsed_items_all)
    
    if atom_c_result.get('is_match'):
        # Success case
        evidence = atom_c_result.get('evidence', [])
        # Add description to each evidence item
        found_items = [{**item, 'description': description} for item in evidence]
        
        return {
            'found_items': found_items,
            'missing_items': [],
            'status': 'PASS'
        }
    else:
        # Failure case: create ghost record
        ghost_record = {
            'description': description,
            'expected': "Existence check failed",
            'searched_files': searched_files,
            'line_number': None,
            'source_file': "",
            'matched_content': "",
            'parsed_fields': {}
        }
        
        return {
            'found_items': [],
            'missing_items': [ghost_record],
            'status': 'FAIL'
        }


def create_ghost_missing_item(
    pattern: str,
    description: str,
    searched_files: List[str]
) -> Dict:
    """
    创建ghost missing item (Plan.txt Section 2, Layer 3)
    
    输出:
        {
            'description': str,
            'expected': str(pattern),
            'searched_files': List[str],
            'line_number': None,
            'source_file': "",
            'matched_content': "",
            'parsed_fields': {}
        }
    """
    return {
        'description': description,
        'expected': str(pattern),
        'searched_files': searched_files,
        'line_number': None,
        'source_file': "",
        'matched_content': "",
        'parsed_fields': {}
    }
