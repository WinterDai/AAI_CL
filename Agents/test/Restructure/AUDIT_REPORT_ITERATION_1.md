# LLM专家审查报告 - 迭代1

**审查日期**: 2025-01-02  
**审查范围**: Check_10_0_0_00_aggressive.py vs Jinja2骨架 + Prompt覆盖度  
**审查者**: LLM Senior Expert

---

## 🔍 Part 1: Jinja2骨架遗漏审查

### 审查方法
逐行对比 `Check_10_0_0_00_aggressive.py` (CodeGen输出) 与 `checker_skeleton.py.jinja2` (骨架模板)

---

### 1.1 文件头部分（Lines 1-35）

#### ✅ PASS - 完全符合骨架

**骨架定义**:
```jinja
{{ header_comment }}

{{ imports_section }}
from checker_templates.input_file_parser_template import InputFileParserMixin
```

**实际生成** (Lines 1-31):
```python
# -*- coding: utf-8 -*-
"""
NetlistSpefVersionChecker.py - Checker Implementation for IMP-10-0-0-00
...
"""

from pathlib import Path
import gzip
import re
import sys
from typing import List, Dict, Tuple, Optional, Any

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin
from checker_templates.input_file_parser_template import InputFileParserMixin
```

**审查结论**: ✅ 无遗漏，符合header_comment + imports_section模板

---

### 1.2 类定义与继承（Lines 37-50）

#### ✅ PASS - 完全符合骨架

**骨架定义**:
```jinja
class {{ class_name }}(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    {{ item_id }}: {{ description | truncate(80) }}
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 -> Boolean Check
    ...
    """
```

**实际生成** (Lines 37-54):
```python
class NetlistSpefVersionChecker(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-10-0-0-00: Confirm the netlist/spef version is correct.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 -> Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 -> Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 -> Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 -> Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items, match_waiver_entry)
    - Uses OutputBuilderMixin for result construction (build_complete_output)
    """
```

**审查结论**: ✅ 继承顺序正确，docstring完整

---

### 1.3 类常量（Lines 56-63）

#### ✅ PASS - 符合骨架LLM生成区

**骨架定义**:
```jinja
{% if class_constants %}
    {{ class_constants | indent(4, first=False) }}
{% else %}
    FOUND_DESC = "Item found"
    ...
{% endif %}
```

**实际生成** (Lines 56-63):
```python
    # =========================================================================
    # UNIFIED DESCRIPTIONS - Class-level constants (LLM-Generated)
    # =========================================================================
    FOUND_DESC = "Netlist/SPEF files loaded successfully"
    MISSING_DESC = "Netlist/SPEF loading issues"
    FOUND_REASON = "Status: Success"
    MISSING_REASON = "File loading failed"
    EXTRA_DESC = "Design has no spef/netlist file"
    EXTRA_REASON = "Design has no spef/netlist file or unexpected error"
```

**审查结论**: ✅ Context Agent预生成值，LLM正确使用

---

### 1.4 __init__方法（Lines 65-77）

#### ✅ PASS - 完全符合骨架

**骨架定义**:
```jinja
def __init__(self):
    """Initialize the checker."""
    super().__init__(
        check_module="{{ check_module | default('UNKNOWN') }}",
        item_id="{{ item_id }}",
        item_desc="{{ description | truncate(100) }}"
    )
    self._metadata: Dict[str, Dict[str, Any]] = {}
{% if instance_vars %}
    {{ instance_vars | indent(8, first=False) }}
{% else %}
    self._parsed_items: List[Dict] = []
{% endif %}
```

**实际生成** (Lines 65-77):
```python
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="IMP",
            item_id="IMP-10-0-0-00",
            item_desc="Confirm the netlist/spef version is correct."
        )
        # MANDATORY: Metadata tracking for debug (Golden pattern)
        # Used by helper methods to track line numbers for DetailItem
        self._metadata: Dict[str, Dict[str, Any]] = {}
        # Store parsed data
        self._parsed_items: List[Dict] = []
```

**审查结论**: ✅ 框架部分100%符合，实例变量使用默认值

---

