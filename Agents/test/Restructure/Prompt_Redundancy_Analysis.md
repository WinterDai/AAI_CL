# Prompt架构冗余分析报告

> 生成日期: 2026-01-03  
> 分析范围: CLAUDE.md (System Prompt 865行) vs prompts.py (User Prompt 1278行)  
> 分析原则: 基于Anthropic Cookbook实地考察结果

---

## 一、Anthropic官方指导 (事实依据)

### 1. Progressive Disclosure - **不适用于我们**

**来源**: `claude-cookbooks/skills/README.md`

```
"Progressive Disclosure Architecture - Skills load only when needed, optimizing token usage"
三层加载: Metadata → Full Instructions → Linked Files
```

**关键发现**: 
- ✅ 这是**Skills Framework**的设计 (多次交互，动态加载)
- ❌ 我们的CodeGen是**单次API调用**，无法分阶段加载
- **结论**: 按需提供Prompt **不适用于我们的场景**

### 2. Agent Prompt Pattern - **支持详细Prompt**

**来源**: `claude-cookbooks/patterns/agents/prompts/research_lead_agent.md`

Anthropic自己的Agent System Prompt:
- 长度: 150+ lines详细指令
- 格式: Markdown，无刻意压缩
- 特点: 极度详细的流程分解、清晰的边界定义

**关键发现**:
- ✅ Anthropic自己的Agent Prompt **没有按需提供**，而是一次性给全
- ✅ 我们的CLAUDE.md (865行) 与Anthropic模式一致
- **结论**: 详细的System Prompt是合理的

### 3. 关于冗余的唯一警告

**来源**: `claude-cookbooks/patterns/agents/prompts/citations_agent.md`

```
"No redundant citations close to each other: Do not place multiple citations 
to the same source in the same sentence"
```

**关键发现**:
- ⚠️ 这是唯一提到"redundant"的地方
- ⚠️ 说的是**输出格式**，不是Prompt工程
- **结论**: Anthropic文档中**没有**关于"System Prompt和User Prompt冗余"的警告

---

## 二、冗余分析表 (详细对比)

