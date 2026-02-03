# L4 执行Plan: Waiver引擎

## 1. 层级职责
Layer 4负责应用waiver逻辑，区分Global Waiver (value=0) 和 Selective Waiver (value>0)，实现MUTATE和MOVE两种不同的语义。

## 2. 交付物
- `waiver_engine.py` - Waiver引擎主模块
- `global_waiver.py` - Global Waiver实现 (MUTATE)
- `selective_waiver.py` - Selective Waiver实现 (MOVE)
- `test_l4.py` - Layer 4单元测试

## 3. 公开API

### 3.1 Main Waiver Engine API
```python
from typing import Dict, List, Callable, Optional

# Atom B函数类型定义 (Plan.txt Section 1)
AtomBFunc = Callable[[str, str, Optional[Dict], str, str], Dict]  
# validate_logic(text, pattern, parsed_fields, default_match, regex_mode) -> MatchResult

# 返回值类型：Dict (修改后的check_result)
# 原地修改check_result字典并返回
# (Plan.txt Section 3: Global/Selective Waiver语义)

def apply_waivers(
    check_result: Dict,
    waiver_config: Dict,
    type_id: int,
    atom_b_func: AtomBFunc
) -> Dict:
    """
    Waiver引擎主函数 (Plan.txt Section 3)
    
    根据waiver.value决定策略:
    - value = 0: Global Waiver (MUTATE语义)
    - value > 0: Selective Waiver (MOVE语义)
    
    输入:
        check_result: L3的CheckResult
        waiver_config: {value, waive_items}
        type_id: 3 或 4
        atom_b_func: Atom B函数引用
        
    输出:
        Dict - 修改后的check_result (原地修改并返回同一个dict)
        (Plan.txt Section 3: Invariant规则)
    """
    pass
```

### 3.2 Global Waiver API (value=0)
```python
def apply_global_waiver(
    check_result: Dict,
    waive_items: List[str]
) -> Dict:
    """
    Global Waiver实现 (Plan.txt Section 3 - Locked)
    
    MUTATE语义:
    1. Violations保持在missing_items/extra_items（不删除）
    2. 对每个violation设置:
       - severity = "INFO"
       - tag = "[WAIVED_AS_INFO]"
    3. 为每个waive_items注入comment到waived:
       - waiver_pattern: str(item)
       - waiver_reason: "Global Waiver"
       - tag: "[WAIVED_INFO]"
    4. Force status = "PASS"
    5. unused_waivers = []
    
    输入:
        check_result: {missing_items, extra_items, status, ...}
        waive_items: List[str]
        
    输出:
        Dict - 修改后的check_result
        
    语义:
        原地修改传入的check_result字典，然后返回它（方便链式调用）
        不创建新dict，直接修改参数
    """
    pass

def mutate_violation_to_info(violation: Dict):
    """
    原地修改violation为INFO级别
    
    修改:
    - severity = "INFO"
    - tag = "[WAIVED_AS_INFO]"
    
    禁止:
    - 删除/重命名现有keys
    """
    pass

def create_waived_info_comment(waive_pattern: str) -> Dict:
    """
    创建Global Waiver的comment record
    
    输出:
    {
        'waiver_pattern': str,
        'waiver_reason': "Global Waiver",
        'tag': "[WAIVED_INFO]"
    }
    """
    pass
```

