# IMP-11-0-0-04: Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field.

## Overview

**Check ID:** IMP-11-0-0-04  
**Description:** Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field.  
**Category:** Power Analysis Verification  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log

This checker validates that Cadence Voltus power analysis (static IR drop, dynamic IR drop, and electromigration) was executed with the correct RC corners and PVT (Process, Voltage, Temperature) corner specifications. It extracts corner information from Voltus log files and reports the PA view, Signal RC corner, and Power/Ground RC corner for each analysis run.

---

## Check Logic

### Input Parsing

The checker parses Voltus log files to extract corner specifications from three key sources:

1. **View Definition File Pattern**: Extracts PA view and PVT corner from `read_view_definition` command
2. **Signal RC Corner**: Extracts from "SPEF files for RC Corner" line in log files
3. **Power/Ground RC Corner**: Extracts from `extraction_tech_file` command or reports "NA" if not found (optional for EM analysis)

**Key Patterns:**

```python
# Pattern 1: Extract view definition file and PVT corner
view_def_pattern = r'read_view_definition\s+\S+/(\S+)_viewdefinition\.tcl'
# Example: "read_view_definition /projects/TC70_LPDDR6_N5P/work/tv_chip/zhaozhao/signoff/signoff-1211b/scr/tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static_viewdefinition.tcl"
# Extracts: "tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static"

# Pattern 2: Extract PVT from view definition basename using pattern "_(\S+)_(\S+)_(\S+c)_"
pvt_pattern = r'_(func|test)_(\w+)_([\d.]+p[\d.]+)v_(m?\d+)c_'
# Example: From "ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static"
# Extracts: process="ffgnp", voltage="0p825v", temperature="125c"

# Pattern 3: Extract Signal RC corner from SPEF files line
signal_rc_pattern = r'SPEF files for RC Corner\s+(\S+):'
# Example: "SPEF files for RC Corner cworst_CCworst_T_125c:"
# Extracts: "cworst_CCworst_T_125c"

# Pattern 4: Extract Power/Ground RC corner from extraction_tech_file
pg_rc_pattern = r'extraction_tech_file\s+(\S+)'
# Example: "extraction_tech_file /path/to/qrc_tech_cbest_CCbest_125c.tch"
# Extracts: "cbest_CCbest_125c" (from filename)
```

### Detection Logic

1. **Parse each log file** (*static*.log, *dynamic*.log, *EM*.log):
   - Scan for `read_view_definition` command to extract PA view basename
   - Extract PVT corner components (process, voltage, temperature) from view definition basename
   - Search for "SPEF files for RC Corner" line to extract Signal RC corner
   - Search for `extraction_tech_file` command to extract Power/Ground RC corner
   - If `extraction_tech_file` not found, set PG RC to "NA" (acceptable for EM analysis which uses `verify_AC_limit` instead of power grid extraction)

2. **Build corner report** for each file:
   - Format: "PA view: {paview}, Signal RC: {signalrc}, PowerGround RC: {pgrc}, PVT is: {process} corner, {voltage}, {temperature}."
   - Example: "PA view: tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static, Signal RC: cworst_CCworst_T_125c, PowerGround RC: cbest_CCbest_125c, PVT is: ffgnp corner, 0p825v, 125c."

3. **Aggregate results** across all log files:
   - Collect all unique corner specifications
   - Report complete list in comments field

