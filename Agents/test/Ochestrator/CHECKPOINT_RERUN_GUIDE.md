# Orchestrator Pipeline 断点重run功能使用指南

## v1.3 新功能：断点重run

现在支持跳过特定阶段，从已有结果继续运行pipeline，适用于调试和迭代开发。

---

## 配置参数

在 `PipelineConfig` 中添加了以下断点重run控制参数：

```python
PipelineConfig(
    # 原有的运行控制（是否执行该阶段）
    run_context_agent: bool = True,
    run_codegen_agent: bool = True,
    run_validation_agent: bool = True,
    
    # v1.3: 新增断点重run控制（从缓存加载，跳过执行）
    skip_context_agent: bool = False,    # 跳过ContextAgent，从item_spec.json加载
    skip_codegen_agent: bool = False,    # 跳过CodeGenAgent，从checker.py加载
    skip_validation_agent: bool = False, # 跳过ValidationAgent，从validation_result.json加载
)
```

---

## 使用场景

### 场景1：调试ValidationAgent

**问题**：每次修改ValidationAgent代码，都要重新运行CodeGenAgent（耗时长）

**解决方案**：跳过Context和CodeGen，只运行Validation

```python
config = PipelineConfig(
    skip_context_agent=True,        # ✓ 从input_item_spec.json加载
    skip_codegen_agent=True,        # ✓ 从Check_*.py加载
    skip_validation_agent=False,    # ✗ 重新运行
    
    run_context_agent=False,
    run_codegen_agent=False,
    run_validation_agent=True,
    
    validation_use_real_executor=True,  # 真实执行checker
)
```

**示例脚本**：`run_validation_only.py`

### 场景2：调试CodeGenAgent

**问题**：每次修改CodeGenAgent代码，都要重新运行ContextAgent

**解决方案**：跳过Context，运行CodeGen和Validation

```python
config = PipelineConfig(
    skip_context_agent=True,        # ✓ 从input_item_spec.json加载
    skip_codegen_agent=False,       # ✗ 重新运行
    skip_validation_agent=False,    # ✗ 重新运行
    
    run_context_agent=False,
    run_codegen_agent=True,
    run_validation_agent=True,
)
```

**示例脚本**：`run_codegen_only.py`

### 场景3：重新生成Validation报告

**问题**：已有checker和validation结果，只想重新格式化报告

**解决方案**：跳过所有阶段，从缓存加载

```python
config = PipelineConfig(
    skip_context_agent=True,
    skip_codegen_agent=True,
    skip_validation_agent=True,     # ✓ 从validation_result.json加载
    
    run_context_agent=False,
    run_codegen_agent=False,
    run_validation_agent=False,     # 不执行，只加载
)
```

---

## 文件名匹配规则

Orchestrator会自动查找以下文件（按优先级）：

### ItemSpec加载（skip_context_agent=True）
1. `item_spec.json`（ContextAgent标准输出）
2. `input_item_spec.json`（Orchestrator使用的输入文件名）

### Checker加载（skip_codegen_agent=True）
1. `Check_{item_id}.py`（例如：`Check_5_0_0_00.py`）
2. `Check_IMP_{item_id}.py`（例如：`Check_IMP_5_0_0_00.py`）
3. `generated_checker.py`（通用名称）

### Validation结果加载（skip_validation_agent=True）
1. `validation_result.json`

---

## 工作原理

### Phase 1: ContextAgent
```
skip_context_agent=True：
  → 在output_dir查找item_spec.json或input_item_spec.json
  → 加载到pipeline_result.item_spec
  → 跳过ContextAgent.process()

skip_context_agent=False：
  → 正常运行ContextAgent
  → 保存item_spec.json
```

### Phase 2: CodeGenAgent
```
skip_codegen_agent=True：
  → 在output_dir查找Check_*.py或generated_checker.py
  → 加载到pipeline_result.generated_code
  → 跳过CodeGenAgent.process()

skip_codegen_agent=False：
  → 正常运行CodeGenAgent
  → 保存Check_*.py
```

### Phase 3: ValidationAgent
```
skip_validation_agent=True：
  → 在output_dir查找validation_result.json
  → 加载到pipeline_result.validation_report
  → 跳过ValidationAgent.process()

skip_validation_agent=False：
  → 正常运行ValidationAgent
  → 保存validation_result.json和checker_outputs/
```

---

## 示例脚本

### 1. run_validation_only.py

**用途**：只重新运行ValidationAgent（最常用）