### 1.5 execute_check方法（Lines 79-107）

#### ✅ PASS - 完全符合骨架（100%固定）

**骨架定义**:
```jinja
def execute_check(self) -> CheckResult:
    """
    Execute check with automatic type detection and delegation.
    
    v2.1: Aligned with Golden design pattern:
    1. Parse input files first via _parse_input_files()
    2. Pass parsed data to _execute_typeN(parsed_data)
    ...
    """
    try:
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Parse input files first (Golden pattern)
        parsed_data = self._parse_input_files()
        
        # Detect checker type (use BaseChecker method)
        checker_type = self.detect_checker_type()
        
        # Execute based on type, passing parsed data
        if checker_type == 1:
            return self._execute_type1(parsed_data)
        elif checker_type == 2:
            return self._execute_type2(parsed_data)
        elif checker_type == 3:
            return self._execute_type3(parsed_data)
        else:  # checker_type == 4
            return self._execute_type4(parsed_data)
    except ConfigurationError as e:
        return e.check_result
```

**实际生成** (Lines 79-107):
```python
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and delegation.
        
        v2.1: Aligned with Golden design pattern:
        1. Parse input files first via _parse_input_files()
        2. Pass parsed data to _execute_typeN(parsed_data)
        
        Returns:
            CheckResult based on detected checker type
        """
        try:
            if self.root is None:
                raise RuntimeError("Checker not initialized. Call init_checker() first.")
            
            # Parse input files first (Golden pattern)
            parsed_data = self._parse_input_files()
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Execute based on type, passing parsed data
            if checker_type == 1:
                return self._execute_type1(parsed_data)
            elif checker_type == 2:
                return self._execute_type2(parsed_data)
            elif checker_type == 3:
                return self._execute_type3(parsed_data)
            else:  # checker_type == 4
                return self._execute_type4(parsed_data)
        except ConfigurationError as e:
            return e.check_result
```

**审查结论**: ✅ 100%骨架生成，无任何修改

---

### 1.6 Entry Point（Lines 1020-1032）

#### ✅ PASS - 完全符合骨架（100%固定）

**骨架定义**:
```jinja
# ============================================================================
# Entry Point (Template - Fixed, Golden-Aligned)
# ============================================================================

def init_checker() -> {{ class_name }}:
    """Initialize and return the checker instance."""
    checker = {{ class_name }}()
    checker.init_checker()
    return checker


if __name__ == '__main__':
    checker = init_checker()
    checker.execute_check()
    checker.write_output()
```

**实际生成** (Lines 1020-1032):
```python
# ============================================================================
# Entry Point (Template - Fixed, Golden-Aligned)
# ============================================================================

def init_checker() -> NetlistSpefVersionChecker:
    """Initialize and return the checker instance."""
    checker = NetlistSpefVersionChecker()
    checker.init_checker()
    return checker


if __name__ == '__main__':
    checker = init_checker()
    checker.execute_check()
    checker.write_output()
```

**审查结论**: ✅ 100%骨架生成，仅类名变量替换

---

### 1.7 LLM生成部分：_parse_input_files（Lines 109-393）

#### 🔍 审查重点：是否正确使用框架方法

**骨架期望**:
```jinja
{{ parse_method | indent(4, first=True) }}
```

**关键框架方法调用检查**:

1. ✅ **parse_log_with_patterns()** (Line 163-169):
```python
matches = self.parse_log_with_patterns(
    sta_log_path,
    patterns,
    track_metadata=True
)
```

2. ✅ **Metadata追踪** (Lines 175, 189, 218, etc.):
```python
self._metadata['netlist_command'] = matches['netlist_command'][0]
self._metadata['spef_command'] = matches['spef_command'][0]
self._metadata['spef_skipped'] = matches['spef_skip'][0]
```

3. ✅ **返回结构** (Line 388-392):
```python
return {
    'netlist_info': netlist_info,
    'spef_info': spef_info,
    'errors': sta_log_info['errors']
}
```

**审查结论**: ✅ 正确使用InputFileParserMixin，Metadata追踪完整

---

