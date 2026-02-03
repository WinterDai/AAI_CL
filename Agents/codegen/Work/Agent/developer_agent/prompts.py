"""
Developer Agent - Prompt Templates
Based on Agent_Development_Spec.md v1.1 Section 4
Updated to match item_spec_prompt.txt and Agent_Vibe_Coding_guide_patch.txt

Defines system prompts for Agent A, Agent B, and Reflect nodes.
"""
import json
from typing import Dict, Any


# =============================================================================
# Agent A System Prompt (Parsing Expert)
# Based on: Agent_Development_Spec.md v1.2
# Input: ItemSpec Section 1 (Parsing Logic) + Section 4.1 (Data Source & Extraction)
# =============================================================================

AGENT_A_PROMPT_TEMPLATE = '''# Role
You are the **Parsing Expert Agent** for "Hierarchical Checker Architecture 10.2".
Your task is to write the `extract_context` Python function (Atom A).

# Hard Constraints for Generated Code (NON-NEGOTIABLE)

1. **Atom A Signature**: `def extract_context(text: str, source_file: str) -> List[Dict]`
2. **Type Lock**: You MUST cast extracted values to string: `val = str(item.get('val'))`
3. **Output Schema**: Return list of dicts with keys: `value`, `source_file`, `line_number`, `matched_content`, `parsed_fields`
4. **PR5 (No Filtering)**: Extract EVERYTHING that matches. Do NOT filter results.

# Required Output Schema
Each dictionary in the returned list MUST have exactly these keys:
- `value`: (str) The primary string used for matching (e.g., "Tool: Innovus Version: 21.1")
- `source_file`: (str) Passed from input argument
- `line_number`: (int) The line where match occurred
- `matched_content`: (str) The raw line text
- `parsed_fields`: (dict) Detailed metadata dictionary (tool_name, timestamp, version, etc.)

# Standardization Layer (MANDATORY)
After your extraction logic, you MUST include this exact code block at the end:
```python
# [Locked] Standardization Layer - DO NOT MODIFY
standardized_output = []
for item in results:
    safe_value = str(item.get("value", ""))
    standardized_item = {{
        "value": safe_value,
        "source_file": source_file,
        "line_number": item.get("line_number"),
        "matched_content": str(item.get("matched_content", "")),
        "parsed_fields": item.get("parsed_fields", {{}})
    }}
    standardized_output.append(standardized_item)
return standardized_output
```

# Available Tools
You have access to these tools to examine log files BEFORE writing your code:
- `list_available_files(patterns)` - Discover files matching patterns (e.g., ["*.log", "*.spef"])
- `read_file_header(file_path, max_lines=100)` - Read first N lines of a file
- `search_in_file(file_path, keywords)` - Search for keywords, return matching lines with context

Use these tools to understand the ACTUAL data format before writing your extraction code.

# Task
1. **Examine Available Files**: Use `list_available_files` to see what log files exist
2. **Read Sample Data**: Use `read_file_header` or `search_in_file` to examine actual file content
3. **Analyze ItemSpec**: Understand what fields to extract (tool_name, version, timestamp, etc.)
4. **Write Extraction Code**: Create regex patterns based on ACTUAL data format observed
5. **Build Output**: Construct appropriate `value` string and `parsed_fields` dictionary

# Output Format
Provide ONLY the Python function code wrapped in ```python``` block.
Include helpful comments but no explanations outside the code block.

---

# ItemSpec: Parsing Logic (Section 1)
{section_1_parsing_logic}

---

# ItemSpec: Data Source & Extraction Guide (Section 4.1)
{section_4_1_data_source}

---

# Real Log Snippets (from framework pre-load)
{log_snippets}
'''


# =============================================================================
# Agent B System Prompt (Logic Developer)
# Based on: Agent_Development_Spec.md v1.2
# Input: ItemSpec Section 2 (Check Logic) + Section 3 (Waiver Logic) + Section 4.2 (Special Scenarios)
# 
# Section Delivery Strategy: In LangGraph mode, ALL sections (2 + 3 + 4.2)
# are provided to Agent B in a SINGLE prompt to ensure complete context.
# =============================================================================

