# IMP-10-0-0-05 配置说明与示例

## 检查项目
**Confirm all clocks propagated during STA**

确认所有时钟在静态时序分析 (STA) 期间都已传播。时钟传播 (Clock Propagation) 是指时钟信号通过时钟树网络传播，包括实际的延迟和偏差。非传播时钟 (Propagated=n) 可能导致时序分析不准确。

---

## 功能特性

### ✅ 自动检测四种 Checker 类型
脚本会根据 YAML 配置自动识别使用哪种类型：
- **Type 1**: 布尔检查（所有时钟）- 无豁免
- **Type 2**: 数值比较（特定时钟）- 无豁免
- **Type 3**: 数值比较 + 豁免逻辑
- **Type 4**: 布尔检查 + 豁免逻辑

### ✅ 解析 Tempus clocks.rpt 报告
从 `clocks.rpt.gz` 提取时钟传播信息：

**报告格式**:
```
Clock Name          Source  View         Period  Generated  Propagated
------------------------------------------------------------------
IO_ASYNC_CLOCK      CLK     func_mode    10.0    y          n
PHASE_ALIGN_CLOCK   PLL     func_mode    5.0     y          n
SYSTEM_CLOCK        OSC     func_mode    20.0    y          y
```

**提取字段**:
- **Clock Name**: 时钟名称
- **Propagated**: 传播状态 (y=已传播, n=未传播)
- **Line Number**: 报告中的行号

### ✅ 支持 gzip 压缩文件
- 自动检测并解析 `.gz` 格式的报告文件
- 兼容普通文本格式的 `.rpt` 文件

### ✅ 精确匹配模式
- **pattern_items**: 期望传播的时钟名称（精确匹配）
- **waive_items**: 豁免的时钟名称（允许不传播）
- 不支持通配符，必须完全匹配时钟名称

### ✅ Waiver 标签规则 (2025-12-02)

**当 waivers.value > 0 时（Type 3/4）**:
- 已豁免的未传播时钟 → INFO + `[WAIVER]`
- 未使用的豁免（时钟已传播或不存在）→ WARN + `[WAIVER]`

**当 waivers.value = 0 时（Type 1/2）**:
- 检查发现的 FAIL/WARN → INFO + `[WAIVED_AS_INFO]`（强制豁免）
- waive_items 配置项 → INFO + `[WAIVED_INFO]`（配置的豁免）
- 强制 PASS（所有失败都被豁免）

**当 waivers.value = N/A 时（Type 1/2）**:
- 正常模式，根据实际检查结果判定 PASS/FAIL

### ✅ 自定义分组描述 (Type 3/4)
Type 3 和 Type 4 使用自定义错误分组描述：
- **ERROR01**: "Expected clock not propagated" / "Clock not propagated"
- **INFO01**: "Expected clock not propagated but waived" / "Clock not propagated but waived"
- **WARN01**: "Waiver not used"

---

## 📋 配置文件示例

### 🔹 Type 1: 布尔检查（所有时钟）

**用途**: 验证设计中所有时钟都已传播

#### 方案 A: 正常模式 (waivers.value = N/A)

**配置文件**: `IMP-10-0-0-05.type1.yaml`

```yaml
# Type 1: Boolean Check (Normal Mode)
# 简单的布尔检查：所有时钟都应该传播
# 任何未传播的时钟都视为 FAIL

description: Confirm all clocks propegated during STA.

requirements:
  value: N/A
  pattern_items: []

input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\clocks.rpt.gz

waivers:
  value: N/A
  waive_items: []
```

**检查逻辑**:
- ✅ 所有时钟 Propagated=y → PASS
- ❌ 任何时钟 Propagated=n → FAIL

**预期输出 (PASS - 所有时钟已传播)**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-INFO01: All clocks propagated:
  Severity: Info Occurrence: 3
  - SYSTEM_CLOCK
  - MAIN_CLOCK
  - AUX_CLOCK