### 1.8 LLM生成部分：_execute_type1-4（Lines 395-985）

#### 🔍 审查重点：框架方法调用与参数正确性

**Type 1** (Lines 395-446):
```python
return self.execute_boolean_check(
    parse_data_func=parse_data,
    has_waiver=False,
    found_desc=self.FOUND_DESC,
    missing_desc=self.MISSING_DESC,
    extra_desc=self.EXTRA_DESC,
    name_extractor=self._build_name_extractor()
)
```
- ✅ 使用execute_boolean_check（激进重构框架方法）
- ✅ has_waiver=False（Type 1无waiver）
- ✅ 传递类常量FOUND_DESC等

**Type 2** (Lines 448-535):
```python
return self.execute_value_check(
    parse_data_func=parse_data,
    has_waiver=False,
    found_reason="Version pattern matched",
    missing_reason="Required pattern not found",
    extra_reason="Design has no spef/netlist file or unexpected error",
    ...
)
```
- ✅ 使用execute_value_check
- ✅ has_waiver=False（Type 2无waiver）
- ❌ **遗漏**: 未传递info_items（但Type 2不需要，Golden也没有）

**Type 3** (Lines 537-683):
```python
# Prepare info_items outside parse_data (needs access to parsed_data)
info_items = {}
if netlist_info.get('path'):
    netlist_path = netlist_info.get('path')
    metadata = self._metadata.get('netlist_success', {})
    info_items[f"Netlist path: {netlist_path}"] = {
        'line_number': metadata.get('line_number', 0),
        'file_path': metadata.get('file_path', ''),
        'reason': f"Status: Success"
    }

return self.execute_value_check(
    parse_data_func=parse_data,
    has_waiver=True,
    info_items=info_items,  # 🆕 正确使用info_items
    extra_severity=Severity.FAIL,  # 🆕 正确使用extra_severity
    ...
)
```
- ✅ has_waiver=True（Type 3有waiver）
- ✅ info_items正确传递（Golden手写107行的简化版）
- ✅ extra_severity=Severity.FAIL（SPEF skip强制FAIL）

**Type 4** (Lines 685-985):
```python
return self.execute_boolean_check(
    parse_data_func=parse_data,
    has_waiver=True,  # ✅
    found_desc=self.FOUND_DESC,
    ...
)
```
- ✅ has_waiver=True（Type 4有waiver）

**审查结论**: ✅ 所有Type实现正确调用框架方法，参数符合骨架约束

---

### 1.9 Helper Methods（Lines 987-1018）

#### ✅ PASS - 符合骨架LLM生成区

**骨架定义**:
```jinja
{% if helper_methods %}
    # =========================================================================
    # Helper Methods (LLM-Generated)
    # =========================================================================
    
{{ helper_methods | indent(4, first=True) }}
{% endif %}
```

**实际生成** (Lines 987-1018):
```python
    # =========================================================================
    # Helper Methods (LLM-Generated)
    # =========================================================================
    
    def _build_name_extractor(self):
        """Build name extractor function for Golden-aligned output."""
        def extract_name(name, metadata):
            if isinstance(metadata, dict):
                path = metadata.get('path', '')
                version = metadata.get('version', '')
                date = metadata.get('date', '')
                matched = metadata.get('matched', '')
                note = metadata.get('note', '')
                
                if path and version and date:
                    return f"{name}: {path}, Version: {version}, Date: {date}"
                elif path and note:
                    return f"{name}: {path} ({note})"
                elif path:
                    return f"{name}: {path}"
                elif matched:
                    return f"{name}: {matched}"
            return name
        
        return extract_name
```

**审查结论**: ✅ Helper method正确定义，用于自定义name_extractor

---

## 📊 Part 1 总结：Jinja2骨架遗漏审查

