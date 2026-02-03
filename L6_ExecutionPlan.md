# L6 执行Plan: 报告生成器

## 1. 层级职责

Layer 6负责将L5的数据字典转换为多种用户可读的输出格式。这是表示层（Presentation Layer），不修改数据，只负责格式化。

**核心原则:**
- **数据不变性**: 不修改L5输出的数据内容
- **格式多样性**: 支持Log、Report、YAML、Excel、HTML等格式
- **向后兼容**: 输出格式与legacy保持一致
- **独立性**: 可以独立添加新格式，不影响L0-L5

## 2. 交付物

- `log_formatter.py` - Log文件生成器
- `report_formatter.py` - Report文件生成器（简化版）
- `summary_generator.py` - Summary YAML生成器
- `excel_generator.py` - Excel报告生成器
- `output_schema.py` - 输出Schema定义
- `test_l6.py` - Layer 6单元测试

## 3. 公开API

### 3.1 Main Report Generator API

```python
from typing import Dict, List, Any
from pathlib import Path
from enum import Enum

# NOTE: OutputFormat is an Enum for constant definition, NOT a data structure.
# Plan.txt does NOT define output format enums, but using Enum for format constants
# is standard Python practice and does NOT violate the "Dict-only" principle.
# Data passed between layers remains Dict; Enum is only for parameter validation.

class OutputFormat(Enum):
    """支持的输出格式常量"""
    LOG = "log"           # 详细日志格式
    REPORT = "report"     # 简化报告格式
    YAML = "yaml"         # Summary YAML
    EXCEL = "excel"       # Excel表格
    HTML = "html"         # HTML Dashboard（可选）

def generate_report(
    l5_output: Dict,
    type_id: int,
    item_id: str,
    item_desc: str,
    output_format: OutputFormat,
    output_path: Path,
    **kwargs
) -> None:
    """
    主入口：生成指定格式的报告
    
    输入:
        l5_output: L5的filter_output_keys()返回值
                   必须包含L5 Schema定义的keys
        type_id: 1, 2, 3, 或 4
        item_id: Checker ID (e.g., "IMP-10-0-0-00")
        item_desc: Checker描述
        output_format: 输出格式枚举
        output_path: 输出文件路径
        **kwargs: 格式特定参数
        
    输出:
        写入文件到output_path
        
    抛出:
        ValueError: L5 output schema不匹配
        IOError: 文件写入失败
    """
    pass
```

### 3.2 Log Formatter API

```python
def format_as_log(
    l5_output: Dict,
    item_id: str,
    item_desc: str,
    type_id: int
) -> str:
    """
    生成Log格式文本
    
    输出格式:
        PASS|FAIL:item_id:item_desc
        [INFO]:info_message (if any)
        [ERROR01]:description (Severity:Fail, Occurrence:N)
          - detail_name
          - Source_line: N
          - Source_file: path
          - Reason: xxx
        [WAIVED_INFO]:waiver_reason
        
    输入:
        l5_output: L5输出字典
        item_id: "IMP-10-0-0-00"
        item_desc: "Confirm netlist version"
        type_id: 1-4
        
    输出:
        格式化的log文本
        
    关键逻辑:
        1. 状态行: PASS/FAIL:item_id:item_desc
        2. 分组生成: ERROR → WARN → INFO
        3. 每组显示: 组ID、描述、Severity、Occurrence、详细列表
        4. Waiver标签: [WAIVED_AS_INFO] / [WAIVED_INFO]
    """
    pass

def write_log_file(
    l5_output: Dict,
    item_id: str,
    item_desc: str,
    type_id: int,
    log_path: Path,
    mode: str = 'a'
) -> None:
    """
    写入Log文件（支持append模式）
    
    输入:
        mode: 'a' (append) or 'w' (overwrite)
    """
    pass
```

### 3.3 Report Formatter API

