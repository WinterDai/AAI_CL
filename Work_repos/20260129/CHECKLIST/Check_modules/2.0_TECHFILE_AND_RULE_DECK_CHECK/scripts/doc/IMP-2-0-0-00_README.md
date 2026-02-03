# IMP-2-0-0-00: List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef

## Overview

**Check ID:** IMP-2-0-0-00
**Description:** List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef
**Category:** TECHFILE_AND_RULE_DECK_CHECK
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv

This checker extracts and validates the technology LEF file used in Cadence Innovus implementation. The tech LEF file contains technology-specific information (layers, vias, design rules) and is critical for physical design. The checker parses the Innovus log to identify the .tlef file loaded during design restoration and reports the filename for verification.

---

## Check Logic

### Input Parsing

- Parse the input log file to extract the tech lef path from Loading LEF file statement.
- Extract the full path to the tech LEF file
- Store the absolute path in variable `tech_lef`

**Key Patterns:**

```python
# Pattern 1: Extract tech lef path from Loading LEF file statement
loading_pattern = r'\[.*?\]\s+Loading LEF file\s+([^\s]+\.tlef)'
# Example: 'Loading LEF file ruledeck\2.0\PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef'
# Extraction: Captures absolute path → stored as `tech_lef`
```

### Detection Logic

**Type 1/4 (No pattern_items):**

- If `tech_lef` successfully extracted and value exists → **PASS**
- If `tech_lef` not found or empty → **FAIL**
- Output: Display the extracted `tech_lef` filename

**Type 2/3 (With pattern_items):**

- Store `pattern_items[0]` into variable `golden_tech`
- Compare extracted `tech_lef` against `golden_tech`
- If `tech_lef` == `golden_tech` → **PASS**
- If `tech_lef` != `golden_tech` → **FAIL**
- Output: Display `tech_lef` with expected value `(golden_tech)` in parentheses

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

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

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates that the expected technology LEF file exists and is loaded in the Innovus session. For Type 2/3, pattern_items contain the golden tech LEF filename(s) that should be found in the log. The checker searches for these filenames and reports whether they were successfully loaded.

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
item_desc = "List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Technology LEF file found in Innovus log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Technology LEF filename matched expected pattern"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Technology LEF file successfully loaded in Innovus session"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Technology LEF filename matched and validated against golden reference"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Technology LEF file not found in Innovus log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Technology LEF filename does not match expected pattern"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "No technology LEF file loading detected in Innovus log - check restoreDesign command"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Technology LEF filename does not match golden reference - verify correct tech file is used"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Technology LEF mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Technology LEF filename mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused tech LEF waiver entry"
unused_waiver_reason = "Waiver entry not matched - no corresponding tech LEF mismatch found in log"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [tech_lef_filename]: [found_reason]"
  Example: "- PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef: Technology LEF file successfully loaded in Innovus session"

ERROR01 (Violation/Fail items):
  Format: "- [tech_lef_filename]: [missing_reason]"
  Example: "- Expected: PRTF_Innovus_N5_16M...13a.tlef, Found: PRTF_Innovus_N7_8M...10b.tlef: Technology LEF filename does not match golden reference - verify correct tech file is used"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-00:
  description: "List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"
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
Type 1 performs boolean existence check - verifies that a technology LEF file is loaded in Innovus.
PASS if tech LEF file is found in log, FAIL if not found.

**Sample Output (PASS):**

```
Status: PASS
Reason: Technology LEF file successfully loaded in Innovus session

Log format (CheckList.rpt):
INFO01:
  - PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef. In line 42, do_innovusOUTwoD.logv: Technology LEF file successfully loaded in Innovus session
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: No technology LEF file loading detected in Innovus log - check restoreDesign command

Log format (CheckList.rpt):
ERROR01:
  - No tech LEF file found

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: No tech LEF file found. In line N/A, do_innovusOUTwoD.logv: No technology LEF file loading detected in Innovus log - check restoreDesign command
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-00:
  description: "List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - tech LEF listing for documentation purposes"
      - "Note: Tech LEF file presence is verified by other checks in the flow"
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
  - "Explanation: This check is informational only - tech LEF listing for documentation purposes"
  - "Note: Tech LEF file presence is verified by other checks in the flow"
INFO02:
  - No tech LEF file found

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: This check is informational only - tech LEF listing for documentation purposes. [WAIVED_INFO]
2: Info: No tech LEF file found. In line N/A, do_innovusOUTwoD.logv: No technology LEF file loading detected in Innovus log - check restoreDesign command [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-00:
  description: "List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"
  requirements:
    value: 1
    pattern_items:
      - "PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- Description says "List Innovus Tech Lef name" → Use COMPLETE FILENAMES
- ✅ Correct: "PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef"
- ❌ Wrong: "/process/tsmcN5/data/.../PRTF_Innovus_N5_16M...13a.tlef" (full path)
- ❌ Wrong: "13a" (version only)

**Check Behavior:**
Type 2 searches for the golden tech LEF filename in the Innovus log.
PASS if the extracted tech LEF matches the pattern_items entry.
FAIL if tech LEF not found or doesn't match.

**Sample Output (PASS):**

```
Status: PASS
Reason: Technology LEF filename matched and validated against golden reference

