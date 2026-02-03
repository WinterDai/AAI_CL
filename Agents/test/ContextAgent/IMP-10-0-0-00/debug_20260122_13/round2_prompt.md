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