```python
def format_as_report(
    l5_output: Dict,
    item_id: str,
    item_desc: str,
    type_id: int
) -> str:
    """
    生成Report格式文本（简化版，无组ID）
    
    输出格式:
        PASS|FAIL:item_id:item_desc
        [INFO]:info_message
        
        Fail Occurrence: N
          - detail (line N, file: path)
            Reason: xxx
        
        Warn Occurrence: N
          - ...
    
    差异 vs Log:
        - 无ERROR01/WARN01等组ID
        - 更紧凑的格式
        - 适合快速浏览
    """
    pass

def write_report_file(
    l5_output: Dict,
    item_id: str,
    item_desc: str,
    type_id: int,
    report_path: Path,
    mode: str = 'a'
) -> None:
    """写入Report文件"""
    pass
```

### 3.4 Summary YAML Generator API

```python
def generate_summary_yaml(
    l5_outputs: List[Dict],
    item_metadata: List[Dict],
    module_name: str,
    stage_name: str,
    output_path: Path
) -> None:
    """
    生成Summary YAML（多个checker的汇总）
    
    输入:
        l5_outputs: 多个checker的L5输出列表
        item_metadata: 每个checker的元数据
                      [{'item_id': 'IMP-10-...', 'item_desc': '...', 'type_id': 3}, ...]
        module_name: "top_module"
        stage_name: "signoff"
        output_path: /path/to/summary.yaml
        
    输出YAML格式:
        module: top_module
        stage: signoff
        check_items:
          IMP-10-0-0-00:
            executed: true
            status: PASS|FAIL
            description: xxx
            failures:
              - occurrence: N
              - index: 1
                detail: xxx
                source_line: N
                source_file: path
                reason: xxx
            warnings:
              - occurrence: N
              - index: 1
                detail: xxx
                ...
    """
    pass

def build_check_item_entry(
    l5_output: Dict,
    item_id: str,
    item_desc: str,
    type_id: int,
    executed: bool = True
) -> Dict:
    """
    构建单个check item的YAML entry
    
    输出:
        {
            'executed': True,
            'status': 'PASS',
            'description': 'xxx',
            'failures': [...],
            'warnings': [...]
        }
    """
    pass
```

### 3.5 Excel Generator API

```python
def generate_excel_report(
    summary_yaml_path: Path,
    output_excel_path: Path,
    module_name: str
) -> None:
    """
    从Summary YAML生成Excel报告
    
    输入:
        summary_yaml_path: Summary YAML文件路径
        output_excel_path: 输出Excel路径
        module_name: 模块名（用于文件命名）
        
    输出Excel列:
        - Module: 模块名
        - Stage: 阶段名
        - ItemID: Checker ID
        - Executed: true/false
        - Status: PASS/FAIL
        - Description: Checker描述
        - Kind: FAILURE/WARNING
        - Occurrence: 发生次数
        - Index: 详细项索引
        - Detail: 详细信息
        - SourceLine: 行号
        - SourceFile: 文件路径
        - Reason: 原因描述
        
    格式增强:
        - Header行加粗居中
        - 自动列宽调整
        - 启用auto-filter
        - Status列条件格式化（FAIL=红色，PASS=绿色）
    """
    pass

def build_excel_rows(summary_dict: Dict) -> List[List[Any]]:
    """
    从Summary字典构建Excel行数据
    
    输入:
        summary_dict: 从YAML加载的字典
        
    输出:
        二维列表，每行13列数据
    """
    pass
```

## 4. 输入Schema（来自L5）

### 4.1 L5输出字段映射

```python
# Type 1 输入 (3 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[FoundItem],
    'missing_items': List[MissingItem]
}

# Type 2 输入 (4 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[FoundItem],
    'missing_items': List[MissingItem],
    'extra_items': List[ExtraItem]
}

# Type 3 输入 (6 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[FoundItem],
    'missing_items': List[MissingItem],
    'extra_items': List[ExtraItem],
    'waived': List[WaivedItem],
    'unused_waivers': List[UnusedWaiver]
}

# Type 4 输入 (5 keys)
{
    'status': 'PASS' | 'FAIL',
    'found_items': List[FoundItem],
    'missing_items': List[MissingItem],
    'waived': List[WaivedItem],
    'unused_waivers': List[UnusedWaiver]
}
```

