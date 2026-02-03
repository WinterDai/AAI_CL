# Validation Report: IMP-10-0-0-00

**Generated:** 2025-12-31 17:03:45

**Status:** success

---

## 目录结构

```
IMP-10-0-0-00/
├── README.md                          # 本文档
├── input/
│   ├── item.yaml                      # 原始 Item 配置
│   ├── item_spec.json                 # Item 规格
│   └── generated_checker.py           # 待验证代码
├── test_cases/
│   └── {item_id}_type{N}_{direction}.yaml
├── execution/                         # ValidationAgent 中间数据
│   ├── logs/
│   │   └── TC_{NN}_{item_id}.log
│   └── reports/
│       └── TC_{NN}_{item_id}.rpt
├── checker_outputs/                   # checker.py 真实执行输出
│   ├── logs/
│   │   └── {item_id}.log              # OutputFormatter 格式
│   ├── reports/
│   │   └── {item_id}.rpt
│   └── cache/
│       └── {item_id}.pkl              # CheckResult 对象
├── results/
│   ├── validation_result.json
│   ├── validation_report.md
│   └── feedback_to_codegen.json
└── archive/
    └── {timestamp}/
```

---

## 完整路径清单

### Input 文件

| 文件 | 路径 | 说明 |
|------|------|------|
| item.yaml | `input\item.yaml` | 原始 Item 配置 |
| item_spec.json | `input\item_spec.json` | Item 规格 (来自 ContextAgent) |
| generated_checker.py | `input\generated_checker.py` | 待验证代码 |

**原始 item.yaml 来源:** `C:\Users\wentao\AAI_local\AAI\Main_Work\ACL\CHECKLIST\Tool\Agent\test\Check_modules\10.0_STA_DCD_CHECK\inputs\items\IMP-10-0-0-00.yaml`

### TestCase 文件

| TestCase ID | Type | Direction | 路径 |
|-------------|------|-----------|------|
| TC_01 | Type 1 | positive | `test_cases\IMP-10-0-0-00_type1_positive.yaml` |
| TC_02 | Type 1 | negative | `test_cases\IMP-10-0-0-00_type1_negative.yaml` |
| TC_03 | Type 2 | positive | `test_cases\IMP-10-0-0-00_type2_positive.yaml` |
| TC_04 | Type 2 | negative | `test_cases\IMP-10-0-0-00_type2_negative.yaml` |
| TC_05 | Type 3 | positive | `test_cases\IMP-10-0-0-00_type3_positive.yaml` |
| TC_06 | Type 3 | negative | `test_cases\IMP-10-0-0-00_type3_negative.yaml` |
| TC_07 | Type 4 | positive | `test_cases\IMP-10-0-0-00_type4_positive.yaml` |
| TC_08 | Type 4 | negative | `test_cases\IMP-10-0-0-00_type4_negative.yaml` |

### Execution 输出

#### Logs

| TestCase | 路径 |
|----------|------|
| TC_01 | `execution\logs\TC_01_IMP-10-0-0-00.log` |
| TC_02 | `execution\logs\TC_02_IMP-10-0-0-00.log` |
| TC_03 | `execution\logs\TC_03_IMP-10-0-0-00.log` |
| TC_04 | `execution\logs\TC_04_IMP-10-0-0-00.log` |
| TC_05 | `execution\logs\TC_05_IMP-10-0-0-00.log` |
| TC_06 | `execution\logs\TC_06_IMP-10-0-0-00.log` |
| TC_07 | `execution\logs\TC_07_IMP-10-0-0-00.log` |
| TC_08 | `execution\logs\TC_08_IMP-10-0-0-00.log` |

#### Reports

| TestCase | 路径 |
|----------|------|
| TC_01 | `execution\reports\TC_01_IMP-10-0-0-00.rpt` |
| TC_02 | `execution\reports\TC_02_IMP-10-0-0-00.rpt` |
| TC_03 | `execution\reports\TC_03_IMP-10-0-0-00.rpt` |
| TC_04 | `execution\reports\TC_04_IMP-10-0-0-00.rpt` |
| TC_05 | `execution\reports\TC_05_IMP-10-0-0-00.rpt` |
| TC_06 | `execution\reports\TC_06_IMP-10-0-0-00.rpt` |
| TC_07 | `execution\reports\TC_07_IMP-10-0-0-00.rpt` |
| TC_08 | `execution\reports\TC_08_IMP-10-0-0-00.rpt` |

### Results 文件

| 文件 | 路径 | 说明 |
|------|------|------|
| validation_result.json | `results\validation_result.json` | 结构化验证结果 |

### Checker 真实执行输出

*checker.py 执行产生的 OutputFormatter 格式输出*

| 类型 | 文件 | 路径 |
|------|------|------|
| Log | IMP-10-0-0-00.log | `checker_outputs\logs\IMP-10-0-0-00.log` |
| Report | IMP-10-0-0-00.rpt | `checker_outputs\reports\IMP-10-0-0-00.rpt` |
| CheckResult | IMP-10-0-0-00.pkl | `checker_outputs\cache\IMP-10-0-0-00.pkl` |

---

## 执行结果摘要

- **总测试数:** 8
- **CORRECT:** 8
- **INCORRECT:** 0
- **UNCERTAIN:** 0
- **TESTCASE_INVALID:** 0

### 详细结果

| TestCase | 预期 | 实际 | 判定 |
|----------|------|------|------|
| TC_01 | PASS | PASS | ✅ CORRECT |
| TC_02 | FAIL | FAIL | ✅ CORRECT |
| TC_03 | PASS | PASS | ✅ CORRECT |
| TC_04 | FAIL | FAIL | ✅ CORRECT |
| TC_05 | WAIVER | WAIVER | ✅ CORRECT |
| TC_06 | FAIL | FAIL | ✅ CORRECT |
| TC_07 | FAIL | FAIL | ✅ CORRECT |
| TC_08 | FAIL | FAIL | ✅ CORRECT |

---

## 历史存档

| 时间戳 | 路径 |
|--------|------|
| 20251231_170345 | `archive\20251231_170345/` |
| 20251231_170326 | `archive\20251231_170326/` |
| 20251231_152118 | `archive\20251231_152118/` |
| 20251231_151805 | `archive\20251231_151805/` |
| 20251231_150119 | `archive\20251231_150119/` |
| 20251231_150025 | `archive\20251231_150025/` |
| 20251231_145932 | `archive\20251231_145932/` |

---

*此文档由 ValidationAgent OutputManager 自动生成*