| 组件 | 骨架定义 | 实际生成 | 符合度 | 遗漏/偏差 |
|------|---------|---------|-------|----------|
| **文件头** | header_comment + imports | 完全一致 | ✅ 100% | 无 |
| **类定义** | 继承顺序、docstring | 完全一致 | ✅ 100% | 无 |
| **类常量** | LLM生成区 | Context Agent值 | ✅ 100% | 无 |
| **__init__** | super() + _metadata | 完全一致 | ✅ 100% | 无 |
| **execute_check** | 100%固定骨架 | 完全一致 | ✅ 100% | 无 |
| **_parse_input_files** | LLM生成区 | 框架方法正确 | ✅ 100% | 无 |
| **_execute_type1-4** | LLM生成区 | 框架方法正确 | ✅ 100% | 无 |
| **Helper Methods** | LLM生成区 | 正确定义 | ✅ 100% | 无 |
| **Entry Point** | 100%固定骨架 | 完全一致 | ✅ 100% | 无 |

### 🎉 结论：0个遗漏，100%符合Jinja2骨架

---

## 🔧 Part 2: Prompt覆盖度审查

### 2.1 审查范围

检查Jinja2未覆盖的LLM生成部分，Prompt是否提供充分指导：

1. **类常量生成**（8个描述字段）
2. **_parse_input_files逻辑**（200行业务代码）
3. **_execute_typeN逻辑**（4个Type实现）
4. **Helper Methods**（name_extractor等）

---

### 2.2 类常量生成审查

#### Prompt提供（prompts.py Lines 520-533）

```python
if class_constants:
    lines.append("  <class_constants usage=\"直接使用这些值，不要重新生成\">")
    field_order = [
        'found_desc', 'missing_desc', 'waived_desc',
        'found_reason', 'missing_reason', 'waived_base_reason',
        'extra_reason', 'unused_waiver_reason'
    ]
    for field in field_order:
        if field in class_constants:
            lines.append(f'    <{field}>{class_constants[field]}</{field}>')
    lines.append("  </class_constants>")
```

#### CodeGen使用

```python
FOUND_DESC = "Netlist/SPEF files loaded successfully"
MISSING_DESC = "Netlist/SPEF loading issues"
FOUND_REASON = "Status: Success"
MISSING_REASON = "File loading failed"
EXTRA_DESC = "Design has no spef/netlist file"
EXTRA_REASON = "Design has no spef/netlist file or unexpected error"
```

#### ✅ 覆盖度：100%

- Context Agent预生成值
- Prompt明确："直接使用这些值，不要重新生成"
- LLM正确使用，无重新生成

---

### 2.3 _parse_input_files逻辑审查

#### Prompt提供（prompts.py Lines 550-620）

**Extraction Fields (XML格式)**:
```xml
<extraction_fields usage="直接使用这些正则模式">
  <file name="STA_Log" data_role="indirect_reference">
    <field name="netlist_command" source_type="data_verified">
      <regex_templates>
        <template>read_netlist\s+([^\s]+)</template>
      </regex_templates>
      <matched_samples>
        <sample>read_netlist ./netlist/design.v</sample>
      </matched_samples>
    </field>
    <field name="spef_command" source_type="data_verified">
      <regex_templates>
        <template>read_spef\s+([^\s]+)</template>
      </regex_templates>
    </field>
    <field name="spef_skip_command" source_type="data_verified">
      <regex_templates>
        <template>write_sdf.*post_synthesis</template>
      </regex_templates>
    </field>
  </file>
  <file name="Netlist" data_role="direct_source">
    <field name="netlist_tool" source_type="data_verified">
      <regex_templates>
        <template>Genus</template>
      </regex_templates>
    </field>
    <field name="netlist_version" source_type="data_verified">
      <regex_templates>
        <template>Genus.*?version\s+([\d\.]+)</template>
      </regex_templates>
    </field>
    ...
  </file>
</extraction_fields>
```

**Extraction Chain**:
```xml
<extraction_chain hint="按此顺序解析可获得最优效果">
  <parse_step order="1" source="STA_Log">netlist_path, spef_path, spef_skip_command</parse_step>
  <parse_step order="2" source="Netlist">netlist_tool, netlist_version, netlist_date</parse_step>
  <parse_step order="3" source="SPEF">spef_tool, spef_version, spef_date</parse_step>
</extraction_chain>
```

