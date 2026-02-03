# Gate 3: Integration Schema - 完整测试矩阵

> **Plan.txt Section 5, Gate 3, Lines 374-399**

## 1. 概述

Gate 3是集成测试的最高级别，验证完整pipeline（L0→L1→L2→L3→L4→L5）在所有Type和Waiver模式组合下的正确性。

**目标:** 确保框架在所有6种locked配置下都能正确工作。

---

## 2. 6种Locked配置 (Plan.txt Line 374-380)

| Config # | Type | req.value | waiver.value | 描述 | Waiver模式 |
|----------|------|-----------|--------------|------|-----------|
| **1** | Type 1 | N/A | N/A | Existence check, 无waiver | - |
| **2** | Type 2 | 1 | N/A | Pattern check, 无waiver | - |
| **3** | Type 3 | 1 | 0 | Pattern check, global waiver | Global (MUTATE) |
| **4** | Type 3 | 1 | 1 | Pattern check, selective waiver | Selective (MOVE) |
| **5** | Type 4 | N/A | 0 | Existence check, global waiver | Global (MUTATE) |
| **6** | Type 4 | N/A | 1 | Existence check, selective waiver | Selective (MOVE) |

**说明:**
- `req.value=N/A`: Existence check (调用Atom C)
- `req.value>=1`: Pattern check (调用Atom B)
- `waiver.value=N/A`: 无waiver处理
- `waiver.value=0`: Global waiver (MUTATE语义)
- `waiver.value>0`: Selective waiver (MOVE语义)

---

## 3. 每个配置的必需断言 (Plan.txt Lines 383-399)

### 3.1 通用断言 (所有6个配置)

#### A. Exact Key Set per Type (CR5) - Line 383

**要求:** 输出必须包含且仅包含Type对应的keys，无多余keys。

```python
TYPE_KEYS = {
    1: {'status', 'found_items', 'missing_items'},
    2: {'status', 'found_items', 'missing_items', 'extra_items'},
    3: {'status', 'found_items', 'missing_items', 'extra_items', 'waived', 'unused_waivers'},
    4: {'status', 'found_items', 'missing_items', 'waived', 'unused_waivers'}
}

def assert_cr5_keys(result, type_id):
    """验证CR5 key集合"""
    actual_keys = set(result.keys())
    expected_keys = TYPE_KEYS[type_id]
    
    assert actual_keys == expected_keys, \
        f"Type {type_id} keys mismatch. Expected: {expected_keys}, Got: {actual_keys}"
    
    # 检查无多余keys
    extra_keys = actual_keys - expected_keys
    assert len(extra_keys) == 0, f"Extra keys found: {extra_keys}"
    
    # 检查无缺失keys
    missing_keys = expected_keys - actual_keys
    assert len(missing_keys) == 0, f"Missing keys: {missing_keys}"
```

#### B. missing_items Schema - Lines 384-385

**要求:** `missing_items`中的每个item必须包含：
- `searched_files`: 排序的绝对路径列表（去重+字母序）
- Ghost fields: `source_file=""`, `matched_content=""`, `parsed_fields={}`

```python
def assert_missing_items_schema(result):
    """验证missing_items的schema"""
    for item in result['missing_items']:
        # 1. searched_files存在且是列表
        assert 'searched_files' in item
        assert isinstance(item['searched_files'], list)
        
        # 2. searched_files是排序的
        assert item['searched_files'] == sorted(item['searched_files']), \
            "searched_files must be alphabetically sorted"
        
        # 3. searched_files是绝对路径
        for path in item['searched_files']:
            assert os.path.isabs(path), f"Path must be absolute: {path}"
        
        # 4. Ghost fields存在且正确
        assert item['source_file'] == "", \
            f"Ghost field source_file must be empty string, got: {item['source_file']}"
        assert item['matched_content'] == "", \
            f"Ghost field matched_content must be empty string, got: {item['matched_content']}"
        assert item['parsed_fields'] == {}, \
            f"Ghost field parsed_fields must be empty dict, got: {item['parsed_fields']}"
        
        # 5. line_number必须是None
        assert item['line_number'] is None, \
            f"Ghost field line_number must be None, got: {item['line_number']}"
```

