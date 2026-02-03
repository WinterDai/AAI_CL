# L0-L6 Framework Implementation

## 项目概述

这是一个完整的6层检查框架实现，严格遵循Plan.txt的设计规范。框架采用Dict-only架构（除Exception外无自定义类），支持4种Type的requirement checking和waiver处理。

## 目录结构

```
Work/
├── L0_Config/          # 配置规范化和Type决策
│   ├── config_validator.py
│   └── test_l0.py
├── L1_IO/              # 文件IO和路径解析
│   ├── io_engine.py
│   └── test_l1.py
├── L2_Parsing/         # 解析编排（递归+DFS）
│   ├── parsing_orchestrator.py
│   └── test_l2.py
├── L3_Check/           # Check装配器（Type 1-4逻辑）
│   ├── check_assembler.py
│   └── test_l3.py
├── L4_Waiver/          # Waiver引擎（Global/Selective）
│   ├── waiver_engine.py
│   └── test_l4.py
├── L5_Output/          # 输出控制器（CR5过滤）
│   ├── output_controller.py
│   └── test_l5.py
├── L6_Report/          # 报告生成器（Log/YAML）
│   ├── log_formatter.py
│   ├── yaml_generator.py
│   └── test_l6.py
├── integration_test.py # 端到端集成测试
├── run_all_tests.py    # 测试运行器
└── requirements.txt    # 依赖清单
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 运行集成测试（推荐）
python integration_test.py

# 运行所有单元测试
python run_all_tests.py

# 运行单层测试
cd L0_Config
python test_l0.py
```

## 架构设计

### 核心原则

1. **Dict-only**: 所有数据使用Dict/List/Tuple传递，无自定义类（除Exception）
2. **Type驱动**: 4种Type决定check逻辑和waiver行为
3. **Pipeline流程**: L0→L1→L2→L3→L4→L5→L6 单向数据流
4. **Policy注入**: Atom B/C调用时注入default_match/regex_mode参数

### Type映射规则（Locked）

| Type | req.value | waiver.value | Check路径 | Waiver路径 | 输出Keys |
|------|-----------|--------------|----------|-----------|----------|
| 1 | N/A | N/A | Existence | - | status, found_items, missing_items |
| 2 | ≥1 | N/A | Pattern | - | status, found_items, missing_items, extra_items |
| 3 | ≥1 | ≥0 | Pattern | Selective | status, found_items, missing_items, extra_items, waived, unused_waivers |
| 4 | N/A | ≥0 | Existence | Global/Selective | status, found_items, missing_items, waived, unused_waivers |

## 层级职责

### L0: Config Validator
- 规范化requirements和waivers
- 验证domain约束（req≥1, waiver≥0）
- Type决策（1-4）
- 默认值处理

**关键函数**:
- `validate_and_normalize_config()` - 主入口
- `normalize_value()` - 值规范化（N/A判定）
- `determine_type()` - Type决策器

### L1: IO Engine
- 文件读取（支持gzip）
- 编码fallback（utf-8 → latin-1）
- 路径规范化（相对→绝对）
- Indirect reference解析

**关键函数**:
- `read_file_content()` - 读取文件内容
- `normalize_path()` - 路径规范化
- `resolve_indirect_reference()` - 解析indirect reference

### L2: Parsing Orchestration
- 递归解析（DFS遍历）
- Loop detection（visited_paths）
- Max depth限制（默认5）
- 稳定排序（文件顺序→行号→提取顺序）
- searched_files去重+排序

**关键函数**:
- `orchestrate_parsing()` - 主编排函数
- `extract_indirect_references()` - 提取间接引用
- `stable_sort_parsed_items()` - 稳定排序

### L3: Check Assembler
- Type 1/4: Existence check（Atom C）
- Type 2/3: Pattern check（Atom B，First Unconsumed Match）
- Description增强（{**item, 'description': desc}）
- Ghost record生成（missing items）

**关键函数**:
- `assemble_check()` - Check装配主函数
- `check_pattern_requirements()` - Pattern检查
- `check_existence_requirements()` - Existence检查
- `consume_first_match()` - 消费策略

**Policy注入**:
- Pattern check: `default_match="contains"`, `regex_mode="search"`

### L4: Waiver Engine
- Global waiver (value=0): 标记severity=INFO, 强制PASS
- Selective waiver (value>0): MOVE匹配violations到waived
- N-to-M匹配（一个pattern匹配多个violations）
- First match wins（每个violation最多waive一次）
- Order stability（剩余violations保持顺序）
- unused_waivers计算

