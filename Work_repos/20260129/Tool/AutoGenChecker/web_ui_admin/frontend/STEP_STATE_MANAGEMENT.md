# WebUI 步骤状态管理和关系总结

## 📊 总体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          generationStore (Zustand + Persist)                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Global State (所有步骤共享)                                                  │
│  ├── currentStep: number (1-9)                                              │
│  ├── module: string                                                         │
│  ├── itemId: string                                                         │
│  └── status: 'idle' | 'running' | 'paused' | 'completed' | 'failed'        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Step-specific State (各步骤专属)                                            │
│  ├── step1State: { selectedModule, selectedItem, yamlData, ... }           │
│  ├── fileAnalysis: []           (Step2 产出)                                │
│  ├── generatedReadme: ''        (Step3 产出)                                │
│  ├── generatedCode: ''          (Step5 产出)                                │
│  └── testResults: []            (Step7 产出)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Process State (各步骤运行状态)                                              │
│  ├── step2IsAnalyzing: boolean                                              │
│  ├── step3IsGenerating: boolean                                             │
│  ├── step5IsGenerating: boolean                                             │
│  ├── step6IsChecking: boolean                                               │
│  ├── step7IsRunning: boolean                                                │
│  ├── step8IsProcessing: boolean                                             │
│  └── step9IsPackaging: boolean                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 步骤依赖关系图

```
Step 1 (Configuration)
    │
    │ 产出: step1State { selectedModule, selectedItem, yamlData }
    │       yamlConfig (用于后续步骤获取 input_files, requirements 等)
    │
    ▼
Step 2 (File Analysis)
    │
    │ 依赖: yamlConfig.input_files (从 Step1)
    │ 产出: fileAnalysis[] (每个文件的 patterns, parsingStrategy, sampleData)
    │
    ▼
Step 3 (README Generation)
    │
    │ 依赖: yamlConfig (Step1), fileAnalysis (Step2)
    │ 产出: generatedReadme
    │
    ▼
Step 4 (Review README)
    │
    │ 依赖: generatedReadme (Step3)
    │ 产出: (修改后的) generatedReadme
    │
    ▼
Step 5 (Code Generation)
    │
    │ 依赖: generatedReadme (Step3/4), fileAnalysis (Step2), yamlConfig (Step1)
    │ 产出: generatedCode
    │
    ▼
Step 6 (Self Check)
    │
    │ 依赖: generatedCode (Step5), step1State.selectedModule/selectedItem
    │ 产出: 运行结果日志
    │
    ▼
Step 7 (Testing)
    │
    │ 依赖: generatedCode (Step5)
    │ 产出: testResults[]
    │
    ▼
Step 8 (Final Review)
    │
    │ 依赖: generatedCode (Step5), testResults (Step7)
    │ 产出: (最终确认)
    │
    ▼
Step 9 (Package)
    │
    │ 依赖: 所有前序步骤的产出
    │ 产出: 打包文件
    │
    ▼
  完成
```

---

## 📋 各步骤详细状态

### Step 1: Configuration (配置)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `step1State.selectedModule` | string | URL params / 用户选择 | Step2-9 使用 |
| `step1State.selectedItem` | string | URL params / 用户选择 | Step2-9 使用 |
| `step1State.yamlData` | object | 后端 API | 显示 + 保存 |
| `yamlConfig` | object | step1State.yamlData | Step2, 3, 5 使用 |

**关键操作:**
- `handleSaveConfiguration()` - 保存配置到 store
- `handleResumeFrom(step)` - 从指定步骤恢复

**问题:**
- ⚠️ 同时有 `step1State.yamlData` 和 `yamlConfig`，冗余
- ⚠️ 保存时机不明确（之前是自动保存，现在改为显式 Save 按钮）

---

### Step 2: File Analysis (文件分析)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `fileAnalysis` | array | 后端分析 API | Step3, 5 使用 |
| `step2IsAnalyzing` | boolean | 本地 | 显示加载状态 |
| `yamlConfig.input_files` | array | Step1 | 获取要分析的文件列表 |

**依赖 Step1:**
```javascript
const yamlConfig = useGenerationStore((s) => s.yamlConfig)
const inputFiles = yamlConfig?.input_files || []
```