### 4.2 Item Schema定义

```python
# FoundItem Schema
{
    'value': str,
    'source_file': str,
    'line_number': int | None,
    'matched_content': str,
    'parsed_fields': Dict,
    # L6特定字段（从parsed_fields提取或默认）
    'severity': 'INFO',  # found_items默认为INFO
}

# MissingItem Schema
{
    'expected': str,
    'source_file': '',  # Ghost field
    'matched_content': '',  # Ghost field
    'parsed_fields': {},  # Ghost field
    # L6特定字段
    'severity': 'FAIL',  # missing_items默认为FAIL
    'reason': 'Expected item not found'
}

# ExtraItem Schema (Type 2/3)
{
    'value': str,
    'source_file': str,
    'line_number': int | None,
    'matched_content': str,
    'parsed_fields': Dict,
    # L6特定字段
    'severity': 'WARN',  # extra_items默认为WARN
    'reason': 'Unexpected item found'
}

# WaivedItem Schema (Type 3/4)
{
    'value': str,
    'source_file': str,
    'line_number': int | None,
    'matched_content': str,
    'parsed_fields': Dict,
    'waiver_reason': str,  # L4添加的waiver原因
    'waiver_pattern': str,  # 匹配的waive_items pattern
    # L6特定字段
    'severity': 'INFO',
    'tag': '[WAIVED_AS_INFO]' | '[WAIVED_INFO]'
}

# UnusedWaiver Schema (Type 3/4)
{
    'pattern': str,
    'reason': str,  # 从waive_items提取
    # L6特定字段
    'severity': 'WARN',
    'tag': '[UNUSED_WAIVER]'
}
```

## 5. 输出Schema

### 5.1 Log格式规范

```text
PASS:IMP-10-0-0-00:Confirm the netlist/spef version is correct
[INFO]:Found 3 valid items
[ERROR01]:Missing required items (Severity:Fail, Occurrence:2)
  - expected_item_1
  - Source_line: N/A
  - Source_file: 
  - Reason: Expected item not found
[ERROR02]:Extra unexpected items (Severity:Warn, Occurrence:1)
  - extra_value
  - Source_line: 123
  - Source_file: /path/to/file.log
  - Reason: Unexpected item found
[WAIVED_INFO]:Global Waiver: All violations waived
[INFO01]:Items found in check (Severity:Info, Occurrence:3)
  - found_value_1
  - Source_line: 45
  - Source_file: /path/to/file.log
  - Reason: Pattern matched successfully

```

**格式规则:**
1. **状态行**: `PASS|FAIL:item_id:item_desc`
2. **INFO消息**: `[INFO]:message` （可选）
3. **错误分组**: `[ERROR01]`, `[ERROR02]`, ... （按发现顺序）
4. **警告分组**: `[WARN01]`, `[WARN02]`, ... （如果有extra_items）
5. **Waiver标签**: `[WAIVED_INFO]`, `[WAIVED_AS_INFO]`
6. **信息分组**: `[INFO01]`, `[INFO02]`, ... （found_items）
7. **组格式**: `描述 (Severity:级别, Occurrence:次数)`
8. **详细项**: 缩进2空格，4行标准格式

### 5.2 Report格式规范

```text
PASS:IMP-10-0-0-00:Confirm the netlist/spef version is correct
[INFO]:Found 3 valid items

Fail Occurrence: 2
  - expected_item_1 (line N/A, file: )
    Reason: Expected item not found
  - expected_item_2 (line N/A, file: )
    Reason: Expected item not found

Warn Occurrence: 1
  - extra_value (line 123, file: /path/to/file.log)
    Reason: Unexpected item found

```

**差异点:**
- 无分组ID（ERROR01等）
- 更紧凑的格式
- 按Severity聚合（Fail/Warn/Info）

### 5.3 Summary YAML格式规范

