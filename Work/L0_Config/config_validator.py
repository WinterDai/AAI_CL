"""
L0: Config Validator - Configuration Normalization and Type Decision
Plan.txt Section 2, Layer 0
"""

from typing import Dict, Any, Union, List


class ConfigError(Exception):
    """Configuration validation error"""
    pass


def validate_and_normalize_config(
    requirements: Dict[str, Any],
    waivers: Dict[str, Any],
    input_files: List[str],
    description: str = ""
) -> Dict[str, Any]:
    """
    配置规范化和验证主函数 (Plan.txt Section 2, Layer 0)
    
    输入:
        requirements: {'value': int|str|None, 'pattern_items': List[str]}
        waivers: {'value': int|str|None, 'waive_items': List[str]}
        input_files: List[str]
        description: str
        
    输出:
        Dict[str, Any] - 规范化后的配置字典
        {
            'req_value': Union[str, int],      # 'N/A' 或 >= 1
            'waiver_value': Union[str, int],   # 'N/A' 或 >= 0
            'pattern_items': List[str],        # 缺失时默认为 []
            'waive_items': List[str],          # 缺失时默认为 []
            'input_files': List[str],
            'description': str                 # 缺失时默认为 ""
        }
        
    异常:
        ConfigError - 当配置不符合domain约束时
    """
    # Normalize values
    req_value = normalize_value(requirements.get('value'))
    waiver_value = normalize_value(waivers.get('value'))
    
    # Validate domain constraints
    validate_domain(req_value, waiver_value)
    
    # Build normalized config with defaults
    normalized_config = {
        'req_value': req_value,
        'waiver_value': waiver_value,
        'pattern_items': requirements.get('pattern_items', []),
        'waive_items': waivers.get('waive_items', []),
        'input_files': input_files,
        'description': description if description else ""
    }
    
    return normalized_config


def normalize_value(raw_value: Any) -> Union[str, int]:
    """
    值规范化逻辑 (Plan.txt Section 2, Layer 0)
    
    N/A定义 (Locked):
    - missing key OR null OR (string after strip equals "N/A")
    - Numeric 0 is NOT N/A
    
    字符串数字解析:
    - "0", "2" → parse to int
    
    返回: 'N/A' 或 int
    """
    # Missing key or None → N/A
    if raw_value is None:
        return 'N/A'
    
    # String handling
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        # Check for N/A string
        if stripped == "N/A":
            return 'N/A'
        # Try to parse as integer
        try:
            return int(stripped)
        except ValueError:
            # Not a valid integer string, return N/A
            return 'N/A'
    
    # Integer handling (including 0)
    if isinstance(raw_value, int):
        return raw_value
    
    # Other types → N/A
    return 'N/A'


def validate_domain(req_value: Union[str, int], waiver_value: Union[str, int]):
    """
    Domain约束验证 (Locked)
    
    约束:
    - req.value MUST be either N/A or an integer >= 1
    - waiver.value MUST be either N/A or an integer >= 0
    
    异常:
        ConfigError - 当值超出valid domain
    """
    # Validate req.value
    if req_value != 'N/A':
        if not isinstance(req_value, int) or req_value < 1:
            raise ConfigError(f"req.value must be 'N/A' or >= 1, got: {req_value}")
    
    # Validate waiver.value
    if waiver_value != 'N/A':
        if not isinstance(waiver_value, int) or waiver_value < 0:
            raise ConfigError(f"waiver.value must be 'N/A' or >= 0, got: {waiver_value}")


def determine_type(req_value: Union[str, int], waiver_value: Union[str, int]) -> int:
    """
    Type决策器 (Plan.txt Section 2, Layer 0 - Locked Mapping)
    
    映射规则:
    - req.value = N/A, waiver.value = N/A → Type 1
    - req.value >= 1, waiver.value = N/A → Type 2
    - req.value >= 1, waiver.value >= 0 → Type 3
    - req.value = N/A, waiver.value >= 0 → Type 4
    
    输入:
        req_value: 'N/A' 或 >= 1
        waiver_value: 'N/A' 或 >= 0
        
    输出:
        int - Type ID (1-4)
    """
    req_is_na = (req_value == 'N/A')
    waiver_is_na = (waiver_value == 'N/A')
    
    if req_is_na and waiver_is_na:
        return 1
    elif not req_is_na and waiver_is_na:
        return 2
    elif not req_is_na and not waiver_is_na:
        return 3
    else:  # req_is_na and not waiver_is_na
        return 4
