# ItemSpec: IMP-10-0-0-00

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

## 3. Waiver Logic

Based on description "Confirm the netlist/spef version is correct", analyze waiver scenarios for validation items:

**Waivable Items and Matching Keywords**:

### 3.1 SPEF File Loading Status (Item 2.3)
- **Waiver scenario**: Early design stages where parasitic extraction has not yet been performed
  - Synthesis stage: Only netlist exists, SPEF generation occurs later in P&R flow
  - Pre-layout timing analysis: Using wireload models instead of extracted parasitics
  - Floorplanning stage: Physical design not finalized for extraction
- **Typical waiver reason**: "Pre-extraction design stage - SPEF file not yet available. Using wireload models for timing analysis."
- **Matching keywords**: `"SPEF"`, `"synthesis"`, `"pre-extraction"`, `"wireload"`, `"early-stage"`, `"floorplan"`
- **Business justification**: SPEF files are only generated after place-and-route completion. Earlier design stages legitimately operate without parasitic data.

### 3.2 SPEF Version Completeness (Item 2.4)
- **Waiver scenario**: Legacy or third-party SPEF files with non-standard headers
  - Regression testing: Golden reference files from previous tool versions may lack complete metadata
  - Vendor-provided IP blocks: SPEF files may use proprietary header formats
  - Format conversion: SPEF files converted from other formats may have incomplete version information
- **Typical waiver reason**: "Legacy SPEF file from regression suite - version metadata grandfathered for compatibility"
- **Matching keywords**: `"SPEF"`, `"legacy"`, `"golden"`, `"regression"`, `"vendor"`, `"third-party"`, `"converted"`
- **Business justification**: Historical data used for validation may predate current version tracking requirements. Functional correctness takes precedence over metadata completeness.

### 3.3 Netlist Version Completeness (Item 2.2)
- **Waiver scenario**: Hand-edited or merged netlists lacking tool-generated headers
  - ECO (Engineering Change Order) flows: Manual netlist modifications for bug fixes
  - Netlist merging: Combining multiple sub-netlists may strip original headers
  - Custom scripting: Automated netlist transformations may not preserve version comments
- **Typical waiver reason**: "ECO-modified netlist - original tool version information removed during manual editing"
- **Matching keywords**: `"netlist"`, `"ECO"`, `"manual"`, `"hand-edit"`, `"merged"`, `"custom"`
- **Business justification**: Engineering change orders require direct netlist modification. Version tracking shifts to ECO documentation rather than file headers.

### 3.4 Both Netlist and SPEF Version Information (Items 2.2 and 2.4)
- **Waiver scenario**: Ideal/academic test cases without real tool provenance
  - Benchmark circuits: Standard test designs (ISCAS, ITC) without tool metadata
  - Simulation-only flows: Behavioral models not requiring production tool versions
  - Algorithm validation: Synthetic test cases for checker development
- **Typical waiver reason**: "Academic benchmark circuit - no production tool version information available"
- **Matching keywords**: `"benchmark"`, `"test"`, `"simulation"`, `"academic"`, `"synthetic"`, `"ISCAS"`, `"ITC"`
- **Business justification**: Research and development activities use standardized test cases that lack production tool metadata but serve valid verification purposes.

---

**Waiver Modes**:

### Global Waiver Mode (waivers.value = 0)
- **Behavior**: All validation items (2.1, 2.2, 2.3, 2.4) are waived unconditionally
- **Use cases**:
  - Initial checker deployment: Gradual rollout without breaking existing flows
  - Tool migration periods: Transitioning between EDA tool versions
  - Emergency bypass: Critical tapeout schedules requiring temporary relaxation
- **Application**: Set `waivers.value = 0` in configuration
- **Traceability**: Global waiver reason must be documented in `waivers.waive_reasons[0]`