#### C. Parsing Recursion (PR2) - Lines 387-388

**要求:** 验证indirect_reference递归解析正确工作。

**测试策略:**
- Mock Atom A返回 `parsed_fields={"indirect_reference": "file2"}`
- 验证框架加载 `file2` 并合并到 `ParsedItems_All`

```python
def test_parsing_recursion():
    """测试PR2递归解析"""
    # Setup: file1引用file2
    def mock_atom_a(text, source_file):
        if source_file == "/file1":
            return [{
                'value': 'data1',
                'source_file': '/file1',
                'line_number': 1,
                'matched_content': 'line1',
                'parsed_fields': {'indirect_reference': '/file2'}  # 引用file2
            }]
        elif source_file == "/file2":
            return [{
                'value': 'data2',
                'source_file': '/file2',
                'line_number': 1,
                'matched_content': 'line1',
                'parsed_fields': {}
            }]
        return []
    
    # Run pipeline
    result = run_pipeline(
        input_files=["/file1"],
        atom_a=mock_atom_a,
        ...
    )
    
    # Assert: file2被加载
    assert '/file2' in result.get('searched_files', []), \
        "indirect_reference file2 should be loaded"
    
    # Assert: ParsedItems_All包含两个文件的数据
    # (通过found_items或missing_items间接验证)
```

#### D. Stable Sorting - Lines 390-391

**要求:** 验证 `ParsedItems_All` 遵循 File > Line > Extraction order。

```python
def test_stable_sorting():
    """测试稳定排序"""
    # Setup: 多个文件、多个行号、多个提取
    def mock_atom_a(text, source_file):
        if source_file == "/file1":
            return [
                {'value': 'f1_l1_e1', 'line_number': 1, ...},
                {'value': 'f1_l1_e2', 'line_number': 1, ...},  # 同行多提取
                {'value': 'f1_l5_e1', 'line_number': 5, ...},
                {'value': 'f1_none_e1', 'line_number': None, ...}  # None应该最后
            ]
        elif source_file == "/file2":
            return [
                {'value': 'f2_l1_e1', 'line_number': 1, ...}
            ]
        return []
    
    result = run_pipeline(input_files=["/file1", "/file2"], ...)
    
    # 验证顺序（通过found_items）
    values = [item['value'] for item in result['found_items']]
    
    # 文件顺序: file1 在 file2 之前
    assert values.index('f1_l1_e1') < values.index('f2_l1_e1')
    
    # 行号顺序: line 1 在 line 5 之前
    assert values.index('f1_l1_e1') < values.index('f1_l5_e1')
    
    # 提取顺序: 同文件同行，保持Atom A返回顺序
    assert values.index('f1_l1_e1') < values.index('f1_l1_e2')
    
    # None line_number在最后
    assert values.index('f1_none_e1') > values.index('f1_l5_e1')
```

---

### 3.2 Global Waiver断言 (Config 3, 5) - Lines 393-395

**要求:** 验证Global Waiver的MUTATE语义。

#### A. Violations保留但标记为INFO

```python
def assert_global_waiver_mutate(result):
    """验证Global Waiver的MUTATE操作"""
    # 1. Violations保留在missing_items/extra_items
    violations = result.get('missing_items', []) + result.get('extra_items', [])
    
    for violation in violations:
        # 2. severity被设置为"INFO"
        assert violation.get('severity') == 'INFO', \
            f"Global waiver violation must have severity='INFO', got: {violation.get('severity')}"
        
        # 3. tag被设置为"[WAIVED_AS_INFO]"
        assert violation.get('tag') == '[WAIVED_AS_INFO]', \
            f"Global waiver violation must have tag='[WAIVED_AS_INFO]', got: {violation.get('tag')}"
```

#### B. Waived包含Comment Records

