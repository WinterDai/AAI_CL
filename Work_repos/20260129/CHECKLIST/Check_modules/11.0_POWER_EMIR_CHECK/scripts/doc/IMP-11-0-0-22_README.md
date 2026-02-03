# IMP-11-0-0-22: Confirm no ERROR message in power analysis log files.

## Overview

**Check ID:** IMP-11-0-0-22  
**Description:** Confirm no ERROR message in power analysis log files.  
**Category:** Power Analysis Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`
- `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv`
- `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv`

This checker validates that Cadence Voltus power analysis log files contain no ERROR messages. It scans multiple power analysis log files (.logv) from different PVT corners and analysis modes (static/dynamic) to ensure the power integrity analysis completed successfully without errors. The checker identifies ERROR messages with or without error codes (e.g., VOLTUS-123, IMPVAC-116), reports the complete error text with line numbers and file paths, and supports waiver mechanisms for known acceptable errors.

---

## Check Logic

### Input Parsing
The checker processes Cadence Voltus IC Power Integrity Solution log files (.logv format) line-by-line to detect ERROR messages while distinguishing them from WARNING messages.

**Key Patterns:**
```python
# Pattern 1: Standard ERROR message with error code in parentheses
pattern1 = r'\*\*ERROR:\s*\(([A-Z_]+-\d+)\):\s*(.+)'
# Example: "**ERROR: (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE"
# Extracts: error_code="VOLTUS-5001", error_message="Rail analysis failed for power domain VDD_CORE"

# Pattern 2: Generic ERROR keyword without error code
pattern2 = r'^\s*ERROR:\s+(.+)$'
# Example: "ERROR: Unable to read power state file"
# Extracts: error_message="Unable to read power state file", error_code=None

# Pattern 3: Case-insensitive ERROR variations
pattern3 = r'(?i)\berror\b.*?:\s*(.+)'
# Example: "Error: Power analysis incomplete due to missing constraints"
# Extracts: error_message="Power analysis incomplete due to missing constraints"

# Pattern 4: WARNING messages (for context, not reported as errors)
pattern4 = r'\*\*WARN:\s*\(([A-Z_]+-\d+)\):\s*(.+)'
# Example: "**WARN: (IMPLF-378): The spacing for cell edge type 'NW_0D5' and 'NW_0D5' is already defined."
# Purpose: Count warnings for statistics, distinguish from errors

