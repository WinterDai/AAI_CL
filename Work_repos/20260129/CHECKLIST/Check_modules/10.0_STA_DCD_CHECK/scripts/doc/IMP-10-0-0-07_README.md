# IMP-10-0-0-07 配置说明与示例

## 检查项目
**Confirm the OCV setting is correct**

确认静态时序分析（STA）中的 OCV（On-Chip Variation）设置是否正确配置，符合最新的 foundry 建议或补充文档。OCV 分析对于先进工艺节点（如 3nm）至关重要，能够准确建模片上变异（die-to-die、within-die）的影响。

---

## 功能特性

### ✅ 自动检测四种 Checker 类型
脚本会根据 YAML 配置自动识别使用哪种类型：
- **Type 1**: 布尔检查（所有 OCV 指标）- 无豁免
- **Type 2**: 模式匹配（特定 OCV 设置）- 无豁免  
- **Type 3**: 模式匹配 + 豁免逻辑
- **Type 4**: 布尔检查 + 豁免逻辑

### ✅ 解析 Tempus STA 日志
从 `sta_post_syn.log` 提取 6 个关键 OCV 指标：

**检查指标**:
1. **Analysis Mode: MMMC OCV (SOCV)** - MMMC OCV 模式确认
2. **timing_enable_spatial_derate_mode to 1** - Spatial derate 启用
3. **timing_spatial_derate_distance_mode to chip_size** - Distance mode 设置
4. **SOCV RC Variation Factors** - SOCV RC 变异因子（Early/Late）
5. **Wire Derate SOCV Factors** - 线路 derate SOCV 因子
6. **SOCV Files** - SOCV 文件加载（文件数量和类型）

**日志格式示例**:
```
#################################################################################
# Analysis Mode: MMMC OCV (SOCV)
#################################################################################
[INFO] setting timing_enable_spatial_derate_mode to 1
[INFO] setting timing_spatial_derate_distance_mode to chip_size

SOCV RC Variation Factors
+----------------------------------------------------------+-------+-------+
| Analysis View                                            | Early | Late  |
+----------------------------------------------------------+-------+-------+
| func_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold | 0.100 | 0.100 |
+----------------------------------------------------------+-------+-------+

### WIRE DERATE ###
+-------------+--------------+
| User Derate | SOCV Factors |
+-------------+--------------+
|             |      X       |
+-------------+--------------+

### OCV FILES ###
+-------------+-------------+
|    AOCV     | Spatial-OCV |
+-------------+-------------+
|             |      X      |
+-------------+-------------+

SOCV Files:
   - /process/tsmcN3/.../file1.socv
   - /process/tsmcN3/.../file2.socv
```

### ✅ 灵活的模式匹配 (Type 2/3)

**大小写不敏感匹配**:
- Pattern: `"WIRE DERATE"` 匹配 log 中的 `### wire derate ###`
- Pattern: `"Analysis Mode: MMMC OCV"` 匹配 `# analysis mode: mmmc ocv (socv)`

**符号自动转换**:
- Pattern: `"timing_enable_spatial_derate_mode = 1"` 自动匹配 `to 1`
- Pattern: `"timing_enable_spatial_derate_mode to 1"` 自动匹配 `= 1`

**特殊语义模式**:
- `"SOCV Files Used"`: 检查 SOCV Files 部分是否列出了 `.socv` 文件
  - 成功: 返回 "SOCV Files Used (N files)"
  - 失败: Pattern not found

### ✅ PASS 状态区分 (Type 3/4)

**当 waivers.value > 0 时（Type 3/4）**:
- **PASS 状态标识**:
  - 真正的 PASS（所有检查都通过） → `PASS:IMP-10-0-0-07:...`
  - 因 waive 而 PASS（有错误但被豁免） → `PASS(Waive):IMP-10-0-0-07:...`

### ✅ 日志分组规则

**Type 1 (布尔检查 - 无豁免)**:
- **waivers.value = N/A** (正常模式):
  - ERROR01: 缺失的 OCV 指标
  - INFO01: 找到的 OCV 指标
  
- **waivers.value = 0** (强制PASS模式):
  - INFO01: 所有检查项（含强制豁免标签）
  - 所有 FAIL → INFO + `[WAIVED_AS_INFO]`

