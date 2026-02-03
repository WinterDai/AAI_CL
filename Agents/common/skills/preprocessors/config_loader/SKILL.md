---
name: config_loader
version: 1.0.0
type: preprocessor
description: Load and parse checker YAML configuration, detect checker type (1-4)
owner:
  - ContextAgent
  - CodeGenAgent
inputs:
  config_path:
    type: string
    description: Absolute path to the YAML configuration file
outputs:
  config_summary:
    type: ConfigSummary
    description: Structured configuration summary with detected type
dependencies:
  - models.ConfigSummary
  - models.FileInfo
---

# Config Loader Preprocessor

## Purpose

Parse checker YAML configuration and automatically detect checker type (1-4) based on deterministic rules.

## Key Functions

```python
def load_config(config_path: str) -> ConfigSummary
```

## Responsibilities (Pure Data Extraction)

✅ **Does**:
- Parse YAML format
- Check if input files exist
- Calculate file_count and aggregation_needed
- Detect Type based on rules (not semantics)

❌ **Does NOT** (Leave to LLM):
- Understand description meaning
- Determine check logic
- Analyze file content

## Type Detection Logic

Based on `DEVELOPER_TASK_PROMPTS.md` rules:

| Type | requirements.value | pattern_items | waivers.value |
|------|-------------------|---------------|---------------|
| Type 1 | N/A | [] (empty) | N/A/0 |
| Type 2 | > 0 | [...] (defined) | N/A/0 |
| Type 3 | > 0 | [...] (defined) | > 0 |
| Type 4 | N/A | [] (empty) | > 0 |

## Output Schema

```python
@dataclass
class ConfigSummary:
    item_id: str
    description: str
    input_files: list[FileInfo]
    file_count: int
    aggregation_needed: bool
    requirements: dict
    pattern_items: list[str]
    waivers: dict
    detected_type: int  # 1, 2, 3, 4
```

## Usage Example

```python
from agents.common.skills.preprocessors.config_loader import load_config

config = load_config("Check_modules/5.0_SYNTHESIS_CHECK/inputs/items/IMP-5-0-0-00.yaml")
print(f"Type: {config.detected_type}")  # Type: 1
print(f"Files: {config.file_count}")    # Files: 1
```
