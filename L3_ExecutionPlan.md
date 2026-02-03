# L3 执行Plan: Check组装器

## 1. 层级职责
Layer 3负责根据Type执行不同的检查策略，包括Pattern Check（Type 2/3）和Existence Check（Type 1/4），并生成包含found_items、missing_items、extra_items的结果。

## 2. 交付物
- `check_assembler.py` - Check组装主模块
- `pattern_checker.py` - Pattern Check实现 (Type 2/3)
- `existence_checker.py` - Existence Check实现 (Type 1/4)
- `ghost_generator.py` - Ghost字段生成器
- `test_l3.py` - Layer 3单元测试

## 3. 公开API

### 3.0 Atom B Interface Specification (Plan_v2.txt Section 1 - Locked)

#### 函数签名与MatchResult Schema

```python
from typing import Dict, Optional, Any

AtomBFunc = Callable[[str, str, Optional[Dict], str, str], Dict]
# validate_logic(text, pattern, parsed_fields, default_match, regex_mode) -> MatchResult

# MatchResult Schema (Plan_v2.txt Section 1 - Locked)
# {
#     'is_match': bool,
#     'reason': str,
#     'kind': str  # 匹配类型: "exact", "contains", "wildcard", "regex", "alternatives"
# }
```

#### Pattern Syntax Specification (Plan_v2.txt Section 1 - Locked)

**Atom B匹配逻辑优先级** (从高到低):

1. **Alternatives Logic** (`|` 分隔符)
   - 示例: `"ERROR|WARNING|FAIL"`
   - 语义: 任一分段匹配即为True（使用contains语义）
   - **关键**: 分段内的regex/wildcard字符视为**字面量**
   - kind值: `"alternatives"`

2. **Regex Logic** (`regex:` 前缀)
   - 示例: `"regex:^ERROR.*line [0-9]+"`
   - 语义: 去除 `"regex:"` 前缀后，作为正则表达式编译
   - Policy注入点: `regex_mode` 控制 `re.search` vs `re.match`
   - 错误处理: regex编译失败时返回 `is_match=False`，reason包含错误信息
   - kind值: `"regex"`

3. **Wildcard Logic** (包含 `*` 或 `?`)
   - 示例: `"ERROR*"`，`"test_?.log"`
   - 语义: 使用 `fnmatch.fnmatchcase`（区分大小写）
   - kind值: `"wildcard"`

4. **Default Logic** (字面量字符串)
   - Policy注入点: `default_match` 控制 `"contains"` vs `"exact"`
   - kind值: `"contains"` 或 `"exact"`

**重要约束 (Locked)**:
- `regex:` 前缀是**强制性的** - 没有前缀的正则表达式会被当作字面量或wildcard
- Alternatives中的 `regex:^a` 会被当作字面量字符串 `"regex:^a"` 匹配

#### Gate 2 测试要求 (Plan_v2.txt Section 5 - Locked)

Atom B实现必须通过以下7个测试向量：

1. **None-Safety**
   ```python
   validate_logic("abc", "a", parsed_fields=None)  # 不得抛出异常
   ```

2. **Empty Alternatives**
   ```python
   validate_logic("abc", "|a||")  # → is_match=True, kind="alternatives"
   ```

3. **Bad Regex**
   ```python
   validate_logic("abc", "regex:[", regex_mode="search")  
   # → is_match=False, kind="regex", reason startswith "Invalid Regex:"
   ```

4. **Literal Alternatives** (regex字符当字面量)
   ```python
   validate_logic("regex:^a", "regex:^a|zzz")  # → is_match=True (contains literal)
   validate_logic("abc", "regex:^a|zzz")       # → is_match=False
   ```

5. **Wildcard Priority**
   ```python
   validate_logic("abc", "a*c")  # → kind="wildcard"
   ```

6. **Default Strategy Policy**
   ```python
   validate_logic("abc", "b", default_match="contains")  # → is_match=True, kind="contains"
   validate_logic("abc", "b", default_match="exact")    # → is_match=False, kind="exact"
   ```

7. **regex_mode Invalid Value**
   ```python
   validate_logic("abc", "regex:^a", regex_mode="BAD")  
   # → 不得抛出异常，行为等同于 regex_mode="search"
   ```

