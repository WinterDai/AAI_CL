# Validation Report: IMP-10-0-0-00

**Generated:** 2025-12-31 15:00:26

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
├── execution/
│   ├── logs/
│   │   └── TC_{NN}_{item_id}.log
│   └── reports/
│       └── TC_{NN}_{item_id}.rpt
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

*暂无 TestCase 文件*

### Execution 输出

*暂无执行输出*

### Results 文件

| 文件 | 路径 | 说明 |
|------|------|------|
| validation_result.json | `results\validation_result.json` | 结构化验证结果 |

---

## 历史存档

| 时间戳 | 路径 |
|--------|------|
| 20251231_150025 | `archive\20251231_150025/` |
| 20251231_145932 | `archive\20251231_145932/` |

---

*此文档由 ValidationAgent OutputManager 自动生成*