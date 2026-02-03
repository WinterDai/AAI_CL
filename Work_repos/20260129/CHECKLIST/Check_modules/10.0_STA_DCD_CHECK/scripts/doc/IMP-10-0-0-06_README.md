# IMP-10-0-0-06 配置说明与示例

## 检查项目
**Confirm the SI setting is correct**

确认静态时序分析（STA）中的信号完整性（Signal Integrity, SI）设置是否正确配置。SI 分析对于先进工艺节点（如 3nm）至关重要，能够检测串扰（crosstalk）、毛刺（glitch）等信号完整性问题。

---

## 功能特性

### ✅ 自动检测四种 Checker 类型
脚本会根据 YAML 配置自动识别使用哪种类型：
- **Type 1**: 布尔检查（所有 SI 指标）- 无豁免
- **Type 2**: 数值比较（特定 SI 设置）- 无豁免  
- **Type 3**: 数值比较 + 豁免逻辑
- **Type 4**: 布尔检查 + 豁免逻辑

### ✅ 解析 Tempus STA 日志
从 `sta_post_syn.log` 提取 5 个关键 SI 指标：

**检查指标**:
1. **Signoff Settings: SI On** - SI 总开关启用
2. **delaycal_enable_si to 1** - Delay calculation SI 启用
3. **timing_library_read_ccs_noise_data to 1** - CCS noise 数据读取
4. **report_noise** - Glitch 分析命令执行
5. **CCS libraries** - CCS 库类型确认（支持 SI 分析）

**日志格式示例**:
```
#################################################################################
# Signoff Settings: SI On (EWM-WFP)
#################################################################################
[INFO] setting delaycal_enable_si to 1
**INFO: (IMPESI-5090): AAE_INFO: switching set_db delaycal_enable_si from false to true ...
[INFO] setting timing_library_read_ccs_noise_data to 1
<CMD> report_noise -view ... -out_file .../glitch.rpt
Read 484 cells in library 'tcbn03e_bwp143mh117l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs'
```

### ✅ 精确匹配模式
- **pattern_items**: 必须在日志中精确匹配（完全包含子串）
- 支持自定义 SI 检查项
- 不支持通配符或正则表达式

### ✅ 错误类型区分 (Type 2/3)

**Type 2/3 区分两种错误情况**:
- **ERROR01 (Missing)**: 期望的模式在日志中完全找不到
- **ERROR02 (Mismatch)**: 找到相关内容但值不匹配
  - 例如：期望 "Signoff Settings: SI On" 但实际是 "Signoff Settings: SI Off"

### ✅ PASS 状态区分 (Type 3/4)

**当 waivers.value > 0 时（Type 3/4）**:
- **PASS 状态标识**:
  - 真正的 PASS（所有检查都通过） → `PASS:IMP-10-0-0-06:...`
  - 因 waive 而 PASS（有错误但被豁免） → `PASS(Waive):IMP-10-0-0-06:...`

### ✅ 日志分组规则 (2025-12-03)

**Type 1/2 (无豁免逻辑)**:
- **waivers.value = N/A** (正常模式):
  - ERROR01: 缺失的指标
  - INFO01: 找到的指标
  
- **waivers.value = 0** (强制PASS模式):
  - INFO01: 所有检查项（含强制豁免标签）
  - 所有 FAIL → INFO + `[WAIVED_AS_INFO]`
  - waive_items → INFO + `[WAIVED_INFO]`

**Type 2 额外分组**:
- ERROR02: 值不匹配的指标

**Type 3 (数值比较 + 豁免)**:
- ERROR01: 缺失的指标（未豁免）
- ERROR02: 值不匹配的指标（未豁免）
- INFO01: 真正通过的指标 → "SI setting is correct"
- INFO02: 因 waive 而通过的指标 → "SI setting verified via waiver"
- WARN01: 未使用的豁免 → "Waiver not used"

**Type 4 (布尔检查 + 豁免)**:
- ERROR01: 缺失的指标
- INFO01: 找到的指标 → "SI setting is correct"
- WARN01: 未使用的豁免 → "Waiver not used"

### ✅ 自定义输出格式