### Selective Waiver Mode (waivers.value > 0)
- **Behavior**: Only validation items matching keywords in `waivers.waive_items` are waived
- **Matching strategy**:
  - **Exact matching**: Item identifier must exactly match waive_items entry
    - Example: `waive_items = ["2.3"]` waives only SPEF loading status
  - **Keyword matching**: Waive_items entries matched against scenario keywords
    - Example: `waive_items = ["SPEF", "synthesis"]` waives items 2.3 and 2.4 in synthesis context
  - **Wildcard matching**: Use `"*"` for pattern-based matching
    - Example: `waive_items = ["SPEF*"]` waives all SPEF-related items (2.3, 2.4)
- **Application**: 
  - Set `waivers.value = N` where N = number of items in `waivers.waive_items`
  - Populate `waivers.waive_items` with item identifiers or keywords
  - Provide corresponding reasons in `waivers.waive_reasons`
- **Traceability**: Each waived item must have corresponding entry in waive_reasons at same index

**Implementation Guidance**:

1. **Waiver-to-Item Mapping**:
   - Item 2.1 (Netlist loading): Rarely waived - indicates fundamental file access problem
   - Item 2.2 (Netlist version): Waivable via keywords `"netlist"`, `"ECO"`, `"manual"`, `"benchmark"`
   - Item 2.3 (SPEF loading): Waivable via keywords `"SPEF"`, `"synthesis"`, `"pre-extraction"`
   - Item 2.4 (SPEF version): Waivable via keywords `"SPEF"`, `"legacy"`, `"vendor"`

2. **Keyword Matching Logic**:
   ```python
   # Pseudo-code for selective waiver matching
   for validation_item in failed_items:
       item_id = validation_item.id  # e.g., "2.3"
       item_keywords = validation_item.keywords  # e.g., ["SPEF", "loading"]
       
       for waive_entry in waivers.waive_items:
           if waive_entry == item_id:  # Exact match
               apply_waiver(validation_item)
           elif any(keyword in waive_entry for keyword in item_keywords):  # Keyword match
               apply_waiver(validation_item)
   ```

3. **Traceability Requirements**:
   - Each waiver must reference specific validation item(s) by ID
   - Waiver reason must include business justification and approver information
   - Waiver application must be logged with timestamp and user context
   - Audit trail must link waived failures to original check results

4. **Best Practices**:
   - Prefer selective waivers over global waivers for better traceability
   - Document waiver expiration conditions (e.g., "valid until P&R completion")
   - Review and refresh waivers periodically (recommend quarterly)
   - Escalate repeated waivers as potential flow issues requiring root cause analysis

## 4. Implementation Guide

### 4.1 Item-Specific Implementation Points

**Data Source Inference**:
- **Primary data source**: Static Timing Analysis (STA) log files
  - Recommended file patterns: `sta*.log`, `timing*.log`, `primetime*.log`, `tempus*.log`
  - These logs typically contain file loading messages and version information
- **Secondary data source**: Netlist and SPEF file headers
  - Netlist files: `*.v`, `*.v.gz`, `*.vg`
  - SPEF files: `*.spef`, `*.spef.gz`
  - File headers contain generator tool and version metadata
- **Fallback strategy**: If STA logs unavailable, parse netlist/SPEF files directly

**Information Extraction Methods**:

- **File Loading Status**: Extract from STA log file loading messages
  - **Innovus/Tempus**: Search for keywords:
    - `"Reading netlist"`, `"read_netlist"`, `"Netlist loaded"`
    - `"Reading SPEF"`, `"read_spef"`, `"SPEF loaded"`
  - **PrimeTime**: Search for keywords:
    - `"read_verilog"`, `"Reading Verilog netlist"`
    - `"read_parasitics"`, `"Reading SPEF"`
  - **Genus**: Search for keywords:
    - `"read_hdl"`, `"Reading design"`
  - **Extraction pattern**: `(?i)(reading|loaded|read_\w+).*?(netlist|spef|verilog|parasitics)`
  - **Success indicators**: Look for "successfully", "completed", or absence of error messages

