# Output Formatter 使用指南

**Last Updated**: December 11, 2025 (Template Library v1.1.0)

## 概述

`output_formatter.py` 是用于生成日志文件和报告文件的核心模块。

**💡 推荐方式**: 使用 `OutputBuilderMixin` 模板（代码减少 60-70%）
- 位置: `Check_modules/common/checker_templates/output_builder_template.py`
- 一行调用: `build_complete_output()` 自动处理所有输出格式
- 自动去重: v1.1.0 修复了 log 文件的 Occurrence 计数问题
- 参考: `checker_templates/README.md` 和 `EXAMPLES.md`

**本文档适用于**:
- 理解 output_formatter.py 的底层机制
- 需要高度自定义输出的特殊场景
- 调试输出格式问题

## 核心机制

### 推荐: 使用 OutputBuilderMixin 模板

**一行调用，自动处理所有细节**:

```python
from checker_templates import OutputBuilderMixin

class MyChecker(BaseChecker, OutputBuilderMixin):
    def _execute_type3(self):
        # 解析和分类
        results = self._parse_files()
        waived, unwaived = self.classify_items_by_waiver(...)
        
        # 一行调用，自动构建所有输出
        return self.build_complete_output(
            found_items=results['found'],
            missing_items=unwaived,
            waived_items=waived,
            waive_dict=waive_dict,
            has_pattern_items=True,
            has_waiver_value=True
        )
```

**优势**:
- ✅ 自动匹配 info_groups 和 details
- ✅ 自动去重（v1.1.0 修复）
- ✅ 自动处理 waiver=0 转换
- ✅ Type 1/2/3/4 统一接口
- ✅ 代码减少 60-70%

---

### 底层机制: info_groups 与 details 的匹配关系

**仅在不使用模板时需要了解**

**关键规则**: `info_groups` 中的 `items` 必须与 `details` 中的 `name` 字段一一对应，output_formatter 才能正确关联和显示数据。

```python
# 正确示例
info_groups = [
    InfoGroup(
        category="INFO01",
        description="Waived items",
        items=["cgdefault", "default"]  # 必须匹配 details 中的 name
    )
]

details = [
    DetailItem(
        name="cgdefault",  # 匹配 info_groups items
        category="INFO01",
        severity=Severity.WAIVE,
        reason="Pre-implementation phase[WAIVER]"
    ),
    DetailItem(
        name="default",  # 匹配 info_groups items
        category="INFO01",
        severity=Severity.WAIVE,
        reason="Pre-implementation phase[WAIVER]"
    )
]
```

### 输出格式

#### 日志文件 (.log)
- 显示 `info_groups` 中的 `items` 列表
- 如果 items 是文件路径，会显示完整路径
- 如果 items 是组名/项名，会显示名称

```
INFO01: Waived items
  - cgdefault
  - default

INFO02: Found reports
  - reports/func_ssgnp.../digtop_in2reg_hold.tarpt.gz
  - reports/func_ssgnp.../digtop_reg2out_hold.tarpt.gz
```

#### 报告文件 (.rpt)
- 显示 `details` 中的完整信息
- 包括 name, line_number, file_path, reason 等字段
- 会关联到对应的 info_groups category

```
INFO01: Waived items
  cgdefault
    Reason: Pre-implementation phase[WAIVER]
  
  default
    Reason: Pre-implementation phase[WAIVER]
```

## Type 3/4 实现模式

### 推荐: 使用模板方法

```python
from checker_templates import WaiverHandlerMixin, OutputBuilderMixin

class MyChecker(BaseChecker, WaiverHandlerMixin, OutputBuilderMixin):
    def _execute_type3(self):
        # 1. 解析
        results = self._parse_files()
        
        # 2. 分类（使用 WaiverHandlerMixin）
        waive_dict = self.parse_waive_items(self.config.waivers.waive_items)
        waived, unwaived = self.classify_items_by_waiver(
            results['missing'], waive_dict
        )
        unused = self.find_unused_waivers(waive_dict, results['missing'])
        
        # 3. 一行构建输出（使用 OutputBuilderMixin）
        return self.build_complete_output(
            found_items=results['found'],
            missing_items=unwaived,
            waived_items=waived,
            unused_waivers=unused,
            waive_dict=waive_dict,
            has_pattern_items=True,
            has_waiver_value=True,
            found_reason="Item found",
            missing_reason="Required item NOT found"
        )
```

