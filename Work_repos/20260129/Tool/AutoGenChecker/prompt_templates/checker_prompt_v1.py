"""Prompt builders for the LLM checker agent."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Sequence

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from utils.models import CheckerAgentRequest, ContextFragment
    from utils.text import condense_whitespace, indent_block
except ImportError:
    from AutoGenChecker.utils.models import CheckerAgentRequest, ContextFragment
    from AutoGenChecker.utils.text import condense_whitespace, indent_block


def _load_developer_prompts() -> str:
    """Load DEVELOPER_TASK_PROMPTS.md Step 3 from CHECKLIST/doc/ directory."""
    try:
        from utils.paths import discover_project_paths
    except ImportError:
        from AutoGenChecker.utils.paths import discover_project_paths
    
    try:
        paths = discover_project_paths()
        # Try CHECKLIST/doc/ first (primary location)
        doc_file = paths.workspace_root / "CHECKLIST" / "doc" / "DEVELOPER_TASK_PROMPTS.md"
        if not doc_file.exists():
            # Fallback to doc/ (legacy location)
            doc_file = paths.workspace_root / "doc" / "DEVELOPER_TASK_PROMPTS.md"
        
        if doc_file.exists():
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract Step 3 section (updated regex to match new format)
            import re
            step3_match = re.search(
                r'## Step 3: Implement Python Code\s*```(.*?)```',
                content,
                re.DOTALL
            )
            
            if step3_match:
                return step3_match.group(1).strip()
        
        print("[WARN] DEVELOPER_TASK_PROMPTS.md Step 3 not found, using fallback instructions")
    except Exception as e:
        print(f"[WARN] Failed to load DEVELOPER_TASK_PROMPTS.md: {e}")
    
    return ""


# Load official developer prompts from documentation
_STEP3_INSTRUCTIONS = _load_developer_prompts()

# Standard CHECKLIST framework development guidelines
# Based on DEVELOPER_TASK_PROMPTS.md v1.1.0 (December 11, 2025)
if _STEP3_INSTRUCTIONS:
    DEFAULT_INSTRUCTIONS = f"""
## CRITICAL: Follow DEVELOPER_TASK_PROMPTS.md Step 3 Guidelines (v1.1.0)

{_STEP3_INSTRUCTIONS}

## Additional Implementation Notes
- Author field should preserve the name from skeleton (assigned developer)
- Date MUST be current date in YYYY-MM-DD format (2025-12-15)
- Implement ALL 4 types: _execute_type1/2/3/4()
- Follow waiver tag rules exactly ([WAIVER], [WAIVED_AS_INFO], [WAIVED_INFO])
- MANDATORY: Use checker_templates (WaiverHandlerMixin + OutputBuilderMixin)
- Reference: Check_modules/common/checker_templates/README.md for 30+ examples
"""
else:
    # Fallback instructions if DEVELOPER_TASK_PROMPTS.md not found
    DEFAULT_INSTRUCTIONS = """
## CRITICAL: Follow 3-Step Development Workflow

You MUST follow these steps IN ORDER:

### Step 1: Write README Documentation First
Before writing any code, create a mental plan for the README that would go in:
`Check_modules/{MODULE}/scripts/doc/{ITEM_ID}_README.md`

The README should include:
1. **Overview section**:
   - Category: (e.g., "Timing Analysis - Constraint Validation")
   - Input Files: List all files from configuration
   - Functional description: What this checker validates and why

2. **Check Logic section**:
   - Input Parsing: How to extract data from input files
   - Detection Logic: Step-by-step PASS/FAIL determination

3. **Configuration Examples** (all 4 types):
   - Type 1: Boolean Check (no pattern_items, requirements.value=N/A, waivers.value=N/A)
   - Type 2: Value Check (use pattern_items, requirements.value>0, waivers.value=N/A)
   - Type 3: Value Check with Waiver Logic (Type 2 + waiver, requirements.value>0, waivers.value>0)
   - Type 4: Boolean Check with Waiver Logic (Type 1 + waiver, requirements.value=N/A, waivers.value>0)

