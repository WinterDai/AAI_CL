# 📋 Dict-Only架构原则澄清文档

## 修订日期: 2026-01-26
## 基于: Plan.txt 10.2 完整审查

---

## 🔍 核心发现

### Plan.txt的明确证据

**Plan.txt中定义的类型别名:**
- Line 25: `ParsedItem = Dict[str, Any]`
- Line 69: `MatchResult = Dict[str, Any]`

**Plan.txt中没有的内容:**
- ❌ 没有 `class NormalizedConfig`
- ❌ 没有 `class ParseResult`
- ❌ 没有 `class IOEngine`
- ❌ 没有 `class CheckResult`
- ❌ 没有 `class WaiverResult`
- ❌ 没有任何 `@dataclass` 装饰器

**结论:**
Plan.txt的设计意图是**所有跨层传递的数据结构使用Dict**。

---

## ✅ 已完成的文档修正

### 1. L0_ExecutionPlan.md

**修改内容:**
- ❌ 移除了 `class NormalizedConfig` 定义
- ✅ 改为返回 `Dict[str, Any]`
- ✅ 测试代码中 `config.pattern_items` → `config['pattern_items']`
- ✅ 添加了架构原则声明

**返回值结构:**
```python
def validate_and_normalize_config(...) -> Dict[str, Any]:
    return {
        'req_value': Union[str, int],
        'waiver_value': Union[str, int],
        'pattern_items': List[str],
        'waive_items': List[str],
        'input_files': List[str],
        'description': str
    }
```

---

### 2. L1_ExecutionPlan.md

**审查结果:**
- ✅ L1已经使用模块函数（`read_file_text()`, `resolve_indirect_reference()`）
- ✅ 没有 `class IOEngine` 定义
- ✅ 无需修改

**重要说明:**
INTEGRATION_EXAMPLE中之前写的 `io_engine = IOEngine()` 是错误的，L1使用函数不是类。

---

### 3. L2_ExecutionPlan.md

**修改内容:**
- ✅ 已经改用 `Tuple[List[ParsedItem], List[str]]` 返回（之前修改）
- ❌ 移除了 `orchestrate_parsing()` 的 `io_engine` 参数
- ✅ L2内部直接导入L1函数：`from l1_io_engine import read_file_text`
- ✅ 为 `RecursionGuard` 类添加说明（内部工具类，非跨层数据结构）

**函数签名更新:**
```python
# 之前:
def orchestrate_parsing(input_files, atom_a_func, io_engine) -> ParseResult

# 现在:
def orchestrate_parsing(input_files, atom_a_func) -> Tuple[List[ParsedItem], List[str]]
```

---

### 4. L3_ExecutionPlan.md

**审查结果:**
- ✅ 已经使用 `Dict` 返回值（之前修改）
- ✅ 没有 `class CheckResult` 定义
- ✅ Atom B调用形式已正确
- ✅ 无需修改

---

### 5. L4_ExecutionPlan.md

**审查结果:**
- ✅ 已经使用 `Dict` 返回值（之前修改）
- ✅ 没有 `class WaiverResult` 定义
- ✅ 原地修改语义明确
- ✅ 无需修改

---

### 6. L5_ExecutionPlan.md

**修改内容:**
- ✅ 集成示例中 `normalized_config.req_value` → `normalized_config['req_value']`
- ✅ `parse_result.parsed_items_all` → 改为tuple解包
- ✅ 更新了完整流程示例

---

### 7. L6_ExecutionPlan.md

**审查结果:**
- ✅ 有 `class OutputFormat(Enum)` 但这是**常量定义**
- ✅ 为Enum添加了澄清说明
- ✅ Enum不违反Dict-only原则（它不是数据结构）

**说明:**
```python
# OutputFormat是常量，用于参数验证
# 数据传递仍使用Dict，Enum只是格式选项
```

---

### 8. INTEGRATION_EXAMPLE.md