**Log 输出格式 (Type 2 - 有 Missing 和 Mismatch)**:
```
FAIL:IMP-10-0-0-06:Confirm the SI setting is correct?
IMP-10-0-0-06-ERROR01: SI setting isn't correct (missing required indicators):
  Severity: Fail Occurrence: 1
  - CCS libraries (SI setting isn't correct: missing)

IMP-10-0-0-06-ERROR02: SI setting isn't correct (value mismatch):
  Severity: Fail Occurrence: 1
  - Signoff Settings: SI On (SI setting isn't correct: mismatch)

IMP-10-0-0-06-INFO01: SI setting is correct (3/5 indicators found):
  Severity: Info Occurrence: 3
  - delaycal_enable_si: 1
  - timing_library_read_ccs_noise_data: 1
  - report_noise: Not available (parasitics issue)
```

**Report 输出格式 (Type 2)**:
```
FAIL:IMP-10-0-0-06:Confirm the SI setting is correct?
Fail Occurrence: 2
1: Fail: Signoff Settings: SI Off. In line 63, sta_post_syn.log: SI setting isn't correct: expected 'Signoff Settings: SI Off', found '# Signoff Settings: SI On (EWM-WFP)'
2: Fail: CCS libraries: SI setting isn't correct: expected 'CCS libraries' not found

Info Occurrence: 3
1: Info: setting delaycal_enable_si to 1. In line 66, sta_post_syn.log: SI setting is correct
2: Info: setting timing_library_read_ccs_noise_data to 1. In line 69, sta_post_syn.log: SI setting is correct
3: Info: Glitch results. In line 76, sta_post_syn.log: SI setting is correct
```

**Log 输出格式 (Type 3 - PASS(Waive))**:
```
PASS(Waive):IMP-10-0-0-06:Confirm the SI setting is correct?
IMP-10-0-0-06-INFO01: SI setting is correct (3/5 indicators found):
  Severity: Info Occurrence: 3
  - delaycal_enable_si: 1
  - timing_library_read_ccs_noise_data: 1
  - report_noise: Not available (parasitics issue)

IMP-10-0-0-06-INFO02: SI setting verified via waiver (2 indicators waived):
  Severity: Info Occurrence: 2
  - Signoff Settings: SI On [WAIVED: mismatch]
  - CCS libraries [WAIVED: missing]
```

**Log 输出格式 (Type 4 - 未使用的 Waiver)**:
```
FAIL:IMP-10-0-0-06:Confirm the SI setting is correct?
IMP-10-0-0-06-ERROR01: SI setting isn't correct (missing indicators):
  Severity: Fail Occurrence: 1
  - CCS libraries

IMP-10-0-0-06-INFO01: SI setting is correct (4/5 indicators found):
  Severity: Info Occurrence: 4
  - Signoff Settings: SI On
  - delaycal_enable_si: 1
  - timing_library_read_ccs_noise_data: 1
  - report_noise: Not available (parasitics issue)

IMP-10-0-0-06-WARN01: Waiver not used (2 items):
  Severity: Warn Occurrence: 2
  - SI configuration note 1
  - SI configuration note 2
```

---

## 📋 配置文件示例

### 🔹 Type 1: 布尔检查（所有 SI 指标）

**用途**: 验证所有 5 个 SI 指标都已正确配置

#### 方案 A: 正常模式 (waivers.value = N/A)

```yaml
description: Confirm the SI setting is correct.
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
- ✅ 所有 5 个 SI 指标都找到 → PASS
- ❌ 任何指标缺失 → FAIL

---

### 🔹 Type 2: 数值比较（特定 SI 设置）

**用途**: 验证特定的 SI 配置项是否存在，并区分 Missing 和 Mismatch 错误

```yaml
description: Confirm the SI setting is correct.
requirements:
  value: 5
  pattern_items:
    - "Signoff Settings: SI On"
    - "setting delaycal_enable_si to 1"
    - "setting timing_library_read_ccs_noise_data to 1"
    - "Glitch results"
    - "CCS libraries"
input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
waivers:
  value: N/A
  waive_items: []
