# ItemSpec: IMP-10-0-0-00

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

## 3. Waiver Logic

Based on description "Confirm the netlist/spef version is correct", analyze waiver scenarios for validation items:

**Waivable Items and Matching Keywords**:

### 3.1 SPEF File Loading Status (Item 2.2)
- **Waiver scenario**: During synthesis or early design stages, SPEF files are not yet available because parasitic extraction occurs during placement and routing phases. Running timing analysis without parasitics (ideal/zero-parasitic mode) is a valid early-stage verification approach.
- **Typical waiver reason**: "SPEF not required at synthesis stage - pre-layout timing analysis" OR "Zero-parasitic analysis mode for early timing checks"
- **Matching keywords**: 
  - `"SPEF"` + `"synthesis"` (stage-based waiver)
  - `"SPEF"` + `"pre-layout"` (stage-based waiver)
  - `"SPEF"` + `"ideal"` (analysis mode waiver)
  - `"SPEF"` + `"zero parasitic"` (analysis mode waiver)
- **Business justification**: Early design stages focus on logical correctness and rough timing estimates; parasitic data is not available until physical implementation

### 3.2 SPEF Version Completeness (Item 2.4)
- **Waiver scenario**: When SPEF loading is waived (synthesis stage), version validation becomes irrelevant. Additionally, legacy SPEF files from older extraction tools may lack embedded version metadata but are still valid for regression testing against golden references.
- **Typical waiver reason**: "SPEF version check waived - synthesis stage" OR "Legacy SPEF format without version metadata - verified externally"
- **Matching keywords**:
  - `"SPEF"` + `"version"` + `"synthesis"` (stage-based waiver)
  - `"SPEF"` + `"version"` + `"legacy"` (format-based waiver)
  - `"SPEF"` + `"version"` + `"golden"` (regression testing waiver)
  - `"SPEF"` + `"version"` + `"historical"` (regression testing waiver)
- **Business justification**: Version metadata may be unavailable in legacy formats or irrelevant when SPEF itself is not required; external verification processes ensure correctness

### 3.3 Netlist Version Completeness (Item 2.3)
- **Waiver scenario**: Legacy netlist formats (e.g., older Verilog netlists, third-party IP blocks) may not contain embedded tool version information. These netlists are still functionally correct but lack metadata. Additionally, during regression testing, golden netlists from previous releases may have different version formats.
- **Typical waiver reason**: "Legacy netlist format - version verified through external documentation" OR "Golden netlist from regression suite - version tracking external"
- **Matching keywords**:
  - `"netlist"` + `"version"` + `"legacy"` (format-based waiver)
  - `"netlist"` + `"version"` + `"golden"` (regression testing waiver)
  - `"netlist"` + `"version"` + `"third-party"` (IP integration waiver)
  - `"netlist"` + `"version"` + `"vendor IP"` (IP integration waiver)
- **Business justification**: Older netlist formats or third-party IP may not follow current version metadata standards; correctness is verified through alternative means (documentation, regression results)

### 3.4 Tool Version Mismatch
- **Waiver scenario**: Incremental design flows may re-run only parasitic extraction with a newer tool version while keeping the original netlist. This intentional version mismatch is acceptable if tool compatibility has been verified. Similarly, tool upgrades mid-project may result in mixed versions across design artifacts.
- **Typical waiver reason**: "Intentional tool version mismatch - incremental extraction flow with verified compatibility" OR "Tool upgrade mid-project - version compatibility confirmed"
- **Matching keywords**:
  - `"version"` + `"mismatch"` + `"incremental"` (flow-based waiver)
  - `"version"` + `"mismatch"` + `"re-extraction"` (flow-based waiver)
  - `"version"` + `"upgrade"` + `"compatible"` (tool upgrade waiver)
  - `"version"` + `"mixed"` + `"verified"` (tool upgrade waiver)
- **Business justification**: Incremental flows optimize runtime by re-running only necessary steps; tool compatibility testing ensures mixed versions produce valid results

---

**Waiver Modes**:

