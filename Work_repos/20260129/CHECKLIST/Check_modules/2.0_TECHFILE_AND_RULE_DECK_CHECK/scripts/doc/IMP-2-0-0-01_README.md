# IMP-2-0-0-01: List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map

## Overview

**Check ID:** IMP-2-0-0-01
**Description:** List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map
**Category:** TECHFILE_AND_RULE_DECK_CHECK
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv

This checker extracts and validates the GDS stream-out map file used during Innovus implementation. The map file defines layer mapping rules for converting the design database to GDSII format. The checker parses the Innovus log to identify the gdsout map file path from the `streamOut` command and reports the map filename for verification.

---

## Check Logic

### Input Parsing

**Step 1: Parse Innovus log file**

- Search for lines containing `streamOut` command with `*PRTF*gdsout*.map` pattern
- Extract the absolute path to the gdsout map file after `streamOut` keyword
- Store the extracted path in `gds_map` variable

**Parsing Strategy:**

- `gds_map` is already an absolute path in the log file
- Extract the full path directly from the `streamOut` command line
- The map file path appears after the `streamOut` keyword and contains both "PRTF" and "gdsout" substrings

**Key Patterns:**

```python
# Pattern 1: Extract GDS map file from streamOut command
pattern1 = r'\[.*\]streamOut\s+.*PRTF.*gdsout.*\.map'
# Example: "[2024-01-15 10:30:45] streamOut -mapFile /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map -outputMacros -stripes 1 -units 1000 -mode ALL CDN_204H_cdn_hs_phy_data_slice.gds"
```

### Detection Logic

**Type 1/4 (No pattern_items):**

1. Parse the input log file line by line
2. Search for lines matching the streamOut pattern with PRTF*gdsout*.map
3. Extract the gds_map file path from the matched line
4. If `gds_map` is successfully extracted and the value exists → **PASS**
5. If `gds_map` cannot be extracted or is empty → **FAIL**

**Type 2/3 (With pattern_items):**

1. Parse the input log file and extract `gds_map` as described above
2. Store `pattern_item[0]` into `golden_gdsmap` (expected map file path)
3. Compare extracted `gds_map` with `golden_gdsmap`:
   - If `gds_map` == `golden_gdsmap` → **PASS**
   - If `gds_map` != `golden_gdsmap` → **FAIL**

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

**Rationale:** This checker validates the gdsout map file path against expected golden values (pattern_items). It only reports whether the extracted map file matches the expected configuration, not whether arbitrary map files exist. The check focuses on validating the specific map file used in the streamOut operation matches the project's expected configuration.

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
item_desc = "List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "GDS stream-out map file found in Innovus log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "GDS stream-out map file matched expected configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "GDS map file path successfully extracted from streamOut command"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "GDS map file path matched golden configuration and validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "GDS stream-out map file not found in Innovus log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "GDS stream-out map file does not match expected configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "No streamOut command with PRTF gdsout map file found in log"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "GDS map file path does not match golden configuration - expected different map file"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "GDS map file mismatch waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "GDS map file mismatch waived - alternative map file approved for this design"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entry for GDS map file"
unused_waiver_reason = "Waiver not matched - specified map file not found in streamOut command"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [gds_map_path]: [found_reason]"
  Example: "- /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map: GDS map file path successfully extracted from streamOut command"

ERROR01 (Violation/Fail items):
  Format: "- [expected_gds_map]: [missing_reason]"
  Example: "- /projects/libs/map/PRTF_Innovus_N5_gdsout_17M_expected.map: GDS map file path does not match golden configuration - expected different map file"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-01:
  description: "List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
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
Reason: GDS map file path successfully extracted from streamOut command

Log format (CheckList.rpt):
INFO01:
  - /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map. In line 150, do_innovusOUTwoD.logv: GDS map file path successfully extracted from streamOut command
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: No streamOut command with PRTF gdsout map file found in log

Log format (CheckList.rpt):
ERROR01:
  - GDS map file not found

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: GDS map file not found. In line N/A, do_innovusOUTwoD.logv: No streamOut command with PRTF gdsout map file found in log
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-01:
  description: "List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - lists the gdsout map file used in streamOut operation"
      - "Note: Map file path is extracted for documentation purposes, no validation required"
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
  - "Explanation: This check is informational only - lists the gdsout map file used in streamOut operation"
  - "Note: Map file path is extracted for documentation purposes, no validation required"
