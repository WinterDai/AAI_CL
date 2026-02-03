# Work Directory Usage Guide

## 概述

`Work` 目录是 CHECKLIST 框架的**集中执行目录**，提供统一的脚本接口来运行检查项、管理配置和查看结果。

## 目录结构

```
Work/
├── run.ps1                    # 主执行脚本（PowerShell）
├── run.sh                     # 主执行脚本（Bash - Linux/Mac）
├── config/                    # 执行配置
│   ├── execution_config.yaml  # 并行度、超时等设置
│   └── module_selection.yaml  # 模块/项目选择配置
├── results/                   # 执行结果输出
│   ├── latest/                # 最新一次运行结果
│   ├── history/               # 历史运行记录
│   └── reports/               # 汇总报告
└── logs/                      # 执行日志
```

---

## 核心脚本：run.ps1 / run.sh

### 基本用法

#### 1. 运行单个检查项

```powershell
# Windows PowerShell
.\run.ps1 -check_module "10.0_STA_DCD_CHECK" -check_item "IMP-10-0-0-00"

# Linux/Mac Bash
./run.sh --check-module "10.0_STA_DCD_CHECK" --check-item "IMP-10-0-0-00"
```

#### 2. 运行整个模块的所有检查项

```powershell
# 运行 10.0_STA_DCD_CHECK 模块
.\run.ps1 -check_module "10.0_STA_DCD_CHECK"
```

#### 3. 运行所有检查项（完整回归测试）

```powershell
# 运行所有已启用的检查项
.\run.ps1 -run_all

# 指定并行度
.\run.ps1 -run_all -parallel_level 4
```

#### 4. 跳过配置分发（测试时保留手动修改）

```powershell
# 在开发/调试阶段，避免覆盖手动修改的 YAML 配置
.\run.ps1 -check_item "IMP-10-0-0-00" -skip_distribution
```

---

## 参数说明

### run.ps1 参数（PowerShell）

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `-check_module` | String | 指定模块名称 | `"10.0_STA_DCD_CHECK"` |
| `-check_item` | String | 指定检查项名称 | `"IMP-10-0-0-00"` |
| `-run_all` | Switch | 运行所有检查项 | `-run_all` |
| `-parallel_level` | Int | 并行执行数量 | `-parallel_level 8` |
| `-skip_distribution` | Switch | 跳过配置分发 | `-skip_distribution` |
| `-dry_run` | Switch | 模拟运行（不实际执行） | `-dry_run` |
| `-verbose` | Switch | 详细输出 | `-verbose` |
| `-output_format` | String | 输出格式（json/html/text） | `-output_format json` |

### run.sh 参数（Bash）

```bash
./run.sh [OPTIONS]

Options:
  --check-module MODULE     指定模块名称
  --check-item ITEM         指定检查项名称
  --run-all                 运行所有检查项
  --parallel-level N        并行执行数量（默认：4）
  --skip-distribution       跳过配置分发
  --dry-run                 模拟运行
  --verbose                 详细输出
  --output-format FORMAT    输出格式（json/html/text）
  --help                    显示帮助信息
```

---

## 典型使用场景

### 场景 1：开发新检查项（本地测试）

```powershell
# Step 1: 进入 Work 目录
cd Work

# Step 2: 跳过配置分发，直接运行（保留手动修改的 YAML）
.\run.ps1 -check_item "IMP-10-0-0-00" -skip_distribution -verbose

# Step 3: 查看结果
cat results\latest\IMP-10-0-0-00\output.json
```

### 场景 2：Type 1/2/3/4 四种类型测试

```powershell
# 修改 Check_modules/10.0_STA_DCD_CHECK/inputs/items/IMP-10-0-0-00.yaml

# Type 1 测试
.\run.ps1 -check_item "IMP-10-0-0-00" -skip_distribution

# 修改 YAML 中的 requirements.value 和 waivers.value 后继续测试
# Type 2: requirements.value="consistent", waivers.value=N/A
# Type 3: requirements.value="consistent", waivers.value=1
# Type 4: requirements.value=N/A, waivers.value=1
```

### 场景 3：模块级回归测试

```powershell
# 测试整个 STA_DCD_CHECK 模块
.\run.ps1 -check_module "10.0_STA_DCD_CHECK" -parallel_level 8

# 查看汇总报告
cat results\latest\module_summary.html
```

### 场景 4：完整回归测试（CI/CD）

```powershell
# 运行所有检查项，生成 JSON 报告
.\run.ps1 -run_all -parallel_level 16 -output_format json

# 检查退出码
if ($LASTEXITCODE -ne 0) {
    Write-Error "Regression test failed!"
    exit 1
}
```

