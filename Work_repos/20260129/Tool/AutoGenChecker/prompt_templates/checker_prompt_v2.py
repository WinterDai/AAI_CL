"""Enhanced prompt builder v2 with Step 2.5 enforcement."""

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
    from prompt_templates.api_v2_reference import (
        get_template_instructions,
        get_type_specific_hints
    )
except ImportError:
    from AutoGenChecker.utils.models import CheckerAgentRequest, ContextFragment
    from AutoGenChecker.utils.text import condense_whitespace, indent_block
    from AutoGenChecker.prompt_templates.api_v2_reference import (
        get_template_instructions,
        get_type_specific_hints
    )


def build_checker_prompt_v2(
    request: CheckerAgentRequest,
    context_fragments: Sequence[ContextFragment],
    file_analysis: list[dict] | None = None,
    *,
    instructions: str | None = None,
    extra_notes: Iterable[str] | None = None,
) -> str:
    """
    Build checker generation prompt with MANDATORY Step 2.5 enforcement.
    
    This prompt structure strictly follows DEVELOPER_WORKFLOW_DIAGRAM.md:
    1. Shows file analysis results FIRST (Step 2.5)
    2. Provides task specification
    3. Includes reference examples
    4. Gives detailed implementation instructions
    
    Args:
        request: Checker generation request
        context_fragments: Collected context (examples, task spec, etc.)
        file_analysis: MANDATORY file analysis results from Step 2.5
        instructions: Additional instructions
        extra_notes: Extra notes to include
    
    Returns:
        Complete LLM prompt string
    """
    sections: list[str] = []
    
    # ========== Section 0: Header ==========
    sections.append(_build_header(request))
    
    # ========== Section 1: CRITICAL - File Analysis Results ==========
    if file_analysis:
        sections.append(_build_file_analysis_section(file_analysis))
    else:
        sections.append(_build_no_file_analysis_warning())
    
    # ========== Section 2: Task Specification ==========
    sections.append(_build_task_spec_section(request))
    
    # ========== Section 3: Context Fragments ==========
    sections.append(_build_context_section(context_fragments))
    
    # ========== Section 4: Implementation Instructions ==========
    sections.append(_build_implementation_instructions(request, file_analysis))
    
    # ========== Section 5: Additional Instructions ==========
    if instructions:
        sections.append(f"\n## Additional Instructions\n\n{instructions}\n")
    
    # ========== Section 6: Extra Notes ==========
    if extra_notes:
        notes_text = "\n".join(f"- {note}" for note in extra_notes)
        sections.append(f"\n## Operator Notes\n\n{notes_text}\n")
    
    # ========== Footer ==========
    sections.append(_build_footer())
    
    return "\n".join(sections)


def _build_header(request: CheckerAgentRequest) -> str:
    """Build prompt header."""
    return f"""
{'='*80}
CHECKER CODE GENERATION TASK
{'='*80}

You are generating a Python checker implementation for the CHECKLIST framework.

**CRITICAL**: Follow the EXACT workflow from DEVELOPER_WORKFLOW_DIAGRAM.md:
  Step 1: Configuration (already done)
  Step 2: README (already done or will be done separately)
  Step 2.5: File Analysis (COMPLETED - results below) ⭐ MANDATORY
  Step 3: Code Generation (YOUR TASK)
  Step 4: Test Setup (will be done after code generation)

Your task is Step 3: Generate the Python checker code.

{'='*80}
"""


