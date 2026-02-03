# Atoms规范补充说明

本文档补充Plan.txt中Atom A/B/C的关键实现细节，这些细节在各Layer执行plan中被引用但需要集中说明。

## Atom B: validate_logic - 关键细节

### 1. Alternatives Split Semantics (Locked)

当pattern包含`|`时，进入alternatives模式，遵循以下规则：

#### 规则详细说明

1. **分隔符是 `'|'`**: 硬分隔符，无转义
2. **Strip每个片段**: `alt.strip()` 应用于每个split后的片段
3. **忽略空片段**: 
   - `"a||b"` ≡ `"a|b"` (双竖线被忽略)
   - `"|a||"` 匹配 `"a"` (前导/尾随竖线被忽略)
4. **无转义**: `\|` 被视为两个字面字符 `\` 和 `|`，而非转义的竖线
5. **Alternatives内的regex/wildcard字符是字面量**:
   - `"regex:^a|zzz"` 匹配字面字符串 `"regex:^a"` OR `"zzz"`
   - `"a*|b?"` 匹配字面字符串 `"a*"` OR `"b?"`，NOT wildcard patterns

#### 优先级说明 (Critical)

> **Plan.txt Section 1, Atom B, Lines 86-91**

Alternatives模式具有**最高优先级**。当检测到`|`时：
- 立即进入alternatives分支
- 内部的 `regex:` 前缀、`*` `?` 通配符等**都被视为字面字符**
- 每个segment使用**contains**策略匹配（ANY hit => match）

#### 测试用例 (Gate 2 #4)

```python
# Test Case 1: Literal regex prefix in alternatives
result = validate_logic("regex:^a", "regex:^a|zzz")
assert result['is_match'] == True
assert result['kind'] == "alternatives"
# 匹配到字面字符串 "regex:^a"

# Test Case 2: No match when text doesn't contain any segment
result = validate_logic("abc", "regex:^a|zzz")
assert result['is_match'] == False
# "abc" 不包含 "regex:^a" 也不包含 "zzz"

# Test Case 3: Wildcard chars are literal in alternatives
result = validate_logic("a*", "a*|b?")
assert result['is_match'] == True
assert result['kind'] == "alternatives"
# 匹配到字面字符串 "a*"

# Test Case 4: No wildcard expansion
result = validate_logic("abc", "a*|b?")
assert result['is_match'] == False
# "abc" 不包含 "a*" 也不包含 "b?"，NOT wildcard match
```

#### 实现伪代码

```python
def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    # 1. Check for alternatives (highest priority)
    if '|' in pattern:
        segments = [seg.strip() for seg in pattern.split('|') if seg.strip()]
        for seg in segments:
            if seg in text:  # contains check (literal)
                return {'is_match': True, 'reason': f'Matched segment: {seg}', 'kind': 'alternatives'}
        return {'is_match': False, 'reason': 'No alternative matched', 'kind': 'alternatives'}
    
    # 2. Check for regex (second priority)
    if pattern.startswith('regex:'):
        # ... regex logic
    
    # 3. Check for wildcard (third priority)
    if '*' in pattern or '?' in pattern:
        # ... wildcard logic
    
    # 4. Default strategy (lowest priority)
    # ... default logic
```

---

### 2. Regex Error Message Prefix (Locked)

> **Plan.txt Section 1, Atom B, Line 67**

**要求:** 当regex编译失败（`re.error`）时，`reason`字段必须以**精确前缀** `"Invalid Regex:"` 开始（包括冒号和空格）。

#### Gate 2 Test #3

```python
result = validate_logic("abc", "regex:[", regex_mode="search")
assert result['is_match'] == False
assert result['kind'] == 'regex'
assert result['reason'].startswith("Invalid Regex:")

# 合法的reason示例:
# - "Invalid Regex: missing ], unterminated character set at position 6"
# - "Invalid Regex: unbalanced parenthesis"
# - "Invalid Regex: bad escape \x at position 5"
```

#### 实现示例

```python
import re

try:
    regex_pattern = pattern[6:]  # Remove "regex:" prefix
    compiled = re.compile(regex_pattern)
    # ... matching logic
except re.error as e:
    return {
        'is_match': False,
        'reason': f"Invalid Regex: {str(e)}",  # MUST start with "Invalid Regex:"
        'kind': 'regex'
    }
```

#### 测试断言

测试代码必须使用 `startswith()` 检查前缀：

```python
assert result['reason'].startswith("Invalid Regex:")
```

**错误示例（不符合要求）:**
- `"Regex Error: ..."`
- `"Invalid regex: ..."` (小写)
- `"Invalid Regex ..."` (缺少冒号)
- `"Regex compilation failed: ..."`

---

### 3. Case Sensitivity (Locked)

> **Plan.txt Section 1, Atom B, Line 70**

**所有分支**都是大小写敏感的：
- `contains`: 子字符串检查（大小写敏感）
- `exact`: 完全相等（大小写敏感）
- `alternatives`: 每个segment的contains检查（大小写敏感）
- `wildcard`: `fnmatch.fnmatchcase` （大小写敏感）
- `regex`: 默认大小写敏感（除非pattern中使用`(?i)`）

#### 示例

```python
# Contains - case sensitive
validate_logic("ABC", "abc", default_match="contains")  # False
validate_logic("ABC", "ABC", default_match="contains")  # True