| # | System Prompt (CLAUDE.md) | User Prompt (prompts.py) | 重复内容 | 冗余程度 | 优化建议 |
|---|---------------------------|--------------------------|----------|----------|----------|
| **1. API契约** | | | | | |
| 1.1 | Section 2.1: `DetailItem` 完整签名 (5参数+Severity枚举) + 4个示例 (~80行) | Grounding Section: 无DetailItem签名，仅在reference_snippets中可能出现用法 | 无重复 | ✅ 无冗余 | 保持现状。System=Reference，User=Examples |
| 1.2 | Section 2.2: `create_check_result` 完整签名 (9参数) + 示例 (~30行) | Grounding Section + Fillable Templates: 展示用法，不是签名定义 | 轻微重复 (用法示例) | 🟡 低冗余 | 建议: User Prompt用`<see CLAUDE.md §2.2>`代替完整示例 |
| 1.3 | Section 2.3: Mixin方法表格 (12个方法，签名+用途) (~40行) | _build_output_instructions(): 提到"Full API contracts in System Prompt" | 无重复 | ✅ 无冗余 | 已做单向引用，保持现状 |
| **2. 框架方法** | | | | | |
| 2.1 | Section 2.3.1: `execute_boolean_check` 完整签名+示例 (~50行) | _build_code_reuse_architecture_section(): 重复展示框架方法用法 (~100行) | **高度重复** | 🔴 **高冗余** | **优先优化**: User Prompt删除完整示例，改为`<see CLAUDE.md §2.3.1>` + 1行调用示例 |
| 2.2 | Section 2.3.2: `execute_value_check` 完整签名+示例 (~50行) | _build_code_reuse_architecture_section(): 重复展示框架方法用法 (~100行) | **高度重复** | 🔴 **高冗余** | **优先优化**: 同上 |
| 2.3 | Section 2.4: `name_extractor` 回调说明 + 完整示例 (~40行) | _build_code_reuse_architecture_section(): 再次展示name_extractor示例 (~30行) | **完全重复** | 🔴 **高冗余** | **优先优化**: User Prompt删除完整示例，改为简短说明 |
| **3. Type规则** | | | | | |
| 3.1 | Section 4: Type 1-4速查表 (requirements/waivers/检查逻辑) | _build_type_specs_section(): XML格式展示Pass/Fail条件 | 轻微重复 (格式不同) | 🟡 低冗余 | 保持。System=表格概览，User=运行时配置详情 |
| 3.2 | Section 5: 运行时参数获取 (pattern_items/waive_items代码) | _build_type_semantics_section(): `<runtime_parameters>` XML + 代码模板 | **部分重复** | 🟠 中冗余 | **建议**: User Prompt只给XML结构，代码模板指向System Prompt |
| **4. 边缘情况** | | | | | |
| 4.1 | Section 5.5: 文件路径存在但不可访问 (详细说明 ~60行) | Grounding Section可能包含Golden代码示例 | 无直接重复 | ✅ 无冗余 | System=理论说明，User=具体Golden案例 |
| 4.2 | Section 5.5.2: SPEF跳过处理 (Type1/4 vs Type2/3区别 ~50行) | 同上 | 无直接重复 | ✅ 无冗余 | 保持现状 |
| **5. 完整示例** | | | | | |
| 5.1 | Section 6: Type1示例 (完整的execute_boolean_check用法 ~120行) | _build_code_reuse_architecture_section(): 三层架构完整示例 (~200行) | **高度重复** | 🔴 **高冗余** | **优先优化**: User Prompt只给架构图，完整示例指向System |
| 5.2 | Section 6: Type3示例 (完整的waiver处理 ~100行) | 无重复 | 无重复 | ✅ 无冗余 | System独有，保持 |
| **6. 输出格式** | | | | | |
| 6.1 | Section 1: 生成边界 (你生成什么/不生成什么) | _build_output_instructions(): "输出要求" | **部分重复** | 🟠 中冗余 | **建议**: User Prompt简化为`<see CLAUDE.md §1>` + XML模板 |
| 6.2 | Section 10: 常见错误 (2个对比示例) | _build_output_instructions(): "CRITICAL Reminders" | **部分重复** | 🟠 中冗余 | **建议**: User Prompt只列要点，详细对比在System |
| **7. 独立内容 (不冗余)** | | | | | |
| 7.1 | - | Grounding Section: Log samples + Reference snippets | System无 | ✅ 独立 | 保持。User Prompt专属，Few-shot学习关键 |
| 7.2 | - | Semantic Intent Section: check_target, data_flow | System无 | ✅ 独立 | 保持。User Prompt专属，任务上下文 |
| 7.3 | - | Context Agent Section: extraction_fields + matched_samples | System无 | ✅ 独立 | 保持。User Prompt专属，预生成数据 |
| 7.4 | - | Fillable Templates Section (v6.1): 90%完整代码骨架 | System无 | ✅ 独立 | 保持。User Prompt专属，具体填空指导 |
| 7.5 | - | Critical Checklist Section (v6.1): LLM自验证 | System无 | ✅ 独立 | 保持。User Prompt专属，质量保证 |
| 7.6 | Section 0: XML标签说明表 | - | User无 | ✅ 独立 | 保持。System专属，XML格式定义 |
| 7.7 | Section 0.5: 类命名规则 | - | User无 | ✅ 独立 | 保持。System专属，命名规范 |
| 7.8 | Section 3: 方法签名约束 | - | User无 | ✅ 独立 | 保持。System专属，Template兼容性 |
| 7.9 | Section 7: Helper Methods规则 | - | User无 | ✅ 独立 | 保持。System专属，设计规范 |
| 7.10 | Section 8: Waiver匹配规则 (Word-Level) | - | User无 | ✅ 独立 | 保持。System专属，算法说明 |
| 7.11 | Section 9: 学习指南 | - | User无 | ✅ 独立 | 保持。System专属，学习路径 |

---

## 三、冗余严重程度统计

| 冗余级别 | 数量 | 占比 | 涉及Section | 预估节省Token |
|----------|------|------|-------------|---------------|
| 🔴 **高冗余** (需立即优化) | 4项 | 19% | §2.3.1, §2.3.2, §2.4, §6示例 | ~800 tokens |
| 🟠 **中冗余** (建议优化) | 3项 | 14% | §5运行时参数, §1生成边界, §10常见错误 | ~400 tokens |
| 🟡 **低冗余** (可接受) | 2项 | 10% | §2.2示例, §4 Type表格 | ~100 tokens |
| ✅ **无冗余** (保持) | 12项 | 57% | 独立内容 | 0 tokens |
| **总计** | 21项 | 100% | - | **~1300 tokens** |

---

## 四、优化清单 (按优先级)

### P0 - 立即优化 (节省~800 tokens)

#### 1. 框架方法示例重复 (Section 2.3.1, 2.3.2)

**当前状态**:
- CLAUDE.md: 完整的 `execute_boolean_check` 和 `execute_value_check` 签名+示例 (~100行)
- prompts.py: `_build_code_reuse_architecture_section()` 再次展示完整用法 (~100行)