```python
config = PipelineConfig(
    skip_context_agent=True,
    skip_codegen_agent=True,
    skip_validation_agent=False,
    
    run_context_agent=False,
    run_codegen_agent=False,
    run_validation_agent=True,
    
    validation_use_real_executor=True,
)
```

**运行时间**：约1-3秒（无需等待LLM）

### 2. run_codegen_only.py

**用途**：重新生成checker代码并验证

```python
config = PipelineConfig(
    skip_context_agent=True,
    skip_codegen_agent=False,
    skip_validation_agent=False,
    
    run_context_agent=False,
    run_codegen_agent=True,
    run_validation_agent=True,
)
```

**运行时间**：约20-60秒（CodeGen LLM调用）

### 3. run_full_pipeline.py

**用途**：完整pipeline（首次运行或全部重新生成）

```python
config = PipelineConfig(
    # 不设置skip_*参数，全部运行
    run_context_agent=False,  # 手动提供item_spec
    run_codegen_agent=True,
    run_validation_agent=True,
)
```

**运行时间**：约30-90秒（全流程）

---

## 调试技巧

### 快速迭代ValidationAgent

1. **首次运行**：`python run_full_pipeline.py`
   - 生成：item_spec.json, checker.py, validation_result.json

2. **修改ValidationAgent代码**

3. **快速测试**：`python run_validation_only.py`
   - 只需1-3秒，无需重新生成代码

4. **反复迭代步骤2-3**，直到验证逻辑正确

### 对比不同配置

```bash
# 使用Mock LLM（快速）
config.validation_use_mock_llm = True
python run_validation_only.py  # 1秒

# 使用真实执行（完整）
config.validation_use_real_executor = True
python run_validation_only.py  # 3秒
```

---

## 错误处理

### 错误：`No ItemSpec file found`

**原因**：`skip_context_agent=True`但output_dir中没有item_spec.json

**解决**：
- 确保先运行过完整pipeline，或
- 设置`skip_context_agent=False`

### 错误：`No checker file found`

**原因**：`skip_codegen_agent=True`但output_dir中没有checker文件

**解决**：
- 确保先运行过完整pipeline，或
- 设置`skip_codegen_agent=False`

### 错误：`No validation_result.json found`

**原因**：`skip_validation_agent=True`但output_dir中没有validation结果

**解决**：
- 确保先运行过完整pipeline，或
- 设置`skip_validation_agent=False`

---

## 最佳实践

1. **首次运行**：使用完整pipeline（不设置skip参数）
2. **调试单一阶段**：设置对应的skip参数
3. **保留输出文件**：不要删除output_dir中的中间文件
4. **增量测试**：从后往前跳过（先skip_context，再skip_codegen）
5. **版本控制**：提交关键的item_spec和checker文件

---

## 性能对比

| 配置 | 运行时间 | 适用场景 |
|------|---------|---------|
| 完整pipeline | 30-90秒 | 首次运行/全部重新生成 |
| skip_context_agent | 20-60秒 | 调试CodeGen/Validation |
| skip_context + skip_codegen | 1-3秒 | 调试Validation（最常用） |
| skip所有阶段 | <1秒 | 只加载已有结果 |

---

## 版本历史

- **v1.0**: 基础Pipeline（必须全部运行）
- **v1.1**: 支持run_*控制是否运行某阶段
- **v1.2**: 添加ValidationAgent真实执行功能
- **v1.3**: 添加skip_*断点重run功能（本版本）

---

## 常见问题

**Q: skip_*和run_*的区别是什么？**

A: 
- `run_* = False`: 完全不执行该阶段（也不加载）
- `skip_* = True`: 跳过执行，但从缓存加载已有结果

**Q: 可以同时设置skip=True和run=True吗？**

A: 可以，但`skip`优先级更高。如果`skip=True`，即使`run=True`也会跳过执行。

**Q: 如何验证skip功能是否生效？**

A: 查看日志输出：
```
✓ Loaded ItemSpec from input_item_spec.json  # skip生效
✓ ContextAgent completed  # 正常运行
```

**Q: 断点重run是否支持跨机器？**

A: 是的。只要复制output_dir到另一台机器，就可以从断点继续。

---

## 技术支持

如有问题，请检查：
1. 日志输出（`activity_log.txt`）
2. 中间文件是否存在（`item_spec.json`, `checker.py`）
3. 配置参数是否正确（`debug_mode=True`可以看详细日志）
