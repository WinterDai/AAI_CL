# README Review & Edit 功能说明

## 新功能：Step 3.5 - 用户交互式README审查

在README生成后、代码生成前，Agent会暂停并提供交互选项。

### 使用场景

```bash
cd Tool/AutoGenChecker

# 运行Agent（启用交互模式）
python cli.py generate --item-id IMP-10-0-0-12 \
    --module 10.0_STA_DCD_CHECK \
    --ai-agent \
    --llm-provider jedai \
    --llm-model claude-sonnet-4-5
```

### 交互流程

```
================================================================================
📝 README Review & Edit
================================================================================

Generated README saved to:
  Check_modules/10.0_STA_DCD_CHECK/scripts/doc/IMP-10-0-0-12_README.md

You can now:
  1. Review Output Descriptions (found_desc, missing_desc, etc.)
  2. Adjust check logic and pattern examples
  3. Add clarifications or modify Type configurations

Options:
  [C] Continue with current README (generate code immediately)
  [E] Edit README now (opens in default editor)
  [Q] Quit (save progress, resume later with --resume-from-step 4)
================================================================================

Your choice [C/E/Q]: 
```

### 选项说明

#### **[C] Continue** - 直接继续
- 使用当前生成的README
- 立即进入Step 4代码生成
- **适用场景**：README质量满意，无需修改

#### **[E] Edit** - 立即编辑
- 在默认编辑器中打开README
- 支持平台：
  - Windows: Notepad
  - macOS: TextEdit
  - Linux: gedit/kate/nano/vim
- 修改完成后按ENTER继续
- **适用场景**：需要微调Output Descriptions或示例

#### **[Q] Quit** - 稍后处理
- 保存当前进度
- 退出Agent
- 用户可以手动精细编辑README
- 编辑完成后使用`--resume-from-step 4`继续
- **适用场景**：需要大幅修改或仔细审查

### 恢复工作流

```bash
# 1. 选择 [Q] 退出后，手动编辑README

# 2. 编辑完成后，从Step 4恢复
python cli.py generate --item-id IMP-10-0-0-12 \
    --module 10.0_STA_DCD_CHECK \
    --ai-agent \
    --llm-provider jedai \
    --llm-model claude-sonnet-4-5 \
    --resume-from-step 4   # ← 跳过Step 1-3，使用修改后的README
```

### 触发条件

- ✅ 必须启用`--ai-agent`（交互模式）
- ✅ 必须是首次运行（未使用`--resume-from-step`）
- ✅ Step 3 README生成完成

### 跳过交互

如果想跳过交互（例如CI/CD环境）：

```bash
# 使用 --resume-from-step 3 强制跳过交互
python cli.py generate ... --ai-agent --resume-from-step 3
```

或者不使用`--ai-agent`标志（但会失去其他AI增强功能）。

### 典型工作流

**场景1：快速迭代**
```
1. 运行Agent → Step 3生成README
2. 选择 [C] 继续 → 生成代码
3. 测试发现输出描述不理想
4. 手动修改README
5. 运行 --resume-from-step 4 → 重新生成代码
```

**场景2：仔细审查**
```
1. 运行Agent → Step 3生成README
2. 选择 [E] 编辑 → 立即微调描述
3. 保存并继续 → 生成代码
4. 测试验证
```

**场景3：团队协作**
```
1. 开发者A运行Agent → Step 3生成README
2. 选择 [Q] 退出
3. 开发者B审查并改进README
4. 开发者A从Step 4恢复 → 使用改进后的README生成代码
```

## 优势

✅ **质量控制**：在代码生成前审查关键描述
✅ **灵活性**：支持立即编辑或稍后处理
✅ **可恢复**：保存进度，支持多次迭代
✅ **团队友好**：支持README单独审查流程