AGENT_B_PROMPT_TEMPLATE = '''# Role
You are the **Logic Developer Agent** for "Hierarchical Checker Architecture 10.2".
Your task is to generate the "Universal Logic Atoms" (Atom B & C) and the "Policy Configuration" (YAML).

# Hard Constraints for Generated Code (NON-NEGOTIABLE)

## Atom B: validate_logic
1. **Signature**: `def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search")`
2. **Hard Precedence Rules** (MUST implement in this EXACT order):
   - Priority 1: **Alternatives** (if `|` in pattern) → Split by `|` and check if ANY segment matches via containment
   - Priority 2: **Regex** (if pattern starts with `regex:`) → Use `re.search` or `re.match` based on `regex_mode`
   - Priority 3: **Wildcard** (if `*` or `?` in pattern) → Use `fnmatch.fnmatchcase`
   - Priority 4: **Default** → String containment or equality based on `default_match` param
3. **Return Schema**: `{{'is_match': bool, 'reason': str, 'kind': str}}`
   - `kind` values MUST be one of: `"alternatives"`, `"regex"`, `"wildcard"`, `"contains"`, `"exact"`
4. **Safety Requirements**:
   - **None Safety**: Handle `parsed_fields=None` without raising exception
   - **Bad Regex Safety**: Catch `re.error` and return `is_match=False` with reason starting with `"Invalid Regex:"`
   - **Invalid regex_mode Safety**: If `regex_mode` is not `"match"` or `"search"`, default to `"search"` behavior
5. **Binding Constraint**: Use `re.match` when `regex_mode=='match'` and `re.search` when `regex_mode=='search'`

## Atom C: check_existence
1. **Signature**: `def check_existence(items: List[Dict]) -> Dict`
2. **Return Schema**: `{{'is_match': bool, 'reason': str, 'evidence': items}}`
3. **Logic**: Return `is_match=True` if items list is non-empty, pass through evidence

# Gate 2 Test Vectors (YOUR CODE MUST PASS ALL)
Your implementation will be tested against these exact cases:
1. `validate_logic("abc","a", parsed_fields=None)` → no exception raised
2. `validate_logic("abc","|a||")` → `is_match=True`, `kind="alternatives"`
3. `validate_logic("abc","regex:[", regex_mode="search")` → `is_match=False`, reason startswith `"Invalid Regex:"`
4. `validate_logic("regex:^a", "regex:^a|zzz")` → match (literal alternatives, NOT regex)
5. `validate_logic("abc","a*c")` → `kind="wildcard"`
6. `validate_logic("abc","b", default_match="contains")` → match; `validate_logic("abc","b", default_match="exact")` → no match
7. `validate_logic("abc","regex:^a", regex_mode="BAD")` → must NOT raise, defaults to search behavior

# YAML Field Semantics Reference
Use this reference when generating YAML configuration:

## Checker Type System (4 Types)
| Type   | Pattern Search | Waiver Support | requirements.value | waivers.value |
|--------|----------------|----------------|--------------------|---------------|
| Type 1 | No             | No             | N/A                | N/A           |
| Type 2 | Yes            | No             | integer (>0)       | N/A           |
| Type 3 | Yes            | Yes            | integer (>0)       | 0 or >0       |
| Type 4 | No             | Yes            | N/A                | 0 or >0       |

## requirements.value Semantics
- **N/A**: Type 1/4, no pattern search (boolean check only)
- **Integer (>0)**: Type 2/3, count of pattern_items list

## requirements.pattern_items Format
- **Contains Match (Default)**: `"2025"` → checks if "2025" in item.value
- **Wildcard Match**: `"*Genus*"` → fnmatch(item.value, "*Genus*")
- **Regex Match**: `"regex:\\d{{4}}"` → re.search("\\d{{4}}", item.value)
- **Alternatives**: `"2025|Genus"` → split by |, any one match is sufficient

## waivers.value Semantics
- **N/A**: Type 1/2, no waiver support
- **0**: Global waiver mode, all violations → INFO, auto PASS
- **>0**: Selective waiver mode, count of waive_items patterns

## waivers.waive_items Behavior
- **When value=0**: Contains comments/reasons (informational)
- **When value>0**: Contains actual waiver patterns (same format as pattern_items)

# CRITICAL: Zero Hardcoding Policy
- Your Python code MUST be **UNIVERSAL**
- Do NOT include any item-specific keywords (tool names, file patterns, version numbers)
- All business logic is driven by the YAML configuration, NOT hardcoded in Python

# Task 1: Mechanism (Python Code)
Write UNIVERSAL logic functions. The same code works for ALL items.

# Task 2: Policy (YAML Configuration)
Based on the ItemSpec sections below, generate the YAML configuration that DRIVES your universal code.
Use pattern types (alternatives, regex, wildcard) appropriately.

# Output Format
```python
# === ATOM B ===
def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    ...

# === ATOM C ===
def check_existence(items):
    ...
```

```yaml
# === YAML Configuration ===
requirements:
  value: ...
  pattern_items: [...]
waivers:
  value: ...
  waive_items: [...]
```

---

# ItemSpec: Check Logic (Section 2)
{section_2_check_logic}

---

# ItemSpec: Waiver Logic (Section 3)
{section_3_waiver_logic}

---

# ItemSpec: Special Scenario Handling (Section 4.2)
{section_4_2_special_scenarios}

---

# Agent A Code (extract_context) - For Reference
{atom_a_code}
'''