- **Global Waiver Mode** (`waivers.value = 0`):
  - **Behavior**: All validation items (2.1, 2.2, 2.3, 2.4) are waived regardless of failure reasons
  - **Use cases**: 
    - Early development phases where version tracking is not yet enforced
    - Experimental runs where version correctness is not critical
    - Quick sanity checks bypassing formal validation
  - **Traceability**: Global waiver reason must be documented in `waivers.reason` field

- **Selective Waiver Mode** (`waivers.value > 0`, `waivers.waive_items` configured):
  - **Behavior**: Only validation items matching keywords in `waivers.waive_items` are waived
  - **Matching strategy**: 
    - Keyword matching is case-insensitive
    - Multiple keywords in a waive_item entry use AND logic (all must match)
    - Multiple waive_item entries use OR logic (any entry can trigger waiver)
    - Example: `waive_items = [["SPEF", "synthesis"], ["netlist", "legacy"]]` waives SPEF checks at synthesis OR netlist checks for legacy formats
  - **Application**: Targeted waivers for specific known issues while maintaining validation for other items
  - **Traceability**: Each waived item must have corresponding entry in `waivers.waive_items` with clear keyword justification

**Implementation Guidance**:

- **Pattern Matching Strategy**:
  - Use exact keyword matching for high-confidence waivers (e.g., "synthesis", "legacy")
  - Support wildcard patterns for tool version variations (e.g., "Genus 21.*" matches "Genus 21.1", "Genus 21.2")
  - Consider regex support for complex version patterns if needed by project requirements

- **Linking Waivers to Validation Items**:
  - Item 2.2 (SPEF Loading) ↔ Keywords containing "SPEF" + stage/mode indicators
  - Item 2.4 (SPEF Version) ↔ Keywords containing "SPEF" + "version" + justification
  - Item 2.3 (Netlist Version) ↔ Keywords containing "netlist" + "version" + justification
  - Item 2.1 (Netlist Loading) ↔ Generally not waivable (netlist is mandatory for all flows)

- **Traceability Requirements**:
  - All waivers must include `waivers.reason` field explaining business justification
  - Waiver decisions must be logged with timestamp and approver information
  - Selective waivers must document which specific validation items were waived and why
  - Waiver audit trail should link to design stage, tool versions, and project phase

## 4. Implementation Guide

### 4.1 Item-Specific Implementation Points

**Data Source Inference**:
- Inferred data source: Static Timing Analysis (STA) log files
- Recommended file: `sta_post_syn.log`, `sta_post_pnr.log`, or similar timing analysis logs
- Rationale: STA tools typically log file loading operations and version information when reading netlist and SPEF files

**Information Extraction Methods**:

- **Netlist Loading Status and Version**:
  - **Primary source**: STA log file sections containing netlist reading operations
  - **Keywords to search**: 
    - Loading indicators: `"Reading netlist"`, `"Loading netlist"`, `"Netlist file"`, `"read_verilog"`, `"read_hdl"`
    - Success indicators: `"successfully"`, `"completed"`, `"loaded"`, `"OK"`
    - Failure indicators: `"failed"`, `"error"`, `"not found"`, `"cannot open"`
  - **Version extraction**: 
    - Look for generator comments in netlist file headers (if accessible): `"// Generator:"`, `"// Tool:"`, `"/* Created by"`, `"# Generated by"`
    - Common patterns: `"Genus"`, `"Innovus"`, `"DC Compiler"`, `"RTL Compiler"` followed by version numbers
    - Date patterns: `YYYY-MM-DD`, `DD-MMM-YYYY`, timestamps in ISO format

- **SPEF Loading Status and Version**:
  - **Primary source**: STA log file sections containing SPEF reading operations
  - **Keywords to search**:
    - Loading indicators: `"Reading SPEF"`, `"Loading SPEF"`, `"read_spef"`, `"SPEF file"`, `"Parasitic file"`
    - Success indicators: Same as netlist
    - Failure indicators: Same as netlist
  - **Version extraction**:
    - SPEF file headers (if accessible): `"*SPEF"`, `"*DESIGN"`, `"*DATE"`, `"*VENDOR"`, `"*PROGRAM"`
    - Standard version: `"IEEE 1481-1999"`, `"IEEE 1481-2009"`
    - Generator info: Tool name and version in SPEF comments