def _build_file_analysis_section(file_analysis: list[dict]) -> str:
    """Build file analysis section (Step 2.5 results)."""
    lines = [
        "\n" + "="*80,
        "📊 STEP 2.5 ANALYSIS RESULTS (MANDATORY INPUT)",
        "="*80,
        "",
        "⚠️ CRITICAL: The following file analysis was ALREADY COMPLETED.",
        "   You MUST use these exact patterns and strategies.",
        "   DO NOT GUESS or assume different file formats!",
        "",
    ]
    
    for idx, analysis in enumerate(file_analysis, 1):
        lines.extend([
            f"\n{'─'*70}",
            f"File {idx}: {analysis.get('file_name', 'Unknown')}",
            f"{'─'*70}",
            "",
        ])
        
        # Basic info
        lines.append(f"📁 File Information:")
        lines.append(f"  Type: {analysis.get('file_type', 'Unknown').upper()}")
        lines.append(f"  Path: {analysis.get('file_path', 'N/A')}")
        lines.append(f"  Exists: {'✅ Yes' if analysis.get('exists', False) else '❌ No'}")
        
        if analysis.get('exists'):
            lines.append(f"  Size: {analysis.get('file_size', 0):,} bytes")
            lines.append(f"  Lines: {analysis.get('total_lines', 0):,}")
        
        lines.append("")
        
        # Detected patterns
        patterns = analysis.get('patterns', [])
        if patterns:
            lines.append("🔍 DETECTED PATTERNS (use these EXACT patterns):")
            lines.append("")
            for pidx, pattern in enumerate(patterns[:5], 1):
                lines.append(f"  Pattern {pidx}: {pattern.get('name', 'Unknown')}")
                lines.append(f"    Regex: {pattern.get('regex', 'N/A')}")
                lines.append(f"    Example: {pattern.get('example', 'N/A')}")
                lines.append(f"    Occurrences: {pattern.get('count', 0)}")
                lines.append("")
        else:
            lines.append("🔍 No specific patterns detected - use generic parsing")
            lines.append("")
        
        # Parsing strategy
        strategy = analysis.get('parsing_strategy', '')
        if strategy:
            lines.append("⚙️ RECOMMENDED PARSING STRATEGY:")
            lines.append(f"  {strategy}")
            lines.append("")
        
        # Output format suggestions
        output_sugg = analysis.get('output_suggestion', {})
        if output_sugg:
            lines.append("📤 OUTPUT FORMAT RECOMMENDATIONS:")
            lines.append(f"  INFO01 should display: {output_sugg.get('info01', 'Item names')}")
            lines.append(f"  ERROR01 should display: {output_sugg.get('error01', 'Violations')}")
            lines.append("")
            lines.append("  ⚠️ CRITICAL: info_groups.items MUST match details.name exactly!")
            lines.append("")
        
        # Real data sample
        sample = analysis.get('sample_data', '')
        if sample:
            lines.append("📝 REAL DATA SAMPLE (first 15 lines):")
            lines.append("  " + "─"*65)
            for line in sample.split('\n')[:15]:
                lines.append(f"  {line[:75]}")
            lines.append("  " + "─"*65)
            lines.append("")
    
    lines.extend([
        "="*80,
        "⚠️ IMPORTANT: Base your parsing logic on the analysis above.",
        "   Do NOT guess patterns or file formats!",
        "="*80,
        "",
    ])
    
    return "\n".join(lines)


def _build_no_file_analysis_warning() -> str:
    """Build warning when no file analysis is available."""
    return """
="*80
⚠️ WARNING: NO FILE ANALYSIS AVAILABLE
="*80

No input files were analyzed (Step 2.5 was skipped or files not found).

You will need to generate a GENERIC template that:
1. Has placeholder parsing logic with TODO comments
2. Includes all 4 type implementations
3. Has proper structure but requires manual refinement

The developer will need to:
- Analyze actual input files manually
- Implement _parse_files() based on real data
- Test with actual input files

="*80

"""


def _build_task_spec_section(request: CheckerAgentRequest) -> str:
    """Build task specification section."""
    lines = [
        "\n" + "="*80,
        "📋 TASK SPECIFICATION",
        "="*80,
        "",
        f"Module: {request.module}",
        f"Item ID: {request.item_id}",
    ]
    
    if request.item_name:
        lines.append(f"Description: {request.item_name}")
    
    if request.target_files:
        lines.append(f"Input Files: {', '.join(request.target_files)}")
    
    if request.priority:
        lines.append(f"Priority: {request.priority}")
    
    if request.notes:
        lines.extend([
            "",
            "Additional Context:",
            indent_block(request.notes, 2),
        ])
    
    lines.append("\n" + "="*80)
    
    return "\n".join(lines)


