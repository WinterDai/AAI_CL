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