# Pattern 5: Alternative WARNING format
pattern5 = r'WARNING\s+\(([A-Z_]+-\d+)\):\s*(.+)'
# Example: "WARNING (LEFPARS-2001): No VERSION statement found, using the default value 5.8."
# Purpose: Additional warning pattern for complete counting
```

### Detection Logic
1. **Multi-file aggregation**: Process all input .logv files sequentially, accumulating errors across all files
2. **Line-by-line scanning**: Read each file line-by-line with line number tracking using enumerate()
3. **Pattern matching priority**:
   - First apply ERROR patterns (pattern1, pattern2, pattern3) to identify error messages
   - If no ERROR match, apply WARNING patterns (pattern4, pattern5) for statistics only
   - Extract error code (if present), full error message text, line number, and file path
4. **Error data structure**: Build list of error dictionaries with keys: `file_path`, `line_number`, `error_code`, `error_message`
5. **Waiver matching** (if applicable):
   - Compare each error's error_code against waive_items by name
   - Match format: waive_item['name'] should contain the error code (e.g., "VOLTUS-5001")
   - Classify errors as waived/unwaived based on matches
6. **Final validation**:
   - PASS: No errors found OR all errors are waived
   - FAIL: Unwaived errors exist
   - Print complete ERROR information including error code, message, line number, and file path for debugging

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

**Rationale:** This checker validates ERROR absence (status check). The checker scans for ERROR messages in log files and reports any found errors. Since the goal is to confirm NO errors exist (a status condition), not to verify specific error codes exist in the file, this is a status_check. The checker reports found errors (violations) and passes only when no errors are detected or all errors are waived.

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
item_desc = "Confirm no ERROR message in power analysis log files."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No ERROR messages found in power analysis logs"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "No ERROR messages detected - power analysis completed successfully"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No ERROR messages found in power analysis log files"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All power analysis logs validated - no ERROR patterns matched"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "ERROR messages detected in power analysis logs"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "ERROR messages found - power analysis validation failed"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "ERROR message detected in power analysis log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "ERROR pattern matched - power analysis contains errors"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived ERROR messages in power analysis logs"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "ERROR message waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for power analysis errors"
unused_waiver_reason = "Waiver entry not matched - no corresponding ERROR found in logs"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [found_reason]"
  Example: "- No errors in func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv: All power analysis logs validated - no ERROR patterns matched"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE: ERROR pattern matched - power analysis contains errors"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. For ERROR messages, the item_name includes the file path, line number, error code (if present), and full error message text to provide complete debugging context.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-22:
  description: "Confirm no ERROR message in power analysis log files."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
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
Reason: No ERROR messages found in power analysis log files

Log format (CheckList.rpt):
INFO01:
  - No errors in func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv
  - No errors in func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv
  - No errors in func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: No errors in func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv. In line [N/A], [filepath]: No ERROR messages found in power analysis log files
2: Info: No errors in func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv. In line [N/A], [filepath]: No ERROR messages found in power analysis log files
3: Info: No errors in func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv. In line [N/A], [filepath]: No ERROR messages found in power analysis log files
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: ERROR message detected in power analysis log file

Log format (CheckList.rpt):
ERROR01:
  - [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE. In line 245, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: ERROR message detected in power analysis log file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-22:
  description: "Confirm no ERROR message in power analysis log files."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power analysis errors are informational only during early design phase"
      - "Note: ERROR messages are expected in pre-optimization runs and do not block signoff"
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
  - "Explanation: Power analysis errors are informational only during early design phase"
  - "Note: ERROR messages are expected in pre-optimization runs and do not block signoff"
INFO02:
  - [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Power analysis errors are informational only during early design phase. [WAIVED_INFO]
2: Info: Note: ERROR messages are expected in pre-optimization runs and do not block signoff. [WAIVED_INFO]
3: Info: [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE. In line 245, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: ERROR message detected in power analysis log file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-22:
  description: "Confirm no ERROR message in power analysis log files."
  requirements:
    value: 3
    pattern_items:
      - "VOLTUS-5001"
      - "IMPVAC-116"
      - "VOLTUS_EXTR-1293"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
  ❌ DO NOT use paths: "innovus/221/22.11-s119_1"
  ❌ DO NOT use filenames: "libtech.lef"
- If description contains "filename"/"name": Use COMPLETE FILENAMES (e.g., "design.v")
- If description contains "status": Use STATUS VALUES (e.g., "Loaded", "Skipped")

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All power analysis logs validated - no ERROR patterns matched

Log format (CheckList.rpt):
INFO01:
  - No errors in func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv
  - No errors in func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv
  - No errors in func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: No errors in func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv. In line [N/A], [filepath]: All power analysis logs validated - no ERROR patterns matched
2: Info: No errors in func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv. In line [N/A], [filepath]: All power analysis logs validated - no ERROR patterns matched
3: Info: No errors in func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv. In line [N/A], [filepath]: All power analysis logs validated - no ERROR patterns matched
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-22:
  description: "Confirm no ERROR message in power analysis log files."
  requirements:
    value: 3
    pattern_items:
      - "VOLTUS-5001"
      - "IMPVAC-116"
      - "VOLTUS_EXTR-1293"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Specific ERROR codes are tracked for informational purposes only"
      - "Note: These errors are expected during power grid optimization and do not require immediate fixes"
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
  - "Explanation: Specific ERROR codes are tracked for informational purposes only"
  - "Note: These errors are expected during power grid optimization and do not require immediate fixes"
INFO02:
  - [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Specific ERROR codes are tracked for informational purposes only. [WAIVED_INFO]
2: Info: Note: These errors are expected during power grid optimization and do not require immediate fixes. [WAIVED_INFO]
3: Info: [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE. In line 245, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: ERROR pattern matched - power analysis contains errors [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-22:
  description: "Confirm no ERROR message in power analysis log files."
  requirements:
    value: 3
    pattern_items:
      - "VOLTUS-5001"
      - "IMPVAC-116"
      - "VOLTUS_EXTR-1293"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
  waivers:
    value: 2
    waive_items:
      - name: "VOLTUS-5001"
        reason: "Waived - known issue with VDD_CORE rail analysis in early design phase, will be resolved in final power grid optimization"
      - name: "IMPVAC-116"
        reason: "Waived - vacuum cell placement error acceptable for this design per power team approval"
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
  - [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE
WARN01:
  - IMPVAC-116

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE. In line 245, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: ERROR message waived per design team approval: Waived - known issue with VDD_CORE rail analysis in early design phase, will be resolved in final power grid optimization [WAIVER]
Warn Occurrence: 1
1: Warn: IMPVAC-116. In line [N/A], [filepath]: Waiver entry not matched - no corresponding ERROR found in logs: Waived - vacuum cell placement error acceptable for this design per power team approval [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-22:
  description: "Confirm no ERROR message in power analysis log files."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
  waivers:
    value: 2
    waive_items:
      - name: "IMPLF-388"
        reason: "Waived - known issue in reading lef file"
      - name: "IMPVAC-116"
        reason: "Waived - vacuum cell placement error acceptable for this design per power team approval"
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
  - [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE
WARN01:
  - IMPVAC-116

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: [func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv:245] ERROR (VOLTUS-5001): Rail analysis failed for power domain VDD_CORE. In line 245, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: ERROR message waived per design team approval: Waived - known issue with VDD_CORE rail analysis in early design phase, will be resolved in final power grid optimization [WAIVER]
Warn Occurrence: 1
1: Warn: IMPVAC-116. In line [N/A], [filepath]: Waiver entry not matched - no corresponding ERROR found in logs: Waived - vacuum cell placement error acceptable for this design per power team approval [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-22 --force

# Run individual tests
python IMP-11-0-0-22.py
```