# Exact - case sensitive
validate_logic("test", "TEST", default_match="exact")  # False
validate_logic("test", "test", default_match="exact")  # True

# Alternatives - case sensitive
validate_logic("ABC", "abc|xyz")  # False (no match)
validate_logic("ABC", "ABC|xyz")  # True (match)

# Wildcard - case sensitive (fnmatchcase)
validate_logic("Test.txt", "test.*")  # False
validate_logic("test.txt", "test.*")  # True
```

---

### 4. Wildcard Implementation (Locked)

> **Plan.txt Section 1, Atom B, Line 66**

**必须使用:** `fnmatch.fnmatchcase` （大小写敏感，操作系统无关）

**不能使用:** `fnmatch.fnmatch` （Windows上大小写不敏感）

#### 实现

```python
import fnmatch

def validate_logic(text, pattern, ...):
    # ...
    if '*' in pattern or '?' in pattern:
        is_match = fnmatch.fnmatchcase(text, pattern)  # NOT fnmatch.fnmatch
        return {
            'is_match': is_match,
            'reason': 'Wildcard match' if is_match else 'No wildcard match',
            'kind': 'wildcard'
        }
```

#### 为什么必须是fnmatchcase?

- `fnmatch.fnmatch`: 在Windows上会忽略大小写
- `fnmatch.fnmatchcase`: 所有平台都大小写敏感
- Plan.txt要求**case-sensitive**且**OS-independent**

---

## Atom A: extract_context - 关键细节

### 1. PR5 (No Filtering)

> **Plan.txt Section 1, Atom A**

**要求:** Atom A必须提取**所有候选items**，不能根据requirements/waivers patterns进行过滤。

**Rationale:**
- 过滤逻辑由Layer 3 (Check Assembler)负责
- Atom A只负责解析和提取
- 保持Atom A的纯粹性（pure function）

**示例（错误做法）:**
```python
# ❌ 错误：在Atom A中根据requirements过滤
def extract_context(text, source_file):
    items = []
    for line in text.split('\n'):
        # 错误：检查是否匹配requirements
        if any(req_pattern in line for req_pattern in requirements):
            items.append(...)
    return items
```

**正确做法:**
```python
# ✅ 正确：提取所有候选items
def extract_context(text, source_file):
    items = []
    for line in text.split('\n'):
        # 提取所有可能的items，不进行过滤
        if line.strip():  # 只基于格式判断，不基于pattern
            items.append(...)
    return items
```

### 2. Value Type Hard Lock

> **Plan.txt Section 1, Atom A, Line 28**

**要求:** `value` 字段**必须是 `str` 类型**。非字符串提取结果必须在Atom A内部转换为字符串。

#### 实现

```python
def extract_context(text, source_file):
    items = []
    for match in parse_logic(text):
        # 如果提取的value是非字符串类型，必须转换
        raw_value = match.group(1)  # 可能是int, float, etc.
        
        item = {
            'value': str(raw_value),  # MUST cast to str
            'source_file': source_file,
            'line_number': match.line_number,
            'matched_content': match.line,
            'parsed_fields': {}
        }
        items.append(item)
    
    return items
```

#### Gate 1测试

```python
# Gate 1: Value Type Safety
parsed_items = extract_context(text, source_file)
for item in parsed_items:
    assert isinstance(item['value'], str), f"ParsedItem['value'] must be str, got {type(item['value'])}"
```

---

## Atom C: check_existence - 关键细节

### Evidence Schema

> **Plan.txt Section 1, Atom C, Line 116**

**要求:** `evidence` 中的每个item必须满足ParsedItem schema（与Atom A输出相同的5个必需keys）。

#### 正确的evidence格式

```python
def check_existence(items):
    if len(items) > 0:
        # Evidence必须是完整的ParsedItem
        evidence = [
            {
                'value': item['value'],
                'source_file': item['source_file'],
                'line_number': item['line_number'],
                'matched_content': item['matched_content'],
                'parsed_fields': item['parsed_fields']
            }
            for item in items
        ]
        return {
            'is_match': True,
            'reason': 'Items found',
            'evidence': evidence
        }
    else:
        return {
            'is_match': False,
            'reason': 'No items found',
            'evidence': []
        }
```

---

## 总结

这些补充细节都是Plan.txt中**Locked**的约束，必须严格遵守：

1. **Alternatives优先级**: 最高优先级，内部字符都是字面量
2. **Regex错误前缀**: 必须是 `"Invalid Regex:"`
3. **Case sensitivity**: 所有分支都大小写敏感
4. **Wildcard实现**: 必须用 `fnmatchcase`
5. **PR5**: Atom A不能过滤
6. **Value类型**: 必须是 `str`
7. **Evidence schema**: 必须满足ParsedItem结构

这些细节在Gate 1/2/3测试中都会被严格验证。
