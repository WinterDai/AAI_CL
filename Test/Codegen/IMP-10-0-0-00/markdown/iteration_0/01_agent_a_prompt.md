# 🔍 Agent A (Parsing Expert) - Prompt Input

**Item:** IMP-10-0-0-00  
**Iteration:** 0  
**Timestamp:** 2026-01-28 14:06:01
**Total Length:** 57,874 characters

---

## 📑 Sections Overview

| Section | Size |
|---------|------|
| Role | 152 chars |
| The 10.2 Hard Constraints (NON-NEGOTIABL | 506 chars |
| Required Output Schema | 399 chars |
| Standardization Layer (MANDATORY) | 89 chars |
| [Locked] Standardization Layer - DO NOT  | 435 chars |
| Input Context | 149 chars |
| Task | 392 chars |
| Output Format | 137 chars |
| ItemSpec Content | 28,410 chars |
| Real Log Snippets | 2 chars |
| Parsed Fields Expected Schema | 26,894 chars |

## 🎯 Key Constraints

### Role

You are the **Parsing Expert Agent** for "Hierarchical Checker Architecture 10.2".
Your task is to write the `extract_context` Python function (Atom A).

### The 10.2 Hard Constraints (NON-NEGOTIABLE)

1. **IO Ban**: You interpret strings only. NO `open()`, `read()`, `write()`, `print()`, or `import os`.
2. **Atom A (Extraction)**:
   - Signature: `def extract_context(text: str, source_file: str) -> List[Dict]`
   - **Type Lock**: You MUST cast extracted values to string: `val = str(item.get('val'))`
   - Schema: Return list of dicts with keys: `value`, `source_file`, `line_number`, `matched_content`, `parsed_fields`

3. **PR5 (No Filtering)**: Extract EVERYTHING that matches. Do NOT filter results.

### Task

1. Analyze the ItemSpec to understand the target fields (tool_name, version, timestamp, etc.)
2. Study the Real Log Snippets to see the actual data format
3. Write regex patterns that work on the ACTUAL data (not verbatim copies of examples)
4. Handle multiple file formats if specified (STA Log, Netlist Header, SPEF Header)
5. Build appropriate `value` string and `parsed_fields` dictionary

## 📄 ItemSpec Content

_item_id: IMP-10-0-0-00
_source_path: C:\Users\wentao\Desktop\AAI\Main_work\ACL\Agentic-AI\Agents\codegen\IMP-10-0-0-00_ItemSpec.md
raw_content: "# ItemSpec: IMP-10-0-0-00\n\n## 1. Parsing Logic\n\n**Information to\
  \ Extract**:\n\n### 1.1 Netlist File Information\n- **Purpose**: Extract version\
  \ metadata from netlist files to verify tool, version, and generation timestamp\
  \ information\n- **Key Fields**:\n  - `loaded`: Boolean indicating whether netlist\
  \ file was successfully accessed and parsed\n  - `tool_name`: String representing\
  \ the EDA tool that generated the netlist (e.g., \"Innovus\", \"Genus\", \"ICC2\"\
  , \"DC\")\n  - `tool_version`: String representing the tool version number (e.g.,\
  \ \"21.1\", \"2023.03-SP2\")\n  - `timestamp`: String representing the generation\
  \ date/time of the netlist\n  - `format`: String representing the netlist format\
  \ (e.g., \"Verilog\", \"VHDL\", \"DEF\")\n\n### 1.2 SPEF File Information\n- **Purpose**:\
  \ Extract version metadata from SPEF (Standard Parasitic Exchange Format) files\
  \ to verify extraction tool, version, standard compliance, and generation timestamp\n\
  - **Key Fields**:\n  - `loaded`: Boolean indicating whether SPEF file was successfully\
  \ accessed and parsed\n  - `tool_name`: String representing the parasitic extraction\
  \ tool (e.g., \"StarRC\", \"Quantus\", \"PrimeTime\")\n  - `tool_version`: String\
  \ representing the extraction tool version number\n  - `timestamp`: String representing\
  \ the generation date/time of the SPEF file\n  - `standard_version`: String representing\
  \ the IEEE standard version (e.g., \"IEEE 1481-1999\", \"IEEE 1481-2009\")\n\n###\
  \ 1.3 File Metadata\n- **Purpose**: Provide traceability information for debugging\
  \ and audit purposes\n- **Key Fields**:\n  - `source_file`: Absolute path to the\
  \ input file where information was extracted\n  - `line_number`: Line number where\
  \ version information was found\n  - `matched_content`: The actual text line that\
  \ was matched during extraction\n\n**Data Structure**: Output structure follows\
  \ global_rules.md Section 2.4.1 (Required metadata + parsed_fields)\n\n**parsed_fields\
  \ Example**:\n```python\n{\n  \"netlist\": {\n    \"loaded\": True,\n    \"tool_name\"\
  : \"Innovus\",\n    \"tool_version\": \"21.10-s080_1\",\n    \"timestamp\": \"2025-01-15\
  \ 14:23:45\",\n    \"format\": \"Verilog\"\n  },\n  \"spef\": {\n    \"loaded\"\
  : True,\n    \"tool_name\": \"StarRC\",\n    \"tool_version\": \"2022.06-SP1\",\n\
  \    \"timestamp\": \"2025-01-15 16:45:12\",\n    \"standard_version\": \"IEEE 1481-2009\"\
  \n  }\n}\n```\n\n**Complete Output Structure Example**:\n```python\n[\n  {\n   \
  \ \"value\": \"Netlist version: Innovus 21.10-s080_1\",\n    \"source_file\": \"\
  /project/design/netlist/top.v.gz\",\n    \"line_number\": 3,\n    \"matched_content\"\
  : \"// Generator: Cadence Innovus 21.10-s080_1\",\n    \"parsed_fields\": {\n  \
  \    \"netlist\": {\n        \"loaded\": True,\n        \"tool_name\": \"Innovus\"\
  ,\n        \"tool_version\": \"21.10-s080_1\",\n        \"timestamp\": \"2025-01-15\
  \ 14:23:45\",\n        \"format\": \"Verilog\"\n      }\n    }\n  },\n  {\n    \"\
  value\": \"SPEF version: IEEE 1481-2009\",\n    \"source_file\": \"/project/design/spef/top.spef.gz\"\
  ,\n    \"line_number\": 1,\n    \"matched_content\": \"*SPEF \\\"IEEE 1481-2009\\\
  \"\",\n    \"parsed_fields\": {\n      \"spef\": {\n        \"loaded\": True,\n\
  \        \"tool_name\": \"StarRC\",\n        \"tool_version\": \"2022.06-SP1\",\n\
  \        \"timestamp\": \"2025-01-15 16:45:12\",\n        \"standard_version\":\
  \ \"IEEE 1481-2009\"\n      }\n    }\n  }\n]\n```\n\n## 2. Check Logic\n\nBased\
  \ on description \"Confirm the netlist/spef version is correct\", the following\
  \ items require validation:\n\n**Validation Items**:\n\n### 2.1 Netlist File Loading\
  \ Status\n- **Purpose**: Verify netlist file was successfully accessed and parsed\n\
  - **Completeness definition**: \n  - `parsed_fields.netlist.loaded == True`\n  -\
  \ File path is accessible and readable\n- **Validation type**: Existence check (Boolean)\n\
  - **PASS condition**: Netlist file successfully loaded\n- **FAIL condition**: File\
  \ not found, access denied, or parsing error\n\n### 2.2 Netlist Version Completeness\n\
  - **Purpose**: Verify netlist contains complete version metadata\n- **Completeness\
  \ definition**:\n  - `parsed_fields.netlist.tool_name` exists and is non-empty\n\
  \  - `parsed_fields.netlist.tool_version` exists and is non-empty\n  - `parsed_fields.netlist.timestamp`\
  \ exists and is non-empty\n  - `parsed_fields.netlist.format` exists and is non-empty\n\
  - **Validation type**: Existence check (Boolean)\n- **PASS condition**: All mandatory\
  \ version fields present and non-empty\n- **FAIL condition**: Any mandatory field\
  \ missing or empty\n\n### 2.3 SPEF File Loading Status\n- **Purpose**: Verify SPEF\
  \ file was successfully accessed and parsed\n- **Completeness definition**:\n  -\
  \ `parsed_fields.spef.loaded == True`\n  - File path is accessible and readable\n\
  - **Validation type**: Existence check (Boolean)\n- **PASS condition**: SPEF file\
  \ successfully loaded\n- **FAIL condition**: File not found, access denied, or parsing\
  \ error\n\n### 2.4 SPEF Version Completeness\n- **Purpose**: Verify SPEF contains\
  \ complete version metadata\n- **Completeness definition**:\n  - `parsed_fields.spef.tool_name`\
  \ exists and is non-empty\n  - `parsed_fields.spef.tool_version` exists and is non-empty\n\
  \  - `parsed_fields.spef.timestamp` exists and is non-empty\n  - `parsed_fields.spef.standard_version`\
  \ exists and is non-empty\n- **Validation type**: Existence check (Boolean)\n- **PASS\
  \ condition**: All mandatory version fields present and non-empty\n- **FAIL condition**:\
  \ Any mandatory field missing or empty\n\n**Pattern Matching**:\n- Items requiring\
  \ pattern matching: None (Type 4 checker - Boolean validation only)\n- Items with\
  \ existence check only: All items (2.1, 2.2, 2.3, 2.4)\n\n**Pattern Correspondence\
  \ Order**: \n- Not applicable (requirements.value = N/A, no pattern_items defined)\n\
  \n**Overall Pass/Fail Logic**:\n- **PASS**: All four validation items pass (both\
  \ netlist and SPEF files loaded successfully with complete version information)\n\
  - **FAIL**: Any validation item fails (file loading failure OR incomplete version\
  \ metadata)\n- **Edge Cases**:\n  - If netlist loads but SPEF fails \u2192 FAIL\
  \ (unless waived)\n  - If version fields exist but contain only whitespace \u2192\
  \ FAIL (treated as empty)\n  - If files are compressed (.gz) \u2192 Must decompress\
  \ before parsing\n  - If multiple version headers exist \u2192 Use first occurrence\n\
  \n**Validation Sequence**:\n1. Check netlist loading status (Item 2.1)\n2. If loaded,\
  \ validate netlist version completeness (Item 2.2)\n3. Check SPEF loading status\
  \ (Item 2.3)\n4. If loaded, validate SPEF version completeness (Item 2.4)\n5. Return\
  \ PASS only if all items pass\n\n## 3. Waiver Logic\n\nBased on description \"Confirm\
  \ the netlist/spef version is correct\", analyze waiver scenarios for validation\
  \ items:\n\n**Waivable Items and Matching Keywords**:\n\n### 3.1 SPEF File Loading\
  \ Status (Item 2.3)\n- **Waiver scenario**: Early design stages where parasitic\
  \ extraction has not yet been performed\n  - Synthesis stage: Only netlist exists,\
  \ SPEF generation occurs later in P&R flow\n  - Pre-layout timing analysis: Using\
  \ wireload models instead of extracted parasitics\n  - Floorplanning stage: Physical\
  \ design not finalized for extraction\n- **Typical waiver reason**: \"Pre-extraction\
  \ design stage - SPEF file not yet available. Using wireload models for timing analysis.\"\
  \n- **Matching keywords**: `\"SPEF\"`, `\"synthesis\"`, `\"pre-extraction\"`, `\"\
  wireload\"`, `\"early-stage\"`, `\"floorplan\"`\n- **Business justification**: SPEF\
  \ files are only generated after place-and-route completion. Earlier design stages\
  \ legitimately operate without parasitic data.\n\n### 3.2 SPEF Version Completeness\
  \ (Item 2.4)\n- **Waiver scenario**: Legacy or third-party SPEF files with non-standard\
  \ headers\n  - Regression testing: Golden reference files from previous tool versions\
  \ may lack complete metadata\n  - Vendor-provided IP blocks: SPEF files may use\
  \ proprietary header formats\n  - Format conversion: SPEF files converted from other\
  \ formats may have incomplete version information\n- **Typical waiver reason**:\
  \ \"Legacy SPEF file from regression suite - version metadata grandfathered for\
  \ compatibility\"\n- **Matching keywords**: `\"SPEF\"`, `\"legacy\"`, `\"golden\"\
  `, `\"regression\"`, `\"vendor\"`, `\"third-party\"`, `\"converted\"`\n- **Business\
  \ justification**: Historical data used for validation may predate current version\
  \ tracking requirements. Functional correctness takes precedence over metadata completeness.\n\
  \n### 3.3 Netlist Version Completeness (Item 2.2)\n- **Waiver scenario**: Hand-edited\
  \ or merged netlists lacking tool-generated headers\n  - ECO (Engineering Change\
  \ Order) flows: Manual netlist modifications for bug fixes\n  - Netlist merging:\
  \ Combining multiple sub-netlists may strip original headers\n  - Custom scripting:\
  \ Automated netlist transformations may not preserve version comments\n- **Typical\
  \ waiver reason**: \"ECO-modified netlist - original tool version information removed\
  \ during manual editing\"\n- **Matching keywords**: `\"netlist\"`, `\"ECO\"`, `\"\
  manual\"`, `\"hand-edit\"`, `\"merged\"`, `\"custom\"`\n- **Business justification**:\
  \ Engineering change orders require direct netlist modification. Version tracking\
  \ shifts to ECO documentation rather than file headers.\n\n### 3.4 Both Netlist\
  \ and SPEF Version Information (Items 2.2 and 2.4)\n- **Waiver scenario**: Ideal/academic\
  \ test cases without real tool provenance\n  - Benchmark circuits: Standard test\
  \ designs (ISCAS, ITC) without tool metadata\n  - Simulation-only flows: Behavioral\
  \ models not requiring production tool versions\n  - Algorithm validation: Synthetic\
  \ test cases for checker development\n- **Typical waiver reason**: \"Academic benchmark\
  \ circuit - no production tool version information available\"\n- **Matching keywords**:\
  \ `\"benchmark\"`, `\"test\"`, `\"simulation\"`, `\"academic\"`, `\"synthetic\"\
  `, `\"ISCAS\"`, `\"ITC\"`\n- **Business justification**: Research and development\
  \ activities use standardized test cases that lack production tool metadata but\
  \ serve valid verification purposes.\n\n---\n\n**Waiver Modes**:\n\n### Global Waiver\
  \ Mode (waivers.value = 0)\n- **Behavior**: All validation items (2.1, 2.2, 2.3,\
  \ 2.4) are waived unconditionally\n- **Use cases**:\n  - Initial checker deployment:\
  \ Gradual rollout without breaking existing flows\n  - Tool migration periods: Transitioning\
  \ between EDA tool versions\n  - Emergency bypass: Critical tapeout schedules requiring\
  \ temporary relaxation\n- **Application**: Set `waivers.value = 0` in configuration\n\
  - **Traceability**: Global waiver reason must be documented in `waivers.waive_reasons[0]`\n\
  \n### Selective Waiver Mode (waivers.value > 0)\n- **Behavior**: Only validation\
  \ items matching keywords in `waivers.waive_items` are waived\n- **Matching strategy**:\n\
  \  - **Exact matching**: Item identifier must exactly match waive_items entry\n\
  \    - Example: `waive_items = [\"2.3\"]` waives only SPEF loading status\n  - **Keyword\
  \ matching**: Waive_items entries matched against scenario keywords\n    - Example:\
  \ `waive_items = [\"SPEF\", \"synthesis\"]` waives items 2.3 and 2.4 in synthesis\
  \ context\n  - **Wildcard matching**: Use `\"*\"` for pattern-based matching\n \
  \   - Example: `waive_items = [\"SPEF*\"]` waives all SPEF-related items (2.3, 2.4)\n\
  - **Application**: \n  - Set `waivers.value = N` where N = number of items in `waivers.waive_items`\n\
  \  - Populate `waivers.waive_items` with item identifiers or keywords\n  - Provide\
  \ corresponding reasons in `waivers.waive_reasons`\n- **Traceability**: Each waived\
  \ item must have corresponding entry in waive_reasons at same index\n\n**Implementation\
  \ Guidance**:\n\n1. **Waiver-to-Item Mapping**:\n   - Item 2.1 (Netlist loading):\
  \ Rarely waived - indicates fundamental file access problem\n   - Item 2.2 (Netlist\
  \ version): Waivable via keywords `\"netlist\"`, `\"ECO\"`, `\"manual\"`, `\"benchmark\"\
  `\n   - Item 2.3 (SPEF loading): Waivable via keywords `\"SPEF\"`, `\"synthesis\"\
  `, `\"pre-extraction\"`\n   - Item 2.4 (SPEF version): Waivable via keywords `\"\
  SPEF\"`, `\"legacy\"`, `\"vendor\"`\n\n2. **Keyword Matching Logic**:\n   ```python\n\
  \   # Pseudo-code for selective waiver matching\n   for validation_item in failed_items:\n\
  \       item_id = validation_item.id  # e.g., \"2.3\"\n       item_keywords = validation_item.keywords\
  \  # e.g., [\"SPEF\", \"loading\"]\n       \n       for waive_entry in waivers.waive_items:\n\
  \           if waive_entry == item_id:  # Exact match\n               apply_waiver(validation_item)\n\
  \           elif any(keyword in waive_entry for keyword in item_keywords):  # Keyword\
  \ match\n               apply_waiver(validation_item)\n   ```\n\n3. **Traceability\
  \ Requirements**:\n   - Each waiver must reference specific validation item(s) by\
  \ ID\n   - Waiver reason must include business justification and approver information\n\
  \   - Waiver application must be logged with timestamp and user context\n   - Audit\
  \ trail must link waived failures to original check results\n\n4. **Best Practices**:\n\
  \   - Prefer selective waivers over global waivers for better traceability\n   -\
  \ Document waiver expiration conditions (e.g., \"valid until P&R completion\")\n\
  \   - Review and refresh waivers periodically (recommend quarterly)\n   - Escalate\
  \ repeated waivers as potential flow issues requiring root cause analysis\n\n##\
  \ 4. Implementation Guide\n\n### 4.1 Item-Specific Implementation Points\n\n**Data\
  \ Source Inference**:\n- **Primary data source**: Static Timing Analysis (STA) log\
  \ files\n  - Recommended file patterns: `sta*.log`, `timing*.log`, `primetime*.log`,\
  \ `tempus*.log`\n  - These logs typically contain file loading messages and version\
  \ information\n- **Secondary data source**: Netlist and SPEF file headers\n  - Netlist\
  \ files: `*.v`, `*.v.gz`, `*.vg`\n  - SPEF files: `*.spef`, `*.spef.gz`\n  - File\
  \ headers contain generator tool and version metadata\n- **Fallback strategy**:\
  \ If STA logs unavailable, parse netlist/SPEF files directly\n\n**Information Extraction\
  \ Methods**:\n\n- **File Loading Status**: Extract from STA log file loading messages\n\
  \  - **Innovus/Tempus**: Search for keywords:\n    - `\"Reading netlist\"`, `\"\
  read_netlist\"`, `\"Netlist loaded\"`\n    - `\"Reading SPEF\"`, `\"read_spef\"\
  `, `\"SPEF loaded\"`\n  - **PrimeTime**: Search for keywords:\n    - `\"read_verilog\"\
  `, `\"Reading Verilog netlist\"`\n    - `\"read_parasitics\"`, `\"Reading SPEF\"\
  `\n  - **Genus**: Search for keywords:\n    - `\"read_hdl\"`, `\"Reading design\"\
  `\n  - **Extraction pattern**: `(?i)(reading|loaded|read_\\w+).*?(netlist|spef|verilog|parasitics)`\n\
  \  - **Success indicators**: Look for \"successfully\", \"completed\", or absence\
  \ of error messages\n\n- **Netlist Version Information**: Extract from netlist file\
  \ headers (first 50-100 lines)\n  - **Location**: Comment blocks at file beginning\n\
  \  - **Comment formats**: \n    - Verilog: `//` or `/* ... */`\n    - VHDL: `--`\n\
  \  - **Keywords to search**:\n    - Tool name: `\"Generator\"`, `\"Created by\"\
  `, `\"Tool\"`, `\"Synthesized by\"`\n    - Version: `\"version\"`, `\"Version\"\
  `, `\"Ver\"`, `\"Release\"`\n    - Date: `\"Date\"`, `\"Generated on\"`, `\"Timestamp\"\
  `\n  - **Parsing pattern**: `(?i)(generator|created by|tool):\\s*(\\w+)\\s+(version\\\
  s+)?([0-9.]+)`\n  - **Date pattern**: `(?i)(date|generated on):\\s*(\\d{4}[-/]\\\
  d{2}[-/]\\d{2}|\\d{2}[-/]\\d{2}[-/]\\d{4})`\n\n- **SPEF Version Information**: Extract\
  \ from SPEF file headers\n  - **Location**: First 20-30 lines of SPEF file\n  -\
  \ **Standard format**: IEEE 1481-1999 or IEEE 1481-2009\n  - **Keywords to search**:\n\
  \    - `*SPEF`, `*DESIGN`, `*DATE`, `*VENDOR`, `*PROGRAM`, `*VERSION`\n  - **Parsing\
  \ pattern**: `\\*(\\w+)\\s+\"([^\"]+)\"`\n  - **Version extraction**: Combine `*PROGRAM`\
  \ and `*VERSION` fields\n  - **Date extraction**: `*DATE` field (format varies by\
  \ tool)\n\n**Adaptive Learning Strategy**:\n- **Do not assume fixed formats**: Different\
  \ EDA tools use different header formats\n  - Learn from actual file content structure\n\
  \  - Use flexible regex patterns with case-insensitive matching\n  - Extract all\
  \ comment blocks and search for version-related keywords\n- **Fallback handling**:\n\
  \  - If netlist file not found in STA log: Search for `*.v` or `*.vg` files in design\
  \ directory\n  - If SPEF file not found: Mark `spef.loaded = False`, set other SPEF\
  \ fields to `null`\n  - If version information incomplete: Mark corresponding completeness\
  \ fields as `False`\n- **Error tolerance**:\n  - Compressed files (`.gz`): Decompress\
  \ before parsing\n  - Encoding issues: Try UTF-8, then Latin-1, then ignore errors\n\
  \  - Malformed headers: Continue parsing, mark fields as missing rather than failing\
  \ completely\n  - Multiple files: If multiple netlist/SPEF files found, extract\
  \ from all and report in metadata\n\n**Multi-Stage Extraction Strategy**:\n1. **Stage\
  \ 1**: Parse STA log to identify file paths\n   - Extract netlist file path from\
  \ loading messages\n   - Extract SPEF file path from loading messages\n2. **Stage\
  \ 2**: Parse identified files for version metadata\n   - Open netlist file, read\
  \ header comments\n   - Open SPEF file, read header directives\n3. **Stage 3**:\
  \ Combine information\n   - Merge loading status from Stage 1 with version info\
  \ from Stage 2\n   - Populate all required fields in structured output\n\n### 4.2\
  \ Special Scenario Handling\n\n#### Scenario 1: SPEF Unavailable During Synthesis\
  \ Stage\n- **Context**: In synthesis flow, parasitic extraction has not yet occurred\n\
  - **Check result**: \n  - Item 2.3 (SPEF loading status): `missing_items` (file\
  \ not found)\n  - Item 2.4 (SPEF version completeness): `missing_items` (no data\
  \ to validate)\n- **Waiver handling**: \n  - If `waive_items` contains keywords:\
  \ `\"synthesis\"`, `\"SPEF\"`, `\"pre-layout\"`, `\"wireload\"`\n  - Apply waiver\
  \ to Items 2.3 and 2.4 \u2192 move to `waived` field\n  - Final status: `PASS` (netlist\
  \ items still validated)\n- **Implementation note**: Check STA log for stage indicators\
  \ like \"synthesis mode\" or \"wireload model\"\n\n#### Scenario 2: Golden Netlist\
  \ with Historical Timestamp\n- **Context**: Using archived golden netlist from previous\
  \ tapeout or reference design\n- **Check result**:\n  - Item 2.1 (Netlist loading):\
  \ `found_items` (file exists)\n  - Item 2.2 (Netlist version completeness): `missing_items`\
  \ if timestamp pattern requires current year\n- **Waiver handling**:\n  - If `waive_items`\
  \ contains keywords: `\"golden\"`, `\"reference\"`, `\"historical\"`, `\"archive\"\
  `, or specific old year like `\"2023\"`\n  - Apply waiver to Item 2.2 timestamp\
  \ validation \u2192 move to `waived` field\n  - Final status: `PASS` (tool name\
  \ and version still validated)\n- **Implementation note**: Extract year from netlist\
  \ date field and compare against pattern requirements\n\n#### Scenario 3: Vendor-Specific\
  \ SPEF Format Extensions\n- **Context**: Some EDA tools add proprietary extensions\
  \ to standard SPEF format\n- **Check result**:\n  - Item 2.3 (SPEF loading): `found_items`\
  \ (file loaded)\n  - Item 2.4 (SPEF version completeness): May fail if expecting\
  \ strict IEEE format\n- **Waiver handling**:\n  - If `waive_items` contains tool-specific\
  \ keywords: `\"Innovus\"`, `\"Calibre\"`, `\"StarRC\"`, `\"vendor extension\"`\n\
  \  - Apply waiver to strict format validation \u2192 move to `waived` field\n  -\
  \ Final status: `PASS` (basic version information still validated)\n- **Implementation\
  \ note**: Parse `*PROGRAM` field to identify tool vendor, adjust validation accordingly\n\
  \n#### Scenario 4: Multiple Netlist/SPEF Files in Hierarchical Design\n- **Context**:\
  \ Large designs may have multiple netlist files (top-level + sub-blocks) or multiple\
  \ SPEF files (per corner)\n- **Check result**:\n  - Items 2.1-2.4: Multiple entries\
  \ in `found_items` (one per file)\n  - Validation applies to each file independently\n\
  - **Waiver handling**:\n  - If `waive_items` contains block-specific patterns: `\"\
  block_*\"`, `\"sub_module_*\"`, or corner patterns: `\"*_slow\"`, `\"*_fast\"`\n\
  \  - Apply selective waivers to specific files \u2192 move matching entries to `waived`\
  \ field\n  - Final status: `PASS` if all required files validated or waived\n- **Implementation\
  \ note**: Preserve file path in metadata to enable pattern matching against specific\
  \ files\n\n#### Scenario 5: Compressed Files Not Accessible\n- **Context**: Netlist/SPEF\
  \ files compressed (`.gz`) but decompression fails due to corruption or permissions\n\
  - **Check result**:\n  - Item 2.1 or 2.3 (File loading): `missing_items` (decompression\
  \ error)\n  - Subsequent version checks: `missing_items` (no data available)\n-\
  \ **Waiver handling**:\n  - If `waive_items` contains: `\"compressed\"`, `\"decompression\
  \ error\"`, or specific file pattern\n  - Apply waiver to affected items \u2192\
  \ move to `waived` field\n  - Final status: `PASS` if waived, otherwise `FAIL`\n\
  - **Implementation note**: Catch decompression exceptions, report clear error message\
  \ with file path\n\n### 4.3 Test Data Generation Guidance\n\n**Note**: The following\
  \ guidance is for generating test configurations covering all 6 test scenarios.\n\
  \n#### Test Scenario Matrix\n\nBased on requirements.value and waivers.value combinations,\
  \ generate 6 test scenarios:\n\n| Scenario | requirements.value | waivers.value\
  \ | Test Objective |\n|----------|-------------------|---------------|----------------|\n\
  | 1 | N/A | N/A | Basic existence validation |\n| 2 | N/A | 0 | Global waiver mechanism\
  \ |\n| 3 | N/A | >0 | Selective waiver matching mechanism |\n| 4 | >0 | N/A | Pattern\
  \ matching - PASS path |\n| 5 | >0 | 0 | Pattern matching - FAIL path + global waiver\
  \ |\n| 6 | >0 | >0 | Pattern matching - FAIL path + selective waiver |\n\n#### Inference\
  \ Strategy\n\n**Step 1: Run Parsing Logic to obtain actual metadata**\n\nAfter Parsing\
  \ Logic execution, analyze the actual output structure and content. Expected fields:\n\
  - `netlist.tool_name`: e.g., \"Genus\", \"Innovus\", \"Design Compiler\"\n- `netlist.version`:\
  \ e.g., \"21.1\", \"19.12-s090_1\"\n- `netlist.date`: e.g., \"2025-01-15\", \"Jan\
  \ 15 2025\"\n- `spef.generator_info`: e.g., \"Innovus 21.1\", \"StarRC 2023.06\"\
  \n- `spef.date`: e.g., \"2025-01-15\"\n\n**Step 2: Extract representative keywords**\n\
  \nFrom the `value` field of parsed objects, extract characteristic keywords:\n\n\
  - **Tool names**: Extract from `netlist.tool_name` and `spef.generator_info`\n \
  \ - Examples: `\"Genus\"`, `\"Innovus\"`, `\"PrimeTime\"`, `\"StarRC\"`, `\"Calibre\"\
  `\n  - Use for pattern matching in Scenarios 4-6\n\n- **Version numbers**: Extract\
  \ from `netlist.version` and `spef.generator_info`\n  - Examples: `\"21.1\"`, `\"\
  19.12\"`, `\"2023.06\"`\n  - Use for pattern matching in Scenarios 4-6\n\n- **Timestamps**:\
  \ Extract year from `netlist.date` and `spef.date`\n  - Examples: `\"2025\"`, `\"\
  2024\"`, `\"2023\"`\n  - Use for pattern matching in Scenarios 4-6\n\n- **Stage\
  \ indicators**: Infer from file presence/absence\n  - Examples: `\"synthesis\"`\
  \ (if SPEF missing), `\"post-route\"` (if SPEF present)\n  - Use for waiver matching\
  \ in Scenarios 2-3, 5-6\n\n**Step 3: Generate test YAML configurations**\n\n```yaml\n\
  # Scenario 1: Basic existence check\n# IMP-10-0-0-00_base.yaml\nrequirements:\n\
  \  value: N/A\n  pattern_items: []\nwaivers:\n  value: N/A\n  waive_items: []\n\n\
  # Scenario 2: Global waiver\n# IMP-10-0-0-00_global_waiver.yaml\nrequirements:\n\
  \  value: N/A\n  pattern_items: []\nwaivers:\n  value: 0\n  waive_items: [\"All\
  \ netlist/SPEF version checks waived for legacy design\"]\n\n# Scenario 3: Selective\
  \ waiver\n# IMP-10-0-0-00_selective_waiver.yaml\nrequirements:\n  value: N/A\n \
  \ pattern_items: []\nwaivers:\n  value: 2\n  waive_items:\n    - \"SPEF\"      \
  \     # Waive SPEF-related failures (synthesis stage)\n    - \"synthesis\"     \
  \ # Waive synthesis-stage specific issues\n\n# Scenario 4: Pattern matching - PASS\n\
  # IMP-10-0-0-00_pattern_pass.yaml\nrequirements:\n  value: 2  # Two items require\
  \ pattern matching: netlist version (2.2) and SPEF version (2.4)\n  pattern_items:\n\
  \    - \"Genus|Innovus|2025\"     # Netlist version: matches if contains tool name\
  \ OR current year\n    - \"Innovus|StarRC|2025\"    # SPEF version: matches if contains\
  \ tool name OR current year\nwaivers:\n  value: N/A\n  waive_items: []\n\n# Scenario\
  \ 5: Pattern matching - FAIL + global waiver\n# IMP-10-0-0-00_pattern_fail_global.yaml\n\
  requirements:\n  value: 2\n  pattern_items:\n    - \"DesignCompiler|2026\"    #\
  \ Netlist version: does NOT match (wrong tool/future year)\n    - \"PrimeTime|2026\"\
  \         # SPEF version: does NOT match (wrong tool/future year)\nwaivers:\n  value:\
  \ 0\n  waive_items: [\"Version mismatch waived for regression testing\"]\n\n# Scenario\
  \ 6: Pattern matching - FAIL + selective waiver\n# IMP-10-0-0-00_pattern_fail_selective.yaml\n\
  requirements:\n  value: 2\n  pattern_items:\n    - \"DesignCompiler|2026\"    #\
  \ Netlist version: does NOT match\n    - \"PrimeTime|2026\"         # SPEF version:\
  \ does NOT match\nwaivers:\n  value: 3\n  waive_items:\n    - \"golden\"       \
  \          # Waive historical netlist timestamp\n    - \"SPEF\"                \
  \   # Waive SPEF version mismatch\n    - \"synthesis\"              # Waive synthesis-stage\
  \ SPEF absence\n```\n\n**Key Principles**:\n1. **PASS scenarios (Scenario 4)**:\
  \ Use patterns that match actual data values\n   - Extract actual tool names and\
  \ years from Parsing Logic output\n   - Use OR (`|`) to combine multiple valid alternatives\n\
  \   - Ensure at least one alternative matches for each pattern_item\n\n2. **FAIL\
  \ scenarios (Scenarios 5-6)**: Use patterns that do NOT match actual data\n   -\
  \ Use wrong tool names (e.g., if actual is \"Genus\", use \"DesignCompiler\")\n\
  \   - Use future years (e.g., \"2026\" when actual is \"2025\")\n   - Ensure patterns\
  \ intentionally mismatch to trigger validation failures\n\n3. **OR relationships**:\
  \ Connect multiple keywords with `|` for higher match probability\n   - Example:\
  \ `\"Genus|Innovus|2025\"` matches if value contains ANY of these strings\n   -\
  \ Increases robustness across different tool versions and configurations\n\n4. **waive_items**:\
  \ Reference matching keywords defined in Section 3\n   - Use keywords from Section\
  \ 3.1-3.4 for selective waivers\n   - Ensure waiver patterns match the violation\
  \ descriptions\n\n**Pattern Matching Correspondence**:\n- **pattern_items[0]** \u2192\
  \ Item 2.2 (Netlist version completeness)\n  - Matches against `netlist.tool_name`,\
  \ `netlist.version`, `netlist.date` combined value\n- **pattern_items[1]** \u2192\
  \ Item 2.4 (SPEF version completeness)\n  - Matches against `spef.generator_info`,\
  \ `spef.date` combined value\n\n**Important**: These are recommendations based on\
  \ expected Parsing Logic output. After actual Parsing Logic execution, adjust patterns\
  \ according to real metadata structure and content values.\n"

## 📋 Log Snippets

*No log snippets provided*
