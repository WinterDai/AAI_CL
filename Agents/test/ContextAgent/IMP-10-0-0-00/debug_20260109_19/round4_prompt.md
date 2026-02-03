<!-- ========================================
     USER PROMPT: Section 3 Guidance
     (From user_prompt.md)
========================================= -->

### For Section 3 (Waiver Logic)

1. **Think through design flow** to identify when checks legitimately fail
2. **List scenarios** where failures are acceptable:
   - Early design stages (incomplete data)
   - Testing scenarios (historical data)
   - Tool-specific exceptions
3. **Provide concrete examples** of waiver reasons
4. **Extract keywords** from scenarios for matching

Example scenarios:
- Synthesis stage → SPEF not yet available
- Regression testing → Using golden files from previous release
- Format exceptions → Special vendor-specific formats


<!-- ========================================
     TASK: Round 4 - Generate Section 3
========================================= -->

<task>
Generate Section 3 (Waiver Logic) of the ItemSpec.
</task>

<!-- ========================================
     CONTEXT: Previous Sections
========================================= -->

<previous_sections>
Section 1 (Parsing Logic):
## 1. Parsing Logic

**Information to Extract**:

### 1.1 Netlist File Information
- **Purpose**: Extract version metadata from netlist files to verify tool, version, and generation timestamp information
- **Key Fields**:
  - `loaded`: Boolean indicating whether netlist file was successfully accessed and parsed
  - `tool_name`: String representing the EDA tool that generated the netlist (e.g., "Innovus", "Genus", "ICC2", "DC")
  - `tool_version`: String representing the tool version number (e.g., "21.1", "2023.03-SP2")
  - `timestamp`: String representing the generation date/time of the netlist
  - `format`: String representing the netlist format (e.g., "Verilog", "VHDL", "DEF")

### 1.2 SPEF File Information
- **Purpose**: Extract version metadata from SPEF (Standard Parasitic Exchange Format) files to verify extraction tool, version, standard compliance, and generation timestamp
- **Key Fields**:
  - `loaded`: Boolean indicating whether SPEF file was successfully accessed and parsed
  - `tool_name`: String representing the parasitic extraction tool (e.g., "StarRC", "Quantus", "PrimeTime")
  - `tool_version`: String representing the extraction tool version number
  - `timestamp`: String representing the generation date/time of the SPEF file
  - `standard_version`: String representing the IEEE standard version (e.g., "IEEE 1481-1999", "IEEE 1481-2009")

### 1.3 File Metadata
- **Purpose**: Provide traceability information for debugging and audit purposes
- **Key Fields**:
  - `source_file`: Absolute path to the input file where information was extracted
  - `line_number`: Line number where version information was found
  - `matched_content`: The actual text line that was matched during extraction

**Data Structure**: Output structure follows global_rules.md Section 2.4.1 (Required metadata + parsed_fields)

**parsed_fields Example**:
```python
{
  "netlist": {
    "loaded": True,
    "tool_name": "Innovus",
    "tool_version": "21.10-s080_1",
    "timestamp": "2025-01-15 14:23:45",
    "format": "Verilog"
  },
  "spef": {
    "loaded": True,
    "tool_name": "StarRC",
    "tool_version": "2022.06-SP1",
    "timestamp": "2025-01-15 16:45:12",
    "standard_version": "IEEE 1481-2009"
  }
}
```

**Complete Output Structure Example**:
```python
[
  {
    "value": "Netlist version: Innovus 21.10-s080_1",
    "source_file": "/project/design/netlist/top.v.gz",
    "line_number": 3,
    "matched_content": "// Generator: Cadence Innovus 21.10-s080_1",
    "parsed_fields": {
      "netlist": {
        "loaded": True,
        "tool_name": "Innovus",
        "tool_version": "21.10-s080_1",
        "timestamp": "2025-01-15 14:23:45",
        "format": "Verilog"
      }
    }
  },
  {
    "value": "SPEF version: IEEE 1481-2009",
    "source_file": "/project/design/spef/top.spef.gz",
    "line_number": 1,
    "matched_content": "*SPEF \"IEEE 1481-2009\"",
    "parsed_fields": {
      "spef": {
        "loaded": True,
        "tool_name": "StarRC",
        "tool_version": "2022.06-SP1",
        "timestamp": "2025-01-15 16:45:12",
        "standard_version": "IEEE 1481-2009"
      }
    }
  }
]
```

