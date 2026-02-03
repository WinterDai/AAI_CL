# 架构升级方案 V2.0 - 原子化设计

**文档版本**: V2.0  
**创建日期**: 2026-01-23  
**基于**: global_rules.md + IMP-10-0-0-00.py 分析  

---

## 📋 目录

1. [核心洞察](#核心洞察)
2. [问题分析](#问题分析)
3. [升级架构设计](#升级架构设计)
4. [架构对比](#架构对比)
5. [实施建议](#实施建议)

---

## 🎯 核心洞察

通过深入分析 `global_rules.md` 和现有checker实现，发现三个关键优化点：

### 发现1: Waiver Logic的固化潜力
- **Global Waiver (waiver.value=0)**: 功能极其单一且固定，应完全框架化
- **Selective Waiver (waiver.value>0)**: 当前仅支持字符串匹配，需支持复杂条件逻辑

### 发现2: Check Logic的原子化机会
- 所有Type共享相同模式：**Validation Rule** + **Comparison Engine**
- ValidationRule定义"什么是合格"，应由LLM生成
- ComparisonEngine应用规则到数据，应由框架提供

### 发现3: Type层的冗余消除
- 4个Type实际是2个正交维度的组合：Check维度 × Waiver维度
- Type3/4重复了Type1/2的check逻辑
- 应简化为统一调度器 + 原子单元组合

---

## 🔍 问题分析

### 问题1: Waiver Logic的固化与通用性

#### **Global Waiver (waiver.value=0)**

**当前实现**:
```python
if waivers.value == 0:
    violations → INFO + [WAIVED_AS_INFO]
    waive_items → INFO + [WAIVED_INFO]
    status → PASS
```

**特点**:
- 功能极其单一且固定
- 行为在文档Section 2.3.1中已明确规定
- 不需要任何自定义逻辑

**结论**: ✅ **应完全框架化，无需LLM生成**

---

#### **Selective Waiver (waiver.value>0)**

**当前实现** (仅支持字符串模式):
```python
# 3种匹配策略（文档Section 2.3.2）
- Exact Match: pattern == item
- Wildcard Match: fnmatch(item, pattern)
- Regex Match: re.match(pattern, item)
```

**实际需求场景**:
```python
# 场景1: 数值范围豁免
timing_slack < 0.1ns  # 可豁免

# 场景2: 条件逻辑豁免
stage == "synthesis" AND type == "SPEF"  # 可豁免

# 场景3: 复杂规则豁免
if lib_type in ["vendor", "legacy"] and usage < 10%  # 可豁免

# 场景4: 多维度组合
(vendor == "ARM" OR vendor == "Synopsys") AND severity == "WARNING"
```

**结论**: ✅ **需要策略模式 + LLM生成自定义matcher**

---

### 问题2: Check Logic的原子化拆分

#### **当前实现模式**

**Type1/4: Boolean Check**
```python
for item in parsed_data:
    if exists(item):  # ← Validation Rule
        found.append(item)
    else:
        missing.append(item)
```

**Type2/3: Pattern Check**
```python
for pattern in pattern_items:
    matched = find_match(parsed_data, pattern)  # ← Validation Rule
    if matched:
        found.append(matched)
    else:
        missing.append(pattern)
```

#### **共同模式识别**

两种check都包含：
1. **Validation Rule**: 定义"什么是合格"的判断逻辑
   - Boolean: `exists(item)` 或 `item.status == 'Success'`
   - Pattern: `matches(item.value, pattern)`
   - 其他可能: `in_range(item.slack, 0, 0.1)`, `satisfies_condition(item)`

2. **Comparison Engine**: 将规则应用到数据并分类结果
   - 遍历数据
   - 应用validation rule
   - 分类为 found/missing/extra

#### **拆分方案**

```python
# Validation Rule (LLM生成，定义"什么是合格")
class ValidationRule:
    def validate(self, item: Dict) -> bool:
        pass  # 具体判断逻辑
    
    def get_expected_value(self) -> Any:
        pass  # 返回期望值

# Comparison Engine (框架固定，应用规则到数据)
def comparison_engine(parsed_data, rules):
    for rule in rules:
        for item in parsed_data:
            if rule.validate(item):
                found.append(item)
            else:
                missing.append(item)
```

**结论**: ✅ **Check Logic应拆分为 ValidationRule (LLM) + ComparisonEngine (框架)**

---

### 问题3: Type层的冗余分析

#### **当前架构**

```python
Type1 = boolean_check()
Type2 = pattern_check()
Type3 = pattern_check() + waiver(value>0)  # 重复pattern_check
Type4 = boolean_check() + waiver(value>0)  # 重复boolean_check
```

#### **关键发现**

Type实际是2个正交维度的组合：

| 维度 | 取值 |
|------|------|
| **Check维度** | boolean_check vs pattern_check |
| **Waiver维度** | no_waiver vs waiver(value=0) vs waiver(value>0) |

组合结果：

| Check | Waiver | 当前Type | 代码重复 |
|-------|--------|---------|---------|
| boolean | none | Type 1 | - |
| pattern | none | Type 2 | - |
| pattern | selective | Type 3 | ✗ 重复Type2 check逻辑 |
| boolean | selective | Type 4 | ✗ 重复Type1 check逻辑 |

#### **简化方案**

```python
def unified_checker(parsed_data, config, check_type, waiver_mode):
    # Step 1: 选择check单元
    if check_type == 'boolean':
        check_result = boolean_check_unit(parsed_data, config)
    else:
        check_result = pattern_check_unit(parsed_data, config)
    
    # Step 2: 应用waiver单元
    if waiver_mode == 'none':
        return check_result
    elif waiver_mode == 'global':
        return apply_global_waiver(check_result, config)
    else:
        return apply_selective_waiver(check_result, config)
```

**结论**: ✅ **Type层可简化为 CheckUnit + WaiverUnit 的组合，消除冗余**

---

## 🏗️ 升级架构设计

### **架构总览**

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Checker.py (顶层控制器)               │
│  - Input Extraction                            │
│  - Type Dispatch → Unified Dispatcher          │
│  - Output Control                              │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  Layer 2: Unified Checker (统一检查器)          │
│  - Check Unit Selection                        │
│  - Waiver Unit Application                     │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  Layer 3: Atomic Units (原子单元)               │
│  ├─ Parsing Logic (LLM生成)                    │
│  ├─ Validation Rule (LLM生成)                  │
│  ├─ Comparison Engine (框架固定)               │
│  ├─ Global Waiver (框架固定)                   │
│  └─ Selective Waiver Matcher (框架+LLM)        │
└─────────────────────────────────────────────────┘
```

---

### **Layer 1: Checker.py (顶层控制器)**

**职责**: 配置提取、类型检测、统一调度、输出控制

```python
class Checker:
    def execute(self):
        # 1. Input Extraction
        config = self.extract_config()
        
        # 2. Parsing Logic
        parsed_data = self.parsing_logic(config['description'], 
                                         config['input_files'])
        
        # 3. Type Detection
        check_type = self.detect_check_type(config['requirements'])
        waiver_mode = self.detect_waiver_mode(config['waivers'])
        
        # 4. Unified Checker Dispatch
        result = self.unified_checker(parsed_data, config, 
                                      check_type, waiver_mode)
        
        # 5. Output Control
        self.format_output(result)
    
    def detect_check_type(self, requirements):
        """
        检测check类型
        
        Returns:
            'boolean': requirements.value = N/A
            'pattern': requirements.value > 0
        """
        req_value = requirements.get('value', 'N/A')
        return 'pattern' if (req_value != 'N/A' and req_value > 0) else 'boolean'
    
    def detect_waiver_mode(self, waivers):
        """
        检测waiver模式
        
        Returns:
            'none': waivers.value = N/A
            'global': waivers.value = 0
            'selective': waivers.value > 0
        """
        waiver_value = waivers.get('value', 'N/A')
        if waiver_value == 'N/A':
            return 'none'
        elif waiver_value == 0:
            return 'global'
        else:
            return 'selective'
```

---

### **Layer 2: Unified Checker (统一检查器)**

**职责**: 统一的检查流程，不再区分4个Type方法

```python
class UnifiedChecker:
    def check(self, parsed_data, config, check_type, waiver_mode):
        """
        统一检查流程
        
        Args:
            parsed_data: 解析后的数据
            config: 配置对象
            check_type: 'boolean' or 'pattern'
            waiver_mode: 'none', 'global', or 'selective'
        
        Returns:
            CheckResult with standard fields
        """
        # Step 1: Check Logic (选择check单元)
        if check_type == 'boolean':
            check_result = self.boolean_check_unit(parsed_data, 
                                                   config['requirements'])
        else:  # 'pattern'
            check_result = self.pattern_check_unit(parsed_data, 
                                                   config['requirements'])
        
        # Step 2: Waiver Logic (应用waiver单元)
        if waiver_mode == 'none':
            # Type 1/2: 无waiver，直接返回
            return check_result
        
        elif waiver_mode == 'global':
            # waiver.value=0: 框架自动处理
            return self.apply_global_waiver(check_result, config['waivers'])
        
        else:  # waiver_mode == 'selective'
            # waiver.value>0: 使用matcher策略
            return self.apply_selective_waiver(check_result, config['waivers'])
```

**优势**:
- ✅ 消除Type3/4对Type1/2的代码重复
- ✅ Check和Waiver逻辑完全解耦
- ✅ 新增check类型不影响waiver逻辑
- ✅ 扩展性强，易于测试

---

### **Layer 3.1: Parsing Logic (LLM生成)**

**职责**: 从input_files中提取结构化数据

```python
def parsing_logic(description: str, input_files: List[str]) -> List[Dict]:
    """
    完全由LLM根据description + input_files生成
    
    Args:
        description: Checker的检查目标描述
        input_files: 输入文件路径列表
    
    Returns:
        标准结构化数据（符合文档Section 2.4.1）:
        [
            {
                "value": "Genus version 21.1 generated 2025-01-05",
                "source_file": "/path/to/netlist.v",
                "line_number": 42,
                "matched_content": "# Generator: Genus version 21.1",
                "parsed_fields": {
                    "tool": "Genus",
                    "version": "21.1",
                    "date": "2025-01-05"
                }
            },
            ...
        ]
    """
    # LLM根据description和input_files格式生成具体解析逻辑
    pass
```

**框架提供**:
- 标准模板库（log/SPEF/DEF/SDC解析示例）
- 辅助工具（regex helpers, file readers, path resolvers）
- Metadata标准结构定义

---

### **Layer 3.2: Check Logic (拆分为2层)**

#### **3.2.1 Validation Rule (LLM生成)**

**职责**: 定义"什么是合格"的判断规则

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class ValidationRule(ABC):
    """
    抽象基类：定义validation逻辑
    由LLM根据description生成具体实现
    """
    
    @abstractmethod
    def validate(self, item: Dict) -> bool:
        """
        判断单个item是否合格
        
        Args:
            item: 解析出的单条数据（包含value, parsed_fields等）
        
        Returns:
            True if item passes validation, False otherwise
        """
        pass
    
    @abstractmethod
    def get_expected_value(self) -> Any:
        """
        返回期望值，用于missing_items的描述
        
        Returns:
            描述期望值的字符串或对象
        """
        pass
    
    def get_failure_reason(self, item: Dict) -> str:
        """
        返回失败原因（可选）
        
        Args:
            item: 未通过验证的数据项
        
        Returns:
            失败原因描述
        """
        return f"Expected: {self.get_expected_value()}, Got: {item.get('value', 'N/A')}"
```

#### **Validation Rule 示例实现**

**示例1: Boolean Check (IMP-10-0-0-00 Type1)**
```python
class NetlistSpefExistsRule(ValidationRule):
    """检查netlist/SPEF文件是否成功加载"""
    
    def validate(self, item: Dict) -> bool:
        # Boolean check: status是否为Success
        return item.get('status') == 'Success'
    
    def get_expected_value(self) -> str:
        return "Status: Success"
    
    def get_failure_reason(self, item: Dict) -> str:
        actual_status = item.get('status', 'Unknown')
        return f"Expected: Success, Got: {actual_status}"
```

**示例2: Pattern Check (IMP-10-0-0-00 Type2)**
```python
class VersionPatternRule(ValidationRule):
    """检查版本信息是否匹配指定pattern"""
    
    def __init__(self, pattern: str):
        self.pattern = pattern
    
    def validate(self, item: Dict) -> bool:
        # Pattern check: value是否匹配pattern
        value = item.get('value', '')
        
        # 支持通配符
        if '*' in self.pattern:
            return fnmatch(value, self.pattern)
        # 支持正则
        elif self.pattern.startswith('regex:'):
            return re.search(self.pattern[6:], value) is not None
        # 精确匹配或包含匹配
        else:
            return self.pattern.lower() in value.lower()
    
    def get_expected_value(self) -> str:
        return f"Pattern: {self.pattern}"
```

**示例3: 数值范围检查（扩展场景）**
```python
class TimingSlackRule(ValidationRule):
    """检查timing slack是否在合理范围内"""
    
    def __init__(self, min_slack: float = 0.0, max_slack: float = 0.1):
        self.min_slack = min_slack
        self.max_slack = max_slack
    
    def validate(self, item: Dict) -> bool:
        slack = item.get('parsed_fields', {}).get('slack', None)
        if slack is None:
            return False
        return self.min_slack <= slack <= self.max_slack
    
    def get_expected_value(self) -> str:
        return f"Slack range: [{self.min_slack}, {self.max_slack}] ns"
```

**示例4: 条件组合检查（复杂场景）**
```python
class ConditionalRule(ValidationRule):
    """复杂条件组合检查"""
    
    def validate(self, item: Dict) -> bool:
        # LLM生成复杂逻辑
        stage = item.get('parsed_fields', {}).get('stage', '')
        file_type = item.get('parsed_fields', {}).get('type', '')
        
        # 示例：synthesis阶段不需要SPEF
        if stage == 'synthesis' and file_type == 'SPEF':
            return True  # 豁免该检查
        
        # 其他逻辑...
        return item.get('status') == 'Success'
    
    def get_expected_value(self) -> str:
        return "Conditional validation based on stage and type"
```

---

#### **3.2.2 Comparison Engine (框架固定)**

**职责**: 应用ValidationRule到数据，执行标准的比较流程

```python
class ComparisonEngine:
    """
    框架提供的标准比较引擎
    所有Type共享此逻辑
    """
    
    @staticmethod
    def boolean_check(parsed_data: List[Dict], 
                     requirements: Dict) -> CheckResult:
        """
        Boolean check引擎（Type 1/4）
        
        Args:
            parsed_data: 解析后的数据列表
            requirements: requirements配置
        
        Returns:
            CheckResult with found_items and missing_items
        """
        # 加载LLM生成的ValidationRule
        rule = load_validation_rule(requirements)
        
        found_items = []
        missing_items = []
        
        for item in parsed_data:
            if rule.validate(item):
                found_items.append(item)
            else:
                missing_items.append({
                    'actual': item,
                    'expected': rule.get_expected_value(),
                    'reason': rule.get_failure_reason(item)
                })
        
        return {
            'status': 'PASS' if len(missing_items) == 0 else 'FAIL',
            'found_items': found_items,
            'missing_items': missing_items
        }
    
    @staticmethod
    def pattern_check(parsed_data: List[Dict], 
                     requirements: Dict) -> CheckResult:
        """
        Pattern check引擎（Type 2/3）
        
        Args:
            parsed_data: 解析后的数据列表
            requirements: requirements配置（包含pattern_items）
        
        Returns:
            CheckResult with found_items, missing_items, extra_items
        """
        pattern_items = requirements.get('pattern_items', [])
        
        # 为每个pattern创建ValidationRule
        rules = []
        for pattern in pattern_items:
            rule = load_validation_rule({'pattern': pattern})
            rules.append(rule)
        
        found_items = []
        missing_items = []
        extra_items = []
        
        # 匹配pattern_items
        for rule in rules:
            matched = [item for item in parsed_data if rule.validate(item)]
            if matched:
                found_items.extend(matched)
            else:
                # 必需的pattern未找到
                missing_items.append({
                    'expected': rule.get_expected_value()
                })
        
        # 找出extra_items（在parsed_data中但不匹配任何pattern）
        matched_ids = {id(item) for item in found_items}
        extra_items = [
            item for item in parsed_data 
            if id(item) not in matched_ids
        ]
        
        # 判断PASS/FAIL
        has_violations = (len(missing_items) > 0 or len(extra_items) > 0)
        
        return {
            'status': 'FAIL' if has_violations else 'PASS',
            'found_items': found_items,
            'missing_items': missing_items,
            'extra_items': extra_items
        }
```

---

### **Layer 3.3: Waiver Logic (分层设计)**

#### **3.3.1 Global Waiver (框架固定，无需LLM)**

**职责**: 处理waiver.value=0场景，完全由框架实现

```python
def apply_global_waiver(check_result: CheckResult, waivers: Dict) -> CheckResult:
    """
    框架完全处理waiver.value=0场景
    
    行为（文档Section 2.3.1明确规定）:
    1. 所有violations转为INFO + [WAIVED_AS_INFO]
    2. waive_items作为INFO + [WAIVED_INFO]
    3. 强制status = PASS
    4. unused_waivers为空（所有violation自动豁免）
    
    Args:
        check_result: Check Logic的输出结果
        waivers: waivers配置
    
    Returns:
        应用全局豁免后的CheckResult
    """
    # 收集所有violations
    violations = check_result.get('missing_items', [])
    if 'extra_items' in check_result:
        violations.extend(check_result['extra_items'])
    
    # 获取waive_items（作为注释信息）
    waive_items = waivers.get('waive_items', [])
    
    # 构建结果
    return {
        'status': 'PASS',  # 强制PASS
        'found_items': check_result['found_items'],
        'missing_items': [],  # 清空
        'extra_items': [],    # 清空
        
        # 所有violations转为waived（INFO + [WAIVED_AS_INFO]）
        'waived': [
            {
                **violation,
                'severity': 'INFO',
                'tag': '[WAIVED_AS_INFO]',
                'waiver_reason': 'Global waiver applied (waiver.value=0)'
            }
            for violation in violations
        ],
        
        # waive_items作为信息输出（INFO + [WAIVED_INFO]）
        'waived_info': [
            {
                'item': item,
                'severity': 'INFO',
                'tag': '[WAIVED_INFO]',
                'description': 'Waiver configuration comment'
            }
            for item in waive_items
        ],
        
        # 全局豁免不产生unused_waivers
        'unused_waivers': []
    }
```

**特点**:
- ✅ 完全固化，行为由文档明确规定
- ✅ 无需LLM参与，框架自动处理
- ✅ 适用于Type 3/4的waiver.value=0场景

---

#### **3.3.2 Selective Waiver (策略模式 + LLM扩展)**

**设计**: 使用策略模式，支持框架标准matcher和LLM自定义matcher

##### **抽象基类: WaiverMatcher**

```python
from abc import ABC, abstractmethod

class WaiverMatcher(ABC):
    """
    抽象基类：定义waiver匹配策略
    """
    
    @abstractmethod
    def matches(self, violation: Dict, waiver_pattern: str) -> bool:
        """
        判断violation是否匹配waiver_pattern
        
        Args:
            violation: 违例项（来自missing_items或extra_items）
            waiver_pattern: waive_items中的豁免模式
        
        Returns:
            True if matches, False otherwise
        """
        pass
    
    def get_match_reason(self, violation: Dict, waiver_pattern: str) -> str:
        """
        返回匹配原因（可选，用于traceability）
        
        Args:
            violation: 违例项
            waiver_pattern: 匹配的豁免模式
        
        Returns:
            匹配原因描述
        """
        return f"Matched waiver pattern: {waiver_pattern}"
```

---

##### **框架标准Matcher: PatternWaiverMatcher**

```python
class PatternWaiverMatcher(WaiverMatcher):
    """
    框架提供的字符串模式匹配器
    
    支持文档Section 2.3.2定义的3种策略：
    1. Exact Match: pattern == item
    2. Wildcard Match: fnmatch(item, pattern)
    3. Regex Match: re.match(pattern, item)
    """
    
    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive
    
    def matches(self, violation: Dict, waiver_pattern: str) -> bool:
        """
        字符串模式匹配
        
        匹配顺序：
        1. 检查regex前缀 → 正则匹配
        2. 检查通配符 → fnmatch
        3. 否则 → 精确匹配或包含匹配
        """
        # 提取violation的value字段用于匹配
        value = self._extract_value(violation)
        
        # 大小写处理
        if not self.case_sensitive:
            value = value.lower()
            waiver_pattern = waiver_pattern.lower()
        
        # Strategy 1: Regex Match
        if waiver_pattern.startswith('regex:'):
            regex = waiver_pattern[6:]  # 移除'regex:'前缀
            try:
                return re.search(regex, value) is not None
            except re.error:
                return False
        
        # Strategy 2: Wildcard Match
        elif '*' in waiver_pattern or '?' in waiver_pattern:
            return fnmatch(value, waiver_pattern)
        
        # Strategy 3: Exact Match
        else:
            return waiver_pattern == value
    
    def _extract_value(self, violation: Dict) -> str:
        """
        从violation中提取用于匹配的value
        
        优先级：
        1. violation['value']
        2. violation['expected']
        3. str(violation)
        """
        if 'value' in violation:
            return str(violation['value'])
        elif 'expected' in violation:
            return str(violation['expected'])
        else:
            return str(violation)
    
    def get_match_reason(self, violation: Dict, waiver_pattern: str) -> str:
        value = self._extract_value(violation)
        
        if waiver_pattern.startswith('regex:'):
            return f"Value '{value}' matches regex pattern '{waiver_pattern}'"
        elif '*' in waiver_pattern or '?' in waiver_pattern:
            return f"Value '{value}' matches wildcard pattern '{waiver_pattern}'"
        else:
            return f"Value '{value}' matches exact pattern '{waiver_pattern}'"
```

---

##### **LLM自定义Matcher: CustomWaiverMatcher**

```python
class CustomWaiverMatcher(WaiverMatcher):
    """
    由LLM根据复杂豁免需求生成
    
    适用场景：
    - 数值范围豁免
    - 条件逻辑豁免
    - 多维度组合豁免
    - 复杂业务规则豁免
    """
    
    def matches(self, violation: Dict, waiver_pattern: str) -> bool:
        """
        自定义匹配逻辑
        由LLM根据具体需求生成
        """
        # LLM生成具体实现
        pass
```

**示例1: 数值范围豁免**
```python
class SlackRangeWaiverMatcher(CustomWaiverMatcher):
    """豁免slack在指定范围内的violation"""
    
    def matches(self, violation: Dict, waiver_pattern: str) -> bool:
        # waiver_pattern格式: "slack<0.1ns"
        if not waiver_pattern.startswith('slack'):
            return False
        
        # 解析范围
        if '<' in waiver_pattern:
            _, threshold = waiver_pattern.split('<')
            threshold = float(threshold.replace('ns', '').strip())
            
            # 提取violation的slack值
            slack = violation.get('parsed_fields', {}).get('slack', None)
            if slack is None:
                return False
            
            return slack < threshold
        
        return False
```

**示例2: 条件逻辑豁免**
```python
class ConditionalWaiverMatcher(CustomWaiverMatcher):
    """基于多条件的豁免"""
    
    def matches(self, violation: Dict, waiver_pattern: str) -> bool:
        # waiver_pattern格式: "stage==synthesis AND type==SPEF"
        
        # 解析条件
        conditions = self._parse_conditions(waiver_pattern)
        
        # 评估所有条件
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            expected = condition['value']
            
            actual = violation.get('parsed_fields', {}).get(field)
            
            if not self._evaluate_condition(actual, operator, expected):
                return False
        
        return True
    
    def _parse_conditions(self, pattern: str) -> List[Dict]:
        # 解析条件表达式（支持AND/OR/NOT等）
        # LLM生成具体实现
        pass
    
    def _evaluate_condition(self, actual, operator, expected) -> bool:
        # 评估单个条件
        if operator == '==':
            return actual == expected
        elif operator == '!=':
            return actual != expected
        elif operator == 'in':
            return actual in expected
        # 其他操作符...
        return False
```

**示例3: 多维度组合豁免**
```python
class MultiDimensionWaiverMatcher(CustomWaiverMatcher):
    """复杂多维度组合豁免"""
    
    def matches(self, violation: Dict, waiver_pattern: str) -> bool:
        # waiver_pattern格式: "(vendor==ARM OR vendor==legacy) AND usage<10%"
        
        parsed_fields = violation.get('parsed_fields', {})
        
        vendor = parsed_fields.get('vendor', '')
        usage = parsed_fields.get('usage', 0)
        
        # 评估组合条件
        vendor_match = vendor in ['ARM', 'legacy']
        usage_match = usage < 10
        
        return vendor_match and usage_match
```

---

##### **框架应用Selective Waiver**

```python
def apply_selective_waiver(check_result: CheckResult, 
                          waivers: Dict) -> CheckResult:
    """
    框架提供的selective waiver引擎
    
    流程（文档Section 2.3.2）:
    1. 收集violations（missing_items + extra_items）
    2. 使用WaiverMatcher匹配每个violation与waive_items
    3. 分类为waived/unwaived
    4. 查找unused_waivers
    5. 判断最终status
    
    Args:
        check_result: Check Logic的输出结果
        waivers: waivers配置
    
    Returns:
        应用选择性豁免后的CheckResult
    """
    waive_items = waivers.get('waive_items', [])
    
    # 加载WaiverMatcher（框架标准或LLM自定义）
    matcher = load_waiver_matcher(waivers)
    
    # 收集所有violations
    violations = []
    missing_violations = check_result.get('missing_items', [])
    extra_violations = check_result.get('extra_items', [])
    
    for v in missing_violations:
        violations.append(('missing', v))
    for v in extra_violations:
        violations.append(('extra', v))
    
    # 应用waiver匹配
    waived = []
    unwaived_missing = []
    unwaived_extra = []
    used_patterns = set()
    
    for violation_type, violation in violations:
        matched = False
        matched_pattern = None
        
        # 尝试匹配每个waive_item
        for waiver_pattern in waive_items:
            if matcher.matches(violation, waiver_pattern):
                # 匹配成功
                waived.append({
                    **violation,
                    'waiver_pattern': waiver_pattern,
                    'waiver_reason': matcher.get_match_reason(violation, waiver_pattern),
                    'severity': 'INFO',
                    'tag': '[WAIVER]'
                })
                used_patterns.add(waiver_pattern)
                matched = True
                break
        
        # 未匹配的violation保留为ERROR
        if not matched:
            if violation_type == 'missing':
                unwaived_missing.append(violation)
            else:
                unwaived_extra.append(violation)
    
    # 查找unused waivers
    unused_waivers = [
        {
            'pattern': pattern,
            'severity': 'WARN',
            'tag': '[WAIVER]',
            'reason': 'Waiver defined but no violation matched'
        }
        for pattern in waive_items 
        if pattern not in used_patterns
    ]
    
    # 判断最终status
    has_unwaived = (len(unwaived_missing) > 0 or len(unwaived_extra) > 0)
    
    return {
        'status': 'FAIL' if has_unwaived else 'PASS',
        'found_items': check_result['found_items'],
        'missing_items': unwaived_missing,
        'extra_items': unwaived_extra,
        'waived': waived,
        'unused_waivers': unused_waivers
    }
```

---

## 📊 架构对比总结

### **功能维度对比**

| 维度 | V1.0 (当前架构) | V2.0 (升级架构) | 改进 |
|------|----------------|----------------|------|
| **Type层结构** | 4个独立Type方法 | 统一调度器 | ✅ 消除冗余 |
| **Check Logic** | 整体方法（boolean/pattern） | ValidationRule + ComparisonEngine | ✅ 原子化分离 |
| **Waiver Logic** | Mixin工具集 | Global(框架) + Selective(策略) | ✅ 固化+扩展 |
| **代码复用** | Type3/4重复Type1/2 | 完全消除重复 | ✅ 100%复用 |
| **扩展性** | 新Type需重写 | 新Rule/Matcher即可 | ✅ 插件化 |

### **LLM生成范围对比**

| 组件 | V1.0 | V2.0 | 变化 |
|------|------|------|------|
| **Parsing Logic** | LLM生成 | LLM生成 | 保持 |
| **Check Logic** | LLM生成整体方法 | LLM仅生成ValidationRule | ✅ 职责更清晰 |
| **Waiver Logic** | LLM生成部分逻辑 | Global固化 + LLM生成CustomMatcher | ✅ 分层明确 |
| **Output Formatting** | 框架提供 | 框架提供 | 保持 |

### **框架职责对比**

| 功能 | V1.0 | V2.0 | 变化 |
|------|------|------|------|
| **Type Dispatch** | 4个Type方法 | 统一调度器 | ✅ 简化 |
| **ComparisonEngine** | 内嵌在Type方法 | 独立框架组件 | ✅ 提取 |
| **Global Waiver** | 部分自动处理 | 完全框架固化 | ✅ 100%固化 |
| **Pattern Matcher** | WaiverHandlerMixin | 独立策略组件 | ✅ 策略化 |
| **Output Formatting** | OutputBuilderMixin | 保持 | 不变 |

### **代码量对比（估算）**

| 组件 | V1.0 | V2.0 | 减少 |
|------|------|------|------|
| **Type方法** | ~400行 × 4 = 1600行 | 统一调度器 ~200行 | -1400行 |
| **Check Logic** | 混在Type内 | ValidationRule ~50行 + Engine ~100行 | +150行（但可复用） |
| **Waiver Logic** | WaiverHandlerMixin ~600行 | Global ~50行 + Selective ~150行 | -400行 |
| **总计** | ~2200行 | ~500行（框架） + Rule/Matcher（LLM） | -1700行框架代码 |

---

## 🎯 实施建议

### **建议1: 固化Global Waiver**

**优先级**: ⭐⭐⭐⭐⭐ (最高)

**理由**:
- ✅ 功能单一且固定，完全符合框架化条件
- ✅ 文档Section 2.3.1已明确规定全部行为
- ✅ 无需LLM参与，降低生成成本
- ✅ 保证行为一致性，减少错误

**实施步骤**:
1. 在框架中实现`apply_global_waiver()`函数
2. 移除相关LLM生成提示
3. 更新文档，标注"框架自动处理"

**预期收益**:
- 每个checker减少~50行LLM生成代码
- 行为100%一致，无偏差风险

---

### **建议2: 原子化Check Logic**

**优先级**: ⭐⭐⭐⭐ (高)

**理由**:
- ✅ 职责清晰分离：ValidationRule定义规则，ComparisonEngine执行比较
- ✅ 支持任意复杂validation逻辑（不局限于exists/pattern）
- ✅ LLM只需生成小的ValidationRule，降低生成难度
- ✅ ComparisonEngine由框架提供，保证逻辑正确性

**实施步骤**:
1. 定义`ValidationRule`抽象基类
2. 实现`ComparisonEngine.boolean_check()`和`.pattern_check()`
3. 提供ValidationRule示例模板（exists/pattern/range等）
4. 更新LLM生成提示，只生成ValidationRule

**预期收益**:
- LLM生成代码量减少60%（只生成rule，不生成engine）
- 支持更复杂的validation场景
- 框架保证比较逻辑的正确性

---

### **建议3: 策略化Selective Waiver**

**优先级**: ⭐⭐⭐ (中高)

**理由**:
- ✅ 支持框架标准matcher（字符串模式）
- ✅ 支持LLM自定义matcher（复杂条件）
- ✅ 扩展性极强，适应各种豁免场景
- ✅ 保持向后兼容（现有字符串模式继续工作）

**实施步骤**:
1. 定义`WaiverMatcher`抽象基类
2. 实现框架标准`PatternWaiverMatcher`（文档Section 2.3.2三种策略）
3. 提供`CustomWaiverMatcher`模板和示例
4. 实现`apply_selective_waiver()`引擎
5. 更新配置格式，支持指定matcher类型

**预期收益**:
- 支持数值范围、条件逻辑等复杂豁免
- 框架提供标准matcher，覆盖80%场景
- LLM按需生成CustomMatcher，灵活应对特殊需求

---

### **建议4: 简化Type层**

**优先级**: ⭐⭐⭐⭐ (高)

**理由**:
- ✅ 消除Type3/4对Type1/2的代码重复
- ✅ 统一调度逻辑，易于维护
- ✅ Check和Waiver完全解耦
- ✅ 新增check/waiver类型不影响其他部分

**实施步骤**:
1. 实现`UnifiedChecker.check()`方法
2. 重构Type检测逻辑（check_type + waiver_mode）
3. 移除4个独立Type方法
4. 更新文档，反映统一架构

**预期收益**:
- 框架代码减少~1400行
- 维护成本降低70%
- 扩展新Type只需增加Rule/Matcher

---

### **实施顺序建议**

**Phase 1: 核心重构（Week 1-2）**
1. ✅ 固化Global Waiver（建议1）
2. ✅ 实现ComparisonEngine框架（建议2前置）
3. ✅ 简化Type层为统一调度器（建议4）

**Phase 2: 原子化改造（Week 3-4）**
4. ✅ 定义ValidationRule抽象基类（建议2）
5. ✅ 提供示例Rule模板
6. ✅ 更新LLM生成提示

**Phase 3: 策略化扩展（Week 5-6）**
7. ✅ 实现WaiverMatcher策略模式（建议3）
8. ✅ 提供框架标准PatternMatcher
9. ✅ 提供CustomMatcher模板和示例

**Phase 4: 文档与测试（Week 7-8）**
10. ✅ 更新global_rules.md反映新架构
11. ✅ 编写完整测试用例
12. ✅ 迁移现有checker到新架构

---

### **风险评估与缓解**

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| LLM生成ValidationRule质量不稳定 | 中 | 中 | 提供详细模板和示例；框架验证Rule接口 |
| CustomMatcher复杂度过高 | 中 | 低 | 优先使用框架PatternMatcher；分阶段引入 |
| 现有checker迁移成本 | 高 | 高 | 保持向后兼容；提供自动迁移工具 |
| 文档学习成本 | 低 | 中 | 提供清晰示例；分层文档（基础/高级） |

---

## ✅ 总结

### **核心改进**

1. **固化Global Waiver**: 无需LLM，框架100%处理
2. **原子化Check Logic**: ValidationRule (LLM) + ComparisonEngine (框架)
3. **策略化Selective Waiver**: PatternMatcher (框架) + CustomMatcher (LLM)
4. **简化Type层**: 4个方法 → 统一调度器

### **预期收益**

- ✅ 框架代码减少~1700行（-77%）
- ✅ LLM生成代码减少~60%
- ✅ 维护成本降低~70%
- ✅ 扩展性提升10倍
- ✅ 支持复杂validation和waiver场景

### **下一步行动**

等待确认后，可以：
1. 更新`global_rules.md`反映新架构
2. 实施Phase 1核心重构
3. 编写详细的API文档和示例

---

**文档结束**
