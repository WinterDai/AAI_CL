<!-- ========================================
     USER PROMPT: Section 1 Guidance
     (From user_prompt.md)
========================================= -->

### For Section 1 (Parsing Logic)

1. **Analyze the description** to identify key entities (e.g., "netlist", "spef", "version")
2. **List information categories** needed for validation (e.g., file info, version info)
3. **Define fields** for each category using EDA standard terminology
4. **Design parsed_fields structure** following global_rules.md Section 2.4.1

Example thought process for "Confirm the netlist/spef version is correct":
- Need netlist info: tool, version, timestamp
- Need SPEF info: standard version, generator, timestamp
- Need file status: to confirm accessibility
- Structure: Group by file type (netlist, spef)


<!-- ========================================
     TASK: Round 2 - Generate Section 1
========================================= -->

<task>
Generate Section 1 (Parsing Logic) of the ItemSpec based on your analysis.
</task>

<!-- ========================================
     CONTEXT: Previous Analysis
========================================= -->

<previous_analysis>
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
</previous_analysis>

<!-- ========================================
     TEMPLATE: Section 1 Structure
========================================= -->

<template_section>
## 1. Parsing Logic

<!-- 
TODO: Define what information to extract based on the description.
Guidelines:
- Identify key entities from the description (e.g., files, versions, configurations)
- List typical fields based on EDA industry standards
- Design parsed_fields structure for checker-specific data
- Reference: global_rules.md Section 2.4.1 for data structure requirements
-->

**Information to Extract**:

### 1.1 {TODO: First Information Category}
<!-- Example: "Netlist File Information", "Clock Configuration", "Timing Constraints" -->
- **Purpose**: {TODO: Why extract this information}
- **Key Fields**:
  - {TODO: Field 1 - describe what it represents}
  - {TODO: Field 2 - describe what it represents}
  - {TODO: Field 3 - describe what it represents}
  - {TODO: Add more fields as needed}

### 1.2 {TODO: Second Information Category}
<!-- Add more subsections (1.3, 1.4, etc.) as needed for different information categories -->
- **Purpose**: {TODO: Why extract this information}
- **Key Fields**:
  - {TODO: Field 1}
  - {TODO: Field 2}
  - {TODO: Field 3}

**Data Structure**: Output structure follows global_rules.md Section 2.4.1 (Required metadata + parsed_fields)

**parsed_fields Example**:
```python
{
  # TODO: Design the structure based on above fields
  # Example structure:
  "{category_1}": {
    "{field_name}": "...",
    "{field_name}": "...",
  },
  "{category_2}": {
    "{field_name}": "...",
    "{field_name}": "...",
  }
}
```

---

</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Parsing Logic section following these requirements:

1. **Information Categories**: Use the categories you identified in the analysis
   - Create subsection 1.1, 1.2, etc. for each category
   - Each subsection should have: Purpose + Key Fields

2. **Field Definitions**: For each field, specify:
   - What it represents (semantic meaning)
   - Data type (string, number, boolean)
   - How to identify it in input files

3. **Data Structure Example**: Provide a complete parsed_fields structure showing:
   - Grouping by category
   - All fields with example values
   - Metadata fields (source_file, line_number, matched_content)

4. **Remove Template Comments**: Delete all `<!-- -->` comments and `{TODO: ...}` markers

5. **Language**: Entire output must be in English

Output the complete Section 1 inside <section1></section1> tags.
</instructions>