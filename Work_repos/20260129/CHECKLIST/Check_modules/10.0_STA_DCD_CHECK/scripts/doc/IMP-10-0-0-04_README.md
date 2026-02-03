# IMP-10-0-0-04 配置说明与示例

## 检查项目
**Confirm the SDC has no ideal clock networks**

确认 SDC (Synopsys Design Constraints) 中没有理想时钟网络。理想时钟网络是指时钟波形被设置为理想状态（无延迟、无偏差），这在时序分析中可能导致不准确的结果。

---

## 功能特性

### ✅ 自动检测四种 Checker 类型
脚本会根据 YAML 配置自动识别使用哪种类型：
- **Type 1**: 布尔检查（无豁免）
- **Type 2**: 数值比较（无豁免）
- **Type 3**: 数值比较 + 豁免逻辑
- **Type 4**: 布尔检查 + 豁免逻辑

### ✅ 解析 check_timing 报告
从 `check_timing.rpt` 提取两种信息：
1. **Summary 部分**: 理想时钟计数
   ```
   ideal_clock_waveform Clock waveform is ideal 1
   ```
2. **Detail 部分**: 具体时钟名称列表
   ```
   TIMING CHECK IDEAL CLOCKS
   ---------------------------
   IO_ASYNC_CLOCK
   ```

### ✅ 双重验证机制
- **Primary Source**: Detail 部分的时钟名称列表（更可靠）
- **Validation**: Summary 计数与 Detail 列表长度一致性检查
- 如果不一致，发出警告但以 Detail 为准

### ✅ 精确匹配模式
- **pattern_items**: 期望的理想时钟名称（精确匹配）
- **waive_items**: 豁免的理想时钟名称（精确匹配）
- 不支持通配符，必须完全匹配时钟名称

### ✅ Waiver标签规则 (2025-12-02更新)
根据 `waivers.value` 的不同值，使用不同的标签：

**当 waivers.value > 0 时（Type 3/4）**:
- 所有与 waive_items 相关的输出统一使用 `[WAIVER]` 后缀
- 已豁免的违规 → INFO + `[WAIVER]`
- 未使用的豁免 → WARN + `[WAIVER]`

**当 waivers.value = 0 时（Type 1/2）**:
- 检查发现的 FAIL/WARN → INFO + `[WAIVED_AS_INFO]`（实际发现的问题被强制豁免）
- waive_items 配置项 → INFO + `[WAIVED_INFO]`（配置的豁免项）
- 强制 PASS（所有失败都被豁免）

**当 waivers.value = N/A 时（Type 1/2）**:
- 正常模式，根据实际检查结果判定 PASS/FAIL

---

## 📋 配置文件示例

### 🔹 Type 1: 布尔检查

**用途**: 简单验证设计中不应存在任何理想时钟网络

#### 方案 A: 正常模式 (waivers.value = N/A)

**配置文件**: `IMP-10-0-0-04.type1.yaml`

```yaml
# Type 1: Boolean Check (Normal Mode)
# 简单的布尔检查：设计中不应有任何理想时钟
# 任何理想时钟的存在都视为 FAIL

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: N/A
  pattern_items: []

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: N/A
  waive_items: []
```

**检查逻辑**:
- ✅ 无理想时钟 → PASS
- ❌ 发现任何理想时钟 → FAIL

**预期输出 (PASS - 无理想时钟)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO01: No ideal clock networks found:
  Severity: Info Occurrence: 1
  - No ideal clock networks found
```

**预期输出 (FAIL - 发现理想时钟)**:
```
FAIL:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-ERROR01: Ideal clock network check:
  Severity: Fail Occurrence: 1
  - IO_ASYNC_CLOCK
```

#### 方案 B: 强制PASS模式 (waivers.value = 0)

**配置文件**: `IMP-10-0-0-04.type1_waiver0.yaml`

```yaml
# Type 1: Boolean Check (Forced PASS Mode)
# 强制PASS模式：所有理想时钟都转为 INFO，后缀 [WAIVED_AS_INFO]
# 用于调试或过渡期

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: N/A
  pattern_items: []

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 0                          # 强制PASS
  waive_items:
    - debug_item_1
    - debug_item_2
