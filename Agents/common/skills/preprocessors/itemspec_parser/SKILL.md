# ItemSpec Parser Skill

**Skill Type:** Preprocessor  
**Version:** v1.0.0  
**Created:** 2025-12-22  
**Agent:** CodeGen Agent

## Overview

This skill parses an ItemSpec JSON file and extracts all information needed for code generation. It transforms the complex ItemSpec structure into a `CodeGenContext` object that can be used by the LLM prompt.

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_spec_path` | str | Yes | Path to the item_spec.json file |
| `item_id` | str | No | Item ID (extracted from path if not provided) |

## Output

Returns a `CodeGenContext` dataclass containing:

- `item_id`: Item identifier (e.g., "IMP-5-0-0-05")
- `class_name`: Python class name (e.g., "Check_5_0_0_05")
- `description`: Item description
- `regex_patterns`: List of regex patterns for parsing
- `input_file_patterns`: Expected input file patterns
- `type_specs`: List of TypeExecutionSpec for Type 1-4
- `pattern_items`: Pattern items to search for
- `waive_items`: Waiver items definition
- `requirements_value`: Requirements.value from ItemSpec
- `waivers_value`: Waivers.value from ItemSpec
- `semantic_hints`: Additional context for code generation

## Type Detection Logic

```
Type 1: requirements.value = N/A, waivers.value = N/A or 0
Type 2: requirements.value > 0, pattern_items exists, waivers.value = N/A or 0  
Type 3: requirements.value > 0, pattern_items exists, waivers.value > 0
Type 4: requirements.value = N/A, waivers.value > 0
```

## Example Usage

```python
from agents.common.skills.preprocessors.itemspec_parser import parse_item_spec

# Parse ItemSpec
context = parse_item_spec(
    item_spec_path="path/to/item_spec.json",
    item_id="IMP-5-0-0-05"
)

# Access extracted data
print(context.class_name)       # Check_5_0_0_05
print(context.regex_patterns)   # ['pattern1', 'pattern2']
print(context.type_specs)       # [TypeExecutionSpec(...), ...]
```

## Dependencies

- `agents.code_generation.models`: CodeGenContext, TypeExecutionSpec
- Standard library: json, pathlib, re

## Error Handling

- Raises `FileNotFoundError` if item_spec.json not found
- Raises `ValueError` if ItemSpec JSON is malformed
- Returns `CodeGenContext` with `errors` list populated on partial failures
