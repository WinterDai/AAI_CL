"""
Code Generation Mixin for IntelligentCheckerAgent.

This mixin handles all code implementation functionality:
- AI-powered code generation (Step 4)
- Loading existing skeleton code
- Building code implementation prompts
- Extracting code from AI responses
"""

from typing import Any, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from rich.console import Console


class CodeGenerationMixin:
    """Mixin providing code generation capabilities."""
    
    def _ai_implement_complete_code(
        self,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
    ) -> str:
        """
        AI implements COMPLETE checker code using MULTI-PHASE generation.
        
        Instead of generating all code at once (which may exceed token limits),
        this method generates code in 3 phases:
        
        Phase 1: Header + Imports + Class + _parse_input_files()
        Phase 2: Type 1 & Type 4 methods (boolean checks with/without waiver)
        Phase 3: Type 2 & Type 3 methods (pattern checks with/without waiver)
        
        Each phase uses smaller token budgets and is more reliable.
        Type 4 reuses Type 1 core logic + waiver handling.
        Type 3 reuses Type 2 core logic + waiver handling.
        """
        print("\n" + "─"*80)
        print("[Step 5/9] 💻 Multi-Phase Code Generation")
        print("─"*80)
        
        # 0. Backup existing skeleton code BEFORE AI fills it (for Reset functionality)
        self._backup_code_template(config)
        print("  📦 Backed up skeleton template")
        
        # === PROGRESS: Step 1/6 ===
        print("\n📋 [1/6] Validating configuration...")
        if not config.get('item_id') or not config.get('module'):
            raise ValueError("Invalid configuration: missing item_id or module")
        print(f"    ✅ Configuration valid (Item: {config['item_id']})")
        
        # === PROGRESS: Step 2/6 ===
        print("\n📄 [2/6] Loading existing code...")
        existing_skeleton = self._load_existing_skeleton(config)
        skeleton_lines = len(existing_skeleton.split('\n')) if existing_skeleton else 0
        if skeleton_lines > 0:
            print(f"    ✅ Loaded {skeleton_lines} lines (existing code)")
        else:
            print(f"    ✅ Starting from scratch (no existing skeleton)")
        
        # === PROGRESS: Step 3/6 ===
        print("\n🔢 [3/6] Planning multi-phase generation...")
        print("    📝 Phase 1: Header + Imports + Class + _parse_input_files()")
        print("    📝 Phase 2: Type 1 & Type 4 (boolean checks, Type4 reuses Type1 logic)")
        print("    📝 Phase 3: Type 2 & Type 3 (pattern checks, Type3 reuses Type2 logic)")
        print(f"    ✅ 3 phases planned (safer than single 64K+ token call)")
        
        # Prepare LLM
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        agent = self._get_llm_agent()
        
        # === PROGRESS: Step 4/6 - Generate code in phases ===
        print("\n🧠 [4/6] AI generating code in phases...")
        
        try:
            # Phase 1: Header + Imports + Class + _parse_input_files()
            print("\n  🔹 Phase 1/3: Generating header, imports, class, and _parse_input_files()...")
            phase1_code = self._generate_phase1(config, file_analysis, readme, agent, existing_skeleton)
            print(f"    ✅ Phase 1 complete ({len(phase1_code.split(chr(10)))} lines)")
            
            # Phase 2: Type 1 & Type 4 methods (boolean checks)
            print("\n  🔹 Phase 2/3: Generating Type 1 & Type 4 methods (Type4 reuses Type1 logic)...")
            phase2_code = self._generate_phase2_type1_and_type4(config, file_analysis, readme, agent, phase1_code)
            print(f"    ✅ Phase 2 complete ({len(phase2_code.split(chr(10)))} lines)")
            
            # Phase 3: Type 2 & Type 3 methods (pattern checks)
            print("\n  🔹 Phase 3/3: Generating Type 2 & Type 3 methods (Type3 reuses Type2 logic)...")
            phase3_code = self._generate_phase3_type2_and_type3(config, file_analysis, readme, agent, phase1_code)
            print(f"    ✅ Phase 3 complete ({len(phase3_code.split(chr(10)))} lines)")
            
            # Combine all phases (main() is in skeleton, no need for phase4)
            code_content = self._combine_phases(phase1_code, phase2_code, phase3_code)
            code_lines = len(code_content.split('\n'))
            
            print(f"\n  ✅ All phases complete! Total: {code_lines} lines")
            
        except Exception as e:
            print(f"\n  ❌ Multi-phase generation failed: {str(e)[:100]}...")
            print(f"  🔄 Falling back to single-phase generation...")
            
            # Fallback to original single-phase generation
            max_tokens = 64000
            llm_config = LLMCallConfig(temperature=0.2, max_tokens=max_tokens)
            prompt = self._build_code_implementation_prompt(config, file_analysis, readme, existing_skeleton)
            
            for attempt in range(2):
                try:
                    response = agent._llm_client.complete(prompt, config=llm_config)
                    code_content = self._extract_code_from_response(response.text)
                    code_lines = len(code_content.split('\n'))
                    print(f"    ✅ Fallback generation complete ({code_lines} lines)")
                    break
                except Exception as fallback_error:
                    print(f"    ❌ Fallback attempt {attempt+1} failed: {str(fallback_error)[:60]}...")
                    if attempt == 1:
                        code_content = existing_skeleton if existing_skeleton else ""
                        code_lines = len(code_content.split('\n')) if code_content else 0
        
        # === PROGRESS: Step 5/6 ===
        print("\n🔍 [5/6] Validating generated code...")
        
        if code_content:
            is_complete, warnings = self._validate_code_completeness_v2(
                code_content, 
                existing_skeleton, 
                code_lines
            )
            
            if is_complete:
                quality_score = self._score_generation_quality(code_content, skeleton_lines)
                print(f"    ✅ Quality Score: {quality_score}/100", end="")
                
                if quality_score >= 90:
                    print(" (Excellent)")
                elif quality_score >= 70:
                    print(" (Good)")
                elif quality_score >= 50:
                    print(" (Acceptable)")
                else:
                    print(" (Needs Review)")
                
                print(f"    ✅ All checks passed ({code_lines} lines generated)")
            else:
                print(f"    ⚠️  Validation warnings:")
                for warning in warnings[:3]:
                    print(f"       • {warning}")
        else:
            print("    ❌ No code generated")
            code_content = existing_skeleton if existing_skeleton else ""
            code_lines = 0
        
        # === PROGRESS: Step 6/6 ===
        print("\n📊 [6/6] Summary")
        print("="*80)
        self._log(f"Generated {code_lines} lines of code (multi-phase method)", "INFO", "✅")
        
        return code_content
    
    def _load_existing_skeleton(self, config: dict[str, Any]) -> str:
        """
        Load existing skeleton code if it exists.
        
        Args:
            config: Configuration dict containing 'module' and 'item_id'
        
        Returns:
            Skeleton code content or empty string if not found
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Use config dict values, not self attributes (which may not be set yet)
        module = config.get('module', '')
        item_id = config.get('item_id', '')
        
        if not module or not item_id:
            if hasattr(self, 'verbose') and self.verbose:
                print(f"    ⚠️  Missing module or item_id in config")
            return ""
        
        checker_file = (
            paths.workspace_root / 
            "Check_modules" / 
            module / 
            "scripts" / 
            "checker" / 
            f"{item_id}.py"
        )
        
        if checker_file.exists():
            with open(checker_file, 'r', encoding='utf-8') as f:
                skeleton_code = f.read()
            # Verbose logging removed - shown in main progress display
            return skeleton_code
        else:
            if hasattr(self, 'verbose') and self.verbose:
                print(f"    ⚠️  Skeleton not found at: {checker_file}")
            return ""
    
    def _build_code_implementation_prompt(
        self,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
        existing_skeleton: str = "",
    ) -> str:
        """
        Build comprehensive prompt for code implementation.
        
        Based on DEVELOPER_TASK_PROMPTS.md v1.1.0 Step 3 (BLOCK 1-4).
        
        Args:
            existing_skeleton: If provided, AI will modify this skeleton instead of generating from scratch
        """
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Determine mode: modify skeleton or generate from scratch
        if existing_skeleton:
            mode_instruction = f"""⚠️ CRITICAL: You are MODIFYING an existing skeleton, NOT generating from scratch!

EXISTING SKELETON CODE:
```python
{existing_skeleton}
```

YOUR TASK:
1. Keep the EXACT class structure and method signatures
2. Fill in ALL TODO sections with real implementation
3. Update the header comment's "Logic:" section with specific steps
4. Implement _parse_input_files() with actual parsing logic
5. Implement all 4 _execute_typeN() methods with real check logic
6. DO NOT change class name, method names, or inheritance order
7. DO NOT remove any template comments or structure

Return the COMPLETE modified code (all lines, not just changes)."""
        else:
            mode_instruction = """You are generating a COMPLETE new checker from scratch."""
        
        return f"""Implement COMPLETE Python checker code for {config['item_id']}.

{mode_instruction}

CRITICAL: Follow DEVELOPER_TASK_PROMPTS.md v1.1.0 Step 3 (BLOCK 1-4 structure).

⚠️ MANDATORY RULES:
1. Use Template Library (WaiverHandlerMixin + OutputBuilderMixin)
2. **DO NOT MODIFY** the standard Waiver Tag Rules section - use EXACTLY as shown below
3. **DO NOT DELETE** template comments - fill in the TODOs with real implementation
4. Consider output logs/reports format requirements (see OUTPUT FORMAT section below)

Reference: Check_modules/common/checker_templates/README.md (30+ examples)

Requirements from Step 3:

1. **Header Comment (MANDATORY - DO NOT MODIFY Waiver Tag Rules!)**:
```python
################################################################################
# Script Name: {config['item_id']}.py
#
# Purpose:
#   {config['description']}
#
# Logic:
#   - Parse input files: {', '.join(Path(f).name for f in config.get('input_files', []))}
#   - [AI: Add 3-6 specific parsing steps based on file analysis]
#   - [AI: Add validation/comparison logic]
#   - [AI: Add waiver handling if applicable]
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   existence_check: pattern_items = items that SHOULD EXIST in input files
#     - found_items = patterns found in file
#     - missing_items = patterns NOT found in file
#   status_check: pattern_items = items to CHECK STATUS (only output matched items)
#     - found_items = patterns matched AND status correct
#     - missing_items = patterns matched BUT status wrong
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
# Author: AutoGenChecker AI
# Date: {current_date}
################################################################################
```

2. **BLOCK 1 - Template Setup (MANDATORY)**:
   - Import WaiverHandlerMixin, OutputBuilderMixin, InputFileParserMixin
   - Inherit in correct order: InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker
   - Add "Refactored: 2025-12-15 (Using checker_templates)" line in header