```

**检查逻辑**:
- 所有理想时钟 → INFO + `[WAIVED_AS_INFO]`
- waive_items → INFO + `[WAIVED_INFO]`
- 强制 PASS

**预期输出 (强制PASS - 有理想时钟)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO01: Ideal clock network check:
  Severity: Info Occurrence: 3
  - IO_ASYNC_CLOCK (理想时钟被强制豁免)
  - debug_item_1 (配置的豁免项)
  - debug_item_2 (配置的豁免项)

# Report 文件中的详细内容:
Info Occurrence: 3
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Ideal clock network detected[WAIVED_AS_INFO]
2: Info: debug_item_1. In line 0, N/A: Waive item[WAIVED_INFO]
3: Info: debug_item_2. In line 0, N/A: Waive item[WAIVED_INFO]
```

---

### 🔹 Type 2: 数值比较

**用途**: 期望特定数量的理想时钟（用于验证已知的理想时钟配置）

#### 方案 A: 正常模式 (waivers.value = N/A)

**配置文件**: `IMP-10-0-0-04.type2.yaml`

```yaml
# Type 2: Value Comparison (Normal Mode)
# 数值比较：期望找到特定的理想时钟
# requirements.value 建议等于 pattern_items 的数量（也可以是 N/A）

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: 2                          # 期望 2 个理想时钟（建议与 pattern_items 数量一致）
  pattern_items:                    # 期望的理想时钟名称（精确匹配）
    - IO_ASYNC_CLOCK
    - TEST_CLOCK

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: N/A
  waive_items: []
```

**检查逻辑**:
- 精确匹配 `pattern_items` 中的时钟名称
- **Matched** → INFO（期望的理想时钟）
- **Missing** → FAIL（期望但未找到）
- **Extra** → FAIL（未期望但发现）
- **PASS**: 所有 pattern_items 都找到，且无额外时钟
- **FAIL**: 有 missing 或 extra 时钟

**预期输出 (PASS - 完全匹配)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO01: Ideal clock pattern matching:
  Severity: Info Occurrence: 2
  - IO_ASYNC_CLOCK
  - TEST_CLOCK

# Report 文件中的详细内容:
Info Occurrence: 2
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Expected ideal clock found
2: Info: TEST_CLOCK. In line 42, ...\check_timing.rpt: Expected ideal clock found
```

**预期输出 (FAIL - 缺少期望时钟)**:
```
FAIL:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO01: Ideal clock pattern matching:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK

IMP-10-0-0-04-ERROR01: Ideal clock pattern matching:
  Severity: Fail Occurrence: 1
  - TEST_CLOCK

# Report 文件中的详细内容:
Fail Occurrence: 1
1: Fail: TEST_CLOCK. In line 0, ...\check_timing.rpt: Expected ideal clock not found

Info Occurrence: 1
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Expected ideal clock found
```

#### 方案 B: 强制PASS模式 (waivers.value = 0)

**配置文件**: `IMP-10-0-0-04.type2_waiver0.yaml`

```yaml
# Type 2: Value Comparison (Forced PASS Mode)
# 强制PASS模式：所有匹配/缺失/额外时钟都转为 INFO
# 所有 FAIL/WARN → INFO + [WAIVED_AS_INFO]
# waive_items → INFO + [WAIVED_INFO]

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: 0                          # 可以是任意值或 N/A
  pattern_items:
    - IO_ASYNC_CLOCK
    - TEST_CLOCK

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 0                          # 强制PASS
  waive_items:
    - debug_waive_item