- **Netlist Version Information**: Extract from netlist file headers (first 50-100 lines)
  - **Location**: Comment blocks at file beginning
  - **Comment formats**: 
    - Verilog: `//` or `/* ... */`
    - VHDL: `--`
  - **Keywords to search**:
    - Tool name: `"Generator"`, `"Created by"`, `"Tool"`, `"Synthesized by"`
    - Version: `"version"`, `"Version"`, `"Ver"`, `"Release"`
    - Date: `"Date"`, `"Generated on"`, `"Timestamp"`
  - **Parsing pattern**: `(?i)(generator|created by|tool):\s*(\w+)\s+(version\s+)?([0-9.]+)`
  - **Date pattern**: `(?i)(date|generated on):\s*(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})`

- **SPEF Version Information**: Extract from SPEF file headers
  - **Location**: First 20-30 lines of SPEF file
  - **Standard format**: IEEE 1481-1999 or IEEE 1481-2009
  - **Keywords to search**:
    - `*SPEF`, `*DESIGN`, `*DATE`, `*VENDOR`, `*PROGRAM`, `*VERSION`
  - **Parsing pattern**: `\*(\w+)\s+"([^"]+)"`
  - **Version extraction**: Combine `*PROGRAM` and `*VERSION` fields
  - **Date extraction**: `*DATE` field (format varies by tool)

**Adaptive Learning Strategy**:
- **Do not assume fixed formats**: Different EDA tools use different header formats
  - Learn from actual file content structure
  - Use flexible regex patterns with case-insensitive matching
  - Extract all comment blocks and search for version-related keywords
- **Fallback handling**:
  - If netlist file not found in STA log: Search for `*.v` or `*.vg` files in design directory
  - If SPEF file not found: Mark `spef.loaded = False`, set other SPEF fields to `null`
  - If version information incomplete: Mark corresponding completeness fields as `False`
- **Error tolerance**:
  - Compressed files (`.gz`): Decompress before parsing
  - Encoding issues: Try UTF-8, then Latin-1, then ignore errors
  - Malformed headers: Continue parsing, mark fields as missing rather than failing completely
  - Multiple files: If multiple netlist/SPEF files found, extract from all and report in metadata

**Multi-Stage Extraction Strategy**:
1. **Stage 1**: Parse STA log to identify file paths
   - Extract netlist file path from loading messages
   - Extract SPEF file path from loading messages
2. **Stage 2**: Parse identified files for version metadata
   - Open netlist file, read header comments
   - Open SPEF file, read header directives
3. **Stage 3**: Combine information
   - Merge loading status from Stage 1 with version info from Stage 2
   - Populate all required fields in structured output

### 4.2 Special Scenario Handling

#### Scenario 1: SPEF Unavailable During Synthesis Stage
- **Context**: In synthesis flow, parasitic extraction has not yet occurred
- **Check result**: 
  - Item 2.3 (SPEF loading status): `missing_items` (file not found)
  - Item 2.4 (SPEF version completeness): `missing_items` (no data to validate)
- **Waiver handling**: 
  - If `waive_items` contains keywords: `"synthesis"`, `"SPEF"`, `"pre-layout"`, `"wireload"`
  - Apply waiver to Items 2.3 and 2.4 → move to `waived` field
  - Final status: `PASS` (netlist items still validated)
- **Implementation note**: Check STA log for stage indicators like "synthesis mode" or "wireload model"

#### Scenario 2: Golden Netlist with Historical Timestamp
- **Context**: Using archived golden netlist from previous tapeout or reference design
- **Check result**:
  - Item 2.1 (Netlist loading): `found_items` (file exists)
  - Item 2.2 (Netlist version completeness): `missing_items` if timestamp pattern requires current year
- **Waiver handling**:
  - If `waive_items` contains keywords: `"golden"`, `"reference"`, `"historical"`, `"archive"`, or specific old year like `"2023"`
  - Apply waiver to Item 2.2 timestamp validation → move to `waived` field
  - Final status: `PASS` (tool name and version still validated)
- **Implementation note**: Extract year from netlist date field and compare against pattern requirements

