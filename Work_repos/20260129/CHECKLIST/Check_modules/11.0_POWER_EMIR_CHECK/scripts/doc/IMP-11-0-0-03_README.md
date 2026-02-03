# IMP-11-0-0-03: Confirm activity file was used? If not, provide default switching activity values in comments field.

## Overview

**Check ID:** IMP-11-0-0-03  
**Description:** Confirm activity file was used? If not, provide default switching activity values in comments field.  
**Category:** Power Analysis Configuration Validation  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log

This checker validates that Cadence Voltus power integrity analysis runs have proper switching activity configuration. It verifies whether an activity file (e.g., SAIF) was successfully loaded via `read_activity_file` command, or if default switching activity values were set via `set_default_switching_activity` command. The checker ensures that power analysis has valid activity data and reports the configuration method used (activity file vs. defaults) along with parameter values when defaults are applied.

---

## Check Logic

### Input Parsing

The checker scans Voltus log files (*static*.log, *dynamic*.log, *EM*.log) for activity configuration commands. These logs contain command execution records prefixed with `<CMD>` tags.

**Key Patterns:**

```python
# Pattern 1: Detect successful activity file read
pattern_read_activity = r"'read_activity_file'\s+finished successfully"
# Example: "'read_activity_file' finished successfully"
# Indicates: Activity file was successfully loaded

# Pattern 2: Detect default switching activity command
pattern_set_default = r"'set_default_switching_activity'\s+finished successfully"
# Example: "'set_default_switching_activity' finished successfully"
# Indicates: Default activity values were set (no activity file used)

# Pattern 3: Extract input_activity parameter value
pattern_input_activity = r"set_default_switching_activity\s+.*?-input_activity\s+(\S+)"
# Example: "set_default_switching_activity -input_activity 0.2 -period 10.0"
# Extraction: Captures "0.2" as the input_activity value
```

### Detection Logic

1. **Scan for activity file usage:**
   - Search entire log file for pattern: `'read_activity_file' finished successfully`
   - If found: Mark as PASS, report "Activity file used" in INFO01
   - Extract file name if available for comments field

2. **If no activity file found, check for default values:**
   - Search for pattern: `'set_default_switching_activity' finished successfully`
   - If found: Mark as PASS, extract parameter values using sub-patterns
   - Report default values in INFO01 with format: `set_default_switching_activity -input_activity X.X`

3. **If neither pattern found:**
   - Mark as FAIL
   - Report ERROR01: "No activity configuration found"

4. **Parameter extraction (when defaults used):**
   - Extract `-input_activity` value using regex group capture
   - Format output: `set_default_switching_activity -input_activity 0.2` 

5. **Per-file processing:**
   - Each log file represents one analysis corner
   - Report one result per file showing actual configuration found
   - If BOTH activity file AND default switching exist: report combined (e.g., "'read_activity_file' finished successfully + set_default_switching_activity -input_activity 0.15")
   - Associate configuration with analysis corner from filename

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the STATUS of activity configuration in power analysis logs. The pattern_items represent different valid configuration states (activity file used vs. default values set). The checker searches for these configuration patterns and reports which method was used. Only matched configuration states are output - this is a status validation check, not an existence check of predefined items.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "Confirm activity file was used? If not, provide default switching activity values in comments field."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Activity configuration found in power analysis log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Activity configuration validated (activity file or defaults set)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
# NOTE: Actual output uses DYNAMIC reasons extracted from each item's description field
# Examples: "'read_activity_file' finished successfully (tv_chip.tcf)"
#           "set_default_switching_activity -input_activity 0.15"
#           "'read_activity_file' finished successfully (-format) + set_default_switching_activity -input_activity 0.15"
found_reason_type1_4 = "Activity file successfully loaded or default switching activity configured"  # Fallback only
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "'read_activity_file' finished successfully OR 'set_default_switching_activity' finished successfully"  # Fallback only

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Activity configuration not found in power analysis log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "No activity configuration detected (neither activity file nor defaults)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Neither 'read_activity_file' nor 'set_default_switching_activity' command found in log"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required activity configuration pattern not satisfied - no valid activity setup detected"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Activity configuration issue waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Activity configuration violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused activity configuration waiver"
unused_waiver_reason = "Waiver not matched - no corresponding activity configuration issue found in log"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [dynamic_reason_from_log]"
  Example: "- ND1_func_ffgnp_0p825v_125c_static.log: set_default_switching_activity -input_activity 0.15"
  Example: "- EM_ND1_func_ffgnp_0p825v_m40c_hold.log: 'read_activity_file' finished successfully (tv_chip.tcf) + set_default_switching_activity -input_activity 0.15"
  Example: "- ND1_func_ssgnp_0p675v_125c_dynamic.log: 'read_activity_file' finished successfully"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- ND1_func_ffgnp_0p825v_125c_EM.log: Neither 'read_activity_file' nor 'set_default_switching_activity' command found in log"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. The found_reason uses a callable lambda to extract the dynamic description from each item, showing exactly what was found in the log (activity file path, default activity values, or both).

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-03:
  description: "Confirm activity file was used? If not, provide default switching activity values in comments field."
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
Type 1 performs boolean validation of activity configuration in Voltus logs. For each log file, the checker searches for either `'read_activity_file' finished successfully` or `'set_default_switching_activity' finished successfully` patterns. PASS if at least one pattern is found (valid activity configuration exists). FAIL if neither pattern is found (no activity configuration detected).