```

**检查逻辑**:
- ✅ 所有 pattern_items 都精确匹配 → PASS
- ❌ 找到相关内容但值不匹配 → ERROR02 (Mismatch)
- ❌ 完全找不到 → ERROR01 (Missing)

---

### 🔹 Type 3: 数值比较 + 豁免逻辑

**用途**: 验证特定 SI 配置，支持对缺失/不匹配项进行豁免

```yaml
description: Confirm the SI setting is correct.
requirements:
  value: 5
  pattern_items:
    - "Signoff Settings: SI On"
    - "setting delaycal_enable_si to 1"
    - "setting timing_library_read_ccs_noise_data to 1"
    - "Glitch results"
    - "CCS libraries"
input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
waivers:
  value: 2
  waive_items:
    - "Signoff Settings: SI On"
    - "CCS libraries"
```

**检查逻辑**:
- 在 waive_items 中的项目缺失/不匹配 → INFO02 + [WAIVED: missing/mismatch]
- 不在 waive_items 中的项目缺失/不匹配 → ERROR01/ERROR02
- waive_items 未使用 → WARN01
- 有豁免项时显示 → `PASS(Waive)`

**预期输出**:
```
PASS(Waive):IMP-10-0-0-06:Confirm the SI setting is correct?
IMP-10-0-0-06-INFO01: SI setting is correct (3/5 indicators found):
  - delaycal_enable_si: 1
  - timing_library_read_ccs_noise_data: 1
  - report_noise: Not available (parasitics issue)

IMP-10-0-0-06-INFO02: SI setting verified via waiver (2 indicators waived):
  - Signoff Settings: SI On [WAIVED: mismatch]
  - CCS libraries [WAIVED: missing]
```

---

### 🔹 Type 4: 布尔检查 + 豁免逻辑

**用途**: 检查所有 SI 指标，未使用的 waiver 显示为 WARN

```yaml
description: Confirm the SI setting is correct.
requirements:
  value: N/A
  pattern_items: []
input_files: 
  - C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
waivers:
  value: 2
  waive_items:
    - "SI configuration note 1"
    - "SI configuration note 2"
```

**检查逻辑**:
- 检查所有 5 个 SI 指标
- waive_items 未用于豁免任何失败项 → WARN01

**预期输出**:
```
FAIL:IMP-10-0-0-06:Confirm the SI setting is correct?
IMP-10-0-0-06-ERROR01: SI setting isn't correct (missing indicators):
  - CCS libraries

IMP-10-0-0-06-INFO01: SI setting is correct (4/5 indicators found):
  - Signoff Settings: SI On
  - delaycal_enable_si: 1
  - timing_library_read_ccs_noise_data: 1
  - report_noise: Not available (parasitics issue)

IMP-10-0-0-06-WARN01: Waiver not used (2 items):
  - SI configuration note 1
  - SI configuration note 2
```

---

## 技术细节

### SI 指标格式化输出

每个 SI 指标在日志中有自定义的格式化输出：

1. **Signoff Settings** → "Signoff Settings: SI On"
2. **delaycal_enable_si** → "delaycal_enable_si: 1"
3. **timing_library_read_ccs_noise_data** → "timing_library_read_ccs_noise_data: 1"
4. **report_noise** → 
   - "report_noise: Not available (parasitics issue)" 或
   - "report_noise: Report generated (xxx.rpt)"
5. **CCS libraries** → "CCS libraries: X libraries found"

### Mismatch 检测逻辑

针对以下指标检测值不匹配：
- **Signoff Settings**: 检测 "SI On" vs "SI Off"
- **delaycal_enable_si**: 检测设置值 0/1
- **timing_library_read_ccs_noise_data**: 检测设置值 0/1

---

## 更新日志

**2025-12-03**:
- ✅ 新增 PASS 状态区分：真正 PASS vs PASS(Waive)
- ✅ Type 2/3 区分 Missing 和 Mismatch 错误类型
- ✅ Type 3 分离 INFO01(通过) 和 INFO02(豁免)
- ✅ Type 4 未使用的 waiver 显示为 WARN01
- ✅ 优化 Report 输出格式，简化为 "SI setting is correct"
- ✅ 统一所有类型的日志和报告输出格式