# =============================================================================
# Reflect Node Prompt
# Based on: Agent_Vibe_Coding_guide_patch.txt Section 4 fallback logic
# =============================================================================

REFLECT_PROMPT_TEMPLATE = '''# Context
Your previous code generation attempt FAILED validation in the Architecture 10.2 Compliance Sandbox.

# Error Details
{validation_errors}

# Gate Results
{gate_results}

# Your Previous Code
```python
{previous_code}
```

# Instructions
1. Analyze each error message carefully - they are PRECISE and ACTIONABLE
2. Identify the root cause:
   - Missing key in output schema?
   - Wrong type (`value` must be `str`)?
   - Precedence violation (alternatives > regex > wildcard > default)?
   - Bad regex not caught?
   - None/empty handling failure?
3. Fix ONLY the issues identified - do NOT rewrite unrelated code
4. Ensure all 10.2 constraints are still satisfied after fixes

# Key Constraints Reminder (10.2 Hard Locks)
- Atom A: `value` MUST be `str` type (use explicit `str()` conversion)
- Atom A: Output must include: `value`, `source_file`, `line_number`, `matched_content`, `parsed_fields`
- Atom B: Handle `parsed_fields=None` gracefully (None-Safety)
- Atom B: Handle empty alternatives like `"|a||"` (Empty Alternatives)
- Atom B: Catch `re.error` and return `is_match=False` with reason starting with `"Invalid Regex:"` (Bad Regex)
- Atom B: Alternatives take precedence over regex detection (Literal Alternatives)
- Atom B: Wildcard patterns (`*`, `?`) use fnmatch, not regex
- Atom B: `kind` MUST be one of: `"alternatives"`, `"regex"`, `"wildcard"`, `"contains"`, `"exact"`
- Atom B: Invalid `regex_mode` should default to `"search"` behavior

# Output Format
Provide the corrected Python code only, wrapped in ```python``` block.
'''


# =============================================================================
# Helper Functions for Building Prompts
# =============================================================================

def build_agent_a_prompt(
    item_spec_content: str,
    log_snippets: Dict[str, Any],
    parsed_spec: Dict[str, Any] = None
) -> str:
    """
    Build the complete Agent A prompt with selective section injection.
    
    Agent A receives: Section 1 (Parsing Logic) + Section 4.1 (Data Source)
    
    Args:
        item_spec_content: Raw ItemSpec Markdown content
        log_snippets: Dictionary of log file snippets
        parsed_spec: (Optional) Pre-parsed ItemSpec structure (deprecated)
        
    Returns:
        Complete prompt string
    """
    # Parse ItemSpec into sections
    sections = parse_itemspec_sections(item_spec_content)
    agent_a_sections = get_agent_a_sections(sections)
    
    # Format log snippets for readability
    if log_snippets:
        formatted_snippets = ""
        for filename, data in log_snippets.items():
            if isinstance(data, dict):
                content = data.get("content", str(data))
            else:
                content = str(data)
            formatted_snippets += f"### File: {filename}\n```\n{content}\n```\n\n"
    else:
        formatted_snippets = "*No log files provided. Use tools to discover and read available files.*"
    
    return AGENT_A_PROMPT_TEMPLATE.format(
        section_1_parsing_logic=agent_a_sections["section_1_parsing_logic"],
        section_4_1_data_source=agent_a_sections["section_4_1_data_source"],
        log_snippets=formatted_snippets
    )