### 3.1 Main Assembler API
```python
from typing import List, Dict, Callable, Any, Optional

# Atom函数类型定义 (Plan.txt Section 1)
AtomBFunc = Callable[[str, str, Optional[Dict], str, str], Dict]  
# validate_logic(text, pattern, parsed_fields, default_match, regex_mode) -> MatchResult

AtomCFunc = Callable[[List[Dict]], Dict]  
# check_existence(items) -> {'is_match': bool, 'reason': str, 'evidence': List[ParsedItem]}

# 返回值类型：Dict (不是Class对象)
# CheckResultDict Schema:
# {
#     'status': 'PASS' | 'FAIL',
#     'found_items': List[Dict],
#     'missing_items': List[Dict],
#     'extra_items': List[Dict],
#     'waived': List[Dict],
#     'unused_waivers': List[Dict],
#     'searched_files': List[str]
# }

def assemble_check_result(
    type_id: int,
    parsed_items_all: List[Dict],
    requirements: Dict,
    searched_files: List[str],
    atom_b_func: AtomBFunc,
    atom_c_func: Optional[AtomCFunc],
    description: str
) -> Dict:
    """
    Check组装主函数 (Plan.txt Section 2, Layer 3)
    
    根据Type ID调度不同的检查策略:
    - Type 1: Existence Check (Atom C)
    - Type 2: Pattern Check (Atom B)
    - Type 3: Pattern Check (Atom B) + Waiver Engine
    - Type 4: Existence Check (Atom C) + Waiver Engine
    
    输入:
        type_id: 1-4
        parsed_items_all: L2的解析结果
        requirements: Dict - L0规范化后的完整配置
            {
                'req_value': Union[str, int],     # 'N/A' 或 >= 1
                'waiver_value': Union[str, int],  # 'N/A' 或 >= 0
                'pattern_items': List[str],        # Type 2/3使用
                'waive_items': List[str],
                'input_files': List[str],
                'description': str                 # item的描述
            }
        searched_files: 搜索过的文件列表
        atom_b_func: Atom B函数引用
        atom_c_func: Atom C函数引用
        description: item描述 (也包含在requirements['description']中)
        
    输出:
        Dict - 包含所有内部状态keys的字典
        (Plan.txt Section 2, Layer 0: Internal Result State)
        
    关键实现细节 (Plan.txt Locked):
    - Type 2/3: 使用 requirements['pattern_items'] 作为requirement patterns
    - 所有 found_items/missing_items/extra_items 必须增强 'description' 字段
    - description值来自输入参数 description (或 requirements['description'])
    - description增强方式: {**item, 'description': description} (浅拷贝+添加字段)
    """
    pass
```

### 3.2 Pattern Checker API (Type 2/3)
```python
def check_pattern_requirements(
    parsed_items_all: List[Dict],
    pattern_items: List[str],
    atom_b_func: Callable,
    description: str,
    searched_files: List[str]
) -> Dict:
    """
    Pattern Check实现 (Plan.txt Section 2, Layer 3)
    
    策略: First Unconsumed Match
    - 对每个requirement pattern按顺序
    - 扫描ParsedItems_All（稳定顺序）
    - 第一个匹配且未消费的item → 消费，加入found_items
    - 无匹配 → 生成missing_item（包含ghost字段）
    
    Policy Injection (Locked):
    - default_match="contains"
    - regex_mode="search"
    
    输入:
        parsed_items_all: 所有ParsedItem
        pattern_items: requirements['pattern_items']
        atom_b_func: Atom B函数
        description: item描述
        searched_files: 搜索文件列表
        
    输出:
        {
            'found_items': List[Dict],
            'missing_items': List[Dict],  # 包含ghost字段
            'extra_items': List[Dict],
            'status': 'PASS' | 'FAIL'
        }
        
    关键实现 (Plan.txt Section 2, Layer 3 - Locked):
    1. found_items: 每个item = ParsedItem完整字段 + {'description': description}
    2. missing_items: 每个item必须包含:
       - 'description': description  # 添加同样的description
       - 'expected': str(req_pattern)
       - 'searched_files': searched_files  # 传入的完整列表
       - 'line_number': None
       - 'source_file': ""          # Ghost字段
       - 'matched_content': ""        # Ghost字段
       - 'parsed_fields': {}          # Ghost字段
    3. extra_items: 每个item = 未消费ParsedItem + {'description': description}
    4. status: PASS iff (missing_items == [] AND extra_items == []), else FAIL
    
    边界情况处理 (Locked):
    - 当pattern_items为空列表时:
      * found_items = [] (无pattern可匹配)
      * missing_items = [] (无pattern可缺失)
      * extra_items = 所有parsed_items_all (全部未消费) + description增强
      * status = 'FAIL' (因为extra_items非空)
    """
    pass

def consume_first_match(
    parsed_items: List[Dict],
    pattern: str,
    consumed_indices: set,
    atom_b_func: Callable
) -> Dict | None:
    """
    First Unconsumed Match策略实现
    
    输入:
        parsed_items: ParsedItem列表
        pattern: 要匹配的pattern
        consumed_indices: 已消费的索引集合
        atom_b_func: Atom B函数
        
    输出:
        匹配的ParsedItem或None
    """
    pass
```

