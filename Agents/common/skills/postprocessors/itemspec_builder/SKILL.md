---
name: itemspec_builder
version: 1.0.0
type: postprocessor
description: Build ItemSpec from preprocessor and LLM outputs for downstream agents
owner:
  - ContextAgent
inputs:
  config_summary:
    type: ConfigSummary
    description: From config_loader preprocessor
  file_analysis:
    type: FileAnalysis
    description: From file_reader preprocessor
  llm_result:
    type: dict
    description: Structured output from LLM
  readme_content:
    type: string
    description: Rendered README from readme_renderer
outputs:
  item_spec:
    type: ItemSpec
    description: Complete specification for downstream agents
dependencies:
  - models.ItemSpec
  - models.ConfigSummary
  - models.FileAnalysis
---

# ItemSpec Builder Postprocessor

## Purpose

Assemble ItemSpec from all preprocessor outputs and LLM results. This is the final postprocessor that creates the output for downstream agents (CodeGenAgent, ValidationAgent).

## Key Functions

```python
def build(
    config_summary: ConfigSummary,
    file_analysis: FileAnalysis,
    llm_result: dict,
    readme_content: str
) -> ItemSpec
```

## Responsibilities (Data Assembly)

✅ **Does**:
- Combine all preprocessor outputs
- Integrate LLM results
- Construct complete ItemSpec
- Prepare data for downstream agents

❌ **Does NOT**:
- Transform or modify data
- Make decisions
- Validate content

## Data Flow

```
┌─────────────────┐
│ config_loader   │──→ ConfigSummary ──┐
└─────────────────┘                     │
                                        │
┌─────────────────┐                     │
│ file_reader     │──→ FileAnalysis ───┼──→ itemspec_builder ──→ ItemSpec
└─────────────────┘                     │
                                        │
┌─────────────────┐                     │
│ LLM Phase       │──→ llm_result ─────┤
└─────────────────┘                     │
                                        │
┌─────────────────┐                     │
│ readme_renderer │──→ readme_content ──┘
└─────────────────┘
```

## Output Schema

```python
@dataclass
class ItemSpec:
    # From config_loader
    item_id: str
    module: str
    description: str
    detected_type: int
    requirements: dict
    pattern_items: list[str]
    waivers: dict
    input_files: list[FileInfo]
    
    # From file_reader
    file_analysis: FileAnalysis
    
    # From LLM
    check_logic: CheckLogic
    type_examples: dict[str, TypeExample]
    
    # From readme_renderer
    generated_readme: str
```

## Usage Example

```python
from agents.common.skills.postprocessors.itemspec_builder import build

item_spec = build(
    config_summary=config_summary,
    file_analysis=file_analysis,
    llm_result=llm_result,
    readme_content=readme_content
)

# Pass to downstream agents
code_gen_agent.generate(item_spec)
validation_agent.validate(item_spec)
```

## Downstream Usage

| Agent | Uses From ItemSpec |
|-------|-------------------|
| CodeGenAgent | check_logic, type_examples, file_analysis |
| ValidationAgent | generated_readme, type_examples |
