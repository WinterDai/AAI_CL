# IMP-9-0-0-02: Confirm SPEF extraction includes NDR rule lef file.

## Overview

**Check ID:** IMP-9-0-0-02  
**Description:** Confirm SPEF extraction includes NDR rule lef file.  
**Category:** RC Extraction Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log`

This checker verifies that Quantus QRC SPEF extraction process successfully loaded NDR (Non-Default Rule) LEF files. It parses the extraction log files to confirm NDR LEF files were included and checks for any version mismatch warnings or errors that could affect extraction accuracy.

---

## Check Logic

### Input Parsing
Parse Quantus QRC extraction log files (`do_qrc*.log`) to extract:
1. NDR LEF file paths from INFO messages (EXTGRMP-338)
2. Version mismatch warnings between tech LEF and NDR LEF files (EXTGRMP-728)
3. Other warnings/errors related to NDR file processing

**Key Patterns:**
```python
# Pattern 1: NDR LEF file loading confirmation
pattern1 = r'INFO \(EXTGRMP-338\) : (.+/ndr/[^\s]+\.lef)'
# Example: "INFO (EXTGRMP-338) : /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef"

# Pattern 2: Version mismatch warnings for NDR LEF files
pattern2 = r'WARNING \(EXTGRMP-728\) : Different version number exists for tech lef "([^"]+)" with version ([\d.]+) and macro lef "([^"]+)" with version ([\d.]+)'
# Example: "WARNING (EXTGRMP-728) : Different version number exists for tech lef \"/process/tsmcN7/data/stdcell/.../PRTF_Innovus_N7_15M_1X1Xa1Ya5Y2Yy2Yx2R_UTRDL_M1P64_M2P40_M3P44_M4P76_M5P76_M6P76_M7P76_M8P76_M9P76_H300.14_1a.tlef\" with version 5.8 and macro lef \"/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef\" with version 5.6."