**修改内容:**
- ✅ `normalized.req_value` → `normalized['req_value']`
- ✅ `normalized.input_files` → `normalized['input_files']`
- ❌ 移除了 `io_engine = IOEngine()` 实例化
- ✅ `orchestrate_parsing()` 调用移除 `io_engine` 参数
- ✅ `parse_result.parsed_items_all` → tuple解包
- ✅ Debug函数中所有对象访问改为Dict访问

**修改前后对比:**
```python
# 之前:
io_engine = IOEngine()
parse_result = orchestrate_parsing(input_files, atom_a, io_engine)
check_result = assemble_check_result(..., parse_result.parsed_items_all, ...)

# 现在:
parsed_items_all, searched_files = orchestrate_parsing(input_files, atom_a)
check_result = assemble_check_result(..., parsed_items_all, ...)
```

---

## 🎯 架构原则总结

### 1. 跨层数据传递规则

| 层级 | 输入类型 | 输出类型 |
|------|---------|---------|
| L0 | Dict (config) | **Dict** (normalized) |
| L1 | str (path) | str (text) |
| L2 | List, Callable | **Tuple[List[Dict], List[str]]** |
| L3 | Dict, List[Dict] | **Dict** (check_result) |
| L4 | Dict | **Dict** (modified in-place) |
| L5 | Dict | **Dict** (filtered) |
| L6 | Dict | str/bytes (output files) |

### 2. 允许的类定义

| 类型 | 允许 | 原因 |
|------|------|------|
| Exception类 | ✅ | 标准Python异常机制 |
| Enum类 | ✅ | 常量定义，非数据结构 |
| 内部工具类 | ✅ | 如RecursionGuard，不跨层传递 |
| 数据结构类 | ❌ | 违反Plan.txt的Dict-only原则 |

### 3. 代码风格指南

**正确 ✅:**
```python
# 访问Dict字段
normalized = validate_and_normalize_config(...)
req_value = normalized['req_value']

# 解包Tuple返回值
parsed_items, searched_files = orchestrate_parsing(...)
```

**错误 ❌:**
```python
# 对象属性访问
normalized = validate_and_normalize_config(...)
req_value = normalized.req_value  # ❌ 错误

# 假设返回对象
parse_result = orchestrate_parsing(...)
items = parse_result.parsed_items_all  # ❌ 错误
```

---

## 📊 修改统计

| 文档 | 修改数量 | 主要变更 |
|------|---------|---------|
| L0 | 3处 | 移除class，改Dict，更新测试 |
| L1 | 0处 | 已经正确 |
| L2 | 2处 | 移除io_engine参数，添加说明 |
| L3 | 0处 | 之前已修正 |
| L4 | 0处 | 之前已修正 |
| L5 | 1处 | 更新集成示例 |
| L6 | 1处 | 添加Enum说明 |
| INTEGRATION | 4处 | 全面改用Dict访问 |
| **总计** | **11处** | **完整统一Dict-only原则** |

---

## 🚀 实施检查清单

实现者在编写代码时，请确认:

- [ ] 所有跨层函数返回 `Dict` 或 `Tuple`，不返回自定义类对象
- [ ] 使用 `data['key']` 访问字段，不使用 `data.key`
- [ ] L1使用模块函数（`read_file_text()`），不实例化IOEngine
- [ ] L2的 `orchestrate_parsing()` 只接收2个参数
- [ ] L0返回的normalized是Dict，可以用 `normalized['req_value']` 访问
- [ ] L2返回Tuple，使用 `items, files = orchestrate_parsing(...)` 解包
- [ ] 测试代码使用Dict访问语法

---

## ✍️ 文档版本

- **创建日期:** 2026-01-26
- **基于:** Plan.txt 10.2 完整审查
- **修订次数:** 1
- **状态:** 完整澄清完成

---

## 📚 相关文档

- [Plan.txt](Plan.txt) - 架构规范源文件
- [L0-L6 ExecutionPlans](.) - 各层执行计划
- [INTEGRATION_EXAMPLE.md](INTEGRATION_EXAMPLE.md) - 集成示例
- [QUESTIONS_FOR_USER.md](QUESTIONS_FOR_USER.md) - 之前的疑问（已解决）