Section 2 (Check Logic):
## 2. Check Logic

Based on description "Confirm the netlist/spef version is correct", the following items require validation:

**Validation Items**:

### 2.1 Netlist File Loading Status
- **Purpose**: Verify netlist file was successfully accessed and parsed
- **Completeness definition**: 
  - `parsed_fields.netlist.loaded == True`
  - File path is accessible and readable
- **Validation type**: Existence check (Boolean)
- **PASS condition**: Netlist file successfully loaded
- **FAIL condition**: File not found, access denied, or parsing error

### 2.2 Netlist Version Completeness
- **Purpose**: Verify netlist contains complete version metadata
- **Completeness definition**:
  - `parsed_fields.netlist.tool_name` exists and is non-empty
  - `parsed_fields.netlist.tool_version` exists and is non-empty
  - `parsed_fields.netlist.timestamp` exists and is non-empty
  - `parsed_fields.netlist.format` exists and is non-empty
- **Validation type**: Existence check (Boolean)
- **PASS condition**: All mandatory version fields present and non-empty
- **FAIL condition**: Any mandatory field missing or empty

### 2.3 SPEF File Loading Status
- **Purpose**: Verify SPEF file was successfully accessed and parsed
- **Completeness definition**:
  - `parsed_fields.spef.loaded == True`
  - File path is accessible and readable
- **Validation type**: Existence check (Boolean)
- **PASS condition**: SPEF file successfully loaded
- **FAIL condition**: File not found, access denied, or parsing error

### 2.4 SPEF Version Completeness
- **Purpose**: Verify SPEF contains complete version metadata
- **Completeness definition**:
  - `parsed_fields.spef.tool_name` exists and is non-empty
  - `parsed_fields.spef.tool_version` exists and is non-empty
  - `parsed_fields.spef.timestamp` exists and is non-empty
  - `parsed_fields.spef.standard_version` exists and is non-empty
- **Validation type**: Existence check (Boolean)
- **PASS condition**: All mandatory version fields present and non-empty
- **FAIL condition**: Any mandatory field missing or empty

**Pattern Matching**:
- Items requiring pattern matching: None (Type 4 checker - Boolean validation only)
- Items with existence check only: All items (2.1, 2.2, 2.3, 2.4)

**Pattern Correspondence Order**: 
- Not applicable (requirements.value = N/A, no pattern_items defined)

**Overall Pass/Fail Logic**:
- **PASS**: All four validation items pass (both netlist and SPEF files loaded successfully with complete version information)
- **FAIL**: Any validation item fails (file loading failure OR incomplete version metadata)
- **Edge Cases**:
  - If netlist loads but SPEF fails → FAIL (unless waived)
  - If version fields exist but contain only whitespace → FAIL (treated as empty)
  - If files are compressed (.gz) → Must decompress before parsing
  - If multiple version headers exist → Use first occurrence

**Validation Sequence**:
1. Check netlist loading status (Item 2.1)
2. If loaded, validate netlist version completeness (Item 2.2)
3. Check SPEF loading status (Item 2.3)
4. If loaded, validate SPEF version completeness (Item 2.4)
5. Return PASS only if all items pass
</previous_sections>

<!-- ========================================
     CONTEXT: Analysis Reference
========================================= -->

<analysis_reference>
## Step 1: Identify Key Entities

**Main subjects mentioned:**
- **netlist**: A file containing the logical/physical connectivity of the design
- **spef**: Standard Parasitic Exchange Format file containing parasitic RC information
- **version**: Version information associated with these files

**Critical interpretation (applying Pattern 1 - Slash Notation):**
- "netlist/spef version" means validate **BOTH** netlist version **AND** spef version
- This is NOT an either/or scenario - both must be verified

## Step 2: Determine Information Categories

To validate "correctness" of netlist/spef versions, we need:

### Category A: File Loading Status
- **Rationale**: Before checking versions, confirm files were successfully loaded/read
- **Data needed**: Load success indicators, error messages, file accessibility

### Category B: Version Information
- **Rationale**: Core requirement - extract version metadata from both file types
- **Data needed**: 
  - Tool name that generated the file
  - Version number/string
  - Generation timestamp/date
  - Format version (e.g., SPEF IEEE standard version)