```yaml
module: top_module
stage: signoff
check_items:
  IMP-10-0-0-00:
    executed: true
    status: FAIL
    description: "Confirm the netlist/spef version is correct"
    failures:
      - occurrence: 2
      - index: 1
        detail: "expected_item_1"
        source_line: "N/A"
        source_file: ""
        reason: "Expected item not found"
      - index: 2
        detail: "expected_item_2"
        source_line: "N/A"
        source_file: ""
        reason: "Expected item not found"
    warnings:
      - occurrence: 1
      - index: 1
        detail: "extra_value"
        source_line: "123"
        source_file: "/path/to/file.log"
        reason: "Unexpected item found"
  IMP-10-0-1-00:
    executed: true
    status: PASS
    description: "Another check"
    failures: []
    warnings: []
```

**关键规则:**
1. **第一项是occurrence**: `{occurrence: N}`
2. **后续是详细项**: `{index, detail, source_line, source_file, reason}`
3. **source_line转为字符串**: `"123"` 或 `"N/A"`
4. **空列表**: `failures: []` 当无错误时

### 5.4 Excel格式规范

**列定义（13列）:**

| 列名 | 宽度 | 示例值 | 来源 |
|------|------|--------|------|
| Module | 15 | top_module | module_name参数 |
| Stage | 10 | signoff | stage_name参数 |
| ItemID | 20 | IMP-10-0-0-00 | item_id |
| Executed | 10 | true | 固定true（如果生成了报告） |
| Status | 10 | FAIL | l5_output['status'] |
| Description | 40 | Confirm netlist... | item_desc |
| Kind | 10 | FAILURE | FAILURE/WARNING（从severity推断） |
| Occurrence | 12 | 2 | len(missing_items) |
| Index | 8 | 1 | 详细项序号 |
| Detail | 30 | expected_item | value或expected字段 |
| SourceLine | 12 | 123 | line_number |
| SourceFile | 50 | /path/to/file | source_file |
| Reason | 50 | Expected item... | reason字段 |

**格式增强:**
- Header行: 加粗 + 居中 + 底部边框
- Status列: FAIL=红色, PASS=绿色
- 自动列宽（最大60字符）
- 启用auto-filter
- 冻结首行

## 6. 数据转换逻辑

### 6.1 Severity推断规则

```python
def infer_severity(item: Dict, item_type: str) -> str:
    """
    从L5 item推断severity
    
    规则:
        found_items    → INFO
        missing_items  → FAIL
        extra_items    → WARN
        waived (有tag) → INFO
        unused_waivers → WARN
        
    特殊情况:
        - Global waiver (value=0): missing/extra → INFO + [WAIVED_AS_INFO]
          (Plan.txt Section 3: L4已在item中添加severity和tag字段)
        - Selective waiver: 已移动到waived → INFO + [WAIVED_AS_INFO]
        
    注意:
        L4 Waiver Engine会在items中添加severity和tag字段
        L5保留这些字段不过滤（CR5只过滤top-level keys）
        L6优先读取item自带的severity，无则按上述规则推断
    """
    # 优先读取item自带的severity（L4添加）
    if 'severity' in item:
        return item['severity']
    
    # 否则按item_type推断
    if item_type == 'found_items':
        return 'INFO'
    elif item_type == 'missing_items':
        # 检查是否有WAIVED标签（L4添加）
        if item.get('tag') == '[WAIVED_AS_INFO]':
            return 'INFO'
        return 'FAIL'
    elif item_type == 'extra_items':
        if item.get('tag') == '[WAIVED_AS_INFO]':
            return 'INFO'
        return 'WARN'
    elif item_type == 'waived':
        return 'INFO'
    elif item_type == 'unused_waivers':
        return 'WARN'
    else:
        return 'INFO'  # Default
```

### 6.2 错误分组生成