**Type 2 (模式匹配 - 无豁免)**:
- ERROR01: 未找到的 pattern
- INFO01: 找到的 pattern

**Type 3 (模式匹配 + 豁免)**:
- ERROR01: 未找到的 pattern（未豁免）
- INFO01: 真正通过的 pattern → "OCV setting is correct"
- INFO02: 因 waive 而通过的 pattern → "OCV setting verified via waiver"
- WARN01: 未使用的豁免 → "Waiver not used"

**Type 4 (布尔检查 + 豁免)**:
- ERROR01: 缺失的 OCV 指标
- INFO01: 找到的 OCV 指标 → "OCV setting found"
- WARN01: 未使用的豁免 → "Waiver not used"

### ✅ 自定义输出格式

**Log 输出格式 (Type 1 - 所有指标找到)**:
```
PASS:IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-INFO01: OCV setting verified (6/6 indicators found):
  Severity: Info Occurrence: 6
  - Analysis Mode: MMMC OCV (SOCV)
  - timing_enable_spatial_derate_mode: 1
  - timing_spatial_derate_distance_mode: chip_size
  - SOCV RC Variation: Early 0.100, Late 0.100
  - Wire derate: SOCV factors enabled
  - SOCV files: Spatial-OCV (16 files)
```

**Report 输出格式 (Type 1)**:
```
PASS:IMP-10-0-0-07:Confirm the OCV setting is correct?
Info Occurrence: 6
1: Info: Analysis Mode: MMMC OCV. In line 61, sta_post_syn.log: OCV setting found
2: Info: timing_enable_spatial_derate_mode to 1. In line 71, sta_post_syn.log: OCV setting found
3: Info: timing_spatial_derate_distance_mode to chip_size. In line 72, sta_post_syn.log: OCV setting found
4: Info: SOCV RC Variation Factors. In line 82, sta_post_syn.log: OCV setting found
5: Info: Wire Derate SOCV Factors. In line 89, sta_post_syn.log: OCV setting found
6: Info: SOCV Files. In line 103, sta_post_syn.log: OCV setting found
```

**Log 输出格式 (Type 2 - 部分 pattern 找到)**:
```
FAIL:IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-ERROR01: OCV setting isn't correct (pattern not found):
  Severity: Fail Occurrence: 2
  - WIRE DERATE
  - SOCV Files Used
IMP-10-0-0-07-INFO01: OCV setting partially correct (4/6 patterns found):
  Severity: Info Occurrence: 4
  - Analysis Mode: MMMC OCV
  - timing_enable_spatial_derate_mode = 1
  - timing_spatial_derate_distance_mode to chip_size
  - SOCV RC Variation Factors
```

**Log 输出格式 (Type 3 - PASS(Waive))**:
```
PASS(Waive):IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-WARN01: Waiver not used:
  Severity: Warn Occurrence: 1
  - Extra Pattern
IMP-10-0-0-07-INFO01: OCV setting is correct (5/6 patterns found):
  Severity: Info Occurrence: 5
  - Analysis Mode: MMMC OCV
  - timing_enable_spatial_derate_mode = 1
  - timing_spatial_derate_distance_mode to chip_size
  - SOCV RC Variation Factors
  - WIRE DERATE
IMP-10-0-0-07-INFO02: OCV setting verified via waiver (1 pattern waived):
  Severity: Info Occurrence: 1
  - AOCV Files Used [WAIVED: missing]
```

**Log 输出格式 (Type 4 - 未使用的 Waiver)**:
```
PASS(Waive):IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-INFO01: OCV setting is correct (6/6 indicators found):
  Severity: Info Occurrence: 6
  - Analysis Mode: MMMC OCV (SOCV)
  - timing_enable_spatial_derate_mode: 1
  - timing_spatial_derate_distance_mode: chip_size
  - SOCV RC Variation: Early 0.100, Late 0.100
  - Wire derate: SOCV factors enabled
  - SOCV files: Standard SOCV (16 files)
IMP-10-0-0-07-WARN01: Waiver not used (2 items):
  Severity: Warn Occurrence: 2
  - Some waived item
  - Another waived item
```

---

## 📋 配置文件示例

### 🔹 Type 1: 布尔检查（所有 OCV 指标）

**用途**: 验证所有 6 个 OCV 指标都已正确配置

#### 方案 A: 正常模式 (waivers.value = N/A)