### Step 2: Analyze Input Files (BEFORE Coding!)
**DO NOT guess file formats or patterns!**

If input files are referenced:
1. Understand file type: Log? Report? JSON? Plain text?
2. Identify parsing requirements:
   - What keywords/patterns to search for?
   - Regex patterns? Line-by-line parsing? Delimiters?
   - Edge cases: Empty files? Missing sections?
3. Define output clearly:
   - What goes in INFO01/ERROR01?
   - How to display file paths vs processed names?
   - info_groups must match details.name for linking

### Step 3: Implement Code with ALL 4 Types
Only after Step 1 & 2, write the Python checker.

## MANDATORY: File Header Comment

```python
################################################################################
# Script Name: {ITEM_ID}.py
#
# Purpose:
#   {One-line description from item_desc}
#
# Logic:
#   - {Parse X file to extract Y data using Z pattern}
#   - {Extract/validate specific fields: A, B, C}
#   - {Compare against requirements/patterns}
#   - {Apply waiver logic if configured}
#   (Add 3-6 detailed, actionable steps - this will be extracted for documentation)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 -> Boolean check (no pattern search)
   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 -> Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 -> Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Author: AutoGen Checker
# Date: {YYYY-MM-DD}
################################################################################
```

**CRITICAL**: 
- Author MUST preserve the name from skeleton file (assigned developer name)
- Date MUST be current date in YYYY-MM-DD format
- Logic section is MANDATORY (3-6 detailed steps)

## Implementation Requirements

### Inheritance & Structure:
- **PRIORITY**: Check `common.checker_templates` first. Use existing templates (e.g., `LogPatternChecker`, `ValueComparisonChecker`) whenever possible to reduce code duplication.
- If no template fits, inherit from `BaseChecker` (from `common.base_checker`)
- Implement `_parse_files()` and `_execute_typeX()` methods (for all 4 types)

### Path Setup (Standard Pattern):
```python
from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult
from output_formatter import DetailItem, Severity, create_check_result
```

### Class Init:
```python
class MyChecker(BaseChecker):
    def __init__(self):
        super().__init__(
            check_module="{MODULE}",
            item_id="{ITEM_ID}",
            item_desc="{DESCRIPTION}"
        )
```

### Type Detection:
Use `self.detect_checker_type()` from BaseChecker - **DO NOT reimplement**:
```python
checker_type = self.detect_checker_type()
# Returns 1/2/3/4 based on requirements/waivers config
```

### Waiver Tag Rules (CRITICAL):

**When waivers.value > 0 (Type 3/4)**:
```python
# All waive_items related outputs use [WAIVER] suffix
DetailItem(
    name=item_name,
    reason=f"{waive_reason}[WAIVER]"
)
```

**When waivers.value = 0 (Type 1/2 - Force PASS mode)**:
```python
# Actual violations -> INFO with [WAIVED_AS_INFO]
DetailItem(
    severity=Severity.INFO,
    name=violation_name,
    reason=f"Issue found[WAIVED_AS_INFO]"
)

# waive_items config -> INFO with [WAIVED_INFO]
DetailItem(
    severity=Severity.INFO,
    name=waive_item,
    reason="Waive item[WAIVED_INFO]"
)
# Force is_pass = True
```

### Error Handling:
```python
from base_checker import ConfigurationError

# Validate configs
if not required_field:
    raise ConfigurationError("Missing required field")

# File operations
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
except FileNotFoundError:
    self.logger.warning(f"File not found: {file_path}")
    # Handle gracefully
```

### Type Implementation Details:

**Type 1 - Boolean Check** (no pattern_items):
- Custom boolean validation (file exists? config valid?)
- Does NOT use pattern_items for searching
- No value comparison
- If waiver=0: all failures -> INFO with [WAIVED_AS_INFO]

**Type 2 - Value Check** (use pattern_items):
- Search pattern_items in input files
- found_items = patterns found; missing_items = patterns not found
- PASS/FAIL depends on check purpose (violation vs requirement)
- Config validation: check len(pattern_items) == requirements.value
- If waiver=0: all failures -> INFO with [WAIVED_AS_INFO]