```python
def build_error_groups(l5_output: Dict, type_id: int) -> Dict:
    """
    从L5扁平输出构建error_groups
    
    输入:
        {
            'missing_items': [item1, item2],
            'extra_items': [item3],
            'found_items': [item4, item5, item6]
        }
        
    输出:
        {
            'error_groups': {
                'ERROR01': {
                    'description': 'Missing required items',
                    'severity': 'Fail',
                    'occurrence': 2,
                    'items': [item1, item2]
                },
                'ERROR02': {
                    'description': 'Extra unexpected items',
                    'severity': 'Warn',
                    'occurrence': 1,
                    'items': [item3]
                }
            },
            'info_groups': {
                'INFO01': {
                    'description': 'Items found in check',
                    'severity': 'Info',
                    'occurrence': 3,
                    'items': [item4, item5, item6]
                }
            }
        }
        
    分组规则（固定映射，不管是否为空）:
        1. missing_items → ERROR01 (always)
        2. extra_items → ERROR02 (Type 2/3 only)
        3. unused_waivers → WARN01 (Type 3/4 only)
        4. found_items → INFO01 (always)
        5. waived → INFO02 (Type 3/4 only)
        
    注意:
        - 即使missing_items为空，ERROR01仍然存在（occurrence=0）
        - 分组ID是固定的，不依赖于实际数据内容
        - 这确保了输出格式的一致性，便于下游解析
    """
    pass
```

### 6.3 Occurrence统计

```python
def calculate_occurrence(items: List[Dict]) -> int:
    """
    计算occurrence（发生次数）
    
    规则:
        - 对于missing_items/extra_items: len(items)
        - 对于found_items: len(items)
        - 对于waived: len(items)
        
    Summary YAML中的occurrence:
        在YAML格式中，occurrence作为列表第一个元素:
        failures:
          - occurrence: N  # N = len(failures) - 1（减去这个元数据元素本身）
          - index: 1
            detail: xxx
          - index: 2
            detail: yyy
        
        因此，calculate_occurrence返回的是原始items数量，
        在生成YAML时需要注意这个-1的调整
        - 对于unused_waivers: len(items)
        
    特殊情况:
        - Ghost items (source_file=""): 仍然计数
        - 去重: 不去重，每个item都计数
    """
    return len(items)
```

## 7. 错误处理

### 7.1 Schema验证

```python
def validate_l5_output(l5_output: Dict, type_id: int) -> None:
    """
    验证L5输出是否符合预期Schema
    
    检查:
        1. 必需keys存在（根据type_id）
        2. 每个item包含必需字段
        3. 数据类型正确
        
    抛出:
        ValueError: Schema不匹配，附带详细错误信息
    """
    required_keys = {
        1: {'status', 'found_items', 'missing_items'},
        2: {'status', 'found_items', 'missing_items', 'extra_items'},
        3: {'status', 'found_items', 'missing_items', 'extra_items', 'waived', 'unused_waivers'},
        4: {'status', 'found_items', 'missing_items', 'waived', 'unused_waivers'}
    }
    
    if not set(l5_output.keys()) == required_keys[type_id]:
        missing = required_keys[type_id] - set(l5_output.keys())
        extra = set(l5_output.keys()) - required_keys[type_id]
        raise ValueError(
            f"L5 output schema mismatch for Type {type_id}. "
            f"Missing keys: {missing}, Extra keys: {extra}"
        )
```

### 7.2 文件写入错误

```python
def safe_write_file(content: str, path: Path, mode: str = 'w') -> None:
    """
    安全写入文件，自动创建目录
    
    错误处理:
        - 目录不存在: 自动创建
        - 权限不足: 抛出IOError with message
        - 磁盘空间不足: 抛出IOError
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode, encoding='utf-8') as f:
            f.write(content)
    except PermissionError as e:
        raise IOError(f"Permission denied writing to {path}: {e}")
    except OSError as e:
        raise IOError(f"Failed to write to {path}: {e}")
```

## 8. 集成示例

### 8.1 单个Checker完整流程

