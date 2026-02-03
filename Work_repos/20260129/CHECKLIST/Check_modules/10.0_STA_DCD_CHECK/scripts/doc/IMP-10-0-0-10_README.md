# IMP-10-0-0-10: Confirm check full path group timing reports (in2out/in2reg/reg2out/reg2reg/default/cgdefault).

## Overview

**Check ID:** IMP-10-0-0-10**Description:** Confirm check full path group timing reports (in2out/in2reg/reg2out/reg2reg/default/cgdefault).**Category:** Timing Analysis - Path Group Reports**Input Files:**

- `IP_project_folder/logs/sta_post_syn.log` - STA log file containing timing report generation commands

**Functional Description:**
This checker verifies that all required timing path group reports were generated during STA (Static Timing Analysis) by parsing the STA log file. The log should contain evidence that timing reports were created for all six standard path groups. Each path group represents a critical timing domain that must be analyzed separately. Missing path group reports indicate incomplete timing verification, which could lead to timing violations in silicon.

The six standard path groups to verify:

- **in2out**: Timing from input ports to output ports
- **in2reg**: Timing from input ports to sequential elements
- **reg2out**: Timing from sequential elements to output ports
- **reg2reg**: Timing between sequential elements (most critical)
- **default**: Catch-all for uncategorized paths
- **cgdefault**: Clock gating paths (power management)

---

## Check Logic

### Input Parsing

1. Read the STA log file: `IP_project_folder/logs/sta_post_syn.log`
2. Search for timing report generation commands or report file paths
3. Look for patterns indicating path group reports were created:
   - Files with `_<group>_` pattern (e.g., `phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz`)
   - `report_timing -group <group>` commands
   - References to `timing_<group>.rpt` files
   - Path group names in timing analysis sections
4. Extract metadata for found path groups:
   - Line number where reference was found
   - Full line content (to extract report file path)
5. Determine which path groups are missing from the log
6. Extract report file paths from log lines (text after `>` character in commands)

### Detection Logic

1. **Type 1 (Default)**: Boolean check - all path groups must be present in log

   - PASS: All 6 path groups found in log
   - FAIL: Any path group missing from log
   - Output: Report file paths for found groups, group names for missing groups
2. **Type 2**: Value check - count-based verification with specific pattern items

   - Check only path groups listed in `pattern_items`
   - Compare: Number of found reports vs `requirements.value` (expected count)
   - PASS: Found count == Expected count
   - FAIL: Found count != Expected count
   - Output: Report file paths for all checked groups
3. **Type 3**: Value check with waiver support

   - Check path groups from `pattern_items`
   - Identify missing groups and check against `waive_items`
   - PASS: All missing groups have valid waivers (no unwaived missing)
   - FAIL: Some missing groups lack waivers
   - Output: 
     - INFO01: Waived missing groups (group name + reason)
     - INFO02: Found groups (report file paths)
     - ERROR01: Unwaived missing groups (group names)
     - WARN01: Unused waivers (group names)
4. **Type 4**: Boolean check with waiver support

   - Check all 6 path groups
   - Similar to Type 3 but no pattern_items filtering
   - PASS: All missing groups have valid waivers
   - FAIL: Some missing groups lack waivers
   - Output: Same format as Type 3
   - Check if missing groups are in `waive_items` list
   - PASS: All missing groups are waived OR no groups missing
   - FAIL: Unwaived groups are missing
4. **Type 4**: Full waiver option

   - Same as Type 3 but for boolean check scenario
   - Allows waiving the entire check if needed

---

## Type 1: Informational Check

**Use Case:** Default mode for simple verification that all path group reports exist. No thresholds, no exceptions.

**Configuration:**

```yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: N/A
  waive_items: []
```

**Check Behavior:**

- Parses STA log file for path group references
- Extracts report file paths from log lines
- **PASS**: All 6 path groups found in log

  ```
  PASS
  Value: 6

  INFO01: All path group reports mentioned in log need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_default_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_cgdefault_hold.tarpt.gz
  ```