**问题:**
- ⚠️ 如果 Step1 没有保存，`yamlConfig` 为 null，无法获取 input_files

---

### Step 3: README Generation (README 生成)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `generatedReadme` | string | LLM 生成 | Step4, 5 使用 |
| `step3IsGenerating` | boolean | 本地 | 显示生成状态 |
| `step3GenerationLogs` | array | 本地 | 显示日志 |
| `hintsHistory` | array | 后端 API | 显示历史 hints |

**依赖:**
```javascript
const yamlConfig = useGenerationStore((s) => s.yamlConfig)     // Step1
const fileAnalysis = useGenerationStore((s) => s.fileAnalysis) // Step2
const step1State = useGenerationStore((s) => s.step1State)     // Step1
```

---

### Step 4: Review (README 审查)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `generatedReadme` | string | Step3 | 编辑后保存 |

**关键操作:**
- 显示 Step3 生成的 README
- 允许用户编辑并保存

---

### Step 5: Code Generation (代码生成)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `generatedCode` | string | LLM 生成 | Step6, 7, 8 使用 |
| `step5IsGenerating` | boolean | 本地 | 显示生成状态 |
| `step5GenerationLogs` | array | 本地 | 显示日志 |

**依赖:**
```javascript
const generatedReadme = useGenerationStore((s) => s.generatedReadme) // Step3/4
const fileAnalysis = useGenerationStore((s) => s.fileAnalysis)       // Step2
const yamlConfig = useGenerationStore((s) => s.yamlConfig)           // Step1
const step1State = useGenerationStore((s) => s.step1State)           // Step1
```

---

### Step 6: Self Check (自检)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `step6IsChecking` | boolean | 本地 | 显示运行状态 |
| `step6CheckLogs` | array | 本地 | 显示运行日志 |

**依赖:**
```javascript
const generatedCode = useGenerationStore((s) => s.generatedCode) // Step5
const step1State = useGenerationStore((s) => s.step1State)       // Step1 (module, item)
```

**关键操作:**
- 运行 checker 脚本
- 显示 PASS/FAIL 结果

---

### Step 7: Testing (测试)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `testResults` | array | 测试执行 | Step8 使用 |
| `step7IsRunning` | boolean | 本地 | 显示运行状态 |
| `step7TestLogs` | array | 本地 | 显示日志 |

**依赖:**
```javascript
const generatedCode = useGenerationStore((s) => s.generatedCode) // Step5
```

---

### Step 8: Final Review (最终审查)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `step8IsProcessing` | boolean | 本地 | 显示处理状态 |

**依赖:**
```javascript
const generatedCode = useGenerationStore((s) => s.generatedCode) // Step5
const testResults = useGenerationStore((s) => s.testResults)     // Step7
```

---

### Step 9: Package (打包)

| 状态变量 | 类型 | 来源 | 去向 |
|---------|------|------|------|
| `step9IsPackaging` | boolean | 本地 | 显示打包状态 |

**依赖:**
- 所有前序步骤的产出

---

## ⚠️ 当前问题总结

### 1. 状态冗余
```
step1State.yamlData  ←→  yamlConfig  ←→  itemConfig
step1State.selectedModule  ←→  module
step1State.selectedItem  ←→  itemId
```
**建议:** 统一使用 `step1State`，删除冗余的 `module`, `itemId`, `itemConfig`

### 2. 保存时机不一致
- Step1: 显式 Save 按钮 ✓
- Step2: 分析完成自动保存到 store
- Step3: 生成完成自动保存 + 可手动保存到文件
- Step4: 编辑后手动保存
- Step5: 生成完成自动保存 + 可手动保存到文件

### 3. 步骤跳转限制
- 当前: ProgressSteps 检查 `configSaved` (step1State.yamlData 存在)
- 问题: 没有检查每个步骤的依赖是否满足

### 4. 恢复逻辑复杂
Step1 有 `handleResumeFrom(step)` 从后端加载历史数据，但其他步骤没有

---

## 📐 建议的状态管理架构