---

## 配置文件说明

### 1. execution_config.yaml

```yaml
# 执行配置
parallel:
  max_workers: 8              # 最大并行数
  timeout_seconds: 300        # 单个检查项超时时间
  
output:
  format: "json"              # 默认输出格式
  save_history: true          # 是否保存历史记录
  keep_last_n: 10             # 保留最近 N 次记录
  
logging:
  level: "INFO"               # 日志级别
  save_to_file: true          # 是否保存日志文件
```

### 2. module_selection.yaml

```yaml
# 模块和检查项选择配置
enabled_modules:
  - "10.0_STA_DCD_CHECK"
  - "20.0_DFT_CHECK"
  
disabled_items:
  - "IMP-10-0-0-99"          # 临时禁用的检查项
  
custom_groups:
  critical:                   # 自定义检查组
    - "IMP-10-0-0-00"
    - "IMP-10-0-0-01"
  optional:
    - "IMP-10-0-0-10"
```

---

## 结果输出结构

### 单个检查项结果

```
results/latest/IMP-10-0-0-00/
├── output.json              # JSON 格式结果
├── output.html              # HTML 格式结果
├── output.txt               # 文本格式结果
├── execution_log.txt        # 执行日志
└── config_snapshot.yaml     # 配置快照
```

### 汇总报告

```
results/latest/
├── module_summary.json      # 模块级汇总（JSON）
├── module_summary.html      # 模块级汇总（HTML）
├── regression_report.html   # 完整回归报告
└── pass_rate_chart.png      # 通过率图表
```

---

## 与 check_flowtool.py 的关系

`run.ps1` 和 `run.sh` 是对 `check_flowtool.py` 的封装：

```
Work/run.ps1 
    ↓
调用 Check_modules/common/check_flowtool.py
    ↓
执行 check_flowtool.run_checks()
    ↓
├── 发现检查项（模块扫描）
├── 分发配置文件（可选）
├── 并行/串行执行
└── 汇总结果
```

**为什么需要 Work 目录脚本？**
1. **统一入口**：避免直接调用 Python 脚本，提供友好的命令行接口
2. **配置管理**：集中管理执行配置和模块选择
3. **结果归档**：自动保存结果和历史记录
4. **CI/CD 集成**：提供标准化的自动化接口

---

## 最佳实践

### 1. 开发阶段

```powershell
# 使用 -skip_distribution 避免覆盖手动修改
.\run.ps1 -check_item "IMP-10-0-0-00" -skip_distribution -verbose
```

### 2. 提交前验证

```powershell
# 运行模块级测试
.\run.ps1 -check_module "10.0_STA_DCD_CHECK"
```

### 3. CI/CD 流水线

```powershell
# 完整回归测试
.\run.ps1 -run_all -parallel_level 16 -output_format json
if ($LASTEXITCODE -ne 0) { exit 1 }
```

### 4. 调试失败的检查项

```powershell
# 单独运行失败的检查项，查看详细日志
.\run.ps1 -check_item "IMP-10-0-0-00" -verbose
cat results\latest\IMP-10-0-0-00\execution_log.txt
```

---

## 常见问题

### Q1: 如何查看上一次运行结果？

```powershell
# 最新结果在 results/latest/
cat results\latest\module_summary.json

# 历史记录在 results/history/
ls results\history\
cat results\history\2025-12-11_14-30-00\module_summary.json
```

### Q2: 如何修改并行度？

```powershell
# 方法 1: 命令行参数
.\run.ps1 -run_all -parallel_level 16

# 方法 2: 修改 config/execution_config.yaml
# parallel.max_workers: 16
```

### Q3: 如何在不覆盖配置的情况下测试？

```powershell
# 使用 -skip_distribution 参数
.\run.ps1 -check_item "IMP-10-0-0-00" -skip_distribution
```

### Q4: 如何生成 HTML 报告？

```powershell
# 指定输出格式
.\run.ps1 -run_all -output_format html

# 查看报告
start results\latest\regression_report.html
```

---

## 总结

`Work` 目录提供了：
- ✅ **统一执行入口**：`run.ps1` / `run.sh`
- ✅ **灵活的参数控制**：模块/项目/全量运行
- ✅ **配置管理**：集中管理执行配置
- ✅ **结果归档**：自动保存历史记录
- ✅ **CI/CD 友好**：标准化接口和退出码

**推荐工作流**：
1. 开发时使用 `-skip_distribution` 进行本地测试
2. 提交前运行模块级测试验证
3. CI/CD 使用 `-run_all` 进行完整回归测试