```

**检查逻辑**:
- 所有 matched/missing/extra → INFO + `[WAIVED_AS_INFO]`
- waive_items → INFO + `[WAIVED_INFO]`
- 强制 PASS

**预期输出 (强制PASS - 有缺失时钟)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO01: Ideal clock pattern matching:
  Severity: Info Occurrence: 3
  - IO_ASYNC_CLOCK
  - TEST_CLOCK (缺失但被豁免)
  - debug_waive_item (配置的豁免项)

# Report 文件中的详细内容:
Info Occurrence: 3
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Expected ideal clock found[WAIVED_AS_INFO]
2: Info: TEST_CLOCK. In line 0, ...\check_timing.rpt: Expected ideal clock not found[WAIVED_AS_INFO]
3: Info: debug_waive_item. In line 0, N/A: Waive item[WAIVED_INFO]
```

---

### 🔹 Type 3: 数值比较 + 豁免逻辑

**用途**: 验证期望的理想时钟，同时允许豁免某些已批准的理想时钟

**配置文件**: `IMP-10-0-0-04.type3.yaml`

```yaml
# Type 3: Value Comparison WITH Waiver Logic
# 数值比较 + 豁免：期望的理想时钟 + 批准的豁免项
# requirements.value 建议等于 pattern_items 的数量（也可以是 N/A）
# waivers.value 必须 > 0，建议等于 waive_items 的数量

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: 1                          # 期望 1 个理想时钟（建议与 pattern_items 数量一致）
  pattern_items:                    # 期望的理想时钟名称
    - IO_ASYNC_CLOCK

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 2                          # 允许 2 个豁免（必须 > 0，建议与 waive_items 数量一致）
  waive_items:                      # 豁免的理想时钟名称
    - name: TEST_CLOCK
      reason: "Test mode clock - approved by design team (Ticket#12345)"
    - name: DEBUG_CLOCK
      reason: "Debug infrastructure - waived for RTL verification"
```

**检查逻辑**:
- **Expected Match** → INFO（期望的理想时钟）
- **Waived Match** → INFO + `[WAIVER]`（豁免的理想时钟）
- **Missing Expected** → FAIL（期望但未找到）
- **Unexpected** → FAIL（既不在 pattern 也不在 waive）
- **Unused Waiver** → WARN + `[WAIVER]`（配置的豁免未使用）
- **PASS**: 无 FAIL
- **FAIL**: 有 missing 或 unexpected

**预期输出 (PASS - 全部匹配)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO02: Expected ideal clocks found:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK

IMP-10-0-0-04-INFO03: Ideal clocks waived:
  Severity: Info Occurrence: 2
  - TEST_CLOCK
  - DEBUG_CLOCK

# Report 文件中的详细内容:
Info Occurrence: 3
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Expected ideal clock found
2: Info: TEST_CLOCK. In line 42, ...\check_timing.rpt: Ideal clock waived[WAIVER]
3: Info: DEBUG_CLOCK. In line 46, ...\check_timing.rpt: Ideal clock waived[WAIVER]
```

**预期输出 (FAIL - 未期望的时钟)**:
```
FAIL:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO02: Expected ideal clocks found:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK

IMP-10-0-0-04-ERROR02: Unexpected ideal clocks:
  Severity: Fail Occurrence: 1
  - SCAN_CLOCK

# Report 文件中的详细内容:
Fail Occurrence: 1
1: Fail: SCAN_CLOCK. In line 50, ...\check_timing.rpt: Unexpected ideal clock

Info Occurrence: 1
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Expected ideal clock found
```

**预期输出 (PASS with WARN - 豁免未使用)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO02: Expected ideal clocks found:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK

IMP-10-0-0-04-WARN01: Configured waivers not used:
  Severity: Warn Occurrence: 1
  - TEST_CLOCK

# Report 文件中的详细内容:
Warn Occurrence: 1
1: Warn: TEST_CLOCK: Waiver not used[WAIVER]

Info Occurrence: 1
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Expected ideal clock found
```

---

### 🔹 Type 4: 布尔检查 + 豁免逻辑

**用途**: 检查理想时钟存在性，允许豁免某些已批准的理想时钟

**配置文件**: `IMP-10-0-0-04.type4.yaml`