3. **BLOCK 2 - File Header** (see above)

4. **BLOCK 3 - _parse_input_files() with Template Helpers**:
   - Use validate_input_files() which returns TUPLE: (valid_files, missing_files)
   - Raise ConfigurationError for missing files
   - Use parse_log_with_patterns(), normalize_command() helpers
   - Return aggregated dict

5. **BLOCK 4 - All 4 Type Methods with build_complete_output()**

2. **Complete Implementation (with Template Mixins)**:

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

# MANDATORY: Import template mixins (BLOCK 1)
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in this order (InputFileParserMixin first if used)
class Checker(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    def __init__(self):
        super().__init__(
            check_module="{config['module']}",
            item_id="{config['item_id']}",
            item_desc="{config['description']}"
        )
    
    def execute_check(self) -> CheckResult:
        '''Execute the checker logic.'''
        # DO NOT reimplement - use BaseChecker's method
        checker_type = self.detect_checker_type()
        parsed_data = self._parse_input_files()
        
        if checker_type == 1:
            return self._execute_type1(parsed_data)
        elif checker_type == 2:
            return self._execute_type2(parsed_data)
        elif checker_type == 3:
            return self._execute_type3(parsed_data)
        else:
            return self._execute_type4(parsed_data)
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> dict:
        '''
        Parse input files based on Step 2.5 analysis (BLOCK 3).
        
        File Analysis Results:
        {file_analysis}
        
        ⚠️ CRITICAL - SEMANTIC CONSISTENCY REQUIREMENT (Type 2/3 only):
        =====================================================================
        The granularity of extracted values MUST match pattern_items in README!
        
        README Pattern Items (golden values for matching):
        {{readme_pattern_items}}
        
        ⚠️⚠️⚠️ Type 3/4 SEMANTIC UNDERSTANDING - CRITICAL! ⚠️⚠️⚠️
        =====================================================================
        pattern_items and waive_items have DIFFERENT semantics! DO NOT treat them as same format!
        
        🎯 pattern_items = GOLDEN VALUE (expected value for matching)
           - Type 3: Defines "what values are correct" (versions, patterns, values)
           - Type 4: Defines "what conditions trigger check" (boolean conditions)
           - Example: ["2.1.0", "v3.*"] (version numbers)
           - Example: ["SPEF: Loaded", "DELAY: Loaded"] (status values)
           
        🏷️ waive_items = EXEMPTION OBJECTS (objects to exempt, matched by name)
           - Type 3/4: Defines "which objects are exempted" (library names, module names, file names)
           - The 'name' field identifies WHICH object to exempt
           - Example: [{{"name": "legacy_lib"}}, {{"name": "special_module"}}] (library names)
           
        💡 LOGIC FOR Type 3/4 _execute() METHODS:
           1. Parse found_items with 'name' field identifying the object
           2. Compare found_item values against pattern_items (golden values)
           3. If NOT matching pattern → it's a violation → check if waive_items exempts it
           4. Match waive by: found_item['name'] == waive_item['name']
           
        Example for version check (Type 3):
           - found_items: {{"lib_A": {{..., "version": "1.0.0"}}, "lib_B": {{..., "version": "2.1.0"}}}}
           - pattern_items: ["2.1.0", "v2.*"]  # GOLDEN versions
           - waive_items: [{{"name": "lib_A", "reason": "legacy"}}]  # EXEMPT lib_A object
           - Logic: lib_A version="1.0.0" NOT in pattern → check waive → MATCH lib_A → WAIVE
                    lib_B version="2.1.0" in pattern → PASS
        =====================================================================
        
        SEMANTIC ALIGNMENT RULES:
        
        1. If pattern_items contain VERSION IDENTIFIERS (e.g., "22.11-s119_1", "v3.2"):
           → Extract ONLY version numbers, NOT full paths or filenames
           → Example: From "innovus/221/22.11-s119_1" extract "22.11-s119_1"
           → Example: From "CORE65GPSVT_v3.2.lib" extract "v3.2" if pattern is version
        
        2. If pattern_items contain FILENAMES (e.g., "design.v", "lib_v3.2.lib"):
           → Extract COMPLETE filenames with extensions
           → Example: From path "/home/user/design.v" extract "design.v"
           → Example: Keep "CORE65GPSVT_v3.2.lib" as complete filename
        
        3. If pattern_items contain STATUS VALUES (e.g., "MODIFIED", "LOADED"):
           → Extract STATUS strings, NOT boolean flags
           → Example: Extract "MODIFIED" or "UNMODIFIED", NOT True/False
           → Example: Extract "SPEF: Loaded" or "SPEF: Skipped", NOT boolean
        
        4. If pattern_items contain COUNTS (e.g., "0", "5"):
           → Extract numeric counts as strings
           → Example: Extract "0" for no violations, "5" for five errors
        
        ⚠️ The item['name'] field MUST use the SAME semantic level as pattern_items!
        This ensures pattern matching in _execute_type2/3() will succeed.
        =====================================================================
        
        MANDATORY Steps:
        1. Validate inputs with validate_input_files() - returns (valid_files, missing_files) tuple
        2. Raise ConfigurationError for missing files
        3. Use template helpers: parse_log_with_patterns(), normalize_command()
        4. Extract values at the SAME semantic granularity as pattern_items (see rules above)
        5. ⚠️ CRITICAL: EVERY parsed item MUST include {{'name': str, 'line_number': int, 'file_path': str}}
        6. Store frequently reused data on self
        7. Return aggregated dict: {{'items': all_items, 'metadata': {{'total': len(all_items)}}}}
        '''
        # Implementation: validate_input_files() returns tuple (valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        if not valid_files:
            raise ConfigurationError("No valid input files found")
        
        # Parse and collect items with metadata
        all_items = []
        for file_path in valid_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Parse line and append: all_items.append({{'name': ..., 'line_number': line_num, 'file_path': str(file_path)}})
                    pass
        
        self._parsed_items = all_items
        return {{'items': all_items, 'metadata': {{'total': len(all_items)}}}}

⚠️ NOTE: Type 1/2/3/4 implementation details and complete examples are provided in Phase 2 and Phase 3 generation sections below. This main prompt focuses on data structure and parsing requirements.


README Context (for understanding requirements):
{readme}

====================================================================================
⚠️ OUTPUT BEHAVIOR FROM README (CRITICAL for Type 2/3 Logic!)
====================================================================================

{{self._extract_output_behavior(readme)}}

====================================================================================
⚠️ OUTPUT DISPLAY FORMAT (Automatic via build_complete_output())
====================================================================================

Output format is AUTOMATIC. Just structure data correctly:
- found_items/missing_items/waived_items/extra_items: Dict with metadata
- Each item value MUST be: {{'name': str, 'line_number': int, 'file_path': str}}
- Log format: "- [item_name]: [reason]"
- Report format: "Info/Fail: [item_name]. In line [line_number], [file_path]: [reason]"

README Display Format section (for reference):
{{self._extract_output_format(readme)}}

====================================================================================
⚠️ OUTPUT DESCRIPTIONS FROM README (Use EXACT strings as class constants)
====================================================================================

{{self._extract_readme_output_descriptions_for_code_gen(readme)}}

CRITICAL: Define these as CLASS CONSTANTS - copy exact strings from README:
- Type 1/4: FOUND_DESC_TYPE1_4, MISSING_DESC_TYPE1_4, FOUND_REASON_TYPE1_4, MISSING_REASON_TYPE1_4
- Type 2/3: FOUND_DESC_TYPE2_3, MISSING_DESC_TYPE2_3, FOUND_REASON_TYPE2_3, MISSING_REASON_TYPE2_3  
- Waiver (all): WAIVED_DESC, WAIVED_BASE_REASON (Type 3/4), UNUSED_WAIVER_REASON (Type 3/4)

====================================================================================
⚠️ build_complete_output() Parameter Reference (see Phase 2/3 for complete templates):

Data parameters: found_items (Dict), missing_items (List), waived_items (List, Type 3/4), 
                 unused_waivers (List, Type 3/4), extra_items (Dict, Type 2), waive_dict (Dict)
Description parameters: found_desc, missing_desc, waived_desc, extra_desc (Type 2)
Reason parameters: found_reason, missing_reason, waived_base_reason (Type 3/4), unused_waiver_reason (Type 3/4)

⚠️ Complete usage templates with all required parameters are in Phase 2/3 FORCED OUTPUT TEMPLATE sections.
====================================================================================
```

The README's "Output Description Specifications" section contains EXACTLY what
you should use for these parameters. DO NOT invent your own descriptions.

⚠️ NON-NEGOTIABLE STRUCTURE REQUIREMENT:
- `found_items`, `waived_items`, `extra_items`, `violation_items`, etc. **MUST** be `dict[str, Dict[str, Any]]` keyed by the item name. Each value stores metadata (always include `line_number` and `file_path`, plus optional `reason` or other context fields).
- Example of CORRECT structure:
```python
waived_items = {{
    item_name: {{
        'line_number': net.get('line_number', 0),
        'file_path': net.get('file_path', 'N/A'),
        'reason': net.get('reason', '')
    }}
}}
```
- NEVER build these collections as lists (e.g., `waived_items = []` + `.append({{{{...}}}}))`). `build_complete_output()` expects dicts and will crash if lists are provided.
- `parse_waive_items()` returns a dict whose KEYS are waiver identifiers (strings). When finding unused waivers, compare against `waived_items.keys()` / `found_items.keys()` (strings only). Do **NOT** try to use entire dict objects as keys.

====================================================================================
⚠️ TYPE 3 / TYPE 4 WAIVER IMPLEMENTATION CONSTRAINTS
====================================================================================
- Type 3 MUST start from the same pattern-matching logic as Type 2 (`existence_check` unless README explicitly says `status_check`). Only after a pattern is matched do you classify it into `found_items` (not waived) versus `waived_items` (matches a waiver). `missing_items` = patterns not matched anywhere in the parsed data.
- Type 4 MUST start from the same boolean logic as Type 1 (acceptable vs physically open nets, or whatever the Type 1 definition is). After you classify the violations, split them into `waived_items` (waiver matched) and `missing_items` (no waiver).
- `waived_items` and `found_items` are always dicts keyed by item name; `missing_items` remains a list of item names/patterns.
- When computing `unused_waivers`, build `used_names = set(waived_items.keys())`, update it with any other relevant matches (e.g., `found_items.keys()` for existence checks), and then compute `[name for name in waive_dict.keys() if name not in used_names]`. Do not store dict objects inside `used_names`.
- Reasons must keep the `[WAIVER]` suffixes described in the Waiver Tag Rules section—`build_complete_output()` automatically adds them when you pass `waived_base_reason`/`unused_waiver_reason`.

====================================================================================
⚠️ OUTPUT BEHAVIOR - Type 2/3 Pattern Matching Logic (CRITICAL!)
====================================================================================

**CHECK README "Output Behavior" SECTION to determine which mode to use!**

### Mode 1: `existence_check` - Existence Check
**Use when:** pattern_items are items that SHOULD EXIST in input files

```python
def _execute_type2(self) -> CheckResult:
    '''existence_check mode: Check if pattern_items exist in input files
    
    ⚠️ CRITICAL: Every item MUST include line_number and file_path for report output!
    '''
    data = self._parse_input_files()
    items = data.get('items', [])
    pattern_items = self.item_data.get('requirements', {{}}).get('pattern_items', [])
    
    # Find which patterns exist in parsed items
    found_items = {{}}
    missing_items = []
    
    for pattern in pattern_items:
        matched = False
        for item in items:
            if pattern.lower() in item['name'].lower():  # or exact match
                # ⚠️ MANDATORY: Include line_number and file_path from parsed item!
                found_items[item['name']] = {{
                    'name': item['name'],
                    'line_number': item.get('line_number', 0),  # REQUIRED!
                    'file_path': item.get('file_path', 'N/A')   # REQUIRED!
                }}
                matched = True
                break
        if not matched:
            missing_items.append(pattern)  # Pattern NOT found in file
    
    return self.build_complete_output(
        found_items=found_items,    # Patterns found in file
        missing_items=missing_items, # Patterns NOT found in file
        ...
    )