**优化方案**:
```python
def _build_code_reuse_architecture_section() -> str:
    return """# ⚠️ CRITICAL: v2.0 三层架构 - 代码复用模式

## 架构设计

```
Layer 1: _parse_input_files()          # 4个Type共享
         ↓
Layer 2: 共享逻辑模块                   
         - _boolean_check_logic()       # Type1/4 共享
         - _pattern_check_logic()       # Type2/3 共享
         ↓
Layer 3: _execute_typeN()              # 使用框架方法
```

## 框架方法 API

> **Full API signatures are in System Prompt Section 2.3**
> 
> - `execute_boolean_check()` - Type 1/4: has_waiver=False/True
> - `execute_value_check()` - Type 2/3: has_waiver=False/True

## 代码模板示例 (简化)

```python
# Type 1: Boolean check
def _execute_type1(self, parsed_data: Dict[str, Any]) -> CheckResult:
    return self.execute_boolean_check(
        parse_data_func=lambda: self._boolean_check_logic(parsed_data),
        has_waiver=False, found_desc=self.FOUND_DESC, ...
    )

# Type 3: 复用Type2逻辑
def _execute_type3(self, parsed_data: Dict[str, Any]) -> CheckResult:
    return self.execute_value_check(
        parse_data_func=lambda: self._pattern_check_logic(parsed_data),
        has_waiver=True,  # 唯一区别
        ...
    )
```

> **详细示例见 System Prompt Section 6**
"""
```

**预期效果**: 从200行精简到60行，节省~500 tokens

---

#### 2. name_extractor重复 (Section 2.4)

**当前状态**:
- CLAUDE.md: 完整的 `_build_name_extractor()` 示例 (~40行)
- prompts.py: 再次展示完整示例 (~30行)

**优化方案**:
```python
# In _build_code_reuse_architecture_section():
"""
### name_extractor 辅助方法

> **Full signature and examples in System Prompt Section 2.4**

```python
def _build_name_extractor(self):
    def extract_name(name: str, metadata: Any) -> str:
        # 根据metadata格式化name，见System Prompt §2.4示例
        ...
    return extract_name
```
"""
```

**预期效果**: 从30行精简到10行，节省~80 tokens

---

#### 3. 完整示例重复 (Section 6)

**当前状态**:
- CLAUDE.md: Type1完整示例 (~120行)
- prompts.py: 三层架构完整示例 (~100行)

**优化方案**:
```python
def _build_code_reuse_architecture_section() -> str:
    return """# ⚠️ CRITICAL: v2.0 三层架构

## 架构图
[保留架构图]

## 代码模板
[保留简化的4-5行调用示例]

> **Complete production examples: System Prompt Section 6**
> - Type 1: Boolean check with edge case handling
> - Type 3: Value check with waiver logic
"""
```

**预期效果**: 从100行精简到40行，节省~220 tokens

---

### P1 - 建议优化 (节省~400 tokens)

#### 4. 运行时参数获取 (Section 5)

**当前状态**:
- CLAUDE.md: 代码模板 (~20行)
- prompts.py: `_build_type_semantics_section()` XML + 重复的代码模板 (~50行)

**优化方案**:
```python
def _build_type_semantics_section(context: CodeGenContext) -> str:
    """构建Type语义说明 (v4.1 去重)"""
    lines = ["<runtime_parameters>"]
    lines.append("  <!-- 获取方式见 System Prompt Section 5 -->")
    
    # 只输出语义说明，不重复代码
    lines.append("  <pattern_items types=\"Type2,Type3\">")
    lines.append("    <note>从 self.item_data['requirements']['pattern_items'] 获取</note>")
    if semantic_mapping:
        lines.append(f"    <semantic>{semantic_mapping}</semantic>")
    lines.append("  </pattern_items>")
    
    # 类似处理waive_items
    ...
    
    lines.append("</runtime_parameters>")
    return "\n".join(lines)
```

**预期效果**: 从50行精简到20行，节省~150 tokens

---

#### 5. 生成边界说明 (Section 1)

**当前状态**:
- CLAUDE.md: 详细的你生成什么/不生成什么 (~40行)
- prompts.py: `_build_output_instructions()` 重复说明 (~30行)

