# Global Rules - Checker Framework Foundation

---

## Overview

This document defines the foundational rules that all checker implementations must follow, regardless of specific checker types or agent roles. These rules establish the Type system, core logic definitions, and output standards.

---

## 1. Type System

### 1.0 Configuration Field Conventions

The following table defines valid values and semantics for item.yaml configuration fields:

| Field | Valid Values | Semantics |
|-------|-------------|-----------|
| `description` | String | Current checker's specific check objective |
| `requirements.value` | `N/A` or Number (> 0) | `N/A` for Type 1/4 (no pattern search); Number represents count of `requirements.pattern_items` for Type 2/3 |
| `requirements.pattern_items` | List of values or strings | Specific pattern requirements; may be numbers, single words, or sentences |
| `waivers.value` | `N/A` or Number (≥ 0) | `N/A` for Type 1/2 (no waiver); `0` = waive all failures (waive_items contains comments); `> 0` = selective waiver (count of waive_items) |
| `waivers.waive_items` | List of strings | When `waivers.value=0`: comments after waiving; When `waivers.value>0`: actual waiver patterns (strings) |

---

### 1.1 Four Checker Types

The framework supports 4 checker types based on two orthogonal features:

- **Pattern Search**: Whether the checker searches for specific patterns (`requirements.pattern_items`)
- **Waiver Support**: Whether the checker supports waiver logic (`waivers.value >= 0`)

#### Type 1: Boolean Check

- **Description**: PASS/FAIL only, no pattern search, no waiver support
- **Pattern Items**: None (requirements.value = N/A)
- **Waiver Support**: None (waivers.value = N/A)
- **Output**: `{'status': 'PASS'/'FAIL', 'found_items': [...], 'missing_items': [...]}`

#### Type 2: Value Check

- **Description**: Search patterns defined in requirements.pattern_items, no waiver support
- **Pattern Items**: Yes (requirements.value > 0)
- **Waiver Support**: None (waivers.value = N/A)
- **Output**: `{'status': 'PASS'/'FAIL', 'found_items': [...], 'missing_items': [...], 'extra_items': [...]}`

#### Type 3: Value Check + Waiver

- **Description**: Search patterns, apply waivers
- **Pattern Items**: Yes (requirements.value > 0)
- **Waiver Support**: Yes (waivers.value >= 0, supporting both global and selective waiver)
- **Output**: `{'status': 'PASS'/'FAIL', 'found_items': [...], 'missing_items': [...], 'extra_items': [...], 'waived': [...], 'unused_waivers': [...]}`

#### Type 4: Boolean Check + Waiver

- **Description**: No pattern search, apply waivers
- **Pattern Items**: None (requirements.value = N/A)
- **Waiver Support**: Yes (waivers.value >= 0, supporting both global and selective waiver)
- **Output**: `{'status': 'PASS'/'FAIL', 'found_items': [...], 'missing_items': [...], 'waived': [...], 'unused_waivers': [...]}`

### 1.2 Type Selection Criteria

**Based on Checker Requirements**:

- **Type 1**: Checker performs boolean validation without pattern search, no waiver support needed
- **Type 2**: Checker searches for specific patterns without waiver support
- **Type 3**: Checker searches for patterns and requires selective waiver capability
- **Type 4**: Checker performs boolean validation and requires selective waiver capability

---

## 2. Logic Definitions

### 2.1 Parsing Logic

**Purpose**: Extract target information from input files

**PR1: Extract Target Information**

- Use format-specific regex patterns
- Reference standard format definitions for typical patterns
- Ensure robust pattern matching with proper escaping

**PR2: Handle Multi-Stage Extraction**

- Some formats require multi-stage extraction (e.g., STA_Log → extract path → parse SPEF)
- Implement indirect_reference handling when needed
- Chain extraction results properly

**PR3: Normalize Format Names**

