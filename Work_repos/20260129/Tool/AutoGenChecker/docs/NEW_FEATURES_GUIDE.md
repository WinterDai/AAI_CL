# AutoGenChecker新功能使用指南 v1.0

## 概述

本文档介绍AutoGenChecker框架新增的5大特性，提升checker开发和测试效率。

---

## 特性一：交互式README生成 (Phase 1)

### 功能描述
- 在AI生成README前，允许用户提供domain-specific hints
- 支持交互模式（命令行提示输入）和脚本模式（参数传递）
- Hints自动保存到JSON文件，支持历史记录追溯
- AI将hints整合到README生成prompt中

### 使用方法

#### 方法1：交互模式（默认）
```bash
python cli.py generate --ai-agent --item-id IMP-15-0-0-03 --module 15.0_ESD_PERC_CHECK
```

系统会提示：
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   📝 README Generation - User Hints                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Item ID: IMP-15-0-0-03
Module: 15.0_ESD_PERC_CHECK
Description: PERC voltage setting check

Input Files:
  - voltage.txt
  - voltage_map.txt

Please provide hints for README generation (e.g., check purpose, key patterns, edge cases).
Press Enter twice to finish, or Ctrl+C to skip.

Your hints:
>
```

输入示例：
```
Check Purpose:
- Verify voltage_map entries match voltage.txt for TT corner DDRIO libraries
- Focus on TT corner and DDRIO library filtering

Key Patterns:
- voltage_map format: [domain]=[voltage]v
- voltage.txt format: domain voltage

Edge Cases:
- Some libraries may not have voltage_map entries
- TT corner regex: /TT|typ/
```

#### 方法2：脚本模式（参数传递）
```bash
python cli.py generate --ai-agent \
  --item-id IMP-15-0-0-03 \
  --module 15.0_ESD_PERC_CHECK \
  --readme-hints "Check voltage_map entries match voltage.txt for TT corner DDRIO libraries"
```

### Hints存储位置
```
Work/phase-1-dev/{item_id}/user_hints.json
```

格式：
```json
{
  "item_id": "IMP-15-0-0-03",
  "history": [
    {
      "timestamp": "2025-12-26T15:30:00",
      "hints": "Check voltage_map entries...",
      "author": "yuyin"
    }
  ],
  "latest": {
    "timestamp": "2025-12-26T15:30:00",
    "hints": "Check voltage_map entries...",
    "author": "yuyin"
  }
}
```

---

## 特性二：全面测试自动化 (Phase 2-3)

### 功能描述
- 自动生成6种测试配置（覆盖所有checker类型）
- 批量执行测试并捕获输出
- 生成合并报告（Markdown + HTML）

### 6种测试类型

| 测试类型 | 描述 | 目的 |
|---------|------|------|
| type1_na | Type 1 无数据 | 测试input file为空/缺失场景 |
| type1_w0 | Type 1 waivers.value=0 | 测试强制PASS模式 |
| type2 | Type 2 标准检查 | 测试pattern value check |
| type3 | Type 3 带waivers | 测试waiver逻辑 |
| type4 | Type 4 全部失败 | 测试错误处理 |
| type4_all | Type 4 混合 | 测试PASS+WAIVED+ERROR混合 |

### 使用方法

#### 方法1：随AI agent生成checker时自动测试
```bash
python cli.py generate --ai-agent \
  --item-id IMP-9-0-0-07 \
  --module 9.0_RC_EXTRACTION_CHECK \
  --full-test
```

执行流程：
1. 生成README（含hints）
2. 生成checker代码
3. 自动生成6种测试配置
4. 批量运行测试
5. 生成综合测试报告

#### 方法2：单独运行测试（对已有checker）
```bash
# Step 1: 生成测试配置
cd Tool/AutoGenChecker
python workflow/test_generator.py IMP-9-0-0-07 9.0_RC_EXTRACTION_CHECK

# Step 2: 运行所有测试
python workflow/test_runner.py IMP-9-0-0-07 9.0_RC_EXTRACTION_CHECK

# Step 3: 生成报告
python workflow/result_merger.py Work/test_results/IMP-9-0-0-07/20250126_143052
```

#### 方法3：运行单个测试
```bash
python workflow/test_runner.py IMP-9-0-0-07 9.0_RC_EXTRACTION_CHECK type1_na
```

### 输出位置
```
Work/
├── test_configs/{item_id}/          # 测试配置
│   ├── type1_na.yaml
│   ├── type1_w0.yaml
│   ├── type2.yaml
│   ├── type3.yaml
│   ├── type4.yaml
│   ├── type4_all.yaml
│   └── manifest.json
│
└── test_results/{item_id}/{timestamp}/  # 测试结果
    ├── test_results.json            # 汇总JSON
    ├── type1_na_output.txt          # 各测试输出
    ├── type1_w0_output.txt
    ├── ...
    ├── consolidated_report.md       # Markdown报告
    └── consolidated_report.html     # HTML报告
```

### 测试报告示例
```markdown
# Test Report: IMP-9-0-0-07