**优化方案**:
```python
def _build_output_instructions() -> str:
    return """# 📤 输出要求

> **Generation boundaries: System Prompt Section 1**
> **Full API contracts: System Prompt Section 2**

## 输出XML格式

```xml
<class_constants>...</class_constants>
<parse_method>...</parse_method>
<execute_type1>...</execute_type1>
...
<helper_methods>
<!-- ⚠️ 所有 self._xxx() 调用必须在这里定义 -->
</helper_methods>
```

## CRITICAL Reminders
1. Method signature: `_execute_typeN(self, parsed_data)`
2. Helper methods: Define all `self._xxx()` in `<helper_methods>`
3. Waiver: Framework methods handle automatically
"""
```

**预期效果**: 从30行精简到15行，节省~120 tokens

---

#### 6. 常见错误对比 (Section 10)

**当前状态**:
- CLAUDE.md: 详细的错误/正确对比示例 (~40行)
- prompts.py: CRITICAL Reminders 重复关键点 (~20行)

**优化方案**:
```python
# In _build_output_instructions():
"""
## CRITICAL Reminders

> **Common mistakes: System Prompt Section 10**

1. Use `Severity.INFO/WARN/FAIL` (not ItemStatus)
2. Use `is_pass=True` (not CheckStatus.PASS)
3. All parameters use keyword arguments
"""
```

**预期效果**: 从20行精简到8行，节省~100 tokens

---

### P2 - 可接受的轻微冗余 (节省~100 tokens)

#### 7. create_check_result示例

**当前状态**: System有签名+示例，User有用法示例
**建议**: User Prompt用 `<see CLAUDE.md §2.2>` 代替示例

#### 8. Type规则表格

**当前状态**: System有表格，User有XML详情
**建议**: 保持。格式不同，互补而非重复

---

## 五、优化后Token预估

| 部分 | 当前Token | 优化后Token | 节省 | 节省率 |
|------|-----------|-------------|------|--------|
| System Prompt (CLAUDE.md) | ~4500 | ~4500 | 0 | 0% |
| User Prompt (prompts.py生成) | ~11000 | ~9700 | ~1300 | **11.8%** |
| **总Token (Input)** | **~15500** | **~14200** | **~1300** | **8.4%** |

**关键发现**:
- 优化主要针对User Prompt（System Prompt保持完整API文档）
- 预估节省1300 tokens，主要来自框架方法和示例重复
- 优化后仍保留11000+ tokens User Prompt，因为：
  - Grounding Data (~2000 tokens) 不可删减
  - extraction_fields + matched_samples (~1500 tokens) 是Context Agent精华
  - Fillable Templates (~2000 tokens) 是v6.1核心特性

---

## 六、TokenBudgetManager激活建议

### 当前状态

**已定义但未使用**:
```python
class TokenBudgetManager:
    """Token分配管理器 (Lines 53-115)"""
    BUDGET = {
        "golden_methods": 2500,
        "log_samples": 1500,
        ...
    }
    
    @classmethod
    def truncate_to_budget(cls, text: str, budget_key: str) -> str:
        """将文本截断到指定budget"""
        # 智能截断逻辑
        ...
```

**问题**: `build_user_prompt()` 中**从未调用** `truncate_to_budget()`

### 激活方案

```python
def build_user_prompt(...) -> str:
    sections = []
    
    # v4.2: 激活Token Budget管理
    if log_samples:
        # 智能截断Log样本
        truncated_samples = {
            name: TokenBudgetManager.truncate_to_budget(content, "log_samples")
            for name, content in log_samples.items()
        }
        sections.append(_build_grounding_section(truncated_samples, ...))
    
    # 类似处理其他大内容
    if reference_snippets:
        truncated_snippets = {
            name: TokenBudgetManager.truncate_to_budget(code, "golden_methods")
            for name, code in reference_snippets.items()
        }
        ...
    
    # === 生成报告 (调试用) ===
    if os.getenv("DEBUG_TOKEN_BUDGET"):
        components = {
            "grounding": sections[1],
            "context_agent": sections[3],
            ...
        }
        report = TokenBudgetManager.get_budget_report(components)
        print(f"[TokenBudget] Total: {report['_total']}, Over: {report['_over_budget']}")
    
    return "\n\n".join(filter(None, sections))
```

**效果**: 动态截断，确保即使有极长Log也不超budget

---

## 七、实施计划

### 阶段1: P0优化 (立即执行)

1. **修改 `_build_code_reuse_architecture_section()`**
   - 删除完整框架方法示例 (~100行)
   - 改为架构图 + 简化调用示例 + `<see System §2.3>`
   - 预估: 200行 → 60行

2. **修改 `_build_output_instructions()`**
   - 删除重复的边界说明 (~20行)
   - 改为 `<see System §1>` + XML模板
   - 预估: 30行 → 15行

