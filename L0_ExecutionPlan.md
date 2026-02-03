# L0 执行Plan: Type决策器 + 配置验证器

> **🚨 CRITICAL ARCHITECTURE PRINCIPLE (基于Plan.txt证据)**
> 
> Plan.txt未定义**任何**数据结构类（除Exception外）
> - Plan.txt Line 25: `ParsedItem = Dict[str, Any]`
> - Plan.txt Line 69: `MatchResult = Dict[str, Any]`
> - Plan.txt **没有**: `class NormalizedConfig`, `class ParseResult`, `class IOEngine`
> 
> **结论**: 所有跨层传递的数据结构**必须使用Dict**
> - 内部工具类（如RecursionGuard）可以存在，但不跨层
> - Enum类型用于常量定义，不属于数据结构

## 1. 层级职责
Layer 0负责配置规范化、类型决策和运行时调度。这是框架的入口层，必须确保所有配置在进入后续层级前已经过验证和规范化。

## 2. 交付物
- `type_dispatcher.py` - Type决策器模块
- `config_validator.py` - 配置验证和规范化模块
- `exceptions.py` - 自定义异常类
- `test_l0.py` - Layer 0单元测试

## 3. 公开API

### 3.1 Config Validator API
```python
from typing import Dict, Any, Union, List

# ⚠️ CRITICAL CLARIFICATION (Plan.txt Evidence):
# Plan.txt defines NO classes except Exception types.
# Plan.txt Line 25: ParsedItem = Dict[str, Any]
# Plan.txt Line 69: MatchResult = Dict[str, Any]
# Plan.txt NEVER defines: class NormalizedConfig, class ParseResult, etc.
# 
# CONCLUSION: All data structures MUST use Dict, NOT custom classes.
# This applies to normalized config, parsing results, check results, etc.

class ConfigError(Exception):
    """配置验证失败时抛出"""
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
        
    实现细节:
        - 缺失的列表字段(pattern_items/waive_items)默认设为空列表 []
        - 缺失的字符串字段(description)默认设为空字符串 ""
        - input_files为必需参数，不提供默认值
        
    注意: Plan.txt未定义NormalizedConfig类，使用Dict
    """
    pass

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
    pass

def validate_domain(req_value: Union[str, int], waiver_value: Union[str, int]):
    """
    Domain约束验证 (Locked)
    
    约束:
    - req.value MUST be either N/A or an integer >= 1
    - waiver.value MUST be either N/A or an integer >= 0
    
    异常:
        ConfigError - 当值超出valid domain
    """
    pass
```

### 3.2 Type Dispatcher API
```python
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
        Type ID: 1, 2, 3, 或 4
    """
    pass

# Type Runner注册表 (Runtime Dispatch)
TYPE_RUNNERS = {
    1: None,  # Type 1 Runner (由L3提供)
    2: None,  # Type 2 Runner (由L3提供)
    3: None,  # Type 3 Runner (由L3+L4提供)
    4: None,  # Type 4 Runner (由L3+L4提供)
}

def register_type_runner(type_id: int, runner_func):
    """注册Type运行器"""
    TYPE_RUNNERS[type_id] = runner_func

def dispatch_runner(type_id: int, **kwargs) -> Dict:
    """
    调度对应Type的Runner
    
    输入:
        type_id: 1-4
        **kwargs: 传递给runner的参数
        
    输出:
        内部结果状态字典 (包含所有list keys)
    """
    pass
```

## 4. 输入输出Schema

### 4.1 输入Schema (Raw Config)
```python
{
    'requirements': {
        'value': int | str | None,        # 例如: 1, "2", "N/A", None
        'pattern_items': List[str]        # 例如: ["pattern1", "pattern2"]
    },
    'waivers': {
        'value': int | str | None,        # 例如: 0, "1", None, "N/A"
        'waive_items': List[str]          # 例如: ["waive1"]
    },
    'input_files': List[str],             # 例如: ["/path/to/file1"]
    'description': str                    # 例如: "Check XYZ"
}
```

### 4.2 输出Schema (Normalized Config)
```python
{
    'req_value': 'N/A' | int,             # 规范化后: 'N/A' 或 >= 1
    'waiver_value': 'N/A' | int,          # 规范化后: 'N/A' 或 >= 0
    'pattern_items': List[str],
    'waive_items': List[str],
    'input_files': List[str],
    'description': str,
    'type_id': int                        # 1, 2, 3, 或 4
}
```