```yaml
# Type 4: Boolean WITH Waiver Logic
# 布尔检查 + 豁免：不应有理想时钟，但允许豁免某些特定时钟
# waivers.value 必须 > 0，建议等于 waive_items 的数量

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: N/A
  pattern_items: []

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 1                          # 允许 1 个豁免（必须 > 0，建议与 waive_items 数量一致）
  waive_items:                      # 豁免的理想时钟名称
    - name: IO_ASYNC_CLOCK
      reason: "Asynchronous clock domain - approved waiver (Ticket#9876)"
```

**检查逻辑**:
- 无理想时钟 → INFO
- **Waived Clock** → INFO + `[WAIVER]`
- **Non-Waived Clock** → FAIL
- **Unused Waiver** → WARN + `[WAIVER]`
- **PASS**: 所有理想时钟都被豁免（或无理想时钟）
- **FAIL**: 存在未豁免的理想时钟

**预期输出 (PASS - 无理想时钟)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO01: No ideal clocks found:
  Severity: Info Occurrence: 0
  (no items)

IMP-10-0-0-04-WARN01: Configured waivers not used:
  Severity: Warn Occurrence: 1
  - IO_ASYNC_CLOCK

# Report 文件中的详细内容:
Warn Occurrence: 1
1: Warn: IO_ASYNC_CLOCK: Waiver not used[WAIVER]

Info Occurrence: 1
1: Info: No ideal clock networks found. In line 0, ...\check_timing.rpt: Check passed
```

**预期输出 (PASS - 理想时钟已豁免)**:
```
PASS:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO03: Ideal clocks waived:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK

# Report 文件中的详细内容:
Info Occurrence: 1
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Ideal clock waived[WAIVER]
```

**预期输出 (FAIL - 未豁免的理想时钟)**:
```
FAIL:IMP-10-0-0-04:Confirm the SDC has no ideal clock networks
IMP-10-0-0-04-INFO03: Ideal clocks waived:
  Severity: Info Occurrence: 1
  - IO_ASYNC_CLOCK

IMP-10-0-0-04-ERROR01: Ideal clocks not waived:
  Severity: Fail Occurrence: 1
  - TEST_CLOCK

# Report 文件中的详细内容:
Fail Occurrence: 1
1: Fail: TEST_CLOCK. In line 42, ...\check_timing.rpt: Ideal clock not waived

Info Occurrence: 1
1: Info: IO_ASYNC_CLOCK. In line 38, ...\check_timing.rpt: Ideal clock waived[WAIVER]
```

---

## 🔍 技术细节

### 报告解析逻辑

#### Summary 部分解析
```
TIMING CHECK SUMMARY
--------------------
ideal_clock_waveform Clock waveform is ideal 1
```
- 使用正则表达式: `r'ideal_clock_waveform\s+.*?\s+(\d+)\s*$'`
- 提取数字 `1` 作为理想时钟计数

#### Detail 部分解析
```
TIMING CHECK IDEAL CLOCKS
---------------------------
IO_ASYNC_CLOCK
```
- 识别 `TIMING CHECK IDEAL CLOCKS` 标题
- 跳过分隔线 (`---`)
- 提取第一列作为时钟名称
- 记录行号用于详细输出

### 验证机制

**Summary vs Detail 一致性**:
```python
if summary_count != len(ideal_clocks):
    print(f"Warning: Summary count ({summary_count}) doesn't match detail list length ({len(ideal_clocks)}). Using detail list.")
```
- Detail 列表是主要数据源（更可靠）
- Summary 计数用于验证
- 不一致时发出警告但继续执行

### 精确匹配策略

**不支持通配符**:
- ❌ `"*ASYNC*"` - 不支持
- ❌ `"IO_.*_CLOCK"` - 不支持
- ✅ `"IO_ASYNC_CLOCK"` - 精确匹配

**匹配逻辑**:
```python
found_clocks = {clock['name'] for clock in self._ideal_clocks}
expected_clocks = set(pattern_items)

