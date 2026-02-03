# Code Assembler Skill

**Skill Type:** Postprocessor  
**Version:** v1.0.0  
**Created:** 2025-12-22  
**Agent:** CodeGen Agent

## Overview

This skill assembles the final Checker Python code by combining:
1. **Fixed templates** (Jinja2): Header comment, imports, `__init__`, entry point
2. **LLM-generated code**: `_parse_input_files()`, `_execute_type1-4()`, helper methods

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `codegen_context` | CodeGenContext | Yes | Context with item metadata |
| `code_fragments` | Dict[str, str] | Yes | LLM-generated code fragments |

### code_fragments Dict Keys:
- `parse_method`: `_parse_input_files()` implementation
- `execute_type1`: `_execute_type1()` implementation
- `execute_type2`: `_execute_type2()` implementation
- `execute_type3`: `_execute_type3()` implementation
- `execute_type4`: `_execute_type4()` implementation
- `helper_methods`: Additional helper methods (optional)

## Output

Returns assembled Python code as a string, ready for formatting and validation.

## Template Structure

```
templates/
├── checker_skeleton.py.jinja2    # Main skeleton with all sections
├── header_comment.jinja2         # File header comment block
├── imports.jinja2                # Standard imports
└── entry_point.jinja2            # if __name__ == "__main__" block
```

## Mixed Mode Architecture

- **~40% Fixed (Templates)**: Header, imports, class definition, `__init__`, `execute_check()`, entry point
- **~60% LLM-Generated**: `_parse_input_files()`, `_execute_type1-4()`, helper methods

## Example Usage

```python
from agents.common.skills.postprocessors.code_assembler import assemble_checker_code

# After getting LLM response
code_fragments = {
    'parse_method': 'def _parse_input_files(self): ...',
    'execute_type1': 'def _execute_type1(self): ...',
    # ... etc
}

# Assemble final code
full_code = assemble_checker_code(
    codegen_context=context,
    code_fragments=code_fragments
)

# Write to file
with open('Check_5_0_0_05.py', 'w') as f:
    f.write(full_code)
```

## Dependencies

- `jinja2`: Template rendering engine
- `agents.code_generation.models`: CodeGenContext

## Error Handling

- Raises `ValueError` if required code fragments are missing
- Returns code with TODO placeholders if LLM fragments are incomplete