- **FAIL**: Any path group missing from log

  ```
  FAIL
  Value: 4

  ERROR01: Missing reports required to be checked
    - cgdefault
    - default

  INFO01: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2reg_hold.tarpt.gz
  ```
    - cgdefault: NOT FOUND

  INFO01: Required path group reports found and need to be checked
    - in2out: Found in line 123
    - in2reg: Found in line 145
    - reg2out: Found in line 167
    - reg2reg: Found in line 189
    - default: Found in line 201
  ```

---

## Type 2: Value Check (No Waivers)

**Use Case:** Enforce exact count of required reports. Useful when only specific path groups are required (e.g., excluding cgdefault for designs without clock gating).

**Configuration:**

```yaml
requirements:
  value: 5
  pattern_items:
    - in2out
    - in2reg
    - reg2out
    - reg2reg
    - default
waivers:
  value: N/A
  waive_items: []
```

**Check Behavior:**

- Checks only the path groups listed in `pattern_items`
- Compares found count vs `requirements.value`
- Extracts report file paths from log
- **PASS**: Exactly 5 reports found (or 4 in example below)

  ```
  PASS
  Value: 4 (Expected: 4)

  INFO01: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2reg_hold.tarpt.gz
  ```
- **FAIL**: Count mismatch

  ```
  FAIL
  Value: 3 (Expected: 4)

  ERROR01: Missing reports required to be checked
    - reg2reg

  INFO01: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
  ```

  ```
  FAIL
  Value: 4 (Expected: 5)

  ERROR01: Missing reports required to be checked
    - timing_reg2reg.rpt: MISSING

  INFO01: Required path group reports found and need to be checked
    - timing_in2out.rpt: Found
    - timing_in2reg.rpt: Found
    - timing_reg2out.rpt: Found
    - timing_default.rpt: Found
  ```

---

## Type 3: Value Check with Waivers

**Use Case:** Allow specific path groups to be missing with documented justification. Example: cgdefault may not apply to designs without clock gating.

**Configuration:**

```yaml
requirements:
  value: 6
  pattern_items:
    - in2out
    - in2reg
    - reg2out
    - reg2reg
    - default
    - cgdefault
waivers:
  value: 1
  waive_items:
    - name: "cgdefault"
      reason: "Design has no clock gating cells - cgdefault not applicable (approved by timing lead)"
```

**Check Behavior:**

- Checks all 6 path groups (from `pattern_items`)
- Missing groups in `waive_items` are marked as waived
- **PASS** (with waiver):

  ```
  PASS
  Value: 4 (2 waived)

  INFO01: The missing reports can be waived
    - cgdefault
    - default

  INFO02: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2reg_hold.tarpt.gz
  ```
- **FAIL** (unwaived missing):

  ```
  FAIL
  Value: 3 (1 waived, 1 unwaived)

  ERROR01: Missing reports required to be checked
    - reg2reg

  INFO01: The missing reports can be waived
    - cgdefault

  INFO02: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
  ```
- **WARN** (unused waiver):

  ```
  PASS
  Value: 6

  WARN01: Unused waivers currently
    - cgdefault

  INFO01: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_default_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_cgdefault_hold.tarpt.gz
  ```

---

## Type 4: Boolean Check with Waivers

**Use Case:** Allow entire check to be waived during early development or when path group analysis is deferred.

**Configuration:**

```yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 1
  waive_items:
    - name: "full_waiver"
      reason: "Pre-implementation phase - timing reports not yet generated (Ticket #12345)"
```

**Check Behavior:**

- Boolean check (all exist vs any missing)
- Can waive entire check failure  
- Same output format as Type 3
- **PASS** (all exist):

  ```
  PASS
  Value: N/A

  INFO01: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_default_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_cgdefault_hold.tarpt.gz
  ```
- **PASS** (waived):

  ```
  PASS
  Value: N/A

  INFO01: The missing reports can be waived
    - cgdefault
    - default

  INFO02: Required path group reports found and need to be checked
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_in2reg_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2out_hold.tarpt.gz
    - reports/func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold/phy_cmn_phase_align_digtop_reg2reg_hold.tarpt.gz
  ```
- **FAIL** (no waiver):

  ```
  FAIL
  Value: N/A

  ERROR01: Missing reports required to be checked
    - cgdefault
    - default
  ```

---

## Testing

### Prepare Test Data

1. **Use existing STA log or create sample:**
   ```powershell
   # Sample log file location
   $logFile = "C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log"

   # Create sample log with all path groups
   @"
   Info: Starting timing analysis...
   Info: Generating timing report for group 'in2out'
   report_timing -group in2out -max_paths 100 > reports/timing_in2out.rpt
   Info: Generating timing report for group 'in2reg'
   report_timing -group in2reg -max_paths 100 > reports/timing_in2reg.rpt
   Info: Generating timing report for group 'reg2out'
   report_timing -group reg2out -max_paths 100 > reports/timing_reg2out.rpt
   Info: Generating timing report for group 'reg2reg'
   report_timing -group reg2reg -max_paths 100 > reports/timing_reg2reg.rpt
   Info: Generating timing report for group 'default'
   report_timing -group default -max_paths 100 > reports/timing_default.rpt
   Info: Generating timing report for group 'cgdefault'
   report_timing -group cgdefault -max_paths 100 > reports/timing_cgdefault.rpt
   Info: Timing analysis complete.
   "@ | Out-File -FilePath $logFile -Encoding utf8
   ```

### Test Commands

```powershell
cd C:\Users\yuyin\Desktop\CHECKLIST\Check_modules\10.0_STA_DCD_CHECK\scripts\checker