**Adaptive Learning Strategy**:
- Do not assume fixed formats; learn from actual file content
  - Different STA tools (PrimeTime, Tempus, ETS) use different log formats
  - Netlist generators (Genus, Innovus, DC) have varying comment styles
  - SPEF formats may include vendor-specific extensions
- Fallback handling:
  - If STA log not found, attempt to read netlist/SPEF files directly for version headers
  - If file loading status cannot be determined from logs, check file existence on filesystem
  - If version information incomplete, mark specific missing fields (e.g., missing date but has tool name)
- Error tolerance:
  - Partial matches are acceptable (e.g., tool name found but version missing → mark as incomplete)
  - Multiple file references in logs → extract all and let Check Logic validate
  - Malformed version strings → preserve original text in `matched_content` for debugging

**Multi-Stage Extraction Pattern**:
1. **Stage 1**: Parse STA log to find file paths and loading status
2. **Stage 2**: If version info not in log, use extracted file paths to read actual netlist/SPEF headers
3. **Stage 3**: Normalize extracted data into structured format with metadata

### 4.2 Special Scenario Handling

#### Scenario 1: SPEF Unavailable During Synthesis Stage
- **Context**: In synthesis flow, SPEF files are not yet generated (require place-and-route completion)
- **Check result**: 
  - SPEF loading status → `missing_items` (Item 2.2 fails)
  - SPEF version completeness → `missing_items` (Item 2.4 fails)
  - Netlist items may still pass
- **Waiver handling**: 
  - If `waive_items` contains keywords: `"synthesis"`, `"SPEF"`, `"pre-layout"`, `"syn stage"`
  - Apply waiver to Items 2.2 and 2.4 → move to `waived` field
  - Final status: PASS (if netlist items pass and SPEF items waived)
- **Implementation note**: Check Logic should clearly separate netlist vs SPEF failures for targeted waiving

#### Scenario 2: Golden Netlist with Historical Timestamps
- **Context**: Using archived "golden" netlists from previous tapeouts for regression testing
- **Check result**:
  - Netlist loading status → PASS (file loads successfully)
  - Netlist version completeness → FAIL if timestamp doesn't match current year/date
  - Pattern matching against `requirements.pattern_items` (e.g., `"2025"`) → `missing_items`
- **Waiver handling**:
  - If `waive_items` contains: `"golden"`, `"historical"`, `"archive"`, `"2024"`, `"2023"` (old years)
  - Apply waiver to timestamp mismatch → move to `waived`
  - Preserve tool name/version validation (should still match requirements)
- **Implementation note**: Consider separating timestamp validation from tool/version validation for granular waiving

#### Scenario 3: Multiple Netlist/SPEF Files Loaded
- **Context**: Hierarchical designs may load multiple netlist files or SPEF files for different blocks
- **Check result**:
  - Parsing Logic extracts multiple entries (one per file)
  - Check Logic validates each entry independently
  - If any file missing version info → partial failure
  - `extra_items` may appear if more files loaded than expected
- **Waiver handling**:
  - If `waive_items` contains specific block names: `"block_A"`, `"test_module_*"`, `"*_wrapper"`
  - Apply waiver to specific blocks' version issues
  - Use wildcard patterns to waive entire categories (e.g., `"test_*"` for all test modules)
- **Implementation note**: Ensure `source_file` metadata clearly identifies which file each validation result corresponds to

#### Scenario 4: Compressed or Encrypted Netlist Files
- **Context**: Netlist files may be gzipped (`.v.gz`) or encrypted (vendor IP)
- **Check result**:
  - STA log shows successful loading, but direct file access for version extraction may fail
  - Parsing Logic should rely on log messages rather than direct file reading
  - If version info only available in file headers → may be incomplete