### 3.3 Existence Checker API (Type 1/4)
```python
def check_existence_requirements(
    parsed_items_all: List[Dict],
    atom_c_func: Callable,
    description: str,
    searched_files: List[str]
) -> Dict:
    """
    Existence Check实现 (Plan.txt Section 2, Layer 3)
    
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
    
    输入:
        parsed_items_all: 所有ParsedItem
        atom_c_func: Atom C函数
        description: item描述
        searched_files: 搜索文件列表
        
    输出:
        {
            'found_items': List[Dict],
            'missing_items': List[Dict],  # 0或1个ghost
            'status': 'PASS' | 'FAIL'
        }
    """
    pass
```

### 3.4 Ghost Generator API
```python
def create_ghost_missing_item(
    pattern: str,
    description: str,
    searched_files: List[str]
) -> Dict:
    """
    生成missing_item的ghost字段 (Plan.txt Section 2, Layer 3)
    
    Ghost Fields (Locked):
    - description: str
    - expected: str(pattern)
    - searched_files: List[str] (排序的绝对路径)
    - line_number: None
    - source_file: ""
    - matched_content: ""
    - parsed_fields: {}
    
    输入:
        pattern: requirement pattern或"Existence check failed"
        description: item描述
        searched_files: 搜索文件列表
        
    输出:
        Ghost record字典
    """
    pass

def augment_with_description(item: Dict, description: str) -> Dict:
    """
    为found_items添加description字段
    
    输入:
        item: ParsedItem
        description: item描述
        
    输出:
        增强后的字典
    """
    pass
```

## 4. 输入输出Schema

### 4.1 输入Schema
```python
# assemble_check_result输入
{
    'type_id': int,  # 1, 2, 3, 或 4
    'parsed_items_all': [
        {
            'value': str,
            'source_file': str,
            'line_number': int | None,
            'matched_content': str,
            'parsed_fields': dict
        },
        ...
    ],
    'requirements': {
        'value': 'N/A' | int,
        'pattern_items': List[str]
    },
    'searched_files': List[str],
    'atom_b_func': Callable,
    'atom_c_func': Callable,
    'description': str
}
```

### 4.2 输出Schema (CheckResult)
```python
{
    'status': 'PASS' | 'FAIL',
    'found_items': [
        {
            'value': str,
            'source_file': str,
            'line_number': int | None,
            'matched_content': str,
            'parsed_fields': dict,
            'description': str  # 增强字段
        },
        ...
    ],
    'missing_items': [
        {
            'description': str,
            'expected': str,
            'searched_files': List[str],
            'line_number': None,
            'source_file': "",
            'matched_content': "",
            'parsed_fields': {}
        },
        ...
    ],
    'extra_items': [  # Type 2/3 only
        {
            'value': str,
            'source_file': str,
            'line_number': int | None,
            'matched_content': str,
            'parsed_fields': dict,
            'description': str
        },
        ...
    ],
    'waived': [],  # L4填充
    'unused_waivers': [],  # L4填充
    'searched_files': List[str]
}
```

