# IMP-11-0-0-00: Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly.

## Overview

**Check ID:** IMP-11-0-0-00  
**Description:** Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly.  
**Category:** Power/EMIR Analysis - Database Loading Verification  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log

This checker validates that all required input database files (LEF, LIB, DEF, SPEF, Verilog netlist, view definition) are loaded correctly into Cadence Voltus for power integrity and electromigration analysis. It scans Voltus log files for ERROR messages during database loading operations.

---

## Check Logic

### Input Parsing
Parse Voltus log files line-by-line to track database loading commands and detect errors. The checker monitors five critical loading phases between command markers:

1. **LEF Loading Phase**: Between `<CMD> read_lib -lef` and next `<CMD>`
2. **View Definition Phase**: Between `<CMD> read_view_definition` and next `<CMD>`
3. **Hierarchical DEF Merge Phase**: Between `<CMD> merge_hierarchical_def` and next `<CMD>`
4. **Verilog Netlist Phase**: Between `<CMD> read_verilog` and next `<CMD>`
5. **DEF Loading Phase**: Between `<CMD> read_def` and next `<CMD>`
6. **SPEF Loading Phase**: Between `SPEF files for RC Corner` and next `<CMD>`

**Key Patterns:**
```python
# Pattern 1: Command section markers
cmd_marker = r'^<CMD>\s+(read_lib|read_view_definition|merge_hierarchical_def|read_verilog|read_def|set_\w+)'
# Example: "<CMD> read_lib -lef {/process/tsmcN5/data/stdcell/n5/TSMC/PRTF_Innovus_5nm_014_Cad_V13a/...}"

# Pattern 2: SPEF loading section marker
spef_marker = r'^SPEF files for RC Corner\s+(\S+)'
# Example: "SPEF files for RC Corner cbest_CCbest_m40c"

# Pattern 3: Error detection with Cadence error codes
error_pattern = r'^\*\*ERROR:\s*(?:\(([A-Z_]+-\d+)\))?\s*(.+)|^ERROR:\s+(.+)'
# Example: "**ERROR: (VOLTUS_SCHD-0075) Failed to load library file"
# Example: "ERROR: Cannot read LEF file /path/to/file.lef"

# Pattern 4: Multi-line file list extraction
file_list_pattern = r'read_(?:lib|verilog)\s+\{([^}]+)\}'
# Example: "<CMD> read_verilog {dbs/tv_chip.innovusOUTwD0.enc.dat/tv_chip.v.gz /projects/TC70_LPDDR6_N5P/output/...}"

# Pattern 5: View definition file path
view_def_pattern = r'read_view_definition\s+(\S+)'
# Example: "<CMD> read_view_definition /projects/TC70_LPDDR6_N5P/work/tv_chip/zhaozhao/signoff/signoff-1211b/scr/tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static_viewdefinition.tcl"
```

### Detection Logic
1. **State Tracking**: Maintain current loading phase state (LEF/View/DEF/Verilog/SPEF)
2. **Section Boundary Detection**: 
   - Enter section when `<CMD>` or `SPEF files for RC Corner` detected
   - Exit section when next `<CMD>` detected
3. **Error Collection**: 
   - Capture all ERROR messages within each section
   - Extract error code (if present) and error message
   - Track line number and file path for traceability
4. **Waiver Filtering**:
   - Compare error codes against waiver list (IMPLF-388, IMPDB-5061)
   - Unwaived errors → FAIL
   - All errors waived → PASS
5. **Per-Section Validation**:
   - Check 1: LEF loading section has no unwaived errors
   - Check 2: View definition section has no unwaived errors
   - Check 3: Hierarchical DEF merge section has no unwaived errors
   - Check 4: Verilog netlist section has no unwaived errors
   - Check 5: DEF loading section has no unwaived errors
   - Check 6: SPEF loading section has no unwaived errors
6. **Overall Result**: PASS if all 6 sections have no unwaived errors

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - Existence Check
**Use when:** pattern_items are items that SHOULD EXIST in input files

```
pattern_items: ["item_A", "item_B", "item_C"]
Input file contains: item_A, item_B

Result:
  found_items:   item_A, item_B    ← Pattern found in file
  missing_items: item_C            ← Pattern NOT found in file

PASS: All pattern_items found in file
FAIL: Some pattern_items not found in file
```

### Mode 2: `status_check` - Status Check  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["port_A", "port_B"]
Input file contains: port_A(fixed), port_B(unfixed), port_C(unfixed)

