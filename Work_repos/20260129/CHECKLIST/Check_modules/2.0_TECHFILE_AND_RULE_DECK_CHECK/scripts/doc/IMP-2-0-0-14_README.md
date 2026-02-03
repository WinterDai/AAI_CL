# IMP-2-0-0-14: List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem

## Overview

**Check ID:** IMP-2-0-0-14  
**Description:** List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem  
**Category:** TECHFILE_AND_RULE_DECK_CHECK  
**Input Files:** 
- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_static.log`

This checker extracts and validates the EM (Electromigration) rule deck file path used in Cadence Voltus power integrity analysis. It parses the Voltus run log to identify the EM rule deck configuration, extracts the version and filename from the absolute path, and reports the EM rule deck identifier in the format: `<version_directory>/<rule_deck_filename>.ictem`.

The checker supports both informational listing (Type 1/4) and golden value validation (Type 2/3) modes. In validation mode, it compares the extracted EM rule deck against expected golden values to ensure the correct EM analysis configuration is being used.

---

## Check Logic

### Input Parsing

**Step 1: Extract EM Rule Deck Path**
Parse the Voltus run log file to locate the line containing EM rule deck information:
- Search for pattern: `Info: Using EM Rules from : '*'`
- Extract the absolute path between the single quotes into `em_path`
- Example: `/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem`

**Step 2: Extract EM Rule Version and Filename**
From the extracted `em_path`, extract the version directory and rule deck filename:
- Identify the version directory (e.g., `ictem_v1d2p1a`)
- Identify the rule deck filename (e.g., `cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem`)
- Combine into `em_rule` format: `<version_directory>/<filename>`
- Store result: `em_rule = "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"`

**Key Patterns:**
```python
# Pattern 1: EM rule deck path extraction from Voltus log
pattern1 = r"Info:\s+Using\s+EM\s+Rules\s+from\s+:\s+'([^']+)'"
# Example: "Info: Using EM Rules from : '/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem'"

# Pattern 2: Extract version directory and filename from absolute path
pattern2 = r'/([^/]+/[^/]+\.ictem)$'
# Example: From "/process/.../ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
#          Extract: "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
```

### Detection Logic

**Type 1/4 (Informational Mode - No pattern_items):**
1. Parse the Voltus log file using Pattern 1 to extract `em_path`
2. If `em_path` is successfully extracted and not empty:
   - Apply Pattern 2 to extract `em_rule` (version/filename format)
   - **PASS**: EM rule deck found and extracted
   - Output `em_rule` in INFO01
3. If `em_path` cannot be extracted or is empty:
   - **FAIL**: EM rule deck information not found in log
   - Output error message in ERROR01

**Type 2/3 (Validation Mode - With pattern_items):**
1. Parse the Voltus log file using Pattern 1 to extract `em_path`
2. If `em_path` is successfully extracted:
   - Apply Pattern 2 to extract `em_rule`
   - Store `pattern_items[0]` into `golden_em` (expected EM rule deck)
   - Compare `em_rule` with `golden_em`:
     - If `em_rule == golden_em`: **PASS** - EM rule deck matches expected configuration
     - If `em_rule != golden_em`: **FAIL** - EM rule deck mismatch
3. If `em_path` cannot be extracted:
   - **FAIL**: EM rule deck information not found in log

**Output Logic:**
- **Type 1/4 PASS**: Output `em_rule` (e.g., "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem")
- **Type 2/3 PASS**: Output `em_rule` (Expected: `golden_em`)
- **Type 2/3 FAIL**: Output `em_rule` (Expected: `golden_em`) with mismatch indication

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates that the EM rule deck configuration exists in the Voltus log and optionally matches expected golden values. In Type 1/4 mode, it verifies the existence and extractability of EM rule deck information. In Type 2/3 mode, it checks whether the extracted EM rule deck identifier matches the expected pattern_items (golden EM rule deck configurations). The pattern_items represent EM rule deck identifiers that SHOULD EXIST and match in the input files.

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
item_desc = "List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "EM rule deck information found in Voltus log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "EM rule deck matched expected configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "EM rule deck path successfully extracted from Voltus run log"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "EM rule deck identifier matched expected golden value and validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "EM rule deck information not found in Voltus log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "EM rule deck does not match expected configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "EM rule deck path not found in Voltus run log - check if EM analysis was enabled"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "EM rule deck identifier does not match expected golden value or extraction failed"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "EM rule deck mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "EM rule deck version difference waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused EM rule deck waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding EM rule deck mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "EM rule deck: <version_directory>/<filename>.ictem"
  Example: "EM rule deck: ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"

ERROR01 (Violation/Fail items):
  Format: "EM rule deck mismatch: Found=<actual_em_rule>, Expected=<golden_em>"
  Example: "EM rule deck mismatch: Found=ictem_v1d2p1a/cln5_1p16m.ictem, Expected=ictem_v1d0p1a/cln3p_1p17m.ictem"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-14:
  description: "List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_static.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean existence check - verifies that EM rule deck information can be extracted from the Voltus log file. PASS if `em_path` is successfully extracted and `em_rule` can be derived; FAIL if extraction fails or EM rule deck information is missing.

**Sample Output (PASS):**
```
Status: PASS
Reason: EM rule deck path successfully extracted from Voltus run log
INFO01:
  - EM rule deck: ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: EM rule deck path not found in Voltus run log - check if EM analysis was enabled