```

⚠️ KEY PATTERNS:
- existence_check (Type 2): missing_items = patterns NOT found in file
- status_check (Type 2/3): missing_items = patterns found BUT status wrong

⚠️ Complete implementation examples are in Phase 2/3 FORCED OUTPUT TEMPLATE sections.
====================================================================================
⚠️ CORE REQUIREMENTS:
====================================================================================

1. Inherit: BaseChecker, WaiverHandlerMixin, OutputBuilderMixin
2. Implement _parse_input_files() with validate_input_files() → returns TUPLE: (valid_files, missing_files)
3. Implement ALL 4 type methods with build_complete_output()
4. Every parsed item MUST include: {{'name': str, 'line_number': int, 'file_path': str}}
5. Production-ready code (proper error handling, no TODO placeholders, keep Author field unchanged)

====================================================================================
⚠️ OUTPUT LOG/REPORT FORMAT REQUIREMENTS
====================================================================================

Report output format: `<Info/Fail/Warn>: <name>. In line <line_number>, <file_path>: <reason>`

CRITICAL: Every item in found_items/missing_items/waived_items MUST include line_number and file_path metadata:
```python
found_items = {{'item_name': {{'name': 'item_name', 'line_number': N, 'file_path': '...'}}}}
```

====================================================================================

====================================================================================
⚠️ COMMON MISTAKES TO AVOID:
====================================================================================

[API-001] validate_input_files() returns TUPLE (valid_files, missing_files) - unpack both!
[API-002] build_complete_output() uses found_desc/missing_desc (no item_desc parameter!)
[API-003] found_items must be dict with metadata: {{'item': {{'line_number': N, 'file_path': '...'}}}}
[OUT-001] Every parsed item MUST include line_number and file_path metadata
[API-004] DetailItem requires: name, severity, reason, line_number, file_path (all positional fields)

====================================================================================

====================================================================================
⚠️ TYPE-SPECIFIC IMPLEMENTATION HINTS (CRITICAL!)
====================================================================================

The following are MANDATORY implementation requirements for each type.
DO NOT skip these steps - they are the core logic for each type!

{{self._get_type_specific_hints_for_prompt(config)}}

====================================================================================

⚠️ CODE OUTPUT FORMAT:
- Generate ONLY raw Python code (no ```python markers)
- Start directly with ################################################################################
- Code will be saved as-is to .py file"""
    
    def _get_type_specific_hints_for_prompt(self, config: dict[str, Any]) -> str:
        """
        Get type-specific hints from api_v2_reference.py.
        
        Returns all 4 types' hints so AI understands the differences.
        """
        try:
            from prompt_templates.api_v2_reference import get_type_specific_hints
        except ImportError:
            from AutoGenChecker.prompt_templates.api_v2_reference import get_type_specific_hints
        
        # Get hints for all 4 types
        hints_parts = []
        for type_num in [1, 2, 3, 4]:
            hint = get_type_specific_hints(type_num)
            if hint:
                hints_parts.append(hint)
        
        return "\n\n".join(hints_parts)
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract Python code from AI response.
        
        Handles multiple formats:
        1. Raw code starting with ####... (preferred)
        2. Code wrapped in ```python ... ```
        3. Code wrapped in ``` ... ```
        """
        import re
        
        # Format 1: Raw code starting with file header
        if response.strip().startswith('####'):
            return response.strip()
        
        # Format 2: Code block with python marker
        code_match = re.search(r'```python\s*(.+?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Format 3: Code block without language marker
        code_match = re.search(r'```\s*(.+?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Format 4: Entire response is code
        return response.strip()
    
    def _calculate_required_tokens(self, code: str, is_modification: bool = True) -> int:
        """
        Calculate required max_tokens based on code size and operation type.
        
        Formula for MODIFICATION (default):
        - Output needs full code: lines × 25 tokens/line
        - Add 100% buffer (AI overhead + possible expansion)
        - Minimum: 48000 (for medium files)
        - Maximum: 128000 (model limit)
        
        Formula for NEW GENERATION:
        - Similar calculation but lower minimum (32000)
        
        Args:
            code: Existing skeleton code (or empty string for new generation)
            is_modification: True if modifying existing code, False if generating new
            
        Returns:
            Calculated max_tokens value
        """
        if not code:
            # New generation from scratch - lower requirements
            return 32000
        
        # Count lines
        lines = code.count('\n') + 1
        
        if is_modification:
            # Modification: Need to output complete modified file
            # Use 2.5x multiplier because:
            # - AI needs to regenerate everything (1x)
            # - Modifications often add code (0.5x)
            # - Safety buffer (1x)
            base_tokens = int(lines * 25 * 2.5)
            min_tokens = 64000  # Higher minimum for modifications
        else:
            # New generation: More efficient
            base_tokens = int(lines * 25 * 1.5)
            min_tokens = 32000
        
        # Apply bounds
        calculated_tokens = max(min(base_tokens, 128000), min_tokens)
        
        # Log if available (mixin may not have _log in standalone tests)
        if hasattr(self, '_log'):
            mode = "modification" if is_modification else "generation"
            self._log(f"Token calculation ({mode}): {lines} lines → {base_tokens} base → {calculated_tokens} final", "DEBUG")
        
        return calculated_tokens
    
    def _validate_code_completeness(self, generated_code: str, skeleton_code: str, generated_lines: int) -> None:
        """
        Validate that generated code is complete and not truncated.
        
        Checks:
        1. Has main() function
        2. Has if __name__ == '__main__' block
        3. Similar line count to skeleton (if modifying)
        4. No abrupt endings
        
        Args:
            generated_code: The generated code
            skeleton_code: Original skeleton (empty if new generation)
            generated_lines: Number of lines in generated code
        """
        warnings = []
        
        # Check 1: Has main function
        if 'def main():' not in generated_code and 'def main(' not in generated_code:
            warnings.append("Missing main() function - code may be truncated")
        
        # Check 2: Has entry point
        if "__name__ == '__main__'" not in generated_code and '__name__ == "__main__"' not in generated_code:
            warnings.append("Missing __name__ == '__main__' block - code may be truncated")
        
        # Check 3: Line count comparison (if modifying existing code)
        if skeleton_code:
            skeleton_lines = skeleton_code.count('\n') + 1
            line_diff_ratio = abs(generated_lines - skeleton_lines) / skeleton_lines
            
            # If generated code is 50%+ shorter, likely truncated
            if generated_lines < skeleton_lines * 0.5:
                warnings.append(f"Generated code ({generated_lines} lines) is 50%+ shorter than skeleton ({skeleton_lines} lines) - likely truncated")
        
        # Check 4: Ends properly (not mid-function)
        last_lines = generated_code.strip().split('\n')[-5:]
        last_content = '\n'.join(last_lines)
        
        # Should not end with incomplete def/class or mid-line code
        if any(line.strip().startswith(('def ', 'class ')) and ':' not in line for line in last_lines):
            warnings.append("Code ends with incomplete function/class definition")
        
        # Display warnings
        if warnings:
            print("\n" + "="*80)
            print("⚠️  CODE COMPLETENESS WARNINGS:")
            print("="*80)
            for warning in warnings:
                print(f"  • {warning}")
            print("\n💡 Possible causes:")
            print("  1. LLM output token limit reached (try increasing max_tokens)")
            print("  2. LLM response was cut off mid-generation")
            print("  3. Code extraction failed to capture complete output")
            print("\n🔧 Recommendations:")
            print("  • Review generated code carefully")
            print("  • Check if main() and Type methods are complete")
            print("  • Consider regenerating with higher token limit")
            print("="*80 + "\n")
    
    def _validate_code_completeness_v2(self, generated_code: str, skeleton_code: str, generated_lines: int) -> tuple[bool, list[str]]:
        """
        Enhanced validation that returns completion status and warnings.
        
        Returns:
            (is_complete: bool, warnings: list[str])
        """
        warnings = []
        critical_errors = []
        
        # Check 1: Has main function
        if 'def main():' not in generated_code and 'def main(' not in generated_code:
            critical_errors.append("Missing main() function")
        
        # Check 2: Has entry point
        if "__name__ == '__main__'" not in generated_code and '__name__ == "__main__"' not in generated_code:
            critical_errors.append("Missing __name__ == '__main__' block")
        
        # Check 3: Has all 4 Type methods
        type_methods = ['_execute_type1', '_execute_type2', '_execute_type3', '_execute_type4']
        for method in type_methods:
            if f'def {method}(' not in generated_code:
                critical_errors.append(f"Missing {method}() method")
        
        # Check 4: Has parse method
        if 'def _parse_input_files(' not in generated_code:
            warnings.append("Missing _parse_input_files() method")
        
        # Check 5: Line count comparison (if modifying existing code)
        if skeleton_code:
            skeleton_lines = skeleton_code.count('\n') + 1
            line_diff_ratio = abs(generated_lines - skeleton_lines) / skeleton_lines
            
            if generated_lines < skeleton_lines * 0.5:
                critical_errors.append(f"Generated code ({generated_lines} lines) is 50%+ shorter than skeleton ({skeleton_lines} lines)")
            elif line_diff_ratio > 0.3:
                warnings.append(f"Line count differs by {int(line_diff_ratio*100)}% from skeleton")
        
        # Check 6: Basic syntax check (try AST parse)
        try:
            import ast
            ast.parse(generated_code)
        except SyntaxError as e:
            critical_errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception:
            warnings.append("Could not perform full syntax validation")
        
        # Check 7: Ends properly
        last_lines = generated_code.strip().split('\n')[-5:]
        if any(line.strip().startswith(('def ', 'class ')) and ':' not in line for line in last_lines):
            critical_errors.append("Code ends with incomplete function/class definition")
        
        # Determine completeness
        is_complete = len(critical_errors) == 0
        all_warnings = critical_errors + warnings
        
        return is_complete, all_warnings
    
    def _score_generation_quality(self, generated_code: str, skeleton_lines: int = 0) -> int:
        """
        Score the quality of generated code (0-100).
        
        Scoring breakdown:
        - 25 points: Has main() function
        - 25 points: Has all 4 Type methods
        - 20 points: Has _parse_input_files()
        - 15 points: Line count reasonable (if skeleton exists)
        - 15 points: No syntax errors
        
        Returns:
            Score from 0 to 100
        """
        score = 0
        
        # 25 points: Has main function
        if 'def main():' in generated_code or 'def main(' in generated_code:
            score += 25
        
        # 25 points: Has all 4 Type methods (6.25 each)
        type_methods = ['_execute_type1', '_execute_type2', '_execute_type3', '_execute_type4']
        for method in type_methods:
            if f'def {method}(' in generated_code:
                score += 6.25
        
        # 20 points: Has _parse_input_files
        if 'def _parse_input_files(' in generated_code:
            score += 20
        
        # 15 points: Line count reasonable (if skeleton provided)
        if skeleton_lines > 0:
            generated_lines = generated_code.count('\n') + 1
            ratio = generated_lines / skeleton_lines
            if 0.5 <= ratio <= 2.0:
                score += 15  # Within reasonable range
            elif 0.3 <= ratio <= 3.0:
                score += 7   # Acceptable range
        else:
            # No skeleton, check if reasonable size
            generated_lines = generated_code.count('\n') + 1
            if 400 <= generated_lines <= 1500:
                score += 15
            elif 200 <= generated_lines <= 2000:
                score += 7
        
        # 15 points: No syntax errors
        try:
            import ast
            ast.parse(generated_code)
            score += 15
        except:
            pass
        
        return int(score)
    
    # =========================================================================
    # Multi-Phase Code Generation Methods
    # =========================================================================
    
    def _generate_phase1(
        self,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
        agent: Any,
        existing_skeleton: str = "",
    ) -> str:
        """
        Phase 1: MODIFY skeleton by filling TODO sections.
        Generate: Header + Imports + Class + Constants + __init__ + execute_check + _parse_input_files()
        
        Token budget: ~16K tokens (safe for most cases).
        """
        from datetime import datetime
        from utils.models import LLMCallConfig
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Determine mode: MODIFY existing skeleton or GENERATE with skeleton structure
        if existing_skeleton:
            # Mode 1: MODIFY existing skeleton
            mode_instruction = f"""⚠️ CRITICAL: MODIFY the skeleton template by filling TODO sections!

EXISTING SKELETON (YOUR TEMPLATE):
```python
{existing_skeleton}
```

YOUR TASK - PRESERVE ARCHITECTURE AND FILL TODOs:
1. ⭐ PRESERVE ALL skeleton structure:
   - Keep EXACT class name: {existing_skeleton.split('class ')[1].split('(')[0] if 'class ' in existing_skeleton else 'Check_' + config['item_id'].replace('-', '_')}
   - Keep ALL section separators: # =========================================================================
   - Keep ALL method signatures (execute_check, _parse_input_files, _execute_type1/2/3/4)
   - Keep Helper Methods section IF it exists in skeleton (optional)
   - Keep Entry Point section: # =========================================================================
                          # Entry Point
                          # =========================================================================
                          def main() and if __name__ == '__main__'"""
        else:
            # Mode 2: GENERATE from scratch but MUST follow skeleton structure
            mode_instruction = f"""⚠️ CRITICAL: Generate code following EXACT skeleton structure!

NO SKELETON PROVIDED - Generate from scratch following standard template structure:

YOUR TASK - GENERATE WITH STANDARD SKELETON ARCHITECTURE:
1. ⭐ MUST include ALL skeleton sections with exact format:
   - File header comment block (################################################################################)
   - Standard imports and path setup
   - Class definition: class Check_{config['item_id'].replace('-', '_')}(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker)
   - Class docstring with template information
   - Constants section (# ========================================================================= with descriptions)
   - __init__ method with member variables
   - execute_check() method with type detection
   - _parse_input_files() method with complete implementation
   - Type 1/2/3/4 method stubs with TODO comments
   - Helper Methods section (optional, with TODO)
   - Entry Point section: # =========================================================================
                          # Entry Point
                          # =========================================================================
                          def main() and if __name__ == '__main__'
2. ⭐ ALL section separators MUST use: # =========================================================================
3. ⭐ ALL Type methods MUST have TODO comments as placeholders
4. ⭐ Follow EXACT format shown in skeleton template examples"""
        
        prompt = f"""MODIFY skeleton template - PHASE 1: Fill header + constants + _parse_input_files()

{mode_instruction}

2. ⭐ Phase 1 Responsibilities (whether modifying or generating):
   - {'Fill' if existing_skeleton else 'Write'} header "Logic:" section with specific parsing steps
   - {'UPDATE' if existing_skeleton else 'ADD'} CONSTANTS after class docstring, before __init__
   - {'Implement' if existing_skeleton else 'Write'} _parse_input_files() body with actual parsing
   - {'KEEP' if existing_skeleton else 'ADD'} Type 1/2/3/4 method stubs with TODO comments as placeholders
   - {'PRESERVE' if existing_skeleton else 'ADD'} Helper Methods section with TODO (optional)
   - {'PRESERVE' if existing_skeleton else 'ADD'} Entry Point section with main() and if __name__

3. Fill header "Logic:" section with specific parsing steps
4. ⭐ MANDATORY: {'UPDATE' if existing_skeleton else 'ADD'} CONSTANTS after class docstring, before __init__:
   Extract EXACT strings from README "Output Descriptions" section and define as class constants!
   
   ```python
   class Check_{config['item_id'].replace('-', '_')}(...):
       \"\"\"...\"\"\"
       
       # =========================================================================
       # DESCRIPTION CONSTANTS - Split by Type semantics
       # =========================================================================
       # ⚠️ COPY EXACT STRINGS from README Output Descriptions section!
       FOUND_DESC_TYPE1_4 = "<COPY from README: found_desc_type1_4>"
       MISSING_DESC_TYPE1_4 = "<COPY from README: missing_desc_type1_4>"
       FOUND_DESC_TYPE2_3 = "<COPY from README: found_desc_type2_3>"
       MISSING_DESC_TYPE2_3 = "<COPY from README: missing_desc_type2_3>"
       WAIVED_DESC = "<COPY from README: waived_desc>"
       
       # REASON CONSTANTS
       FOUND_REASON_TYPE1_4 = "<COPY from README: found_reason_type1_4>"
       MISSING_REASON_TYPE1_4 = "<COPY from README: missing_reason_type1_4>"
       FOUND_REASON_TYPE2_3 = "<COPY from README: found_reason_type2_3>"
       MISSING_REASON_TYPE2_3 = "<COPY from README: missing_reason_type2_3>"
       WAIVED_BASE_REASON = "<COPY from README: waived_base_reason>"
       UNUSED_WAIVER_REASON = "<COPY from README: unused_waiver_reason>"
       
       def __init__(self):
   ```
   
   ⚠️ CRITICAL: You MUST extract these values from the README Output Descriptions section provided above!
   Do NOT use placeholder text - use EXACT strings from README!
   
5. Add domain-specific constants if needed (e.g., LPE_INDICATORS, file patterns, thresholds)
6. Implement _parse_input_files() body with actual parsing
7. ⚠️ _parse_input_files MUST return: dict with 'items' list, 'metadata' dict, 'errors' list
8. Each item MUST have: 'name', 'line_number', 'file_path', optionally 'type'
9. ⭐ Phase 1 ONLY generates: Header + Imports + Class + Constants + __init__ + execute_check + _parse_input_files()
10. ⭐ {'PRESERVE' if existing_skeleton else 'ADD'} Type 1/2/3/4 methods with TODO placeholders
11. ⭐ {'PRESERVE' if existing_skeleton else 'ADD'} Helper Methods section with TODO (optional)
12. ⭐ {'PRESERVE' if existing_skeleton else 'ADD'} Entry Point section
13. Return COMPLETE {'modified skeleton' if existing_skeleton else 'generated code'} with Phase 1 filled + Type methods as TODO stubs"""
        
        prompt = f"""MODIFY skeleton template - PHASE 1: Fill header + constants + _parse_input_files()

{mode_instruction}

Item: {config['item_id']}
Description: {config['description']}
Module: {config['module']}

File Analysis:
{file_analysis}

README Specifications (CRITICAL - Follow these exactly!):
{readme[readme.find('**Key Patterns:**'):readme.find('## Output Descriptions')] if readme and '**Key Patterns:**' in readme else 'No patterns specified'}

README Output Descriptions (for understanding output format):
{readme[readme.find('## Output Descriptions'):readme.find('## Type 1:') if '## Type 1:' in readme else len(readme)] if readme and '## Output Descriptions' in readme else (readme[:2000] if readme else 'N/A - README not generated')}



⚠️ GENERATE ONLY:
1. File header comment (################################################################################)
2. Standard imports: from pathlib import Path, import sys, import re
3. ⚠️ MANDATORY path setup (EXACT format):
   ```python
   # Add common module to path
   _SCRIPT_DIR = Path(__file__).resolve().parent
   _CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
   _COMMON_DIR = _CHECK_MODULES_DIR / 'common'
   if str(_COMMON_DIR) not in sys.path:
       sys.path.insert(0, str(_COMMON_DIR))
   ```
4. Base imports:
   ```python
   from base_checker import BaseChecker, CheckResult, ConfigurationError
   from output_formatter import DetailItem, Severity, create_check_result
   ```
5. Template mixin imports (MANDATORY):
   ```python
   # MANDATORY: Import template mixins (checker_templates v1.1.0)
   from checker_templates.waiver_handler_template import WaiverHandlerMixin
   from checker_templates.output_builder_template import OutputBuilderMixin
   from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended
   ```
6. Class definition with proper mixin inheritance order
7. ⭐ CRITICAL: ADD constants block after class docstring (with 4-space indentation)
   Extract EXACT values from README Output Descriptions section above!
8. __init__ method with domain-specific member variables (4-space indentation)
9. execute_check() method (4-space indentation) - KEEP AS-IS from skeleton!
10. Complete _parse_input_files() method with real parsing logic based on file_analysis (4-space indentation)
11. ⭐ CRITICAL: PRESERVE ALL Type method sections from skeleton:
    ```python
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        \"\"\"...[keep skeleton docstring]...\"\"\"
        # TODO: [keep all TODO content from skeleton]
    
    # [Same for Type 2/3/4]
    ```
12. ⭐ OPTIONAL: If skeleton has Helper Methods section, preserve it:
    ```python
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    def _matches_waiver(self, item: str, waive_patterns: List[str]) -> bool:
        \"\"\"...[keep skeleton content]...\"\"\"
        # [Keep all implementation from skeleton]
    ```
    If skeleton doesn't have this section, DO NOT generate it!
13. ⭐ CRITICAL: PRESERVE Entry Point section from skeleton:
    ```python
    # =========================================================================
    # Entry Point
    # =========================================================================
    
    def main():
        \"\"\"Main entry point.\"\"\"
        checker = Check_XXX()
        checker.init_checker(Path(__file__))
        result = checker.execute_check()
        checker.write_output(result)
        return 0 if result.is_pass else 1
    
    if __name__ == '__main__':
        import sys
        sys.exit(main())
    ```

⚠️ CRITICAL CONSTANT EXTRACTION:
README "Output Descriptions" section above contains Python code block like:
```python
found_desc_type1_4 = "All loaded spice netlists are LPE-based with RC information"
missing_desc_type1_4 = "Non-LPE spice netlists found - RC information missing"
...
```
You MUST extract these EXACT strings and define as class constants:
```python
FOUND_DESC_TYPE1_4 = "All loaded spice netlists are LPE-based with RC information"
MISSING_DESC_TYPE1_4 = "Non-LPE spice netlists found - RC information missing"
```
Do NOT use generic/placeholder text - use EXACT strings from README Output Descriptions!

⚠️ CRITICAL DATA CONTRACT:
- _parse_input_files() MUST return: {{'items': [...], 'metadata': {{}}, 'errors': []}}
- Each item dict MUST have: {{'name': str, 'line_number': int, 'file_path': str, 'type': str (optional)}}
- Type methods will use: data = self._parse_input_files(); items = data.get('items', [])

⚠️ FORMAT REQUIREMENTS:
- ⭐ MANDATORY: _parse_input_files() MUST follow this COMPLETE architecture:
  ```python
  def _parse_input_files(self) -> Dict[str, Any]:
      \"\"\"
      Parse input files to extract [domain-specific] information.
      
      [Add docstring based on file_analysis]
      
      Returns:
          Dict with parsed data:
          - 'items': List[Dict] - [Description of items]
          - 'metadata': Dict - File metadata
          - 'errors': List - Parsing errors
      \"\"\"
      # 1. Validate input files (returns tuple: valid_files, missing_files)
      valid_files, missing_files = self.validate_input_files()
      
      # FIXED: Explicitly check for empty list
      if missing_files and len(missing_files) > 0:
          raise ConfigurationError(
              self.create_missing_files_error(missing_files)
          )
      
      # FIXED: Explicitly check for empty list
      if not valid_files or len(valid_files) == 0:
          raise ConfigurationError("No valid input files found")
      
      # 2. Initialize parsing structures
      items = []
      metadata = {{}}
      errors = []
      # Add domain-specific containers (e.g., library_versions = {{}})
      
      # 3. Parse each input file for [domain-specific] information
      for file_path in valid_files:
          try:
              with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                  for line_num, line in enumerate(f, 1):
                      # Your pattern matching logic based on file_analysis
                      # Example:
                      # match = re.search(r'YOUR_PATTERN', line)
                      # if match:
                      #     items.append({{
                      #         'name': match.group(1),
                      #         'line_number': line_num,
                      #         'file_path': str(file_path),
                      #         'type': 'category'
                      #     }})
          except Exception as e:
              errors.append(f"Error parsing {{file_path}}: {{str(e)}}")
      
      # 4. Store frequently reused data on self
      self._parsed_items = items
      # Store other domain-specific data (e.g., self._library_versions = library_versions)
      
      return {{
          'items': items,
          'metadata': metadata,
          'errors': errors
      }}
  ```
- ⚠️ CRITICAL: validate_input_files() gets files from input YAML config (NOT virtual files!)
- validate_input_files() returns TUPLE: (valid_files, missing_files)
- MUST keep ALL 4 architecture sections: # 1. Validate, # 2. Initialize, # 3. Parse, # 4. Store
- Follow inheritance order: InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker
- Keep section separators: # =========================================================================
- DO NOT modify the standard path setup format!

11. ⭐ {'KEEP' if existing_skeleton else 'ADD'} Type 1/2/3/4 method stubs with TODO placeholders:
    ```python
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        \"\"\"Type 1: Boolean Check.\"\"\"
        # TODO: Implement Type 1 logic
        pass
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        \"\"\"Type 2: Value Check.\"\"\"
        # TODO: Implement Type 2 logic
        pass
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        \"\"\"Type 3: Value Check with Waiver Logic.\"\"\"
        # TODO: Implement Type 3 logic
        pass
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        \"\"\"Type 4: Boolean Check with Waiver Logic.\"\"\"
        # TODO: Implement Type 4 logic
        pass
    ```

12. ⭐ {'KEEP' if existing_skeleton else 'ADD'} Helper Methods section (optional):
    ```python
    # =========================================================================
    # Helper Methods (Optional - Add as needed)
    # =========================================================================
    
    # TODO: Add helper methods if needed
    ```

13. ⭐ {'KEEP' if existing_skeleton else 'ADD'} Entry Point section:
    ```python
    # =========================================================================
    # Entry Point
    # =========================================================================
    
    def main():
        \"\"\"Main entry point.\"\"\"
        checker = Check_{config['item_id'].replace('-', '_')}()
        checker.init_checker(Path(__file__))
        result = checker.execute_check()
        checker.write_output(result)
        return 0 if result.is_pass else 1
    
    
    if __name__ == '__main__':
        import sys
        sys.exit(main())
    ```

Output ONLY raw Python code (no ```python markers):
"""
        
        llm_config = LLMCallConfig(temperature=0.2, max_tokens=16000)
        response = agent._llm_client.complete(prompt, config=llm_config)
        return self._extract_code_from_response(response.text)
    
    def _generate_phase2_type1_and_type4(
        self,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
        agent: Any,
        phase1_code: str,
    ) -> str:
        """
        Phase 2: Generate Type 1 & Type 4 methods.
        Type 4 reuses Type 1's core logic + adds waiver handling.
        
        Token budget: ~16K tokens.
        """
        from utils.models import LLMCallConfig
        
        # Get Type 1/4 specific hints
        try:
            from prompt_templates.api_v2_reference import get_type_specific_hints
        except ImportError:
            from AutoGenChecker.prompt_templates.api_v2_reference import get_type_specific_hints
        
        type1_hints = get_type_specific_hints(1)
        type4_hints = get_type_specific_hints(4)
        
        # Extract constants from Phase 1 to show AI what's available
        has_constants = 'FOUND_DESC_TYPE1_4' in phase1_code
        constants_hint = """⚠️ Use constants from Phase 1:
- Type 1/4: self.FOUND_DESC_TYPE1_4, self.FOUND_REASON_TYPE1_4, self.MISSING_DESC_TYPE1_4, self.MISSING_REASON_TYPE1_4
- Waiver (Type 4): self.WAIVED_DESC, self.WAIVED_BASE_REASON, self.UNUSED_WAIVER_REASON
""" if has_constants else """⚠️ No constants in Phase 1 - use item_desc directly."""
        
        prompt = f"""GENERATE PHASE 2 ONLY: Type 1 & Type 4 method implementations

⚠️ CRITICAL ARCHITECTURE: Type 4 REUSES Type 1 core logic!

Item: {config['item_id']}

🚨🚨🚨 CRITICAL OUTPUT FORMAT REQUIREMENTS 🚨🚨🚨

1. OUTPUT ONLY _execute_type1() and _execute_type4() methods
2. Type 4 implementation MUST:
   - Extract Type 1's core boolean logic into a helper method _type1_core_logic()
   - Call _type1_core_logic() to get violations
   - Then apply waiver matching logic to split violations into waived_items and missing_items
3. DO NOT include:
   - Class definition (class CheckerName...)
   - __init__ method
   - _parse_input_files() method (already in Phase 1)
   - Constants definitions (already in Phase 1)
   - Imports (already in Phase 1)
   - Type 2/3 methods (will be in Phase 3)
   - main() function (skeleton already has it)
   - Any code from Phase 1

4. START directly with the method definition:
   ```python
   # =========================================================================
   # Type 1: Boolean Check
   # =========================================================================
   
   def _execute_type1(self) -> CheckResult:
       ...
   ```

5. Methods MUST have 4-space indentation (class-level methods)

🚨🚨🚨 TYPE 4 IMPLEMENTATION PATTERN 🚨🚨🚨

⚠️ MANDATORY: Type 4 must follow this exact pattern:

```python
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        \"\"\"Type 1: Boolean check without waiver support.\"\"\"
        # Core boolean logic
        violations = self._type1_core_logic()

        # found_items and missing_items semantics (same as Type 2/3):
        # - found_items: objects that PASS the check (compliant objects)
        # - missing_items: objects that FAIL the check (violations / non-compliant objects)
        #
        # Implementation guide:
        # 1. Parse input files to get all relevant objects
        # 2. Classify them: passing objects → found_items, failing objects → missing_items
        # 3. Both should include metadata (line_number, file_path) for traceability
        #
        # IMPORTANT: Handle "nothing found" scenario:
        # If parsing returns NO objects (items=[]), this typically means FAIL:
        # - found_items = {{}} (no compliant objects found)
        # - missing_items = {{'expected_item': {{'line_number': 0, 'file_path': 'N/A', 'reason': '...'}}}} 
        #   Use a descriptive key like 'required_evidence' or 'expected_configuration'
        #
        # Example patterns:
        # - LPE check: found_items=LPE files, missing_items=non-LPE files
        # - Config check: found_items=correct configs, missing_items=incorrect configs
        # - Constraint check: found_items=met constraints, missing_items=violated constraints
        found_items = <PASSING_OBJECTS_DICT>  # Dict[str, Dict] with line_number/file_path
        
        # Convert to missing_items for output
        missing_items = list(violations.keys()) if violations else []
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    def _type1_core_logic(self) -> dict[str, dict]:
        \"\"\"
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).
        
        Returns:
            Dict of violations: {{item_name: {{'line_number': ..., 'file_path': ..., 'reason': ...}}}}
            Empty dict if all checks pass.
        \"\"\"
        data = self._parse_input_files()
        items = data.get('items', [])
        
        violations = {{}}
        
        # Your boolean check logic here
        # Example: check for unwanted items
        for item in items:
            if <condition_that_should_fail>:
                violations[item['name']] = {{
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A'),
                    'reason': '<why this is a violation>'
                }}
        
        return violations
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        \"\"\"Type 4: Boolean check with waiver support (reuses Type 1 core logic).\"\"\"
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # found_items: objects that PASS the check (same semantics as Type 1)
        found_items = <PASSING_OBJECTS_DICT>  # Dict[str, Dict] with line_number/file_path
        
        # Step 2: Parse waiver configuration
        waive_dict = self.parse_waive_items()
        
        # Step 3: Split violations into waived and unwaived
        waived_items = {{}}
        missing_items = {{}}
        used_waivers = set()
        
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()),
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
```

⚠️ KEY ARCHITECTURAL POINTS:
1. _type1_core_logic() contains the shared boolean check logic
2. _execute_type1() calls _type1_core_logic() and formats output without waivers
3. _execute_type4() calls _type1_core_logic() and adds waiver processing
4. This eliminates code duplication between Type 1 and Type 4

🚨🚨🚨 ABSOLUTE REQUIREMENT - BUILD_COMPLETE_OUTPUT PARAMETERS 🚨🚨🚨

ALL build_complete_output() calls MUST use ONLY class constants:
❌ FORBIDDEN: found_desc=f"{{self.CONSTANT}} ({{count}} items)"
❌ FORBIDDEN: missing_reason=lambda item: ...

✅ REQUIRED FORMAT:
    return self.build_complete_output(
        found_items=...,
        missing_items=...,
        found_desc=self.FOUND_DESC_TYPE1_4,      # Pure constant ONLY!
        missing_desc=self.MISSING_DESC_TYPE1_4,  # Pure constant ONLY!
        found_reason=self.FOUND_REASON_TYPE1_4,  # Pure constant ONLY!
        missing_reason=self.MISSING_REASON_TYPE1_4  # Pure constant ONLY!
    )

⚠️ CONTEXT FROM PHASE 1 (constants and data structure available):
```python
{phase1_code[:3000]}
```

{constants_hint}

⚠️ DATA STRUCTURE from _parse_input_files():
data = self._parse_input_files()
items = data.get('items', [])  # ALWAYS use 'items'
metadata = data.get('metadata', {{}})
errors = data.get('errors', [])

README Type 1 Configuration:
{readme[readme.find('## Type 1:'):readme.find('## Type 2:') if '## Type 2:' in readme else len(readme)] if '## Type 1:' in readme else 'Type 1 not found'}

README Type 4 Configuration:
{readme[readme.find('## Type 4:'):readme.find('## Testing') if '## Testing' in readme else len(readme)] if '## Type 4:' in readme else 'Type 4 not found'}

Type 1 Hints:
{type1_hints}

Type 4 Hints:
{type4_hints}

⚠️ OUTPUT REQUIREMENTS:
1. Generate THREE methods: _execute_type1(), _type1_core_logic(), _execute_type4()
2. All methods MUST have 4-space indentation (class-level methods)
3. Use proper section separator: # =========================================================================
4. Include docstrings explaining the logic and code reuse
5. Use build_complete_output() with constants ONLY (no f-strings!)
6. Include line_number and file_path in all item dicts
7. DO NOT include any code from Phase 1
8. DO NOT generate Type 2/3 methods (those are Phase 3)
9. DO NOT generate Helper Methods section - skeleton already has it!
10. DO NOT generate Entry Point (main/__name__) - skeleton already has it!

Expected output format (with proper 4-space indentation):
```python
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        \"\"\"Type 1 implementation...\"\"\"
        violations = self._type1_core_logic()
        # ... format and return
    
    def _type1_core_logic(self) -> dict[str, dict]:
        \"\"\"Core Type 1 logic shared by Type 1 and Type 4.\"\"\"
        # ... actual boolean check logic
        return violations
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        \"\"\"Type 4 implementation (reuses Type 1 core logic)...\"\"\"
        violations = self._type1_core_logic()  # Reuse Type 1 logic
        # ... add waiver processing
        return self.build_complete_output(...)
```

⚠️ CRITICAL: Output these three methods with proper code reuse architecture!

🚨🚨🚨 FORCED OUTPUT TEMPLATE - COPY THIS EXACT STRUCTURE 🚨🚨🚨

YOU MUST generate build_complete_output() calls in THIS EXACT FORMAT (replace <...> with actual code):

Type 1:
```python
    def _execute_type1(self) -> CheckResult:
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        # Build dict from your clean/passing objects:
        found_items = {{}}
        for item in <YOUR_CLEAN_OBJECTS_LIST>:
            found_items[item['name']] = {{
                'name': item['name'],
                'line_number': item['line_number'],
                'file_path': item['file_path']
            }}
        
        missing_items = list(violations.keys()) if violations else []
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
```

Type 4:
```python
    def _execute_type4(self) -> CheckResult:
        violations = self._type1_core_logic()
        
        # ⚠️ CRITICAL: found_items MUST be dict[str, dict], NOT list!
        found_items = {{}}
        for item in <YOUR_CLEAN_OBJECTS_LIST>:
            found_items[item['name']] = {{
                'name': item['name'],
                'line_number': item['line_number'],
                'file_path': item['file_path']
            }}
        
        waive_dict = self.parse_waive_items()
        waived_items = {{}}
        missing_items = {{}}
        used_waivers = set()
        
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()),
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
```

⚠️ DO NOT SKIP ANY PARAMETERS! COPY THE EXACT FORMAT ABOVE!
"""
        
        llm_config = LLMCallConfig(temperature=0.2, max_tokens=16000)
        response = agent._llm_client.complete(prompt, config=llm_config)
        return self._extract_code_from_response(response.text)
    
    def _generate_phase3_type2_and_type3(
        self,
        config: dict[str, Any],
        file_analysis: dict[str, Any],
        readme: str,
        agent: Any,
        phase1_code: str,
    ) -> str:
        """
        Phase 3: Generate Type 2 & Type 3 methods.
        Type 3 reuses Type 2's core logic + adds waiver handling.
        
        Token budget: ~16K tokens.
        """
        from utils.models import LLMCallConfig
        
        # Get Type 2/3 specific hints
        try:
            from prompt_templates.api_v2_reference import get_type_specific_hints
        except ImportError:
            from AutoGenChecker.prompt_templates.api_v2_reference import get_type_specific_hints
        
        type2_hints = get_type_specific_hints(2)
        type3_hints = get_type_specific_hints(3)
        
        # Extract constants info from Phase 1
        has_constants = 'FOUND_DESC_TYPE2_3' in phase1_code
        constants_hint = """⚠️ Use constants from Phase 1:
- Type 2/3: self.FOUND_DESC_TYPE2_3, self.FOUND_REASON_TYPE2_3, self.MISSING_DESC_TYPE2_3, self.MISSING_REASON_TYPE2_3
- Waiver (Type 3): self.WAIVED_DESC, self.WAIVED_BASE_REASON, self.UNUSED_WAIVER_REASON
""" if has_constants else """⚠️ No constants - build descriptions inline."""
        
        prompt = f"""GENERATE PHASE 3 ONLY: Type 2 & Type 3 method implementations

⚠️ CRITICAL ARCHITECTURE: Type 3 REUSES Type 2 core logic!

Item: {config['item_id']}

🚨🚨🚨 CRITICAL OUTPUT FORMAT REQUIREMENTS 🚨🚨🚨

1. OUTPUT ONLY _execute_type2() and _execute_type3() methods
2. Type 3 implementation MUST:
   - Extract Type 2's core pattern matching logic into a helper method _type2_core_logic()
   - Call _type2_core_logic() to get found/missing items
   - Then apply waiver matching logic to split missing items into waived_items and actual missing_items
3. DO NOT include:
   - Class definition (class CheckerName...)
   - __init__ method
   - _parse_input_files() method (already in Phase 1)
   - Constants definitions (already in Phase 1)
   - Imports (already in Phase 1)
   - Type 1/4 methods (already in Phase 2)
   - main() function (skeleton already has it)
   - Any code from Phase 1 or Phase 2

4. START directly with the method definition:
   ```python
   # =========================================================================
   # Type 2: Value Check
   # =========================================================================
   
   def _execute_type2(self) -> CheckResult:
       ...
   ```

5. Methods MUST have 4-space indentation (class-level methods)

🚨🚨🚨 TYPE 3 IMPLEMENTATION PATTERN 🚨🚨🚨

⚠️ MANDATORY: Type 3 must follow this exact pattern:

```python
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        \"\"\"Type 2: Pattern/value check without waiver support.\"\"\"
        # Core pattern matching logic
        found_items, missing_items = self._type2_core_logic()
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()) if isinstance(missing_items, dict) else missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        \"\"\"
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).
        
        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {{item_name: {{'line_number': ..., 'file_path': ...}}}}
            - missing_items: {{item_name: {{'line_number': ..., 'file_path': ..., 'reason': ...}}}}
        \"\"\"
        data = self._parse_input_files()
        items = data.get('items', [])
        
        requirements = self.item_data.get('requirements', {{}})
        pattern_items = requirements.get('pattern_items', [])
        
        found_items = {{}}
        missing_items = {{}}
        
        # Your pattern matching logic here
        # Example for existence_check:
        for pattern in pattern_items:
            matched = False
            for item in items:
                if pattern.lower() in item['name'].lower():
                    found_items[item['name']] = {{
                        'line_number': item.get('line_number', 0),
                        'file_path': item.get('file_path', 'N/A')
                    }}
                    matched = True
                    break
            
            if not matched:
                missing_items[pattern] = {{
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Pattern "{{pattern}}" not found'
                }}
        
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        \"\"\"Type 3: Pattern/value check with waiver support (reuses Type 2 core logic).\"\"\"
        # Step 1: Get found/missing items using Type 2's core logic
        found_items, violations = self._type2_core_logic()
        
        # Step 2: Parse waiver configuration
        waive_dict = self.parse_waive_items()
        
        # Step 3: Split violations into waived and unwaived
        waived_items = {{}}
        missing_items = {{}}
        used_waivers = set()
        
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()),
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
```

⚠️ KEY ARCHITECTURAL POINTS:
1. _type2_core_logic() contains the shared pattern matching logic
2. _execute_type2() calls _type2_core_logic() and formats output without waivers
3. _execute_type3() calls _type2_core_logic() and adds waiver processing
4. This eliminates code duplication between Type 2 and Type 3

🚨🚨🚨 ABSOLUTE REQUIREMENT - BUILD_COMPLETE_OUTPUT PARAMETERS 🚨🚨🚨

ALL build_complete_output() calls MUST use ONLY class constants:
❌ FORBIDDEN: found_reason=lambda item: f"..."
❌ FORBIDDEN: found_desc=f"{{self.CONSTANT}} (extra)"
❌ FORBIDDEN: missing_reason=lambda item: ...

✅ REQUIRED FORMAT:
    return self.build_complete_output(
        found_items=...,
        missing_items=...,
        found_desc=self.FOUND_DESC_TYPE2_3,      # Pure constant!
        missing_desc=self.MISSING_DESC_TYPE2_3,  # Pure constant!
        found_reason=self.FOUND_REASON_TYPE2_3,  # Pure constant!
        missing_reason=self.MISSING_REASON_TYPE2_3  # Pure constant!
    )

⚠️ CONTEXT FROM PHASE 1 (constants and data structure available):
```python
{phase1_code[:3000]}
```

{constants_hint}

⚠️ DATA STRUCTURE from _parse_input_files():
data = self._parse_input_files()
items = data.get('items', [])  # ALWAYS 'items'

README Type 2 Configuration:
{readme[readme.find('## Type 2:'):readme.find('## Type 3:') if '## Type 3:' in readme else len(readme)] if '## Type 2:' in readme else 'Type 2 not found'}

README Type 3 Configuration:
{readme[readme.find('## Type 3:'):readme.find('## Type 4:') if '## Type 4:' in readme else len(readme)] if '## Type 3:' in readme else 'Type 3 not found'}

Type 2 Hints:
{type2_hints}

Type 3 Hints:
{type3_hints}

⚠️ CRITICAL TYPE 2 LOGIC - Output ACTUAL items, not pattern names:
- For existence_check: found_items = actual files/entities that matched patterns
- For status_check: found_items = items that matched AND have correct status
- missing_items = patterns not found (existence) OR items with wrong status (status_check)

🚨 CRITICAL: NO LAMBDA FUNCTIONS OR F-STRINGS IN build_complete_output()!
❌ WRONG: found_reason=lambda item: f"Found {{item['name']}}"
❌ WRONG: found_desc=f"Found {{len(items)}} items"
✅ CORRECT: found_reason=self.FOUND_REASON_TYPE2_3
✅ CORRECT: found_desc=self.FOUND_DESC_TYPE2_3

⚠️ OUTPUT REQUIREMENTS:
1. Generate THREE methods: _execute_type2(), _type2_core_logic(), _execute_type3()
2. All methods MUST have 4-space indentation (class-level methods)
3. Use proper section separator: # =========================================================================
4. Include docstrings explaining waiver logic and code reuse
5. Use build_complete_output() with constants ONLY (no f-strings, no lambdas!)
6. Include line_number and file_path in all item dicts
7. DO NOT include any code from Phase 1 or Phase 2
8. DO NOT generate Helper Methods section - skeleton already has it!
9. DO NOT generate Entry Point (main/__name__) - skeleton already has it!

Expected output format (with proper 4-space indentation):
```python
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        \"\"\"Type 2 implementation...\"\"\"
        found_items, missing_items = self._type2_core_logic()
        # ... format and return
    
    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        \"\"\"Core Type 2 logic shared by Type 2 and Type 3.\"\"\"
        # ... actual pattern matching logic
        return found_items, missing_items
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        \"\"\"Type 3 implementation (reuses Type 2 core logic)...\"\"\"
        found_items, violations = self._type2_core_logic()  # Reuse Type 2 logic
        # ... add waiver processing
        return self.build_complete_output(...)
```

⚠️ CRITICAL: Output these three methods with proper code reuse architecture!

🚨🚨🚨 FORCED OUTPUT TEMPLATE - COPY THIS EXACT STRUCTURE 🚨🚨🚨

YOU MUST generate build_complete_output() calls in THIS EXACT FORMAT (replace <...> with actual code):

Type 2:
```python
    def _execute_type2(self) -> CheckResult:
        found_items, missing_items = self._type2_core_logic()
        
        # ⚠️ _type2_core_logic() returns dict[str, dict] for both found_items and missing_items
        # Convert missing_items dict to list of keys for build_complete_output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()) if isinstance(missing_items, dict) else missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
```

Type 3:
```python
    def _execute_type3(self) -> CheckResult:
        found_items_base, violations = self._type2_core_logic()
        waive_dict = self.parse_waive_items()
        
        found_items = {{}}
        waived_items = {{}}
        missing_items = {{}}
        used_waivers = set()
        
        # Process found_items_base (no waiver needed)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data
        
        # Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data
        
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()) if isinstance(missing_items, dict) else missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
```

⚠️ DO NOT SKIP ANY PARAMETERS! COPY THE EXACT FORMAT ABOVE!
"""
        
        llm_config = LLMCallConfig(temperature=0.2, max_tokens=16000)
        response = agent._llm_client.complete(prompt, config=llm_config)
        return self._extract_code_from_response(response.text)
    
    def _generate_phase4(
        self,
        config: dict[str, Any],
        agent: Any,
    ) -> str:
        """
        Phase 4: Generate main() entry point (standard boilerplate).
        
        NOTE: Skeleton already has main() and Entry Point!
        This phase is kept for compatibility but skeleton should preserve it.
        
        Token budget: ~4K tokens (simple).
        """
        from utils.models import LLMCallConfig
        
        prompt = f"""Generate PHASE 4: main() entry point (standard boilerplate)

⚠️ IMPORTANT: Skeleton already has Entry Point section!
Output ONLY if skeleton is missing main() - otherwise output empty string.

Item: {config['item_id']}

⚠️ CRITICAL FORMAT - Use EXACT separator:
```python
# =========================================================================
# Entry Point
# =========================================================================

def main():
    \"\"\"Main entry point.\"\"\"
    checker = Check_{config['item_id'].replace('-', '_')}()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
```

⚠️ DO NOT use alternative formats like # --- or # === Entry Point ===

Output ONLY the code above:
"""
        
        llm_config = LLMCallConfig(temperature=0.2, max_tokens=4000)
        response = agent._llm_client.complete(prompt, config=llm_config)
        return self._extract_code_from_response(response.text)
    
    def _combine_phases(
        self,
        phase1: str,
        phase2: str,
        phase3: str,
    ) -> str:
        """
        Intelligently combine all 3 phases into complete checker code.
        
        Phase 1: Header + Imports + Class + Constants + _parse_input_files()
        Phase 2: Type 1 + _type1_core_logic() + Type 4 (reuses Type 1 logic)
        Phase 3: Type 2 + _type2_core_logic() + Type 3 (reuses Type 2 logic)
        
        Handles:
        - Validating Phase 1 has constants (auto-insert if missing)
        - Removing skeleton's TODO Type methods
        - Inserting Phase2/3 actual implementations
        - Proper indentation for methods  
        - Ensuring format separator consistency
        - Clean section transitions
        """
        # Step 1: Validate and fix Phase 1 (constants, format)
        phase1 = self._validate_and_fix_phase1(phase1)
        
        # Step 2: Remove skeleton's Type 1-4 TODO methods from Phase 1
        phase1 = self._remove_skeleton_type_methods(phase1)
        
        # Step 3: Find where to insert Type methods (after _parse_input_files)
        lines = phase1.split('\n')
        
        # Find the end of _parse_input_files method (look for next method definition at class level)
        insert_index = -1
        in_parse_method = False
        method_indent = 4  # Standard method indentation in class
        parse_method_start = -1
        
        for i, line in enumerate(lines):
            # Found start of _parse_input_files
            if 'def _parse_input_files(' in line:
                in_parse_method = True
                parse_method_start = i
                continue
            
            # Look for next class-level definition (same indentation as def _parse_input_files)
            if in_parse_method:
                # Skip empty lines and comments
                if not line.strip() or line.strip().startswith('#'):
                    continue
                    
                # Check if this line is a new method definition at class level (4 spaces)
                stripped = line.lstrip()
                current_indent = len(line) - len(stripped)
                
                # Found next class-level element (method, property, or class variable)
                if current_indent == method_indent and (stripped.startswith('def ') or 
                                                        stripped.startswith('@') or
                                                        stripped.startswith('# =====')):
                    insert_index = i
                    break
                # Or found end of class (indent < 4)
                elif current_indent < method_indent and stripped:
                    insert_index = i
                    break
        
        # Fallback: if still not found, insert before main() or helper methods
        if insert_index == -1:
            for i, line in enumerate(lines):
                if ('def main(' in line or 
                    '# Entry Point' in line or
                    'def _matches_waiver' in line or
                    'def _is_lpe_based' in line):
                    insert_index = i
                    break
            if insert_index == -1:
                # Ultimate fallback: use after parse method start + reasonable offset
                if parse_method_start > 0:
                    insert_index = parse_method_start + 50
                else:
                    insert_index = len(lines) - 10
        
        # Step 3: Ensure Phase 2/3 have proper separators and strip any leading/trailing blank lines
        # Phase 2 contains Type 1 and Type 4
        # Phase 3 contains Type 2 and Type 3
        phase2 = self._ensure_method_separators(phase2, [1, 4]).strip()
        phase3 = self._ensure_method_separators(phase3, [2, 3]).strip()
        
        # Step 4: Strip any class definition or imports from Phase 2/3 (LLM might include them)
        phase2 = self._strip_unwanted_code(phase2)
        phase3 = self._strip_unwanted_code(phase3)
        
        # Step 4.5: Normalize indentation for Phase 2/3 (ensure 4-space indent for methods)
        phase2 = self._normalize_method_indentation(phase2)
        phase3 = self._normalize_method_indentation(phase3)
        
        # Step 5: Insert Phase 2 (Type 1/2) - DO NOT add extra indentation!
        # Phase 2/3 already have correct indentation from generation
        # Add blank line before for readability
        lines.insert(insert_index, '')
        insert_index += 1
        
        phase2_lines = phase2.split('\n')
        for line in reversed(phase2_lines):
            lines.insert(insert_index, line)
        
        # Update insert position for Phase 3
        insert_index += len(phase2_lines)
        
        # Step 6: Add blank line between Phase 2 and Phase 3
        lines.insert(insert_index, '')
        insert_index += 1
        
        # Step 7: Insert Phase 3 (Type 2/3) - DO NOT add extra indentation!
        phase3_lines = phase3.split('\n')
        for line in reversed(phase3_lines):
            lines.insert(insert_index, line)
        
        # Step 8: Combine all lines
        combined = '\n'.join(lines)
        
        # Step 9: Clean up orphaned Helper Methods section comments
        # (may appear after _parse_input_files if skeleton had them)
        combined = self._cleanup_orphaned_comments(combined)
        
        # Note: main() and Entry Point are already in skeleton (Phase 1)
        # No need to append Phase 4 since skeleton preserves it
        
        return combined
    
    def _cleanup_orphaned_comments(self, code: str) -> str:
        """
        Remove orphaned section comments that appear in wrong places.
        
        Specifically handles:
        - Empty section separators without content
        - PRESERVES "Helper Methods" section - we want to keep it!
        
        NOTE: The "Helper Methods" section should be PRESERVED after Type methods.
        This method only removes truly orphaned comments (empty separators with no content).
        """
        lines = code.split('\n')
        cleaned_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # NEVER delete Helper Methods section - it should be preserved!
            # Only skip truly orphaned empty separators (no section name)
            if stripped.startswith('# ===') and 'Helper Methods' not in stripped:
                # Check if this is an empty separator (no meaningful content follows)
                lookahead = i + 1
                while lookahead < len(lines) and not lines[lookahead].strip():
                    lookahead += 1
                
                # If next non-empty line is another separator or def, this might be orphaned
                if lookahead < len(lines):
                    next_line = lines[lookahead].strip()
                    # Skip only if this is an empty separator followed by Type method
                    # (not a section header like "# Type 1" but the actual separator "# ====")
                    if (stripped == '# =========================================================================' and
                        (next_line.startswith('def _execute_type') or 
                         next_line.startswith('# ==='))):
                        # This is just a bare separator line before a method, skip it
                        i += 1
                        continue
            
            cleaned_lines.append(line)
            i += 1
        
        return '\n'.join(cleaned_lines)
    
    def _remove_skeleton_type_methods(self, phase1: str) -> str:
        """
        Remove ALL Type 1-4 methods and related code blocks from Phase 1.
        
        This removes:
        - All _execute_type1/2/3/4 methods
        - All _type1_core_logic and _type2_core_logic helper methods
        - Section separators (# =========...) for Type 1/2/3/4
        
        Phase 2/3 will regenerate these with proper implementations.
        
        Args:
            phase1: Code from Phase 1 (with skeleton Type methods)
            
        Returns:
            Phase 1 code with Type methods removed
        """
        lines = phase1.split('\n')
        filtered_lines = []
        in_type_block = False
        type_block_indent = -1
        
        # Also track Type section separators to remove
        type_section_keywords = ['Type 1:', 'Type 2:', 'Type 3:', 'Type 4:', 
                                  'Boolean Check', 'Value Check', 'Waiver Logic']
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            
            # Check if this is a Type-related method definition
            # Match: _execute_type1/2/3/4, _type1_core_logic, _type2_core_logic
            is_type_method = (
                stripped.startswith('def _execute_type') and any(
                    f'_execute_type{n}' in line for n in [1, 2, 3, 4]
                )
            ) or (
                stripped.startswith('def _type') and any(
                    f'_type{n}_core_logic' in line for n in [1, 2]
                )
            )
            
            if is_type_method:
                in_type_block = True
                type_block_indent = current_indent
                # Look back to remove "# =========..." Type section separators
                while filtered_lines:
                    last_line = filtered_lines[-1]
                    last_stripped = last_line.strip()
                    # Remove section separators and Type comments
                    if (not last_stripped or 
                        last_stripped.startswith('# ===') or
                        any(kw in last_line for kw in type_section_keywords)):
                        filtered_lines.pop()
                    else:
                        break
                i += 1
                continue
            
            # If we're in a Type method block, skip until we find:
            # - A new def at same or lesser indent (but not another Type method)
            # - Entry Point section
            # - main() function
            if in_type_block:
                # Check if we should exit the skip mode
                should_exit = False
                
                # Exit conditions:
                # 1. Non-Type method definition at class level
                if stripped.startswith('def ') and current_indent <= type_block_indent:
                    # But NOT if it's another Type method or helper
                    if not ('_execute_type' in line or '_type1_core_logic' in line or '_type2_core_logic' in line):
                        should_exit = True
                
                # 2. Entry Point section (keep this!)
                if 'Entry Point' in line:
                    should_exit = True
                
                # 3. main() function
                if 'def main(' in line:
                    should_exit = True
                
                # 4. Helper Methods section (keep this!)
                if 'Helper Methods' in line:
                    should_exit = True
                
                if should_exit:
                    in_type_block = False
                    type_block_indent = -1
                    # Process this line normally (don't skip)
                else:
                    # Skip this line (part of Type block)
                    i += 1
                    continue
            
            # Not in Type block, keep this line
            # But also check for standalone Type section separators
            is_type_separator = (
                stripped.startswith('# ===') and 
                any(kw in line for kw in type_section_keywords)
            )
            
            if not is_type_separator:
                filtered_lines.append(line)
            
            i += 1
        
        return '\n'.join(filtered_lines)
    
    def _validate_and_fix_phase1(self, phase1: str) -> str:
        """
        Validate Phase 1 and auto-fix issues:
        1. Check if constants are defined
        2. Insert fallback constants if missing
        3. Validate format separators
        """
        # Check if constants exist
        has_constants = 'FOUND_DESC_TYPE1_4' in phase1 or 'FOUND_REASON_TYPE1_4' in phase1
        
        if not has_constants:
            if hasattr(self, 'verbose') and self.verbose:
                print("    ⚠️  Phase 1 missing constants, inserting fallback...")
            
            # Find where to insert (after class docstring, before __init__)
            insert_pos = phase1.find('def __init__')
            if insert_pos > 0:
                constants_block = '''    # =========================================================================
    # DESCRIPTION CONSTANTS - Fallback (Phase 1 missed)
    # =========================================================================
    FOUND_DESC_TYPE1_4 = "Required items found and validated"
    MISSING_DESC_TYPE1_4 = "Required items not found or invalid"
    FOUND_DESC_TYPE2_3 = "Pattern requirements satisfied"
    MISSING_DESC_TYPE2_3 = "Pattern requirements not satisfied"
    WAIVED_DESC = "Items waived per configuration"
    
    # REASON CONSTANTS
    FOUND_REASON_TYPE1_4 = "Items found in expected locations"
    MISSING_REASON_TYPE1_4 = "Items not found in expected locations"
    FOUND_REASON_TYPE2_3 = "Pattern matched successfully"
    MISSING_REASON_TYPE2_3 = "Pattern not matched"
    WAIVED_BASE_REASON = "Waived per project configuration"
    UNUSED_WAIVER_REASON = "Waiver defined but not used"
    
'''
                phase1 = phase1[:insert_pos] + constants_block + phase1[insert_pos:]
        
        return phase1
    
    def _strip_unwanted_code(self, code: str) -> str:
        """
        Remove unwanted code that LLM might accidentally include in Phase 2/3.
        
        Removes:
        - Class definitions
        - Import statements  
        - Constants definitions
        - __init__ methods
        - _parse_input_files methods
        """
        lines = code.split('\n')
        filtered_lines = []
        skip_until_next_method = False
        
        for line in lines:
            # Skip class definitions
            if line.strip().startswith('class '):
                skip_until_next_method = True
                continue
            
            # Skip imports
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                continue
            
            # Skip constants (UPPERCASE = ...)
            if line.strip() and '=' in line:
                var_name = line.split('=')[0].strip()
                if var_name.isupper() and not line.strip().startswith('def '):
                    continue
            
            # Skip __init__ method
            if 'def __init__' in line:
                skip_until_next_method = True
                continue
            
            # Skip _parse_input_files method
            if 'def _parse_input_files' in line:
                skip_until_next_method = True
                continue
            
            # Found next method - stop skipping
            if skip_until_next_method and line.strip().startswith('def _execute_type'):
                skip_until_next_method = False
            
            # Add line if not skipping
            if not skip_until_next_method:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _normalize_method_indentation(self, code: str) -> str:
        """
        Normalize indentation for Phase 2/3 code to ensure proper class-level method formatting.
        
        Rules:
        - Method definitions (def _execute_type*, def _type*_core_logic) should have 4-space indent
        - Method body should have 8-space indent
        - Section separators (# ===) should have 4-space indent
        - Handles LLM output that may have inconsistent or no indentation
        """
        lines = code.split('\n')
        normalized_lines = []
        in_method = False
        method_indent = 4  # Class-level method indent
        body_indent = 8    # Method body indent
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines - preserve them
            if not stripped:
                normalized_lines.append('')
                continue
            
            # Section separators should have 4-space indent
            if stripped.startswith('# ===') or (stripped.startswith('# Type') and ':' in stripped):
                normalized_lines.append(' ' * method_indent + stripped)
                continue
            
            # Method definitions should have 4-space indent
            if stripped.startswith('def '):
                in_method = True
                normalized_lines.append(' ' * method_indent + stripped)
                continue
            
            # Decorators should have 4-space indent
            if stripped.startswith('@'):
                normalized_lines.append(' ' * method_indent + stripped)
                continue
            
            # Method body (when in method) should have 8+ space indent
            if in_method:
                # Docstrings and code inside methods
                current_indent = len(line) - len(line.lstrip())
                
                # If line has less than body indent, it might be a continuation or needs adjustment
                if current_indent < body_indent and stripped:
                    # Check if it's a return statement or other top-level method code
                    if stripped.startswith(('return ', 'raise ', 'if ', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ', 'elif ', 'else:')):
                        normalized_lines.append(' ' * body_indent + stripped)
                    elif stripped.startswith('"""') or stripped.startswith("'''"):
                        # Docstring
                        normalized_lines.append(' ' * body_indent + stripped)
                    else:
                        # Preserve relative indentation for nested code
                        extra_indent = max(0, current_indent - 4)  # Assume original was 4-based
                        normalized_lines.append(' ' * (body_indent + extra_indent) + stripped)
                else:
                    # Line already has sufficient indentation, adjust relative to body_indent
                    relative_indent = current_indent - 8 if current_indent >= 8 else 0
                    normalized_lines.append(' ' * (body_indent + relative_indent) + stripped)
            else:
                # Not in a method, preserve as-is with minimum 4-space indent for comments
                if stripped.startswith('#'):
                    normalized_lines.append(' ' * method_indent + stripped)
                else:
                    normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)
    
    def _ensure_method_separators(self, code: str, type_nums: list[int]) -> str:
        """
        Ensure method separators are in correct format with proper indentation.
        Fixes: # --- Type 1 --- → properly indented # =========================================================================
        """
        import re
        
        for type_num in type_nums:
            # Check if separator exists and is correct
            if f'def _execute_type{type_num}' in code:
                # Find and fix separator before this method
                # Match various separator formats (with or without indentation)
                pattern = rf'(\s*# [=-]+\s*Type {type_num}[^\n]*\n)'
                type_desc = 'Boolean Check' if type_num in [1, 4] else 'Value Check'
                waiver_suffix = ' with Waiver Logic' if type_num in [3, 4] else ''
                # All lines must have 4-space indent for class-level methods
                replacement = f'''    # =========================================================================
    # Type {type_num}: {type_desc}{waiver_suffix}
    # =========================================================================
'''
                code = re.sub(pattern, replacement, code, flags=re.IGNORECASE)
        
        return code