def _build_context_section(context_fragments: Sequence[ContextFragment]) -> str:
    """Build context section with reference examples."""
    if not context_fragments:
        return ""
    
    # Sort by importance
    critical = [f for f in context_fragments if f.importance == "critical"]
    high = [f for f in context_fragments if f.importance == "high"]
    medium = [f for f in context_fragments if f.importance == "medium"]
    
    lines = ["\n" + "="*80, "📚 REFERENCE CONTEXT", "="*80, ""]
    
    # Critical fragments (file analysis already shown above, skip here)
    # Only show non-file-analysis critical items
    critical_non_file = [f for f in critical if "File Analysis" not in f.title]
    if critical_non_file:
        lines.append("\n🔴 CRITICAL CONTEXT:\n")
        for frag in critical_non_file:
            lines.append(f"### {frag.title}\n")
            lines.append(condense_whitespace(frag.content))
            lines.append("")
    
    # High importance (templates, examples)
    if high:
        lines.append("\n🔶 HIGH PRIORITY REFERENCES:\n")
        for frag in high[:3]:  # Limit to top 3
            lines.append(f"### {frag.title}\n")
            lines.append(condense_whitespace(frag.content[:2000]))  # Limit length
            lines.append("")
    
    # Medium importance
    if medium:
        lines.append("\n🔷 ADDITIONAL REFERENCES:\n")
        for frag in medium[:2]:  # Limit to top 2
            lines.append(f"### {frag.title}\n")
            lines.append(condense_whitespace(frag.content[:1000]))
            lines.append("")
    
    lines.append("="*80)
    
    return "\n".join(lines)