```javascript
// 推荐的 store 结构
const generationStore = {
  // ============ 核心配置 (Step1 产出) ============
  project: {
    module: '',
    itemId: '',
    yamlConfig: null,  // 合并原 yamlConfig + step1State.yamlData
  },
  
  // ============ 各步骤产出 ============
  outputs: {
    step2: { fileAnalysis: [], completed: false },
    step3: { readme: '', completed: false },
    step4: { readme: '', completed: false },  // 编辑后的 README
    step5: { code: '', completed: false },
    step6: { results: null, completed: false },
    step7: { testResults: [], completed: false },
    step8: { approved: false, completed: false },
    step9: { packagePath: '', completed: false },
  },
  
  // ============ UI 状态 ============
  ui: {
    currentStep: 1,
    status: 'idle',
    isProcessing: false,  // 统一的处理状态
    logs: [],
  },
  
  // ============ Actions ============
  saveProject: (module, itemId, yamlConfig) => {},
  completeStep: (step, output) => {},
  goToStep: (step) => {},  // 检查依赖后跳转
  reset: () => {},
}
```

### 步骤跳转检查逻辑
```javascript
const canGoToStep = (targetStep) => {
  const { project, outputs } = get()
  
  // Step 1 总是可以访问
  if (targetStep === 1) return true
  
  // Step 2+ 需要 Step1 完成
  if (!project.module || !project.itemId || !project.yamlConfig) {
    return { allowed: false, reason: 'Please complete Step 1 first' }
  }
  
  // Step 3 需要 Step2 完成
  if (targetStep >= 3 && !outputs.step2.completed) {
    return { allowed: false, reason: 'Please complete File Analysis first' }
  }
  
  // Step 5 需要 Step3 完成
  if (targetStep >= 5 && !outputs.step3.completed) {
    return { allowed: false, reason: 'Please generate README first' }
  }
  
  // Step 6+ 需要 Step5 完成
  if (targetStep >= 6 && !outputs.step5.completed) {
    return { allowed: false, reason: 'Please generate Code first' }
  }
  
  return { allowed: true }
}
```

---

## 🔄 数据流动图

```
URL (module, item)
      │
      ▼
┌─────────────────┐
│   Step 1        │ ──► 保存 ──► store.project
│  Configuration  │              { module, itemId, yamlConfig }
└─────────────────┘
         │
         ▼ yamlConfig.input_files
┌─────────────────┐
│   Step 2        │ ──► 保存 ──► store.outputs.step2
│  File Analysis  │              { fileAnalysis }
└─────────────────┘
         │
         ▼ fileAnalysis + yamlConfig
┌─────────────────┐
│   Step 3        │ ──► 保存 ──► store.outputs.step3
│ README Generate │              { readme }
└─────────────────┘
         │
         ▼ readme
┌─────────────────┐
│   Step 4        │ ──► 保存 ──► store.outputs.step4
│  Review README  │              { readme (edited) }
└─────────────────┘
         │
         ▼ readme + fileAnalysis + yamlConfig
┌─────────────────┐
│   Step 5        │ ──► 保存 ──► store.outputs.step5
│ Code Generation │              { code }
└─────────────────┘
         │
         ▼ code + module + itemId
┌─────────────────┐
│   Step 6        │ ──► 保存 ──► store.outputs.step6
│   Self Check    │              { results }
└─────────────────┘
         │
         ▼ code
┌─────────────────┐
│   Step 7        │ ──► 保存 ──► store.outputs.step7
│    Testing      │              { testResults }
└─────────────────┘
         │
         ▼ code + testResults
┌─────────────────┐
│   Step 8        │ ──► 保存 ──► store.outputs.step8
│  Final Review   │              { approved }
└─────────────────┘
         │
         ▼ all outputs
┌─────────────────┐
│   Step 9        │ ──► 保存 ──► store.outputs.step9
│    Package      │              { packagePath }
└─────────────────┘
```

---

## ✅ 下一步行动建议

1. **简化 store 结构** - 删除冗余状态
2. **统一保存机制** - 每个步骤完成时都显式保存
3. **增强步骤跳转检查** - 根据依赖检查是否可跳转
4. **添加步骤完成指示** - 在 ProgressSteps 显示每步是否完成
5. **统一恢复逻辑** - 在 Generator 初始化时检查后端状态