- **Waiver handling**:
  - If `waive_items` contains: `"encrypted"`, `"IP block"`, `"vendor"`, `"*.gz"`
  - Apply waiver to version completeness checks for these files
  - Loading status should still pass (STA tool can read them)
- **Implementation note**: Prioritize log-based extraction over direct file parsing for robustness

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
- `parsed_fields.netlist.tool_name` (e.g., "Genus", "Innovus", "DC Compiler")
- `parsed_fields.netlist.version` (e.g., "21.1", "19.12-s090_1")
- `parsed_fields.netlist.date` (e.g., "2025-01-05", "05-Jan-2025")
- `parsed_fields.spef.generator_info` (e.g., "Innovus 21.1", "StarRC 2024.06")
- `parsed_fields.spef.date` (e.g., "2025-01-05")

**Step 2: Extract representative keywords**

From the `value` field of parsed objects, extract characteristic keywords:
- **Timestamps**: Year patterns like `"2025"`, `"2024"`, month patterns like `"Jan"`, `"January"`
- **Tool names**: `"Genus"`, `"Innovus"`, `"DC"`, `"RTL Compiler"`, `"PrimeTime"`, `"StarRC"`
- **Version numbers**: Major versions like `"21"`, `"19"`, `"2024"`, full versions like `"21.1"`
- **Status indicators**: `"Success"`, `"Loaded"`, `"Complete"`
- **File types**: `"netlist"`, `"SPEF"`, `"verilog"`, `"parasitic"`

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
    - "SPEF"           # Waive all SPEF-related failures
    - "synthesis"      # Waive failures in synthesis stage

# Scenario 4: Pattern matching - PASS
# IMP-10-0-0-00_pattern_pass.yaml
requirements:
  value: 2  # Two items require pattern matching: netlist version (2.2) and SPEF version (2.4)
  pattern_items:
    - "2025|Genus|Innovus"     # Netlist version: match year OR tool names
    - "2025|StarRC|Innovus"    # SPEF version: match year OR generator tools
waivers:
  value: N/A
  waive_items: []

# Scenario 5: Pattern matching - FAIL + global waiver
# IMP-10-0-0-00_pattern_fail_global.yaml
requirements:
  value: 2
  pattern_items:
    - "2026"           # Future year - will not match current data
    - "2026"           # Future year - will not match current data
waivers:
  value: 0
  waive_items: ["Using historical netlist/SPEF from previous tapeout"]

# Scenario 6: Pattern matching - FAIL + selective waiver
# IMP-10-0-0-00_pattern_fail_selective.yaml
requirements:
  value: 2
  pattern_items:
    - "2026|FutureTool"        # Will not match - triggers missing_items
    - "2026|FutureTool"        # Will not match - triggers missing_items
waivers:
  value: 3
  waive_items:
    - "golden"                 # Waive historical netlist issues
    - "SPEF"                   # Waive SPEF version mismatches
    - "synthesis"              # Waive synthesis stage limitations
```

**Key Principles**:
1. **PASS scenarios**: Use patterns that match actual data values
   - Combine multiple alternatives with `|` for robustness (e.g., `"2025|Genus"` matches if either appears)
   - Include both temporal (year) and tool-specific keywords
2. **FAIL scenarios**: Use patterns that do NOT match actual data
   - Future years (`"2026"`) guaranteed to fail for current data
   - Non-existent tool names (`"FutureTool"`)
3. **OR relationships**: Connect multiple keywords with `|` for higher match probability
   - Example: `"2025|Genus|Innovus"` matches any of the three keywords
4. **waive_items**: Reference matching keywords defined in Section 3
   - Use domain-specific terms: `"synthesis"`, `"SPEF"`, `"golden"`, `"historical"`
   - Use wildcard patterns for flexibility: `"*_wrapper"`, `"test_*"`

**Important**: These are recommendations based on typical Parsing Logic output. Adjust according to actual metadata structure and content observed in your specific design flow.