```python
def assert_global_waiver_comments(result, waive_items):
    """验证Global Waiver的comment injection"""
    waived = result.get('waived', [])
    
    # 1. waived数量应该等于waive_items数量
    assert len(waived) == len(waive_items), \
        f"Global waiver should inject {len(waive_items)} comments, got {len(waived)}"
    
    for i, comment in enumerate(waived):
        # 2. waiver_pattern匹配waive_items
        assert comment['waiver_pattern'] == str(waive_items[i]), \
            f"waiver_pattern mismatch at index {i}"
        
        # 3. waiver_reason是"Global Waiver"
        assert comment['waiver_reason'] == 'Global Waiver', \
            f"waiver_reason must be 'Global Waiver', got: {comment['waiver_reason']}"
        
        # 4. tag是"[WAIVED_INFO]"
        assert comment['tag'] == '[WAIVED_INFO]', \
            f"Comment tag must be '[WAIVED_INFO]', got: {comment['tag']}"
```

#### C. unused_waivers必须为空

```python
def assert_global_waiver_no_unused(result):
    """验证Global Waiver的unused_waivers为空"""
    if 'unused_waivers' in result:  # Type 3/4才有这个key
        assert result['unused_waivers'] == [], \
            f"Global waiver unused_waivers must be empty, got: {result['unused_waivers']}"
```

#### D. Status强制为PASS

```python
def assert_global_waiver_status(result):
    """验证Global Waiver强制status=PASS"""
    assert result['status'] == 'PASS', \
        f"Global waiver must force status='PASS', got: {result['status']}"
```

---

### 3.3 Selective Waiver断言 (Config 4, 6) - Lines 397-399

**要求:** 验证Selective Waiver的MOVE语义。

#### A. Matched Violations被MOVE

```python
def assert_selective_waiver_move(result, expected_moved_count):
    """验证Selective Waiver的MOVE操作"""
    waived = result.get('waived', [])
    
    # 1. waived数量应该等于匹配的violations数量
    assert len(waived) == expected_moved_count, \
        f"Expected {expected_moved_count} violations moved to waived, got {len(waived)}"
    
    for waived_item in waived:
        # 2. 包含原violation的所有字段（description, expected/value等）
        assert 'description' in waived_item or 'expected' in waived_item or 'value' in waived_item, \
            "Waived item must contain original violation fields"
        
        # 3. waiver_pattern存在
        assert 'waiver_pattern' in waived_item, \
            "Waived item must have waiver_pattern"
        
        # 4. waiver_reason是"N/A"
        assert waived_item['waiver_reason'] == 'N/A', \
            f"Selective waiver_reason must be 'N/A', got: {waived_item['waiver_reason']}"
        
        # 5. tag是"[WAIVER]"
        assert waived_item['tag'] == '[WAIVER]', \
            f"Selective waiver tag must be '[WAIVER]', got: {waived_item['tag']}"
```

#### B. Violations不在missing/extra中

```python
def assert_selective_waiver_removed(result, waived_items):
    """验证被waived的violations已从missing/extra中移除"""
    violations = result.get('missing_items', []) + result.get('extra_items', [])
    waived = result.get('waived', [])
    
    # 获取waived items的expected/value
    waived_texts = set()
    for w in waived:
        text = w.get('expected') or w.get('value') or w.get('description') or ''
        waived_texts.add(text)
    
    # 验证这些text不在violations中
    for v in violations:
        v_text = v.get('expected') or v.get('value') or v.get('description') or ''
        assert v_text not in waived_texts, \
            f"Waived violation '{v_text}' should not remain in missing/extra"
```

#### C. unused_waivers仅包含零匹配patterns

```python
def assert_selective_waiver_unused(result, waive_items, expected_unused):
    """验证unused_waivers正确追踪"""
    unused = result.get('unused_waivers', [])
    
    # 1. unused数量正确
    assert len(unused) == len(expected_unused), \
        f"Expected {len(expected_unused)} unused waivers, got {len(unused)}"
    
    # 2. unused保持waive_items顺序
    unused_patterns = [u['pattern'] for u in unused]
    waive_items_str = [str(w) for w in waive_items]
    
    for pattern in unused_patterns:
        assert pattern in waive_items_str, \
            f"Unused pattern '{pattern}' not in original waive_items"
    
    # 3. 每个unused有reason="Not matched"
    for u in unused:
        assert u['reason'] == 'Not matched', \
            f"Unused waiver reason must be 'Not matched', got: {u['reason']}"
```