# Type 1 (Default) - All path groups in log
python IMP-10-0-0-10.py
# Expected: PASS - "All 6 path groups found in log"

# Type 1 - Simulate missing path group
# Edit sta_post_syn.log, remove the line with 'cgdefault'
python IMP-10-0-0-10.py
# Expected: FAIL - "1 Path group timing reports NOT found in log: cgdefault"

# Type 2 - Count verification
# Edit ../../inputs/items/IMP-10-0-0-10.yaml:
#   requirements:
#     value: 6
#     pattern_items: [in2out, in2reg, reg2out, reg2reg, default, cgdefault]
python IMP-10-0-0-10.py
# Expected: PASS - "Value: 6 (Expected: 6)"

# Type 3 - With waiver
# Edit log to remove 'cgdefault' references
# Edit YAML:
#   requirements:
#     value: 6
#     pattern_items: [in2out, in2reg, reg2out, reg2reg, default, cgdefault]
#   waivers:
#     value: 1
#     waive_items:
#       - name: "cgdefault"
#         reason: "No clock gating in design"
python IMP-10-0-0-10.py
# Expected: PASS - "Value: 5 (1 waived)" with [WAIVER] tag

# Type 4 - Boolean with full waiver
# Edit log to remove all path group references
# Edit YAML:
#   requirements:
#     value: N/A
#   waivers:
#     value: 1
#     waive_items:
#       - name: "full_waiver"
#         reason: "Pre-implementation phase"
python IMP-10-0-0-10.py
# Expected: PASS (waived) - "Check waived: Pre-implementation phase[WAIVER]"
```

### Verify Output Files

After each test, check:

```powershell
# Machine-readable output
cat ../../outputs/IMP-10-0-0-10.yaml

# Human-readable report
cat ../../reports/IMP-10-0-0-10.rpt
```

**Expected Output Structure:**

- **outputs/IMP-10-0-0-10.yaml**: Valid YAML with status, value, details
- **reports/IMP-10-0-0-10.rpt**: Formatted report with severity groups

### Edge Cases

1. **Missing log file:**

   ```powershell
   mv C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log sta_post_syn.log.bak
   python IMP-10-0-0-10.py
   # Expected: FAIL - "Log file not found: sta_post_syn.log"
   mv sta_post_syn.log.bak C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
   ```
2. **Empty log file:**

   ```powershell
   echo "" > C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\logs\sta_post_syn.log
   python IMP-10-0-0-10.py
   # Expected: FAIL - "No path groups found in log"
   # Restore original log
   ```
3. **Invalid configuration:**

   ```powershell
   # Edit YAML with invalid value type
   # requirements.value: "not_a_number"
   python IMP-10-0-0-10.py
   # Expected: ConfigurationError with clear message
   ```

---

## Notes

- **Input source**: Parses STA log file, not individual report files
- **Search patterns**: Looks for path group names (in2out, in2reg, etc.) in log content
- **Case sensitivity**: Path group names are case-sensitive
- **Log format**: Compatible with standard STA tools (PrimeTime, Tempus, etc.)
- **Waiver justification**: Always include ticket numbers or approval references in waiver reasons
- **Pattern matching**: Checks for exact path group name strings in log
- **Performance**: Very fast (~50ms) as it only parses one log file
- **Common failures**:
  - Missing cgdefault (design has no clock gating)
  - Missing in2out/reg2out (pure combinational or sequential design)
  - Log file not generated or truncated
  - Wrong log file path in configuration
