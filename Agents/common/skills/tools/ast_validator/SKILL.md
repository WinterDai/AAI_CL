# AST Validator Skill

**Skill Type:** Tool  
**Version:** v1.0.0  
**Created:** 2025-12-22  
**Agent:** CodeGen Agent

## Overview

This skill validates Python code using AST (Abstract Syntax Tree) parsing. It checks for syntax errors without executing the code, providing detailed error information for the Evaluator-Optimizer feedback loop.

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | str | Yes | Python code to validate |
| `check_style` | bool | No | Also check basic style issues (default: True) |

## Output

Returns `ValidationResult` dataclass:
- `is_valid`: bool - Whether code is syntactically valid
- `errors`: List[SyntaxError] - List of syntax errors found
- `warnings`: List[str] - Style/lint warnings
- `ast_tree`: ast.Module - Parsed AST (if valid)

## Validation Checks

1. **AST Parsing**: Verify code is valid Python syntax
2. **Method Signatures**: Check required methods exist and have correct signatures
3. **Type Annotations**: Verify type hints are present (optional)
4. **Import Verification**: Check imports are valid
5. **Style Checks**: Basic PEP8 compliance

## Example Usage

```python
from agents.common.skills.tools.ast_validator import validate_code

# Validate generated code
result = validate_code(generated_code)

if result.is_valid:
    print("Code is valid!")
else:
    for error in result.errors:
        print(f"Line {error.line}: {error.message}")
```

## Integration with Evaluator-Optimizer

```python
# In retry loop
result = validate_code(generated_code)

if not result.is_valid:
    feedback = ValidationFeedback(
        attempt_number=attempt,
        is_valid=False,
        previous_code=generated_code,
        syntax_errors=result.errors,
        suggestions=result.get_fix_suggestions()
    )
    # Send feedback back to LLM
```

## Dependencies

- Standard library only: `ast`, `tokenize`
- No external dependencies required

## Error Handling

- Returns detailed error location (line, column)
- Provides error message and context
- Suggests potential fixes where possible