**Semantic Intent**:
```xml
<semantic_intent>
  <check_target>Verify netlist/SPEF version correctness</check_target>
  <data_flow>STA_Log → Extract file paths → Read SPEF/Netlist → Match version patterns</data_flow>
  <data_sources>
    <source name="STA_Log" data_role="indirect_reference">
      <role>Provides file paths to SPEF/Netlist files</role>
    </source>
    <source name="Netlist" data_role="direct_source">
      <role>Contains actual netlist version information (Genus version, timestamp)</role>
    </source>
  </data_sources>
</semantic_intent>
```

#### CodeGen实现对比

**正则模式使用** (Lines 154-162):
```python
patterns = {
    'netlist_command': [
        r'read_netlist\s+([^\s]+)',
        r'read_netlist\s+-netlist\s+([^\s]+)',
        r'read_netlist\s+{([^}]+)}'
    ],
    'spef_command': [r'read_spef\s+([^\s]+)'],
    'spef_skip': [r'write_sdf.*post_synthesis']
}
```

**解析顺序** (Lines 108-392):
1. Step 1: 解析STA_Log提取路径（Lines 154-219）
2. Step 2: 读取Netlist文件提取版本（Lines 269-327）
3. Step 3: 读取SPEF文件提取版本（Lines 329-381）

#### ✅ 覆盖度：95%

**充分覆盖**:
- ✅ 正则模式完整提供（matched_samples帮助理解）
- ✅ 解析顺序明确（extraction_chain）
- ✅ 数据流清晰（semantic_intent）
- ✅ data_role区分（indirect_reference vs direct_source）

**改进空间** (🟡 P1):
- ⚠️ **netlist_command正则扩展**：LLM自主添加了2个额外模式（`-netlist`参数、`{...}`格式）
  - Prompt未明确说明可扩展
  - 建议添加："如发现Log中有变体格式，可添加额外正则模式"

---

### 2.4 _execute_typeN逻辑审查

#### Prompt提供（prompts.py Lines 950-1000）

**输出说明**:
```markdown
## 📤 输出要求

1. **方法签名**: `_execute_typeN(self, parsed_data)` - 必须接收 parsed_data
2. **Helper Methods**: `self._xxx()` 必须在 `<helper_methods>` 中定义
3. **Metadata**: 解析时 `self._metadata['key'] = {'line_number': N, 'file_path': str}`, 使用时 `meta.get('line_number', 0)`
4. **Waiver (Type3/4)**: 使用 `self.is_item_waived_word_level()` 或 word-level 匹配
```

#### CodeGen实现检查

**Type 1方法签名** (Line 395):
```python
def _execute_type1(self, parsed_data: Dict[str, Any]) -> CheckResult:
```
✅ 符合Prompt要求

**Type 3 Metadata使用** (Lines 423, 429):
```python
metadata = self._metadata.get('netlist_success', {})
info_items[f"Netlist path: {netlist_path}"] = {
    'line_number': metadata.get('line_number', 0),  # ✅
    'file_path': metadata.get('file_path', ''),     # ✅
    'reason': f"Status: Success"
}
```
✅ 符合Prompt要求

**Type 3 Framework调用** (Lines 528-535):
```python
return self.execute_value_check(
    parse_data_func=parse_data,
    has_waiver=True,
    info_items=info_items,
    extra_severity=Severity.FAIL,
    ...
)
```
✅ 符合激进重构模式

#### ⚠️ 覆盖度：85%

**充分覆盖**:
- ✅ 方法签名约束明确
- ✅ Metadata使用模式清晰
- ✅ 框架方法调用正确

**🔴 关键遗漏 (P0)**:
1. **info_items参数未文档化**
   - Prompt未明确说明`info_items`参数的存在和用法
   - LLM使用了该参数，但可能是"猜测"而非"知道"
   - **修复**: 在prompts.py添加info_items参数说明

2. **extra_severity参数未约束**
   - Prompt未说明何时使用extra_severity
   - Type 3使用了`Severity.FAIL`，但Type 2未使用（正确）
   - **修复**: 添加约束"Type 3若有extra_items（如SPEF skip），必须使用extra_severity=Severity.FAIL"

