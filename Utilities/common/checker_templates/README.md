# Checker Templates - 可复用组件库 / Reusable Checker Components

## 📚 Documentation Quick Access

**🆕 OutputBuilderTemplate v2.0** - Unified API for building CheckResult outputs

| Document | Purpose | Target Audience |
|----------|---------|-----------------|
| **[🔖 QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | **ONE-PAGE CHEAT SHEET** 🖨️ | Quick lookup |
| **[TEMPLATE_USAGE_GUIDE.md](TEMPLATE_USAGE_GUIDE.md)** | 👈 **START HERE** - Complete usage guide | All developers |
| **[API_V2_MIGRATION_GUIDE.md](API_V2_MIGRATION_GUIDE.md)** | v1.x→v2.0 migration guide | Existing users |
| **[output_builder_template.py](output_builder_template.py)** | Source code with inline docs | Advanced users |

**Quick Links**:
- [⚡ Quick Reference Card](QUICK_REFERENCE.md) - Print-friendly one-pager
- [Quick Start Example](TEMPLATE_USAGE_GUIDE.md#quick-start)
- [Common Patterns](TEMPLATE_USAGE_GUIDE.md#common-patterns)
- [Troubleshooting](TEMPLATE_USAGE_GUIDE.md#troubleshooting)
- [What's New in v2.0](API_V2_MIGRATION_GUIDE.md)

---

## 概述 / Overview

这个目录包含从实际项目中提取的、经过验证的可复用 checker 组件。所有模板都基于真实代码，确保可靠性和实用性。

This directory contains verified, reusable checker components extracted from production code.

**提取自以下已验证的 checkers:**

- IMP-10-0-0-10: 模式匹配、文件路径提取、waiver处理、输出构建
- IMP-5-0-0-01: 文件引用提取 (.lef, .tlef)
- IMP-5-0-0-02: 多阶段链式提取 (domain→rc_corner→qrc_tech)
- IMP-5-0-0-05: 基于章节的解析 (Check Design Report)
- IMP-5-0-0-07: 结构化块提取 (create_delay_corner)
- IMP-6-0-0-02: 简单列表提取
- IMP-13-0-0-00: 命令提取

## 模板概览


| 模板                      | 功能                | 代码行数 | 模式数量 | 代码减少 |
| ------------------------- | ------------------- | -------- | -------- | -------- |
| **InputFileParserMixin**  | 输入文件解析        | 943 行   | 7 种模式 | ~60%     |
| **WaiverHandlerMixin** | Waiver 处理逻辑 | 567 行   | 8 种模式 | ~50%     |
| **OutputBuilderMixin** | 输出结果构建    | 606 行   | 6 种模式 | ~70%     |

**IMP-10-0-0-10 重构效果:** 684 行 → 402 行 (-282 行, **-41.2%**)

## 可用模板

### 1. InputFileParserMixin - 输入文件解析（v2.0.0）

**支持 7 种解析模式，覆盖 90% 的日志解析场景**

#### 模式 1: 简单模式匹配 (Pattern Matching)

**适用场景：** 搜索特定关键字、正则表达式

**来源：** IMP-10-0-0-10

```python
from checker_templates.input_file_parser_template import InputFileParserMixin

class MyChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        patterns = {
            'in2out': r'_(in2out)_|timing_in2out',
            'in2reg': r'_(in2reg)_|timing_in2reg',
        }
      
        return self.parse_log_with_patterns(
            log_file=self.input_files[0],
            patterns=patterns
        )
```

#### 工具方法: 命令规范化 (Command Normalization)

**适用场景：** 统一命令格式，用于匹配和去重

**来源：** IMP-10-0-0-02

```python
class SDCChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        # 规范化命令格式以便匹配
        cmd1 = "set_clock_uncertainty 0.02 -hold -from [get_clocks { PHASE_ALIGN_CLOCK}]"
        cmd2 = "set_clock_uncertainty 0.02 -hold -from [get_clocks {PHASE_ALIGN_CLOCK}]"
        
        # 使用 normalize_command 统一格式
        normalized1 = self.normalize_command(cmd1)
        normalized2 = self.normalize_command(cmd2)
        # normalized1 == normalized2  # True
        
        # 常用于 waiver 匹配的 normalizer 参数
        matched = self.match_waiver_entry(
            item=cmd1,
            waive_dict=waive_items,
            normalizer=self.normalize_command  # 传入作为 normalizer
        )
```

#### 模式 2: 文件引用提取 (File Reference Extraction)

**适用场景：** 提取 .lef, .tlef, .qrc, .lib 等文件引用

**来源：** IMP-5-0-0-01, IMP-5-0-0-02

```python
class LEFChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        # 提取所有 .lef 和 .tlef 文件
        result = self.extract_file_references(
            log_file=self.input_files[0],
            extensions=['.lef', '.tlef']
        )
        return result['files']  # ['tech.lef', 'macro.tlef', ...]
```

#### 模式 3: 章节解析 (Section-Based Parsing)

**适用场景：** 解析特定章节内容（如 Check Design Report）

**来源：** IMP-5-0-0-07

```python
class CornerChecker(BaseChecker, InputFileParserMixin):ixin):
    def _parse_input_files(self):
        # 从 Check Design Report 中提取未解析的引用
        result = self.parse_section(
            log_file=self.input_files[0],
            start_marker=r'Check Design Report',
            end_marker=r'Total number',
            item_pattern=r'hinst:\s*(\S+)'
        )
        return result['items']  # ['ref1', 'ref2', ...]
```

#### 模式 4: 命令块提取 (Command Block Extraction)

**适用场景：** 提取结构化命令块及参数

**来源：** IMP-5-0-0-02, IMP-5-0-0-07

```python
class CornerChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        # 提取 create_delay_corner 命令块
        result = self.extract_command_blocks(
            log_file=self.input_files[0],
            command='create_delay_corner',
            extract_params=['-name', '-rc_corner']
        )
      
        # 获取所有 rc_corner 值
        rc_corners = [
            block['params']['-rc_corner'] 
            for block in result['blocks']
        ]
        return rc_corners
```

#### 模式 5: 计数/出现检测 (Count/Occurrence Detection)

**适用场景：** 统计 ERROR、WARNING 等出现次数

```python
class ErrorChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        # 统计 ERROR 消息
        result = self.count_pattern(
            log_file=self.input_files[0],
            pattern=r'ERROR:',
            return_matches=True
        )
        return result  # {'count': 5, 'matches': [...]}
```

#### 模式 6: 多阶段链式提取 (Multi-Stage Chain Extraction)

**适用场景：** 通过多个阶段追踪数据（domain → rc_corner → qrc_tech）

**来源：** IMP-5-0-0-02

```python
class QRCChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        # 定义提取链：domain → rc_corner → qrc_tech
        chain_spec = [
            {
                'in_command': 'create_delay_corner',
                'match_param': '-early_analysis_domain',
                'extract_param': '-rc_corner'
            },
            {
                'in_command': 'create_rc_corner',
                'match_param': '-name',
                'extract_param': '-qrc_tech'
            }
        ]
      
        # 从 qor.rpt 获取 domains
        domains = ['domain1', 'domain2']
      
        # 提取链式数据
        result = self.extract_chain(
            log_files=self.input_files,
            chain_spec=chain_spec,
            initial_values=domains
        )
        # result = {'domain1': 'path/to/qrc1.tech', 'domain2': 'path/to/qrc2.tech'}
        return list(result.values())
```

#### 模式 7: 简单列表提取 (Simple List Extraction)

**适用场景：** 提取简单的逐行列表（黑盒模块、命令列表）

**来源：** IMP-6-0-0-02, IMP-13-0-0-00

```python
class BlackBoxChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        # 提取黑盒模块列表，跳过表头
        result = self.extract_simple_list(
            log_file=self.input_files[0],
            skip_patterns=[r'---', r'Module', r'^\s*$']
        )
        return result['items']
```

---

## 完整使用示例

### 示例 1：时序路径组检查（模式 1）

**基于：** IMP-10-0-0-10

```python
from pathlib import Path
from base_checker import BaseChecker
from checker_templates.input_file_parser_template import InputFileParserMixin

class TimingPathGroupChecker(BaseChecker, InputFileParserMixin):
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-10",
            item_desc="Check timing path group reports"
        )
  
    def _parse_input_files(self):
        patterns = {
            'in2out': r'_(in2out)_|timing_in2out',
            'in2reg': r'_(in2reg)_|timing_in2reg',
            'reg2out': r'_(reg2out)_|timing_reg2out',
            'reg2reg': r'_(reg2reg)_|timing_reg2reg',
            'default': r'_(default)_|timing_default',
            'cgdefault': r'_(cgdefault)_|timing_cgdefault'
        }
      
        return self.parse_log_with_patterns(
            log_file=self.input_files[0],
            patterns=patterns,
            extract_paths=True  # 自动提取文件路径
        )
```

### 示例 2：LEF 文件检查（模式 2）

**基于：** IMP-5-0-0-01

```python
class LEFFileChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        result = self.extract_file_references(
            log_file=self.input_files[0],
            extensions=['.lef', '.tlef']
        )
      
        # 存储元数据供后续使用
        self._lef_metadata = result['metadata']
      
        return result['files']
```

### 示例 3：未解析引用检查（模式 3）

**基于：** IMP-5-0-0-05

```python
class UnresolvedRefChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        result = self.parse_section(
            log_file=self.input_files[0],
            start_marker=r'Check\s+Design\s+Report',
            end_marker=r'Total\s+number\s+of\s+unresolved',
            item_pattern=r'hinst:\s*(\S+)'
        )
      
        if not result['found']:
            # 未找到 Check Design Report
            return {'items': [], 'has_report': False}
      
        # 存储元数据
        self._ref_metadata = result['metadata']
      
        return {'items': result['items'], 'has_report': True}
```

### 示例 4：QRC 文件链式提取（模式 2+4+6 组合）

**基于：** IMP-5-0-0-02

```python
class QRCTechChecker(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        # 1. 从 qor.rpt 提取 domains（使用其他工具）
        from parse_qor import parse_qor
        qor_file = [f for f in self.input_files if f.name == 'qor.rpt'][0]
        qor_info = parse_qor(qor_file)
        domains = [d['domain'] for d in qor_info['domains']]
      
        # 2. 提取日志文件
        log_files = [f for f in self.input_files if f.suffix == '.log']
      
        # 3. 定义链式提取规则
        chain_spec = [
            {
                'in_command': 'create_delay_corner',
                'match_param': '-early_analysis_domain',
                'extract_param': '-rc_corner'
            },
            {
                'in_command': 'create_rc_corner',
                'match_param': '-name',
                'extract_param': '-qrc_tech'
            }
        ]
      
        # 4. 执行链式提取
        qrc_map = self.extract_chain(
            log_files=log_files,
            chain_spec=chain_spec,
            initial_values=domains
        )
      
        return list(qrc_map.values())
```

---

## 方法速查表


| 方法                         | 用途             | 返回值                          | 来源 Checker    |
| ---------------------------- | ---------------- | ------------------------------- | --------------- |
| `parse_log_with_patterns()`  | 模式匹配查找     | `{'found': {}, 'missing': []}`  | IMP-10-0-0-10   |
| `parse_log_with_keywords()`  | 关键字搜索       | `{'matches': {}}`               | IMP-10-0-0-10   |
| `extract_metrics_from_log()` | 数值提取         | `{'metrics': {}}`               | 通用            |
| `extract_file_references()`  | 文件引用提取     | `{'files': [], 'metadata': {}}` | IMP-5-0-0-01/02 |
| `parse_section()`            | 章节解析         | `{'found': bool, 'items': []}`  | IMP-5-0-0-05    |
| `extract_command_blocks()`   | 命令块提取       | `{'blocks': []}`                | IMP-5-0-0-02/07 |
| `count_pattern()`            | 计数统计         | `{'count': int}`                | 通用            |
| `extract_chain()`            | 链式提取         | `{initial: final}`              | IMP-5-0-0-02    |
| `extract_simple_list()`      | 简单列表         | `{'items': []}`                 | IMP-6-0-0-02    |
| `normalize_command()`        | 命令格式规范化   | str                             | IMP-10-0-0-02   |

---

## 设计原则

**适用场景：**

- Type 3: Value Check with Waivers
- Type 4: Boolean Check with Waivers

**核心功能：**

```python
from checker_templates.waiver_handler_mixin import WaiverHandlerMixin

class MyChecker(BaseChecker, WaiverHandlerMixin):
    def _execute_type3(self):
        # 分类违规项
        classified = self.classify_violations(
            violations=['item1', 'item2'],
            waive_items=['item1']
        )
        # classified = {
        #     'waived': ['item1'],
        #     'unwaived': ['item2'],
        #     'unused_waivers': []
        # }
```

### 3. OutputBuilderUtils - 输出构建工具（即将推出）

**适用场景：**

- 需要构建 info_groups 和 details
- 确保两者匹配关系正确

**核心功能：**

```python
from checker_templates.output_builder_utils import build_output

result = build_output(
    found_items=['item1', 'item2'],
    missing_items=['item3'],
    waived_items=['item3']
)
# 自动生成正确匹配的 info_groups 和 details
```

## 快速开始

### 示例 1：简单日志关键字检查

```python
from pathlib import Path
from base_checker import BaseChecker
from checker_templates.input_file_parser_template import InputFileParserMixin

class SimpleLogChecker(BaseChecker, InputFileParserMixin):
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="EXAMPLE-01",
            item_desc="Check if timing reports were generated"
        )
  
    def _parse_input_files(self):
        # 定义要查找的关键字
        patterns = {
            'setup_report': r'setup.*\.rpt',
            'hold_report': r'hold.*\.rpt'
        }
      
        return self.parse_log_with_patterns(
            log_file=self.input_files[0],
            patterns=patterns
        )
  
    def _execute_type1(self):
        data = self._parse_input_files()
        found = data['found']
        missing = data['missing']
      
        is_pass = len(missing) == 0
      
        # 构建详情...
        # （使用 OutputBuilderUtils 会更简单）
```

### 示例 2：提取数值指标

```python
class MetricExtractor(BaseChecker, InputFileParserMixin):
    def _parse_input_files(self):
        metric_patterns = {
            'setup_slack': r'Worst Setup Slack:\s+(-?\d+\.?\d*)',
            'hold_slack': r'Worst Hold Slack:\s+(-?\d+\.?\d*)',
            'violation_count': r'Total Violations:\s+(\d+)'
        }
      
        return self.extract_metrics_from_log(
            log_file=self.input_files[0],
            metric_patterns=metric_patterns
        )
  
    def _execute_type2(self):
        data = self._parse_input_files()
        metrics = data['metrics']
      
        # 提取数值
        violation_count = metrics['violation_count']['value']
        required_count = int(self.config.requirements.value)
      
        is_pass = violation_count <= required_count
        # ...
```

## 设计原则

### 1. 从真实代码提取

所有模板都来自已验证的 checker 实现（如 IMP-10-0-0-10），确保可靠性。

### 2. 最小侵入性

使用 Mixin 模式，不影响现有代码结构：

```python
# 添加功能只需要继承 Mixin
class MyChecker(BaseChecker, InputFileParserMixin):
    pass  # 立即获得所有解析功能
```

### 3. 灵活配置

所有方法都提供丰富的参数：

```python
# 基础用法
result = self.parse_log_with_patterns(log_file, patterns)

# 高级用法
result = self.parse_log_with_patterns(
    log_file=log_file,
    patterns=patterns,
    required_items=['in2out', 'in2reg'],  # 只检查部分
    extract_paths=True,                    # 提取文件路径
    case_sensitive=False                   # 大小写不敏感
)
```

### 4. 详细文档

每个方法都有完整的文档字符串，包括：

- 参数说明
- 返回值结构
- 使用示例

## 最佳实践

### ✅ 推荐做法

1. **优先使用模板方法**

   ```python
   # ✅ 好 - 使用模板
   result = self.parse_log_with_patterns(log_file, patterns)

   # ❌ 差 - 手写解析逻辑
   found = {}
   with open(log_file) as f:
       for line in f:
           if 'pattern' in line:
               found['item'] = line
   ```
2. **组合多个 Mixin**

   ```python
   # ✅ 好 - 组合使用
   class MyChecker(BaseChecker, InputFileParserMixin, WaiverHandlerMixin):
       pass
   ```
3. **利用返回值结构**

   ```python
   # ✅ 好 - 直接使用结构化数据
   result = self.parse_log_with_patterns(...)
   for item, meta in result['found'].items():
       print(f"Found {item} at line {meta['line_number']}")

   # ❌ 差 - 重新解析
   for item in result['found'].keys():
       # 手动查找行号...
   ```

### ⚠️ 注意事项

1. **不要修改模板代码**

   - 模板是共享的，修改会影响所有 checkers
   - 如需定制，在子类中覆盖方法
2. **理解返回值结构**

   - 查看文档字符串了解返回值格式
   - 使用结构化数据，避免硬编码索引
3. **处理边界情况**

   ```python
   result = self.parse_log_with_patterns(...)

   # ✅ 好 - 检查是否存在
   if 'item' in result['found']:
       path = result['found']['item']['extracted_path']

   # ❌ 差 - 假设一定存在
   path = result['found']['item']['extracted_path']  # 可能 KeyError
   ```

## 性能优化

### 1. 文件路径提取

如果不需要提取文件路径，设置 `extract_paths=False` 加快速度：

```python
result = self.parse_log_with_patterns(
    log_file=log_file,
    patterns=patterns,
    extract_paths=False  # 跳过路径提取
)
```

### 2. 大文件处理

对于超大日志文件，考虑只读取部分内容：

```python
# 可以在子类中覆盖 read_file 方法
def read_file(self, file_path, max_lines=10000):
    lines = []
    with open(file_path) as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line.rstrip('\n'))
    return lines
```

## 故障排除

### 问题 1: 导入失败

```python
ModuleNotFoundError: No module named 'checker_templates'
```

**解决：** 确保 `Check_modules/common` 在 Python path 中：

```python
import sys
from pathlib import Path

_COMMON_DIR = Path(__file__).parents[2] / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from checker_templates.input_file_parser_template import InputFileParserMixin
```

### 问题 2: 模式匹配失败

```python
result['missing'] = ['item1', 'item2']  # 明明在日志里存在
```

**解决：** 检查正则表达式是否正确：

```python
# 使用 pattern_debugger 工具测试
python tools/pattern_debugger.py --log /path/to/log.log

# 或者手动测试
import re
pattern = r'_(in2out)_'
test_line = "reports/timing_in2out_hold.rpt"
print(bool(re.search(pattern, test_line)))  # 应该是 True
```

### 问题 3: 文件路径提取不正确

```python
result['found']['item']['extracted_path'] = ''  # 空字符串
```

**解决：** 查看原始行内容，确认格式：

```python
result = self.parse_log_with_patterns(...)
print(result['found']['item']['line_content'])  # 查看原始行
# 根据实际格式调整提取逻辑，或在子类中覆盖 _extract_file_path_from_line
```

## 贡献新模板

如果你开发了通用的 checker 组件，欢迎提交到模板库：

1. 确保代码已在至少 2 个 checkers 中验证
2. 添加完整的文档字符串
3. 提供使用示例
4. 更新本 README

## 参考实现

- **IMP-10-0-0-10.py** - InputFileParserMixin 的原始实现
  - 路径: `Check_modules/10.0_STA_DCD_CHECK/scripts/checker/IMP-10-0-0-10.py`
  - 包含完整的日志解析和文件路径提取逻辑

## 更新日志

### v1.0.0 (2025-12-08)

- ✅ InputFileParserMixin 初始版本
  - `parse_log_with_patterns()` - 模式匹配解析
  - `parse_log_with_keywords()` - 关键字解析
  - `extract_metrics_from_log()` - 数值提取
  - 自动文件路径提取
- ⏳ WaiverHandlerMixin 开发中
- ⏳ OutputBuilderUtils 开发中

---

# WaiverHandlerMixin - Waiver 处理模板 v1.0.0

## 概述

从 15+ checkers 提取的标准化 waiver 处理逻辑，支持 Type 3/4 检查项。

**提取来源:**

- IMP-10-0-0-10: Type 3/4 waiver 逻辑
- IMP-7-0-0-00~04: 通配符匹配
- IMP-3-0-0-00~03: 模式匹配
- IMP-5-0-0-00: Waiver 值处理

## 核心方法


| 方法                         | 功能                         | 返回值            |
| ---------------------------- | ---------------------------- | ----------------- |
| `matches_waiver_pattern()`   | 检查项是否匹配 waiver 模式   | bool              |
| `parse_waive_items()`        | 解析 waive_items 配置        | Dict[str, str]    |
| `classify_items_by_waiver()` | 分类为 waived/unwaived       | Tuple[List, List] |
| `find_unused_waivers()`      | 查找未使用的 waiver          | List[str]         |
| `format_waiver_reason()`     | 格式化 reason + [WAIVER] tag | str               |

## 快速开始

```python
from checker_templates.waiver_handler_template import WaiverHandlerMixin

class MyChecker(BaseChecker, WaiverHandlerMixin):
    def _execute_type3(self):
        # 1. Parse waivers
        waive_dict = self.parse_waive_items(self.get_waivers().get('waive_items', []))
      
        # 2. Classify items
        waived, unwaived = self.classify_items_by_waiver(
            all_items=missing_items,
            waive_dict=waive_dict
        )
      
        # 3. Check PASS/FAIL
        is_pass = len(unwaived) == 0
      
        # 4. Format reasons
        for item in waived:
            reason = self.format_waiver_reason('Not found', waive_dict[item])
```

完整文档见 waiver_handler_template.py 文件头部注释。

---

## 3. OutputBuilderMixin - 输出结果构建(v1.0.0)

**一步构建完整 CheckResult，代码减少~70%**

### IMP-10-0-0-10 重构效果

- Type 3 方法: 120 行 → 52 行 (**-56.7%**)
- Type 4 方法: 110 行 → 47 行 (**-57.3%**)

### 核心方法


| 方法                       | 功能                      | 代码减少 |
| -------------------------- | ------------------------- | -------- |
| build_complete_output()    | 一步构建完整 CheckResult  | ~70%     |
| build_details_from_items() | 构建 DetailItem 列表      | ~60%     |
| build_result_groups()      | 生成 INFO/ERROR/WARN 分组 | ~50%     |

### 快速开始

```python
from checker_templates import InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin

class MyChecker(BaseChecker, InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin):
    def _execute_type3(self):
        # Parse & classify
        results = self.parse_log_with_patterns(log_file, patterns)
        waive_dict = self.parse_waive_items(waive_items_raw)
        waived, unwaived = self.classify_items_by_waiver(missing, waive_dict)
      
        # Build output (one call replaces 100+ lines!)
        return self.build_complete_output(
            found_items=results['found'],
            missing_items=unwaived,
            waived_items=waived,
            waive_dict=waive_dict,
            has_pattern_items=True,
            has_waiver_value=True
        )
```

---

## 性能数据

### IMP-10-0-0-10 完整重构


| 指标           | 重构前 | 重构后 | 改善         |
| -------------- | ------ | ------ | ------------ |
| **总代码行数** | 684 行 | 402 行 | **-41.2%**   |
| Type 1         | 78 行  | 32 行  | -59.0%       |
| Type 2         | 88 行  | 41 行  | -53.4%       |
| Type 3         | 120 行 | 52 行  | -56.7%       |
| Type 4         | 110 行 | 47 行  | -57.3%       |
| 测试结果       | PASS   | PASS   | ✅ 100% 兼容 |

---

## 完整示例

```python
class MyChecker(BaseChecker, InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin):
    def _execute_type3(self):
        # 1. Parse logs
        results = self.parse_log_with_patterns(log_file, patterns)
      
        # 2. Handle waivers
        waive_dict = self.parse_waive_items(waive_items_raw)
        waived, unwaived = self.classify_items_by_waiver(results['missing'], waive_dict)
        unused = self.find_unused_waivers(waive_dict, results['missing'])
      
        # 3. Build output
        return self.build_complete_output(
            found_items=results['found'],
            missing_items=unwaived,
            waived_items=waived,
            unused_waivers=unused,
            waive_dict=waive_dict,
            has_pattern_items=True,
            has_waiver_value=True
        )
```

**效果:** 150 行 → 40 行 (**-73%**)

---

## 版本历史

**v1.0.0** (2025-12-08)

- ✅ InputFileParserMixin v2.0 (943 lines, 7 patterns)
- ✅ WaiverHandlerMixin v1.0 (567 lines, 8 patterns)
- ✅ OutputBuilderMixin v1.0 (606 lines, 6 patterns)
- ✅ IMP-10-0-0-10 验证 (-41.2% code)