matched = expected_clocks & found_clocks  # 交集
missing = expected_clocks - found_clocks  # 期望但未找到
extra = found_clocks - expected_clocks    # 未期望但找到
```

---

## ⚠️ 重要注意事项

### 配置规则

1. **Type 1/2**: 
   - `requirements.value` 可以是 `N/A`、`0` 或任意正数
   - 建议：Type 2 的 `requirements.value` 等于 `len(pattern_items)`
   
2. **Type 3/4**: 
   - `waivers.value` 必须 `> 0`（这是 Type 3/4 的定义条件）
   - 建议：`waivers.value` 等于 `len(waive_items)`
   
3. **Type 1/2 的 waiver=0 模式**:
   - 设置 `waivers.value = 0` 启用强制PASS模式
   - 所有 FAIL → INFO + `[WAIVED_AS_INFO]`
   - waive_items → INFO + `[WAIVED_INFO]`
   
4. **不一致时的行为**:
   - 脚本会发出警告但继续执行
   - 建议修复配置以保证一致性

### Waiver标签含义

**`[WAIVER]`** (Type 3/4，waivers.value > 0):
- 正常豁免模式
- 用于已批准的、有计划的豁免项
- 已豁免违规 → INFO + `[WAIVER]`
- 未使用豁免 → WARN + `[WAIVER]`

**`[WAIVED_AS_INFO]`** (Type 1/2，waivers.value = 0):
- 强制豁免模式
- 表示实际检测到的违规项被强制转为 INFO
- 用于调试模式或过渡期
- 便于识别实际存在的问题

**`[WAIVED_INFO]`** (Type 1/2，waivers.value = 0):
- 强制豁免模式
- 表示 YAML 中预配置的 waive_items
- 与实际检查结果无关，仅用于记录配置

### 文件路径要求

- 必须使用绝对路径
- 支持 Windows 路径格式 (`C:\Users\...`)
- 文件必须存在，否则抛出 `ConfigurationError`

---

## 📁 配置文件示例（完整版）

以下是四种类型的完整配置文件，可直接复制使用。

### Type 1 - 正常模式

**文件名**: `IMP-10-0-0-04.type1.yaml`

```yaml
# Type 1: Boolean Check (Normal Mode)
# 简单的布尔检查：设计中不应有任何理想时钟
# 任何理想时钟的存在都视为 FAIL

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: N/A
  pattern_items: []

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: N/A
  waive_items: []
```

### Type 1 - 强制PASS模式

**文件名**: `IMP-10-0-0-04.type1_waiver0.yaml`

```yaml
# Type 1: Boolean Check (Forced PASS Mode)
# 强制PASS模式：所有理想时钟都转为 INFO，后缀 [WAIVED_AS_INFO]
# 用于调试或过渡期

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: N/A
  pattern_items: []

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 0                          # 强制PASS
  waive_items:
    - debug_item_1
    - debug_item_2
```

### Type 2 - 正常模式

**文件名**: `IMP-10-0-0-04.type2.yaml`

```yaml
# Type 2: Value Comparison (Normal Mode)
# 数值比较：期望找到特定的理想时钟
# requirements.value 建议等于 pattern_items 的数量（也可以是 N/A）

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: 2                          # 期望 2 个理想时钟（建议与 pattern_items 数量一致）
  pattern_items:                    # 期望的理想时钟名称（精确匹配）
    - IO_ASYNC_CLOCK
    - TEST_CLOCK

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: N/A
  waive_items: []
```

### Type 2 - 强制PASS模式

**文件名**: `IMP-10-0-0-04.type2_waiver0.yaml`

```yaml
# Type 2: Value Comparison (Forced PASS Mode)
# 强制PASS模式：所有匹配/缺失/额外时钟都转为 INFO
# 所有 FAIL/WARN → INFO + [WAIVED_AS_INFO]
# waive_items → INFO + [WAIVED_INFO]

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: 0                          # 可以是任意值或 N/A
  pattern_items:
    - IO_ASYNC_CLOCK
    - TEST_CLOCK

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 0                          # 强制PASS
  waive_items:
    - debug_waive_item