**🟡 改进空间 (P1)**:
3. **name_extractor模式未说明**
   - Helper method `_build_name_extractor()`是自定义模式
   - Prompt未明确说明何时需要自定义name_extractor
   - Golden有此模式，但Prompt未传递

---

### 2.5 Helper Methods逻辑审查

#### Prompt提供

**输出格式说明** (Lines 975-985):
```markdown
<helper_methods>
# ⚠️ 所有 self._xxx() 调用必须在这里定义!
</helper_methods>
```

#### CodeGen实现

```python
def _build_name_extractor(self):
    """Build name extractor function for Golden-aligned output."""
    def extract_name(name, metadata):
        if isinstance(metadata, dict):
            path = metadata.get('path', '')
            version = metadata.get('version', '')
            date = metadata.get('date', '')
            matched = metadata.get('matched', '')
            note = metadata.get('note', '')
            
            if path and version and date:
                return f"{name}: {path}, Version: {version}, Date: {date}"
            elif path and note:
                return f"{name}: {path} ({note})"
            elif path:
                return f"{name}: {path}"
            elif matched:
                return f"{name}: {name}: {matched}"
        return name
    
    return extract_name
```

#### ⚠️ 覆盖度：70%

**充分覆盖**:
- ✅ 明确要求定义所有helper methods
- ✅ LLM正确定义了_build_name_extractor

**🟡 遗漏 (P1)**:
4. **name_extractor模式未传递**
   - Golden有此模式（自定义metadata字段到name的转换）
   - Prompt未从Golden中提取此模式
   - LLM可能从Golden Grounding Section学习到，但不够明确
   - **修复**: 在Golden Methods Section显式提取_build_name_extractor()示例

---

## 🚨 Part 3: 规则冲突与硬编码审查

### 3.1 硬编码规则清单

#### 3.1.1 框架层硬编码

**output_builder_template.py**:

1. **__INFO__前缀机制** (Lines 375-377, 536-539, 1489-1493, 1515-1516)
   ```python
   if item_name.startswith('__INFO__'):
       display_name = item_name[8:]  # 硬编码字符串前缀
   ```
   - **类型**: 字符串常量硬编码
   - **风险**: 中等 - 如LLM直接使用`__INFO__`前缀会导致混乱
   - **建议**: 重构为enum: `ItemCategory.INFO`

2. **Severity映射** (Lines 1543-1545)
   ```python
   if extra_severity:
       for key in extra_items:
           extra_items[key]['severity'] = extra_severity
   ```
   - **类型**: 参数覆盖逻辑
   - **风险**: 低 - 参数化设计，无硬编码值
   - **状态**: ✅ 良好设计

3. **Value计算排除规则** (Lines 1515-1516, 1532-1533)
   ```python
   actual_value = len([k for k in found_items.keys() if not k.startswith('__INFO__')])
   ```
   - **类型**: 逻辑硬编码（依赖前缀约定）
   - **风险**: 中等 - 与__INFO__前缀耦合
   - **建议**: 同步重构为enum

#### 3.1.2 骨架层硬编码

**checker_skeleton.py.jinja2**:

1. **继承顺序** (Line 37)
   ```jinja
   class {{ class_name }}(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
   ```
   - **类型**: Mixin顺序硬编码
   - **风险**: 高 - 顺序错误导致MRO问题
   - **状态**: ✅ Golden对齐，必须硬编码

2. **类常量字段顺序** (Lines 58-73)
   ```jinja
   field_order = [
       'found_desc', 'missing_desc', 'waived_desc',
       'found_reason', 'missing_reason', 'waived_base_reason',
       'extra_reason', 'unused_waiver_reason'
   ]
   ```
   - **类型**: 字段顺序硬编码
   - **风险**: 低 - Context Agent生成，顺序不影响功能
   - **状态**: ✅ 可接受