## 5. 依赖关系

### Mock依赖
- **Atom B函数**: Mock validate_logic返回 {is_match, reason, kind}
- **Atom C函数**: Mock check_existence返回 {is_match, reason, evidence}

### 真实依赖
- **L2 ParseResult**: parsed_items_all和searched_files

## 6. 测试策略

### 6.1 Type 1 (Existence Check) 测试
```python
def test_type1_existence_pass(mock_atom_c):
    """测试Type 1 existence检查通过"""
    mock_atom_c.return_value = {
        'is_match': True,
        'reason': 'Found',
        'evidence': [
            {'value': 'v1', 'source_file': '/f1', 'line_number': 1,
             'matched_content': 'line1', 'parsed_fields': {}}
        ]
    }
    
    result = assemble_check_result(
        type_id=1,
        parsed_items_all=[...],
        requirements={'value': 'N/A', 'pattern_items': []},
        searched_files=['/f1'],
        atom_b_func=None,
        atom_c_func=mock_atom_c,
        description="Test"
    )
    
    # assemble_check_result returns Dict
    assert result['status'] == 'PASS'
    assert len(result['found_items']) == 1
    assert len(result['missing_items']) == 0

def test_type1_existence_fail(mock_atom_c):
    """测试Type 1 existence检查失败"""
    mock_atom_c.return_value = {
        'is_match': False,
        'reason': 'Not found',
        'evidence': []
    }
    
    result = assemble_check_result(
        type_id=1,
        parsed_items_all=[],
        requirements={'value': 'N/A', 'pattern_items': []},
        searched_files=['/f1'],
        atom_b_func=None,
        atom_c_func=mock_atom_c,
        description="Test"
    )
    
    assert result['status'] == 'FAIL'
    assert len(result['found_items']) == 0
    assert len(result['missing_items']) == 1
    assert result['missing_items'][0]['expected'] == "Existence check failed"
    assert result['missing_items'][0]['source_file'] == ""
    assert result['missing_items'][0]['line_number'] is None
```

### 6.2 Type 2 (Pattern Check) 测试
```python
def test_type2_all_found(mock_atom_b):
    """测试Type 2所有pattern都找到"""
    mock_atom_b.return_value = {'is_match': True, 'reason': 'match', 'kind': 'contains'}
    
    parsed_items = [
        {'value': 'pattern1', 'source_file': '/f1', 'line_number': 1,
         'matched_content': 'line1', 'parsed_fields': {}},
        {'value': 'pattern2', 'source_file': '/f1', 'line_number': 2,
         'matched_content': 'line2', 'parsed_fields': {}}
    ]
    
    result = assemble_check_result(
        type_id=2,
        parsed_items_all=parsed_items,
        requirements={'value': 2, 'pattern_items': ['pattern1', 'pattern2']},
        searched_files=['/f1'],
        atom_b_func=mock_atom_b,
        atom_c_func=None,
        description="Test"
    )
    
    assert result['status'] == 'PASS'
    assert len(result['found_items']) == 2
    assert len(result['missing_items']) == 0
    assert len(result['extra_items']) == 0

def test_type2_with_missing(mock_atom_b):
    """测试Type 2有missing pattern"""
    def atom_b_side_effect(text, pattern, **kwargs):
        return {'is_match': pattern in text, 'reason': '', 'kind': 'contains'}
    
    mock_atom_b.side_effect = atom_b_side_effect
    
    parsed_items = [
        {'value': 'pattern1', 'source_file': '/f1', 'line_number': 1,
         'matched_content': 'line1', 'parsed_fields': {}}
    ]
    
    result = assemble_check_result(
        type_id=2,
        parsed_items_all=parsed_items,
        requirements={'value': 2, 'pattern_items': ['pattern1', 'pattern2']},
        searched_files=['/f1'],
        atom_b_func=mock_atom_b,
        atom_c_func=None,
        description="Test"
    )
    
    assert result['status'] == 'FAIL'
    assert len(result['found_items']) == 1
    assert len(result['missing_items']) == 1
    assert result['missing_items'][0]['expected'] == 'pattern2'

def test_type2_with_extra(mock_atom_b):
    """测试Type 2有extra items"""
    mock_atom_b.return_value = {'is_match': True, 'reason': 'match', 'kind': 'contains'}
    
    parsed_items = [
        {'value': 'pattern1', 'source_file': '/f1', 'line_number': 1,
         'matched_content': 'line1', 'parsed_fields': {}},
        {'value': 'extra', 'source_file': '/f1', 'line_number': 2,
         'matched_content': 'line2', 'parsed_fields': {}}
    ]
    
    result = assemble_check_result(
        type_id=2,
        parsed_items_all=parsed_items,
        requirements={'value': 1, 'pattern_items': ['pattern1']},
        searched_files=['/f1'],
        atom_b_func=mock_atom_b,
        atom_c_func=None,
        description="Test"
    )
    
    assert result['status'] == 'FAIL'
    assert len(result['found_items']) == 1
    assert len(result['extra_items']) == 1
```

