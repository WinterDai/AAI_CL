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

Section 2 (Check Logic):
## 2. Check Logic

Based on description "Confirm the netlist/spef version is correct", the following items require validation:

**Validation Items**:

### 2.1 Netlist Loading Status
- **Purpose**: Verify the netlist file was successfully loaded before validating version information
- **Completeness definition**: 
  - `parsed_fields.netlist.loaded` exists AND equals `True` (or "Success")
  - `parsed_fields.netlist.source_file` exists (confirms which file was loaded)
- **Validation type**: Existence check only (no pattern matching required)
- **Pass condition**: Netlist loaded successfully
- **Fail condition**: Netlist loading failed or status is missing

### 2.2 SPEF Loading Status
- **Purpose**: Verify the SPEF file was successfully loaded before validating version information
- **Completeness definition**: 
  - `parsed_fields.spef.loaded` exists AND equals `True` (or "Success")
  - `parsed_fields.spef.source_file` exists (confirms which file was loaded)
- **Validation type**: Existence check only (no pattern matching required)
- **Pass condition**: SPEF loaded successfully
- **Fail condition**: SPEF loading failed or status is missing

### 2.3 Netlist Version Completeness
- **Purpose**: Verify the netlist contains complete and valid version information
- **Completeness definition**: 
  - `parsed_fields.netlist.tool_name` exists and is non-empty
  - `parsed_fields.netlist.version` exists and is non-empty
  - `parsed_fields.netlist.timestamp` exists and is non-empty
  - Combined version string matches expected pattern from `requirements.pattern_items[0]`
- **Validation type**: Pattern matching required
- **Pass condition**: All version fields present AND match expected pattern
- **Fail condition**: Missing version fields OR version pattern mismatch

### 2.4 SPEF Version Completeness
- **Purpose**: Verify the SPEF contains complete and valid version information
- **Completeness definition**: 
  - `parsed_fields.spef.tool_name` exists and is non-empty
  - `parsed_fields.spef.version` exists and is non-empty
  - `parsed_fields.spef.timestamp` exists and is non-empty
  - Combined version string matches expected pattern from `requirements.pattern_items[1]`
- **Validation type**: Pattern matching required
- **Pass condition**: All version fields present AND match expected pattern
- **Fail condition**: Missing version fields OR version pattern mismatch

**Pattern Matching**:
- Items requiring pattern matching: **Item 2.3, Item 2.4**
- Items with existence check only: **Item 2.1, Item 2.2**

**Pattern Correspondence Order**:
- `pattern_items[0]` → **Item 2.3 (Netlist Version Completeness)**
  - Pattern format: `"<tool_name> <version>"` (e.g., `"Genus 21.1|DC 2023.03"`)
  - Multiple alternatives separated by `|` for OR relationship
- `pattern_items[1]` → **Item 2.4 (SPEF Version Completeness)**
  - Pattern format: `"<tool_name> <version>"` (e.g., `"Innovus 21.1|StarRC 2022.06|ICC2 2023.03"`)
  - Multiple alternatives separated by `|` for OR relationship

**Overall Pass/Fail Logic**:
- **PASS**: All four validation items pass
  - Both files loaded successfully (Items 2.1, 2.2)
  - Both files have complete version information matching expected patterns (Items 2.3, 2.4)
- **FAIL**: Any validation item fails
  - File loading failure → Cannot proceed with version validation
  - Incomplete version information → Missing required metadata
  - Version pattern mismatch → Unexpected tool or version detected
- **Edge Cases**:
  - If `requirements.value = 0` (waiver mode), failed items may be waived based on `waivers.waive_items` configuration
  - If netlist loads but SPEF fails, Items 2.1 and 2.3 may still pass (partial success scenario)
  - Empty or malformed version strings are treated as FAIL for completeness items
</previous_sections>

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