INFO02:
  - GDS map file not found

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: This check is informational only - lists the gdsout map file used in streamOut operation. [WAIVED_INFO]
2: Info: GDS map file not found. In line N/A, do_innovusOUTwoD.logv: No streamOut command with PRTF gdsout map file found in log [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-01:
  description: "List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"
  requirements:
    value: 1
    pattern_items:
      - "/projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- Description says "List Innovus gdsout map name" → Use COMPLETE MAP FILE PATHS
- Extract the full absolute path from the streamOut command
- Pattern items represent the expected/golden map file path(s) for this project
- ✅ Correct: "/projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map"
- ❌ Wrong: "PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map" (filename only - too narrow)
- ❌ Wrong: "13a" (version only - wrong semantic level)

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:

- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**

```
Status: PASS
Reason: GDS map file path matched golden configuration and validated

Log format (CheckList.rpt):
INFO01:
  - /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map. In line 150, do_innovusOUTwoD.logv: GDS map file path matched golden configuration and validated. Expect (/projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-01:
  description: "List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"
  requirements:
    value: 1
    pattern_items:
      - "/projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - map file path mismatch is acceptable for this project"
      - "Note: Alternative map files are allowed based on design requirements"
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
  - "Explanation: This check is informational only - map file path mismatch is acceptable for this project"
  - "Note: Alternative map files are allowed based on design requirements"
INFO02:
  - /projects/alternative/libs/map/PRTF_Innovus_N5_gdsout_17M_alternative.map

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: This check is informational only - map file path mismatch is acceptable for this project. [WAIVED_INFO]
2: Info: /projects/alternative/libs/map/PRTF_Innovus_N5_gdsout_17M_alternative.map. In line 150, do_innovusOUTwoD.logv: GDS map file path does not match golden configuration - expected different map file [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-01:
  description: "List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"
  requirements:
    value: 1
    pattern_items:
      - "/projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map"  # ⚠️ GOLDEN VALUE - Defines "what is correct"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 2
    waive_items:
      - name: "/projects/legacy/libs/map/PRTF_Innovus_N5_gdsout_16M_legacy.12b.map"  # ⚠️ EXEMPTION - Defines "which exceptions are allowed"
        reason: "Legacy map file approved for backward compatibility with older design blocks"
      - name: "/projects/experimental/libs/map/PRTF_Innovus_N5_gdsout_16M_experimental.14a.map"
        reason: "Experimental map file approved for advanced node testing"
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
  - /projects/legacy/libs/map/PRTF_Innovus_N5_gdsout_16M_legacy.12b.map
WARN01:
  - /projects/experimental/libs/map/PRTF_Innovus_N5_gdsout_16M_experimental.14a.map

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: /projects/legacy/libs/map/PRTF_Innovus_N5_gdsout_16M_legacy.12b.map. In line 150, do_innovusOUTwoD.logv: GDS map file mismatch waived - alternative map file approved for this design: Legacy map file approved for backward compatibility with older design blocks [WAIVER]
Warn Occurrence: 1
1: Warn: /projects/experimental/libs/map/PRTF_Innovus_N5_gdsout_16M_experimental.14a.map. In line N/A, do_innovusOUTwoD.logv: Waiver not matched - specified map file not found in streamOut command: Experimental map file approved for advanced node testing [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-01:
  description: "List Innovus gdsout map name. eg: PRTF_Innovus_N3P_gdsout_17M_1Xa_h_1Xb_v_1Xc_h_1Xd_v_1Ya_h_1Yb_v_4Y_hvhv_2Yy2Yx2R_SHDMIM.10c.map"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 2
    waive_items:
      - name: "/projects/legacy/libs/map/PRTF_Innovus_N5_gdsout_16M_legacy.12b.map"  # ⚠️ MUST match Type 3 waive_items
        reason: "Legacy map file approved for backward compatibility with older design blocks"
      - name: "/projects/experimental/libs/map/PRTF_Innovus_N5_gdsout_16M_experimental.14a.map"
        reason: "Experimental map file approved for advanced node testing"
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
  - /projects/legacy/libs/map/PRTF_Innovus_N5_gdsout_16M_legacy.12b.map
WARN01:
  - /projects/experimental/libs/map/PRTF_Innovus_N5_gdsout_16M_experimental.14a.map

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: /projects/legacy/libs/map/PRTF_Innovus_N5_gdsout_16M_legacy.12b.map. In line 150, do_innovusOUTwoD.logv: GDS map file mismatch waived - alternative map file approved for this design: Legacy map file approved for backward compatibility with older design blocks [WAIVER]
Warn Occurrence: 1
1: Warn: /projects/experimental/libs/map/PRTF_Innovus_N5_gdsout_16M_experimental.14a.map. In line N/A, do_innovusOUTwoD.logv: Waiver not matched - specified map file not found in streamOut command: Experimental map file approved for advanced node testing [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-01 --force

# Run individual tests
python IMP-2-0-0-01.py
```

---

## Notes

**Parsing Considerations:**

- The gdsout map file path is extracted as an absolute path directly from the log
- The checker searches for lines containing both "PRTF" and "gdsout" substrings to distinguish gdsout map files from QRC map files
- If multiple streamOut commands exist in the log, the checker extracts all unique map file paths
- The map file path may vary between projects based on technology node and metal stack configuration

**Edge Cases:**

- If no streamOut command is found in the log, the check will fail (design not streamed out yet)
- If the streamOut command uses a relative path, it will be extracted as-is (though typically absolute paths are used)
- QRC map files (containing "qrc" instead of "gdsout") are filtered out and not reported
- The map filename typically encodes technology information (node, metal layers, via configurations) which should match project requirements

**Limitations:**

- The checker only validates the map file path used in the streamOut command, not the actual contents of the map file
- If the map file path is incorrect but the streamOut command succeeds, this checker will not detect layer mapping errors
- The checker assumes the Innovus log format follows standard Cadence conventions for the streamOut command