```yaml
description: Confirm the OCV setting is correct (matches to latest foundary
  recommendation or addendum).
requirements:
  value: N/A
  pattern_items: []
input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
waivers:
  value: N/A
  waive_items: []
```

**检查逻辑**:
- ✅ 所有 6 个 OCV 指标都找到 → PASS
- ❌ 任何指标缺失 → FAIL

**预期输出 (PASS)**:
```
PASS:IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-INFO01: OCV setting verified (6/6 indicators found):
  - Analysis Mode: MMMC OCV (SOCV)
  - timing_enable_spatial_derate_mode: 1
  - timing_spatial_derate_distance_mode: chip_size
  - SOCV RC Variation: Early 0.100, Late 0.100
  - Wire derate: SOCV factors enabled
  - SOCV files: Spatial-OCV (16 files)
```

---

### 🔹 Type 2: 模式匹配（特定 OCV 设置）

**用途**: 验证特定的 OCV 配置项是否存在

```yaml
description: Confirm the OCV setting is correct (matches to latest foundary
  recommendation or addendum).
requirements:
  value: 6
  pattern_items:
    - "Analysis Mode: MMMC OCV"
    - "timing_enable_spatial_derate_mode = 1"
    - "timing_spatial_derate_distance_mode to chip_size"
    - "SOCV RC Variation Factors"
    - "WIRE DERATE"
    - "SOCV Files Used"
input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
waivers:
  value: N/A
  waive_items: []
```

**检查逻辑**:
- ✅ 所有 pattern_items 都匹配 → PASS
- ❌ 任何 pattern 未找到 → ERROR01

**模式匹配特性**:
- **大小写不敏感**: `"WIRE DERATE"` 匹配 `### wire derate ###`
- **符号自动转换**: `"= 1"` 自动匹配 `to 1`
- **特殊语义**: `"SOCV Files Used"` 检查是否真的使用了 SOCV 文件

**预期输出 (PASS)**:
```
PASS:IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-INFO01: OCV setting is correct (6/6 patterns found):
  - Analysis Mode: MMMC OCV
  - timing_enable_spatial_derate_mode = 1
  - timing_spatial_derate_distance_mode to chip_size
  - SOCV RC Variation Factors
  - WIRE DERATE
  - SOCV Files Used
```

---

### 🔹 Type 3: 模式匹配 + 豁免逻辑

**用途**: 验证特定 OCV 配置，支持对缺失项进行豁免

```yaml
description: Confirm the OCV setting is correct (matches to latest foundary
  recommendation or addendum).
requirements:
  value: 6
  pattern_items:
    - "Analysis Mode: MMMC OCV"
    - "timing_enable_spatial_derate_mode = 1"
    - "timing_spatial_derate_distance_mode to chip_size"
    - "SOCV RC Variation Factors"
    - "WIRE DERATE"
    - "AOCV Files Used"
input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
waivers:
  value: 2
  waive_items:
    - "AOCV Files Used"
    - "Extra Pattern"
```

**检查逻辑**:
- 在 waive_items 中的 pattern 缺失 → INFO02 + [WAIVED: missing]
- 不在 waive_items 中的 pattern 缺失 → ERROR01
- waive_items 未使用 → WARN01
- 有豁免项时显示 → `PASS(Waive)`

**预期输出**:
```
PASS(Waive):IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-WARN01: Waiver not used:
  Severity: Warn Occurrence: 1
  - Extra Pattern
IMP-10-0-0-07-INFO01: OCV setting is correct (5/6 patterns found):
  Severity: Info Occurrence: 5
  - Analysis Mode: MMMC OCV
  - timing_enable_spatial_derate_mode = 1
  - timing_spatial_derate_distance_mode to chip_size
  - SOCV RC Variation Factors
  - WIRE DERATE
IMP-10-0-0-07-INFO02: OCV setting verified via waiver (1 pattern waived):
  Severity: Info Occurrence: 1
  - AOCV Files Used [WAIVED: missing]
```

---

### 🔹 Type 4: 布尔检查 + 豁免逻辑

**用途**: 检查所有 OCV 指标，未使用的 waiver 显示为 WARN

```yaml
description: Confirm the OCV setting is correct (matches to latest foundary
  recommendation or addendum).
requirements:
  value: N/A
  pattern_items: []
input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
waivers:
  value: 2
  waive_items:
    - "Some waived item"
    - "Another waived item"
```