### Category C: Version Completeness
- **Rationale**: "Correct" implies complete version information, not just existence
- **Data needed**: Presence of all mandatory version fields

### Category D: Version Consistency (Optional)
- **Rationale**: In EDA flows, netlist and SPEF should typically come from compatible tool versions
- **Data needed**: Tool compatibility indicators, flow stage markers

## Step 3: List Required Fields

### For Netlist Version:
- `netlist_file_loaded`: Boolean/status indicator
- `netlist_tool_name`: String (e.g., "Innovus", "ICC2", "Genus")
- `netlist_version`: String (e.g., "21.1", "2023.03-SP2")
- `netlist_timestamp`: String (generation date/time)
- `netlist_format`: String (e.g., "Verilog", "VHDL", "DEF")
- `netlist_source_line`: Integer (for traceability)

### For SPEF Version:
- `spef_file_loaded`: Boolean/status indicator
- `spef_tool_name`: String (extraction tool name)
- `spef_version`: String (tool version)
- `spef_timestamp`: String (generation date/time)
- `spef_standard_version`: String (e.g., "IEEE 1481-1999", "IEEE 1481-2009")
- `spef_source_line`: Integer (for traceability)

### Metadata:
- `source_file`: String (which input file contained this info)
- `extraction_timestamp`: String (when parsing occurred)

## Step 4: Design Data Structure

**Proposed structure** (grouped by file type for clarity):

```python
parsed_fields = {
    'netlist': {
        'loaded': bool,
        'tool_name': str,
        'tool_version': str,
        'timestamp': str,
        'format': str,
        'source_line': int
    },
    'spef': {
        'loaded': bool,
        'tool_name': str,
        'tool_version': str,
        'timestamp': str,
        'standard_version': str,
        'source_line': int
    },
    'metadata': {
        'source_file': str,
        'extraction_timestamp': str
    }
}
```

**Rationale:**
- Parallel structure for netlist/spef makes validation logic symmetric
- Metadata separate for cross-cutting concerns
- All fields optional (may not exist in all files) - validation logic handles missing data

## Step 5: Identify Validation Items

Based on the description "Confirm the netlist/spef version is correct", I identify **4 validation items**:

### Item 1: Netlist File Loading Status
- **What**: Verify netlist file was successfully loaded
- **Why**: Cannot validate version if file isn't accessible
- **Check**: `parsed_fields['netlist']['loaded'] == True`

### Item 2: Netlist Version Completeness
- **What**: Verify netlist has complete version information
- **Why**: "Correct" implies all mandatory version fields present
- **Check**: `tool_name`, `tool_version`, and `timestamp` all exist and non-empty

### Item 3: SPEF File Loading Status
- **What**: Verify SPEF file was successfully loaded
- **Why**: Cannot validate version if file isn't accessible
- **Check**: `parsed_fields['spef']['loaded'] == True`

### Item 4: SPEF Version Completeness
- **What**: Verify SPEF has complete version information
- **Why**: "Correct" implies all mandatory version fields present
- **Check**: `tool_name`, `tool_version`, `timestamp`, and `standard_version` all exist and non-empty

## Step 6: Determine Pattern Matching Needs

### Items Requiring **Existence Checks Only** (Boolean validation):
- **Item 1** (Netlist loading): Boolean check - file loaded or not
- **Item 3** (SPEF loading): Boolean check - file loaded or not

### Items Requiring **Pattern Matching** (if requirements.pattern_items provided):
- **Item 2** (Netlist version): Could match against expected tool/version patterns
  - Example pattern: "Innovus 21.1" or "ICC2 2023.03"
- **Item 4** (SPEF version): Could match against expected tool/version/standard patterns
  - Example pattern: "StarRC 2022.06 IEEE-1481-2009"

**However**, given `requirements.value: N/A` in configuration, this appears to be a **Type 1 checker** (Boolean Check):
- No predefined patterns to search for
- Validates presence and completeness only
- PASS if all 4 items have complete information
- FAIL if any item is incomplete

## Step 7: Consider Waiver Scenarios

### Scenario 1: Early Design Stage (Pre-Parasitic Extraction)
- **When**: Synthesis or early floorplanning stage
- **Why waive**: SPEF doesn't exist yet - only netlist available
- **Waiver reason**: "Pre-extraction stage - SPEF not required"
- **Keywords**: "synthesis", "pre-extraction", "no-spef", "early-stage"