**Sample Output (PASS):**
```
Status: PASS
Reason: Activity file successfully loaded or default switching activity configured

Log format (CheckList.rpt):
INFO01:
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.log
  - EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold.log
  - ND1_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_dynamic.log

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.log. In line 1533, logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.log: set_default_switching_activity -input_activity 0.15
2: Info: EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold.log. In line 1655, logs/EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold.log: 'read_activity_file' finished successfully (tv_chip.tcf) + set_default_switching_activity -input_activity 0.15
3: Info: ND1_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_dynamic.log. In line 1491, logs/ND1_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold_dynamic.log: set_default_switching_activity -input_activity 0.15
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Neither 'read_activity_file' nor 'set_default_switching_activity' command found in log

Log format (CheckList.rpt):
ERROR01:
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log: Neither 'read_activity_file' nor 'set_default_switching_activity' command found in log
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-03:
  description: "Confirm activity file was used? If not, provide default switching activity values in comments field."
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
      - "Explanation: Activity configuration check is informational only for early-stage power analysis"
      - "Note: Missing activity files are expected during initial design exploration - defaults are acceptable"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: Activity configuration check is informational, missing activity files acceptable during early design phases

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Activity configuration check is informational only for early-stage power analysis"
  - "Note: Missing activity files are expected during initial design exploration - defaults are acceptable"
INFO02:
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Activity configuration check is informational only for early-stage power analysis. [WAIVED_INFO]
2: Info: Note: Missing activity files are expected during initial design exploration - defaults are acceptable. [WAIVED_INFO]
3: Info: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log: Neither 'read_activity_file' nor 'set_default_switching_activity' command found in log [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-03:
  description: "Confirm activity file was used? If not, provide default switching activity values in comments field."
  requirements:
    value: 2
    pattern_items:
      - "'read_activity_file' finished successfully"
      - "'set_default_switching_activity' finished successfully"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches for activity configuration patterns in Voltus logs. The checker validates that each log file contains at least one of the required activity configuration patterns (either activity file read or default values set). PASS if all pattern_items are satisfied across the log files (at least one valid configuration method found per file). FAIL if any log file is missing both configuration patterns.

**Sample Output (PASS):**
```
Status: PASS
Reason: 'read_activity_file' finished successfully

Log format (CheckList.rpt):
INFO01:
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.log

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.log. In line 245, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.log: 'read_activity_file' finished successfully
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-03:
  description: "Confirm activity file was used? If not, provide default switching activity values in comments field."
  requirements:
    value: 2
    pattern_items:
      - "'read_activity_file' finished successfully"
      - "'set_default_switching_activity' finished successfully"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Activity configuration validation is informational during early power analysis iterations"
      - "Note: Pattern mismatches are expected when activity files are not yet available - defaults are acceptable"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: Pattern check is informational, mismatches expected during early design phases

**Sample Output (PASS with mismatches):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Activity configuration validation is informational during early power analysis iterations"
  - "Note: Pattern mismatches are expected when activity files are not yet available - defaults are acceptable"
INFO02:
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Activity configuration validation is informational during early power analysis iterations. [WAIVED_INFO]
2: Info: Note: Pattern mismatches are expected when activity files are not yet available - defaults are acceptable. [WAIVED_INFO]
3: Info: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log: Required activity configuration pattern not satisfied - no valid activity setup detected [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-03:
  description: "Confirm activity file was used? If not, provide default switching activity values in comments field."
  requirements:
    value: 2
    pattern_items:
      - "'read_activity_file' finished successfully"
      - "'set_default_switching_activity' finished successfully"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 2
    waive_items:
      - name: "ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log"
        reason: "EM analysis uses conservative defaults - activity file not required per design review"
      - name: "ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log"
        reason: "Test mode static analysis waived - using default activity acceptable for this corner"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Search for activity configuration patterns in each log file
- Match log files with missing configurations against waive_items by filename
- Unwaived missing configurations → ERROR (need fix)
- Waived missing configurations → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all log files with missing configurations are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log
WARN01:
  - ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log: Activity configuration violation waived per design team approval: EM analysis uses conservative defaults - activity file not required per design review [WAIVER]
Warn Occurrence: 1
1: Warn: ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log: Waiver not matched - no corresponding activity configuration issue found in log: Test mode static analysis waived - using default activity acceptable for this corner [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-03:
  description: "Confirm activity file was used? If not, provide default switching activity values in comments field."
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
      - name: "ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log"
        reason: "EM analysis uses conservative defaults - activity file not required per design review"
      - name: "ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log"
        reason: "Test mode static analysis waived - using default activity acceptable for this corner"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (log filenames with missing configurations)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Validate activity configuration exists in each log file
- Match log files with missing configurations against waive_items by filename
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
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log
WARN01:
  - ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_EM.log: Activity configuration violation waived per design team approval: EM analysis uses conservative defaults - activity file not required per design review [WAIVER]
Warn Occurrence: 1
1: Warn: ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/ND1_test_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold_static.log: Waiver not matched - no corresponding activity configuration issue found in log: Test mode static analysis waived - using default activity acceptable for this corner [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-03 --force

# Run individual tests
python IMP-11-0-0-03.py
```

---

## Notes

**Implementation Details:**
- The checker prioritizes `read_activity_file` over `set_default_switching_activity` when both are present
- When default switching activity is used, the checker extracts and reports parameter values (-input_activity, -period) in the comments field
- Multiple `set_default_switching_activity` commands in one log: the checker uses the last occurrence
- The checker associates activity configuration with analysis corner by extracting corner information from log filename

**Known Limitations:**
- The checker only validates command execution success patterns, not the actual activity data quality
- Compressed or encrypted activity files are not validated beyond the command success message
- If activity file path is present but no success confirmation exists, the checker will check for error messages but may not catch all failure modes

**Edge Cases:**
- If neither `read_activity_file` nor `set_default_switching_activity` is found, the checker reports ERROR with clear message
- If activity file read command is present but failed, the checker treats it as missing configuration (FAIL)
- Partial parameter extraction from `set_default_switching_activity`: the checker reports only available parameters