### 3.3 Selective Waiver API (value>0)
```python
def apply_selective_waiver(
    check_result: Dict,
    waive_items: List[str],
    type_id: int,
    atom_b_func: Callable
) -> Dict:
    """
    Selective Waiver实现 (Plan.txt Section 3 - Locked)
    
    MOVE语义:
    1. Target set:
       - Type 4: missing_items only
       - Type 3: missing_items then extra_items
    2. Violation iteration order:
       - missing_items列表顺序优先
       - 然后extra_items列表顺序
    3. Policy Injection (Locked):
       - default_match="exact"
       - regex_mode="match"
    4. N-to-M matching:
       - 一个waive pattern可以匹配多个violations
       - 追踪每个pattern的match count
    5. Conflict determinism:
       - 对每个violation，按waive_items顺序评估
       - 第一个匹配的pattern胜出
       - 一个violation最多被移动一次
    6. MOVE操作:
       - 从missing_items/extra_items中删除
       - 添加到waived，包含:
         - 原violation所有字段
         - waiver_pattern: str
         - waiver_reason: "N/A"
         - tag: "[WAIVER]"
    7. 保持顺序:
       - 剩余violations保持原顺序
       - waived保持violation iteration顺序
    8. unused_waivers:
       - 只包含match count=0的patterns
       - 保持waive_items顺序
       - {'pattern': str, 'reason': "Not matched"}
    9. Status更新:
       - Type 4: status = PASS iff missing_items为空
    
    输入:
        check_result: {missing_items, extra_items, status, ...}
        waive_items: List[str]
        type_id: 3 或 4
        atom_b_func: Atom B函数
        
    输出:
        Dict - 修改后的check_result
        
    语义:
        原地修改传入的check_result字典（MOVE violations）
        从missing/extra中删除，添加到waived
        然后返回修改后的同一个dict
    """
    pass

def match_violation_with_waivers(
    violation: Dict,
    waive_items: List[str],
    atom_b_func: Callable
) -> str | None:
    """
    为violation找到第一个匹配的waiver pattern
    
    Violation Text Source (Locked):
    violation_text = v.get("expected") or v.get("value") or v.get("description") or ""
    Framework MUST cast violation_text = str(violation_text)
    
    Policy Injection:
    validate_logic(text=violation_text, pattern=str(waive_pattern),
                   parsed_fields=None, default_match="exact", regex_mode="match")
    
    **为什么 `parsed_fields=None`? (Rationale):**
    - Violations（来自missing_items/extra_items）是**ghost records**或**未消费的ParsedItems**
    - Violation text从 `expected`, `value`, 或 `description` 字段提取
    - 这些是**扁平字典字段**，不是带有 `parsed_fields` 的ParsedItem结构
    - 传递 `None` 向Atom B表明不需要自定义字段匹配
    
    输入:
        violation: violation字典
        waive_items: waiver patterns列表
        atom_b_func: Atom B函数
        
    输出:
        匹配的pattern字符串，或None
    """
    pass

def move_to_waived(
    violation: Dict,
    waiver_pattern: str
) -> Dict:
    """
    创建waived record (MOVE语义)
    
    输出:
    原violation所有字段 + 
    {
        'waiver_pattern': str,
        'waiver_reason': "N/A",
        'tag': "[WAIVER]"
    }
    """
    pass
```

## 4. 输入输出Schema

### 4.1 输入Schema
```python
# apply_waivers输入
{
    'check_result': {
        'status': 'PASS' | 'FAIL',
        'found_items': List[Dict],
        'missing_items': List[Dict],
        'extra_items': List[Dict],  # Type 3 only
        'waived': [],
        'unused_waivers': [],
        'searched_files': List[str]
    },
    'waiver_config': {
        'value': 0 | int > 0,
        'waive_items': List[str]
    },
    'type_id': 3 | 4,
    'atom_b_func': Callable
}
```