- Use standardized format names (SPEF, DEF, SDC, Liberty, etc.)
- Apply format normalization rules to handle aliases
- Maintain consistency across all parsing logic

**PR4: Handle Missing or Malformed Data**

- Define fallback strategies for missing data
- Return clear error messages for malformed input
- Fail gracefully with actionable diagnostics

**PR5: Extract All Available Information**

- Parsing Logic should extract all matching information found in input files
- Do not filter or limit results based on checker Type at parsing stage
- Return complete list of all extracted items with metadata
- Check Logic determines found/missing/extra based on Type requirements

**PR6: Output Structured Data with Metadata**

- Return structured objects (not plain strings) for all extracted data
- Include traceability metadata: source file path, line number, matched content
- Enable downstream logic to preserve provenance information
- See Section 2.4 for detailed data structure standards

### 2.2 Check Logic

**Purpose**: Validate extracted data against requirements

**CR1: Align with Type Definition**

- **Type 1/4**: Boolean check (`requirements.value = N/A`)
- **Type 2/3**: Pattern-based search (`requirements.value > 0`)
- Return appropriate data structure for type

**CR2: Produce Clear Pass/Fail Criteria**

- Return explicit PASS/FAIL status with detailed reasons
- Provide actionable diagnostics for failures
- Include context for why check passed or failed

**CR3: Handle Edge Cases**

- Multiple files with different results
- Partial matches (some patterns found, some missing)
- Empty results (no data extracted)
- Conflicting data from multiple sources

**CR4: Preserve Metadata Throughout Validation**

- Accept structured input from Parsing Logic with metadata
- Preserve all traceability fields (source_file, line_number, matched_content) in output
- Add validation-specific information (description, expected vs actual) to output items
- Ensure found_items/missing_items/extra_items retain provenance for downstream rendering
- See Section 2.4 for detailed data handling requirements

**CR5: Support Type-Specific Outputs**

- **Type 1**: Return `status`, `found_items`, `missing_items` (boolean check, no pattern search, no waiver)
  - `found_items` contains items that passed validation
  - `missing_items` contains items that failed validation
- **Type 2**: Return `status`, `found_items`, `missing_items`, `extra_items` (pattern search, no waiver)
  - `found_items` contains items matching requirements.pattern_items
  - `missing_items` contains required items not found
  - `extra_items` contains items not matching requirements.pattern_items
- **Type 3**: Return `status`, `found_items`, `missing_items`, `extra_items`, `waived`, `unused_waivers` (pattern search with waiver)
  - `found_items` contains items matching requirements.pattern_items
  - `missing_items` contains required items not found (unwaived)
  - `extra_items` contains items not matching requirements.pattern_items (unwaived)
  - `waived` contains violations (from missing_items/extra_items) that matched waivers.waive_items
  - `unused_waivers` contains waive_items patterns that did not match any violations
- **Type 4**: Return `status`, `found_items`, `missing_items`, `waived`, `unused_waivers` (boolean check with waiver)
  - `found_items` contains items that passed validation
  - `missing_items` contains items that failed validation (unwaived)
  - `waived` contains violations that matched waivers.waive_items
  - `unused_waivers` contains waive_items patterns that did not match any violations

**Pattern Matching Rules for requirements.pattern_items**:

1. **Structure**: pattern_items is a list of patterns, each corresponding to a validation item that requires pattern matching (as defined in ItemSpec)

2. **Matching Logic**:
   - Each validation item must match at least one pattern from its corresponding pattern_item
   - If a pattern_item contains multiple alternatives (using `|` separator), any one match is sufficient
   - All validation items requiring pattern matching must be satisfied for overall PASS

3. **Pattern Format** (same as waive_items):
   - **Contains Match (Default)**: `"2025"` → `"2025" in item.value`
   - **Wildcard Match**: `"*Genus*"` → `fnmatch(item.value, "*Genus*")`
   - **Regex Match**: `"regex:\\d{4}"` → `re.search("\\d{4}", item.value)`
   - **Multiple Alternatives**: `"2025|Genus"` → split by `|`, then apply Contains match to each alternative; any one match is sufficient