**Type 3 - Value Check with Waiver Logic**:
- Same pattern search logic as Type 2
- Additional waiver classification: match found_items against waive_items
- Waived -> INFO with [WAIVER]
- Unwaived -> ERROR
- Unused waivers -> WARN with [WAIVER]
- PASS if all found items are waived

**Type 4 - Boolean Check with Waiver Logic**:
- Same boolean check as Type 1 (no pattern_items)
- Additional waiver classification for violations
- All waive-related use [WAIVER] suffix
- PASS if all violations are waived

## Step 3: Output Structure

### info_groups Linking (IMPORTANT):
The output_formatter.py matches data by comparing `info_groups.items` with `details.name`:

```python
info_groups = {
    "INFO01": {
        "description": "Waived violations",
        "items": [item.name for item in waived_items]  # Must match details.name
    }
}
```

### DetailItem Format:
```python
DetailItem(
    severity=Severity.INFO,      # INFO, ERROR, WARN, FAIL
    name="Item Name",             # Will be matched by info_groups
    line_number=line_num,         # Optional
    file_path="path/to/file",     # Optional
    reason="Detailed reason[TAG]" # Optional, add [WAIVER]/[WAIVED_AS_INFO] tags
)
```

## Step 4: Testing Mindset

After implementation, the checker will be tested with:
```bash
python common/regression_testing/create_all_snapshots.py --modules {MODULE} --checkers {ITEM_ID} --force
```

Ensure:
- Code runs without crashes
- Output YAML is valid
- Snapshot data matches expected behavior
- All 4 types work correctly
"""


def build_checker_prompt(
    request: CheckerAgentRequest,
    context_fragments: Sequence[ContextFragment],
    *,
    instructions: str | None = None,
    extra_notes: Iterable[str] | None = None,
) -> str:
    """Render a structured prompt for the LLM call."""

    sections: list[str] = []

    sections.append(
        "## Task\n"
        f"Generate a Python checker for module {request.module} item {request.item_id}.\n"
        "Return fully executable code that fits the CHECKLIST BaseChecker pattern."
    )

    metadata_lines = [f"Item name: {request.item_name or 'unknown'}"]
    if request.priority:
        metadata_lines.append(f"Priority: {request.priority}")
    if request.target_files:
        metadata_lines.append(
            "Target inputs: " + ", ".join(sorted(set(request.target_files)))
        )
    if request.notes:
        metadata_lines.append(f"Operator notes: {request.notes}")

    sections.append("## Request Metadata\n" + "\n".join(metadata_lines))

    # Always include default instructions first
    combined_instructions = DEFAULT_INSTRUCTIONS
    if instructions:
        combined_instructions += "\n\n## Additional Custom Instructions\n" + instructions.strip()
    
    sections.append("## Implementation Guidelines\n" + combined_instructions.strip())

    if extra_notes:
        notes = "\n".join(note.strip() for note in extra_notes if note)
        if notes:
            sections.append("## Additional Notes\n" + notes)

    if context_fragments:
        fragment_parts: list[str] = []
        for fragment in context_fragments:
            header = f"### {fragment.title}" if fragment.title else "### Context"
            source_line = f"(source: {fragment.source})" if fragment.source else ""
            body = indent_block(fragment.content, 2)
            fragment_parts.append(f"{header} {source_line}\n{body}")
        sections.append("## Reference Material\n" + "\n\n".join(fragment_parts))

    sections.append(
        "## Output Requirements\n"
        "1. Provide the checker code inside a fenced Python block.\n"
        "2. Include the MANDATORY header comment with Logic section.\n"
        "3. Implement ALL 4 types (_execute_type1/2/3/4).\n"
        "4. Follow waiver tag rules exactly ([WAIVER], [WAIVED_AS_INFO], [WAIVED_INFO]).\n"
        "5. Include error handling with ConfigurationError.\n"
        "6. Highlight any assumptions or follow-up actions."
    )

    return condense_whitespace("\n\n".join(sections))