3. **测试验证**
   - 运行4个Type的CodeGen测试
   - 确认生成代码质量不下降

**预期结果**: 节省~800 tokens，User Prompt从11000 → 10200

---

### 阶段2: P1优化 (第二周)

1. **修改 `_build_type_semantics_section()`**
   - 删除重复的代码模板
   - 只保留语义说明

2. **激活TokenBudgetManager**
   - 在 `build_user_prompt()` 调用 `truncate_to_budget()`
   - 添加DEBUG模式的budget报告

3. **测试验证**

**预期结果**: 再节省~400 tokens，User Prompt 10200 → 9800

---

### 阶段3: 监控与调优 (持续)

1. **监控生成质量**
   - 对比优化前后的4/4 Pass率
   - 收集Evaluator反馈的错误类型

2. **A/B测试**
   - 10个新Item用优化后Prompt
   - 10个新Item用原Prompt
   - 对比生成质量和成本

3. **持续调优**
   - 如果质量下降，回滚或调整
   - 如果质量不变，继续P2优化

---

## 八、风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| LLM看不到完整示例，生成质量下降 | 中 | 高 | 1. System Prompt保留完整示例<br>2. User Prompt给架构图辅助理解<br>3. A/B测试验证 |
| 单向引用 `<see System §X>` LLM不理解 | 低 | 中 | 1. 测试Claude对引用的理解能力<br>2. 必要时改为"详见System Prompt Section X"的自然语言 |
| TokenBudgetManager截断丢失关键信息 | 中 | 中 | 1. 智能截断保留关键行<br>2. 设置合理的budget（1500 tokens）<br>3. 保留文件头尾 |
| 优化后仍超context window | 低 | 低 | 当前15500，优化后14200，距离200k window还很远 |

---

## 九、结论

### 核心发现

1. **Anthropic没有推荐"按需提供Prompt"** (Progressive Disclosure不适用于单次调用)
2. **Anthropic的Agent Prompt也是详细的一次性给全** (150+ lines)
3. **真正的冗余主要在框架方法和示例重复** (~1300 tokens, 8.4%)

### 优化策略

- ✅ **保守优化**: 删除重复的示例和代码模板，保留所有独立内容
- ✅ **单向引用**: System = API Reference (完整)，User = Application Guide (简化+引用)
- ✅ **保留精华**: extraction_fields, Fillable Templates, Context Agent数据全部保留

### 预期效果

- Token节省: ~1300 tokens (8.4%)
- 质量风险: 低 (System Prompt保留完整文档)
- 实施难度: 中 (需修改3个函数)

### 下一步

**选择你的路径**:
1. 我立即实施P0优化 (修改3个函数)
2. 先运行TokenBudgetManager.get_budget_report()看实际分布
3. 先做A/B测试验证优化方案

---

## 附录A: TokenBudgetManager诊断脚本

```python
# Add to prompts.py for debugging
def diagnose_token_budget(codegen_context, log_samples, reference_snippets):
    """诊断当前Prompt的Token分布"""
    sections_dict = {
        "feedback": "",  # 假设无feedback
        "grounding": _build_grounding_section(log_samples, reference_snippets),
        "semantic_intent": _build_semantic_intent_section(codegen_context),
        "context_agent": _build_context_agent_section(codegen_context),
        "task_context": _build_task_header(codegen_context) + "\n" + codegen_context.to_prompt_text(),
        "type_specs": _build_type_specs_section(codegen_context),
        "code_reuse": _build_code_reuse_architecture_section(),
        "fillable_templates": build_fillable_templates_section(...),
        "output": _build_output_instructions(),
    }
    
    report = TokenBudgetManager.get_budget_report(sections_dict)
    
    print("=" * 60)
    print("Token Budget Diagnostic Report")
    print("=" * 60)
    for name, tokens in sorted(report.items(), key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True):
        if name.startswith("_"):
            continue
        print(f"{name:20s}: {tokens:5d} tokens")
    print("=" * 60)
    print(f"{'TOTAL':20s}: {report['_total']:5d} tokens")
    print(f"{'BUDGET':20s}: {report['_budget']:5d} tokens")
    print(f"{'OVER BUDGET?':20s}: {'YES ⚠️' if report['_over_budget'] else 'NO ✅'}")
    print("=" * 60)
    
    return report
```

**使用方式**:
```python
# In your test script
from CHECKLIST.Tool.Agent.agents.code_generation.prompts import diagnose_token_budget

report = diagnose_token_budget(context, log_samples, reference_snippets)
```