#### Scenario 3: Vendor-Specific SPEF Format Extensions
- **Context**: Some EDA tools add proprietary extensions to standard SPEF format
- **Check result**:
  - Item 2.3 (SPEF loading): `found_items` (file loaded)
  - Item 2.4 (SPEF version completeness): May fail if expecting strict IEEE format
- **Waiver handling**:
  - If `waive_items` contains tool-specific keywords: `"Innovus"`, `"Calibre"`, `"StarRC"`, `"vendor extension"`
  - Apply waiver to strict format validation → move to `waived` field
  - Final status: `PASS` (basic version information still validated)
- **Implementation note**: Parse `*PROGRAM` field to identify tool vendor, adjust validation accordingly

#### Scenario 4: Multiple Netlist/SPEF Files in Hierarchical Design
- **Context**: Large designs may have multiple netlist files (top-level + sub-blocks) or multiple SPEF files (per corner)
- **Check result**:
  - Items 2.1-2.4: Multiple entries in `found_items` (one per file)
  - Validation applies to each file independently
- **Waiver handling**:
  - If `waive_items` contains block-specific patterns: `"block_*"`, `"sub_module_*"`, or corner patterns: `"*_slow"`, `"*_fast"`
  - Apply selective waivers to specific files → move matching entries to `waived` field
  - Final status: `PASS` if all required files validated or waived
- **Implementation note**: Preserve file path in metadata to enable pattern matching against specific files

#### Scenario 5: Compressed Files Not Accessible
- **Context**: Netlist/SPEF files compressed (`.gz`) but decompression fails due to corruption or permissions
- **Check result**:
  - Item 2.1 or 2.3 (File loading): `missing_items` (decompression error)
  - Subsequent version checks: `missing_items` (no data available)
- **Waiver handling**:
  - If `waive_items` contains: `"compressed"`, `"decompression error"`, or specific file pattern
  - Apply waiver to affected items → move to `waived` field
  - Final status: `PASS` if waived, otherwise `FAIL`
- **Implementation note**: Catch decompression exceptions, report clear error message with file path

### 4.3 Test Data Generation Guidance

**Note**: The following guidance is for generating test configurations covering all 6 test scenarios.

#### Test Scenario Matrix

Based on requirements.value and waivers.value combinations, generate 6 test scenarios:

| Scenario | requirements.value | waivers.value | Test Objective |
|----------|-------------------|---------------|----------------|
| 1 | N/A | N/A | Basic existence validation |
| 2 | N/A | 0 | Global waiver mechanism |
| 3 | N/A | >0 | Selective waiver matching mechanism |
| 4 | >0 | N/A | Pattern matching - PASS path |
| 5 | >0 | 0 | Pattern matching - FAIL path + global waiver |
| 6 | >0 | >0 | Pattern matching - FAIL path + selective waiver |

#### Inference Strategy

**Step 1: Run Parsing Logic to obtain actual metadata**

After Parsing Logic execution, analyze the actual output structure and content. Expected fields:
- `netlist.tool_name`: e.g., "Genus", "Innovus", "Design Compiler"
- `netlist.version`: e.g., "21.1", "19.12-s090_1"
- `netlist.date`: e.g., "2025-01-15", "Jan 15 2025"
- `spef.generator_info`: e.g., "Innovus 21.1", "StarRC 2023.06"
- `spef.date`: e.g., "2025-01-15"

**Step 2: Extract representative keywords**

From the `value` field of parsed objects, extract characteristic keywords:

- **Tool names**: Extract from `netlist.tool_name` and `spef.generator_info`
  - Examples: `"Genus"`, `"Innovus"`, `"PrimeTime"`, `"StarRC"`, `"Calibre"`
  - Use for pattern matching in Scenarios 4-6

- **Version numbers**: Extract from `netlist.version` and `spef.generator_info`
  - Examples: `"21.1"`, `"19.12"`, `"2023.06"`
  - Use for pattern matching in Scenarios 4-6