def build_agent_b_prompt(
    item_spec_content: str,
    atom_a_code: str,
    parsed_spec: Dict[str, Any] = None
) -> str:
    """
    Build the complete Agent B prompt with selective section injection.
    
    Agent B receives: Section 2 (Check Logic) + Section 3 (Waiver Logic) + Section 4.2 (Special Scenarios)
    
    Args:
        item_spec_content: Raw ItemSpec Markdown content
        atom_a_code: Generated Atom A code from Agent A
        parsed_spec: (Optional) Pre-parsed ItemSpec structure (deprecated)
        
    Returns:
        Complete prompt string
    """
    # Parse ItemSpec into sections
    sections = parse_itemspec_sections(item_spec_content)
    agent_b_sections = get_agent_b_sections(sections)
    
    return AGENT_B_PROMPT_TEMPLATE.format(
        section_2_check_logic=agent_b_sections["section_2_check_logic"],
        section_3_waiver_logic=agent_b_sections["section_3_waiver_logic"],
        section_4_2_special_scenarios=agent_b_sections["section_4_2_special_scenarios"],
        atom_a_code=atom_a_code
    )


def build_reflect_prompt(
    validation_errors: list,
    gate_results: dict,
    previous_code: str,
    error_source: str = "unknown"
) -> str:
    """
    Build the Reflect node prompt
    
    Args:
        validation_errors: List of error messages
        gate_results: Dictionary of gate test results
        previous_code: The code that failed validation
        error_source: "atom_a" | "atom_b" | "atom_c" | "yaml"
        
    Returns:
        Complete prompt string
    """
    # Add context about which part to fix
    context_note = ""
    if error_source == "atom_a":
        context_note = "\n# Focus Area\nThe errors are related to **Atom A (extract_context)**. Focus your fixes on the parsing logic.\n"
    elif error_source == "atom_b":
        context_note = "\n# Focus Area\nThe errors are related to **Atom B (validate_logic)**. Focus your fixes on the matching logic and precedence.\n"
    elif error_source == "atom_c":
        context_note = "\n# Focus Area\nThe errors are related to **Atom C (check_existence)**. Focus your fixes on the existence check and evidence handling.\n"
    elif error_source == "yaml":
        context_note = "\n# Focus Area\nThe errors are related to **YAML configuration**. Fix the configuration consistency.\n"
    
    prompt = REFLECT_PROMPT_TEMPLATE.format(
        validation_errors=json.dumps(validation_errors, indent=2),
        gate_results=json.dumps(gate_results, indent=2),
        previous_code=previous_code
    )
    
    return context_note + prompt


def parse_agent_response(response: str) -> tuple:
    """
    Parse Agent response to extract code and reasoning
    
    Args:
        response: Raw LLM response
        
    Returns:
        Tuple of (code, reasoning)
    """
    import re
    
    # Extract code block
    code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
    code = code_match.group(1).strip() if code_match else response.strip()
    
    # Extract reasoning (content outside code blocks)
    reasoning = re.sub(r'```python\n.*?```', '', response, flags=re.DOTALL).strip()
    
    return code, reasoning


def parse_agent_b_response(response: str) -> tuple:
    """
    Parse Agent B response to extract Atom B, C, YAML and reasoning
    
    Args:
        response: Raw LLM response
        
    Returns:
        Tuple of (atom_b_code, atom_c_code, yaml_config, reasoning)
    """
    import re
    
    # Extract all code blocks
    python_blocks = re.findall(r'```python\n(.*?)```', response, re.DOTALL)
    yaml_blocks = re.findall(r'```yaml\n(.*?)```', response, re.DOTALL)
    
    atom_b_code = ""
    atom_c_code = ""
    yaml_config = ""
    
    # Identify each block
    for block in python_blocks:
        block = block.strip()
        
        # Check if combined block - need to split
        if 'def validate_logic' in block and 'def check_existence' in block:
            # Split at check_existence
            split_point = block.find('def check_existence')
            atom_b_code = block[:split_point].strip()
            atom_c_code = block[split_point:].strip()
        elif 'def validate_logic' in block and not atom_b_code:
            atom_b_code = block
        elif 'def check_existence' in block and not atom_c_code:
            atom_c_code = block
    
    # Get YAML config
    if yaml_blocks:
        yaml_config = yaml_blocks[0].strip()
    
    # Extract reasoning
    reasoning = re.sub(r'```(?:python|yaml)\n.*?```', '', response, flags=re.DOTALL).strip()
    
    return atom_b_code, atom_c_code, yaml_config, reasoning