---

## Notes

**Important Considerations:**
1. **Error Code Extraction**: The checker handles both ERROR messages with error codes (e.g., `**ERROR: (VOLTUS-5001):`) and generic ERROR messages without codes. When no error code is present, the checker sets error_code to None or "GENERIC" for tracking purposes.

2. **Multi-line Error Messages**: Currently, the checker captures only the first line of multi-line error messages. If error messages span multiple lines, consider implementing continuation logic to capture complete error text.

3. **WARNING vs ERROR Distinction**: The checker carefully distinguishes between WARNING messages (e.g., `**WARN: (IMPLF-378):`, `WARNING (LEFPARS-2001):`) and ERROR messages. Warnings are counted for statistics but not reported as failures.

4. **File Format Variations**: The checker handles both `.log` and `.logv` file extensions. Compressed files (`.gz`) can be supported by adding gzip.open() handling if needed.

5. **Performance**: Line-by-line streaming ensures efficient processing of large log files without loading entire files into memory.

6. **Waiver Matching**: For Type 3/4 configurations, waive_items should use error codes (e.g., "VOLTUS-5001") as the `name` field to match against detected errors. The waiver reason should explain why the specific error is acceptable.

7. **Complete Error Context**: When errors are found, the checker prints the complete ERROR information including:
   - File path where error occurred
   - Line number in the file
   - Error code (if present)
   - Full error message text
   This provides sufficient context for debugging and resolution.

8. **Known Limitations**:
   - Does not parse multi-line error messages that span across line breaks
   - Does not extract metadata like tool version or execution timestamps (though patterns are defined for future enhancement)
   - Assumes ERROR messages follow standard Cadence Voltus format conventions