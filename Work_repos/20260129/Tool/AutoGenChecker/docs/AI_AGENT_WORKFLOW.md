# AI Agent 工作流程 - 智能Checker开发

## 🎯 核心理念

**开发者的工作：审查和微调AI生成的代码，而不是从零实现**

传统方式：
```
Manager分发 → 开发者实现解析逻辑 → 开发者实现4种type → 测试 → 修复
时间：2-4小时
```

AI Agent方式：
```
开发者运行AI Agent → AI分析文件+生成README+实现完整代码 → 开发者审查测试微调
时间：20-40分钟
```

---

## 📋 完整工作流

### 第一步：Manager分发任务

Manager使用 `work_dispatcher.py` 分发checker骨架：

```bash
cd Tool/Mdispatcher
python work_dispatcher.py --item-id IMP-10-0-0-09 --module 10.0_STA_DCD_CHECK --developer yuyin
```

这会生成：
- `Check_modules/10.0_STA_DCD_CHECK/inputs/items/IMP-10-0-0-09.yaml` - 配置文件
- `Check_modules/10.0_STA_DCD_CHECK/scripts/checker/IMP-10-0-0-09.py` - 代码骨架
- `Check_modules/10.0_STA_DCD_CHECK/scripts/doc/IMP-10-0-0-09_README.md` - README模板

### 第二步：开发者使用AI Agent

**重要：现在开发者不需要手动实现，而是让AI帮你完成！**

```bash
cd Tool/AutoGenChecker

# 🤖 使用智能AI Agent（推荐）
python cli.py generate \
    --item-id IMP-10-0-0-09 \
    --module 10.0_STA_DCD_CHECK \
    --ai-agent \
    --output-dir ../../Work/ai_generated
```

AI Agent会自动：

#### 1. 📄 解析YAML配置
```yaml
# IMP-10-0-0-09.yaml
description: Confirm no SPEF annotation issue in STA.
input_files:
  - C:\...\logs\sta_post_route.log
requirements:
  value: N/A
waivers:
  value: N/A
```

提取：
- ✅ 描述：用于README
- ✅ input_files：用于文件分析
- ✅ requirements/waivers：用于自动检测Type

#### 2. 🔍 AI分析真实文件

AI读取 `sta_post_route.log` 并分析：
```
SPEF file ./inputs/spef/xxx.spef.gz.
**WARN: (SPEF-1169): Invalid value of the parameter '$LAYER'...
End spef parsing (MEM=9114.92 CPU=0:00:48.7).
No not-annotated real net.
```

AI识别：
- 文件类型：`sta_log` / `spef_annotation_log`
- 关键模式：`**WARN: (SPEF-\d+):` 正则表达式
- 提取字段：警告代码、行号、描述
- 输出建议：INFO01=文件路径，ERROR01=SPEF警告详情

#### 3. 📝 AI生成完整README

基于 `DEVELOPER_TASK_PROMPTS.md` Step 2模板：

```markdown
# IMP-10-0-0-09 - SPEF Annotation Check

## Overview
- Category: Static Timing Analysis
- Input Files: sta_post_route.log
- Function: Validates SPEF file annotation has no critical errors

## Check Logic

### Input Parsing
Parse `sta_post_route.log` for:
- Search pattern: `**WARN: (SPEF-\d+):`
- Extract: error code, line number, message
- Count total warnings

### Detection Logic
1. Read log file line by line
2. Match regex: r'\*\*WARN: \(SPEF-(\d+)\):\s+(.+)'
3. Store warnings in list
4. Type 1: PASS if no warnings, FAIL if warnings found

## Configuration Examples

### Type 1: Informational Check
```yaml
requirements:
  value: N/A  # Boolean: any warning = FAIL
waivers:
  value: N/A  # No waivers
```
Behavior: Reports PASS/FAIL based on presence of SPEF warnings

### Type 2: Value Check
```yaml
requirements:
  value: 5  # Allow max 5 warnings
  pattern_items: ["SPEF-1169"]  # Specific warning codes to count
waivers:
  value: 0
```
Behavior: FAIL if warnings > 5

### Type 3: Value Check with Waivers
```yaml
requirements:
  value: 10
  pattern_items: ["SPEF-.*"]
waivers:
  value: 3
  waive_items:
    - name: "SPEF-1169"
      reason: "Known issue in IP library, safe to ignore"
```
Behavior: Allow 3 waived warnings, tag with [WAIVER]

### Type 4: Boolean with Waivers
```yaml
requirements:
  value: N/A