```python
# Step 1: L0-L5 生成数据字典
from L0.type_dispatcher import validate_and_normalize_config, determine_type
from L1.io_engine import read_file_text
from L2.parsing_orchestrator import orchestrate_parsing
from L3.check_assembler import assemble_check_result
from L4.waiver_engine import apply_waivers
from L5.output_controller import filter_output_keys

# L0: Type决策
config = validate_and_normalize_config(req, waiver, input_files, desc)
type_id = determine_type(config)

# L1-L4: 数据处理
# ... (省略中间步骤)

# L5: 过滤输出
internal_result = apply_waivers(check_result, waiver_config)
l5_output = filter_output_keys(internal_result, type_id)

# Step 2: L6 生成多种格式报告
from L6.log_formatter import write_log_file
from L6.report_formatter import write_report_file
from L6.summary_generator import build_check_item_entry

# 生成Log文件
write_log_file(
    l5_output=l5_output,
    item_id="IMP-10-0-0-00",
    item_desc="Confirm netlist version",
    type_id=type_id,
    log_path=Path("output/IMP-10-0-0-00.log")
)

# 生成Report文件
write_report_file(
    l5_output=l5_output,
    item_id="IMP-10-0-0-00",
    item_desc="Confirm netlist version",
    type_id=type_id,
    report_path=Path("output/IMP-10-0-0-00.rpt")
)

# 生成Summary YAML entry
yaml_entry = build_check_item_entry(
    l5_output=l5_output,
    item_id="IMP-10-0-0-00",
    item_desc="Confirm netlist version",
    type_id=type_id,
    executed=True
)
```

### 8.2 批量Checkers汇总

```python
# Collect all checker results
all_results = []
for checker in checkers:
    l5_output = run_checker(checker)
    all_results.append({
        'l5_output': l5_output,
        'item_id': checker.item_id,
        'item_desc': checker.item_desc,
        'type_id': checker.type_id
    })

# Generate Summary YAML
from L6.summary_generator import generate_summary_yaml

generate_summary_yaml(
    l5_outputs=[r['l5_output'] for r in all_results],
    item_metadata=[
        {'item_id': r['item_id'], 'item_desc': r['item_desc'], 'type_id': r['type_id']}
        for r in all_results
    ],
    module_name="top_module",
    stage_name="signoff",
    output_path=Path("output/summary.yaml")
)

# Generate Excel Report
from L6.excel_generator import generate_excel_report

generate_excel_report(
    summary_yaml_path=Path("output/summary.yaml"),
    output_excel_path=Path("output/top_module.xlsx"),
    module_name="top_module"
)
```

### 8.3 增量Log写入

```python
# Append mode for continuous logging
for checker in checkers:
    l5_output = run_checker(checker)
    write_log_file(
        l5_output=l5_output,
        item_id=checker.item_id,
        item_desc=checker.item_desc,
        type_id=checker.type_id,
        log_path=Path("output/all_checks.log"),
        mode='a'  # Append mode
    )
```

## 9. 性能优化

### 9.1 批量生成优化

```python
def batch_generate_reports(
    results: List[Dict],
    output_dir: Path,
    formats: List[OutputFormat]
) -> None:
    """
    批量生成报告，共享资源
    
    优化策略:
        - Log文件: 单次打开，批量写入
        - YAML: 一次性生成
        - Excel: openpyxl复用Workbook对象
    """
    # 批量写入log
    if OutputFormat.LOG in formats:
        log_path = output_dir / "all_checks.log"
        with log_path.open('w', encoding='utf-8') as f:
            for result in results:
                log_content = format_as_log(
                    result['l5_output'],
                    result['item_id'],
                    result['item_desc'],
                    result['type_id']
                )
                f.write(log_content)
                f.write('\n')
```

### 9.2 内存优化

```python
def stream_excel_generation(
    summary_yaml_path: Path,
    output_excel_path: Path
) -> None:
    """
    流式处理Excel生成（大数据集）
    
    策略:
        - 逐行读取YAML
        - 逐行写入Excel
        - 避免全部加载到内存
    """
    import yaml
    from openpyxl import Workbook
    
    wb = Workbook(write_only=True)  # write_only mode
    ws = wb.create_sheet()
    
    # Write header
    ws.append(['Module', 'Stage', 'ItemID', ...])
    
    # Stream process
    with open(summary_yaml_path) as f:
        summary = yaml.safe_load(f)
        for item_id, item_data in summary['check_items'].items():
            rows = build_rows_for_item(item_id, item_data)
            for row in rows:
                ws.append(row)
    
    wb.save(output_excel_path)
```