4. **Validation**:
   - PASS: All log files contain required corner specifications (PA view, Signal RC, and PVT)
   - FAIL: Missing view definition, Signal RC, or PVT information in any log file
   - NOTE: Power/Ground RC corner is optional and not validated (EM analysis doesn't require it)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates that corner specifications exist and are properly configured in Voltus analysis logs. The pattern_items represent corner configurations to verify (e.g., specific PVT corners, RC corner names). The checker reports which corners were found with correct configuration (found_items) versus which corners have missing or incorrect specifications (missing_items). This is a status validation check, not a simple existence check, because we need to verify the correctness of corner configurations, not just their presence.

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
item_desc = "Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "RC/PVT corner specifications found in Voltus analysis logs"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "RC/PVT corner configuration validated and matched expected specification"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "PA view, Signal RC corner, and Power/Ground RC corner specifications found in log file"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Corner specification matched: PA view, Signal RC, and PG RC corners validated against expected configuration"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "RC/PVT corner specifications not found or incomplete in Voltus analysis logs"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "RC/PVT corner configuration not satisfied - missing or incorrect specification"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Missing corner specification: PA view definition, Signal RC corner, or PVT information not found in log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Corner specification not satisfied: expected PA view, Signal RC corner, or PVT configuration missing or incorrect"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "RC/PVT corner specification waived for this analysis"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Corner specification waived per design team approval - alternative corner configuration accepted"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused corner waiver entry"
unused_waiver_reason = "Waiver not matched - no corresponding corner specification violation found in analysis logs"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [corner_spec]: PA view: {paview}, Signal RC: {signalrc}, PowerGround RC: {pgrc}, PVT is: {process} corner, {voltage}, {temperature}."
  Example: "- ND1_func_ffgnp_0p825v_125c: PA view: tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static, Signal RC: cworst_CCworst_T_125c, PowerGround RC: cbest_CCbest_125c, PVT is: ffgnp corner, 0p825v, 125c."

ERROR01 (Violation/Fail items):
  Format: "- [log_file]: Missing corner specification - [missing_component]"
  Example: "- ND1_func_static.log: Missing corner specification - Signal RC corner not found (SPEF files for RC Corner line missing)"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. The checker formats corner information according to the user-provided hints: "PA view: {paview}, Signal RC: {signalrc}, PowerGround RC: {pgrc}, PVT is: Process corner, voltage, temperature."

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-04:
  description: "Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."
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
Type 1 performs boolean validation: checks if all Voltus log files contain required corner specifications (PA view, Signal RC, and PVT information).
PASS if all log files have complete corner data.
FAIL if any log file is missing required specifications.
NOTE: Power/Ground RC corner is reported but not validated as mandatory (EM analysis doesn't require it).

**Sample Output (PASS):**
```
Status: PASS
Reason: PA view, Signal RC corner, and Power/Ground RC corner specifications found in log file

Log format (CheckList.rpt):
INFO01:
  - ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static: PA view: tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static, Signal RC: cworst_CCworst_T_125c, PowerGround RC: cbest_CCbest_125c, PVT is: ffgnp corner, 0p825v, 125c.
  - EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold: PA view: tv_chip_EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold, Signal RC: cbest_CCbest_T_m40c, PowerGround RC: rcbest_CCbest_m40c, PVT is: ffgnp corner, 0p825v, m40c.

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static. In line 45, logs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.log: PA view, Signal RC corner, and Power/Ground RC corner specifications found in log file
2: Info: EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold. In line 52, logs/EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold.log: PA view, Signal RC corner, and Power/Ground RC corner specifications found in log file
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Missing corner specification: PA view definition, Signal RC corner, or PVT information not found in log file

Log format (CheckList.rpt):
ERROR01:
  - ND1_func_static.log: Missing Signal RC corner (SPEF files for RC Corner line not found)

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: ND1_func_static.log. In line 0, logs/ND1_func_static.log: Missing corner specification: PA view definition, Signal RC corner, or PVT information not found in log file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-04:
  description: "Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."
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
      - "Explanation: This check is informational only - corner specifications are validated separately in timing signoff"
      - "Note: Missing Power/Ground RC corners are expected for early analysis runs and do not require fixes"
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
  - "Explanation: This check is informational only - corner specifications are validated separately in timing signoff"
  - "Note: Missing Power/Ground RC corners are expected for early analysis runs and do not require fixes"
INFO02:
  - ND1_func_static.log: Missing Signal RC corner (SPEF files for RC Corner line not found)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: This check is informational only - corner specifications are validated separately in timing signoff. [WAIVED_INFO]
2: Info: ND1_func_static.log. In line 0, logs/ND1_func_static.log: Missing corner specification: PA view definition, Signal RC corner, or PVT information not found in log file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-04:
  description: "Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."
  requirements:
    value: 3
    pattern_items:
      - "func_ffgnp_0p825v_125c"
      - "func_ffgnp_0p825v_m40c"
      - "test_ssgnp_0p675v_125c"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "rc/PVT corners" → Use CORNER IDENTIFIERS (mode_process_voltage_temperature format)
  ✅ Correct: "func_ffgnp_0p825v_125c" (corner identifier)
  ❌ Wrong: "tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static" (full view name - too detailed)
  ❌ Wrong: "cbest_CCbest_125c" (RC corner only - incomplete)

**Check Behavior:**
Type 2 searches for required PVT corner identifiers in Voltus log files.
PASS if all pattern_items (required corners) are found in the analysis logs.
FAIL if any required corner is missing.

**Sample Output (PASS):**
```
Status: PASS
Reason: Corner specification matched: PA view, Signal RC, and PG RC corners validated against expected configuration

Log format (CheckList.rpt):
INFO01:
  - func_ffgnp_0p825v_125c: PA view: tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static, Signal RC: cworst_CCworst_T_125c, PowerGround RC: cbest_CCbest_125c, PVT is: ffgnp corner, 0p825v, 125c.
  - func_ffgnp_0p825v_m40c: PA view: tv_chip_EM_ND1_func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold, Signal RC: cbest_CCbest_T_m40c, PowerGround RC: rcbest_CCbest_m40c, PVT is: ffgnp corner, 0p825v, m40c.
  - test_ssgnp_0p675v_125c: PA view: tv_chip_ND1_test_ssgnp_0p675v_125c_rcworst_CCworst_T_cworst_CCworst_setup, Signal RC: rcworst_CCworst_T_125c, PowerGround RC: cworst_CCworst_125c, PVT is: ssgnp corner, 0p675v, 125c.

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: func_ffgnp_0p825v_125c. In line 45, logs/ND1_func_ffgnp_0p825v_125c_static.log: Corner specification matched: PA view, Signal RC, and PG RC corners validated against expected configuration
2: Info: func_ffgnp_0p825v_m40c. In line 52, logs/EM_ND1_func_ffgnp_0p825v_m40c_hold.log: Corner specification matched: PA view, Signal RC, and PG RC corners validated against expected configuration
3: Info: test_ssgnp_0p675v_125c. In line 38, logs/ND1_test_ssgnp_0p675v_125c_setup.log: Corner specification matched: PA view, Signal RC, and PG RC corners validated against expected configuration
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-04:
  description: "Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."
  requirements:
    value: 3
    pattern_items:
      - "func_ffgnp_0p825v_125c"
      - "func_ffgnp_0p825v_m40c"
      - "test_ssgnp_0p675v_125c"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - corner coverage is validated in separate timing signoff checklist"
      - "Note: Missing test mode corners are expected for power-only analysis and do not require fixes"
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
  - "Explanation: This check is informational only - corner coverage is validated in separate timing signoff checklist"
  - "Note: Missing test mode corners are expected for power-only analysis and do not require fixes"
INFO02:
  - test_ssgnp_0p675v_125c: Corner not found in analysis logs

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: This check is informational only - corner coverage is validated in separate timing signoff checklist. [WAIVED_INFO]
2: Info: test_ssgnp_0p675v_125c. In line 0, N/A: Corner specification not satisfied: expected PA view or RC corner configuration missing or incorrect [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-04:
  description: "Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."
  requirements:
    value: 3
    pattern_items:
      - "func_ffgnp_0p825v_125c"
      - "func_ffgnp_0p825v_m40c"
      - "test_ssgnp_0p675v_125c"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*static*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*dynamic*.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*EM*.log"
  waivers:
    value: 2
    waive_items:
      - name: "ND1_test_ssgnp_0p675v_125c_setup"
        reason: "Waived - test mode corner not required for power-only EM analysis per design review"
      - name: "ND1_func_rcss_0p675v_m40c_dynamic"
        reason: "Waived - low temperature dynamic analysis skipped per project plan"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found corner violations against waive_items (by analysis view name)
- Unwaived violations → ERROR (need fix)
- Waived violations → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all corner violations are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - ND1_test_ssgnp_0p675v_125c_setup: Missing corner specification (waived)
WARN01:
  - ND1_func_rcss_0p675v_m40c_dynamic: Unused waiver (no corresponding violation found)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: ND1_test_ssgnp_0p675v_125c_setup. In line 0, N/A: Corner specification waived per design team approval - alternative corner configuration accepted: Waived - test mode corner not required for power-only EM analysis per design review [WAIVER]
Warn Occurrence: 1
1: Warn: ND1_func_rcss_0p675v_m40c_dynamic. In line 0, N/A: Waiver not matched - no corresponding corner specification violation found in analysis logs: Waived - low temperature dynamic analysis skipped per project plan [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-04:
  description: "Confirm proper rc/PVT corners were used for IR drop and EM analysis. List rc/PVT corners used in comments field."
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
      - name: "ND1_test_ssgnp_0p675v_125c_setup"
        reason: "Waived - test mode corner not required for power-only EM analysis per design review"
      - name: "ND1_func_rcss_0p675v_m40c_dynamic"
        reason: "Waived - low temperature dynamic analysis skipped per project plan"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (analysis view names)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (validates corner specifications exist), plus waiver classification:
- Match violations (missing corners) against waive_items (by analysis view name)
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
  - ND1_test_ssgnp_0p675v_125c_setup: Missing Signal RC corner (waived)
WARN01:
  - ND1_func_rcss_0p675v_m40c_dynamic: Unused waiver (no corresponding violation found)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: ND1_test_ssgnp_0p675v_125c_setup. In line 0, logs/ND1_test_ssgnp_0p675v_125c_setup.log: Corner specification waived per design team approval - alternative corner configuration accepted: Waived - test mode corner not required for power-only EM analysis per design review [WAIVER]
Warn Occurrence: 1
1: Warn: ND1_func_rcss_0p675v_m40c_dynamic. In line 0, N/A: Waiver not matched - no corresponding corner specification violation found in analysis logs: Waived - low temperature dynamic analysis skipped per project plan [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-04 --force

# Run individual tests
python IMP-11-0-0-04.py
```

---

## Notes

**Important Implementation Details:**

1. **PVT Pattern Extraction**: The checker uses the pattern `_(\S+)_(\S+)_(\S+c)_` to extract PVT components from view definition basename. This matches: mode (func/test), process corner (ffgnp/ssgnp/etc), voltage (0p825v), and temperature (125c/m40c).

2. **Power/Ground RC Corner Handling**: If `extraction_tech_file` command is not found in the log, the checker sets PG RC to "NA". This is expected and acceptable for EM analysis (electromigration) which uses `verify_AC_limit` command and doesn't require power grid extraction. Only IR drop analysis (static/dynamic) typically includes extraction_tech_file.

3. **Output Format**: The checker follows the user-specified format: "PA view: {paview}, Signal RC: {signalrc}, PowerGround RC: {pgrc}, PVT is: Process corner, voltage, temperature."

4. **Multi-File Analysis**: The checker processes all three log types (*static*.log, *dynamic*.log, *EM*.log) and aggregates corner specifications across all files.

5. **Corner Validation**: For Type 2/3, pattern_items should contain PVT corner identifiers in the format "mode_process_voltage_temperature" (e.g., "func_ffgnp_0p825v_125c"), NOT full view definition names or RC corner names alone.

**Known Limitations:**

- The checker assumes Voltus log files follow standard Cadence format with `<CMD>` prefixes for commands
- PVT extraction relies on consistent naming convention in view definition filenames
- If log files are truncated or incomplete, corner extraction may fail