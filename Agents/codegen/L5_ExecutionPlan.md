# L5 执行Plan: 输出控制器

## 1. 层级职责
Layer 5负责CR5 (Contract Requirement 5) 严格的key过滤，确保最终输出只包含当前Type所需的keys，移除内部状态keys。

## 2. 交付物
- `output_controller.py` - 输出控制主模块
- `cr5_schema.py` - CR5 key集合定义
- `test_l5.py` - Layer 5单元测试

## 3. 公开API

### 3.1 Main Output Controller API
```python
from typing import Dict, List, Set

# CR5 Key集合定义 (Plan.txt Section 4 - Locked)
TYPE_KEYS = {
    1: {'status', 'found_items', 'missing_items'},
    2: {'status', 'found_items', 'missing_items', 'extra_items'},
    3: {'status', 'found_items', 'missing_items', 'extra_items', 'waived', 'unused_waivers'},
    4: {'status', 'found_items', 'missing_items', 'waived', 'unused_waivers'}
}

def filter_output_keys(
    internal_result: Dict,
    type_id: int
) -> Dict:
    """
    CR5输出控制器 (Plan.txt Section 4)
    
    功能:
    1. 根据Type ID获取允许的key集合
    2. 过滤internal_result，只保留允许的keys
    3. 确保所有必需keys存在（即使为空列表）
    4. 返回CR5兼容的输出字典
    
    输入:
        internal_result: L4的完整内部结果状态
        type_id: 1, 2, 3, 或 4
        
    输出:
        CR5过滤后的字典
    """
    pass

def ensure_required_keys(
    filtered_result: Dict,
    required_keys: Set[str]
):
    """
    确保所有必需keys存在
    
    对于缺失的keys:
    - 如果是列表类型: 添加空列表 []
    - 如果是status: 添加 None 或 "UNKNOWN"
    
    输入:
        filtered_result: 已过滤的结果
        required_keys: 必需的key集合
    """
    pass
```

### 3.2 Schema Validator API
```python
def validate_cr5_output(
    output: Dict,
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
        True if valid, False otherwise
    """
    pass

def get_missing_keys(output: Dict, type_id: int) -> Set[str]:
    """获取缺失的必需keys"""
    pass

def get_extra_keys(output: Dict, type_id: int) -> Set[str]:
    """获取多余的keys"""
    pass
```

## 4. 输入输出Schema

### 4.1 输入Schema (Internal Result)
```python
# L4输出的完整内部状态
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[Dict],
    'missing_items': List[Dict],
    'extra_items': List[Dict],
    'waived': List[Dict],
    'unused_waivers': List[Dict],
    'searched_files': List[str],
    # 可能还有其他内部keys
}
```

### 4.2 输出Schema (CR5过滤后)
```python
# Type 1 输出 (3 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[Dict],
    'missing_items': List[Dict]
}

# Type 2 输出 (4 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[Dict],
    'missing_items': List[Dict],
    'extra_items': List[Dict]
}

# Type 3 输出 (6 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[Dict],
    'missing_items': List[Dict],
    'extra_items': List[Dict],
    'waived': List[Dict],
    'unused_waivers': List[Dict]
}

# Type 4 输出 (5 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[Dict],
    'missing_items': List[Dict],
    'waived': List[Dict],
    'unused_waivers': List[Dict]
}
```

## 5. 依赖关系

### Mock依赖
- **L4 Internal Result**: Mock完整的内部结果状态

### 真实依赖
- 无外部依赖（纯数据过滤）

## 6. 测试策略

### 6.1 Type 1 输出过滤测试
```python
def test_type1_output_filtering():
    """测试Type 1的key过滤"""
    internal_result = {
        'status': 'PASS',
        'found_items': [{'value': 'v1'}],
        'missing_items': [],
        'extra_items': [],  # 不应出现在输出
        'waived': [],  # 不应出现在输出
        'unused_waivers': [],  # 不应出现在输出
        'searched_files': ['/f1']  # 不应出现在输出
    }
    
    output = filter_output_keys(internal_result, type_id=1)
    
    assert set(output.keys()) == {'status', 'found_items', 'missing_items'}
    assert 'extra_items' not in output
    assert 'waived' not in output
    assert 'searched_files' not in output

def test_type1_ensure_empty_lists():
    """测试Type 1确保空列表存在"""
    internal_result = {
        'status': 'PASS'
        # 缺少found_items和missing_items
    }
    
    output = filter_output_keys(internal_result, type_id=1)
    
    assert 'found_items' in output
    assert output['found_items'] == []
    assert 'missing_items' in output
    assert output['missing_items'] == []
```

