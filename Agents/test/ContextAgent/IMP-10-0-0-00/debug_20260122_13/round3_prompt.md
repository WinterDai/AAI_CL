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
- **Purpose**: Extract netlist loading status and version metadata to verify the netlist file was successfully read and contains complete version information
- **Key Fields**:
  - `loaded`: Boolean or status string indicating whether the netlist was successfully loaded (e.g., "Success", "Failed", True/False)
  - `tool_name`: String representing the synthesis/netlist generation tool (e.g., "Genus", "Design Compiler", "Innovus")
  - `version`: String representing the tool version number (e.g., "21.1", "2023.03-SP1")
  - `timestamp`: String representing the netlist generation timestamp (ISO format preferred, or tool-specific format)
  - `source_file`: String containing the path to the netlist file that was parsed (metadata for traceability)

### 1.2 SPEF File Information
- **Purpose**: Extract SPEF loading status and version metadata to verify the parasitic file was successfully read and contains complete version information
- **Key Fields**:
  - `loaded`: Boolean or status string indicating whether the SPEF was successfully loaded (e.g., "Success", "Failed", True/False)
  - `tool_name`: String representing the parasitic extraction tool (e.g., "Innovus", "ICC2", "StarRC", "Quantus")
  - `version`: String representing the tool version number (e.g., "21.1", "2022.06")
  - `timestamp`: String representing the SPEF generation timestamp (ISO format preferred, or tool-specific format)
  - `source_file`: String containing the path to the SPEF file that was parsed (metadata for traceability)

### 1.3 Extraction Metadata
- **Purpose**: Provide traceability information about when and where the parsing occurred
- **Key Fields**:
  - `extraction_timestamp`: String representing when the parsing logic extracted this information (ISO 8601 format recommended)
  - `log_file_path`: String containing the absolute path to the log file or input file being parsed

**Data Structure**: Output structure follows global_rules.md Section 2.4.1 (Required metadata + parsed_fields)

**parsed_fields Example**:
```python
{
  "netlist": {
    "loaded": True,  # or "Success"
    "tool_name": "Genus",
    "version": "21.1-s100",
    "timestamp": "2025-01-15T14:30:00",
    "source_file": "/project/design/netlist/top.v.gz"
  },
  "spef": {
    "loaded": True,  # or "Success"
    "tool_name": "Innovus",
    "version": "21.1",
    "timestamp": "2025-01-15T16:45:00",
    "source_file": "/project/design/spef/top.spef.gz"
  },
  "metadata": {
    "extraction_timestamp": "2025-01-16T09:00:00",
    "log_file_path": "/project/logs/sta_run.log"
  }
}
```