**检查逻辑**:
- 检查所有 6 个 OCV 指标
- waive_items 未用于豁免任何失败项 → WARN01
- 有 waiver 时显示 → `PASS(Waive)`

**预期输出**:
```
PASS(Waive):IMP-10-0-0-07:Confirm the OCV setting is correct?
IMP-10-0-0-07-INFO01: OCV setting is correct (6/6 indicators found):
  Severity: Info Occurrence: 6
  - Analysis Mode: MMMC OCV (SOCV)
  - timing_enable_spatial_derate_mode: 1
  - timing_spatial_derate_distance_mode: chip_size
  - SOCV RC Variation: Early 0.100, Late 0.100
  - Wire derate: SOCV factors enabled
  - SOCV files: Standard SOCV (16 files)
IMP-10-0-0-07-WARN01: Waiver not used (2 items):
  Severity: Warn Occurrence: 2
  - Some waived item
  - Another waived item
```

---

## 技术细节

### OCV 指标详解

#### 1. Analysis Mode: MMMC OCV (SOCV)
**检查内容**: 确认分析模式设置为 MMMC OCV 且启用了 SOCV

**日志格式**:
```
# Analysis Mode: MMMC OCV (SOCV)
```

**格式化输出**: `"Analysis Mode: MMMC OCV (SOCV)"`

---

#### 2. timing_enable_spatial_derate_mode
**检查内容**: 验证 spatial derate 模式已启用

**日志格式**:
```
[INFO] setting timing_enable_spatial_derate_mode to 1
```

**格式化输出**: `"timing_enable_spatial_derate_mode: 1"`

---

#### 3. timing_spatial_derate_distance_mode
**检查内容**: 验证 distance 模式设置为 chip_size

**日志格式**:
```
[INFO] setting timing_spatial_derate_distance_mode to chip_size
```

**格式化输出**: `"timing_spatial_derate_distance_mode: chip_size"`

---

#### 4. SOCV RC Variation Factors
**检查内容**: 验证 SOCV RC 变异因子（Early/Late 值）

**优先级**: 
1. **表格优先**: 解析 SOCV RC Variation Factors 表格
2. **命令回退**: 如果表格不存在，查找 `set_socv_rc_variation_factor` 命令

**日志格式（表格）**:
```
SOCV RC Variation Factors
+----------------------------------------------------------+-------+-------+
| Analysis View                                            | Early | Late  |
+----------------------------------------------------------+-------+-------+
| func_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold | 0.100 | 0.100 |
+----------------------------------------------------------+-------+-------+
```

**日志格式（命令）**:
```
<CMD> set_socv_rc_variation_factor 0.100 -early -views func_...
<CMD> set_socv_rc_variation_factor 0.100 -late -views func_...
```

**格式化输出**: 
- 表格模式: `"SOCV RC Variation: Early 0.100, Late 0.100"`
- 命令模式: `"SOCV RC Variation: 0.100 (command only)"`

---

#### 5. Wire Derate SOCV Factors
**检查内容**: 验证线路 derate 是否使用 SOCV 因子

**日志格式**:
```
### WIRE DERATE ###
+-------------+--------------+
| User Derate | SOCV Factors |
+-------------+--------------+
|             |      X       |
+-------------+--------------+
```

**检查逻辑**: 在 SOCV Factors 列中查找 `X` 标记

**格式化输出**: 
- 启用: `"Wire derate: SOCV factors enabled"`
- 未启用: `"Wire derate: No SOCV factors"`

---

#### 6. SOCV Files
**检查内容**: 验证 SOCV 文件已加载（文件数量和类型）

**日志格式**:
```
### OCV FILES ###
+-------------+-------------+
|    AOCV     | Spatial-OCV |
+-------------+-------------+
|             |      X      |
+-------------+-------------+

SOCV Files:
   - /process/tsmcN3/data/stdcell/.../file1.socv
   - /process/tsmcN3/data/stdcell/.../file2.socv
   - /process/tsmcN3/data/stdcell/.../file3.socv
```

**检查逻辑**: 
1. 检查 OCV FILES 表格中是否标记 Spatial-OCV
2. 统计 `SOCV Files:` 部分的 `.socv` 文件数量