Log format (CheckList.rpt):
INFO01:
  - PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef. In line 42, do_innovusOUTwoD.logv: Technology LEF filename matched and validated against golden reference. Expect (PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-00:
  description: "List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"
  requirements:
    value: 1
    pattern_items:
      - "PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Tech LEF filename check is informational - different versions may be used across projects"
      - "Note: Tech LEF compatibility is verified by Innovus tool during loading"
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
  - "Explanation: Tech LEF filename check is informational - different versions may be used across projects"
  - "Note: Tech LEF compatibility is verified by Innovus tool during loading"
INFO02:
  - PRTF_Innovus_N7_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.10b.tlef

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Tech LEF filename check is informational - different versions may be used across projects. [WAIVED_INFO]
2: Info: PRTF_Innovus_N7_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.10b.tlef. In line 42, do_innovusOUTwoD.logv: Technology LEF filename does not match golden reference - verify correct tech file is used. Expect (PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-00:
  description: "List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"
  requirements:
    value: 1
    pattern_items:
      - "PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 2
    waive_items:
      - name: "PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.12b.tlef"
        reason: "Waived - using previous tech LEF version for legacy block compatibility"
      - name: "PRTF_Innovus_N5_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_H210_SHDMIM.13a.tlef"
        reason: "Waived - using 8M stack variant for low-power design"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:

- Match found tech LEF filename against waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
  PASS if all mismatches are waived.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.12b.tlef
WARN01:
  - PRTF_Innovus_N5_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_H210_SHDMIM.13a.tlef

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.12b.tlef. In line 42, do_innovusOUTwoD.logv: Technology LEF filename mismatch waived per design team approval: Waived - using previous tech LEF version for legacy block compatibility [WAIVER]
Warn Occurrence: 1
1: Warn: PRTF_Innovus_N5_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_H210_SHDMIM.13a.tlef. In line N/A, do_innovusOUTwoD.logv: Waiver entry not matched - no corresponding tech LEF mismatch found in log: Waived - using 8M stack variant for low-power design [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-00:
  description: "List Innovus Tech Lef name. eg:N16_Encounter_11M_2Xa1Xd3Xe2Y2R_UTRDL_9T_PODE_1.2a.tlef"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_innovusOUTwoD.logv
  waivers:
    value: 2
    waive_items:
      - name: "PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.12b.tlef"
        reason: "Waived - using previous tech LEF version for legacy block compatibility"
      - name: "PRTF_Innovus_N5_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_H210_SHDMIM.13a.tlef"
        reason: "Waived - using 8M stack variant for low-power design"
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
  - PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.12b.tlef
WARN01:
  - PRTF_Innovus_N5_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_H210_SHDMIM.13a.tlef

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.12b.tlef. In line 42, do_innovusOUTwoD.logv: Technology LEF filename mismatch waived per design team approval: Waived - using previous tech LEF version for legacy block compatibility [WAIVER]
Warn Occurrence: 1
1: Warn: PRTF_Innovus_N5_8M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_H210_SHDMIM.13a.tlef. In line N/A, do_innovusOUTwoD.logv: Waiver entry not matched - no corresponding tech LEF mismatch found in log: Waived - using 8M stack variant for low-power design [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-00 --force

# Run individual tests
python IMP-2-0-0-00.py
```

---

## Notes

**Implementation Notes:**

- The checker searches for the pattern `*Loading LEF file *PRTF*.tlef` in the Innovus log
- Tech LEF path is already absolute and can be directly parsed
- Only the filename (basename) is extracted for comparison and reporting
- The PRTF naming convention is typical for TSMC technology LEF files

**Limitations:**

- Assumes tech LEF follows PRTF naming convention (PRTF_Innovus_*.tlef)
- If multiple tech LEF files are loaded, only the first match is reported
- Does not validate tech LEF content, only filename presence/matching

**Known Issues:**

- If restoreDesign command uses a different LEF loading method, pattern may not match
- Tech LEF path format may vary across different Innovus versions