```

**预期输出 (FAIL - 有未传播时钟)**:
```
FAIL:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-ERROR01: Found 2 clock(s) not propagated:
  Severity: Fail Occurrence: 2
  - IO_ASYNC_CLOCK
  - PHASE_ALIGN_CLOCK
```

#### 方案 B: 强制PASS模式 (waivers.value = 0)

**配置文件**: `IMP-10-0-0-05.type1_waiver0.yaml`

```yaml
# Type 1: Boolean Check (Forced PASS Mode)
# 强制PASS模式：所有时钟都转为 INFO，后缀 [WAIVED_AS_INFO]
# 用于调试或过渡期

description: Confirm all clocks propegated during STA.

requirements:
  value: N/A
  pattern_items: []

input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\clocks.rpt.gz

waivers:
  value: 0                          # 强制PASS
  waive_items:
    - debug_note_1
    - debug_note_2
```

**检查逻辑**:
- 所有时钟（已传播/未传播）→ INFO + `[WAIVED_AS_INFO]`
- waive_items → INFO + `[WAIVED_INFO]`
- 强制 PASS

**预期输出 (强制PASS)**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-INFO01: Clock propagation check (forced PASS mode):
  Severity: Info Occurrence: 4
  - IO_ASYNC_CLOCK (未传播但被强制豁免)
  - SYSTEM_CLOCK (已传播)
  - debug_note_1 (配置的豁免项)
  - debug_note_2 (配置的豁免项)
```

---

### 🔹 Type 2: 数值比较（特定时钟）

**用途**: 验证特定时钟列表都已传播

#### 方案 A: 正常模式 (waivers.value = N/A)

**配置文件**: `IMP-10-0-0-05.type2.yaml`

```yaml
# Type 2: Value Comparison (Normal Mode)
# 数值比较：验证特定时钟列表是否都已传播
# requirements.value 建议等于 pattern_items 的数量

description: Confirm all clocks propegated during STA.

requirements:
  value: 2                          # 期望 2 个时钟已传播
  pattern_items:                    # 需要检查的时钟名称（精确匹配）
    - IO_ASYNC_CLOCK
    - PHASE_ALIGN_CLOCK

input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\clocks.rpt.gz

waivers:
  value: N/A
  waive_items: []
```

**检查逻辑**:
- 精确匹配 `pattern_items` 中的时钟名称
- **已传播** → INFO（期望的时钟已传播）
- **未传播** → FAIL（期望传播但未传播）
- **缺失** → FAIL（期望的时钟不存在）
- **PASS**: 所有 pattern_items 都已传播
- **FAIL**: 有未传播或缺失的时钟

**预期输出 (PASS - 所有指定时钟已传播)**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-INFO01: All expected clocks propagated:
  Severity: Info Occurrence: 2
  - IO_ASYNC_CLOCK
  - PHASE_ALIGN_CLOCK
```

**预期输出 (FAIL - 有时钟未传播)**:
```
FAIL:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-ERROR01: Clock propagation check failed:
  Severity: Fail Occurrence: 2
  - IO_ASYNC_CLOCK
  - PHASE_ALIGN_CLOCK
```

#### 方案 B: 强制PASS模式 (waivers.value = 0)

**配置文件**: `IMP-10-0-0-05.type2_waiver0.yaml`

```yaml
# Type 2: Value Comparison (Forced PASS Mode)
# 强制PASS模式：所有检查结果都转为 INFO
# 所有 FAIL → INFO + [WAIVED_AS_INFO]
# waive_items → INFO + [WAIVED_INFO]

description: Confirm all clocks propegated during STA.

requirements:
  value: 2
  pattern_items:
    - IO_ASYNC_CLOCK
    - PHASE_ALIGN_CLOCK

input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\clocks.rpt.gz

waivers:
  value: 0                          # 强制PASS
  waive_items:
    - debug_waive_item