### 4.2 输出Schema (Waiver后)
```python
# Global Waiver (value=0) 输出
{
    'status': 'PASS',  # 强制PASS
    'found_items': List[Dict],
    'missing_items': [  # 保留但MUTATE
        {
            ...原字段,
            'severity': "INFO",
            'tag': "[WAIVED_AS_INFO]"
        },
        ...
    ],
    'extra_items': [  # Type 3, 保留但MUTATE
        {
            ...原字段,
            'severity': "INFO",
            'tag': "[WAIVED_AS_INFO]"
        },
        ...
    ],
    'waived': [  # Comment records
        {
            'waiver_pattern': str,
            'waiver_reason': "Global Waiver",
            'tag': "[WAIVED_INFO]"
        },
        ...
    ],
    'unused_waivers': [],  # 总是空
    'searched_files': List[str]
}

# Selective Waiver (value>0) 输出
{
    'status': 'PASS' | 'FAIL',  # Type 4: PASS if missing_items空
    'found_items': List[Dict],
    'missing_items': [  # 移除了匹配的violations
        ...剩余violations
    ],
    'extra_items': [  # Type 3, 移除了匹配的violations
        ...剩余violations
    ],
    'waived': [  # MOVE过来的violations
        {
            ...原violation字段,
            'waiver_pattern': str,
            'waiver_reason': "N/A",
            'tag': "[WAIVER]"
        },
        ...
    ],
    'unused_waivers': [  # match count=0的patterns
        {
            'pattern': str,
            'reason': "Not matched"
        },
        ...
    ],
    'searched_files': List[str]
}
```

## 5. 依赖关系

### Mock依赖
- **Atom B函数**: Mock validate_logic用于selective matching
- **L3 CheckResult**: Mock check_result字典

### 真实依赖
- **L3 Check Assembler**: 接收CheckResult作为输入

## 6. 测试策略

### 6.1 Global Waiver (value=0) 测试
```python
def test_global_waiver_mutate():
    """测试Global Waiver的MUTATE语义"""
    check_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [
            {'description': 'test', 'expected': 'pattern1'}
        ],
        'extra_items': [],
        'waived': [],
        'unused_waivers': []
    }
    
    result = apply_global_waiver(
        check_result,
        waive_items=['waive1', 'waive2']
    )
    
    # 验证MUTATE
    assert result['status'] == 'PASS'
    assert len(result['missing_items']) == 1  # 保留
    assert result['missing_items'][0]['severity'] == 'INFO'
    assert result['missing_items'][0]['tag'] == '[WAIVED_AS_INFO]'
    
    # 验证comment injection
    assert len(result['waived']) == 2
    assert result['waived'][0]['waiver_pattern'] == 'waive1'
    assert result['waived'][0]['waiver_reason'] == 'Global Waiver'
    assert result['waived'][0]['tag'] == '[WAIVED_INFO]'
    
    # 验证unused_waivers
    assert result['unused_waivers'] == []

def test_global_waiver_type3_with_extra():
    """测试Global Waiver对Type 3的extra_items"""
    check_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [],
        'extra_items': [
            {'description': 'extra', 'value': 'extra1'}
        ],
        'waived': [],
        'unused_waivers': []
    }
    
    result = apply_global_waiver(check_result, ['waive1'])
    
    # extra_items也要MUTATE
    assert len(result['extra_items']) == 1
    assert result['extra_items'][0]['severity'] == 'INFO'
    assert result['extra_items'][0]['tag'] == '[WAIVED_AS_INFO]'
```