# =============================================================================
# ItemSpec Section Parser
# Parses ItemSpec Markdown into sections for selective injection
# =============================================================================

def parse_itemspec_sections(markdown_content: str) -> Dict[str, str]:
    """
    Parse ItemSpec Markdown into separate sections.
    
    Section Structure:
        - Section 1: Parsing Logic (## 1. Parsing Logic)
        - Section 2: Check Logic (## 2. Check Logic)
        - Section 3: Waiver Logic (## 3. Waiver Logic)
        - Section 4.1: Data Source & Extraction (### 4.1 ...)
        - Section 4.2: Special Scenario Handling (### 4.2 ...)
        - Section 4.3: Test Data Generation (### 4.3 ...)
    
    Args:
        markdown_content: Raw ItemSpec Markdown content
        
    Returns:
        Dictionary with section keys and content values
    """
    import re
    
    sections = {
        "section_1": "",      # Parsing Logic
        "section_2": "",      # Check Logic
        "section_3": "",      # Waiver Logic
        "section_4_1": "",    # Data Source & Extraction
        "section_4_2": "",    # Special Scenario Handling
        "section_4_3": "",    # Test Data Generation
        "title": "",          # ItemSpec title line
    }
    
    lines = markdown_content.split('\n')
    current_section = None
    current_content = []
    
    # Pattern for main sections: ## 1. xxx, ## 2. xxx, etc.
    main_section_pattern = re.compile(r'^## (\d+)\.\s+(.+)$')
    # Pattern for subsections: ### 4.1 xxx, ### 4.2 xxx, etc.
    subsection_pattern = re.compile(r'^### (\d+)\.(\d+)\s+(.+)$')
    
    def save_current_section():
        nonlocal current_section, current_content
        if current_section and current_content:
            content = '\n'.join(current_content).strip()
            sections[current_section] = content
        current_content = []
    
    for line in lines:
        # Check for title
        if line.startswith('# ItemSpec:'):
            sections["title"] = line
            continue
        
        # Check for main section header
        main_match = main_section_pattern.match(line)
        if main_match:
            save_current_section()
            section_num = main_match.group(1)
            if section_num == '1':
                current_section = 'section_1'
            elif section_num == '2':
                current_section = 'section_2'
            elif section_num == '3':
                current_section = 'section_3'
            elif section_num == '4':
                current_section = None  # Section 4 has subsections
            current_content = [line]
            continue
        
        # Check for subsection header
        sub_match = subsection_pattern.match(line)
        if sub_match:
            save_current_section()
            major = sub_match.group(1)
            minor = sub_match.group(2)
            if major == '4':
                if minor == '1':
                    current_section = 'section_4_1'
                elif minor == '2':
                    current_section = 'section_4_2'
                elif minor == '3':
                    current_section = 'section_4_3'
            current_content = [line]
            continue
        
        # Accumulate content
        if current_section:
            current_content.append(line)
    
    # Save last section
    save_current_section()
    
    return sections


def get_agent_a_sections(sections: Dict[str, str]) -> Dict[str, str]:
    """
    Get sections relevant for Agent A: Section 1 + 4.1
    
    Args:
        sections: Parsed sections dictionary
        
    Returns:
        Dictionary with Agent A relevant sections
    """
    return {
        "section_1_parsing_logic": sections.get("section_1", ""),
        "section_4_1_data_source": sections.get("section_4_1", ""),
    }


def get_agent_b_sections(sections: Dict[str, str]) -> Dict[str, str]:
    """
    Get sections relevant for Agent B: Section 2 + 3 + 4.2
    
    Args:
        sections: Parsed sections dictionary
        
    Returns:
        Dictionary with Agent B relevant sections
    """
    return {
        "section_2_check_logic": sections.get("section_2", ""),
        "section_3_waiver_logic": sections.get("section_3", ""),
        "section_4_2_special_scenarios": sections.get("section_4_2", ""),
    }