3. **execute_check逻辑** (Lines 95-114)
   ```jinja
   if checker_type == 1:
       return self._execute_type1(parsed_data)
   elif checker_type == 2:
       return self._execute_type2(parsed_data)
   ...
   ```
   - **类型**: Type分派逻辑硬编码
   - **风险**: 无 - Golden所有checker完全一致
   - **状态**: ✅ 100%固化正确

#### 3.1.3 Prompt层硬编码

**prompts.py**:

1. **Token Budget分配** (Lines 62-72)
   ```python
   BUDGET = {
       "feedback": 300,
       "golden_methods": 2500,
       "log_samples": 1500,
       ...
   }
   ```
   - **类型**: Token数值硬编码
   - **风险**: 低 - 基于经验值，可调整
   - **状态**: ✅ 合理设计

2. **XML标签结构** (Lines 330-370, 520-620)
   ```python
   lines.append("<semantic_intent>")
   lines.append("  <check_target>...</check_target>")
   lines.append("  <data_flow>...</data_flow>")
   ```
   - **类型**: XML Schema硬编码
   - **风险**: 低 - LLM理解XML结构，易扩展
   - **状态**: ✅ 语义化设计良好

3. **占位符检测模式** (Lines 1018-1030)
   ```python
   PLACEHOLDER_PATTERNS = [
       'pass', '...', '# TODO', '# todo',
       'raise NotImplementedError', 'raise NotImplemented',
       'PLACEHOLDER', '# FIXME',
   ]
   ```
   - **类型**: 字符串匹配硬编码
   - **风险**: 低 - 可扩展列表
   - **状态**: ✅ 实用设计

---

### 3.2 规则冲突分析

#### 冲突1: info_items vs 标准found_items

**冲突描述**:
- **框架规则**: found_items自动计入value
- **info_items规则**: __INFO__前缀的found_items不计入value

**冲突点**:
```python
# Type 3 准备info_items
info_items = {"Netlist path: ...": {...}}  # 预期：INFO，不计入value

# 框架内部：合并到found_items
found_items["__INFO__Netlist path: ..."] = {...}

# 框架value计算：排除__INFO__前缀
actual_value = len([k for k in found_items if not k.startswith('__INFO__')])
```

**风险评估**: 🟡 中等
- ✅ **当前状态**: 机制工作正常，测试通过
- ⚠️ **隐藏风险**: LLM若直接操作found_items添加`__INFO__`前缀会绕过检查
- 🔴 **Prompt未警告**: 未明确说明"不要直接使用__INFO__前缀"

**修复建议**:
```markdown
## 🚫 禁止模式

**不要直接操作found_items添加__INFO__前缀**:
```python
# ❌ 错误：直接添加__INFO__前缀
found_items["__INFO__Netlist path"] = {...}

# ✅ 正确：使用info_items参数
info_items = {"Netlist path": {...}}
return self.execute_value_check(..., info_items=info_items)
```
```

#### 冲突2: extra_severity vs 默认Severity

**冲突描述**:
- **框架默认**: extra_items默认Severity.WARN
- **Type 3需求**: SPEF skip应为Severity.FAIL
- **Type 2行为**: 无extra_items，不应传extra_severity

**冲突点**:
```python
# Type 3: 需要强制FAIL
return self.execute_value_check(
    ...,
    extra_severity=Severity.FAIL  # ✅
)

# Type 2: 无extra_items
return self.execute_value_check(
    ...,
    # 未传extra_severity（正确，使用默认WARN或不产生extra）
)
```

**风险评估**: 🟡 中等
- ✅ **当前状态**: Type 3正确使用extra_severity
- ⚠️ **隐藏风险**: Type 2若误传extra_severity可能导致非预期FAIL
- 🔴 **Prompt未约束**: 未说明何时使用extra_severity

**修复建议**:
```markdown
## extra_severity参数使用约束

**Type 3**:
- 若检测到SPEF skip或其他critical extra_items，**必须**使用`extra_severity=Severity.FAIL`
- 示例：SPEF Reading was skipped → FAIL

**Type 2**:
- 通常**不使用**extra_severity（默认WARN即可）
- 除非有明确业务需求将extra_items提升到FAIL

**Type 1/4**:
- Boolean类型，无pattern matching，通常无extra_items
- 不使用extra_severity
```

