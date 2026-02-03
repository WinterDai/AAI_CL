# AutoGenChecker v2.0 - Architecture Upgrade Guide

## 🎯 What Changed?

The AutoGenChecker has been completely redesigned to strictly follow the workflow defined in `DEVELOPER_WORKFLOW_DIAGRAM.md` and `DEVELOPER_TASK_PROMPTS.md`.

### Key Improvements

1. **✅ Workflow Enforcement**: State machine that follows Step 1→2→2.5→3→4 exactly
2. **✅ Mandatory Step 2.5**: File analysis is now REQUIRED before code generation
3. **✅ Enhanced Context**: 4 collectors instead of 2 (added FileAnalysis + Templates)
4. **✅ Structured Prompts**: LLM receives file analysis results FIRST
5. **✅ Unified CLI**: Single entry point for all operations

## 📐 New Architecture

```
AutoGenChecker/
├── workflow/                   # NEW: Orchestration layer
│   ├── pipeline.py            # 5-step state machine
│   ├── orchestrator.py        # High-level API
│   └── models.py              # Data structures
│
├── context_collectors/
│   ├── task_spec.py           # ✅ Existing
│   ├── checker_examples.py    # ✅ Existing
│   ├── file_analysis.py       # 🆕 Step 2.5 enforcement
│   └── templates.py           # 🆕 Template recommendations
│
├── prompt_templates/
│   ├── checker_prompt.py      # ✅ Original (backward compat)
│   └── checker_prompt_v2.py   # 🆕 Enhanced with Step 2.5
│
├── file_format_analyzer.py    # ✅ Enhanced with analyze_file_detailed()
├── cli.py                      # 🆕 Unified CLI
└── (other files unchanged)
```

## 🚀 Quick Start

### Option 1: Full Workflow (Recommended)

Generates README + Code + Test scaffolding:

```bash
cd Tool/AutoGenChecker

python cli.py generate \
    --item-id IMP-10-0-0-11 \
    --module 10.0_STA_DCD_CHECK
```

**Output:**
- ✅ Configuration loaded/updated
- ✅ README generated (if enabled)
- ✅ **Files analyzed (Step 2.5 - MANDATORY)**
- ✅ Code generated based on file analysis
- ✅ Test scaffolding created

**Time:** 2-5 minutes (AI) + 10-30 minutes (manual refinement)

### Option 2: Code Only (Fast)

Skip README and test setup:

```bash
python cli.py generate \
    --item-id IMP-10-0-0-11 \
    --module 10.0_STA_DCD_CHECK \
    --code-only
```

**Time:** 30-60 seconds

### Option 3: Interactive Mode

Prompts at each step for customization:

```bash
python cli.py generate \
    --item-id IMP-10-0-0-11 \
    --module 10.0_STA_DCD_CHECK \
    --interactive
```

### Option 4: Analyze Files Only

Run only Step 2.5 to understand file formats:

```bash
python cli.py analyze \
    --module 10.0_STA_DCD_CHECK \
    --files reports/timing.rpt logs/sta.log
```

## 📊 Workflow Comparison

### Before (v1.x)

```
Developer runs multiple separate tools:
1. file_format_analyzer.py (optional, often skipped)
2. smart_recommend.py (optional)
3. llm_checker_agent.py (generates code)
4. Manual integration

❌ Problem: Steps are disconnected
❌ Problem: File analysis often skipped → guessed patterns
❌ Problem: LLM doesn't see file analysis results
```

### After (v2.0)

```
Developer runs single command:
python cli.py generate --item-id X --module Y

Pipeline automatically executes:
Step 1: Load configuration ✅
Step 2: Generate README ✅
Step 2.5: Analyze files (MANDATORY) ⭐
Step 3: Generate code (based on Step 2.5) ✅
Step 4: Setup test ✅

✅ All steps connected
✅ File analysis ALWAYS runs
✅ LLM sees analysis results in prompt
```

## 🔧 Using the Workflow API

For programmatic usage:

```python
from AutoGenChecker.workflow import CheckerWorkflowOrchestrator

# Full workflow
artifacts = CheckerWorkflowOrchestrator.generate_full_checker(
    item_id="IMP-10-0-0-11",
    module="10.0_STA_DCD_CHECK",
    use_llm=True,
    llm_provider="openai",
)

print(f"Generated code: {len(artifacts.code)} lines")
print(f"File analysis: {len(artifacts.file_analysis)} files")
print(f"Time taken: {artifacts.time_taken_seconds:.1f}s")

# Code only
code = CheckerWorkflowOrchestrator.generate_code_only(
    item_id="IMP-10-0-0-11",
    module="10.0_STA_DCD_CHECK",
)

# Analyze files only
analysis = CheckerWorkflowOrchestrator.analyze_files_only(
    module="10.0_STA_DCD_CHECK",
    input_files=["reports/timing.rpt"],
)
```