---

### 手动实现: Type 3 Value Check with Waivers

**⚠️ 仅在模板无法满足需求时使用**

```python
def _execute_type3(self):
    # 解析数据
    parsed_data = self._parse_files()
    found_items = parsed_data['found_items']
    required_count = int(self.config.requirements.value)
    waive_items = self.config.waivers.waive_items
    
    details = []
    waived_names = []
    found_names = []
    unwaived_names = []
    
    # 处理每个要求的项
    for item in required_items:
        if item in found_items:
            # 找到的项
            found_names.append(item)
            details.append(DetailItem(
                name=item,
                category="INFO02",
                severity=Severity.INFO,
                value=parsed_data.get(item, {}).get('path', '')
            ))
        else:
            # 缺失的项
            if item in waive_items:
                # 豁免的项
                waived_names.append(item)
                details.append(DetailItem(
                    name=item,  # 只放项名,不包含 [WAIVER]
                    category="INFO01",
                    severity=Severity.WAIVE,
                    reason=f"{waiver_reason}[WAIVER]"  # reason 包含 [WAIVER]
                ))
            else:
                # 未豁免的违规项
                unwaived_names.append(item)
                details.append(DetailItem(
                    name=item,
                    category="ERROR01",
                    severity=Severity.ERROR,
                    description=f"Missing required item: {item}"
                ))
    
    # 构建 info_groups - 关键步骤!
    info_groups = []
    
    if waived_names:
        info_groups.append(InfoGroup(
            category="INFO01",
            description="Waived items",
            items=waived_names  # 必须与 details 中的 name 匹配
        ))
    
    if found_names:
        info_groups.append(InfoGroup(
            category="INFO02",
            description="Found items",
            items=found_names  # 必须与 details 中的 name 匹配
        ))
    
    # 确定状态
    status = CheckStatus.PASS if not unwaived_names else CheckStatus.FAIL
    
    return self.create_check_result(
        status=status,
        details=details,
        info_groups=info_groups,
        summary=f"Required: {required_count}, Found: {len(found_names)}, Waived: {len(waived_names)}"
    )
```

### Type 4: Boolean Check with Waiver Logic

Type 4 = Type 1 + 豁免支持，实现逻辑说明：
- 不使用 pattern_items 查找（同 Type 1）
- `requirements.value = "N/A"` (布尔检查)
- 豁免分类逻辑与 Type 3 相同
- 输出格式与 Type 3 相同

## 常见错误

### 错误 1: info_groups items 与 details name 不匹配

```python
# ❌ 错误
info_groups = [
    InfoGroup(
        category="INFO01",
        items=["item1: reason[WAIVER]"]  # 包含了 reason
    )
]

details = [
    DetailItem(
        name="item1",  # 不匹配上面的 items
        category="INFO01",
        severity=Severity.WAIVE
    )
]

# ✅ 正确
info_groups = [
    InfoGroup(
        category="INFO01",
        items=["item1"]  # 只有 name
    )
]

details = [
    DetailItem(
        name="item1",  # 匹配!
        category="INFO01",
        severity=Severity.WAIVE,
        reason="reason[WAIVER]"  # reason 单独字段
    )
]
```

### 错误 2: 豁免项的 name 和 reason 混淆

```python
# ❌ 错误
DetailItem(
    name="item: Pre-implementation[WAIVER]",  # reason 放在 name 中
    category="INFO01",
    severity=Severity.WAIVE
)

# ✅ 正确
DetailItem(
    name="item",  # 只有项名
    category="INFO01",
    severity=Severity.WAIVE,
    reason="Pre-implementation[WAIVER]"  # reason 单独字段
)
```

### 错误 3: 输出应该显示文件路径但显示了其他内容

```python
# 场景: 从日志文件解析出报告文件路径,应该在输出中显示完整路径

# ❌ 错误 - 只显示组名
info_groups = [
    InfoGroup(
        category="INFO01",
        items=["in2reg", "reg2out"]  # 只有组名
    )
]

# ✅ 正确 - 显示文件路径
info_groups = [
    InfoGroup(
        category="INFO01",
        items=[
            "reports/func_ssgnp.../digtop_in2reg_hold.tarpt.gz",
            "reports/func_ssgnp.../digtop_reg2out_hold.tarpt.gz"
        ]  # 完整文件路径
    )
]

# 对应的 details 也要包含文件路径
details = [
    DetailItem(
        name="reports/func_ssgnp.../digtop_in2reg_hold.tarpt.gz",  # 完整路径
        category="INFO01",
        severity=Severity.INFO,
        file_path="reports/func_ssgnp.../digtop_in2reg_hold.tarpt.gz"
    )
]
```