## 10. 向后兼容性

### 10.1 Legacy格式支持

**兼容性检查清单:**

| Legacy特性 | L6支持 | 备注 |
|-----------|--------|------|
| Log格式 | ✅ | 完全兼容 |
| Report格式 | ✅ | 完全兼容 |
| Summary YAML | ✅ | occurrence字段兼容 |
| Excel 13列 | ✅ | 列顺序和命名一致 |
| [WAIVED_INFO] | ✅ | 标签格式一致 |
| [WAIVED_AS_INFO] | ✅ | 标签格式一致 |
| ERROR01分组 | ✅ | 分组逻辑一致 |
| Severity标记 | ✅ | Fail/Warn/Info一致 |

### 10.2 迁移路径

**从legacy output_formatter.py迁移:**

```python
# Legacy代码
from output_formatter import OutputFormatter, CheckResult

formatter = OutputFormatter(item_id="IMP-10-0-0-00", item_desc="...")
result = create_check_result(value=10, is_pass=True, details=[...])
formatter.write_log(result, log_path)

# 迁移到L6
from L5.output_controller import filter_output_keys
from L6.log_formatter import write_log_file

# 假设已有l5_output
write_log_file(
    l5_output=l5_output,
    item_id="IMP-10-0-0-00",
    item_desc="...",
    type_id=type_id,
    log_path=log_path
)
```

**关键变化:**
1. 不再使用CheckResult对象，直接使用L5字典
2. 分组逻辑从预计算移到动态生成
3. Severity从显式字段变为推断

## 11. 测试策略

### 11.1 单元测试

```python
# test_l6.py
import pytest
from L6.log_formatter import format_as_log
from L6.output_schema import validate_l5_output

def test_log_format_type1():
    """测试Type 1 Log格式"""
    l5_output = {
        'status': 'PASS',
        'found_items': [
            {'value': 'item1', 'source_file': '/path', 'line_number': 10, 
             'matched_content': 'content', 'parsed_fields': {}}
        ],
        'missing_items': []
    }
    
    log_text = format_as_log(l5_output, "IMP-10-0-0-00", "Test", 1)
    
    assert "PASS:IMP-10-0-0-00:Test" in log_text
    assert "[INFO01]" in log_text
    assert "item1" in log_text

def test_log_format_type3_with_waiver():
    """测试Type 3带waiver的Log格式"""
    l5_output = {
        'status': 'PASS',
        'found_items': [],
        'missing_items': [],
        'extra_items': [],
        'waived': [
            {'value': 'waived_item', 'waiver_reason': 'Test waiver', 
             'tag': '[WAIVED_AS_INFO]', 'source_file': '', 
             'line_number': None, 'matched_content': '', 'parsed_fields': {}}
        ],
        'unused_waivers': []
    }
    
    log_text = format_as_log(l5_output, "IMP-10-0-0-00", "Test", 3)
    
    assert "PASS:IMP-10-0-0-00:Test" in log_text
    assert "[WAIVED_AS_INFO]" in log_text
    assert "Test waiver" in log_text
```

### 11.2 集成测试

```python
def test_full_pipeline_type3():
    """完整流程测试：L0-L6"""
    # Setup
    config = {...}
    
    # L0-L5
    l5_output = run_full_pipeline(config)
    
    # L6
    log_path = tmp_path / "test.log"
    write_log_file(l5_output, "TEST-01", "Test", 3, log_path)
    
    # Verify
    assert log_path.exists()
    content = log_path.read_text()
    assert "TEST-01" in content
```

### 11.3 格式兼容性测试

