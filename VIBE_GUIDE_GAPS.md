# Vibe Coding Guide 未明确部分清单（基于 Plan_v2.txt 审查）

**审查日期**: 2026-01-27  
**审查依据**: Plan_v2.txt (10.2 FINAL LOCKED)  
**审查范围**: Agent_Vibe_Coding_guide.txt 实施可行性

---

## ✅ 已基于 Plan_v2.txt 明确事实更新的内容

以下内容已在 Agent_Vibe_Coding_guide.txt 中补充，均有 Plan_v2.txt 行号依据：

1. **Gatekeeper Node 检查项补充**：
   - Atom A 双参数签名要求 `(text: str, source_file: str)` (Plan_v2.txt L18)
   - Atom B 'kind' 字段要求：MatchResult 必须返回 `{'is_match', 'reason', 'kind'}` (Plan_v2.txt L71, L95, L120, L133)
   - Atom C 'evidence' 字段要求：check_existence 必须返回 `{'is_match', 'reason', 'evidence'}` (Plan_v2.txt L157)
   - Gate 2 七个测试向量完整要求 (Plan_v2.txt L431-452)

2. **System Prompt 模板增强**：
   - Atom A/B/C 完整签名规范（带 Plan_v2.txt 行号引用）
   - MatchResult 和 check_existence 返回 schema 明确定义
   - 'kind' 字段的合法值列表：alternatives, regex, wildcard, contains, exact

3. **AST 验证工具规范**：
   - 基于 Plan_v2.txt 第5节 Gate 1/2 要求列出6项检查清单
   - 明确标注：Plan_v2.txt 未提供 AST 实现细节，需开发者自行实现

---

## 🚩 Plan_v2.txt 中明确**不存在**的规范（禁止擅自补充）

以下内容在 Agent_Vibe_Coding_guide.txt 中被提及，但在 Plan_v2.txt 中**找不到任何依据**：

### 1. Few-Shot Examples (少样本示例)

**出现位置**: Agent_Vibe_Coding_guide.txt L85  
**内容**: `[Insert a perfect pair of Atom A code and corresponding log snippet here]`

**审查结论**:
- Plan_v2.txt 仅在 L34-37 标注 `[AGENT FILL AREA START/END]`，未提供任何具体示例日志。
- Plan_v2.txt L12-161 包含完整的 Atom A/B/C 参考实现代码，但**没有**配对的日志样本。
- 搜索关键词 "example", "sample", "log snippet", "few.?shot" 在 Plan_v2.txt 中无匹配结果。

**问题**:
- 如何构建 Few-Shot 示例？是否需要从 Work/atoms_example.py 提取？
- Few-Shot 示例的覆盖范围？（简单 regex vs 复杂多行解析 vs 递归引用？）
- 是否需要针对不同 Type (1-4) 准备不同的示例？

**举手**：**需要用户明确 Few-Shot 示例的来源和范围**。

---

### 2. Reflect Node 修复策略

**出现位置**: Agent_Vibe_Coding_guide.txt L54-58  
**内容**: "Agent 阅读报错信息，修改 `generated_code`... Prompt 注入：'你之前的代码违背了 10.2 规范，错误是 X，请修复它。'"

**审查结论**:
- Plan_v2.txt 第5节（L405-488）定义了 Gate 1/2/3 的**测试要求**，但未定义"测试失败后如何修复"的策略。
- Plan_v2.txt 仅声明 "Generated code MUST pass ALL tests before Runtime integration" (L405)，未提供失败后的补救流程。

**问题**:
- 如果 Agent 连续3次修复仍未通过 Gate 1 检查，是否应该回退到用户交互（HITL）？
- Reflect Node 的 Prompt 应该包含什么级别的错误详情？（仅错误类型 vs 具体代码行号？）
- 是否允许 Agent 部分重写（例如只修复 Atom B）还是必须全部重新生成？

**举手**：**需要用户定义 Reflect Node 的失败处理策略和迭代上限**。

---

### 3. 流式输出 (Streaming) 实现细节

**出现位置**: Agent_Vibe_Coding_guide.txt L104-107  
**内容**: "Agent 的思考过程和代码生成过程需要**流式传输**到前端... 用户应该看到：'正在分析日志结构... 识别到时间戳...'"