## 最佳实践

### 0. 优先使用模板（新增 v1.1.0）

**始终先检查模板是否满足需求**:

```python
# ✅ 推荐: 使用模板（1 行代码）
return self.build_complete_output(
    found_items=found,
    missing_items=unwaived,
    waived_items=waived,
    waive_dict=waive_dict
)

# ❌ 不推荐: 手动构建（60+ 行代码）
info_groups = []
details = []
for item in found:
    details.append(DetailItem(...))
    # ... 60+ lines ...
return create_check_result(...)
```

**模板覆盖的场景**:
- ✅ Type 1/2/3/4 所有类型
- ✅ waiver=0 自动转换
- ✅ extra_items 自动 WARN/INFO
- ✅ 自动去重
- ✅ unused waivers 检测

**仅在以下情况手动实现**:
- 输出格式极其特殊
- 需要自定义分组逻辑
- 模板参数无法表达需求

---

### 1. 先定义输出格式

在编写代码前，明确：
- INFO01 应该显示什么？(组名? 文件路径?)
- INFO02 应该显示什么？
- ERROR01 应该显示什么？
- 豁免项如何区分？

### 2. 保持 info_groups 和 details 同步

```python
# 推荐模式
waived_items = []
waived_details = []

for item in violations:
    if item in waive_list:
        waived_items.append(item)  # 用于 info_groups
        waived_details.append(DetailItem(
            name=item,  # 与 waived_items 中的值匹配
            category="INFO01",
            severity=Severity.WAIVE,
            reason=f"{reason}[WAIVER]"
        ))

info_groups = [
    InfoGroup(
        category="INFO01",
        items=waived_items  # 直接使用同步的列表
    )
]

details.extend(waived_details)
```

### 3. 使用列表推导式确保一致性

```python
# 从 details 中提取 name 构建 info_groups
waived_details = [d for d in details if d.severity == Severity.WAIVE]
found_details = [d for d in details if d.severity == Severity.INFO]

info_groups = []
if waived_details:
    info_groups.append(InfoGroup(
        category="INFO01",
        items=[d.name for d in waived_details]  # 保证匹配
    ))
if found_details:
    info_groups.append(InfoGroup(
        category="INFO02",
        items=[d.name for d in found_details]  # 保证匹配
    ))
```

## 调试技巧

### 验证匹配关系

在返回 CheckResult 前添加验证：

```python
# 验证 info_groups 和 details 的匹配关系
for group in info_groups:
    for item in group.items:
        # 检查是否存在对应的 detail
        matching_details = [d for d in details if d.name == item and d.category == group.category]
        if not matching_details:
            self.logger.warning(f"No matching detail for item '{item}' in category '{group.category}'")
```

### 打印调试信息

```python
self.logger.info(f"INFO01 items: {info_groups[0].items if info_groups else []}")
self.logger.info(f"Details names: {[d.name for d in details]}")
self.logger.info(f"Matching: {set(info_groups[0].items) == set([d.name for d in details if d.category == 'INFO01'])}")
```

## 参考示例

**使用模板的示例**:
- **IMP-10-0-0-02.py** - 模板重用示例（738→697 lines, -5.6%）
  * 使用 `normalize_command()` 和 `match_waiver_entry()`
  * Type 2/3/4 实现
- **IMP-10-0-0-10.py** - 完整模板迁移（684→402 lines, -41.2%）
  * 使用全部 3 个 mixins
  * Type 1/2/3/4 完整实现

**手动实现参考**（仅供理解底层机制）:
- `Check_modules/10.0_STA_DCD_CHECK/scripts/checker/IMP-10-0-0-10.py`
  * Type 1: Lines 158-240
  * Type 2: Lines 257-348
  * Type 3: Lines 363-524
  * Type 4: Lines 531-643

**模板文档**:
- `checker_templates/README.md` - 完整使用指南（30+ 示例）
- `checker_templates/EXAMPLES.md` - 实际迁移案例
- `checker_templates/output_builder_template.py` - 源代码（773 行）