### 6.3 First Unconsumed Match策略测试
```python
def test_first_unconsumed_match():
    """测试First Unconsumed Match策略"""
    def atom_b_mock(text, pattern, **kwargs):
        return {'is_match': 'pattern' in text, 'reason': '', 'kind': 'contains'}
    
    parsed_items = [
        {'value': 'pattern match', 'source_file': '/f1', 'line_number': 1,
         'matched_content': 'line1', 'parsed_fields': {}},
        {'value': 'pattern match', 'source_file': '/f1', 'line_number': 2,
         'matched_content': 'line2', 'parsed_fields': {}}
    ]
    
    # 两个相同的pattern应该消费两个不同的item
    result = check_pattern_requirements(
        parsed_items,
        ['pattern', 'pattern'],
        atom_b_mock,
        "Test",
        ['/f1']
    )
    
    assert len(result['found_items']) == 2
    assert result['found_items'][0]['line_number'] == 1
    assert result['found_items'][1]['line_number'] == 2
```

### 6.4 Ghost字段测试
```python
def test_ghost_field_generation():
    """测试ghost字段生成"""
    ghost = create_ghost_missing_item(
        pattern="missing_pattern",
        description="Test Item",
        searched_files=["/file1", "/file2"]
    )
    
    assert ghost['description'] == "Test Item"
    assert ghost['expected'] == "missing_pattern"
    assert ghost['searched_files'] == ["/file1", "/file2"]
    assert ghost['line_number'] is None
    assert ghost['source_file'] == ""
    assert ghost['matched_content'] == ""
    assert ghost['parsed_fields'] == {}
```

### 6.5 Policy Injection测试
```python
def test_policy_injection_for_requirements(mock_atom_b):
    """测试requirements匹配的policy injection"""
    call_args = []
    
    def atom_b_capture(*args, **kwargs):
        call_args.append((args, kwargs))
        return {'is_match': True, 'reason': '', 'kind': 'contains'}
    
    mock_atom_b.side_effect = atom_b_capture
    
    parsed_items = [
        {'value': 'test', 'source_file': '/f1', 'line_number': 1,
         'matched_content': 'line1', 'parsed_fields': {}}
    ]
    
    check_pattern_requirements(
        parsed_items,
        ['pattern1'],
        mock_atom_b,
        "Test",
        ['/f1']
    )
    
    # 验证policy injection
    assert call_args[0][1]['default_match'] == 'contains'
    assert call_args[0][1]['regex_mode'] == 'search'
```

## 7. 关键实现要求 (Plan.txt提取)

### 7.1 Pattern Check策略 (Locked)
> **Plan.txt Section 2, Layer 3: Type 2 / Type 3 (Pattern Check Path)**
> - Consumption Strategy (Locked): First Unconsumed Match
> - For each requirement pattern (in order), scan ParsedItems_All (stable order)
> - First item that matches AND is not consumed → consume it, append to found_items

### 7.2 Policy Injection (Locked)
> **Plan.txt Section 2, Layer 3**
> - Policy Injection (Locked): Requirements matching MUST call Atom B with:
>   default_match="contains", regex_mode="search"

