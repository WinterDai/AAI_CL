# CHECKLIST Framework Development Prompt

## 项目概述

这是一个基于 Python 的 **VLSI 设计验证自动化框架**，用于在芯片设计的各个阶段（综合、布局布线、时序分析等）执行标准化检查。框架采用模块化架构，支持四种检查类型的自动检测和执行。

## 最新更新 (2025年12月15日)

### 路径可移植性架构重构 ⭐ NEW

1. **${CHECKLIST_ROOT}变量系统**
   - **目标**: 实现完全Git-friendly的配置文件，消除个人路径依赖
   - **架构**: 2-Phase workflow (placeholder → merge)
   - **Phase 1**: 基于CheckList_Index.yaml生成346个checker的template
   - **Phase 2**: 合并items/*.yaml到template（保留${CHECKLIST_ROOT}变量）
   - **Phase 3**: ~~解析变量为绝对路径~~ (已废弃，保留代码备用)
   - **变量展开**: 在checker运行时动态展开（内存中操作）

2. **核心修改**
   - **parse_interface.py**:
     * 读取DATA_INTERFACE.template.yaml（带变量版本）
     * extract_module_data()移除expand_variables()调用
     * 分发的items/*.yaml文件保留${CHECKLIST_ROOT}变量
   - **base_checker.py**:
     * validate_input_files()在验证前自动展开${CHECKLIST_ROOT}
     * 硬盘文件：${CHECKLIST_ROOT} (可移植)
     * 内存数据：绝对路径 (可执行)
   - **data_interface.py**:
     * cmd_run()注释掉Phase 3 (resolve)
     * 保持2-Phase workflow: placeholder → merge

3. **收益**
   - ✅ 所有配置文件Git-friendly（69个items文件，48个使用${CHECKLIST_ROOT}）
   - ✅ 团队成员间无需修改路径即可共享
   - ✅ 跨平台兼容（Windows/Linux自动适配）
   - ✅ Checker正常运行（变量在运行时展开）

## 历史更新 (2025年12月4日)

### YAML输出格式优化

1. **Windows路径单引号格式**
   - **优化点**: YAML输出中Windows路径改用单引号，无需转义反斜杠
   - **改进前**: `source_file: "C:\\Users\\yuyin\\Desktop\\..."`
   - **改进后**: `source_file: 'C:\Users\yuyin\Desktop\...'`
   - **优势**:
     * 更简洁易读的YAML输出
     * 减少转义字符复杂度
     * 保持完全的YAML解析器兼容性
   - **实现**: `write_summary_yaml.py` 智能引号选择逻辑
     * 包含单引号的字符串 → 使用双引号+转义
     * 其他情况（包括Windows路径） → 使用单引号

### 重要架构迁移完成

1. **13.0_POST_PD_EQUIVALENCE_CHECK 模块迁移**
   - 全部8个checker已迁移至BaseChecker架构
   - 完整支持type1/2/3/4自动检测
   - 添加ConfigurationError异常处理
   - 修复IMP-13-0-0-01, 03, 07的逻辑问题

2. **6.0_POST_SYNTHESIS_LEC_CHECK 模块创建**
   - 从13.0复制并重命名为6.0
   - 全部8个checker (IMP-6-0-0-00 到 IMP-6-0-0-07)
   - 相同逻辑适配综合后LEC验证

3. **10.0_STA_DCD_CHECK 模块增强** ⭐ NEW
   - 新增3个checker:
     * IMP-10-0-0-06: 检查SDC中set_case_analysis命令
     * IMP-10-0-0-07: 检查SDC中set_disable_timing命令
     * IMP-10-0-0-08: 验证generated clock的source clock
   - 完整支持BaseChecker架构和type1/2/3/4自动检测

4. **Waiver标签规则统一** (2025-12-02)
   - **目的**: 统一Type 1/2/3/4的waiver标签使用规则
   - **新规则**:
     * **当 waivers.value > 0 时（Type 3/4）**:
       - 所有与 waive_items 相关的 INFO/FAIL/WARN 输出，reason 后缀统一为 `[WAIVER]`
     * **当 waivers.value = 0 时（Type 1/2）**:
       - waive_items 配置项作为 INFO 输出，后缀为 `[WAIVED_INFO]`
       - 检查发现的 FAIL/WARN 转为 INFO，后缀为 `[WAIVED_AS_INFO]`
       - 强制 PASS（所有失败都被豁免）
     * **所有类型均支持 value = N/A**
   - **修改范围**:
     * 10.0_STA_DCD_CHECK: IMP-10-0-0-04.py 完整支持新规则
     * 5.0_SYNTHESIS_CHECK: 11个checker文件（待更新）
     * 6.0_POST_SYNTHESIS_LEC_CHECK: 8个checker文件（待更新）
     * 13.0_POST_PD_EQUIVALENCE_CHECK: 8个checker文件（待更新）
   - **收益**: 
     * 清晰区分强制豁免（waiver=0）与正常豁免（waiver>0）
     * Type 1/2 支持强制PASS模式，便于调试和过渡期使用
     * 标签含义更明确，提升可追溯性

4. **框架功能增强**
   - **Windows路径处理**: 修复YAML序列化中Windows路径的转义问题
   - **终端输出过滤**: Summary YAML警告仅写入日志文件，不显示在终端
   - **输出格式优化**: 移除add_pin_constraints输出中的"//"前缀

### 技术改进详情

**check_flowtool.py**
- TeeLogger增加过滤器，屏蔽冗余的summary警告
- 过滤内容: `Summary directory not found`, `Failed to generate summary YAML`, `Summary YAML missing`

**write_summary_yaml.py**
- 修复Windows路径YAML转义
- `needs_quotes`条件增加`'\\' in value`检查
- 确保路径如`C:\Users\...`被正确双引号转义

**Checker脚本**
- 全部16个checker (13.0的8个 + 6.0的8个) 实现BaseChecker模式
- ConfigurationError处理与try-except块
- 方法命名修复: `detect_checker_type()` (之前错误为`detect_check_type()`)
- 严重性枚举修复: `Severity.FAIL` (之前错误为`Severity.ERROR`)

### 重要修复

**IMP-13-0-0-00 / IMP-6-0-0-00** (Conformal约束审查)
- 移除输出中的"//"前缀
- 清洁提取add_pin_constraints命令

**IMP-13-0-0-01 / IMP-6-0-0-01** (Conformal日志警告)
- 从警告行中去除"//"前缀
- 清洁提取add_pin_constraints命令

**IMP-13-0-0-03 / IMP-6-0-0-03** (黑盒端口定义)
- 原逻辑: 在black_box.rpt中搜索HIER/SYSTEM ❌
- 修复后: 匹配pattern_items黑盒与日志中的.lib文件 ✅
- 解析日志中的`// Parsing file .../xxx.lib ...`
- 大小写敏感的包含匹配

**IMP-13-0-0-07 / IMP-6-0-0-07** (LEC Flatten模型验证)
- 原逻辑: 检查LEC PASS/FAIL结果 ❌
- 修复后: 搜索确切字符串`set flatten model -library_pin_verification` ✅
- 在所有输入文件中搜索，带详细错误信息

---

## 核心架构

### 目录结构
```
CHECKLIST/
├── Check_modules/
│   ├── common/                          # 公共基础类和工具
│   │   ├── base_checker.py              # 统一 Checker 基类
│   │   ├── output_formatter.py          # 输出格式化（Log/Report）
│   │   ├── check_flowtool.py            # Checker 执行引擎
│   │   ├── write_summary_yaml.py        # YAML总结生成器
│   │   ├── parse_interface.py           # DATA_INTERFACE 分发
│   │   └── ...
│   ├── 1.0_LIBRARY_CHECK/               # 库文件检查模块 ✅ 已迁移
│   ├── 5.0_SYNTHESIS_CHECK/             # 综合检查模块 ✅ 已迁移
│   │   ├── scripts/checker/
│   │   │   ├── IMP-5-0-0-00.py          # 库模型检查
│   │   │   ├── IMP-5-0-0-10.py          # 禁用单元检查
│   │   │   └── ...
│   │   ├── inputs/items/                # 检查项配置
│   │   │   ├── IMP-5-0-0-00.yaml
│   │   │   └── IMP-5-0-0-10.yaml
│   │   ├── logs/                        # 检查日志（分组格式）
│   │   ├── reports/                     # 检查报告（详细列表）
│   │   └── outputs/                     # 模块总结
│   ├── 6.0_POST_SYNTHESIS_LEC_CHECK/    # 综合后LEC检查 ⭐ 新增
│   ├── 10.0_STA_DCD_CHECK/              # 时序分析检查 ✅ 已迁移
│   ├── 13.0_POST_PD_EQUIVALENCE_CHECK/  # PD后等价性检查 ⭐ 已迁移
│   └── [其他模块]/
├── Data_interface/
│   ├── scripts/
│   │   └── data_interface.py            # 2-Phase workflow管理
│   └── outputs/
│       ├── DATA_INTERFACE.template.yaml # 模板文件（带${CHECKLIST_ROOT}变量）
│       └── DATA_INTERFACE.yaml          # (已废弃) 绝对路径版本
├── IP_project_folder/
│   └── reports/                         # 设计工具输出报告
│       ├── qor.rpt
│       ├── gates.rpt
│       └── ...
├── Project_config/
│   └── prep_config/Initial/latest/
│       └── CheckList_Index.yaml         # 346个checker的索引定义
└── Work/
    ├── Results/                         # 汇总结果
    └── Reports/                         # HTML可视化
```

---

## 配置文件与变量系统 ⭐ NEW (2025-12-15)

### 2-Phase Workflow

框架采用2阶段工作流生成配置：

```
Phase 1: Placeholder Generation (占位符生成)
  CheckList_Index.yaml (346 checkers)
        ↓
  DATA_INTERFACE.template.yaml (带${CHECKLIST_ROOT}变量)

Phase 2: Items Merge (配置合并)
  Check_modules/*/inputs/items/*.yaml (开发者编写)
        ↓
  合并到 template.yaml (保留${CHECKLIST_ROOT}变量)

Phase 3: (已废弃)
  ~~Resolve ${CHECKLIST_ROOT} → 绝对路径~~
```

### ${CHECKLIST_ROOT} 变量系统

**设计原则**：
- 配置文件保持Git-friendly（硬盘上使用变量）
- 运行时动态展开（内存中使用绝对路径）
- 跨平台兼容（Windows/Linux自动适配）

**配置文件示例** (`items/IMP-10-0-0-02.yaml`):
```yaml
description: Confirm the clock uncertainty setting is correct.
requirements:
  value: N/A
  pattern_items: []
input_files:
- ${CHECKLIST_ROOT}/IP_project_folder/reports/constr.rpt  # 使用变量
waivers:
  value: 2
  waive_items:
  - name: set_clock_uncertainty 0.01 -hold
    reason: Pre-implementation phase
```

**运行时展开**：
```python
# base_checker.py - validate_input_files()
from parse_interface import expand_variables, get_builtin_variables
variables = get_builtin_variables()  # {'CHECKLIST_ROOT': 'C:/Users/yuyin/Desktop/CHECKLIST'}
expanded_files = expand_variables(input_files, variables)

# 硬盘: ${CHECKLIST_ROOT}/IP_project_folder/reports/constr.rpt
# 内存: C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\reports\constr.rpt
```

**修改的核心文件**：
1. **parse_interface.py**:
   - 读取 `DATA_INTERFACE.template.yaml`（带变量版本）
   - `extract_module_data()` 移除 `expand_variables()` 调用
   - `find_input_files()` 在查找前展开变量
   
2. **base_checker.py**:
   - `validate_input_files()` 在验证前展开变量
   
3. **data_interface.py**:
   - `cmd_run()` 注释掉 Phase 3 (resolve)
   - 保持2-Phase: placeholder → merge

---

## Checker 头注释规范 ⭐ NEW (2025-12-09)

**所有新开发的checker必须包含标准化的头注释**，这是强制要求，不可省略。

### 标准格式

```python
################################################################################
# Script Name: {ITEM_ID}.py
#
# Purpose:
#   {One-line description from item_desc}
#   {Optional: Additional context about what this checker validates}
#
# Logic:
#   - {First logical step - what files are parsed and how}
#   - {Second logical step - what data is extracted}
#   - {Third logical step - how validation/comparison is performed}
#   - {Additional steps as needed - waiver logic, special handling, etc.}
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Author: {your_name}
# Date: {current_date}
################################################################################
```

### 各部分说明

1. **Script Name**: checker文件名（如 IMP-10-0-0-02.py）

2. **Purpose**: 
   - 第一行：从item_desc复制的简短描述
   - 可选：添加额外的上下文说明

3. **Logic** （⭐ 关键部分，必填）:
   - 描述checker的检查逻辑步骤
   - 每个步骤一行，以 `- ` 开头
   - 清晰、具体、可操作
   - 将被自动提取用于Excel文档和报告生成
   
   **好的Logic示例**:
   ```
   # Logic:
   #   - Parse constr.rpt to extract set_clock_uncertainty commands
   #   - Extract metadata (tool version, generation date, design name)
   #   - Verify existence and content consistency with expected patterns
   #   - Support waiver for missing or mismatched constraints
   ```
   
   **不好的Logic示例**:
   ```
   # Logic:
   #   - Check stuff
   #   - Run validation
   #   - Return result
   ```

4. **Auto Type Detection**: 标准模板，直接复制即可

5. **Waiver Tag Rules**: 标准模板，直接复制即可

6. **Author & Date**: 填入开发者名字和日期

### 参考示例

查看 `Check_modules/10.0_STA_DCD_CHECK/scripts/checker/` 中的任何checker文件：
- IMP-10-0-0-02.py - 完整示例
- IMP-10-0-0-04.py - 完整示例
- IMP-10-0-0-05.py - 完整示例

### 为什么这很重要

1. **自动文档生成**: Logic部分会被提取到Excel文档的Comments列
2. **代码可维护性**: 清晰的逻辑说明帮助其他开发者理解checker
3. **一致性**: 所有checker遵循相同的文档标准
4. **可追溯性**: 明确的作者和日期信息

### 开发流程集成

在DEVELOPER_TASK_PROMPTS.md的Step 3中，头注释是第一步（Step 0），必须在编写任何代码之前完成。

---

## 四种 Checker 类型

### 类型检测逻辑
基于 `requirements.value` 和 `waivers.value` 自动检测：

| Type | requirements.value | waivers.value | 描述 | 豁免标签 |
|------|-------------------|---------------|------|---------|
| **Type 1** | `N/A` | `N/A` 或 `0` | 布尔检查 | waiver=0时使用`[WAIVED_AS_INFO]`/`[WAIVED_INFO]` |
| **Type 2** | `>0` 或 `N/A` | `N/A` 或 `0` | 数值比较 | waiver=0时使用`[WAIVED_AS_INFO]`/`[WAIVED_INFO]` |
| **Type 3** | `>0` 或 `N/A` | `>0` | 数值比较 + 豁免 | 统一使用`[WAIVER]` |
| **Type 4** | `N/A` | `>0` | 布尔检查 + 豁免 | 统一使用`[WAIVER]` |

**⚠️ 重要更新：**
- **所有类型均支持 `value = N/A`**（2025-12-02更新）
- **Type 2/3**: 当使用 `pattern_items` 时，建议 `requirements.value` 等于 `pattern_items` 的数量
  - 示例：如果 `pattern_items: ["CLOCK_A", "CLOCK_B"]`，则 `value: 2`
  - 但 `value: N/A` 也被支持
- **Type 3/4**: 当使用 `waive_items` 且 `value > 0` 时，建议 `waivers.value` 等于 `waive_items` 的数量
  - 示例：如果 `waive_items: ["ITEM_X", "ITEM_Y"]`，则 `value: 2`
  - `value` 也可以是任意正数或 `N/A`
- **Type 1/2**: 当 `waivers.value = 0` 时，启用强制PASS模式
- **验证建议**: Checker 应在运行时验证数量一致性，不一致时输出警告

### Type 1: 布尔检查
```yaml
# 配置示例（正常模式）
requirements:
  value: N/A
  pattern_items: []  # 空列表，不使用 pattern 查找
waivers:
  value: N/A
  waive_items: []

# 配置示例（强制PASS模式，waiver=0）
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 0
  waive_items:
    - "waive_item_1"
    - "waive_item_2"
```

**检查逻辑：**
- 简单布尔判断：是/否，存在/不存在
- **正常模式（waiver=N/A）**:
  - PASS: 条件满足
  - FAIL: 条件不满足
- **强制PASS模式（waiver=0）**:
  - 所有 FAIL → INFO，后缀 `[WAIVED_AS_INFO]`
  - waive_items → INFO，后缀 `[WAIVED_INFO]`
  - 强制 PASS

**输出示例（正常PASS）：**
```
PASS
INFO01: All items meet requirements
  - Item1: Details...
  - Item2: Details...
```

**输出示例（waiver=0强制PASS）：**
```
PASS
INFO01: All violations waived
  - Item1: Issue found[WAIVED_AS_INFO]
  - Item2: Issue found[WAIVED_AS_INFO]
  - waive_item_1: Waive item[WAIVED_INFO]
  - waive_item_2: Waive item[WAIVED_INFO]
```

---

### Type 2: Value Check
```yaml
# 配置示例（正常模式）
requirements:
  value: 2                    # pattern 个数（配置验证）
  pattern_items:              # 要查找的 pattern 列表
    - "*nldm*"
    - "*quick*"
waivers:
  value: N/A
  waive_items: []

# 配置示例（强制PASS模式，waiver=0）
requirements:
  value: 0
  pattern_items:
    - "*nldm*"
    - "*quick*"
waivers:
  value: 0
  waive_items:
    - "waive_item_1"
```

**检查逻辑：**
1. 在输入文件中搜索 `pattern_items`
2. 分类结果：
   - `found_items`: 找到的 pattern
   - `missing_items`: 没找到的 pattern
3. **PASS/FAIL 取决于检查目的**：
   - **违规检查**：PASS 当 found_items 为空（没有违规）
   - **需求检查**：PASS 当 missing_items 为空（所有需求满足）
4. **配置验证**：检查 `len(pattern_items) == requirements.value`（不一致时警告，不影响 PASS/FAIL）
5. **extra_items**: 不在 pattern_items 中的项目（Type 2 特有）
   * 正常模式: 输出为 WARN
   * waiver=0 模式: 自动转为 INFO
   * 使用 `build_complete_output(extra_items=...)` 自动处理
6. **正常模式（waiver=N/A）**:
   - PASS/FAIL 根据检查目的决定
- **强制PASS模式（waiver=0）**:
  - 所有 FAIL → INFO，后缀 `[WAIVED_AS_INFO]`
  - waive_items → INFO，后缀 `[WAIVED_INFO]`
  - 强制 PASS

**输出示例（正常FAIL）：**
```
FAIL
Value: 3 (Expected: 0)

ERROR01: Forbidden items found
  - ItemA (Line 7): Matches pattern: *nldm*
  - ItemB (Line 12): Matches pattern: *quick*

INFO01: Patterns not found (good)
  - *nlpm*: Not found
```

**输出示例（waiver=0强制PASS）：**
```
PASS
Value: 3 (all waived)

INFO01: All violations waived
  - ItemA (Line 7): Matches pattern: *nldm*[WAIVED_AS_INFO]
  - ItemB (Line 12): Matches pattern: *quick*[WAIVED_AS_INFO]
  - waive_item_1: Waive item[WAIVED_INFO]
```

---

### Type 3: Value Check with Waiver Logic（Type 2 + 豁免支持）
```yaml
# 配置示例
requirements:
  value: 0
  pattern_items:
    - "*nldm*"
waivers:
  value: 2                    # 允许的豁免数
  waive_items:
    - name: "ItemA"
      reason: "Approved by architect - Ticket#12345"
    - name: "ItemB"
      reason: "Legacy requirement - will fix in Q2"
```

**检查逻辑：**
1. **与 Type 2 相同**：在输入文件中搜索 `pattern_items`
2. **额外的豁免分类**：
   - 将 found_items 与 waive_items 匹配
   - **未豁免项目 → ERROR**（需要修复）
   - **已豁免项目 → INFO + `[WAIVER]`**（批准的例外）
   - **未使用豁免 → WARN + `[WAIVER]`**（配置了但未用到）
3. **PASS/FAIL**（取决于检查目的）：
   - **违规检查**：PASS 当所有 found_items 都被豁免
   - **需求检查**：PASS 当所有 missing_items 被豁免或找到
4. **配置验证**：与 Type 2 相同

**输出示例（PASS）：**
```
PASS
Value: 2 (all waived)

INFO01: Waived violations and unmatched patterns (good)
  - ItemA: Approved by architect - Ticket#12345[WAIVER]
  - ItemB: Legacy requirement - will fix in Q2[WAIVER]
  - *quick*: Not found (good)
```

**输出示例（FAIL）：**
```
FAIL
Value: 3 (1 unwaived)

ERROR01: Unwaived violations
  - ItemC: Matches pattern: *nldm*

INFO01: Waived violations
  - ItemA: Approved by architect[WAIVER]
  - ItemB: Legacy requirement[WAIVER]
```

**输出示例（WARN - 未使用豁免）：**
```
PASS
Value: 1 (all waived)

INFO01: Waived violations
  - ItemA: Approved by architect[WAIVER]

WARN01: Unused waivers
  - ItemB: Waived item not found in check[WAIVER]
```

---

### Type 4: Boolean Check with Waiver Logic（Type 1 + 豁免支持）
```yaml
# 配置示例
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 1                    # 豁免数量必须 > 0
  waive_items:
    - name: "ItemA"
      reason: "Approved exception"
```

**检查逻辑：**
1. **与 Type 1 相同**：执行自定义布尔检查（不使用 pattern_items）
2. **额外的豁免分类**：
   - 将违例与 waive_items 匹配
   - **未豁免违例 → ERROR**
   - **已豁免违例 → INFO + `[WAIVER]`**
   - **未使用豁免 → WARN + `[WAIVER]`**
3. **PASS/FAIL**：PASS 当所有违例都被豁免
4. **value**: 显示为 "N/A"
5. **标签**: 所有waive相关输出使用 `[WAIVER]`

**输出示例（PASS）：**
```
PASS
Value: N/A

INFO01: Waived violations
  - ItemA: Approved exception[WAIVER]
```

**输出示例（FAIL）：**
```
FAIL
Value: N/A

ERROR01: Unwaived violations
  - ItemB: Violation not waived

INFO01: Waived violations
  - ItemA: Approved exception[WAIVER]
```

---

## Waiver标签使用规则 ⭐

### 规则概述

框架统一了所有类型的waiver标签使用规则：

| waivers.value | 适用类型 | 已豁免违规 | 未使用豁免 | waive_items配置 | 检查结果 |
|---------------|---------|-----------|-----------|----------------|---------|
| **> 0**       | Type 3/4 | INFO + `[WAIVER]` | WARN + `[WAIVER]` | - | 根据未豁免违规判定 |
| **= 0**       | Type 1/2 | INFO + `[WAIVED_AS_INFO]` | - | INFO + `[WAIVED_INFO]` | 强制 PASS |
| **= N/A**     | Type 1/2 | FAIL（正常）| - | - | 根据实际结果判定 |

### 标签含义

- **`[WAIVER]`**: 正常豁免项（waivers.value > 0，Type 3/4）
  - 表示这是经过批准的、有计划的豁免
  - 所有与 waive_items 相关的输出都使用此标签
  
- **`[WAIVED_AS_INFO]`**: 强制豁免的违规（waivers.value = 0，Type 1/2）
  - 表示检查中实际发现的违规项，但被强制转为 INFO
  - 用于调试模式或过渡期，便于识别实际存在的问题
  
- **`[WAIVED_INFO]`**: 强制豁免的配置项（waivers.value = 0，Type 1/2）
  - 表示 YAML 中预配置的 waive_items
  - 与实际检查结果无关，仅用于记录配置

### 使用场景

#### Scenario 1: 正常豁免（Type 3/4，waiver > 0）
```yaml
waivers:
  value: 2
  waive_items:
    - name: "CLOCK_A"
      reason: "Approved by architect"
```
**输出：**
```
INFO: CLOCK_A: Approved by architect[WAIVER]
WARN: CLOCK_B: Waived item not found[WAIVER]
```

#### Scenario 2: 强制PASS（Type 1/2，waiver = 0）
```yaml
waivers:
  value: 0
  waive_items:
    - "debug_item"
```
**输出：**
```
PASS (forced)
INFO: Violation found: Issue detected[WAIVED_AS_INFO]
INFO: debug_item: Waive item[WAIVED_INFO]
```

### 实现要点

```python
# Type 1/2 实现
waivers = self.get_waivers()
waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
is_waiver_zero = (waiver_value == 0)

if is_waiver_zero:
    # 强制PASS模式
    # FAIL → INFO + [WAIVED_AS_INFO]
    # waive_items → INFO + [WAIVED_INFO]
    pass
else:
    # 正常模式
    # 按实际结果判定
    pass

# Type 3/4 实现
# 固定使用 [WAIVER] 标签（因为 Type 3/4 必定 value > 0）
waived_tag = '[WAIVER]'
unused_waiver_tag = '[WAIVER]'
```

---

## 核心代码实现

### 1. BaseChecker 基类
**文件位置：** `Check_modules/common/base_checker.py`

**核心方法：**
```python
class BaseChecker(ABC):
    def __init__(self, check_module: str, item_id: str, item_desc: str):
        """初始化 Checker"""
        
    def init_checker(self, script_path: Path) -> None:
        """加载配置和初始化环境"""
        
    def get_requirements(self) -> Dict[str, Any]:
        """获取 requirements 配置"""
        
    def get_waivers(self) -> Dict[str, Any]:
        """获取 waivers 配置"""
    
    def detect_checker_type(self, custom_requirements: Optional[Dict[str, Any]] = None) -> int:
        """自动检测 Checker 类型（Type 1/2/3/4）"""
        
    @abstractmethod
    def execute_check(self) -> CheckResult:
        """执行检查（子类实现）"""
        
    def run(self) -> None:
        """主入口：初始化 → 执行 → 输出"""
```

---

### 2. 实现 Checker 的标准模板

#### 步骤 1: 类定义和初始化
```python
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import sys
import re

# 添加 common 到路径
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult
from output_formatter import DetailItem, Severity, create_check_result

class MyChecker(BaseChecker):
    def __init__(self):
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-XX",
            item_desc="检查描述"
        )
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._forbidden_patterns: List[str] = []
```

#### 步骤 2: 类型检测（使用 BaseChecker 方法）
**注意：** `detect_checker_type()` 已在 `BaseChecker` 中实现，无需在子类中重复定义。

**基本用法：**
```python
# 使用自身的 requirements（默认）
checker_type = self.detect_checker_type()
```

**跨模块引用用法（如 IMP-5-0-0-10 引用 IMP-1-0-0-02）：**
```python
# 加载外部 requirements 进行类型检测
try:
    imp_1_path = self.root / "Check_modules" / "1.0_LIBRARY_CHECK" / "inputs" / "items" / "IMP-1-0-0-02.yaml"
    with open(imp_1_path, 'r', encoding='utf-8') as f:
        imp_1_data = yaml.safe_load(f)
    custom_requirements = imp_1_data.get('requirements', {}) if imp_1_data else {}
except:
    custom_requirements = {}

checker_type = self.detect_checker_type(custom_requirements=custom_requirements)
```

**BaseChecker.detect_checker_type() 源码：**
```python
def detect_checker_type(self, custom_requirements: Optional[Dict[str, Any]] = None) -> int:
    """
    Auto-detect checker type based on configuration.
    
    Args:
        custom_requirements: Optional custom requirements dict (for cross-reference cases).
                            If None, uses self.get_requirements()
    
    Returns:
        1: Type 1 (Boolean check, no waiver logic)
        2: Type 2 (Value comparison, no waiver)
        3: Type 3 (Value comparison WITH waiver logic)
        4: Type 4 (Boolean WITH waiver logic)
    """
    # 详见 Check_modules/common/base_checker.py
```

#### 步骤 3: 输入文件解析
```python
def _parse_input_files(self) -> List[str]:
    """
    解析输入文件，提取检查项
    
    Returns:
        List of items to check
    """
    if not self.item_data or 'input_files' not in self.item_data:
        return []
    
    input_files = self.item_data['input_files']
    if isinstance(input_files, str):
        input_files = [input_files]
    
    all_items = []
    
    for file_path_str in input_files:
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            continue
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 解析文件内容
        items = self._extract_items_from_lines(lines, file_path)
        all_items.extend(items)
    
    return all_items
```

#### 步骤 4: 模式匹配（Type 2/3）
```python
def _match_forbidden_item(self, item_name: str, patterns: List[str]) -> Optional[str]:
    """
    检查项是否匹配禁用模式
    
    支持：
    - 通配符: *nldm* 匹配包含 nldm 的任何项
    - 正则: ^pattern.* 
    - 精确匹配
    
    Returns:
        Matched pattern if found, None otherwise
    """
    for pattern in patterns:
        try:
            # 将通配符转换为正则
            regex_pattern = pattern
            if '*' in pattern and not pattern.startswith('^'):
                regex_pattern = pattern.replace('*', '.*')
            
            if re.search(regex_pattern, item_name):
                return pattern
        except re.error:
            # 正则错误，使用精确匹配
            if pattern == item_name:
                return pattern
    return None

def _find_violations(self, all_items: List[str], forbidden_patterns: List[str]) -> List[Tuple[str, str]]:
    """
    查找违例项
    
    Returns:
        List of (item_name, matched_pattern) tuples
    """
    violations = []
    for item_name in all_items:
        matched_pattern = self._match_forbidden_item(item_name, forbidden_patterns)
        if matched_pattern:
            violations.append((item_name, matched_pattern))
    return violations
```

#### 步骤 5: 主执行逻辑
```python
def execute_check(self) -> CheckResult:
    """执行检查"""
    if self.root is None:
        raise RuntimeError("Checker not initialized. Call init_checker() first.")
    
    # 获取配置
    requirements = self.get_requirements()
    self._forbidden_patterns = requirements.get('pattern_items', []) if requirements else []
    
    # 检测类型（使用 BaseChecker 提供的方法）
    checker_type = self.detect_checker_type()
    
    # 解析输入
    all_items = self._parse_input_files()
    
    # 查找违例
    violations = self._find_violations(all_items, self._forbidden_patterns)
    
    # 执行对应类型的检查
    if checker_type == 1:
        return self._execute_type1(all_items, violations)
    elif checker_type == 2:
        return self._execute_type2(all_items, violations)
    elif checker_type == 3:
        return self._execute_type3(all_items, violations)
    else:
        return self._execute_type4(all_items, violations)
```

#### 步骤 6: Type 1 实现
```python
def _execute_type1(self, all_items: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
    """Type 1: 布尔检查"""
    waivers = self.get_waivers()
    waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
    waive_items = waivers.get('waive_items', []) if waivers else []
    is_waiver_zero = (waiver_value == 0)
    
    details = []
    
    # 特殊情况：无项目
    if not all_items:
        details.append(DetailItem(
            severity=Severity.FAIL,
            name="",
            line_number=0,
            file_path="N/A",
            reason="No items found"
        ))
        return create_check_result(
            value=1,
            is_pass=False,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            item_desc=self.item_desc,
            default_group_desc="No items found"
        )
    
    # PASS: 显示所有项作为 INFO
    for item_name in all_items:
        metadata = self._metadata.get(item_name, {})
        details.append(DetailItem(
            severity=Severity.INFO,
            name=item_name,
            line_number=metadata.get('line_number', ''),
            file_path=metadata.get('file_path', ''),
            reason="Item passed check"
        ))
    
    # 添加豁免项
    if waive_items:
        for item in waive_items:
            tag = "[WAIVED_AS_INFO]" if is_waiver_zero else ""
            details.append(DetailItem(
                severity=Severity.INFO,
                name=item,
                line_number=0,
                file_path="N/A",
                reason=f"Waiver{tag}"
            ))
    
    info_groups = {
        "INFO01": {
            "description": "All items passed check",
            "items": all_items
        }
    }
    
    return create_check_result(
        value=len(all_items),
        is_pass=True,
        has_pattern_items=False,
        has_waiver_value=bool(waive_items),
        details=details,
        info_groups=info_groups,
        item_desc=self.item_desc
    )
```

#### 步骤 7: Type 2 实现
```python
def _execute_type2(self, all_items: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
    """Type 2: 数值比较"""
    requirements = self.get_requirements()
    expected_value = requirements.get('value', 0) if requirements else 0
    try:
        expected_value = int(expected_value)
    except:
        expected_value = 0
    
    waivers = self.get_waivers()
    waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
    waive_items = waivers.get('waive_items', []) if waivers else []
    is_waiver_zero = (waiver_value == 0)
    
    details = []
    
    # 找出未匹配的模式（好的）
    violated_patterns = set(pattern for _, pattern in violations)
    unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
    
    if is_waiver_zero:
        # waiver=0: 转为 INFO
        for item_name, pattern in violations:
            metadata = self._metadata.get(item_name, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=item_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Matches pattern: {pattern}[WAIVED_AS_INFO]"
            ))
        for item in waive_items:
            details.append(DetailItem(
                severity=Severity.INFO,
                name=item,
                line_number=0,
                file_path="N/A",
                reason="Waiver item[WAIVED_AS_INFO]"
            ))
        is_pass = True
    else:
        # 正常模式: 违例 = FAIL
        for item_name, pattern in violations:
            metadata = self._metadata.get(item_name, {})
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=item_name,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Matches forbidden pattern: {pattern}"
            ))
        
        # 未匹配模式 = INFO
        for pattern in unmatched_patterns:
            details.append(DetailItem(
                severity=Severity.INFO,
                name=pattern,
                line_number='',
                file_path='',
                reason="Pattern not found (good)"
            ))
        
        is_pass = (len(violations) == expected_value)
    
    return create_check_result(
        value=len(violations),
        is_pass=is_pass,
        has_pattern_items=True,
        has_waiver_value=bool(waive_items),
        details=details,
        item_desc=self.item_desc,
        default_group_desc="Forbidden items found"
    )
```

#### 步骤 8: Type 3 实现
```python
def _execute_type3(self, all_items: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
    """Type 3: 数值比较 + 豁免逻辑"""
    waivers = self.get_waivers()
    waive_items_dict = self._get_waive_items_with_reasons()
    waive_items = list(waive_items_dict.keys())
    
    # 分类违例
    waive_set = set(waive_items)
    unwaived = [(item, pattern) for item, pattern in violations if item not in waive_set]
    waived = [(item, pattern) for item, pattern in violations if item in waive_set]
    
    # 未使用的豁免
    violated_items = set(item for item, _ in violations)
    unused_waivers = [item for item in waive_items if item not in violated_items]
    
    # 未匹配的模式
    violated_patterns = set(pattern for _, pattern in violations)
    unmatched_patterns = [p for p in self._forbidden_patterns if p not in violated_patterns]
    
    details = []
    
    # ERROR: 未豁免违例
    for item_name, pattern in unwaived:
        metadata = self._metadata.get(item_name, {})
        details.append(DetailItem(
            severity=Severity.FAIL,
            name=item_name,
            line_number=metadata.get('line_number', ''),
            file_path=metadata.get('file_path', ''),
            reason=f"Matches forbidden pattern: {pattern}"
        ))
    
    # INFO: 已豁免违例
    for item_name, pattern in waived:
        metadata = self._metadata.get(item_name, {})
        waiver_reason = waive_items_dict.get(item_name, '')
        reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
        details.append(DetailItem(
            severity=Severity.INFO,
            name=item_name,
            line_number=metadata.get('line_number', ''),
            file_path=metadata.get('file_path', ''),
            reason=reason
        ))
    
    # INFO: 未匹配模式
    for pattern in unmatched_patterns:
        details.append(DetailItem(
            severity=Severity.INFO,
            name=pattern,
            line_number='',
            file_path='',
            reason="Pattern not found (good)"
        ))
    
    # WARN: 未使用豁免
    for item in unused_waivers:
        details.append(DetailItem(
            severity=Severity.WARN,
            name=item,
            line_number='',
            file_path='',
            reason="Waived item not found in check[WAIVER]"
        ))
    
    is_pass = (len(unwaived) == 0)
    
    # 创建分组
    error_groups = {}
    warn_groups = {}
    info_groups = {}
    
    if unwaived:
        error_groups["ERROR01"] = {
            "description": "Unwaived violations",
            "items": [item for item, _ in unwaived]
        }
    
    if unused_waivers:
        warn_groups["WARN01"] = {
            "description": "Unused waivers",
            "items": unused_waivers
        }
    
    info_items = []
    if waived:
        info_items.extend([item for item, _ in waived])
    if unmatched_patterns:
        info_items.extend(unmatched_patterns)
    
    if info_items:
        info_groups["INFO01"] = {
            "description": "Waived violations and unmatched patterns (good)",
            "items": info_items
        }
    
    return create_check_result(
        value=len(violations),
        is_pass=is_pass,
        has_pattern_items=True,
        has_waiver_value=True,
        details=details,
        error_groups=error_groups if error_groups else None,
        warn_groups=warn_groups if warn_groups else None,
        info_groups=info_groups if info_groups else None,
        item_desc=self.item_desc
    )
```

#### 步骤 9: Type 4 实现
```python
def _execute_type4(self, all_items: List[str], violations: List[Tuple[str, str]]) -> CheckResult:
    """Type 4: 布尔检查 + 豁免逻辑"""
    waivers = self.get_waivers()
    waive_items_dict = self._get_waive_items_with_reasons()
    waive_items = list(waive_items_dict.keys())
    
    # 分类违例（与 Type 3 类似）
    waive_set = set(waive_items)
    unwaived = [(item, pattern) for item, pattern in violations if item not in waive_set]
    waived = [(item, pattern) for item, pattern in violations if item in waive_set]
    
    violated_items = set(item for item, _ in violations)
    unused_waivers = [item for item in waive_items if item not in violated_items]
    
    details = []
    
    # ERROR: 未豁免违例
    for item_name, pattern in sorted(unwaived):
        metadata = self._metadata.get(item_name, {})
        details.append(DetailItem(
            severity=Severity.FAIL,
            name=item_name,
            line_number=metadata.get('line_number', ''),
            file_path=metadata.get('file_path', ''),
            reason=f"Violation found: {pattern}"
        ))
    
    # INFO: 已豁免违例
    for item_name, pattern in sorted(waived):
        metadata = self._metadata.get(item_name, {})
        waiver_reason = waive_items_dict.get(item_name, '')
        reason = f"{waiver_reason}[WAIVER]" if waiver_reason else "Waived[WAIVER]"
        details.append(DetailItem(
            severity=Severity.INFO,
            name=item_name,
            line_number=metadata.get('line_number', ''),
            file_path=metadata.get('file_path', ''),
            reason=reason
        ))
    
    # WARN: 未使用豁免
    for item in unused_waivers:
        details.append(DetailItem(
            severity=Severity.WARN,
            name=item,
            line_number='',
            file_path='',
            reason="Waived item not found in check[WAIVER]"
        ))
    
    is_pass = (len(unwaived) == 0)
    
    # 创建分组
    error_groups = {}
    warn_groups = {}
    info_groups = {}
    
    if unwaived:
        error_groups["ERROR01"] = {
            "description": "Unwaived violations",
            "items": [item for item, _ in sorted(unwaived)]
        }
    
    if unused_waivers:
        warn_groups["WARN01"] = {
            "description": "Unused waivers",
            "items": unused_waivers
        }
    
    if waived:
        info_groups["INFO01"] = {
            "description": "Waived violations (approved exceptions)",
            "items": [item for item, _ in sorted(waived)]
        }
    
    return create_check_result(
        value="N/A",
        is_pass=is_pass,
        has_pattern_items=False,
        has_waiver_value=True,
        details=details,
        error_groups=error_groups if error_groups else None,
        warn_groups=warn_groups if warn_groups else None,
        info_groups=info_groups if info_groups else None,
        item_desc=self.item_desc
    )
```

#### 步骤 10: 辅助方法
```python
def _get_waive_items_with_reasons(self) -> Dict[str, str]:
    """
    获取豁免项及原因
    
    Returns:
        Dict mapping waive_item to reason string
    """
    waivers = self.get_waivers()
    if not waivers:
        return {}
    
    waive_items = waivers.get('waive_items', [])
    
    # 如果是字典列表（包含 name 和 reason）
    if waive_items and isinstance(waive_items[0], dict):
        return {item['name']: item.get('reason', '') for item in waive_items}
    
    # 如果是简单列表
    return {item: '' for item in waive_items}
```

#### 步骤 11: 主入口
```python
if __name__ == '__main__':
    checker = MyChecker()
    checker.run()
```

---

## 输出格式

### Log 文件（分组格式）
**位置：** `Check_modules/[MODULE]/logs/[ITEM_ID].log`

**格式：**
```
PASS/FAIL:ITEM_ID:Description
ITEM_ID-ERROR01: Error description:
  Severity: Fail Occurrence: N
  - Item1
  - Item2

ITEM_ID-WARN01: Warning description:
  Severity: Warn Occurrence: N
  - Item1

ITEM_ID-INFO01: Info description:
  Severity: Info Occurrence: N
  - Item1
```

### Report 文件（详细列表）
**位置：** `Check_modules/[MODULE]/reports/[ITEM_ID].rpt`

**格式：**
```
PASS/FAIL:ITEM_ID:Description
Fail Occurrence: N
1: Fail: ItemName. In line X, file.rpt: Reason
2: Fail: ItemName. In line Y, file.rpt: Reason

Info Occurrence: N
1: Info: ItemName. In line X, file.rpt: Reason
```

---

## 参考示例

### 示例 1: IMP-5-0-0-00（库模型检查）
**检查目标：** 确认综合使用的所有库都存在且加载成功

**输入文件：** `qor.rpt`
```
Technology libraries: tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs 110
                      tcbn03e_bwp143mh117l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs 110
```

**配置（Type 1）：**
```yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: N/A
```

**解析逻辑：**
```python
def _extract_libraries_from_lines(self, lines: List[str], file_path: Path) -> List[str]:
    libraries = []
    in_tech_lib_section = False
    
    for line_num, line in enumerate(lines, 1):
        if 'Technology libraries:' in line:
            in_tech_lib_section = True
            # 检查同一行是否有库
            if ':' in line:
                parts = line.split(':', 1)[1].strip().split()
                if len(parts) >= 2:
                    lib_name = parts[0]
                    libraries.append(lib_name)
                    self._library_metadata[lib_name] = {
                        'line_number': line_num,
                        'file_path': str(file_path)
                    }
            continue
        
        if in_tech_lib_section:
            stripped = line.strip()
            if any(keyword in stripped for keyword in [
                'Operating conditions:', 'Interconnect mode:', 'Area mode:'
            ]):
                break
            
            if stripped and len(line) - len(line.lstrip()) > 10:
                parts = stripped.split()
                if len(parts) >= 2:
                    lib_name = parts[0]
                    libraries.append(lib_name)
                    self._library_metadata[lib_name] = {
                        'line_number': line_num,
                        'file_path': str(file_path)
                    }
    
    return libraries
```

---

### 示例 2: IMP-5-0-0-10（禁用单元检查）
**检查目标：** 确认综合网表中未使用 IMP-1-0-0-02 指定的禁用单元

**输入文件：** `gates.rpt`
```
INVD1BWP143M117H3P48CPDLVT  3  0.051  library  0
ND2D1BWP143M117H3P48CPDLVT  5  0.082  library  0
```

**参考配置：** `IMP-1-0-0-02.yaml`
```yaml
requirements:
  value: N/A
  pattern_items:
    - "*INVD1*"
    - "*ND2D1*"
```

**配置（Type 4）：**
```yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 2
  waive_items:
    - name: "INVD1BWP143M117H3P48CPDLVT"
      reason: "Required for critical timing path"
    - name: "ND2D1BWP143M117H3P48CPDLVT"
      reason: "Low power optimization approved"
```

**解析逻辑：**
```python
def _parse_gates_rpt(self) -> List[str]:
    all_cells = []
    for file_path_str in input_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, start=1):
                # 格式: "CELL_NAME  <number>"
                match = re.match(r'^(\S+)\s+\d+', line)
                if match:
                    cell_name = match.group(1)
                    all_cells.append(cell_name)
                    
                    if cell_name not in self._cell_metadata:
                        self._cell_metadata[cell_name] = {
                            'line_number': line_num,
                            'file_path': str(file_path)
                        }
    
    return all_cells

def _get_forbidden_cells_from_imp_1_0_0_02(self) -> List[str]:
    imp_1_path = self.root / "Check_modules" / "1.0_LIBRARY_CHECK" / "inputs" / "items" / "IMP-1-0-0-02.yaml"
    
    if not imp_1_path.exists():
        return []
    
    with open(imp_1_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if data and 'requirements' in data:
        pattern_items = data['requirements'].get('pattern_items', [])
        return pattern_items if pattern_items else []
    
    return []
```

---

## 执行流程

### 1. 单个 Checker 执行
```bash
cd Work
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial -check_module 5.0_SYNTHESIS_CHECK -check_item IMP-5-0-0-00
```

### 2. 模块级执行
```bash
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial -check_module 5.0_SYNTHESIS_CHECK
```

### 3. check_flowtool.py 核心逻辑
```python
# 1. 加载配置
item_yaml_path = check_modules_dir / module / "inputs" / "items" / f"{item_id}.yaml"

# 2. 初始化 Checker
checker = CheckerClass()
checker.init_checker(script_path)

# 3. 执行检查
result = checker.execute_check()

# 4. 写入输出
checker.write_output(result)

# 5. 更新总结
update_module_summary(module, item_id, result)
```

---

## 配置文件说明

### YAML 配置结构
```yaml
description: "检查描述"

requirements:
  value: N/A | 0 | >0              # 期望值
  pattern_items:                    # 匹配模式（Type 2/3）
    - "*pattern1*"
    - "^pattern2.*"

input_files: path/to/file.rpt      # 输入文件路径

waivers:
  value: N/A | 0 | >0               # 豁免数量
  waive_items:                      # 豁免列表
    - name: "ItemName"
      reason: "Reason and ticket"
```

### 类型判定规则
```
if requirements.value>0 AND pattern_items AND waivers.value>0:
    → Type 3
elif requirements.value>0 AND pattern_items:
    → Type 2
elif waivers.value>0:
    → Type 4
else:
    → Type 1
```

---

## 回归测试 (Regression Testing)

为了确保 Checker 的稳定性和兼容性，请使用自动化快照工具进行回归测试。

### 1. 创建/更新快照
使用 `create_all_snapshots.py` 运行 Checker 并生成基准快照：

```bash
python common/regression_testing/create_all_snapshots.py --modules {MODULE} --checkers {ITEM_ID} --force
```

此命令将：
- 执行 Checker 脚本
- 解析生成的 YAML 输出
- 在 `common/regression_testing/tests/data/snapshots.json` 中创建或更新快照
- 验证执行结果 (PASS/FAIL)

### 2. 验证快照
检查生成的快照数据是否符合预期：
- 打开 `common/regression_testing/tests/data/snapshots.json`
- 确认 `value`, `is_pass`, `info_groups`, `error_groups` 等字段正确

### 3. 运行回归测试
在修改代码后，运行验证脚本确保没有破坏现有功能：

```bash
python common/regression_testing/verify_all_snapshots.py --modules {MODULE}
```

## 最佳实践

### 1. 优先使用 Checker 模板
- **检查 `common.checker_templates`**: 在从头实现之前，先检查是否有现成的模板可用。
- **常用模板**:
  - `LogPatternChecker`: 适用于检查日志文件中是否存在特定模式（支持黑白名单）。
  - `ValueComparisonChecker`: 适用于提取数值并与阈值比较。
- **优势**: 减少重复代码，统一错误处理，自动适配新功能。

### 2. Checker 命名规范
- 文件名：`IMP-X-Y-Z-NN.py`
- 类名：`{Purpose}Checker`（如 `LibraryChecker`, `DontUseCellChecker`）

### 3. 错误处理
```python
# 文件不存在
if not file_path.exists():
    continue  # 跳过，不报错

# 解析错误
try:
    data = yaml.safe_load(f)
except Exception as e:
    print(f"Warning: Failed to load {file_path}: {e}")
    return []
```

### 3. 元数据存储
```python
# 存储每个项的元数据（行号、文件路径）
self._metadata[item_name] = {
    'line_number': line_num,
    'file_path': str(file_path)
}
```

### 4. 豁免匹配
- **Type 1/2**: 使用简单列表
- **Type 3/4**: 使用字典结构（name + reason）
- 匹配时使用精确名称或规范化名称

### 5. 输出描述
```python
# Type 3/4: 使用显式 error_groups 设置不同描述
error_groups = {
    "ERROR01": {
        "description": "Unwaived violations",
        "items": [...]
    }
}
warn_groups = {
    "WARN01": {
        "description": "Unused waivers",
        "items": [...]
    }
}
info_groups = {
    "INFO01": {
        "description": "Waived violations and unmatched patterns",
        "items": [...]
    }
}
```

---

## 调试技巧

### 1. 查看解析结果
```python
# 添加调试输出
print(f"DEBUG: Found {len(items)} items")
print(f"DEBUG: Violations: {violations}")
```

### 2. 检查配置加载
```python
requirements = self.get_requirements()
print(f"DEBUG: requirements={requirements}")

waivers = self.get_waivers()
print(f"DEBUG: waivers={waivers}")
```

### 3. 验证类型检测
```python
# 使用 BaseChecker 提供的 detect_checker_type()
checker_type = self.detect_checker_type()
print(f"DEBUG: Detected Type {checker_type}")
```

### 4. 删除 Cache 重新运行
```bash
Remove-Item Check_modules\5.0_SYNTHESIS_CHECK\inputs\.cache\*.json
Remove-Item Check_modules\5.0_SYNTHESIS_CHECK\outputs\.cache\*.pkl
```

---

## 常见问题

### Q1: 为什么 input_files 是空的？
**A**: 需要删除旧的 cache 文件并重新运行：
```bash
Remove-Item Check_modules\MODULE\inputs\.cache\ITEM_ID.json -Force
```

### Q2: 如何引用其他模块的配置？
**A**: 使用绝对路径读取：
```python
ref_path = self.root / "Check_modules" / "1.0_LIBRARY_CHECK" / "inputs" / "items" / "IMP-1-0-0-02.yaml"
with open(ref_path, 'r') as f:
    ref_data = yaml.safe_load(f)
```

### Q3: Type 3/4 的 ERROR/WARN/INFO 描述都一样？
**A**: 使用显式的 `error_groups`, `warn_groups`, `info_groups` 而不是 `default_group_desc`。

### Q4: 正则表达式不匹配？
**A**: 
- 通配符 `*` 会自动转换为 `.*`
- 使用 `re.search()` 而非 `re.match()`
- 特殊字符需要转义

---

## 总结

这个框架的核心设计理念：
1. **统一架构**：所有 Checker 继承自 `BaseChecker`
2. **自动检测**：根据配置自动判断使用哪种类型
3. **模块化**：解析、匹配、执行、输出分离
4. **灵活豁免**：支持精细的豁免管理和未使用豁免告警
5. **详细输出**：Log 分组 + Report 详细列表双重输出

遵循这个 prompt 的模式，可以快速开发新的 Checker 并确保与现有框架的一致性。
