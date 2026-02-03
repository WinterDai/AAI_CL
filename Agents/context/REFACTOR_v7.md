# ContextAgent v7.0 重构说明

## 版本历史

- **v6.0**: 两层模型（Layer 0 + Layer 2，移除 Layer 1）
- **v7.0**: 单层简化模型（完全重构）

---

## 重构概述

### 架构变更

**v6.0 架构（已废弃）**：
```
Config + Files
    ↓
Preprocessors (Config Loader + File Reader)
    ↓
Layer 0 (Semantic Intent - 动态生成 prompt)
    ↓
Layer 2 (Type Specifications - 动态生成 prompt)
    ↓
Postprocessors (JSON Validator + README Renderer + Gate)
    ↓
Output: README.md + context_output.json
```

**v7.0 架构（新）**：
```
Config (item.yaml)
    ↓
Load Prompts (global_rules.md + ItemSpec_Generation_Prompt.md + ItemSpec_Template_EN.md)
    ↓
LLM Call (system_prompt + user_prompt)
    ↓
Output: <item_id>_ItemSpec.md
```

---

## 核心变更

### 1. Prompt 方式变更

**v6.0**：
- Layer 0: 使用 `build_layer0_prompt()` 函数动态构建 prompt
- Layer 2: 使用 `build_layer2_prompt()` 函数动态构建 prompt
- Prompt 定义在 `layers.py` 中

**v7.0**：
- System Prompt: 直接读取 `global_rules.md` 文件
- User Prompt: 组合 `ItemSpec_Generation_Prompt.md` + YAML配置 + `ItemSpec_Template_EN.md`
- 无需动态构建，prompt 完全外部化

### 2. 移除的组件

以下组件在 v7.0 中**完全移除**：

#### Preprocessors
- ❌ `config_loader.py` - ConfigSummary 数据类
- ❌ `file_reader.py` - FileAnalysis 数据类

#### Layers
- ❌ `layers.py` - 所有 Layer 0/1/2 的 prompt 构建函数
- ❌ Layer 0 数据模型（SemanticIntent, FormatSpec）
- ❌ Layer 1 数据模型（ExtractionFieldV2）
- ❌ Layer 2 数据模型（ItemSpec, TypeSpec）

#### Postprocessors
- ❌ `json_validator.py` - JSON 验证器
- ❌ `readme_renderer.py` - README 渲染器
- ❌ Gate - ItemSpec 门禁检查

#### Models
- ❌ `models.py` - 所有数据模型定义

### 3. 保留的组件

以下组件在 v7.0 中**继续使用**：

✅ `protocols.py` - BaseAgent 和 AgentResult 接口
✅ `llm_skill.py` - LLM 调用封装
✅ YAML 配置文件格式（item.yaml）

---

## 文件变更对比

### agent.py 变更

| 功能 | v6.0 | v7.0 |
|------|------|------|
| 代码行数 | ~517 行 | ~333 行 |
| 依赖导入 | 14 个导入 | 3 个导入 |
| 主要方法 | `_run_two_layer_model()`, `_render_v6_readme()` | `_run_pipeline()`, `_build_user_prompt()` |
| LLM 调用 | 2 次（Layer 0 + Layer 2，可能重试） | 1 次 |
| 输出格式 | JSON + README | 纯 Markdown |

### 新增文件

v7.0 需要以下外部文件（必须存在）：
- `global_rules.md` - System Prompt（543 行）
- `ItemSpec_Generation_Prompt.md` - User Prompt 模板（261 行）
- `ItemSpec_Template_EN.md` - ItemSpec 模板（301 行）

---

## 使用方式

### v6.0 用法（已废弃）

```python
agent = ContextAgent(debug_mode=True)
result = await agent.process({
    "config_path": "path/to/item.yaml",
    "output_dir": "output"
})

# 输出：
# - output/README.md
# - output/context_output.json
# - output/llm_debug/ (debug模式)
```

### v7.0 用法（新）

```python
agent = ContextAgent(debug_mode=True)
result = await agent.process({
    "config_path": "path/to/item.yaml",
    "output_dir": "output"
})

# 输出：
# - output/<item_id>_ItemSpec.md
# - output/debug/ (debug模式，包含 system_prompt.md, user_prompt.md, config.yaml)
```

