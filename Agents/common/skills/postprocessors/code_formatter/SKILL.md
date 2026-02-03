# Code Formatter Skill

**Skill Type:** Postprocessor  
**Version:** v1.0.0  
**Created:** 2025-12-22  
**Agent:** CodeGen Agent

## Overview

This skill formats Python code using `black` for code formatting and `isort` for import sorting. It ensures generated code follows PEP8 standards and has consistent style.

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | str | Yes | Python code to format |
| `line_length` | int | No | Maximum line length (default: 100) |
| `skip_isort` | bool | No | Skip import sorting (default: False) |
| `skip_black` | bool | No | Skip black formatting (default: False) |

## Output

Returns formatted Python code as a string.

## Processing Steps

1. **isort**: Sort and organize imports
2. **black**: Format code according to PEP8

## Configuration

Default settings aligned with CHECKLIST project standards:
- Line length: 100 characters
- Target Python version: 3.8+
- Import sections: STDLIB, THIRDPARTY, FIRSTPARTY, LOCALFOLDER

## Example Usage

```python
from agents.common.skills.postprocessors.code_formatter import format_code

# Format generated code
formatted = format_code(
    code=raw_code,
    line_length=100
)

# Format with specific options
formatted = format_code(
    code=raw_code,
    line_length=88,
    skip_isort=True  # If imports are already sorted
)
```

## Dependencies

- `black`: Code formatter
- `isort`: Import sorter

Install: `pip install black isort`

## Error Handling

- Returns original code if formatting fails
- Logs warning but doesn't raise exception (code may still be valid)
- Captures and reports formatting errors for debugging