**Complete Output Structure Example**:
```python
[
  {
    "value": "Netlist: Genus 21.1-s100, SPEF: Innovus 21.1",
    "source_file": "/project/logs/sta_run.log",
    "line_number": 42,
    "matched_content": "Reading netlist from /project/design/netlist/top.v.gz (Genus 21.1-s100)",
    "parsed_fields": {
      "netlist": {
        "loaded": True,
        "tool_name": "Genus",
        "version": "21.1-s100",
        "timestamp": "2025-01-15T14:30:00",
        "source_file": "/project/design/netlist/top.v.gz"
      },
      "spef": {
        "loaded": True,
        "tool_name": "Innovus",
        "version": "21.1",
        "timestamp": "2025-01-15T16:45:00",
        "source_file": "/project/design/spef/top.spef.gz"
      },
      "metadata": {
        "extraction_timestamp": "2025-01-16T09:00:00",
        "log_file_path": "/project/logs/sta_run.log"
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
- **netlist**: Gate-level or transistor-level circuit representation file
- **spef**: Standard Parasitic Exchange Format file (contains parasitic RC data)
- **version**: Version information for both files

**Critical interpretation (applying Pattern 1 - Slash Notation):**
- "netlist/spef version" means validate **BOTH** netlist version **AND** spef version
- This is NOT an either/or scenario - both must be verified

## Step 2: Determine Information Categories

To validate "correctness" of netlist/spef versions, we need:

### Category A: File Loading Status
- **Rationale**: Can't verify version if files aren't loaded successfully
- **Data needed**: Whether netlist was read, whether SPEF was read
- **Typical indicators**: "Reading netlist", "Loading SPEF", success/failure messages

### Category B: Version Information
- **Rationale**: Core requirement - actual version data for both files
- **Data needed**: 
  - Netlist: Tool name, version number, generation timestamp
  - SPEF: Tool name, version number, generation timestamp
- **Typical indicators**: File headers, tool output logs

### Category C: Version Consistency/Compatibility
- **Rationale**: "Correct" implies not just existence but also validity
- **Data needed**: 
  - Are versions from compatible tool releases?
  - Are timestamps reasonable (SPEF should be after or same as netlist)?
  - Do versions match expected project standards?

## Step 3: List Required Fields

### For Netlist Version:
- `netlist_loaded`: Boolean or status string
- `netlist_tool_name`: String (e.g., "Genus", "DC", "Innovus")
- `netlist_version`: String (e.g., "21.1", "2023.03")
- `netlist_timestamp`: String (ISO format or tool-specific)
- `netlist_source_file`: String (metadata - which file was parsed)

### For SPEF Version:
- `spef_loaded`: Boolean or status string
- `spef_tool_name`: String (e.g., "Innovus", "ICC2", "StarRC")
- `spef_version`: String
- `spef_timestamp`: String
- `spef_source_file`: String (metadata)

### Additional Metadata:
- `extraction_timestamp`: When this data was extracted
- `log_file_path`: Source of the information

## Step 4: Design Data Structure

**Proposed structure** (grouped by file type for clarity):

```python
parsed_fields = {
    'netlist': {
        'loaded': <bool/string>,
        'tool_name': <string>,
        'version': <string>,
        'timestamp': <string>,
        'source_file': <string>  # metadata
    },
    'spef': {
        'loaded': <bool/string>,
        'tool_name': <string>,
        'version': <string>,
        'timestamp': <string>,
        'source_file': <string>  # metadata
    },
    'metadata': {
        'extraction_timestamp': <string>,
        'log_file_path': <string>
    }
}
```

**Rationale**: 
- Parallel structure for netlist and spef makes validation logic symmetric
- Metadata separated for clarity
- Each file type has complete version information

## Step 5: Identify Validation Items

Based on the description "Confirm the netlist/spef version is correct", validation items should be:

1. **Netlist Loading Status**: Verify netlist was successfully loaded
2. **SPEF Loading Status**: Verify SPEF was successfully loaded
3. **Netlist Version Completeness**: Verify netlist has complete version information (tool_name + version + timestamp)
4. **SPEF Version Completeness**: Verify SPEF has complete version information (tool_name + version + timestamp)

**Total: 4 validation items** (reasonable scope)

**Alternative consideration**: Could combine into 2 items (loading status + version completeness for each file), but 4 items provides better granularity for debugging.

## Step 6: Determine Pattern Matching Needs

### Items Requiring Pattern Matching:
- **Item 3 (Netlist Version Completeness)**: YES
  - Need to match against expected tool names, version formats
  - Pattern: `["Genus 21.1", "DC 2023.03"]` (examples)
  
- **Item 4 (SPEF Version Completeness)**: YES
  - Need to match against expected SPEF generator versions
  - Pattern: `["Innovus 21.1", "StarRC 2022.06"]` (examples)

### Items Using Existence Checks:
- **Item 1 (Netlist Loading)**: Existence check only
  - Just verify `netlist.loaded` is True/Success
  
- **Item 2 (SPEF Loading)**: Existence check only
  - Just verify `spef.loaded` is True/Success

**Checker Type Determination**:
- Pattern search: YES (Items 3-4 need pattern matching)
- Waiver support: Likely YES (see Step 7)
- **Preliminary type: Type 3 (Value Check + Waiver)**

## Step 7: Consider Waiver Scenarios

### Scenario 1: Early Design Stages (Synthesis)
- **Situation**: At synthesis stage, SPEF may not exist yet
- **Legitimacy**: SPEF is generated during P&R, not available pre-placement
- **Waiver**: "SPEF not required at synthesis stage"
- **Keywords**: "synthesis", "pre-layout", "no parasitic"

### Scenario 2: Ideal/Zero-Parasitic Analysis
- **Situation**: Running timing analysis without parasitics (best-case scenario)
- **Legitimacy**: Valid analysis mode for early timing checks
- **Waiver**: "Zero-parasitic analysis mode"
- **Keywords**: "ideal", "zero parasitic", "no RC"

### Scenario 3: Legacy Netlist Format
- **Situation**: Older netlist format without embedded version info
- **Legitimacy**: Historical data, regression testing against golden files
- **Waiver**: "Legacy netlist format - version verified externally"
- **Keywords**: "legacy", "golden", "historical"

### Scenario 4: Version Mismatch (Tool Upgrade)
- **Situation**: SPEF from newer tool version than netlist
- **Legitimacy**: Incremental flow where only extraction was re-run
- **Waiver**: "Intentional tool version mismatch - verified compatible"
- **Keywords**: "incremental", "re-extraction", "tool upgrade"

**Waiver Support Needed**: YES
- Multiple legitimate scenarios where check might fail
- Selective waivers needed (can't waive all version checks globally)

**Final Checker Type: Type 3 (Value Check + Waiver)**

## Summary

**Key Entities**: netlist (both files), spef, version information for each

**Information Categories**: 
1. File loading status
2. Version information (tool, version, timestamp)
3. Completeness validation

**Required Fields**: 10 fields total (5 per file type + metadata)

**Data Structure**: Nested dict grouped by file type

**Validation Items**: 4 items
- 2 existence checks (loading status)
- 2 pattern matches (version completeness)

**Pattern Matching**: Required for version validation

**Waiver Scenarios**: 4 common scenarios identified

**Checker Type**: Type 3 (Value Check + Waiver)
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