```

### Type 3 - 数值比较 + 豁免

**文件名**: `IMP-10-0-0-04.type3.yaml`

```yaml
# Type 3: Value Comparison WITH Waiver Logic
# 数值比较 + 豁免：期望的理想时钟 + 批准的豁免项
# requirements.value 建议等于 pattern_items 的数量（也可以是 N/A）
# waivers.value 必须 > 0，建议等于 waive_items 的数量

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: 1                          # 期望 1 个理想时钟（建议与 pattern_items 数量一致）
  pattern_items:                    # 期望的理想时钟名称
    - IO_ASYNC_CLOCK

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 2                          # 允许 2 个豁免（必须 > 0，建议与 waive_items 数量一致）
  waive_items:                      # 豁免的理想时钟名称
    - name: TEST_CLOCK
      reason: "Test mode clock - approved by design team (Ticket#12345)"
    - name: DEBUG_CLOCK
      reason: "Debug infrastructure - waived for RTL verification"
```

### Type 4 - 布尔检查 + 豁免

**文件名**: `IMP-10-0-0-04.type4.yaml`

```yaml
# Type 4: Boolean WITH Waiver Logic
# 布尔检查 + 豁免：不应有理想时钟，但允许豁免某些特定时钟
# waivers.value 必须 > 0，建议等于 waive_items 的数量

description: Confirm the SDC has no ideal clock networks.

requirements:
  value: N/A
  pattern_items: []

input_files: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\check_timing.rpt

waivers:
  value: 1                          # 允许 1 个豁免（必须 > 0，建议与 waive_items 数量一致）
  waive_items:                      # 豁免的理想时钟名称
    - name: IO_ASYNC_CLOCK
      reason: "Asynchronous clock domain - approved waiver (Ticket#9876)"
```

---

## 🚀 执行示例

### 运行单个 Checker
```powershell
cd Work
python ..\Check_modules\common\check_flowtool.py `
    -root .. `
    -stage Initial `
    -check_module 10.0_STA_DCD_CHECK `
    -check_item IMP-10-0-0-04
```

### 测试不同类型
```powershell
# 测试 Type 1 (正常模式)
cp ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.type1.yaml `
   ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.yaml
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial `
    -check_module 10.0_STA_DCD_CHECK -check_item IMP-10-0-0-04

# 测试 Type 1 (强制PASS模式)
cp ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.type1_waiver0.yaml `
   ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.yaml
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial `
    -check_module 10.0_STA_DCD_CHECK -check_item IMP-10-0-0-04

# 测试 Type 2 (正常模式)
cp ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.type2.yaml `
   ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.yaml
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial `
    -check_module 10.0_STA_DCD_CHECK -check_item IMP-10-0-0-04

# 测试 Type 3 (数值比较 + 豁免)
cp ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.type3.yaml `
   ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.yaml
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial `
    -check_module 10.0_STA_DCD_CHECK -check_item IMP-10-0-0-04

# 测试 Type 4 (布尔检查 + 豁免)
cp ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.type4.yaml `
   ..\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-04.yaml
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial `
    -check_module 10.0_STA_DCD_CHECK -check_item IMP-10-0-0-04
```

### 查看结果
**日志文件**:
```
Check_modules/10.0_STA_DCD_CHECK/logs/IMP-10-0-0-04.log
```

**报告文件**:
```
Check_modules/10.0_STA_DCD_CHECK/reports/IMP-10-0-0-04.rpt
```

---

## 📚 相关文档

- **BaseChecker 框架**: `Check_modules/common/base_checker.py`
- **输出格式说明**: `Check_modules/common/output_formatter.py`
- **项目整体文档**: `Development_prompt.md`
- **框架说明**: `README.md`

---

## 📞 支持与反馈

如有问题或建议，请联系开发团队或提交 Issue。