### 4.3 内部结果状态初始化 (Locked)
```python
# Layer 0初始化后，传递给Type Runners的内部状态
{
    'status': None,                       # 待Type Runner填充
    'found_items': [],                    # 初始化为空列表
    'missing_items': [],                  # 初始化为空列表
    'extra_items': [],                    # 初始化为空列表
    'waived': [],                         # 初始化为空列表
    'unused_waivers': [],                 # 初始化为空列表
    'searched_files': []                  # 待L2填充
}
```

## 5. 依赖关系

### Mock依赖
- **TYPE_RUNNERS**: 在L0测试时mock为返回固定字典的函数
- **文件系统**: 不涉及文件IO，无需mock

### 真实依赖
- 无外部依赖（纯Python标准库）

## 6. 测试策略

### 6.1 N/A定义测试
```python
def test_na_definition():
    """测试N/A定义的所有情况"""
    # Case 1: missing key
    assert normalize_value(None) == 'N/A'
    
    # Case 2: null
    assert normalize_value(None) == 'N/A'
    
    # Case 3: string "N/A"
    assert normalize_value("N/A") == 'N/A'
    assert normalize_value("  N/A  ") == 'N/A'  # with whitespace
    
    # Case 4: Numeric 0 is NOT N/A
    assert normalize_value(0) == 0
    assert normalize_value("0") == 0  # string numeric
```

### 6.2 字符串数字解析测试
```python
def test_string_numeric_parsing():
    """测试字符串数字解析"""
    assert normalize_value("0") == 0
    assert normalize_value("2") == 2
    assert normalize_value("  10  ") == 10
    assert isinstance(normalize_value("5"), int)
```

### 6.3 Domain验证测试
```python
def test_domain_validation():
    """测试valid domain约束"""
    # Valid cases
    validate_domain('N/A', 'N/A')       # Type 1
    validate_domain(1, 'N/A')           # Type 2
    validate_domain(5, 0)               # Type 3
    validate_domain('N/A', 2)           # Type 4
    
    # Invalid cases - 必须抛出ConfigError
    with pytest.raises(ConfigError):
        validate_domain(0, 'N/A')       # req.value=0 invalid
    
    with pytest.raises(ConfigError):
        validate_domain(-1, 'N/A')      # req.value<0 invalid
    
    with pytest.raises(ConfigError):
        validate_domain('N/A', -1)      # waiver.value<0 invalid
    
    with pytest.raises(ConfigError):
        validate_domain(0, 0)           # req.value=0 invalid
```

### 6.4 Type决策器测试 (4种组合)
```python
def test_type_decision():
    """测试Type Decider的4种映射"""
    assert determine_type('N/A', 'N/A') == 1
    assert determine_type(1, 'N/A') == 2
    assert determine_type(2, 'N/A') == 2
    assert determine_type(1, 0) == 3
    assert determine_type(5, 2) == 3
    assert determine_type('N/A', 0) == 4
    assert determine_type('N/A', 3) == 4
```

### 6.5 边界条件测试
```python
def test_edge_cases():
    """测试边界条件"""
    # req.value = 1 (最小valid值)
    assert determine_type(1, 'N/A') == 2
    
    # waiver.value = 0 (最小valid值)
    assert determine_type('N/A', 0) == 4
    
    # 空pattern_items/waive_items
    config = validate_and_normalize_config(
        {'value': 'N/A', 'pattern_items': []},
        {'value': 'N/A', 'waive_items': []},
        [],
        ""
    )
    assert config['pattern_items'] == []
    assert config['waive_items'] == []
```

### 6.6 集成测试 (端到端)
```python
def test_l0_end_to_end():
    """测试L0完整流程"""
    # 模拟YAML config输入
    raw_config = {
        'requirements': {'value': "2", 'pattern_items': ["pat1"]},
        'waivers': {'value': None, 'waive_items': []},
        'input_files': ["/file1"],
        'description': "Test"
    }
    
    # 规范化
    normalized = validate_and_normalize_config(
        raw_config['requirements'],
        raw_config['waivers'],
        raw_config['input_files'],
        raw_config['description']
    )
    
    # 验证规范化结果
    assert normalized['req_value'] == 2
    assert normalized['waiver_value'] == 'N/A'
    
    # Type决策
    type_id = determine_type(normalized['req_value'], normalized['waiver_value'])
    assert type_id == 2
    
    # Mock runner调度
    def mock_type2_runner(**kwargs):
        return {'status': 'PASS', 'found_items': []}
    
    register_type_runner(2, mock_type2_runner)
    result = dispatch_runner(2, config=normalized)
    assert result['status'] == 'PASS'
```