4. **Order Correspondence**:
   - The order of pattern_items corresponds to the order of validation items that require pattern matching (as defined in ItemSpec)
   - Validation items not requiring pattern matching (e.g., existence checks) are skipped in the pattern_items list

5. **Matching Against Value Field**:
   - Pattern items match against the `value` field of each parsed object (see Section 2.4.1)
   - All metadata fields (source_file, line_number, matched_content) are preserved regardless of match result

**Example**:
```yaml
# For a checker with 2 validation items requiring pattern matching
requirements:
  value: 2
  pattern_items:
    - "2025|Genus"     # First item: matches if value contains "2025" OR "Genus"
    - "2025|Innovus"   # Second item: matches if value contains "2025" OR "Innovus"
```

### 2.3 Waiver Logic

**Purpose**: Apply waiver rules to violations

**Applicability**: Type 3 and Type 4 only (Type 1/2 do not support waiver logic)

---

#### 2.3.1 Global Waiver Mode (waivers.value=0)

**Behavior**:

- Converts all violations to **INFO** severity, resulting in **PASS** status
- Adds `[WAIVED_AS_INFO]` tag to violations:
  - **Type 3**: from `missing_items` and `extra_items`
  - **Type 4**: from `missing_items` only
- Outputs waive_items configuration as part of `waived` field with `[WAIVED_INFO]` tag
  - `waive_items` contents (comments) become informational output in `waived`
  - This documents the global waiver configuration for traceability
- Global mode does not produce `unused_waivers` (empty list, as all violations are automatically waived)

**Use Cases**:

- Legacy designs that cannot be fixed
- Known issues approved for waiver
- Temporary bypass during development

**LLM Implementation Note**:

- You do NOT need to implement explicit waiver matching logic
- The framework automatically handles conversion when `waivers.value=0`
- Simply return violations as usual; framework applies transformation
- Document this behavior in ItemSpec Section 4.1

**Framework Detection** (for reference):

```python
# Framework checks: should_convert_fail_to_info() in waiver_handler_template.py
if waivers.value == 0:
    # Auto-convert FAIL → INFO with [WAIVED_AS_INFO]
    # Auto-convert waive_items → INFO with [WAIVED_INFO]
```

**Rule Summary**:

- **WR0**: When `waivers.value=0`, framework auto-converts FAIL→INFO
- No explicit implementation needed in waiver_logic
- Only Type 3/4 support this mode

---

#### 2.3.2 Selective Waiver Mode (waivers.value>0)

**Behavior**:

1. **Identify violations**: Checker produces `missing_items` or `extra_items` (Type 3 only; Type 4 does not include `extra_items`)
2. **Match patterns**: Match each violation against `waive_items` patterns using three strategies:
   
   **Strategy 1: Exact Match**
   ```
   waiver.pattern: "cdn_hs_phy_slice_0"
   item: "cdn_hs_phy_slice_0"
   Algorithm: pattern == item
   Result: MATCH
   ```
   
   **Strategy 2: Wildcard Match**
   ```
   waiver.pattern: "cdn_hs_phy_slice*"
   item: "cdn_hs_phy_slice_0"
   Algorithm: fnmatch(item, pattern)
   Result: MATCH
   ```
   
   **Strategy 3: Regex Match**
   ```
   waiver.pattern: "regex:test_.*_ff"
   item: "test_module_ff"
   Algorithm: re.match(pattern.removeprefix("regex:"), item)
   Result: MATCH
   ```

3. **Apply waivers**:
   - **Matched violations**: Remove from `missing_items`/`extra_items` and add to `waived` field
   - **Matched violations**: Change severity from ERROR to INFO with `[WAIVER]` tag
   - **Unmatched violations**: Remain in `missing_items`/`extra_items` as ERROR
   - **Unused waive_items**: Add to `unused_waivers` field and report as WARN with `[WAIVER]` tag