## 🎯 Key Features

### 1. Mandatory Step 2.5

File analysis is now **enforced** before code generation:

```python
# In CheckerGenerationPipeline:
def step2_5_analyze_files(self, config):
    """MANDATORY: Analyze input files before generating code."""
    
    # This step ALWAYS runs
    # LLM receives analysis results in prompt
```

### 2. Enhanced File Analysis

`FileFormatAnalyzer` now provides:
- File type detection
- Pattern extraction with examples
- Real data samples
- Parsing strategy recommendations
- **Output format suggestions** (what INFO01/ERROR01 should display)

### 3. Structured LLM Prompts

New `build_checker_prompt_v2()` format:

```
1. File Analysis Results (Step 2.5) ⭐ SHOWN FIRST
   - File type: timing_report
   - Patterns: [list of regex with examples]
   - Real data sample: [actual file content]
   - Output recommendations: INFO01=path groups, ERROR01=violations

2. Task Specification
3. Reference Context (examples, templates)
4. Implementation Instructions (based on file analysis)
```

### 4. Context Collectors

Now 4 collectors provide rich context:

1. **TaskSpecCollector**: Configuration and item spec
2. **CheckerExampleCollector**: Similar checker examples
3. **FileAnalysisCollector**: Step 2.5 analysis results ⭐
4. **TemplateCollector**: Available templates (LogPatternChecker, etc.)

## 📋 Migration Guide

### For Existing Code

The original tools still work (backward compatible):

```bash
# Old way (still works)
python llm_checker_agent.py generate ...

# New way (recommended)
python cli.py generate ...
```

### For Custom Scripts

Update imports:

```python
# Old
from AutoGenChecker.llm_checker_agent import LLMCheckerAgent

# New (recommended)
from AutoGenChecker.workflow import CheckerWorkflowOrchestrator
```

## ⚙️ Configuration

### LLM Settings

```bash
# Use OpenAI (default)
python cli.py generate --item-id X --module Y

# Use Anthropic
python cli.py generate --item-id X --module Y --llm-provider anthropic

# Specify model
python cli.py generate --item-id X --module Y --llm-model gpt-4

# Without LLM (template only)
python cli.py generate --item-id X --module Y --no-llm
```

### Output Control

```bash
# Save artifacts to directory
python cli.py generate \
    --item-id X --module Y \
    --output-dir /path/to/output

# This creates:
#   /path/to/output/README.md
#   /path/to/output/X.py
#   /path/to/output/artifacts.json
```

## 🐛 Troubleshooting

### Issue: File analysis fails

```
⚠️ File not found: reports/timing.rpt
```

**Solution:** Place input files in module's `inputs/` directory or use absolute paths.

### Issue: LLM generates wrong patterns

**Cause:** File analysis was skipped or incomplete.

**Solution:** Verify Step 2.5 output shows actual patterns:

```bash
python cli.py analyze --module X --files reports/file.rpt
```

### Issue: Code has many TODOs

This is expected! The AI generates 70-80% of the code. You still need to:
1. Refine `_parse_files()` based on real data
2. Complete type-specific logic
3. Test with actual input files

## 📈 Benefits Summary

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Workflow consistency** | Manual steps | Automated pipeline | 100% |
| **Step 2.5 execution** | Often skipped | Always runs | Critical |
| **Context quality** | 2 collectors | 4 collectors | 100% |
| **Prompt structure** | Generic | Step-aware | Significant |
| **Development time** | 1-2 hours | 15-30 min (AI) + 10-30 min (manual) | 50%+ |

## 🔮 Future Enhancements

- [ ] Interactive prompts in Step 2.5 (ask user to confirm patterns)
- [ ] Automatic test data generation
- [ ] Integration with regression testing framework
- [ ] VSCode extension for one-click generation
- [ ] Support for more LLM providers (local models, etc.)

## 📞 Support

Issues? Check:
1. This guide
2. `doc/DEVELOPER_WORKFLOW_DIAGRAM.md`
3. `doc/DEVELOPER_TASK_PROMPTS.md`
4. Generated code's TODO comments

---

**Version:** 2.0  
**Date:** 2025-12-10  
**Author:** AutoGenChecker Team