**审查结论**:
- Plan_v2.txt 是**纯框架规范**，不涉及任何 Agent 实现细节。
- 搜索 "stream", "output", "frontend", "UI", "user experience" 在 Plan_v2.txt 中无匹配。
- Plan_v2.txt 关注的是 Atom 的**函数契约** (L18, L68, L145)，不关心 Agent 如何生成这些函数。

**问题**:
- LangGraph 的 `astream_events()` 如何与 Gatekeeper Node 集成？（Gatekeeper 是同步工具调用还是异步？）
- 流式输出的粒度？（按节点 vs 按 LLM token？）
- 错误日志是否也需要流式传输？（如果 Gate 1 失败，用户立即看到还是等 Reflect Node 修复后一起显示？）

**举手**：**需要用户明确流式输出的技术实现方案和 UX 需求**。

---

### 4. LangGraph 条件边（Conditional Edge）的具体逻辑

**出现位置**: Agent_Vibe_Coding_guide.txt L60-63  
**内容**: "如果 `error_logs` 为空 -> **End**... 如果 `error_logs` 有值 -> 回到 **Reflect Node** (最多重试 3 次)"

**审查结论**:
- Plan_v2.txt 未定义"重试次数上限"或"循环终止条件"。
- Plan_v2.txt L405 仅说 "MUST pass ALL tests"，未说明"如果无法通过测试应该怎么办"。

**问题**:
- 为什么是"最多重试 3 次"？这个数字的依据是什么？
- 如果3次后仍未通过，Agent 是否应该：
  - 返回最接近正确的版本 + 警告信息？
  - 直接失败并要求用户手动介入？
  - 降级到更简单的模板代码？

**举手**：**需要用户定义循环终止策略和失败降级方案**。

---

### 5. AST 工具的完整实现规范

**出现位置**: Agent_Vibe_Coding_guide.txt L96-102（已更新），原 validate_10_2_compliance 工具

**审查结论**:
- Plan_v2.txt 第5节定义了**测试要求**（Gate 1-3），但未提供 AST 解析的实现细节。
- Plan_v2.txt L409-427 仅描述"Signature Check 必须检查函数存在"和"Schema Check 必须检查 key 存在"，但未说明"如何提取函数签名"或"如何验证返回值 schema"。
- 现有 Work/verify_agent_guide.py 包含一个简化的签名检查实现，但它是**外部验证脚本**，不是 Plan_v2.txt 的一部分。

**问题**:
- AST 工具应该使用 Python 的 `ast` 模块还是 `inspect` 模块？
- 如何验证 Atom B 的 `default_match` 和 `regex_mode` 参数存在？（检查函数签名 vs 检查 AST 的 arguments 节点？）
- 如何验证 MatchResult 的 'kind' 字段存在？（静态分析 return 语句 vs 运行时执行测试？）

**举手**：**需要用户提供 AST 工具的参考实现或指定实现技术栈**。

---

## 📋 推荐后续行动

### 必须由用户明确的决策点（按优先级排序）：

1. **Few-Shot 示例来源** [高优先级]
   - 建议：是否使用 Work/atoms_example.py 的代码作为 Few-Shot？
   - 或者需要准备多个覆盖不同复杂度的示例？

2. **Reflect Node 失败处理策略** [高优先级]
   - 最大重试次数？（当前 guide 中写的是3次）
   - 失败后是否触发 HITL（人工介入）？

3. **AST 工具实现方案** [中优先级]
   - 是否直接使用 verify_agent_guide.py 的逻辑？
   - 是否需要扩展以支持运行时测试（例如执行 Gate 2 的7个测试向量）？

4. **流式输出技术方案** [低优先级]
   - 是否必须实现？还是可以先实现同步版本？
   - LangGraph 的 astream_events API 是否已经验证可行？

5. **条件边循环终止逻辑** [低优先级]
   - 3次重试的依据？是否需要调整？
   - 失败降级方案？（返回部分代码 vs 完全失败）

---

## 总结

**已完成**：基于 Plan_v2.txt 明确事实，补充了 Gatekeeper 检查项、System Prompt schema、AST 工具检查清单。

**待用户决策**：5个关键实现细节（Few-Shot、Reflect 策略、Streaming、循环终止、AST 实现）在 Plan_v2.txt 中不存在，需要用户提供额外的设计决策或参考实现。

**禁止擅自补充**：上述5个部分在当前版本的 Agent_Vibe_Coding_guide.txt 中保持原样或标注"需实现者自行决定"，不添加未经验证的假设。