4. **Final Status Determination**:
   - All violations waived → PASS
   - Any violation not waived → FAIL

**Waiver YAML Format**:

```yaml
waivers:
  value: 3  # Number of waiver items
  waive_items:
    - "cdn_hs_phy_slice*"      # Wildcard pattern
    - "regex:test_.*_ff"        # Regex pattern
    - "exact_module_name"       # Exact match
```

---

#### 2.3.3 Waiver Processing Rules

**WR1: Matching Strategy Implementation**

- Implement all three matching strategies: exact, wildcard, and regex
- Handle string format for waive_items
- Preserve original pattern for traceability
- Validate pattern syntax before applying (especially regex)

**WR2: Traceability Requirements**

- Output unused waive_items to `unused_waivers` field and report as WARN with `[WAIVER]` tag
- Include original pattern in waiver messages
- Link each waived item back to matching waive_item pattern

---

### 2.4 Data Structure Standards

**Purpose**: Define structured data contracts between Parsing Logic, Check Logic, and Waiver Logic to ensure metadata traceability throughout the validation pipeline.

---

#### 2.4.0 Output Fields Summary

The following table defines all output structures across the validation pipeline:

**Parsing Logic Output**:

| Component | Structure | Content |
|-----------|-----------|----------|
| Parsing result | List of objects | Each object contains: `value`, `source_file`, `line_number`, `matched_content`, and optional `parsed_fields` |

**Check Logic & Waiver Logic Output** (final return to framework):

| Field | Applicable Types | Source Logic | Content |
|-------|-----------------|--------------|----------|
| `status` | All Types | Check Logic | String: `'PASS'` or `'FAIL'` |
| `found_items` | All Types | Check Logic | List of objects from Parsing (preserved) |
| `missing_items` | All Types | Check Logic | List of objects (+ expected/actual fields) |
| `extra_items` | Type 2/3 only | Check Logic | List of objects from Parsing (preserved) |
| `waived` | Type 3/4 only | Waiver Logic | List of objects (+ waiver_pattern/waiver_reason) |
| `unused_waivers` | Type 3/4 only | Waiver Logic | List of objects (pattern + reason) |

**Note**: Detailed structure specifications for each component are provided in sections 2.4.1 (Parsing), 2.4.2 (Check), and 2.4.3 (Waiver).

---

#### 2.4.1 Parsing Logic Output Structure

Parsing Logic must return structured objects (not plain strings or simple values). Each extracted data item must include:

**Required Metadata Fields**:

- `value`: The primary extracted content (string or number)
- `source_file`: Absolute path to the file where data was found
- `line_number`: Line number where match occurred (integer ≥ 1; null if not applicable)
- `matched_content`: The actual text line that was matched

**Optional Metadata Fields**:

- `context_before`: List of lines before the match (for context)
- `context_after`: List of lines after the match (for context)
- `match_pattern`: The regex or pattern used for extraction

**Checker-Specific Fields**:

- Use `parsed_fields` dictionary to include checker-specific extracted information
- Examples: tool name, version number, timestamp, or any domain-specific data

**Example Output**:

```python
parsing_output = [
    {
        "value": "Genus version 21.1",
        "source_file": "/path/to/design.v.gz",
        "line_number": 42,
        "matched_content": "# Generator: Genus version 21.1",
        "parsed_fields": {
            "tool": "Genus",
            "version": "21.1",
            "timestamp": "2025-01-05"
        }
    }
]
```

---

#### 2.4.2 Check Logic Data Handling

Check Logic must preserve metadata from Parsing Logic and enrich it with validation information.

**Input**: Structured data from Parsing Logic (with metadata)

**Output Structure Requirements**:

1. **Preserve all metadata fields** from Parsing Logic:
   - `source_file`, `line_number`, `matched_content`, `parsed_fields`

