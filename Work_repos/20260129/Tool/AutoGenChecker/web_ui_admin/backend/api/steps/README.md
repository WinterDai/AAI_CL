# Web UI API Structure - Aligned with CLI

## Overview

Web UI的后端API已重构为与CLI的workflow结构完全对齐。每个步骤都有独立的模块，对应CLI中的mixins。

## Directory Structure

```
web_ui/backend/
├── app.py                      # Main FastAPI app
└── api/
    ├── generation.py           # Legacy generation endpoints
    ├── history.py             # Generation history
    ├── templates.py           # Template management
    ├── settings.py            # User settings
    └── steps/                 # ⭐ Step-by-step modules (aligned with CLI)
        ├── __init__.py
        ├── step1_config.py            # Configuration (CLI: config loading)
        ├── step2_file_analysis.py     # File Analysis (CLI: file_analysis_mixin.py)
        ├── step3_code_generation.py   # Code Generation (CLI: code_generation_mixin.py) [TODO]
        ├── step4_testing.py           # Testing (CLI: testing_mixin.py) [TODO]
        └── ...
```

## Step Mapping: Web ↔ CLI

| Step | Web Module | CLI Mixin | Status |
|------|-----------|-----------|--------|
| Step 1 | `step1_config.py` | Configuration loading | ✅ Complete |
| Step 2 | `step2_file_analysis.py` | `file_analysis_mixin.py` | ✅ Complete |
| Step 3 | `step3_code_generation.py` | `code_generation_mixin.py` | ❌ TODO |
| Step 4 | `step4_testing.py` | `testing_mixin.py` | ❌ TODO |
| Step 5 | `step5_self_check.py` | `self_check_mixin.py` | ❌ TODO |
| Step 6 | `step6_readme_generation.py` | `readme_generation_mixin.py` | ❌ TODO |
| Step 7 | `step7_final_review.py` | `final_review_mixin.py` | ❌ TODO |

## API Endpoints

### Step 1: Configuration Management

**Base URL:** `/api/step1`

- `GET /modules` - List all checker modules
- `GET /modules/{module_id}/items/{item_id}` - Get item configuration
- `PUT /modules/{module_id}/items/{item_id}` - Update YAML configuration
- `GET /checklist-root` - Get CHECKLIST root path

**CLI Equivalent:**
- Configuration file loading and validation
- YAML parsing

---

### Step 2: File Analysis

**Base URL:** `/api/step2`

- `POST /file-stats` - Get file statistics (lines, size)
- `POST /analyze-file` - Analyze file with LLM

**CLI Equivalent:**
- `file_analysis_mixin.py::_ai_analyze_input_files()`
- `file_analysis_mixin.py::_call_ai_for_file_analysis()`
- `file_analysis_mixin.py::_build_file_analysis_prompt()`
- `file_analysis_mixin.py::_parse_ai_file_analysis()`

**Key Features:**
- Uses EXACT same prompt structure as CLI
- Matches CLI's temperature (0.1)
- Parses JSON and text responses
- Expands path variables (${CHECKLIST_ROOT}, etc.)
- Returns structured analysis:
  - `file_type`: Detected file type
  - `patterns`: Key regex patterns
  - `sample_data`: Real data samples
  - `parsing_strategy`: Recommended approach
  - `output_format`: INFO/ERROR format definition
  - `template_recommendations`: Helper suggestions

---

## Frontend Integration

### Step1 Component
```javascript
// Module list
fetch('http://localhost:8000/api/step1/modules')

// Get item detail
fetch(`http://localhost:8000/api/step1/modules/${module}/items/${item}`)

// Update YAML
fetch(`http://localhost:8000/api/step1/modules/${module}/items/${item}`, {
  method: 'PUT',
  body: JSON.stringify({ yaml_content: yamlText })
})
```

### Step2 Component
```javascript
// Get file stats
fetch('http://localhost:8000/api/step2/file-stats', {
  method: 'POST',
  body: JSON.stringify({ file_path: path })
})

// Analyze file with LLM
fetch('http://localhost:8000/api/step2/analyze-file', {
  method: 'POST',
  body: JSON.stringify({
    file_path: path,
    file_type: type,
    llm_provider: 'jedai',
    llm_model: 'claude-sonnet-4-5',
    description: 'Checker description'
  })
})
```

---

## Implementation Guidelines

### Adding a New Step

1. **Create step module:** `api/steps/stepN_name.py`

2. **Reference CLI mixin:** Study corresponding mixin in `workflow/mixins/`

3. **Match CLI logic:**
   - Use same prompt structure
   - Use same temperature settings
   - Use same parsing logic
   - Return same data structure

4. **Create router:**
```python
from fastapi import APIRouter

router = APIRouter()

@router.post("/endpoint-name")
async def function_name(request: RequestModel):
    # Match CLI's logic here
    pass
```

5. **Register in `app.py`:**
```python
from api.steps import stepN_router
app.include_router(stepN_router, prefix="/api/stepN", tags=["stepN-name"])
```

6. **Update frontend component:**
```javascript
fetch(`http://localhost:8000/api/stepN/endpoint`)
```

### Key Principles

1. **CLI Parity:** Every web endpoint should have a corresponding CLI function
2. **Same Prompts:** Use EXACT same LLM prompts as CLI
3. **Same Parsing:** Use EXACT same response parsing logic
4. **Same Config:** Use same temperature, max_tokens, etc.
5. **Path Variables:** Support ${CHECKLIST_ROOT}, ${IP_PROJECT_FOLDER}, ${WORK}

---

## Testing Alignment

To verify web implementation matches CLI:

1. **Run CLI:** `python cli.py generate -i` with same config
2. **Run Web:** Use web UI with same config
3. **Compare outputs:** File analysis, generated code, etc.

Expected: Identical results (same patterns, same code structure, same recommendations)

---

## Next Steps

1. ✅ Step 1: Configuration - Complete
2. ✅ Step 2: File Analysis - Complete
3. ❌ Step 3: Code Generation - TODO
   - Create `step3_code_generation.py`
   - Match `code_generation_mixin.py`
   - Use same prompt from `checker_prompt_v2.py`
4. ❌ Step 4: Testing - TODO
5. ❌ Step 5: Self-Check - TODO
6. ❌ Step 6: README Generation - TODO
7. ❌ Step 7: Final Review - TODO

---

## Migration Notes

**Old Structure:**
- All endpoints in `api/checklist.py`
- Mixed concerns (config + analysis + generation)
- Hard to maintain CLI parity

**New Structure:**
- Each step in separate module
- Clear CLI correspondence
- Easy to verify alignment
- Modular and maintainable

**Migration Path:**
- ✅ Created `api/steps/` directory
- ✅ Moved Step 1 endpoints to `step1_config.py`
- ✅ Moved Step 2 endpoints to `step2_file_analysis.py`
- ✅ Updated frontend to use new endpoints
- ✅ Kept old `checklist.py` for backward compatibility (deprecated)
- ❌ Remove `checklist.py` after full migration