### 6.2 Selective Waiver (value>0) 测试
```python
def test_selective_waiver_move(mock_atom_b):
    """测试Selective Waiver的MOVE语义"""
    mock_atom_b.return_value = {'is_match': True, 'reason': '', 'kind': 'exact'}
    
    check_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [
            {'description': 'test', 'expected': 'pattern1'}
        ],
        'extra_items': [],
        'waived': [],
        'unused_waivers': []
    }
    
    result = apply_selective_waiver(
        check_result,
        waive_items=['pattern1'],
        type_id=4,
        atom_b_func=mock_atom_b
    )
    
    # 验证MOVE
    assert len(result['missing_items']) == 0  # 移除
    assert len(result['waived']) == 1  # 移动到这里
    assert result['waived'][0]['waiver_pattern'] == 'pattern1'
    assert result['waived'][0]['waiver_reason'] == 'N/A'
    assert result['waived'][0]['tag'] == '[WAIVER]'
    
    # Type 4: missing_items空 → PASS
    assert result['status'] == 'PASS'
    
    # unused_waivers应该为空（pattern1匹配了）
    assert len(result['unused_waivers']) == 0

def test_selective_waiver_unused():
    """测试unused_waivers追踪"""
    def atom_b_mock(text, pattern, **kwargs):
        return {'is_match': pattern == text, 'reason': '', 'kind': 'exact'}
    
    check_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [
            {'description': 'test', 'expected': 'pattern1'}
        ],
        'extra_items': [],
        'waived': [],
        'unused_waivers': []
    }
    
    result = apply_selective_waiver(
        check_result,
        waive_items=['pattern1', 'unused_pattern'],
        type_id=4,
        atom_b_func=atom_b_mock
    )
    
    # unused_pattern没有匹配任何violation
    assert len(result['unused_waivers']) == 1
    assert result['unused_waivers'][0]['pattern'] == 'unused_pattern'
    assert result['unused_waivers'][0]['reason'] == 'Not matched'

def test_selective_waiver_n_to_m_matching():
    """测试N-to-M matching"""
    mock_atom_b = lambda text, pattern, **kwargs: {
        'is_match': True, 'reason': '', 'kind': 'exact'
    }
    
    check_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [
            {'description': 'v1', 'expected': 'pattern1'},
            {'description': 'v2', 'expected': 'pattern1'},
            {'description': 'v3', 'expected': 'pattern1'}
        ],
        'extra_items': [],
        'waived': [],
        'unused_waivers': []
    }
    
    result = apply_selective_waiver(
        check_result,
        waive_items=['pattern1'],  # 一个pattern
        type_id=4,
        atom_b_func=mock_atom_b
    )
    
    # 一个pattern可以匹配多个violations
    assert len(result['missing_items']) == 0
    assert len(result['waived']) == 3
    assert len(result['unused_waivers']) == 0
```

### 6.3 Violation Iteration Order测试
```python
def test_violation_iteration_order_type3():
    """测试Type 3的violation迭代顺序"""
    call_order = []
    
    def atom_b_capture(text, pattern, **kwargs):
        call_order.append(text)
        return {'is_match': False, 'reason': '', 'kind': 'exact'}
    
    check_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [
            {'description': 'm1', 'expected': 'miss1'},
            {'description': 'm2', 'expected': 'miss2'}
        ],
        'extra_items': [
            {'description': 'e1', 'value': 'extra1'},
            {'description': 'e2', 'value': 'extra2'}
        ],
        'waived': [],
        'unused_waivers': []
    }
    
    apply_selective_waiver(
        check_result,
        waive_items=['pattern1'],
        type_id=3,
        atom_b_func=atom_b_capture
    )
    
    # 验证missing_items优先，然后extra_items
    assert call_order[0] == 'miss1'
    assert call_order[1] == 'miss2'
    assert call_order[2] == 'extra1'
    assert call_order[3] == 'extra2'
```

### 6.4 Policy Injection测试
```python
def test_selective_waiver_policy_injection():
    """测试selective waiver的policy injection"""
    call_args = []
    
    def atom_b_capture(*args, **kwargs):
        call_args.append((args, kwargs))
        return {'is_match': True, 'reason': '', 'kind': 'exact'}
    
    check_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [
            {'description': 'test', 'expected': 'pattern1'}
        ],
        'extra_items': [],
        'waived': [],
        'unused_waivers': []
    }
    
    apply_selective_waiver(
        check_result,
        waive_items=['pattern1'],
        type_id=4,
        atom_b_func=atom_b_capture
    )
    
    # 验证policy injection
    assert call_args[0][1]['default_match'] == 'exact'
    assert call_args[0][1]['regex_mode'] == 'match'
    assert call_args[0][1]['parsed_fields'] is None
```

