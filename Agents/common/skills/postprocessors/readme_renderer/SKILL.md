---
name: readme_renderer
version: 1.0.0
type: postprocessor
description: Render README from LLM output using Jinja2 templates
owner:
  - ContextAgent
inputs:
  llm_result:
    type: dict
    description: Structured JSON output from LLM containing check_logic, type_examples, etc.
  config_summary:
    type: ConfigSummary
    description: Configuration summary from preprocessor
  template_name:
    type: string
    default: checker_readme.jinja2
    description: Name of the Jinja2 template to use
outputs:
  readme_content:
    type: string
    description: Rendered README markdown content
dependencies:
  - jinja2
  - models.ConfigSummary
---

# README Renderer Postprocessor

## Purpose

Deterministically render README from LLM's structured JSON output using fixed Jinja2 templates. This postprocessor contains NO business logic - only template rendering.

## Key Functions

```python
def render_readme(
    llm_result: dict,
    config_summary: ConfigSummary,
    template_name: str = "checker_readme.jinja2"
) -> str
```

## Responsibilities (Deterministic Rendering)

✅ **Does**:
- Load fixed Jinja2 template
- Fill in LLM-generated content
- Return complete README

❌ **Does NOT**:
- Make any logic decisions
- Generate content
- Modify LLM output

## Why Fixed Templates Instead of Dynamic TODO Search

| Dynamic TODO Search | Fixed Jinja2 Templates |
|--------------------|-----------------------|
| Search README for TODO markers | Use predefined template |
| LLM fills arbitrary positions | LLM outputs structured JSON |
| Unpredictable results | Deterministic rendering |
| Hard to validate | Easy to validate |

## Template Structure

```jinja2
# {{ item_id }}: {{ description }}

## Overview

**Category**: {{ check_logic.category }}
**Type**: Type {{ detected_type }} - {{ type_description }}

## Check Logic

### Parsing Method
{{ check_logic.parsing_method }}

### Pass/Fail Criteria
{{ check_logic.pass_fail_logic }}

## Type Examples

{% for type_id, example in type_examples.items() %}
### {{ type_id | title }}

**YAML Configuration:**
```yaml
{{ example.yaml }}
```

**Behavior:** {{ example.behavior }}

**Output:** {{ example.output }}
{% endfor %}

## Testing

{{ testing_commands }}
```

## Usage Example

```python
from agents.common.skills.postprocessors.readme_renderer import render_readme

readme = render_readme(llm_result, config_summary)
with open("README.md", "w") as f:
    f.write(readme)
```