waivers:
  value: 1
  waive_items:
    - name: "entire_check"
      reason: "SPEF not critical for this design"
```
Behavior: Entire check can be waived

## Testing
...
```

#### 4. 💻 AI实现完整代码

**这是核心价值：AI生成真实可运行的代码！**

```python
################################################################################
# Script Name: IMP-10-0-0-09.py
#
# Purpose:
#   Confirm no SPEF annotation issue in STA.
#
# Logic:
#   - Parse sta_post_route.log for SPEF warning patterns
#   - Extract warning code (SPEF-xxxx) and description
#   - Count total warnings matching pattern_items
#   - Apply waiver logic if configured
#   - Return PASS if within threshold, FAIL otherwise
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A → Boolean check
#   ...
#
# Author: AutoGenChecker AI
# Date: 2025-12-10
################################################################################

from pathlib import Path
import sys
import re

# [标准路径设置代码...]

from base_checker import BaseChecker, CheckResult
from output_formatter import DetailItem, Severity, create_check_result


class Checker(BaseChecker):
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-09",
            item_desc="Confirm no SPEF annotation issue in STA."
        )
    
    def execute_check(self) -> CheckResult:
        checker_type = self.detect_checker_type()
        parsed_data = self._parse_files()
        
        if checker_type == 1:
            return self._execute_type1(parsed_data)
        elif checker_type == 2:
            return self._execute_type2(parsed_data)
        elif checker_type == 3:
            return self._execute_type3(parsed_data)
        else:
            return self._execute_type4(parsed_data)
    
    def _parse_files(self) -> dict:
        """Parse STA log for SPEF warnings."""
        warnings = []
        
        # 获取输入文件路径
        input_files = self.config.get('input_files', [])
        if not input_files:
            return {'warnings': [], 'errors': []}
        
        log_file = Path(input_files[0])
        if not log_file.exists():
            return {'warnings': [], 'errors': ['File not found: ' + str(log_file)]}
        
        # 解析SPEF警告
        spef_pattern = re.compile(r'\*\*WARN: \(SPEF-(\d+)\):\s+(.+)')
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    match = spef_pattern.search(line)
                    if match:
                        warnings.append({
                            'code': f'SPEF-{match.group(1)}',
                            'description': match.group(2).strip(),
                            'line': line_num,
                            'file': str(log_file),
                        })
        except Exception as e:
            return {'warnings': [], 'errors': [f'Parse error: {str(e)}']}
        
        return {'warnings': warnings, 'errors': []}
    
    def _execute_type1(self, parsed_data: dict) -> CheckResult:
        """Type 1: Boolean - any SPEF warning = FAIL."""
        warnings = parsed_data.get('warnings', [])
        errors = parsed_data.get('errors', [])
        
        if errors:
            # 文件读取错误
            return create_check_result(
                value="N/A",
                is_pass=False,
                has_pattern_items=False,
                has_waiver_value=False,
                details=[
                    DetailItem(
                        severity=Severity.ERROR,
                        info01=err,
                        info02="",
                    )
                    for err in errors
                ],
                item_desc=self.item_desc,
            )
        
        has_warnings = len(warnings) > 0
        
        details = [
            DetailItem(
                severity=Severity.WARN if has_warnings else Severity.INFO,
                info01=w['file'],
                info02=f"Line {w['line']}: {w['code']} - {w['description']}",
            )
            for w in warnings
        ]
        
        return create_check_result(
            value="N/A",
            is_pass=not has_warnings,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
        )
    
    def _execute_type2(self, parsed_data: dict) -> CheckResult:
        """Type 2: Value check - count warnings vs threshold."""
        warnings = parsed_data.get('warnings', [])
        
        # 获取pattern_items（要统计的警告类型）
        pattern_items = self.config.get('requirements', {}).get('pattern_items', [])
        threshold = self.config.get('requirements', {}).get('value', 0)
        
        # 过滤匹配的警告
        if pattern_items:
            matched_warnings = [
                w for w in warnings
                if any(re.match(pattern, w['code']) for pattern in pattern_items)
            ]
        else:
            matched_warnings = warnings
        
        actual_count = len(matched_warnings)
        is_pass = actual_count <= threshold
        
        details = [
            DetailItem(
                severity=Severity.WARN if not is_pass else Severity.INFO,
                info01=w['code'],
                info02=f"{w['description']} (line {w['line']})",
            )
            for w in matched_warnings
        ]
        
        return create_check_result(
            value=str(actual_count),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
        )
    
    def _execute_type3(self, parsed_data: dict) -> CheckResult:
        """Type 3: Value check with waiver logic."""
        # [完整实现，包括豁免匹配、[WAIVER]标签等...]
        pass  # AI会填充完整逻辑
    
    def _execute_type4(self, parsed_data: dict) -> CheckResult:
        """Type 4: Boolean with waiver logic."""
        # [完整实现...]
        pass


if __name__ == '__main__':
    checker = Checker()
    checker.run()
```