- **Timestamps**: Extract year from `netlist.date` and `spef.date`
  - Examples: `"2025"`, `"2024"`, `"2023"`
  - Use for pattern matching in Scenarios 4-6

- **Stage indicators**: Infer from file presence/absence
  - Examples: `"synthesis"` (if SPEF missing), `"post-route"` (if SPEF present)
  - Use for waiver matching in Scenarios 2-3, 5-6

**Step 3: Generate test YAML configurations**

```yaml
# Scenario 1: Basic existence check
# IMP-10-0-0-00_base.yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: N/A
  waive_items: []

# Scenario 2: Global waiver
# IMP-10-0-0-00_global_waiver.yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 0
  waive_items: ["All netlist/SPEF version checks waived for legacy design"]

# Scenario 3: Selective waiver
# IMP-10-0-0-00_selective_waiver.yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 2
  waive_items:
    - "SPEF"           # Waive SPEF-related failures (synthesis stage)
    - "synthesis"      # Waive synthesis-stage specific issues

# Scenario 4: Pattern matching - PASS
# IMP-10-0-0-00_pattern_pass.yaml
requirements:
  value: 2  # Two items require pattern matching: netlist version (2.2) and SPEF version (2.4)
  pattern_items:
    - "Genus|Innovus|2025"     # Netlist version: matches if contains tool name OR current year
    - "Innovus|StarRC|2025"    # SPEF version: matches if contains tool name OR current year
waivers:
  value: N/A
  waive_items: []

# Scenario 5: Pattern matching - FAIL + global waiver
# IMP-10-0-0-00_pattern_fail_global.yaml
requirements:
  value: 2
  pattern_items:
    - "DesignCompiler|2026"    # Netlist version: does NOT match (wrong tool/future year)
    - "PrimeTime|2026"         # SPEF version: does NOT match (wrong tool/future year)
waivers:
  value: 0
  waive_items: ["Version mismatch waived for regression testing"]

# Scenario 6: Pattern matching - FAIL + selective waiver
# IMP-10-0-0-00_pattern_fail_selective.yaml
requirements:
  value: 2
  pattern_items:
    - "DesignCompiler|2026"    # Netlist version: does NOT match
    - "PrimeTime|2026"         # SPEF version: does NOT match
waivers:
  value: 3
  waive_items:
    - "golden"                 # Waive historical netlist timestamp
    - "SPEF"                   # Waive SPEF version mismatch
    - "synthesis"              # Waive synthesis-stage SPEF absence
```

**Key Principles**:
1. **PASS scenarios (Scenario 4)**: Use patterns that match actual data values
   - Extract actual tool names and years from Parsing Logic output
   - Use OR (`|`) to combine multiple valid alternatives
   - Ensure at least one alternative matches for each pattern_item

2. **FAIL scenarios (Scenarios 5-6)**: Use patterns that do NOT match actual data
   - Use wrong tool names (e.g., if actual is "Genus", use "DesignCompiler")
   - Use future years (e.g., "2026" when actual is "2025")
   - Ensure patterns intentionally mismatch to trigger validation failures

3. **OR relationships**: Connect multiple keywords with `|` for higher match probability
   - Example: `"Genus|Innovus|2025"` matches if value contains ANY of these strings
   - Increases robustness across different tool versions and configurations

4. **waive_items**: Reference matching keywords defined in Section 3
   - Use keywords from Section 3.1-3.4 for selective waivers
   - Ensure waiver patterns match the violation descriptions

**Pattern Matching Correspondence**:
- **pattern_items[0]** → Item 2.2 (Netlist version completeness)
  - Matches against `netlist.tool_name`, `netlist.version`, `netlist.date` combined value
- **pattern_items[1]** → Item 2.4 (SPEF version completeness)
  - Matches against `spef.generator_info`, `spef.date` combined value

**Important**: These are recommendations based on expected Parsing Logic output. After actual Parsing Logic execution, adjust patterns according to real metadata structure and content values.