**Generated:** 2025-12-26T15:45:00
**Module:** 9.0_RC_EXTRACTION_CHECK
**Checker:** `Check_modules/.../IMP-9-0-0-07.py`

---

## Summary

- **Total Tests:** 6
- **Passed:** 5
- **Failed:** 1
- **Skipped:** 0
- **Pass Rate:** 83.3%
- **Total Time:** 12.5s

---

## Test Results

### ✅ type1_na
- **Status:** PASS
- **Execution Time:** 2.1s

### ❌ type4
- **Status:** ERROR
- **Execution Time:** 2.3s

**Errors:**
```
TypeError: ...
```

📄 [Full Output](type4_output.txt)
```

---

## 特性三：Baseline管理 (Phase 4)

### 功能描述
- 保存测试结果作为baseline
- 支持baseline历史追溯
- Checksum完整性验证
- 用于regression testing对比基准

### 使用方法

#### 保存baseline
```bash
# 方法1: 随测试一起保存
python cli.py generate --ai-agent \
  --item-id IMP-9-0-0-07 \
  --module 9.0_RC_EXTRACTION_CHECK \
  --full-test \
  --save-baseline

# 方法2: 单独保存
python workflow/baseline_manager.py save \
  IMP-9-0-0-07 \
  Work/test_results/IMP-9-0-0-07/20250126_143052 \
  "Initial stable baseline"
```

#### 查看baseline
```bash
python workflow/baseline_manager.py list IMP-9-0-0-07
```

输出：
```
📦 Baseline for IMP-9-0-0-07
================================================================================
Created: 2025-12-26T15:45:00
Author: yuyin
Description: Initial stable baseline

Test Summary:
  Total Tests: 6
  Passed: 6
  Failed: 0
  Pass Rate: 100%

Test Types: type1_na, type1_w0, type2, type3, type4, type4_all

✅ Baseline integrity verified
```

#### 加载baseline（代码）
```python
from workflow.baseline_manager import load_baseline

baseline = load_baseline("IMP-9-0-0-07")
if baseline:
    print(f"Baseline pass rate: {baseline['summary']['pass_rate']}")
```

### 存储位置
```
test_baseline/{item_id}/
├── manifest.json             # Baseline元数据
├── test_results.json         # 测试结果
├── type1_na_output.txt       # 各测试输出
├── consolidated_report.md    # 报告副本
└── ...
```

---

## 特性四：Regression测试 (Phase 5)

### 功能描述
- 智能对比当前结果与baseline
- 忽略时间戳、行号等无关差异
- 聚焦status变化、item count变化、error message
- 自动检测regression（PASS→FAIL）和improvement（FAIL→PASS）
- 生成detailed regression report

### 使用方法

#### 方法1：随测试一起运行regression
```bash
python cli.py generate --ai-agent \
  --item-id IMP-9-0-0-07 \
  --module 9.0_RC_EXTRACTION_CHECK \
  --full-test \
  --regression
```

前提：必须先有baseline（使用`--save-baseline`创建）

#### 方法2：单独运行regression test
```bash
# Step 1: 运行测试
python workflow/test_runner.py IMP-9-0-0-07 9.0_RC_EXTRACTION_CHECK

# Step 2: 运行regression对比
python workflow/regression_diff.py \
  IMP-9-0-0-07 \
  Work/test_results/IMP-9-0-0-07/20250126_153000

# Step 3: 生成报告
python workflow/regression_reporter.py \
  Work/test_results/IMP-9-0-0-07/20250126_153000/regression_diff.json
```

### Regression报告示例

```markdown
# Regression Test Report: IMP-9-0-0-07

**Generated:** 2025-12-26T15:45:00
**Overall Status:** ❌ **REGRESSION** (New failures detected)

---

## Executive Summary

### Baseline
- **Created:** 2025-12-26T10:00:00
- **Description:** Initial stable baseline
- **Pass Rate:** 100%

### Current Run
- **Total Tests:** 6
- **Pass Rate:** 83.3%
- **Pass Rate Change:** -16.7% 📉 (Regression)

---

## ❌ Regressions Detected

**Count:** 1

### 🔴 Critical Regressions

- **type2**: PASS → ERROR (Severity: CRITICAL)

---

## Conclusion

⚠️ **Action Required:** Regressions detected in this test run.

**Recommended Actions:**
1. Review regression details above
2. Investigate root cause of status changes
3. Fix critical and high priority regressions first
4. Re-run tests after fixes
5. Update baseline once all regressions resolved
```

### 智能Diff特性

regression_diff.py会忽略：
- 时间戳（所有格式）
- 行号（"line 123"）
- 执行时间（"2.5s", "2.5 seconds"）
- 内存地址（"0x7fff..."）

专注于：
- Status变化（PASS↔ERROR↔FAIL）
- Item count变化（INFO01: 3 → 5）
- Error message内容变化

---

## 特性五：批量处理 (Phase 6)

### 功能描述
- 批量生成多个checker
- 批量运行测试
- 批量regression测试

### 使用方法

#### 批量生成（使用配置文件）
创建`batch_config.yaml`:
```yaml
checkers:
  - item_id: IMP-9-0-0-07
    module: 9.0_RC_EXTRACTION_CHECK
    hints: "QRC warning count check"
  
  - item_id: IMP-15-0-0-01
    module: 15.0_ESD_PERC_CHECK
    hints: "CNOD requirement check"
  
  - item_id: IMP-15-0-0-02
    module: 15.0_ESD_PERC_CHECK
    hints: "PERC voltage validation"