### Scenario 2: Ideal Netlist (Zero Parasitics)
- **When**: Using ideal/wireload models instead of extracted parasitics
- **Why waive**: SPEF intentionally not used
- **Waiver reason**: "Ideal timing analysis - wireload models used"
- **Keywords**: "ideal", "wireload", "no-parasitics", "wlm"

### Scenario 3: Legacy/Golden Reference Files
- **When**: Comparing against historical regression data
- **Why waive**: Old files may have incomplete version headers
- **Waiver reason**: "Legacy golden file - version info grandfathered"
- **Keywords**: "legacy", "golden", "regression", "historical"

### Scenario 4: Partial SPEF (Incremental ECO)
- **When**: ECO flow with partial SPEF updates
- **Why waive**: May have different version info than full netlist
- **Waiver reason**: "ECO flow - partial SPEF update"
- **Keywords**: "eco", "incremental", "partial-spef"

**Waiver Support Decision:**
Given these legitimate scenarios, this checker should support waivers.

**Revised Type Classification**: 
- Original assumption: Type 1 (Boolean, no waiver)
- **Corrected**: Type 4 (Boolean Check + Waiver)
  - No pattern search (requirements.value = N/A)
  - Waiver support needed (waivers.value >= 0)

## Summary

**Checker Type**: Type 4 (Boolean Check + Waiver)

**Validation Items**: 4 items
1. Netlist file loading status
2. Netlist version completeness
3. SPEF file loading status  
4. SPEF version completeness

**Pattern Matching**: None (existence/completeness checks only)

**Waiver Support**: Yes (4 common scenarios identified)

**Data Structure**: Parallel netlist/spef structure with metadata
</analysis_reference>

<!-- ========================================
     TEMPLATE: Section 3 Structure
========================================= -->

<template_section>
## 3. Waiver Logic

<!-- 
TODO: Define scenarios where validation failures are acceptable.
Guidelines:
- Think about different design stages and when checks might legitimately fail
- Consider testing scenarios (golden files, regression testing)
- List 2-4 common waiver scenarios based on engineering experience
- Provide concrete waiver reasons and matching keywords
- Reference: global_rules.md Section 2.3 for waiver logic rules
-->

Based on description "{DESCRIPTION}", analyze waiver scenarios for validation items:

**Waivable Items and Matching Keywords**:

1. **{TODO: First Waivable Item}**
   <!-- Example: "SPEF File Loading Status" -->
   - Waiver scenario: {TODO: Describe when this failure is acceptable}
   <!-- Example: "Synthesis stage does not require SPEF files" -->
   - Typical waiver reason: {TODO: Provide example reason text}
   <!-- Example: "Current stage is synthesis, SPEF check not applicable" -->
   - Matching keywords: {TODO: List keywords for selective waiver matching}
   <!-- Example: "SPEF", "synthesis" -->

2. **{TODO: Second Waivable Item}**
   - Waiver scenario: {TODO: Describe acceptable failure scenario}
   - Typical waiver reason: {TODO: Example reason}
   - Matching keywords: {TODO: Keywords}

3. **{TODO: Third Waivable Item}**
   <!-- Add more waivable items as needed (typically 2-4 items) -->
   - Waiver scenario: {TODO: Scenario description}
   - Typical waiver reason: {TODO: Example reason}
   - Matching keywords: {TODO: Keywords}

---

</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Waiver Logic section following these requirements:

1. **Waivable Scenarios**: Identify 2-4 common scenarios where failures are acceptable
   - Consider different design stages (synthesis, P&R, signoff)
   - Think about regression testing with historical data
   - Account for legacy formats or special cases

2. **For Each Scenario**, specify:
   - Scenario name and description
   - Typical waiver reason (business justification)
   - Matching keywords for waivers.waive_items
   - Which validation items from Section 2 can be waived

3. **Waiver Modes Documentation**:
   - Global Mode (waivers.value=0): Behavior and use cases
   - Selective Mode (waivers.value>0): Matching strategy and application

4. **Implementation Guidance**:
   - Pattern matching strategies (exact, wildcard, regex)
   - How to link waivers to validation items
   - Traceability requirements

5. **Remove Template Comments**: Delete all instructional text

Output the complete Section 3 inside <section3></section3> tags.
</instructions>