def _build_implementation_instructions(
    request: CheckerAgentRequest,
    file_analysis: list[dict] | None = None
) -> str:
    """
    Build detailed implementation instructions.
    
    Based on DEVELOPER_TASK_PROMPTS.md v1.1.0 (December 11, 2025) Step 3.
    """
    from datetime import datetime
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    instructions = f"""
{'='*80}
💻 CODE GENERATION REQUIREMENTS (DEVELOPER_TASK_PROMPTS.md Step 3)
{'='*80}

⚠️ CRITICAL: Follow BLOCK 1-4 structure from DEVELOPER_TASK_PROMPTS.md v1.1.0

====================================================================================
BLOCK 1 – Template Setup (MANDATORY)
====================================================================================
1. Review Check_modules/common/checker_templates/README.md (30+ examples) before coding
2. Import and inherit REQUIRED mixins in this exact order:
   ```python
   from checker_templates.waiver_handler_template import WaiverHandlerMixin
   from checker_templates.output_builder_template import OutputBuilderMixin
   from checker_templates.input_file_parser_template import InputFileParserMixin  # optional but recommended
   ```
3. Class skeleton must inherit from BaseChecker + mixins (InputFileParserMixin first if used)
4. Reference migrations: IMP-10-0-0-10 (all mixins), IMP-10-0-0-02 (template reuse)

====================================================================================
BLOCK 2 – File Header & Auto Type Detection
====================================================================================

## 1. MANDATORY FILE HEADER

```python
################################################################################
# Script Name: {request.item_id}.py
#
# Purpose:
#   {request.item_name or 'TBD - provide one-line description'}
#
# Logic:
#   - Parse {{input_file}} using patterns from Step 2.5 analysis
#   - Extract {{specific_fields}} based on file format
#   - Validate/compare against requirements or patterns
#   - Apply waiver logic if Type 3/4
#   (Provide 3-6 detailed, actionable steps)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean check (no pattern search)
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: {current_date} (Using checker_templates v1.1.0)
#
# Author: AutoGenChecker
# Date: {current_date}
################################################################################
```

**⚠️ CRITICAL - DO NOT MODIFY:**
- **Waiver Tag Rules section**: Copy EXACTLY as shown above - DO NOT simplify or change
- **Logic section**: Must be detailed (3-6 actionable steps based on file analysis)
- **Refactored line**: Include "Refactored: {{date}} (Using checker_templates v1.1.0)"
- **Author field**: DO NOT MODIFY - preserve exactly as is from skeleton
- **Template comments**: DO NOT DELETE - fill in TODOs with real implementation, keep structure

====================================================================================
BLOCK 3 – Implement _parse_input_files()
====================================================================================

## 2. STANDARD IMPORTS AND PATH SETUP (with Template Mixins)

```python
from pathlib import Path
import sys
import re

_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result

# MANDATORY: Import template mixins
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin
from checker_templates.input_file_parser_template import InputFileParserMixin  # optional
```


## 3. CLASS STRUCTURE (with Template Mixins)

```python
# MANDATORY: Inherit mixins in this order (InputFileParserMixin first if used)
class Checker(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    \"\"\"
    {request.item_id}: {request.item_name or 'TBD'}
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing
    - Uses WaiverHandlerMixin for waiver processing
    - Uses OutputBuilderMixin for result construction
    \"\"\"
    
    # =========================================================================
    # ⭐ UNIFIED DESCRIPTIONS - CRITICAL: Define these constants!
    # =========================================================================
    # These MUST be identical across ALL Type 1/2/3/4 implementations
    # Use these in build_complete_output() calls to ensure consistency
    #
    # 📝 WRITING GUIDELINES (based on checker type):
    #
    # Type 1/4 (Boolean Checks - existence/configuration):
    #   - Use generic existence terms: "found", "exists", "detected", "configured"
    #   - Focus on presence/absence: "Item found" vs "Item not found"
    #   - Examples:
    #     ✅ FOUND_DESC = "FEOL dummy rule deck successfully extracted"
    #     ✅ MISSING_DESC = "FEOL dummy rule deck not found in runset"
    #     ✅ FOUND_DESC = "Configuration validated"
    #     ✅ MISSING_DESC = "Configuration missing or invalid"
    #
    # Type 2/3 (Pattern Matching - requirement satisfaction):
    #   - Use pattern/requirement terms: "matched", "satisfied", "compliant"
    #   - Focus on requirement fulfillment: "Pattern matched" vs "Pattern missing"
    #   - Include counts when checking multiple patterns:
    #     ✅ FOUND_DESC = "Required patterns satisfied (2/2)"
    #     ✅ MISSING_DESC = "Required patterns not matched (1/2 missing)"
    #   - Examples:
    #     ✅ FOUND_DESC = "Antenna rule deck pattern matched"
    #     ✅ MISSING_DESC = "Expected antenna rule deck pattern not found"
    #     ✅ FOUND_DESC = "All timing path groups validated"
    #     ✅ MISSING_DESC = "Timing path group requirements not met"
    
    # ⭐ DESCRIPTION CONSTANTS - Split by Type semantics (API-026)
    # DESC constants are split by Type for semantic clarity (same as REASON split)
    # Type 1/4 emphasize "found/not found", Type 2/3 emphasize "matched/satisfied"
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "TBD - e.g., 'Tool version found in configuration'"
    MISSING_DESC_TYPE1_4 = "TBD - e.g., 'Required item not found in setup file'"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "TBD - e.g., 'Required pattern matched (2/2)'"
    MISSING_DESC_TYPE2_3 = "TBD - e.g., 'Expected pattern not satisfied (1/2 missing)'"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "TBD - describe waived items"
    
    # ⭐ REASON CONSTANTS - Type-specific semantic requirements!
    # 
    # 🔴 CRITICAL RULE: Split REASON constants by Type semantics!
    # 
    # ALL Types pass found_reason/missing_reason to build_complete_output()
    # BUT use different constant names to enforce correct semantics:
    # 
    # Type 1/4 (Boolean Checks):
    #   ✅ Use FOUND_REASON_TYPE1_4 / MISSING_REASON_TYPE1_4
    #   ✅ Emphasize existence: "found" / "not found"
    #   ✅ Example: "Tool version found in configuration"
    #   ✅ Example: "Required item not found in setup file"
    #   → Type 1 = no pattern_items, Type 4 = Type 1 + waiver
    # 
    # Type 2/3 (Pattern Checks):
    #   ✅ Use FOUND_REASON_TYPE2_3 / MISSING_REASON_TYPE2_3
    #   ✅ Emphasize pattern matching: matched | satisfied | validated | compliant | fulfilled
    #   ✅ Example: "Required pattern matched and validated"
    #   ✅ Example: "Expected pattern not satisfied in configuration"
    #   → Type 2 = has pattern_items, Type 3 = Type 2 + waiver
    # 
    # Type 3/4 (With Waivers):
    #   ✅ MUST pass waiver parameters:
    #      - waived_desc=self.WAIVED_DESC (ALL Types need this, but Type 3/4 use for actual waived items)
    #      - waived_base_reason=self.WAIVED_BASE_REASON (Type 3/4 ONLY)
    #      - unused_waiver_reason=self.UNUSED_WAIVER_REASON (Type 3/4 ONLY, if unused_waivers)
    # 
    # ⚠️ Note: ALL Types need waived_desc!
    #   - Type 1/2 (waivers=0): Use for waive_items comment "No waiver support"
    #   - Type 3/4 (waivers>0): Use for actual waived violation descriptions
    # 
    # ⚠️ DECISION GUIDE: Use String or Lambda?
    # 
    # Check the README "Display Format" section:
    # 
    # 1️⃣ README shows STATIC format (same text for all items):
    #    Example: "Required antenna rule deck pattern matched"
    #    → Use STRING constant:
    #    FOUND_REASON = "Required antenna rule deck pattern matched"
    # 
    # 2️⃣ README shows DYNAMIC format (includes item-specific fields):
    #    Example: "[pattern]: Matched [deck_name] (version: [version])"
    #    → Use LAMBDA function:
    #    FOUND_REASON = lambda item: (
    #        f"{{item.get('pattern', 'N/A')}}: Matched {{item.get('deck_name', 'N/A')}} "
    #        f"(version: {{item.get('version', 'N/A')}})"
    #    )
    # 
    # Type 1/2 + waiver=0 Compatibility:
    # If Type 2 supports waiver=0 mode AND needs dynamic format:
    # - Lambda is OK! Modern output_builder supports callable reasons
    # - Ensure parsed items contain all fields needed by lambda
    # 
    # Type 1/4: Keep as TBD (not passed to build_complete_output)
    # Type 2/3: Replace with actual pattern matching reason
    # Type 1/4: Boolean checks - emphasize "found/not found"
    FOUND_REASON_TYPE1_4 = "TBD - e.g., 'Tool version found in configuration'"
    MISSING_REASON_TYPE1_4 = "TBD - e.g., 'Required item not found in setup file'"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied/validated/compliant/fulfilled"
    FOUND_REASON_TYPE2_3 = "TBD - e.g., 'Required pattern matched and validated'"
    MISSING_REASON_TYPE2_3 = "TBD - e.g., 'Expected pattern not satisfied in configuration'"
    WAIVED_BASE_REASON = "TBD - why item was waived (Type 3/4 only)"
    UNUSED_WAIVER_REASON = "Waiver defined but no violation matched (Type 3/4 only)"
    
    def __init__(self):
        super().__init__(
            check_module="{request.module}",
            item_id="{request.item_id}",
            item_desc="{request.item_name or 'TBD'}"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {{}}
    
    def execute_check(self) -> CheckResult:
        # Auto-detect type (DO NOT reimplement - use BaseChecker's method)
        checker_type = self.detect_checker_type()
        
        # Parse files
        parsed_data = self._parse_input_files()
        
        # Execute based on type
        if checker_type == 1:
            return self._execute_type1(parsed_data)
        elif checker_type == 2:
            return self._execute_type2(parsed_data)
        elif checker_type == 3:
            return self._execute_type3(parsed_data)
        else:
            return self._execute_type4(parsed_data)
```

**⚠️ CRITICAL REQUIREMENTS:**
1. **Define ALL class constants** (FOUND_DESC, MISSING_DESC, FOUND_REASON, MISSING_REASON, etc.)
2. **Use these constants** in EVERY build_complete_output() call
3. **Same descriptions** across all Type 1/2/3/4 implementations
4. **DO NOT use generic strings** like "Item found" - always use class constants!

**Note**: If not using InputFileParserMixin, inherit: `class Checker(OutputBuilderMixin, WaiverHandlerMixin, BaseChecker)`


## 4. IMPLEMENT _parse_input_files() - Use Template Helpers!
"""
    
    if file_analysis and any(a.get('exists') for a in file_analysis):
        instructions += """
**Use the patterns from Step 2.5 analysis above!**

```python
def _parse_input_files(self) -> dict:
    \"\"\"Parse input files based on Step 2.5 analysis.\"\"\"
    # 1. Validate inputs with template helper
    # IMPORTANT: validate_input_files() returns a TUPLE: (valid_files_list, missing_files_list)
    valid_files, missing_files = self.validate_input_files()
    if not valid_files:
        raise ConfigurationError("No valid input files found")
    
    # 2. Use template helpers (parse_log_with_patterns, normalize_command, etc.)
    all_items = []
    
    for file_path in valid_files:
        # Option A: Use parse_log_with_patterns for regex-based parsing
        # patterns = {{
        #     'error_pattern': r'\\*\\*ERROR:\\s*\\(([A-Z]+-\\d+)\\)',
        #     'warning_pattern': r'\\*\\*WARNING:\\s*(.+)'
        # }}
        # results = self.parse_log_with_patterns(file_path, patterns)
        
        # Option B: Manual parsing with normalization
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Use patterns from Step 2.5 analysis:
                match = re.search(r'{{pattern_from_analysis}}', line)
                if match:
                    item = {{
                        'name': match.group(1),
                        'line_number': line_num,
                        'file_path': str(file_path)
                    }}
                    all_items.append(item)
    
    # 3. Store frequently reused data on self
    self._parsed_items = all_items
    
    # 4. Return aggregated dict
    return {{'items': all_items, 'metadata': {{'total': len(all_items)}}}}
```
"""
    else:
        instructions += """
**No file analysis available - create generic template:**

```python
def _parse_input_files(self) -> dict:
    \"\"\"Parse input files - NEEDS MANUAL IMPLEMENTATION.\"\"\"
    # 1. Validate inputs
    # IMPORTANT: validate_input_files() returns a TUPLE: (valid_files_list, missing_files_list)
    valid_files, missing_files = self.validate_input_files()
    if not valid_files:
        raise ConfigurationError("No valid input files found")
    
    # TODO: Analyze actual input files first!
    # TODO: Implement parsing based on real file format
    # TODO: Use template helpers: parse_log_with_patterns(), normalize_command()
    
    return {{'items': []}}  # Placeholder
```
"""
    
    # Add API v2.0 specific instructions
    checker_type = request.checker_type or 1
    instructions += f"""

{'='*80}
⭐ OUTPUT_BUILDER_TEMPLATE API v2.0 REQUIREMENTS
{'='*80}

{get_template_instructions()}

{get_type_specific_hints(checker_type)}

{'='*80}

====================================================================================
BLOCK 4 – Execute Methods by Checker Type
====================================================================================

## 5. IMPLEMENT ALL 4 TYPE METHODS (Use Template Helpers!)

**Type 1: Boolean Check (no pattern_items search, use build_complete_output and let template auto-handle waiver=0)**

**⚠️ CRITICAL: found_items MUST be a dict with line_number and file_path metadata!**
```python
def _execute_type1(self, parsed_data: dict) -> CheckResult:
    # Type 1: Custom boolean check (file exists? config valid?)
    # Does NOT use pattern_items for searching
    items = parsed_data.get('items', [])
    
    # Convert list to dict with metadata for source file/line display
    # Output format: "Info: <name>. In line <N>, <filepath>: <reason>"
    found_items = {{
        item['name']: {{
            'name': item['name'],
            'line_number': item.get('line_number', 0),  # REQUIRED!
            'file_path': item.get('file_path', 'N/A')   # REQUIRED!
        }}
        for item in items
    }} if items else {{}}
    
    return self.build_complete_output(
        found_items=found_items,
        missing_items=[] if found_items else ['Expected item'],
        found_desc=self.FOUND_DESC,
        missing_desc=self.MISSING_DESC
        # ❌ Type 1: DO NOT pass found_reason/missing_reason
        # Uses default: "Item found" / "Item not found"
    )
```

**Type 2: Value Check (use pattern_items, use build_complete_output and let template auto-handle waiver=0)**
```python
def _execute_type2(self, parsed_data: dict) -> CheckResult:
    # Type 2: Search pattern_items in input files
    # found_items = patterns found; missing_items = patterns not found
    # PASS/FAIL depends on check purpose (violation check vs requirement check)
    items = parsed_data.get('items', [])
    pattern_items = self.item_data.get('requirements', {{}}).get('pattern_items', [])
    
    # Convert to dict with metadata - REQUIRED for source file/line display
    found_items = {{
        item['name']: {{
            'name': item['name'],
            'line_number': item.get('line_number', 0),
            'file_path': item.get('file_path', 'N/A')
        }}
        for item in items
    }} if items else {{}}
    
    # Compare actual vs expected
    extra_items = {{
        item['name']: item for item in items 
        if item['name'] not in pattern_items
    }}
    
    return self.build_complete_output(
        found_items=found_items,
        extra_items=extra_items,
        found_desc=self.FOUND_DESC,
        missing_desc=self.MISSING_DESC,
        found_reason=self.FOUND_REASON,      # ✅ Type 2: REQUIRED!
        missing_reason=self.MISSING_REASON   # ✅ Type 2: REQUIRED!
    )
```

**Type 3: Value Check with Waiver Logic (use waiver helpers)**
```python
def _execute_type3(self, parsed_data: dict) -> CheckResult:
    # Type 3 = Type 2 + waiver support
    # Same pattern search logic as Type 2, plus waiver classification
    
    # 🔴 CRITICAL: Report ALL items found in file (not just pattern matches!)
    all_items = parsed_data.get('items', [])
    pattern_items = self.item_data.get('requirements', {{}}).get('pattern_items', [])
    
    # Step 1: Classify ALL items as found (complete visibility for users!)
    found_items = {{
        item['name']: {{
            'name': item['name'],
            'line_number': item.get('line_number', 0),
            'file_path': item.get('file_path', 'N/A')
        }}
        for item in all_items
    }}
    
    # Step 2: Check which required patterns are violated (missing or non-compliant)
    violations = []
    for pattern in pattern_items:
        # Use appropriate matching strategy (exact/substring/regex)
        matched = any(matches(item, pattern) for item in all_items)
        if not matched:
            violations.append({{'name': pattern, 'reason': 'Pattern not found'}})
    
    # Step 3: Parse waivers and classify violations
    # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() to preserve dict format
    waivers = self.get_waivers()
    waive_items_raw = waivers.get('waive_items', [])
    waive_dict = self.parse_waive_items(waive_items_raw)
    
    waived_items = []
    unwaived_items = []
    
    for violation in violations:
        matched_waiver = self.match_waiver_entry(violation, waive_dict)
        if matched_waiver:
            waived_items.append(violation)
        else:
            unwaived_items.append(violation)
    
    # Step 4: Find unused waivers
    used_names = {{w['name'] for w in waived_items}}
    unused_waivers = [name for name in waive_dict if name not in used_names]
    
    return self.build_complete_output(
        found_items=found_items,             # ✅ ALL items (pattern + non-pattern)!
        waived_items=waived_items,
        missing_items=unwaived_items,
        waive_dict=waive_dict,
        unused_waivers=unused_waivers,
        found_desc=self.FOUND_DESC,
        missing_desc=self.MISSING_DESC,
        waived_desc=self.WAIVED_DESC,                    # ✅ Type 3: REQUIRED!
        found_reason=self.FOUND_REASON,                  # ✅ Type 3: REQUIRED!
        missing_reason=self.MISSING_REASON,              # ✅ Type 3: REQUIRED!
        waived_base_reason=self.WAIVED_BASE_REASON,     # ✅ Type 3: REQUIRED!
        unused_waiver_reason=self.UNUSED_WAIVER_REASON  # ✅ Type 3: REQUIRED!
    )
```

**Type 4: Boolean Check with Waiver Logic**
```python
def _execute_type4(self, parsed_data: dict) -> CheckResult:
    # Type 4 = Type 1 + waiver support
    # Same boolean check as Type 1 (no pattern_items), plus waiver classification
    items = parsed_data.get('items', [])
    # FIXED: KNOWN_ISSUE_API-016 - Use waivers.get() to preserve dict format
    waivers = self.get_waivers()
    waive_items_raw = waivers.get('waive_items', [])
    waive_dict = self.parse_waive_items(waive_items_raw)
    
    # Implement boolean check with waiver logic
    # Use has_waiver_value=True when calling build_complete_output()
    
    return self.build_complete_output(
        found_items=items,
        waive_dict=waive_dict,
        found_desc=self.FOUND_DESC,
        missing_desc=self.MISSING_DESC,
        waived_desc=self.WAIVED_DESC,                    # ✅ Type 4: REQUIRED!
        waived_base_reason=self.WAIVED_BASE_REASON,     # ✅ Type 4: REQUIRED!
        unused_waiver_reason=self.UNUSED_WAIVER_REASON  # ✅ Type 4: REQUIRED!
        # ❌ Type 4: DO NOT pass found_reason/missing_reason
    )
```

**Framework APIs** (from template mixins):
- `self.get_waivers()` - Get waivers dict from config (CORRECT way to get waive_items!)
- `self.parse_waive_items(waive_items_raw)` - Parse waiver configuration
- `self.match_waiver_entry(item, waive_dict)` - Match item against waivers

⚠️ **CRITICAL API WARNING:**
❌ WRONG: `waive_items_raw = self.get_waive_items()`  # Converts dict to string!
✅ CORRECT: `waivers = self.get_waivers(); waive_items_raw = waivers.get('waive_items', [])`
- `self.build_complete_output(...)` - Auto-format output with waiver handling
- `self.normalize_command(cmd)` - Normalize text for consistent matching
- `self.validate_input_files()` - Validate and return TUPLE: (valid_files_list, missing_files_list)


**Common Pitfalls to Avoid**:
- ❌ Skipping mandatory mixins (OutputBuilderMixin & WaiverHandlerMixin)
- ❌ Re-implementing output formatting instead of using `build_complete_output()`
- ❌ Manually normalizing commands; use `self.normalize_command()`
- ❌ Adding waiver tags to DetailItem.name (must stay in reason)
- ❌ Forgetting to document unused waivers (pass `unused_waivers` list)
- ❌ Leaving TODO logic from template skeletons


## 6. OUTPUT STRUCTURE - CRITICAL!

**⚠️ info_groups.items MUST match details.name exactly!**

The `build_complete_output()` helper handles this automatically, but if you create
manual output, ensure:

```python
# For waived items:
waived_names = ['item1', 'item2']

# Create details
details = [
    DetailItem(name=name, reason="Reason[WAIVER]")  # Tag in reason, NOT name
    for name in waived_names
]

# Create info_groups - items must match details.name!
info_groups = {{
    "INFO01": {{
        "description": "Waived items",
        "items": waived_names  # Same names as details
    }}
}}
```


## 7. MAIN ENTRY POINT

```python
if __name__ == '__main__':
    checker = Checker()
    checker.run()
```

{'='*80}
"""
    
    return instructions