#### D. Type 4 Status规则

```python
def assert_type4_selective_status(result):
    """验证Type 4 selective waiver的status规则"""
    # Type 4: status = PASS iff missing_items为空
    if len(result.get('missing_items', [])) == 0:
        assert result['status'] == 'PASS', \
            "Type 4: status should be PASS when missing_items is empty"
    else:
        assert result['status'] == 'FAIL', \
            "Type 4: status should be FAIL when missing_items is not empty"
```

---

## 4. 完整测试实现示例

### 4.1 Pytest参数化测试

```python
import pytest
from typing import Dict, Any

# 6种配置定义
GATE3_CONFIGS = [
    {
        'id': 1,
        'type': 1,
        'req_value': 'N/A',
        'waiver_value': 'N/A',
        'description': 'Type 1: Existence, no waiver'
    },
    {
        'id': 2,
        'type': 2,
        'req_value': 1,
        'waiver_value': 'N/A',
        'description': 'Type 2: Pattern, no waiver'
    },
    {
        'id': 3,
        'type': 3,
        'req_value': 1,
        'waiver_value': 0,
        'description': 'Type 3: Pattern, global waiver'
    },
    {
        'id': 4,
        'type': 3,
        'req_value': 1,
        'waiver_value': 1,
        'description': 'Type 3: Pattern, selective waiver'
    },
    {
        'id': 5,
        'type': 4,
        'req_value': 'N/A',
        'waiver_value': 0,
        'description': 'Type 4: Existence, global waiver'
    },
    {
        'id': 6,
        'type': 4,
        'req_value': 'N/A',
        'waiver_value': 1,
        'description': 'Type 4: Existence, selective waiver'
    }
]

@pytest.mark.parametrize("config", GATE3_CONFIGS, ids=lambda c: f"Config{c['id']}")
def test_gate3_integration(config: Dict[str, Any]):
    """
    Gate 3集成测试 - 6种配置
    """
    # 1. 准备测试数据
    test_config = prepare_test_config(config)
    
    # 2. 运行完整pipeline
    result = run_full_pipeline(test_config)
    
    # 3. 通用断言（所有配置）
    assert_cr5_keys(result, config['type'])
    assert_missing_items_schema(result)
    # assert_parsing_recursion(result)  # 如果测试递归
    # assert_stable_sorting(result)     # 如果测试排序
    
    # 4. Waiver模式特定断言
    if config['waiver_value'] == 0:  # Global Waiver
        assert_global_waiver_mutate(result)
        assert_global_waiver_comments(result, test_config['waive_items'])
        assert_global_waiver_no_unused(result)
        assert_global_waiver_status(result)
        
    elif config['waiver_value'] != 'N/A':  # Selective Waiver
        assert_selective_waiver_move(result, expected_moved=1)
        assert_selective_waiver_removed(result, result.get('waived', []))
        assert_selective_waiver_unused(result, test_config['waive_items'], expected_unused=[])
        
        if config['type'] == 4:
            assert_type4_selective_status(result)
    
    # 5. 配置特定验证
    verify_config_specific(result, config)
```

### 4.2 辅助函数

```python
def prepare_test_config(config: Dict) -> Dict:
    """准备测试配置"""
    return {
        'requirements': {
            'value': config['req_value'],
            'pattern_items': ['pattern1', 'pattern2'] if config['req_value'] != 'N/A' else []
        },
        'waivers': {
            'value': config['waiver_value'],
            'waive_items': ['waive1'] if config['waiver_value'] != 'N/A' else []
        },
        'input_files': ['/test_file.txt'],
        'description': config['description']
    }

def run_full_pipeline(test_config: Dict) -> Dict:
    """运行完整pipeline (L0→L1→L2→L3→L4→L5)"""
    # 实现完整pipeline调用
    # 这里需要集成所有6个层级
    pass
```

---

## 5. 测试数据准备建议

### 5.1 通用测试数据