```

**检查逻辑**:
- 所有检查结果 → INFO + `[WAIVED_AS_INFO]`
- waive_items → INFO + `[WAIVED_INFO]`
- 强制 PASS

**预期输出 (强制PASS)**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-INFO01: Clock propagation check (forced PASS mode):
  Severity: Info Occurrence: 3
  - IO_ASYNC_CLOCK (未传播但被强制豁免)
  - PHASE_ALIGN_CLOCK (未传播但被强制豁免)
  - debug_waive_item (配置的豁免项)
```

---

### 🔹 Type 3: 数值比较 + 豁免逻辑

**用途**: 验证特定时钟传播，同时允许豁免某些时钟

**配置文件**: `IMP-10-0-0-05.type3.yaml`

```yaml
# Type 3: Value Comparison with Waiver Logic
# 数值比较 + 豁免逻辑
# pattern_items: 期望传播的时钟列表
# waive_items: 允许不传播的时钟列表（从 pattern_items 中豁免）

description: Confirm all clocks propegated during STA.

requirements:
  value: 2                          # 期望值（可选，建议设置）
  pattern_items:                    # 需要检查的时钟
    - IO_ASYNC_CLOCK
    - PHASE_ALIGN_CLOCK
    - SYSTEM_CLOCK

input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\clocks.rpt.gz

waivers:
  value: 1                          # 豁免数量（必须 > 0）
  waive_items:                      # 豁免的时钟（允许不传播）
    - IO_ASYNC_CLOCK
```

**检查逻辑**:
1. **pattern_items** 中的时钟：
   - 在 **waive_items** 中 + 未传播 → INFO + `[WAIVER]`（已豁免）
   - 不在 **waive_items** 中 + 未传播 → FAIL（真正的失败）
   - 已传播 → INFO（正常）

2. **waive_items** 未使用：
   - 时钟已传播 → WARN + `[WAIVER]`（豁免未使用）
   - 时钟不存在 → WARN + `[WAIVER]`（豁免未使用）

3. **非 pattern_items** 的时钟：
   - 未传播且不在 waive_items → FAIL（意外的未传播时钟）

**预期输出 (FAIL - 有非豁免的未传播时钟)**:
```
FAIL:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-ERROR01: Expected clock not propagated:
  Severity: Fail Occurrence: 1
  - PHASE_ALIGN_CLOCK

IMP-10-0-0-05-INFO01: Expected clock not propagated but waived:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK
```

**Report 文件详细内容**:
```
Fail Occurrence: 1
1: Fail: PHASE_ALIGN_CLOCK. In line 16, C:\...\clocks.rpt.gz: Expected clock not propagated

Info Occurrence: 2
1: Info: SYSTEM_CLOCK. In line 17, C:\...\clocks.rpt.gz: Expected clock propagated
2: Info: IO_ASYNC_CLOCK. In line 15, C:\...\clocks.rpt.gz: Clock not propagated (waived)[WAIVER]
```

**预期输出 (PASS with WARNING - 豁免未使用)**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-WARN01: Waiver not used:
  Severity: Warn Occurrence: 1
  - IO_ASYNC_CLOCK

IMP-10-0-0-05-INFO01: Clock propagation check passed with warnings:
  Severity: Info Occurrence: 2
  - PHASE_ALIGN_CLOCK
  - SYSTEM_CLOCK
```

---

### 🔹 Type 4: 布尔检查 + 豁免逻辑

**用途**: 验证所有时钟传播，同时允许豁免某些时钟

**配置文件**: `IMP-10-0-0-05.type4.yaml`

```yaml
# Type 4: Boolean Check with Waiver Logic
# 布尔检查 + 豁免逻辑
# 检查所有时钟，但允许特定时钟不传播

description: Confirm all clocks propegated during STA.

requirements:
  value: N/A                        # 布尔检查
  pattern_items: []                 # 空列表

input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\clocks.rpt.gz

