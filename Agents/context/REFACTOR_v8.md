# ContextAgent v8.0 重构说明

## 版本演进

- **v6.0**: 两层模型（Layer 0 + Layer 2）
- **v7.0**: 单层简化模型（单次LLM调用）
- **v8.0**: 多轮渐进式模型（Chain of Thought + 分段生成）

---

## v8.0 核心变更

### 1. System Prompt 整合

**新文件：claude.md**
- 合并 `global_rules.md` 的全部内容（543行）
- 添加角色定义（Senior Physical Implementation Engineer）
- 添加核心原则（4条）
- 添加输出格式要求

**替代关系**：
- ❌ `global_rules.md` → ✅ `claude.md` (作为 system prompt)
- ✅ `ItemSpec_Generation_Prompt.md` (保留作为参考)
- ✅ `ItemSpec_Template_EN.md` (保留，分段使用)

---

### 2. 多轮对话架构

**4 轮渐进式生成**：

```
Round 1: 分析理解 (Chain of Thought)
  输入: 配置 + 指导原则
  输出: <analysis> 识别信息类别、字段、验证项、豁免场景
  
Round 2: 生成 Parsing Logic
  输入: 分析结果 + Section 1 模板
  输出: <section1> 完整的 Parsing Logic
  
Round 3: 生成 Check Logic
  输入: Section 1 + 分析结果 + Section 2 模板
  输出: <section2> 完整的 Check Logic
  
Round 4: 生成 Waiver Logic
  输入: Section 1+2 + 分析结果 + Section 3 模板
  输出: <section3> 完整的 Waiver Logic
  
最终: 组装完整 ItemSpec
```

---

### 3. XML 标签结构化

**每轮 Prompt 使用 XML 标签**：

```xml
<task>明确本轮任务</task>
<configuration>YAML配置</configuration>
<analysis_reference>前一轮分析</analysis_reference>
<template_section>本轮要填充的模板</template_section>
<instructions>详细指导步骤</instructions>
```

**输出也使用 XML 标签**：
```xml
<analysis>...</analysis>
<section1>...</section1>
<section2>...</section2>
<section3>...</section3>
```

---

### 4. Debug 功能增强

**保留所有中间结果**（当 debug_mode=True）：

```
output_v8/
├── IMP-10-0-0-00_ItemSpec.md  # 最终输出
└── debug/
    ├── system_prompt.md        # System prompt (claude.md)
    ├── config.yaml             # 配置文件
    ├── round1_prompt.md        # Round 1 输入
    ├── round1_response.md      # Round 1 完整响应
    ├── round1_analysis.md      # 提取的分析内容
    ├── round2_prompt.md        # Round 2 输入
    ├── round2_response.md      # Round 2 完整响应
    ├── round2_section1.md      # 提取的 Section 1
    ├── round3_prompt.md        # Round 3 输入
    ├── round3_response.md      # Round 3 完整响应
    ├── round3_section2.md      # 提取的 Section 2
    ├── round4_prompt.md        # Round 4 输入
    ├── round4_response.md      # Round 4 完整响应
    └── round4_section3.md      # 提取的 Section 3
```

---

## 技术优势

### Chain of Thought 优势

1. **更好的语义理解**：第一轮专注于分析，不急于生成
2. **减少幻觉**：逐步推理，有据可查
3. **可追溯**：每步决策都有明确依据

### 分段生成优势

1. **降低单次 Prompt 长度**：每轮 5K-10K tokens（vs. v7.0 的 80K）
2. **提高质量**：每个 Section 独立生成，专注度更高
3. **易于调试**：可以单独重跑某个 Section
4. **渐进式信息注入**：前一轮的输出指导后一轮

### XML 标签优势

1. **Claude 最佳实践**：Claude 对 XML 结构理解更好
2. **清晰的边界**：输入输出明确分离
3. **易于提取**：正则表达式准确提取内容
4. **结构化思考**：引导 LLM 按结构输出

---

## 性能对比

| 指标 | v7.0 | v8.0 | 变化 |
|------|------|------|------|
| LLM 调用次数 | 1 次 | 4 次 | +300% |
| 单次 Prompt Token | 80K | 10K-20K | -75% |
| 总 Token 消耗 | 80K | 80K-100K | +0~25% |
| 执行时间 | 30s | 60-90s | +100~200% |
| 输出质量 | 中 | 高 | ⬆️ |
| 可调试性 | 低 | 高 | ⬆️⬆️ |
| 可维护性 | 中 | 高 | ⬆️ |