def _build_footer() -> str:
    """Build prompt footer."""
    return f"""
{'='*80}
📝 PRE-COMMIT CHECKLIST (DEVELOPER_TASK_PROMPTS.md Step 3)
{'='*80}

Before generating code, ensure:
✅ BLOCK 1: Imported WaiverHandlerMixin + OutputBuilderMixin (mandatory)
✅ BLOCK 2: Added complete header with detailed Logic section (3-6 steps)
✅ BLOCK 2: **Waiver Tag Rules section copied EXACTLY as shown (DO NOT simplify!)**
✅ BLOCK 2: Included "Refactored: YYYY-MM-DD (Using checker_templates v1.1.0)" line
✅ BLOCK 2: Author field preserved exactly as is (DO NOT modify)
✅ BLOCK 3: Used validate_input_files() and raised ConfigurationError for missing files
✅ BLOCK 3: Used template helpers (parse_log_with_patterns, normalize_command)
✅ BLOCK 3: **Template comments preserved and filled in (NOT deleted)**
✅ BLOCK 4: All 4 type methods use build_complete_output() from template
✅ BLOCK 4: Waiver tags in reason field only ([WAIVER], [WAIVED_AS_INFO])
✅ Used patterns from Step 2.5 file analysis (if available)
✅ Error handling with ConfigurationError for config issues
✅ No TODO placeholders left in production code

{'='*80}
📊 OUTPUT LOG/REPORT FORMAT REQUIREMENTS
{'='*80}

Consider how results will appear in logs/reports:

**INFO01 Section**: Display descriptive item names with context
  - Example: "func_rcss_0p675v_125c: reg2reg setup clean (slack=0.123ns)"

**ERROR01 Section**: Display specific violation details
  - Example: "TIMING VIOLATION: Corner X, Path Group Y, Slack -0.012ns (3 violations)"

**PASS/FAIL Reasons**: Clear explanations
  - PASS: "All timing is clean (32 corners analyzed, 0 violations)"
  - FAIL: "5 timing violations found in 2 corners"

{'='*80}

⚠️ CODE OUTPUT FORMAT REQUIREMENTS:
1. Generate ONLY raw Python code
2. DO NOT wrap code in ```python ... ``` markers
3. Start directly with the file header comment (################################)
4. The code will be extracted and saved as-is

{'='*80}

Generate the complete, production-ready checker code now.
"""


# Export both versions
def build_checker_prompt(
    request: CheckerAgentRequest,
    context_fragments: Sequence[ContextFragment],
    *,
    instructions: str | None = None,
    extra_notes: Iterable[str] | None = None,
) -> str:
    """
    Backward compatible wrapper.
    
    For new code, use build_checker_prompt_v2 with file_analysis parameter.
    """
    # Use v2 without file analysis for backward compatibility
    return build_checker_prompt_v2(
        request,
        context_fragments,
        file_analysis=None,
        instructions=instructions,
        extra_notes=extra_notes,
    )