### 7.3 Atom B调用形式 (Locked)
> **Plan.txt Section 2, Layer 3: Atom B Call Form (Locked)**
> - Framework MUST call Atom B exactly as:
>   validate_logic(text=item['value'], pattern=str(req_pattern), 
>                  parsed_fields=item['parsed_fields'], 
>                  default_match="contains", regex_mode="search")

**精确参数传递 (Critical):**
```python
result = validate_logic(
    text=item['value'],                    # NOT just 'value'
    pattern=str(req_pattern),              # Explicit str() cast
    parsed_fields=item['parsed_fields'],   # Pass the parsed_fields dict
    default_match="contains",              # Policy injection (Locked)
    regex_mode="search"                    # Policy injection (Locked)
)
```

**关键细节:**
- `text` 参数接收 `item['value']` (ParsedItem中的value)
- `pattern` 参数接收 `str(req_pattern)` (显式字符串转换)
- `parsed_fields` 参数传递完整的 `item['parsed_fields']` 字典
- `default_match` 和 `regex_mode` 是策略注入，NOT from config

**Rationale:** 传递 `parsed_fields` 允许Atom B实现使用自定义字段进行匹配逻辑（可扩展性）

### 7.4 Ghost字段 (Locked)
> **Plan.txt Section 2, Layer 3: Output Schema Enforcer**
> - missing_items MUST contain:
>   - description, expected = str(req_pattern), searched_files
>   - line_number = None
>   - Ghost Fields: source_file = "", matched_content = "", parsed_fields = {}

### 7.5 Status规则 (Locked)
> **Plan.txt Section 2, Layer 3**
> - Type 2: status = PASS iff missing_items and extra_items are both empty; else FAIL

**Type 3 Status Override (Critical):**
> **Plan.txt Section 2, Layer 3, Line 224**
> - Type 3规则在**waiver处理之后**评估（Layer 4执行后）
> - **Selective waiver模式** (waiver.value > 0): MOVE操作后应用Type 2规则
> - **Global waiver模式** (waiver.value = 0): Status被**强制覆盖为PASS**，无论missing_items/extra_items中是否还有violations

**实现说明:**
Layer 3生成pre-waiver status，Layer 4（Waiver Engine）负责status override。
Layer 3必须正确计算初始status，以便Layer 4能正确应用override逻辑

### 7.6 Existence Check映射 (Locked)
> **Plan.txt Section 2, Layer 3: Type 1 / Type 4 (Existence Path)**
> - If AtomC.is_match=True: found_items = evidence, missing_items = [], status = PASS
> - If AtomC.is_match=False: found_items = [], missing_items = [1 ghost record], 
>   expected = "Existence check failed", status = FAIL

## 8. 验收标准

### 必须通过的测试
- [ ] Type 1 existence检查正确 (is_match=True/False)
- [ ] Type 2 pattern检查正确 (found/missing/extra)
- [ ] First Unconsumed Match策略正确
- [ ] Ghost字段完整且正确
- [ ] Policy injection正确 (contains/search)
- [ ] Status计算正确 (Type 2: missing+extra空则PASS)
- [ ] Atom B/C调用参数正确

### 代码质量要求
- [ ] 类型注解完整
- [ ] 单元测试覆盖率 >= 95%
- [ ] 消费逻辑清晰无bug

### 性能要求
- [ ] 1000个ParsedItem + 10个pattern < 100ms

## 9. 调试提示

### 常见错误
1. **重复消费**: 检查consumed_indices是否正确更新
2. **Ghost字段缺失**: 确保所有必需字段都初始化
3. **Status错误**: Type 2必须检查missing+extra都为空

### 调试日志建议
```python
logger.debug(f"Pattern: {pattern}, Consumed: {consumed_indices}")
logger.debug(f"Match result: {match_result}")
logger.debug(f"Status: missing={len(missing)}, extra={len(extra)}")
```

## 10. 文件结构
```
L3/
├── check_assembler.py      # Check组装主逻辑
├── pattern_checker.py       # Pattern Check实现
├── existence_checker.py     # Existence Check实现
├── ghost_generator.py       # Ghost字段生成
├── test_l3.py               # 单元测试
└── README.md                # L3使用文档
```