**权衡**：
- ❌ 时间更长（2-3倍）
- ❌ 成本略高（+0~25%）
- ✅ 质量更高（逐步推理）
- ✅ 可调试性强（中间结果完整）
- ✅ 失败可恢复（单个 Section 重跑）

---

## 使用方式

### 命令行

```bash
cd Agentic-AI/agents/demo/context
python agent.py IMP-10-0-0-00.yaml output_v8
```

### Python API

```python
agent = ContextAgent(debug_mode=True)
result = await agent.process({
    "config_path": "IMP-10-0-0-00.yaml",
    "output_dir": "output_v8"
})

# 访问中间结果
rounds = result.artifacts.get('rounds', {})
print(rounds['analysis'])   # Round 1 分析
print(rounds['section1'])   # Section 1
print(rounds['section2'])   # Section 2
print(rounds['section3'])   # Section 3
```

### 测试

```bash
python test_v7.py  # 文件名保持不变，但内容已更新为 v8.0
```

---

## 文件清单

### 新增文件
- ✅ `claude.md` - 新的 system prompt（合并版）

### 修改文件
- ✅ `agent.py` - 重构为多轮对话
- ✅ `test_v7.py` - 更新测试（文件名未变）

### 保留文件（作为参考）
- ✅ `global_rules.md` - 原始规则（已被 claude.md 替代）
- ✅ `ItemSpec_Generation_Prompt.md` - 生成指南（按需加载）
- ✅ `ItemSpec_Template_EN.md` - 模板（分段加载）

---

## 代码结构

### 新增方法

```python
# LLM 调用
async _llm_call_single(system_prompt, user_prompt, round_name) -> str

# Prompt 构建（4轮）
_build_round1_prompt(config, generation_prompt) -> str  # 分析理解
_build_round2_prompt(analysis, template_section1) -> str  # Parsing Logic
_build_round3_prompt(section1, analysis, template_section2) -> str  # Check Logic
_build_round4_prompt(section1, section2, analysis, template_section3) -> str  # Waiver Logic

# 工具方法
_load_template_sections(template_path) -> Dict[str, str]  # 分割模板
_extract_xml_content(text, tag) -> str  # 提取 XML 标签内容
```

### 修改方法

```python
_run_pipeline(config_path, output_dir) -> Dict
  # v7.0: 单次 LLM 调用
  # v8.0: 4 轮渐进式调用 + 组装
```

---

## 迁移指南

### 从 v7.0 迁移

1. **更新代码**：使用新的 agent.py

2. **确认文件**：
   - ✅ `claude.md` 存在
   - ✅ `ItemSpec_Generation_Prompt.md` 存在
   - ✅ `ItemSpec_Template_EN.md` 存在

3. **调整调用**（无变化）：
   ```python
   # API 完全兼容，无需修改调用代码
   agent = ContextAgent(debug_mode=True)
   result = await agent.process({...})
   ```

4. **访问新功能**：
   ```python
   # 新增：访问中间结果
   rounds = result.artifacts['rounds']
   ```

---

## 优化建议

### 已实现
- ✅ System Prompt 合并
- ✅ 多轮对话结构
- ✅ XML 标签引导
- ✅ Chain of Thought
- ✅ 分段生成
- ✅ 完整 Debug

### 未来改进
- ⏸️ 并行生成（Section 1-3 可能部分并行）
- ⏸️ 缓存机制（相同配置跳过 Round 1）
- ⏸️ 失败重试（单个 Section 失败时重跑）
- ⏸️ Few-Shot Examples（为每个 Section 提供示例）

---

## 总结

v8.0 实现了以下目标：

1. ✅ **合并 System Prompt**：claude.md = global_rules + 角色 + 格式
2. ✅ **多轮对话结构**：4 轮渐进式生成
3. ✅ **XML 标签引导**：所有输入输出结构化
4. ✅ **Chain of Thought + 分段生成**：混合策略
5. ✅ **保留所有细节**：无丢失语义，上下文一致
6. ✅ **完整 Debug**：所有中间版本可追溯

**适用场景**：
- ✅ 需要高质量输出
- ✅ 需要可调试性
- ✅ 可接受 2-3 倍执行时间
- ✅ 愿意投入 25% 额外成本

**不适用场景**：
- ❌ 需要实时响应（< 30s）
- ❌ 成本敏感型应用
- ❌ 简单任务（不需要分析）