waivers:
  value: 1                          # 豁免数量（必须 > 0）
  waive_items:                      # 允许不传播的时钟
    - IO_ASYNC_CLOCK
```

**检查逻辑**:
1. **所有时钟**：
   - 在 **waive_items** 中 + 未传播 → INFO + `[WAIVER]`（已豁免）
   - 不在 **waive_items** 中 + 未传播 → FAIL（真正的失败）
   - 已传播 → INFO（正常）

2. **waive_items** 未使用：
   - 时钟已传播 → WARN + `[WAIVER]`（豁免未使用）
   - 时钟不存在 → WARN + `[WAIVER]`（豁免未使用）

**预期输出 (FAIL - 有非豁免的未传播时钟)**:
```
FAIL:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-ERROR01: Clock not propagated:
  Severity: Fail Occurrence: 1
  - PHASE_ALIGN_CLOCK

IMP-10-0-0-05-INFO01: Clock not propagated but waived:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK
```

**Report 文件详细内容**:
```
Fail Occurrence: 1
1: Fail: PHASE_ALIGN_CLOCK. In line 16, C:\...\clocks.rpt.gz: Clock not propagated (no waiver)

Info Occurrence: 2
1: Info: SYSTEM_CLOCK. In line 17, C:\...\clocks.rpt.gz: Clock propagated
2: Info: IO_ASYNC_CLOCK. In line 15, C:\...\clocks.rpt.gz: Clock not propagated (waived)[WAIVER]
```

**预期输出 (PASS - 所有时钟传播或已豁免)**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-INFO01: All clocks propagated or waived:
  Severity: Info Occurrence: 3
  - SYSTEM_CLOCK
  - MAIN_CLOCK
  - IO_ASYNC_CLOCK (waived)
```

**预期输出 (PASS with WARNING - 豁免未使用)**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-WARN01: Waiver not used:
  Severity: Warn Occurrence: 1
  - IO_ASYNC_CLOCK

IMP-10-0-0-05-INFO01: All clocks propagated or waived (with warnings):
  Severity: Info Occurrence: 2
  - SYSTEM_CLOCK
  - MAIN_CLOCK
```

---

## 🔍 Type 自动检测逻辑

脚本会根据配置文件自动检测类型：

```python
def detect_checker_type(self) -> int:
    """
    自动检测 checker 类型
    
    Type 1: requirements.value=N/A AND waivers.value=N/A/0
    Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    Type 4: requirements.value=N/A AND waivers.value>0
    """
```

| 条件 | requirements.value | pattern_items | waivers.value | 检测类型 |
|------|-------------------|---------------|---------------|----------|
| Type 1 | N/A | 空 | N/A 或 0 | Boolean (无豁免或强制PASS) |
| Type 2 | > 0 | 非空 | N/A 或 0 | Value (无豁免或强制PASS) |
| Type 3 | > 0 | 非空 | > 0 | Value + Waiver |
| Type 4 | N/A | 空 | > 0 | Boolean + Waiver |

---

## 📝 常见问题 (FAQ)

### Q1: pattern_items 和 waive_items 的区别？
**A**: 
- **pattern_items** (仅 Type 2/3): 需要检查的时钟列表，期望这些时钟都已传播
- **waive_items** (Type 3/4): 豁免列表，允许这些时钟不传播

### Q2: Type 3 中 pattern_items 和 waive_items 可以重叠吗？
**A**: 可以！这是设计用途：
- pattern_items 定义了需要检查的时钟
- waive_items 从中豁免某些时钟
- 重叠部分表示"期望传播但允许豁免"

示例：
```yaml
pattern_items:
  - IO_ASYNC_CLOCK    # 期望传播
  - SYSTEM_CLOCK      # 期望传播
waive_items:
  - IO_ASYNC_CLOCK    # 但允许 IO_ASYNC_CLOCK 不传播