Result:
  found_items:   port_A            ← Pattern matched AND status correct
  missing_items: port_B            ← Pattern matched BUT status wrong
  (port_C not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the STATUS of database loading operations across 6 specific sections. The pattern_items represent the 6 loading phases to monitor (LEF/View/DEF/Verilog/SPEF sections). The checker only reports on these specific sections, not all possible errors in the log. For each section, it checks whether errors exist and whether they are waived. This is a status validation pattern, not an existence check.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All database loading sections completed without unwaived errors"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Database loading section validated successfully (no unwaived errors)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - Section-specific dynamic reasons using callable lambda
# The checker generates specific reasons for each section based on what was loaded:
#   - LEF Loading: "LEF loading completed successfully (125 libraries loaded)"
#   - View Definition: "View definition loaded: tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static_viewdefinition.tcl"
#   - Hierarchical DEF Merge: "Hierarchical DEF merge completed (1 merge operation(s))"
#   - Verilog Netlist: "Verilog netlist loading completed (6 netlist file(s) loaded)"
#   - DEF Loading: "DEF loading completed (1 DEF file(s) loaded)"
#   - SPEF Loading: "SPEF files loaded for RC corner 'cworst_CCworst_125c' (6 file(s))"
found_reason_type1_4 = lambda meta: meta.get('reason', 'Database loading section completed without unwaived errors')

# Type 2/3: Pattern checks - Section-specific dynamic reasons using callable lambda
# Same section-specific reasons as Type 1/4, providing detailed information about what was loaded
found_reason_type2_3 = lambda meta: meta.get('reason', 'Section validated: no ERROR messages found, or all errors matched waiver list')

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Database loading errors detected in one or more sections"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Database loading section failed validation (unwaived errors detected)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Unwaived ERROR messages detected during database loading"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "ERROR detected and not satisfied by waiver list (error code not in waive_items)"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Database loading errors waived per approved exception list"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "ERROR message matched waiver list (error code in approved exceptions)"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Waiver entry not matched to any error in log files"
unused_waiver_reason = "Waiver defined but no corresponding ERROR found in database loading sections"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [section_name]: [found_reason]"
  Example: "- LEF Loading Section: Section validated: no ERROR messages found, or all errors matched waiver list"

ERROR01 (Violation/Fail items):
  Format: "- [section_name]: [error_code] [error_message] (line [N], [filepath])"
  Example: "- SPEF Loading Section: (VOLTUS-1234) Failed to load SPEF file /path/to/file.spef (line 456, tv_chip_static.log)"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-00:
  description: "Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.

**Sample Output (PASS):**
```
Status: PASS
Reason: All 6 database loading sections (LEF/View/DEF/Verilog/SPEF) completed without unwaived errors

Log format (CheckList.rpt):
INFO01:
  - LEF Loading
  - View Definition
  - Hierarchical DEF Merge
  - Verilog Netlist
  - DEF Loading
  - SPEF Loading

Report format (item_id.rpt):
Info Occurrence: 6
1: Info: LEF Loading. In line 0, N/A: LEF loading completed successfully (125 libraries loaded)
2: Info: View Definition. In line 0, N/A: View definition loaded: tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static_viewdefinition.tcl
3: Info: Hierarchical DEF Merge. In line 0, N/A: Hierarchical DEF merge completed (1 merge operation(s))
4: Info: Verilog Netlist. In line 0, N/A: Verilog netlist loading completed (6 netlist file(s) loaded)
5: Info: DEF Loading. In line 0, N/A: DEF loading completed (1 DEF file(s) loaded)
6: Info: SPEF Loading. In line 0, N/A: SPEF files loaded for RC corner 'cworst_CCworst_125c' (6 file(s))
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Unwaived ERROR messages detected during database loading

Log format (CheckList.rpt):
ERROR01:
  - SPEF Loading Section: (VOLTUS-5678) SPEF file not found /path/to/missing.spef

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: SPEF Loading Section. In line 456, tv_chip_static.log: Unwaived ERROR messages detected during database loading
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-00:
  description: "Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Database loading errors are informational only for initial design exploration phase"
      - "Note: SPEF loading failures are expected when running pre-route analysis without extracted parasitics"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: Check is informational only, violations expected/acceptable

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Database loading errors are informational only for initial design exploration phase"
  - "Note: SPEF loading failures are expected when running pre-route analysis without extracted parasitics"
  - LEF Loading
  - View Definition
  - Hierarchical DEF Merge
  - Verilog Netlist
  - SPEF Loading
INFO02:
  - DEF Loading: (IMPDEF-123) DEF file format error

Report format (item_id.rpt):
Info Occurrence: 8
1: Info: Explanation: Database loading errors are informational only for initial design exploration phase. [WAIVED_INFO]
2: Info: Note: SPEF loading failures are expected when running pre-route analysis without extracted parasitics. [WAIVED_INFO]
3: Info: LEF Loading. In line 0, N/A: LEF loading completed successfully (125 libraries loaded)
4: Info: View Definition. In line 0, N/A: View definition loaded: tv_chip_viewdefinition.tcl
5: Info: Hierarchical DEF Merge. In line 0, N/A: Hierarchical DEF merge completed (1 merge operation(s))
6: Info: Verilog Netlist. In line 0, N/A: Verilog netlist loading completed (6 netlist file(s) loaded)
7: Info: SPEF Loading. In line 0, N/A: SPEF files loaded for RC corner 'cworst_CCworst_125c' (6 file(s))
8: Info: DEF Loading. In line 1252, tv_chip_static.log: Unwaived ERROR messages detected during database loading [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-00:
  description: "Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."
  requirements:
    value: 6  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "LEF Loading Section"
      - "View Definition Section"
      - "Hierarchical DEF Merge Section"
      - "Verilog Netlist Section"
      - "DEF Loading Section"
      - "SPEF Loading Section"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items represent the 6 database loading sections to validate
- Each section name corresponds to a command boundary in the log file
- Checker validates that each section completes without unwaived errors

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: Database loading section validated successfully (no unwaived errors)

Log format (CheckList.rpt):
INFO01:
  - LEF Loading Section
  - View Definition Section
  - Hierarchical DEF Merge Section
  - Verilog Netlist Section
  - DEF Loading Section
  - SPEF Loading Section

Report format (item_id.rpt):
Info Occurrence: 6
1: Info: LEF Loading Section. In line 0, N/A: LEF loading completed successfully (125 libraries loaded)
2: Info: View Definition Section. In line 0, N/A: View definition loaded: tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static_viewdefinition.tcl
3: Info: Hierarchical DEF Merge Section. In line 0, N/A: Hierarchical DEF merge completed (1 merge operation(s))
4: Info: Verilog Netlist Section. In line 0, N/A: Verilog netlist loading completed (6 netlist file(s) loaded)
5: Info: DEF Loading Section. In line 0, N/A: DEF loading completed (1 DEF file(s) loaded)
6: Info: SPEF Loading Section. In line 0, N/A: SPEF files loaded for RC corner 'cworst_CCworst_125c' (6 file(s))
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-00:
  description: "Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."
  requirements:
    value: 6  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "LEF Loading Section"
      - "View Definition Section"
      - "Hierarchical DEF Merge Section"
      - "Verilog Netlist Section"
      - "DEF Loading Section"
      - "SPEF Loading Section"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Database loading validation is informational during early design stages"
      - "Note: SPEF and DEF loading errors are expected when running analysis on incomplete databases"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: Pattern check is informational, mismatches expected

**Sample Output (PASS with mismatches):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Database loading validation is informational during early design stages"
  - "Note: SPEF and DEF loading errors are expected when running analysis on incomplete databases"
  - LEF Loading Section
  - View Definition Section
  - Hierarchical DEF Merge Section
INFO02:
  - Verilog Netlist Section: (IMPVLG-456) Verilog syntax error
  - DEF Loading Section: (IMPDEF-789) DEF file missing
  - SPEF Loading Section: (VOLTUS-5678) SPEF file not found

Report format (item_id.rpt):
Info Occurrence: 9
1: Info: Explanation: Database loading validation is informational during early design stages. [WAIVED_INFO]
2: Info: Note: SPEF and DEF loading errors are expected when running analysis on incomplete databases. [WAIVED_INFO]
3: Info: LEF Loading Section. In line 0, N/A: LEF loading completed successfully (125 libraries loaded)
4: Info: View Definition Section. In line 0, N/A: View definition loaded: tv_chip_viewdefinition.tcl
5: Info: Hierarchical DEF Merge Section. In line 0, N/A: Hierarchical DEF merge completed (1 merge operation(s))
6: Info: Verilog Netlist Section. In line 320, tv_chip_static.log: ERROR detected and not satisfied by waiver list (error code not in waive_items) [WAIVED_AS_INFO]
7: Info: DEF Loading Section. In line 450, tv_chip_static.log: ERROR detected and not satisfied by waiver list (error code not in waive_items) [WAIVED_AS_INFO]
8: Info: SPEF Loading Section. In line 580, tv_chip_static.log: ERROR detected and not satisfied by waiver list (error code not in waive_items) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-00:
  description: "Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."
  requirements:
    value: 6  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "LEF Loading Section"
      - "View Definition Section"
      - "Hierarchical DEF Merge Section"
      - "Verilog Netlist Section"
      - "DEF Loading Section"
      - "SPEF Loading Section"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 2
    waive_items:
      - name: "IMPLF-388"
        reason: "Known Voltus issue - LEF layer mapping warning does not affect analysis accuracy"
      - name: "IMPDB-5061"
        reason: "Database version mismatch warning - approved for use with legacy libraries"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items against waive_items
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - View Definition Section
  - Hierarchical DEF Merge Section
  - Verilog Netlist Section
  - DEF Loading Section
  - SPEF Loading Section
  - LEF Loading Section: (IMPLF-388) LEF layer mapping mismatch
WARN01:
  - IMPDB-5061

Report format (item_id.rpt):
Info Occurrence: 6
1: Info: View Definition Section. In line 0, N/A: View definition loaded: tv_chip_viewdefinition.tcl
2: Info: Hierarchical DEF Merge Section. In line 0, N/A: Hierarchical DEF merge completed successfully
3: Info: Verilog Netlist Section. In line 0, N/A: Verilog netlist loading completed (6 netlist file(s) loaded)
4: Info: DEF Loading Section. In line 0, N/A: DEF loading completed successfully
5: Info: SPEF Loading Section. In line 0, N/A: SPEF loading completed successfully
6: Info: LEF Loading Section. In line 78, tv_chip_static.log: ERROR message matched waiver list (error code in approved exceptions): Known Voltus issue - LEF layer mapping warning does not affect analysis accuracy [WAIVER]
Warn Occurrence: 1
1: Warn: IMPDB-5061. In line N/A, N/A: Waiver defined but no corresponding ERROR found in database loading sections: Database version mismatch warning - approved for use with legacy libraries [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-00:
  description: "Confirm input database(netlist/def/lef/spef/lib/pgv/etc) are loaded correctly."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 2
    waive_items:
      - name: "IMPLF-388"
        reason: "Known Voltus issue - LEF layer mapping warning does not affect analysis accuracy"
      - name: "IMPDB-5061"
        reason: "Database version mismatch warning - approved for use with legacy libraries"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - LEF Loading
  - View Definition
  - Hierarchical DEF Merge
  - Verilog Netlist
  - SPEF Loading
  - DEF Loading: (IMPDB-5061) Database version warning
WARN01:
  - IMPLF-388

Report format (item_id.rpt):
Info Occurrence: 6
1: Info: LEF Loading. In line 0, N/A: LEF loading completed successfully (125 libraries loaded)
2: Info: View Definition. In line 0, N/A: View definition loaded: tv_chip_viewdefinition.tcl
3: Info: Hierarchical DEF Merge. In line 0, N/A: Hierarchical DEF merge completed successfully
4: Info: Verilog Netlist. In line 0, N/A: Verilog netlist loading completed (6 netlist file(s) loaded)
5: Info: SPEF Loading. In line 0, N/A: SPEF loading completed successfully
6: Info: DEF Loading. In line 78, tv_chip_static.log: ERROR message matched waiver list (error code in approved exceptions): Database version mismatch warning - approved for use with legacy libraries [WAIVER]
Warn Occurrence: 1
1: Warn: IMPLF-388. In line N/A, N/A: Waiver defined but no corresponding ERROR found in database loading sections: Known Voltus issue - LEF layer mapping warning does not affect analysis accuracy [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-00 --force

# Run individual tests
python IMP-11-0-0-00.py
```

---

## Notes

**Implementation Details:**
- The checker uses state machine logic to track current loading phase
- Multi-line commands (file lists spanning multiple lines) are accumulated until closing brace detected
- Error messages are associated with the most recent loading phase

**Known Limitations:**
- Checker assumes standard Voltus log format with `<CMD>` markers
- Compressed file paths (.gz) are supported but not validated for existence
- Error messages without error codes are captured but may be harder to waive specifically

**Waiver Strategy:**
- Use error codes (e.g., IMPLF-388, IMPDB-5061) for precise waiver matching
- Generic ERROR messages without codes will require manual review
- Unused waivers indicate either log file changes or overly broad waiver definitions

**Edge Cases:**
- If a loading section has no `<CMD>` terminator, errors may be attributed to wrong section
- SPEF loading uses different marker (`SPEF files for RC Corner`) instead of `<CMD>`
- Empty log files or logs without any loading commands will PASS (no errors found)