options:
  full_test: true
  save_baseline: true
  regression: false
```

运行：
```bash
# 批量生成（依次执行）
for item in IMP-9-0-0-07 IMP-15-0-0-01 IMP-15-0-0-02; do
  python cli.py generate --ai-agent \
    --item-id $item \
    --module <module_name> \
    --full-test \
    --save-baseline
done
```

#### 批量测试（对已有checkers）
```bash
# 使用Shell脚本
for item in IMP-9-0-0-07 IMP-15-0-0-01 IMP-15-0-0-02; do
  echo "Testing $item..."
  python workflow/test_generator.py $item <module>
  python workflow/test_runner.py $item <module>
done
```

---

## 完整工作流示例

### 场景：新checker开发 + 完整测试 + baseline建立

```bash
# Step 1: 生成checker（带hints，带测试）
python cli.py generate --ai-agent \
  --item-id IMP-NEW-CHECKER \
  --module XX.X_CHECK \
  --full-test \
  --save-baseline

# 输出：
# 1. Checker代码: Check_modules/.../IMP-NEW-CHECKER.py
# 2. README: Check_modules/.../IMP-NEW-CHECKER_README.md
# 3. 6个测试配置: Work/test_configs/IMP-NEW-CHECKER/
# 4. 测试结果: Work/test_results/IMP-NEW-CHECKER/{timestamp}/
# 5. Baseline: test_baseline/IMP-NEW-CHECKER/

# Step 2: 修改checker后重新测试
python workflow/test_runner.py IMP-NEW-CHECKER XX.X_CHECK

# Step 3: 运行regression测试
python workflow/regression_diff.py \
  IMP-NEW-CHECKER \
  Work/test_results/IMP-NEW-CHECKER/{new_timestamp}

python workflow/regression_reporter.py \
  Work/test_results/IMP-NEW-CHECKER/{new_timestamp}/regression_diff.json

# Step 4: 如果无regression，更新baseline
python workflow/baseline_manager.py save \
  IMP-NEW-CHECKER \
  Work/test_results/IMP-NEW-CHECKER/{new_timestamp} \
  "Updated after bug fix"
```

---

## 目录结构总览

```
Tool/AutoGenChecker/
├── cli.py                    # 主入口（新增--readme-hints, --full-test, --regression）
├── utils/
│   └── hints_manager.py      # [NEW] Hints管理
├── workflow/
│   ├── intelligent_agent.py  # [UPDATED] 支持hints参数
│   ├── user_interaction.py   # [NEW] 交互式hints收集
│   ├── test_generator.py     # [NEW] 6种测试配置生成
│   ├── test_runner.py        # [NEW] 测试执行引擎
│   ├── result_merger.py      # [NEW] 结果合并报告
│   ├── baseline_manager.py   # [NEW] Baseline管理
│   ├── regression_diff.py    # [NEW] 智能diff引擎
│   └── regression_reporter.py # [NEW] Regression报告生成
└── test_phase1.py            # [NEW] Phase 1测试脚本

Work/
├── phase-1-dev/{item_id}/
│   └── user_hints.json       # Hints历史记录
├── test_configs/{item_id}/   # 测试配置
├── test_results/{item_id}/{timestamp}/  # 测试结果
└── ...

test_baseline/{item_id}/      # Baseline存储
```

---

## 常见问题 (FAQ)

### Q1: 如何跳过hints提示直接生成？
A: 在交互提示时按Ctrl+C跳过，或使用`--readme-hints ""`提供空hints。

### Q2: 测试失败怎么办？
A: 查看`Work/test_results/{item_id}/{timestamp}/{test_type}_output.txt`获取详细输出，修复checker代码后重新测试。

### Q3: 如何更新baseline？
A: 使用`baseline_manager.py save`命令覆盖现有baseline，会保留历史版本信息在manifest.json中。

### Q4: Regression测试需要什么前提？
A: 必须先有baseline。首次运行时使用`--save-baseline`创建baseline，后续运行才能使用`--regression`。

### Q5: 如何批量处理多个checker？
A: 使用Shell循环或编写Python脚本调用CLI命令，逐个处理。

---

## 版本历史

- **v1.0** (2025-12-26): 初始版本
  - Phase 1: Interactive README hints
  - Phase 2-3: 6-type test automation
  - Phase 4: Baseline management
  - Phase 5: Regression testing
  - Phase 6: Batch processing support

---

## 技术支持

如有问题，请联系：yuyin@cadence.com