**格式化输出**: 
- Spatial-OCV: `"SOCV files: Spatial-OCV (16 files)"`
- Standard SOCV: `"SOCV files: Standard SOCV (16 files)"`

---

### 特殊模式处理（Type 2/3）

#### "SOCV Files Used" 语义检查

**Pattern**: `"SOCV Files Used"`

**检查逻辑**:
```python
1. 查找日志中的 "SOCV Files:" 部分
2. 统计 .socv 文件条目数量
3. 如果 file_count > 0:
     返回 "SOCV Files Used (N files)"
   否则:
     返回未找到
```

**使用场景**: 验证设计是否真的使用了 SOCV 文件，而不仅仅是配置了相关设置

---

### 大小写不敏感匹配

所有 pattern 匹配都是**大小写不敏感**的：

| Pattern (YAML) | Log 内容 | 匹配结果 |
|---|---|---|
| `"WIRE DERATE"` | `### wire derate ###` | ✅ 匹配 |
| `"Analysis Mode: MMMC OCV"` | `# analysis mode: mmmc ocv (socv)` | ✅ 匹配 |
| `"socv rc variation factors"` | `SOCV RC Variation Factors` | ✅ 匹配 |

---

### 符号自动转换

支持 `=` 和 `to` 符号的自动转换：

| Pattern (YAML) | Log 内容 | 匹配结果 |
|---|---|---|
| `"timing_enable_spatial_derate_mode = 1"` | `setting timing_enable_spatial_derate_mode to 1` | ✅ 匹配 |
| `"timing_enable_spatial_derate_mode to 1"` | `setting timing_enable_spatial_derate_mode = 1` | ✅ 匹配 |

---

## 使用建议

### 推荐使用场景

**Type 1**: 
- 适用于严格验证所有 OCV 设置的场景
- 所有 6 个指标都必须正确配置
- 适合 signoff 阶段

**Type 2**: 
- 适用于验证特定 OCV 配置项
- 可以自定义检查哪些 pattern
- 适合有特定 foundry 要求的场景

**Type 3**: 
- 适用于允许部分 OCV 设置缺失但需要豁免的场景
- 可以区分真正的 PASS 和因豁免而 PASS
- 适合有已知限制的设计

**Type 4**: 
- 适用于检查所有 OCV 指标但需要记录备注的场景
- waiver 作为信息记录而非真正的豁免
- 适合需要追踪设计决策的场景

---

## 常见问题

### Q1: Pattern 明明在 log 中，为什么还是 "not found"？
**A**: 检查以下几点：
- Pattern 是大小写不敏感的，不需要完全匹配大小写
- Pattern 支持部分匹配（substring match）
- `=` 和 `to` 会自动转换
- 确认 pattern 中没有多余的空格

### Q2: "SOCV Files Used" 总是失败？
**A**: 这是一个特殊的语义检查，需要满足：
1. Log 中有 `SOCV Files:` 部分
2. 该部分下列出了 `.socv` 文件（以 `-` 开头）
3. 至少有 1 个 `.socv` 文件

### Q3: Type 1 vs Type 2 如何选择？
**A**: 
- **Type 1**: 自动解析所有 6 个 OCV 指标，提供详细的值信息（如 Early/Late、文件数量）
- **Type 2**: 只做简单的字符串匹配，不解析具体的值

如果需要验证具体的 OCV 参数值，使用 Type 1。如果只需要确认某些关键字出现，使用 Type 2。

### Q4: PASS 和 PASS(Waive) 的区别？
**A**: 
- **PASS**: 所有检查项都真正通过，没有使用任何 waiver
- **PASS(Waive)**: 
  - Type 3: 部分检查项失败但被 waive
  - Type 4: 所有检查项通过但存在 waiver 记录

---

## 更新日志

**2025-12-04**:
- ✅ 初始版本实现
- ✅ 支持 4 种 checker 类型（Type 1-4）
- ✅ 支持 6 个 OCV 指标解析（Type 1/4）
- ✅ 支持灵活的模式匹配（Type 2/3）
- ✅ 大小写不敏感匹配
- ✅ 符号自动转换（`=` ↔ `to`）
- ✅ 特殊语义模式：SOCV Files Used
- ✅ PASS/PASS(Waive) 状态区分
- ✅ 表格优先 + 命令回退解析策略（SOCV RC Variation）
- ✅ 统一的日志和报告输出格式