**注意：AI生成的是完整可运行的代码，不是TODO模板！**

---

### 第三步：开发者审查和微调

开发者的工作（20-40分钟）：

1. **审查README（5分钟）**
   - 检查描述是否准确
   - 验证4种Type示例是否合理
   - 补充测试说明

2. **测试代码（10分钟）**
   ```bash
   # 运行checker
   python Check_modules/10.0_STA_DCD_CHECK/scripts/checker/IMP-10-0-0-09.py
   
   # 检查输出
   cat Work/CheckList.rpt
   ```

3. **微调解析逻辑（如需要，5-15分钟）**
   - 如果正则表达式不够精确
   - 如果需要处理特殊格式
   - 如果需要额外的边界检查

4. **完善豁免逻辑（如需要，5-10分钟）**
   - 验证Type 3/4的豁免匹配
   - 确认[WAIVER]标签正确应用

5. **回归测试**
   ```bash
   python common/regression_testing/create_all_snapshots.py
   ```

---

## 🆚 对比：传统vs AI Agent

### 传统方式

```python
def _parse_files(self) -> dict:
    """Parse input files."""
    # TODO: Implement parsing logic based on file analysis
    return {'items': []}
```

开发者需要：
1. 自己阅读文件找规律
2. 编写正则表达式
3. 处理边界情况
4. 实现数据提取
⏱️ **时间：30-60分钟**

### AI Agent方式

```python
def _parse_files(self) -> dict:
    """Parse STA log for SPEF warnings."""
    warnings = []
    
    # AI已经实现：
    # - 文件路径处理
    # - 正则表达式匹配
    # - 错误处理
    # - 数据结构返回
    
    spef_pattern = re.compile(r'\*\*WARN: \(SPEF-(\d+)\):\s+(.+)')
    # ... 完整实现 ...
    
    return {'warnings': warnings, 'errors': []}
```

开发者需要：
1. 审查AI的正则是否准确
2. 测试几个case
3. 微调（如需要）
⏱️ **时间：5-10分钟**

---

## 💡 最佳实践

### 1. 准备好测试数据

在运行AI Agent前，确保input_files存在：
```bash
# 检查文件
ls IP_project_folder/logs/sta_post_route.log
```

### 2. 使用正确的LLM

```bash
# OpenAI GPT-4 (推荐，代码质量最高)
python cli.py generate --item-id X --module Y --ai-agent --llm-provider openai

# Anthropic Claude (推荐，上下文理解好)
python cli.py generate --item-id X --module Y --ai-agent --llm-provider anthropic
```

### 3. 审查AI输出

AI很强大但不完美，重点检查：
- ✅ 正则表达式是否匹配实际格式
- ✅ 边界情况处理（空文件、格式变化）
- ✅ 输出格式（INFO01/INFO02/ERROR01）
- ✅ 豁免逻辑的name vs reason字段

### 4. 迭代改进

如果第一次生成不满意：
```bash
# 重新运行，可能得到不同结果
python cli.py generate --item-id X --module Y --ai-agent

# 或者手动调整prompt（在intelligent_agent.py中）
```

---

## 📊 效率提升

| 任务 | 传统开发 | AI Agent | 节省 |
|------|---------|----------|------|
| 理解文件格式 | 15-20分钟 | AI自动分析 | 15分钟 |
| 编写README | 20-30分钟 | AI生成+审查(5分钟) | 20分钟 |
| 实现_parse_files() | 30-60分钟 | AI生成+测试(10分钟) | 40分钟 |
| 实现4种Type | 40-60分钟 | AI生成+审查(10分钟) | 45分钟 |
| **总计** | **2-3小时** | **30-40分钟** | **70%时间** |

---

## 🎯 总结

**新的开发模式：**

```
Manager分发 
  ↓
开发者运行: python cli.py generate --ai-agent ...
  ↓
AI分析文件 → AI写README → AI实现完整代码
  ↓
开发者审查、测试、微调（20-40分钟）
  ↓
完成！
```

**开发者角色转变：**
- ❌ 不再是：从零编写解析逻辑
- ✅ 现在是：审查和优化AI生成的代码

**这才是真正的AI辅助开发！** 🚀