2. **Add validation-specific fields**:
   - `description`: Human-readable explanation of the validation result
   - For `missing_items`: Include `expected` (what was required) vs `actual` (what was found, if any)
   - For `extra_items`: Include `description` explaining why item is unexpected

**Example - found_items**:

```python
found_items = [
    {
        "description": "Netlist version information complete",
        # Preserved from Parsing
        "value": "Genus version 21.1",
        "source_file": "/path/to/design.v.gz",
        "line_number": 42,
        "matched_content": "# Generator: Genus version 21.1",
        "parsed_fields": {"tool": "Genus", "version": "21.1"}
    }
]
```

**Example - missing_items**:

```python
missing_items = [
    {
        "description": "SPEF version not found",
        "expected": "SPEF version: IEEE 1481-1999",
        "searched_files": ["/path/to/sta.log"],
        "line_number": null  # No match found
    }
]
```

---

#### 2.4.3 Waiver Logic Data Handling

Waiver Logic must preserve all metadata from Check Logic when processing violations.

**For `waived` field**:
- Preserve all metadata from the original violation (missing_items/extra_items)
- Add waiver-specific fields:
  - `waiver_pattern`: The pattern from waivers.waive_items that matched
  - `waiver_reason`: Explanation for the waiver (from waive_items comments if waiver=0)

**For `unused_waivers` field**:
- Contains patterns that did not match any violations
- Structure: List of objects with `pattern` and optional `reason`

**Example - waived**:

```python
waived = [
    {
        "description": "SPEF check not applicable in synthesis stage",
        "waiver_pattern": "SPEF*",
        "waiver_reason": "Synthesis stage, SPEF not required",
        # Preserved from original violation
        "expected": "SPEF version: IEEE 1481-1999",
        "searched_files": ["/path/to/sta.log"]
    }
]
```

**Example - unused_waivers**:

```python
unused_waivers = [
    {
        "pattern": "unused_module_*",
        "reason": "No violations matched this pattern"
    }
]
```

---

**Data Flow Summary**:

```
Parsing Logic → [structured data + metadata]
       ↓
Check Logic → [preserve metadata + add validation info]
       ↓
Waiver Logic → [preserve metadata + add waiver info]
       ↓
Framework → [render with full traceability]
```

## 3. Quality Checklist

### Q1: Functional Units Completeness

- ✅ `parsing_logic` exists and extracts required data (all Types)
- ✅ `check_logic` exists and validates requirements (all Types)
- ✅ `waiver_logic` exists and documents waiver behavior (Type 3/4 only)
  - Type 1/2: No waiver_logic required (waiver not supported)
  - Type 3/4: Document Global Waiver Mode (value=0) + Selective Waiver Mode (value>0)

### Q2: Type Specification Alignment

- ✅ `functional_units.type_specifications` matches Type definition
- ✅ Type 1/4: `requirements.value = N/A`
- ✅ Type 2/3: `requirements.value > 0`
- ✅ Type 3/4: `waivers.value >= 0`

### Q3: Criticality Consistency

- ✅ All `required` formats appear in `parsing_logic`
- ✅ All `optional` formats clearly marked
- ✅ Missing required formats trigger ERROR

### Q4: No Hardcoded Values

- ✅ Reference `item.yaml` configuration fields
- ✅ Use `requirements.*` for expected values
- ✅ Use `waivers.*` for waiver configuration
- ✅ No absolute file paths

### Q5: Error Handling Completeness

- ✅ Each functional unit documents failure modes
- ✅ Clear error messages for missing files
- ✅ Clear error messages for malformed data
- ✅ Fallback strategies documented

### Q6: Traceability

- ✅ All formats trace to Layer 0 `involved_formats`
- ✅ All detailed requirement items trace to `requirements.*`
- ✅ All waivers trace to `waivers.waive_items`
- ✅ No orphaned functional units

---