```yaml
# test_data_common.yaml
input_files:
  - /test_file.txt

file_content:
  /test_file.txt: |
    Line 1: pattern1 data
    Line 2: pattern2 data
    Line 3: extra data
    Line 4: another pattern1
```

### 5.2 Config特定测试数据

**Config 3 (Type 3 Global):**
```yaml
requirements:
  value: 2
  pattern_items:
    - pattern1
    - pattern2

waivers:
  value: 0
  waive_items:
    - global_waive

expected_result:
  status: PASS  # 强制PASS
  missing_items: []  # 或有但标记为INFO
  extra_items:
    - value: "extra data"
      severity: INFO
      tag: "[WAIVED_AS_INFO]"
  waived:
    - waiver_pattern: "global_waive"
      waiver_reason: "Global Waiver"
      tag: "[WAIVED_INFO]"
  unused_waivers: []
```

**Config 4 (Type 3 Selective):**
```yaml
requirements:
  value: 2
  pattern_items:
    - pattern1
    - pattern2

waivers:
  value: 1
  waive_items:
    - pattern2  # 匹配missing_items中的pattern2

expected_result:
  status: PASS  # 如果MOVE后missing/extra都空
  missing_items: []  # pattern2被MOVE
  extra_items:
    - value: "extra data"  # 未被waive
  waived:
    - expected: "pattern2"
      waiver_pattern: "pattern2"
      waiver_reason: "N/A"
      tag: "[WAIVER]"
  unused_waivers: []  # pattern2有匹配
```

---

## 6. 验收标准

### 必须通过的测试
- [ ] 所有6个配置的CR5 key集合正确
- [ ] 所有6个配置的missing_items schema正确
- [ ] PR2递归解析在至少1个配置中验证
- [ ] 稳定排序在至少1个配置中验证
- [ ] Config 3的Global Waiver MUTATE语义正确
- [ ] Config 5的Global Waiver MUTATE语义正确
- [ ] Config 4的Selective Waiver MOVE语义正确
- [ ] Config 6的Selective Waiver MOVE语义正确
- [ ] Type 4的status规则正确

### 代码质量要求
- [ ] 测试代码覆盖率 >= 90%
- [ ] 所有断言有清晰的错误消息
- [ ] 测试数据参数化，易于扩展

### 性能要求
- [ ] 单个配置测试 < 1s
- [ ] 完整6个配置测试 < 5s

---

## 7. 调试技巧

### 7.1 当测试失败时

```python
def debug_gate3_failure(result, config):
    """调试Gate 3测试失败"""
    print(f"\n=== Config {config['id']} Failed ===")
    print(f"Type: {config['type']}")
    print(f"req.value: {config['req_value']}")
    print(f"waiver.value: {config['waiver_value']}")
    
    print(f"\nActual keys: {set(result.keys())}")
    print(f"Expected keys: {TYPE_KEYS[config['type']]}")
    
    if 'missing_items' in result:
        print(f"\nmissing_items count: {len(result['missing_items'])}")
        if result['missing_items']:
            print("First missing_item:")
            print(json.dumps(result['missing_items'][0], indent=2))
    
    if 'waived' in result:
        print(f"\nwaived count: {len(result['waived'])}")
        if result['waived']:
            print("First waived item:")
            print(json.dumps(result['waived'][0], indent=2))
```

### 7.2 日志建议

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Running Gate 3 Config {config['id']}: {config['description']}")
logger.debug(f"Input config: {test_config}")
logger.debug(f"Pipeline result keys: {result.keys()}")
logger.debug(f"Status: {result['status']}")
```

---

## 8. 总结

Gate 3测试矩阵是框架正确性的**最终验证**。6个配置覆盖了：
- 2种检查类型（Existence vs Pattern）
- 3种waiver模式（None, Global, Selective）
- 2种Type分类（with/without extra_items）

**通过Gate 3意味着:**
- 所有Layer (L0-L5) 正确集成
- 所有Atoms (A/B/C) 正确调用
- 所有数据流转正确
- 所有Waiver语义正确
- 所有CR5约束满足

**这是deployment ready的最终关卡。**