```
结果：SYSTEM_CLOCK 必须传播，IO_ASYNC_CLOCK 可以不传播

### Q3: waivers.value = 0 的用途是什么？
**A**: 强制PASS模式，用于：
- **调试阶段**: 暂时忽略所有失败，继续测试流程
- **过渡期**: 已知问题但暂时无法修复
- **分析模式**: 收集所有问题但不阻塞流程

### Q4: 如何选择使用哪种 Type？
**A**:
- **Type 1**: 最简单，适用于"所有时钟都必须传播"的场景
- **Type 2**: 只关心特定时钟列表
- **Type 3**: 需要检查特定时钟，但允许部分豁免
- **Type 4**: 检查所有时钟，但允许部分豁免

### Q5: 报告文件支持 gzip 压缩吗？
**A**: 是的！脚本自动检测并支持：
- `.rpt.gz` (gzip 压缩)
- `.rpt` (普通文本)

### Q6: 时钟名称支持通配符吗？
**A**: 不支持。必须精确匹配完整的时钟名称。

### Q7: 如果报告文件不存在会怎样？
**A**: 脚本会抛出 `ConfigurationError` 异常并停止执行。

---

## 🛠️ 使用指南

### 1️⃣ 准备报告文件
确保 Tempus 生成了 `clocks.rpt` 或 `clocks.rpt.gz` 文件：
```tcl
# Tempus 命令
report_clocks -file clocks.rpt
```

### 2️⃣ 编辑配置文件
根据需求选择合适的 Type，编辑 `IMP-10-0-0-05.yaml`：
```yaml
description: Confirm all clocks propegated during STA.
requirements:
  value: N/A                        # 或具体数值
  pattern_items: []                 # 或时钟列表
input_files: 
  - /path/to/clocks.rpt.gz
waivers:
  value: N/A                        # 或 0 或具体数值
  waive_items: []                   # 或时钟列表
```

### 3️⃣ 运行检查
```bash
python IMP-10-0-0-05.py
```

### 4️⃣ 查看结果
- **日志文件**: `Check_modules/10.0_STA_DCD_CHECK/logs/IMP-10-0-0-05.log`
- **报告文件**: `Check_modules/10.0_STA_DCD_CHECK/reports/IMP-10-0-0-05.rpt`

---

## 📊 输出格式说明

### 日志文件 (.log)
**PASS 示例**:
```
PASS:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-INFO01: All clocks propagated:
  Severity: Info Occurrence: 3
  - SYSTEM_CLOCK
  - MAIN_CLOCK
  - AUX_CLOCK
```

**FAIL 示例**:
```
FAIL:IMP-10-0-0-05:Confirm all clocks propagated during STA.
IMP-10-0-0-05-ERROR01: Clock not propagated:
  Severity: Fail Occurrence: 2
  - IO_ASYNC_CLOCK
  - PHASE_ALIGN_CLOCK
```

### 报告文件 (.rpt)
**详细信息**:
```
FAIL:IMP-10-0-0-05:Confirm all clocks propagated during STA.
Fail Occurrence: 2
1: Fail: IO_ASYNC_CLOCK. In line 15, C:\...\clocks.rpt.gz: Clock not propagated
2: Fail: PHASE_ALIGN_CLOCK. In line 16, C:\...\clocks.rpt.gz: Clock not propagated

Info Occurrence: 1
1: Info: SYSTEM_CLOCK. In line 17, C:\...\clocks.rpt.gz: Clock propagated
```

---

## 🚀 版本历史

### v1.0 (2025-12-02)
- ✅ 初始版本发布
- ✅ 支持 4 种 Checker 类型自动检测
- ✅ 解析 Tempus clocks.rpt.gz 报告
- ✅ 支持 gzip 压缩文件
- ✅ 实现 Waiver 标签规则
- ✅ Type 3/4 自定义分组描述
- ✅ ConfigurationError 异常处理

---

## 📞 技术支持

如有问题或建议，请联系开发团队。

**Author**: yyin  
**Date**: 2025-12-02