## 7. 关键实现要求 (Plan.txt提取)

### 7.1 N/A定义 (Locked)
> **Plan.txt Section 2, Layer 0: Config Normalization & Validation (Locked)**
> - N/A Definition (Locked): missing key OR null OR (string after strip equals "N/A")
> - Numeric 0 is NOT N/A

### 7.2 字符串数字解析
> **Plan.txt Section 2, Layer 0**
> - If value is a string numeric (e.g., "0", "2"), Framework MUST parse to integer

### 7.3 Valid Domain约束 (Locked)
> **Plan.txt Section 2, Layer 0**
> - req.value MUST be either N/A or an integer >= 1
> - waiver.value MUST be either N/A or an integer >= 0
> - If outside domain, Framework MUST raise a ConfigError and MUST NOT dispatch any runner

### 7.4 Type映射 (Locked)
> **Plan.txt Section 2, Layer 0: Type Decider (Locked Mapping)**
> - req.value = N/A, waiver.value = N/A → Type 1
> - req.value >= 1, waiver.value = N/A → Type 2
> - req.value >= 1, waiver.value >= 0 → Type 3
> - req.value = N/A, waiver.value >= 0 → Type 4

### 7.5 内部结果状态初始化 (Locked)
> **Plan.txt Section 2, Layer 0: Internal Result State (Locked)**
> - Framework internal result state MUST always initialize list keys (empty lists by default), regardless of Type
> - Keys: found_items, missing_items, extra_items, waived, unused_waivers

### 7.6 Runtime Dispatch
> **Plan.txt Section 2, Layer 0: Orchestrator**
> - Runtime Dispatch (Locked): TYPE_RUNNERS = {1:..., 2:..., 3:..., 4:...}

## 8. 验收标准

### 必须通过的测试
- [ ] 所有N/A定义case正确识别
- [ ] 字符串数字正确解析为int
- [ ] Domain验证正确拒绝invalid值
- [ ] 4种Type映射100%准确
- [ ] ConfigError在invalid情况下正确抛出
- [ ] 内部结果状态正确初始化所有list keys
- [ ] Mock runner调度成功

### 代码质量要求
- [ ] 类型注解完整 (typing模块)
- [ ] Docstring遵循Google风格
- [ ] 单元测试覆盖率 >= 95%
- [ ] 无pylint警告

### 性能要求
- [ ] normalize_value性能 < 1ms
- [ ] determine_type性能 < 0.1ms

### Gate 3集成要求 (Locked)
- [ ] L0实现必须通过Gate 3的6个配置测试
- [ ] Type决策逻辑对所有config组合正确
- [ ] 内部结果状态初始化对所有Types工作正常
- [ ] Type runners接收到正确规范化的configs

**Gate 3 Test Matrix (Plan.txt Section 5):**
- Config 1: Type 1 (req=N/A, waiver=N/A)
- Config 2: Type 2 (req=1, waiver=N/A)
- Config 3: Type 3 Global (req=1, waiver=0)
- Config 4: Type 3 Selective (req=1, waiver=1)
- Config 5: Type 4 Global (req=N/A, waiver=0)
- Config 6: Type 4 Selective (req=N/A, waiver=1)

## 9. 调试提示

### 常见错误
1. **0被误判为N/A**: 检查normalize_value中是否正确区分numeric 0和missing/null
2. **字符串"0"未转换**: 确保string numeric parsing在N/A判断之前执行
3. **ConfigError未抛出**: 检查validate_domain的边界条件逻辑

### 调试日志建议
```python
import logging
logger = logging.getLogger(__name__)

def normalize_value(raw_value):
    logger.debug(f"normalize_value input: {raw_value} (type: {type(raw_value)})")
    result = ...
    logger.debug(f"normalize_value output: {result}")
    return result
```

## 10. 文件结构
```
L0/
├── type_dispatcher.py      # Type决策器实现
├── config_validator.py     # 配置验证和规范化
├── exceptions.py           # ConfigError等异常
├── test_l0.py              # 单元测试
└── README.md               # L0使用文档
```