**关键函数**:
- `apply_waiver_rules()` - Waiver主入口
- `apply_global_waiver()` - Global waiver逻辑
- `apply_selective_waiver()` - Selective waiver逻辑
- `match_violation_with_waivers()` - Violation匹配

**Policy注入**:
- Selective waiver: `default_match="exact"`, `regex_mode="match"`

**Violation text source (Locked)**:
```python
violation_text = v.get("expected") or v.get("value") or v.get("description") or ""
```

### L5: Output Controller
- CR5 strict key filtering
- 按Type过滤输出keys
- 缺失keys补充默认值（空列表）
- 输出验证

**关键函数**:
- `filter_output_keys()` - CR5过滤主函数
- `validate_cr5_output()` - 输出验证
- `initialize_internal_result()` - 内部状态初始化

### L6: Report Generator
- Log格式生成（详细）
- YAML Summary生成
- Excel报告生成（可选）
- Failure/Warning分类（by severity）

**关键函数**:
- `generate_log_file()` - 生成详细Log
- `generate_summary_dict()` - 生成Summary字典
- `generate_summary_yaml()` - 生成YAML

## 数据流示例

```python
# L0: Config normalization
config = validate_and_normalize_config(
    requirements={'value': 2, 'pattern_items': ['p1', 'p2']},
    waivers={'value': 0, 'waive_items': ['global']},
    input_files=['/path/file.rpt'],
    description="Test checker"
)
type_id = determine_type(config['req_value'], config['waiver_value'])  # → 3

# L1+L2: Parse files
parsed_items_all, searched_files = orchestrate_parsing(
    input_files=config['input_files'],
    atom_a_func=my_atom_a,
    io_read_func=read_file_content
)

# L3: Check
check_result = assemble_check(
    requirements=config,
    parsed_items_all=parsed_items_all,
    searched_files=searched_files,
    atom_b_func=my_atom_b,
    atom_c_func=my_atom_c,
    description=config['description']
)

# L4: Waiver
final_result = apply_waiver_rules(
    check_result=check_result,
    waive_items=config['waive_items'],
    waiver_value=config['waiver_value'],
    type_id=type_id,
    atom_b_func=my_atom_b
)

# L5: Output filter
final_output = filter_output_keys(final_result, type_id=type_id)

# L6: Report
generate_log_file(
    l5_output=final_output,
    type_id=type_id,
    item_id="MY-CHECKER-01",
    item_desc="My checker",
    output_path=Path("output.log")
)
```

## 测试覆盖

### 单元测试
- L0: 14个测试（normalize_value, domain validation, type决策）
- L1: 8个测试（文件读取, gzip, 编码fallback, 路径解析）
- L2: 7个测试（递归, loop detection, max depth, 排序）
- L3: 8个测试（Pattern/Existence check, 边界情况）
- L4: 9个测试（Global/Selective waiver, order stability）
- L5: 8个测试（CR5过滤, 验证, 默认值）
- L6: 8个测试（Log/YAML生成, Summary格式）

### 集成测试
- Type 1: Existence check PASS
- Type 2: Pattern check with missing
- Type 3: Selective waiver
- Type 4: Global waiver

## 关键边界情况处理

1. **空pattern_items**: 所有parsed items成为extra_items, status=FAIL
2. **None line_number**: 排序时视为+∞，排在最后
3. **Ghost records**: source_file="", matched_content="", parsed_fields={}
4. **Global waiver**: violations保留，只修改severity和tag
5. **Selective waiver**: violations MOVE，保持order stability
6. **parsed_fields=None**: Atom B内部视为{}，不抛异常

## 依赖说明

- **pytest**: 单元测试框架
- **pyyaml**: YAML文件生成

无其他外部依赖，所有功能使用Python标准库实现。

## 实现状态

✅ **完成并测试通过**:
- L0: Config Validator
- L1: IO Engine
- L2: Parsing Orchestration
- L3: Check Assembler
- L4: Waiver Engine
- L5: Output Controller
- L6: Report Generator (Log + YAML)

✅ **所有单元测试通过**: 7/7 layers
✅ **集成测试通过**: 4/4 Type scenarios

## 下一步扩展

可选增强功能（不影响核心框架）：
1. Excel报告生成器（L6扩展）
2. HTML Dashboard（L6扩展）
3. Atom A/B/C的参考实现
4. 性能优化（大文件处理）
5. 并行解析支持

## 参考文档

- Plan.txt: 完整设计规范
- L0-L6 ExecutionPlan.md: 各层详细实现文档
- DICT_ONLY_CLARIFICATION.md: 架构原则说明

---

**实现完成时间**: 2026-01-26
**所有测试通过**: ✅
**符合Plan.txt规范**: ✅