# Pattern 3: General WARNING messages with message codes
pattern3 = r'WARNING \(([A-Z]+-\d+)\) : (.+)'
# Example: "WARNING (EXTGRMP-769) : DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR."
```

### Detection Logic
1. **First Pass - Collect NDR LEF Files:**
   - Scan log file for INFO (EXTGRMP-338) messages
   - Extract all NDR LEF file paths (containing '/ndr/' in path)
   - Store in `ndr_files_found` list

2. **Second Pass - Detect Version Mismatches:**
   - Scan for WARNING (EXTGRMP-728) messages
   - Extract tech LEF path, version, NDR LEF path, and version
   - If macro lef path contains '/ndr/', classify as NDR-related warning
   - Store version mismatch details

3. **Third Pass - Collect Other Warnings:**
   - Scan for other WARNING/ERROR messages
   - Filter for messages related to NDR files (path contains '/ndr/')
   - Associate warnings with specific NDR files

4. **Result Classification:**
   - **PASS:** NDR LEF files found AND no critical errors
   - **FAIL:** No NDR LEF files found OR critical version mismatches detected

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - 存在性检查
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

### Mode 2: `status_check` - 状态检查  
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

**Rationale:** This checker verifies that specific NDR LEF files exist in the extraction log. The pattern_items represent NDR LEF file paths that SHOULD be loaded during SPEF extraction. The checker searches for these file paths in INFO messages and reports which ones were found vs. missing.

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
item_desc = "Confirm SPEF extraction includes NDR rule lef file."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "NDR LEF files found in SPEF extraction log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All required NDR LEF files matched in extraction log"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "NDR LEF files successfully found during SPEF extraction"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All required NDR LEF file patterns matched and validated in extraction log"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "NDR LEF files not found in SPEF extraction log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Required NDR LEF files not satisfied in extraction log"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "NDR LEF files not found in SPEF extraction log or version mismatch detected"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required NDR LEF file patterns not satisfied or missing from extraction log"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "NDR LEF file issues waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "NDR LEF file missing or version mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused NDR LEF waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding NDR LEF issue found in extraction log"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[ndr_lef_file_path]"
  Example: "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef"

ERROR01 (Violation/Fail items):
  Format: "VERSION MISMATCH: [ndr_lef_file] (v[ndr_version]) vs tech LEF (v[tech_version])"
  Example: "VERSION MISMATCH: /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef (v5.6) vs tech LEF (v5.8)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-02:
  description: "Confirm SPEF extraction includes NDR rule lef file."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
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
Reason: NDR LEF files successfully found during SPEF extraction
INFO01:
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: NDR LEF files not found in SPEF extraction log or version mismatch detected
ERROR01:
  - VERSION MISMATCH: /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef (v5.6) vs tech LEF (v5.8)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-02:
  description: "Confirm SPEF extraction includes NDR rule lef file."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: NDR LEF version mismatch is acceptable for this design"
      - "Note: Version differences do not affect extraction accuracy for this technology node"
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
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: NDR LEF version mismatch is acceptable for this design"
  - "Note: Version differences do not affect extraction accuracy for this technology node"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - VERSION MISMATCH: /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef (v5.6) vs tech LEF (v5.8) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-02:
  description: "Confirm SPEF extraction includes NDR rule lef file."
  requirements:
    value: 2
    pattern_items:
      - "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef"
      - "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All required NDR LEF file patterns matched and validated in extraction log
INFO01:
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-02:
  description: "Confirm SPEF extraction includes NDR rule lef file."
  requirements:
    value: 0
    pattern_items:
      - "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef"
      - "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: NDR LEF file check is informational only for this design"
      - "Note: Missing NDR LEF files are expected in flat extraction mode and do not require fixes"
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
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: NDR LEF file check is informational only for this design"
  - "Note: Missing NDR LEF files are expected in flat extraction mode and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-02:
  description: "Confirm SPEF extraction includes NDR rule lef file."
  requirements:
    value: 2
    pattern_items:
      - "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef"
      - "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 2
    waive_items:
      - name: "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef"
        reason: "Waived - NDR LEF v5.6 approved for this design despite tech LEF v5.8"
      - name: "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef"
        reason: "Waived - legacy NDR file used per design team agreement"
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
INFO01 (Waived):
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef [WAIVER]
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef [WAIVER]
WARN01 (Unused Waivers):
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_3w4s.lef: Waiver not matched - no corresponding NDR LEF issue found in extraction log
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-02:
  description: "Confirm SPEF extraction includes NDR rule lef file."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 2
    waive_items:
      - name: "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef"
        reason: "Waived - NDR LEF v5.6 approved for this design despite tech LEF v5.8"
      - name: "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef"
        reason: "Waived - legacy NDR file used per design team agreement"
```

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
INFO01 (Waived):
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef [WAIVER]
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 9.0_RC_EXTRACTION_CHECK --checkers IMP-9-0-0-02 --force

# Run individual tests
python IMP-9-0-0-02.py
```

---

## Notes

- **NDR LEF File Detection:** The checker specifically looks for LEF files in paths containing '/ndr/' directory
- **Version Mismatch Handling:** EXTGRMP-728 warnings indicate version differences between tech LEF and NDR LEF files, which may affect extraction accuracy
- **Multi-file Support:** The checker can process multiple `do_qrc*.log` files and aggregate NDR file information across all extraction runs
- **Metal Fill Processing:** The log also contains metal fill information (EXTSNZ-169), but this is not directly related to NDR LEF validation
- **Warning Summary:** The log includes a warning summary section with occurrence counts, useful for identifying recurring issues
- **Known Limitations:** 
  - Only detects NDR files explicitly mentioned in INFO (EXTGRMP-338) messages
  - Version mismatch warnings (EXTGRMP-728) are informational; actual impact depends on design requirements
  - Does not validate NDR rule content, only file loading confirmation