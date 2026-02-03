<!-- ========================================
     USER PROMPT: Section 2 Guidance
     (From user_prompt.md)
========================================= -->

### For Section 2 (Check Logic)

1. **Derive validation items** from parsing categories (typically one item per info category)
2. **Define completeness** as "all required fields present"
3. **Determine pattern matching needs**:
   - Version info → needs pattern matching
   - File status → only existence check
4. **Specify pattern_items order** corresponding to items requiring pattern matching

Example for "version is correct":
- Item 1: File loading status (existence check)
- Item 2: Version information (pattern matching)
- pattern_items[0] → Item 2


<!-- ========================================
     TASK: Round 3 - Generate Section 2
========================================= -->

<task>
Generate Section 2 (Check Logic) of the ItemSpec.
</task>

<!-- ========================================
     CONTEXT: Section 1 (Parsing Logic)
========================================= -->

<section1_parsing_logic>
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
</section1_parsing_logic>

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
     TEMPLATE: Section 2 Structure
========================================= -->

<template_section>
## 2. Check Logic

<!-- 
TODO: Define what to verify based on the description.
Guidelines:
- Determine validation items (typically 2-6 items)
- Define completeness criteria for each item
- Decide which items need pattern matching vs. existence checks
- Specify pattern_items correspondence for items requiring pattern matching
- Reference: global_rules.md Section 2.2 for check logic rules
-->

Based on description "{DESCRIPTION}", the following items require validation:

**Validation Items**:

1. **{TODO: First Validation Item Name}**
   <!-- Example: "Netlist File Loading Status", "Clock Frequency Constraints" -->
   - Completeness definition: {TODO: What makes this item complete/valid}
   <!-- Example: "parsed_fields.netlist.file_path exists AND loaded=True" -->

2. **{TODO: Second Validation Item Name}**
   - Completeness definition: {TODO: Define validation criteria}

3. **{TODO: Third Validation Item Name}**
   <!-- Add more items as needed -->
   - Completeness definition: {TODO: Define validation criteria}

**Pattern Matching** (when requirements.pattern_items > 0):
<!-- TODO: Specify which items require pattern matching -->
- Items requiring pattern matching: {TODO: List item numbers, e.g., "Item 2, Item 4"}
- Items with existence check only: {TODO: List item numbers, e.g., "Item 1, Item 3"}

**Pattern Correspondence Order** (follows global_rules.md pattern_items rules):
<!-- TODO: Define the mapping between pattern_items array indices and validation items -->
- `pattern_items[0]` → {TODO: Item number and name}
- `pattern_items[1]` → {TODO: Item number and name}
<!-- Add more mappings as needed for all items requiring pattern matching -->

**Note**: Each pattern_item can use `|` to separate multiple alternative patterns (OR relationship).

---

</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Check Logic section following these requirements:

1. **Validation Items**: Define 2-6 validation items based on your analysis
   - Each item validates one aspect from Parsing Logic
   - Create subsection 2.1, 2.2, etc.

2. **For Each Validation Item**, specify:
   - Item name and description
   - Completeness criteria (what fields must be present)
   - Whether pattern matching is needed
   - Expected behavior on PASS/FAIL

3. **Pattern Matching Correspondence**:
   - If requirements.value > 0, specify which items need pattern matching
   - Define the order correspondence with requirements.pattern_items
   - Items not requiring pattern matching are skipped in pattern_items list

4. **Overall Pass/Fail Logic**:
   - Define when checker returns PASS
   - Define when checker returns FAIL
   - Consider edge cases

5. **Remove Template Comments**: Delete all instructional text

Output the complete Section 2 inside <section2></section2> tags.
</instructions>