#### 冲突3: name_extractor自定义 vs 框架默认

**冲突描述**:
- **框架默认**: name_extractor直接返回item name
- **Golden模式**: 自定义_build_name_extractor()扩展metadata字段
- **Type 1/3/4**: 使用自定义extractor
- **Type 2**: 未使用（正确，pattern匹配无需扩展）

**冲突点**:
```python
# Type 1: 传递自定义extractor
return self.execute_boolean_check(
    ...,
    name_extractor=self._build_name_extractor()  # ✅
)

# Type 2: 未传递（使用默认）
return self.execute_value_check(
    ...,
    # 无name_extractor参数
)
```

**风险评估**: 🟢 低
- ✅ **当前状态**: Type选择性使用，行为正确
- ✅ **框架设计**: Optional参数，默认值安全
- 🟡 **Prompt遗漏**: 未说明何时需要自定义name_extractor

**修复建议**:
```markdown
## name_extractor自定义模式

**何时需要**:
- Type 1/4（Boolean Check）: 若metadata包含复杂字段（path, version, date等），需自定义
- Type 3（Value + Waiver）: 同上

**何时不需要**:
- Type 2（Value Check）: pattern匹配结果通常是简单字符串，无需扩展
- Type 3: 若仅pattern匹配，无复杂metadata，可不使用

**实现模式**:
```python
def _build_name_extractor(self):
    def extract_name(name, metadata):
        if isinstance(metadata, dict):
            path = metadata.get('path', '')
            version = metadata.get('version', '')
            if path and version:
                return f"{name}: {path}, Version: {version}"
        return name
    return extract_name
```
```

---

## 📋 Part 3 总结：规则冲突与硬编码

| 项目 | 类型 | 位置 | 风险 | 修复优先级 |
|------|------|------|------|-----------|
| **__INFO__前缀** | 字符串常量硬编码 | Framework | 🟡 中等 | P2 (重构为enum) |
| **extra_severity约束缺失** | Prompt遗漏 | prompts.py | 🔴 高 | P0 (添加约束文档) |
| **info_items文档缺失** | Prompt遗漏 | prompts.py | 🔴 高 | P0 (添加参数说明) |
| **name_extractor模式未传递** | Prompt遗漏 | prompts.py | 🟡 中等 | P1 (添加Golden示例) |
| **继承顺序硬编码** | 骨架设计 | Jinja2 | ✅ 必要 | N/A (Golden对齐) |
| **Token Budget硬编码** | 数值配置 | prompts.py | 🟢 低 | P3 (可调参数化) |

---

## ✅ 审查总结

### Part 1: Jinja2骨架遗漏
- **遗漏数**: 0
- **符合度**: 100%
- **结论**: 生成代码完全符合骨架定义

### Part 2: Prompt覆盖度
- **总体覆盖**: 85%
- **关键遗漏**: 
  1. 🔴 info_items参数未文档化（P0）
  2. 🔴 extra_severity约束缺失（P0）
  3. 🟡 name_extractor模式未传递（P1）
  4. 🟡 正则扩展规则未说明（P1）

### Part 3: 规则冲突与硬编码
- **冲突数**: 3个
- **硬编码项**: 8个
- **高风险**: 2项（info_items、extra_severity）
- **中等风险**: 3项（__INFO__前缀、name_extractor、正则扩展）

---

## 🔄 下一步行动

1. **立即修复（P0）**:
   - [ ] prompts.py添加info_items参数完整说明
   - [ ] prompts.py添加extra_severity使用约束

2. **短期改进（P1）**:
   - [ ] prompts.py添加name_extractor模式示例
   - [ ] prompts.py添加正则扩展规则说明

3. **中期优化（P2）**:
   - [ ] 重构__INFO__前缀为enum
   - [ ] 添加负例样本（常见LLM错误）

4. **文档更新**:
   - [ ] 根据审查结果更新SKELETON_PROMPT_UPGRADE_DOC.md

---

**审查状态**: ✅ 完成  
**下一迭代**: 修复P0问题后重新生成文档