### 6.5 Violation Text Source测试
```python
def test_violation_text_source():
    """测试violation text提取优先级"""
    # expected > value > description
    
    def atom_b_capture(text, pattern, **kwargs):
        return {'is_match': text == 'expected_value', 'reason': '', 'kind': 'exact'}
    
    # Case 1: expected存在
    violation1 = {'expected': 'expected_value', 'value': 'value', 'description': 'desc'}
    result = match_violation_with_waivers(violation1, ['expected_value'], atom_b_capture)
    assert result == 'expected_value'
    
    # Case 2: 只有value
    def atom_b_value(text, pattern, **kwargs):
        return {'is_match': text == 'value_only', 'reason': '', 'kind': 'exact'}
    
    violation2 = {'value': 'value_only', 'description': 'desc'}
    result = match_violation_with_waivers(violation2, ['value_only'], atom_b_value)
    assert result == 'value_only'
    
    # Case 3: 只有description
    def atom_b_desc(text, pattern, **kwargs):
        return {'is_match': text == 'desc_only', 'reason': '', 'kind': 'exact'}
    
    violation3 = {'description': 'desc_only'}
    result = match_violation_with_waivers(violation3, ['desc_only'], atom_b_desc)
    assert result == 'desc_only'
```

## 7. 关键实现要求 (Plan.txt提取)

### 7.1 Global Waiver (Locked)
> **Plan.txt Section 3: Global Waiver (waiver.value = 0)**
> - Invariant (Persistence): Violations remain in missing_items / extra_items (do NOT remove)
> - Allowed Mutation Only: Set severity = "INFO", Set tag = "[WAIVED_AS_INFO]"
> - Comment Injection to waived: waiver_pattern, waiver_reason="Global Waiver", tag="[WAIVED_INFO]"
> - Global Status: Force status = "PASS"
> - unused_waivers: MUST be []

### 7.2 Selective Waiver (Locked)
> **Plan.txt Section 3: Selective Waiver (waiver.value > 0)**
> - Policy Injection: default_match="exact", regex_mode="match"
> - Target Set: Type 4: missing_items only; Type 3: missing_items then extra_items
> - Violation Iteration Order: missing_items list order first, then extra_items list order
> - Violation Text Source: v.get("expected") or v.get("value") or v.get("description") or ""
> - N-to-M Matching: One waive pattern may match multiple violations
> - Conflict Determinism: First matched pattern wins
> - Invariant (Removal): Matched violations MUST be MOVED out
> - Waived Output Schema: original fields + waiver_pattern, waiver_reason="N/A", tag="[WAIVER]"
> - Type 4 status: PASS iff missing_items is empty after MOVE

## 8. 验收标准

### 必须通过的测试
- [ ] Global Waiver正确MUTATE (severity+tag)
- [ ] Global Waiver强制status=PASS
- [ ] Global Waiver注入comments到waived
- [ ] Global Waiver的unused_waivers总是空
- [ ] Selective Waiver正确MOVE violations
- [ ] Selective Waiver的policy injection正确
- [ ] N-to-M matching正确
- [ ] unused_waivers正确追踪
- [ ] Violation iteration order正确 (missing→extra)
- [ ] Violation text source优先级正确
- [ ] Type 4 status更新正确

### 代码质量要求
- [ ] 类型注解完整
- [ ] 单元测试覆盖率 >= 95%
- [ ] MUTATE和MOVE语义清晰分离

### 性能要求
- [ ] 100 violations + 10 waivers < 50ms

## 9. 调试提示

### 常见错误
1. **MUTATE vs MOVE混淆**: Global保留violations，Selective删除
2. **unused_waivers错误**: Global应该总是空列表
3. **顺序错误**: Type 3必须先missing后extra

### 调试日志建议
```python
logger.debug(f"Waiver mode: {'Global' if value==0 else 'Selective'}")
logger.debug(f"Matching violation: {violation_text} with {waive_pattern}")
logger.debug(f"Match count: {match_counts}")
```

## 10. 文件结构
```
L4/
├── waiver_engine.py         # Waiver引擎主逻辑
├── global_waiver.py          # Global Waiver实现
├── selective_waiver.py       # Selective Waiver实现
├── test_l4.py                # 单元测试
└── README.md                 # L4使用文档
```