```python
def test_legacy_compatibility():
    """验证与legacy输出格式一致性"""
    # 使用legacy golden output作为参考
    legacy_log = Path("tests/golden/IMP-10-0-0-00.log").read_text()
    
    # 生成新格式
    new_log = format_as_log(l5_output, "IMP-10-0-0-00", "...", 3)
    
    # 对比关键行
    legacy_lines = [l for l in legacy_log.split('\n') if l.strip()]
    new_lines = [l for l in new_log.split('\n') if l.strip()]
    
    assert len(legacy_lines) == len(new_lines)
    for legacy, new in zip(legacy_lines, new_lines):
        assert normalize_line(legacy) == normalize_line(new)
```

## 12. 文件结构

```
L6/
├── __init__.py
├── log_formatter.py            # Log文件生成器
├── report_formatter.py         # Report文件生成器
├── summary_generator.py        # Summary YAML生成器
├── excel_generator.py          # Excel报告生成器
├── output_schema.py            # Schema定义和验证
├── severity_inference.py       # Severity推断逻辑
├── error_grouping.py           # 错误分组构建
├── format_utils.py             # 格式化工具函数
├── test_l6.py                  # 单元测试
├── test_integration.py         # 集成测试
└── README.md                   # L6使用文档
```

## 13. 依赖关系

**上游依赖:**
- L5.output_controller: 提供l5_output字典

**下游消费者:**
- 用户: 查看Log/Report/Excel
- CI/CD: 解析Summary YAML判断通过/失败
- Dashboard: 读取YAML/Excel生成可视化

**外部库依赖:**
```python
# requirements.txt
pyyaml>=6.0        # YAML生成
openpyxl>=3.1.0    # Excel生成
```

## 14. 扩展性

### 14.1 添加新格式

```python
# 示例：添加JSON格式
def format_as_json(l5_output: Dict, item_id: str, item_desc: str, type_id: int) -> str:
    """生成JSON格式输出"""
    import json
    
    output = {
        'item_id': item_id,
        'item_desc': item_desc,
        'type_id': type_id,
        'status': l5_output['status'],
        'found_items': l5_output['found_items'],
        'missing_items': l5_output['missing_items'],
        # ... 其他字段
    }
    
    return json.dumps(output, indent=2)

# 注册到OutputFormat枚举
class OutputFormat(Enum):
    LOG = "log"
    REPORT = "report"
    YAML = "yaml"
    EXCEL = "excel"
    JSON = "json"  # 新格式
```

### 14.2 自定义分组策略

```python
def build_custom_error_groups(
    l5_output: Dict, 
    type_id: int,
    grouping_strategy: str = 'default'
) -> Dict:
    """
    支持多种分组策略
    
    策略:
        - 'default': 按item type分组（missing → ERROR01, extra → ERROR02）
        - 'by_severity': 按severity分组
        - 'by_file': 按source_file分组
        - 'flat': 不分组，所有item在ERROR01
    """
    if grouping_strategy == 'default':
        return build_error_groups(l5_output, type_id)
    elif grouping_strategy == 'by_severity':
        return build_error_groups_by_severity(l5_output, type_id)
    # ... 其他策略
```

## 15. 最佳实践

### 15.1 错误消息清晰性

```python
# Good: 明确的错误信息
reason = "Expected item 'VERSION 24.10' not found in netlist header (lines 1-50)"

# Bad: 模糊的错误信息
reason = "Not found"
```

### 15.2 文件路径处理

```python
# 统一使用绝对路径
source_file = str(Path(source_file).resolve())

# Log中使用相对路径（更易读）
def relative_path(absolute_path: str, base_dir: Path) -> str:
    try:
        return str(Path(absolute_path).relative_to(base_dir))
    except ValueError:
        return absolute_path
```

### 15.3 大数据集优化

```python
# 对于大量items，分页或汇总
if len(missing_items) > 100:
    # 只显示前10个 + 统计信息
    display_items = missing_items[:10]
    summary = f"... and {len(missing_items) - 10} more items"
else:
    display_items = missing_items
    summary = ""
```

---

**版本:** 1.0  
**最后更新:** 2026-01-26  
**依赖:** L5 Output Controller  
**状态:** Ready for Implementation