### 6.2 Type 2 输出过滤测试
```python
def test_type2_output_filtering():
    """测试Type 2的key过滤"""
    internal_result = {
        'status': 'FAIL',
        'found_items': [],
        'missing_items': [{'expected': 'pattern1'}],
        'extra_items': [{'value': 'extra1'}],
        'waived': [],  # 不应出现
        'unused_waivers': [],  # 不应出现
        'searched_files': ['/f1']
    }
    
    output = filter_output_keys(internal_result, type_id=2)
    
    assert set(output.keys()) == {'status', 'found_items', 'missing_items', 'extra_items'}
    assert 'waived' not in output
    assert 'unused_waivers' not in output
```

### 6.3 Type 3 输出过滤测试
```python
def test_type3_output_filtering():
    """测试Type 3的key过滤（全部6个keys）"""
    internal_result = {
        'status': 'PASS',
        'found_items': [],
        'missing_items': [],
        'extra_items': [],
        'waived': [{'waiver_pattern': 'w1'}],
        'unused_waivers': [],
        'searched_files': ['/f1']  # 不应出现
    }
    
    output = filter_output_keys(internal_result, type_id=3)
    
    expected_keys = {'status', 'found_items', 'missing_items', 'extra_items', 'waived', 'unused_waivers'}
    assert set(output.keys()) == expected_keys
    assert 'searched_files' not in output
```

### 6.4 Type 4 输出过滤测试
```python
def test_type4_output_filtering():
    """测试Type 4的key过滤（无extra_items）"""
    internal_result = {
        'status': 'PASS',
        'found_items': [],
        'missing_items': [],
        'extra_items': [{'value': 'should_not_appear'}],  # Type 4不应有
        'waived': [],
        'unused_waivers': [],
        'searched_files': ['/f1']
    }
    
    output = filter_output_keys(internal_result, type_id=4)
    
    expected_keys = {'status', 'found_items', 'missing_items', 'waived', 'unused_waivers'}
    assert set(output.keys()) == expected_keys
    assert 'extra_items' not in output
```

### 6.5 CR5验证测试
```python
def test_cr5_validation_pass():
    """测试CR5验证通过"""
    output_type2 = {
        'status': 'PASS',
        'found_items': [],
        'missing_items': [],
        'extra_items': []
    }
    
    assert validate_cr5_output(output_type2, type_id=2) is True

def test_cr5_validation_missing_keys():
    """测试CR5验证失败：缺少keys"""
    output_incomplete = {
        'status': 'PASS',
        'found_items': []
        # 缺少missing_items
    }
    
    assert validate_cr5_output(output_incomplete, type_id=1) is False
    missing = get_missing_keys(output_incomplete, type_id=1)
    assert 'missing_items' in missing

def test_cr5_validation_extra_keys():
    """测试CR5验证失败：多余keys"""
    output_extra = {
        'status': 'PASS',
        'found_items': [],
        'missing_items': [],
        'searched_files': ['/f1']  # 多余key
    }
    
    assert validate_cr5_output(output_extra, type_id=1) is False
    extra = get_extra_keys(output_extra, type_id=1)
    assert 'searched_files' in extra
```

### 6.6 边界条件测试
```python
def test_empty_internal_result():
    """测试空内部结果"""
    internal_result = {}
    
    output = filter_output_keys(internal_result, type_id=1)
    
    # 应该填充默认值
    assert 'status' in output
    assert 'found_items' in output
    assert output['found_items'] == []
    assert 'missing_items' in output
    assert output['missing_items'] == []

def test_all_types_key_count():
    """测试各Type的key数量"""
    assert len(TYPE_KEYS[1]) == 3
    assert len(TYPE_KEYS[2]) == 4
    assert len(TYPE_KEYS[3]) == 6
    assert len(TYPE_KEYS[4]) == 5
```