### 命令行用法

```bash
# v6.0
python agent.py IMP-10-0-0-00.yaml output_v6

# v7.0
python agent.py IMP-10-0-0-00.yaml output_v7
```

---

## 输出格式变更

### v6.0 输出

**README.md**:
```markdown
# Context Agent v6.0 Output

## Item: IMP-10-0-0-00
**Description**: ...

## Data Flow Understanding
...

## TYPE1: ...
...
```

**context_output.json**:
```json
{
  "functional_units": {
    "parsing_logic": {...},
    "check_logic": {...},
    "waiver_logic": {...}
  },
  "type_specifications": {
    "type1": {...},
    ...
  },
  "_v6_metadata": {...}
}
```

### v7.0 输出

**IMP-10-0-0-00_ItemSpec.md**:
```markdown
# ItemSpec: IMP-10-0-0-00

## 1. Parsing Logic

**Information to Extract**:

### 1.1 Netlist File Information
- **Purpose**: Verify netlist version correctness
- **Key Fields**:
  - netlist_file_path: Path to netlist file
  - netlist_version: Version string
  ...

## 2. Check Logic
...

## 3. Waiver Logic
...
```

---

## 性能对比

| 指标 | v6.0 | v7.0 | 改进 |
|------|------|------|------|
| LLM 调用次数 | 2-6 次（含重试） | 1 次 | -50% ~ -83% |
| Token 消耗 | ~20K-40K | ~10K-20K | -50% |
| 执行时间 | 30-60s | 15-30s | -50% |
| 代码复杂度 | 高（三层抽象） | 低（直接调用） | 显著降低 |

---

## 迁移指南

### 从 v6.0 迁移到 v7.0

1. **更新 agent.py**：使用新版本代码

2. **准备 Prompt 文件**：
   - 确保 `global_rules.md` 存在且更新
   - 确保 `ItemSpec_Generation_Prompt.md` 存在
   - 确保 `ItemSpec_Template_EN.md` 存在

3. **更新调用代码**：
   - 输出文件名从 `README.md` 改为 `<item_id>_ItemSpec.md`
   - 输出格式从 JSON + README 改为纯 Markdown

4. **移除依赖**：
   - 不再需要 `layers.py`
   - 不再需要 `models.py`
   - 不再需要 preprocessors 和 postprocessors

### 向后兼容性

⚠️ **v7.0 不向后兼容 v6.0**

- 输出格式完全不同
- 无法直接使用 v6.0 的输出
- 需要重新生成所有 ItemSpec

---

## 优势

v7.0 相比 v6.0 的优势：

1. **简化架构**：单次 LLM 调用，无中间层
2. **Prompt 外部化**：易于调试和修改，无需改代码
3. **Token 效率**：减少 50% 的 Token 消耗
4. **执行速度**：减少 50% 的执行时间
5. **易于维护**：代码量减少 35%，复杂度大幅降低
6. **输出直观**：直接生成 Markdown，无需后处理

## 劣势

v7.0 相比 v6.0 的劣势：

1. **无结构化验证**：没有 JSON 验证和 Gate 检查
2. **无重试机制**：LLM 输出质量完全依赖 Prompt
3. **无中间产物**：无法查看 Layer 0 的语义理解结果
4. **灵活性降低**：Prompt 固定，难以动态调整

---

## 测试

运行测试：

```bash
cd Agentic-AI/agents/demo/context
python test_v7.py
```

测试覆盖：
- ✅ 读取 YAML 配置
- ✅ 加载 Prompt 文件
- ✅ LLM 调用
- ✅ 输出 ItemSpec Markdown
- ✅ Debug 模式输出

---

## 未来改进

可能的改进方向：

1. **增加输出验证**：检查生成的 Markdown 格式正确性
2. **支持重试**：LLM 失败时自动重试
3. **批量处理**：一次处理多个 item.yaml
4. **模板可配置**：支持自定义 ItemSpec 模板
5. **增量更新**：只更新变化的部分