ERROR01:
  - EM rule deck information not found in log file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-14:
  description: "List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_static.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - EM rule deck listing for documentation purposes"
      - "Note: Missing EM rule deck information is acceptable for non-EM analysis runs"
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
  - "Explanation: This check is informational only - EM rule deck listing for documentation purposes"
  - "Note: Missing EM rule deck information is acceptable for non-EM analysis runs"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - EM rule deck information not found in log file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-14:
  description: "List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  requirements:
    value: 2
    pattern_items:
      - "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
      - "ictem_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_static.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "List EM irxc rule deck name" → Use COMPLETE EM RULE DECK IDENTIFIERS
- Format: `<version_directory>/<filename>.ictem`
- ✅ CORRECT: "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
- ❌ WRONG: "/process/tsmcN5/data/g/QRC/.../ictem_v1d2p1a/cln5_1p16m.ictem" (full path)
- ❌ WRONG: "ictem_v1d2p1a" (version directory only)
- ❌ WRONG: "cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem" (filename only)

**Check Behavior:**
Type 2 searches pattern_items in input files. This is a requirement check - PASS if the extracted `em_rule` matches one of the pattern_items (expected EM rule deck configurations). FAIL if `em_rule` does not match any pattern_items or if extraction fails.

**Sample Output (PASS):**
```
Status: PASS
Reason: EM rule deck identifier matched expected golden value and validated
INFO01:
  - EM rule deck: ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem (Expected: ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-14:
  description: "List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  requirements:
    value: 2
    pattern_items:
      - "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
      - "ictem_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_static.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - EM rule deck version tracking for documentation"
      - "Note: EM rule deck version mismatches are expected during technology migration and do not require immediate fixes"
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
  - "Explanation: This check is informational only - EM rule deck version tracking for documentation"
  - "Note: EM rule deck version mismatches are expected during technology migration and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - EM rule deck mismatch: Found=ictem_v1d3p0a/cln5_1p16m.ictem, Expected=ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-14:
  description: "List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  requirements:
    value: 2
    pattern_items:
      - "ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"
      - "ictem_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_static.log"
  waivers:
    value: 2
    waive_items:
      - name: "ictem_v1d3p0a/cln5_1p16m+alrdl_1x1xb1xe1ya1yb6y2yy2r.ictem"
        reason: "Waived - intermediate EM rule deck version approved for pre-tapeout analysis"
      - name: "ictem_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
        reason: "Waived - legacy EM rule deck version used for baseline comparison"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description says "List EM irxc rule deck name" → Use COMPLETE EM RULE DECK IDENTIFIERS
- ✅ pattern_items: ["ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem"] (complete identifier)
- ✅ waive_items.name: "ictem_v1d3p0a/cln5_1p16m+alrdl_1x1xb1xe1ya1yb6y2yy2r.ictem" (same level as pattern_items)
- ❌ DO NOT mix: pattern_items="/process/.../ictem_v1d2p1a/cln5.ictem" (path) with waive_items.name="ictem_v1d2p1a/cln5.ictem" (identifier)

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items (extracted EM rule deck) against waive_items
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - EM rule deck: ictem_v1d3p0a/cln5_1p16m+alrdl_1x1xb1xe1ya1yb6y2yy2r.ictem [WAIVER]
WARN01 (Unused Waivers):
  - ictem_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem: Waiver not matched - no corresponding EM rule deck mismatch found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-14:
  description: "List EM irxc rule deck name. eg: ICT_EM_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_static.log"
  waivers:
    value: 2
    waive_items:
      - name: "ictem_v1d3p0a/cln5_1p16m+alrdl_1x1xb1xe1ya1yb6y2yy2r.ictem"
        reason: "Waived - intermediate EM rule deck version approved for pre-tapeout analysis"
      - name: "ictem_v1d0p1a/cln3p_1p17m+ut-alrdl_1xa1xb1xc1xd1ya1yb4y2yy2yx2r_shdmim.ictem"
        reason: "Waived - legacy EM rule deck version used for baseline comparison"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
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
INFO01 (Waived):
  - EM rule deck: ictem_v1d3p0a/cln5_1p16m+alrdl_1x1xb1xe1ya1yb6y2yy2r.ictem [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-14 --force

# Run individual tests
python IMP-2-0-0-14.py
```

---

## Notes

**Limitations:**
- The checker relies on the specific log format: `Info: Using EM Rules from : '*'`. If Voltus changes this format, the pattern extraction may fail.
- The version/filename extraction assumes a specific path structure with the version directory immediately preceding the `.ictem` filename. Non-standard path structures may require pattern adjustment.
- If multiple EM rule decks are referenced in the log (e.g., for different metal stacks), only the first occurrence is extracted.

**Known Issues:**
- If the EM rule deck path is split across multiple lines due to TCL continuation characters, the current pattern may not capture it correctly.
- Compressed or archived EM rule deck files (e.g., `.ictem.gz`) may not match the `.ictem` extension pattern.

**Edge Cases:**
- Empty log files or logs without EM analysis enabled will result in FAIL for Type 1/4 (unless waived).
- For Type 2/3, if the extracted EM rule deck does not match any pattern_items, it will be reported as a mismatch even if it's a valid EM rule deck.
- Unused waivers in Type 3/4 indicate that the waived EM rule deck identifier was not found in the actual log, which may suggest the waiver is outdated or incorrect.