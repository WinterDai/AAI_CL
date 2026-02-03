"""
L5: Output Controller - CR5 Strict Key Filtering
Plan.txt Section 4
"""

from typing import Dict, Any, Set

# CR5 Locked key sets by Type ID (Plan.txt Section 4)
TYPE_KEYS = {
    1: {'status', 'found_items', 'missing_items'},
    2: {'status', 'found_items', 'missing_items', 'extra_items'},
    3: {'status', 'found_items', 'missing_items', 'extra_items', 'waived', 'unused_waivers'},
    4: {'status', 'found_items', 'missing_items', 'waived', 'unused_waivers'}
}


def filter_output_keys(
    internal_result: Dict[str, Any],
    type_id: int
) -> Dict[str, Any]:
    """
    输出控制器主函数 - CR5 Strict Key Filtering (Plan.txt Section 4)
    
    输入:
        internal_result: L4输出的完整内部结果（包含所有keys）
        type_id: 1-4
        
    输出:
        Dict - 仅包含type_id对应的CR5 keys
        
    实现细节:
    - 过滤到精确的key集合
    - 所有keys必须存在，即使是空列表
    - 不存在的keys使用默认空列表
    
    CR5 Keys by Type:
    - Type 1: status, found_items, missing_items
    - Type 2: status, found_items, missing_items, extra_items
    - Type 3: status, found_items, missing_items, extra_items, waived, unused_waivers
    - Type 4: status, found_items, missing_items, waived, unused_waivers
    """
    if type_id not in TYPE_KEYS:
        raise ValueError(f"Invalid type_id: {type_id}. Must be 1-4.")
    
    required_keys = TYPE_KEYS[type_id]
    
    # Build filtered output with defaults
    filtered_output = {}
    
    for key in required_keys:
        if key == 'status':
            # Status must exist
            filtered_output['status'] = internal_result.get('status', 'FAIL')
        else:
            # List keys default to empty list
            filtered_output[key] = internal_result.get(key, [])
    
    return filtered_output


def validate_cr5_output(
    output: Dict[str, Any],
    type_id: int
) -> bool:
    """
    验证输出是否符合CR5规范
    
    检查:
    1. Key集合精确匹配TYPE_KEYS[type_id]
    2. 无多余keys
    3. 所有必需keys存在
    
    输入:
        output: 待验证的输出字典
        type_id: 1-4
        
    输出:
        bool - True if valid, False otherwise
    """
    if type_id not in TYPE_KEYS:
        return False
    
    required_keys = TYPE_KEYS[type_id]
    output_keys = set(output.keys())
    
    return output_keys == required_keys


def get_missing_keys(output: Dict[str, Any], type_id: int) -> Set[str]:
    """
    获取缺失的必需keys
    
    输入:
        output: 输出字典
        type_id: 1-4
        
    输出:
        Set[str] - 缺失的keys
    """
    if type_id not in TYPE_KEYS:
        return set()
    
    required_keys = TYPE_KEYS[type_id]
    output_keys = set(output.keys())
    
    return required_keys - output_keys


def get_extra_keys(output: Dict[str, Any], type_id: int) -> Set[str]:
    """
    获取多余的keys
    
    输入:
        output: 输出字典
        type_id: 1-4
        
    输出:
        Set[str] - 多余的keys
    """
    if type_id not in TYPE_KEYS:
        return set()
    
    required_keys = TYPE_KEYS[type_id]
    output_keys = set(output.keys())
    
    return output_keys - required_keys


def initialize_internal_result() -> Dict[str, Any]:
    """
    初始化内部结果状态 (Plan.txt Section 2)
    
    输出:
        Dict - 包含所有internal keys的初始状态
        
    实现细节:
    - Framework内部总是初始化所有list keys为空列表
    - Output Controller在最后应用CR5过滤
    """
    return {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [],
        'extra_items': [],
        'waived': [],
        'unused_waivers': []
    }