## 7. 关键实现要求 (Plan.txt提取)

### 7.1 CR5 Strict Keys (Locked)
> **Plan.txt Section 4: Output Controller (CR5 Strict Keys, Locked)**
> - Must filter keys to exact set by Type ID
> - Keys must exist even if empty lists
> 
> Key sets:
> - Type 1: status, found_items, missing_items
> - Type 2: status, found_items, missing_items, extra_items
> - Type 3: status, found_items, missing_items, extra_items, waived, unused_waivers
> - Type 4: status, found_items, missing_items, waived, unused_waivers

### 7.2 内部结果状态
> **Plan.txt Section 2, Layer 0: Internal Result State (Locked)**
> - Framework internal result state MUST always initialize list keys (empty lists by default)
> - Output Controller applies CR5 filtering only at final output

## 8. 验收标准

### 必须通过的测试
- [ ] Type 1-4的key过滤完全正确
- [ ] 无多余keys泄漏到输出
- [ ] 缺失keys自动填充为空列表
- [ ] CR5验证正确识别invalid输出
- [ ] get_missing_keys和get_extra_keys正确
- [ ] 所有Type的key数量正确

### 代码质量要求
- [ ] 类型注解完整
- [ ] 单元测试覆盖率 >= 95%
- [ ] TYPE_KEYS常量清晰定义

### 性能要求
- [ ] 过滤操作 < 1ms

## 9. 调试提示

### 常见错误
1. **Key泄漏**: 确保只保留TYPE_KEYS中定义的keys
2. **缺失keys**: 使用ensure_required_keys填充
3. **Type混淆**: 检查type_id是否正确传递

### 调试日志建议
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Filtering for Type {type_id}")
logger.debug(f"Input keys: {set(internal_result.keys())}")
logger.debug(f"Expected keys: {TYPE_KEYS[type_id]}")
logger.debug(f"Output keys: {set(output.keys())}")
```

## 10. 文件结构
```
L5/
├── output_controller.py    # 输出控制主逻辑
├── cr5_schema.py            # CR5 key定义
├── test_l5.py               # 单元测试
└── README.md                # L5使用文档
```

## 11. CR5 Key集合速查表

| Type | Key Count | Keys |
|------|-----------|------|
| Type 1 | 3 | status, found_items, missing_items |
| Type 2 | 4 | status, found_items, missing_items, extra_items |
| Type 3 | 6 | status, found_items, missing_items, extra_items, waived, unused_waivers |
| Type 4 | 5 | status, found_items, missing_items, waived, unused_waivers |

**Key差异分析:**
- Type 1/2: 无waiver相关keys
- Type 2/3: 有extra_items (Pattern Check)
- Type 1/4: 无extra_items (Existence Check)
- Type 3/4: 有waived和unused_waivers

## 12. 集成示例

```python
# 完整流程示例
def full_pipeline_example():
    # L0: 配置规范化和Type决策
    normalized_config = validate_and_normalize_config(...)
    type_id = determine_type(normalized_config['req_value'], normalized_config['waiver_value'])
    
    # L1: 文件读取
    text = read_file_text(input_file)
    
    # L2: 解析编排 (returns Tuple, not class)
    parsed_items_all, searched_files = orchestrate_parsing(input_files, atom_a, io_engine)
    
    # L3: Check组装
    check_result = assemble_check_result(
        type_id, 
        parsed_items_all,
        requirements,
        searched_files,
        atom_b, atom_c, description
    )
    
    # L4: Waiver引擎
    if type_id in [3, 4]:
        waiver_result = apply_waivers(check_result, waiver_config, type_id, atom_b)
        internal_result = {**check_result, **waiver_result}
    else:
        internal_result = check_result
    
    # L5: 输出控制 (CR5过滤)
    final_output = filter_output_keys(internal_result, type_id)
    
    return final_output
```
