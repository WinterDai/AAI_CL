---
name: json_validator
version: 1.0.0
type: postprocessor
description: Validate LLM output against rules (TODO check, type completeness, etc.)
owner:
  - ContextAgent
inputs:
  result:
    type: dict
    description: LLM output to validate
  config_summary:
    type: ConfigSummary
    description: Configuration summary for context
outputs:
  status:
    type: string
    enum: [PASS, NEEDS_IMPROVEMENT, FAIL]
    description: Validation status
  issues:
    type: list[str]
    description: List of validation issues found
dependencies:
  - models.ConfigSummary
---

# JSON Validator Postprocessor

## Purpose

Rule-based validation of LLM output. This postprocessor performs deterministic checks without consuming LLM tokens.

## Key Functions

```python
def validate_result(
    result: dict, 
    config_summary: ConfigSummary
) -> tuple[str, list[str]]
```

## Responsibilities (Rule-Based Validation)

✅ **Does**:
- Check for TODO/TBD/FIXME placeholders
- Verify all 4 Type examples exist
- Validate required fields are present
- Check field completeness

❌ **Does NOT**:
- Evaluate content quality (that's LLM's job)
- Make semantic judgments
- Generate fixes

## Validation Rules

### 1. TODO Residual Check
```python
if "TODO" in readme or "TBD" in readme or "FIXME" in readme:
    issues.append("README contains unfilled placeholders")
```

### 2. Type Examples Completeness
```python
for t in ["type1", "type2", "type3", "type4"]:
    if t not in type_examples:
        issues.append(f"Missing {t} example")
    else:
        if "yaml" not in example or "behavior" not in example:
            issues.append(f"{t} example incomplete")
```

### 3. Check Logic Completeness
```python
if not check_logic.get("parsing_method"):
    issues.append("Missing parsing_method")
if not check_logic.get("pass_fail_logic"):
    issues.append("Missing pass_fail_logic")
```

## Status Determination

| Condition | Status |
|-----------|--------|
| No issues | PASS |
| 1-2 issues | NEEDS_IMPROVEMENT |
| 3+ issues | FAIL |

## Usage Example

```python
from agents.common.skills.postprocessors.json_validator import validate_result

status, issues = validate_result(llm_result, config_summary)
if status != "PASS":
    print(f"Issues: {issues}")
    # Retry LLM with feedback
```

## Integration with Retry Loop

```python
for attempt in range(MAX_RETRIES):
    llm_result = await llm_call(prompt)
    status, issues = validate_result(llm_result, config_summary)
    
    if status == "PASS":
        break
    
    # Add issues as feedback for next attempt
    feedback = f"Previous issues: {issues}"
```
