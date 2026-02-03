# IMP-11-0-0-19: Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)

## Overview

**Check ID:** IMP-11-0-0-19  
**Description:** Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)  
**Category:** Power Analysis Validation  
**Input Files:** 
- `${CHECKLIST_ROOT}\IP_project_folder\reports\11.0\Powerup.rpt`

This checker validates the completeness and correctness of the powerup simulation report. It verifies that all power switch cells turned on properly during the power-up sequence, extracts critical metrics (rush current and wake-up time), and identifies the first and last power switches to activate. The checker ensures designers are aware of these metrics to confirm compliance with customer requirements.

---

## Check Logic

### Input Parsing

The checker parses the Powerup.rpt file to extract power-up simulation metrics and validate power switch activation.

**Key Patterns:**

```python
# Pattern 1: Extract maximum rush current measurement
pattern_rush_current = r'Measured maximum rush current\s*=\s*([0-9.eE+-]+)A'
# Example: "\tMeasured maximum rush current          = 0.427297A"

# Pattern 2: Extract wake-up time for switched net
pattern_wakeup_time = r'Measured wake-up time for switched net\s*=\s*([0-9.eE+-]+)s'
# Example: "\tMeasured wake-up time for switched net = 6.11e-08s"

# Pattern 3: Extract total number of power switches
pattern_switch_count = r'Number of power switches turned on in this simulation\s*=\s*(\d+)\s*\[of total\s*(\d+)\]'
# Example: "\tNumber of power switches turned on in this simulation = 28215 [of total 28215]"

# Pattern 4: Extract last power switch turn-on information
pattern_last_switch = r"Last power switch to turn-on in this simulation is '([^']+)' at time\s*([0-9.eE+-]+)s"
# Example: "\tLast power switch to turn-on in this simulation is 'cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18559:NSLEEPIN' at time 4.50069e-07s."

# Pattern 5: Extract first power switch turn-on (from Detailed Report section)
pattern_first_switch = r"^\s*([^\s]+)\s+([0-9.eE+-]+)s"
# Example: "cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_0:NSLEEPIN    1.00e-09s"

# Pattern 6: Extract simulation metadata
pattern_sim_time = r'Simulation time\s*=\s*([0-9.eE+-]+)s'
pattern_threshold = r'Threshold \(Vt\)\s*=\s*([0-9.]+)V'
# Example: "\tSimulation time = 4.50155e-07s"
# Example: "\tThreshold (Vt)  = 0.675V"
```

### Detection Logic

1. **Completeness Check**:
   - Verify the report contains the "Summary" section
   - Confirm rush current and wake-up time values are present
   - Validate that switch count information exists

2. **Correctness Validation**:
   - Extract switches_turned_on and total_switches counts
   - Compare: If switches_turned_on == total_switches, all switches activated properly
   - If mismatch detected, report ERROR with details

3. **First/Last Switch Extraction**:
   - Parse "Detailed Report" section to find first switch (earliest timestamp)
   - Extract last switch from Summary section
   - Output both switch instances with their activation times

4. **Metric Extraction**:
   - Extract rush_current value (in Amperes)
   - Extract wake_up_time value (in seconds, scientific notation)
   - Format output with units for clarity

5. **Customer Requirement Reminder**:
   - Output extracted metrics in INFO section
   - Include reminder: "Please confirm your wake-up time and rush current followed customer requirements"
   - This reminder appears as the last INFO item (line 6) after all metrics

6. **Edge Cases**:
   - Missing Summary section → Report incomplete file error
   - Partial switch activation (turned_on < total) → Report activation failure
   - Missing rush current or wake-up time → Report incomplete data error
   - Scientific notation variations (e.g., 1.23e-07 vs 1.23E-07) → Handle case-insensitively

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

**Rationale:** This checker validates that critical powerup simulation metrics (rush current, wake-up time, switch activation counts) EXIST in the Powerup.rpt file. It extracts these values and presents them to the user for confirmation against customer requirements. The checker does not validate whether the values meet specific thresholds - it only confirms that the required metrics are present in the report. The output includes all extracted metrics with a reminder for the user to verify compliance with customer specifications, making this an existence/completeness check rather than a status validation check.

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
item_desc = "Powerup simulation report validation - rush current and wake-up time analysis"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Powerup report complete with all required metrics found"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All power switches activated successfully, metrics validated"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Powerup report contains rush current, wake-up time, and complete switch activation data"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All power switches turned on successfully (28215/28215), rush current and wake-up time metrics validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Powerup report incomplete or missing required metrics"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Power switch activation incomplete or metrics missing"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required rush current or wake-up time data not found in powerup report"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Power switch activation failed (partial activation detected) or required metrics not satisfied"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Powerup report issues waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Powerup simulation metrics waived - customer requirements confirmed separately"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused powerup waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding powerup issue found in report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items - each metric on separate line):
  Each metric displayed individually with line number and file path:
  - "Rush Current: [value]A. In line [N], [file_path]"
  - "Wake-up Time: [value]s. In line [N], [file_path]"
  - "Switches: [turned_on]/[total]. In line [N], [file_path]"
  - "First Switch: [instance] @ [time]s. In line [N], [file_path]"
  - "Last Switch: [instance] @ [time]s. In line [N], [file_path]"
  - "Please confirm your wake-up time and rush current followed customer requirements" (last line, no line number)

  Example:
    1: Info: Rush Current: 0.427297A. In line 8, C:\...\Powerup.rpt
    2: Info: Wake-up Time: 1.11e-07s. In line 9, C:\...\Powerup.rpt
    3: Info: Switches: 28215/28215. In line 11, C:\...\Powerup.rpt
    4: Info: First Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18497:NSLEEPIN @ 7.33883e-10s. In line 21, C:\...\Powerup.rpt
    5: Info: Last Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18559:NSLEEPIN @ 4.50069e-07s. In line 12, C:\...\Powerup.rpt
    6: Info: Please confirm your wake-up time and rush current followed customer requirements

ERROR01 (Violation/Fail items):
  Format: "[ERROR_TYPE]: [details]"
  Example: "INCOMPLETE ACTIVATION: Only 28000/28215 power switches turned on - 215 switches failed to activate"
  Example: "MISSING METRIC: Rush current value not found in powerup report Summary section"
  Example: "MISSING METRIC: Wake-up time value not found in powerup report Summary section"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-19:
  description: "Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of the powerup report:
- Validates report completeness (Summary section exists)
- Checks all power switches activated (turned_on == total)
- Confirms rush current and wake-up time metrics are present
- Extracts first and last switch activation details
- PASS if all validations succeed, FAIL if any check fails

**Sample Output (PASS):**
```
Status: PASS
Reason: Powerup report contains rush current, wake-up time, and complete switch activation data
INFO Occurrence: 6
1: Info: Rush Current: 0.427297A. In line 8, C:\Users\...\Powerup.rpt: Powerup report contains rush current, wake-up time, and complete switch activation data
2: Info: Wake-up Time: 1.11e-07s. In line 9, C:\Users\...\Powerup.rpt: Powerup report contains rush current, wake-up time, and complete switch activation data
3: Info: Switches: 28215/28215. In line 11, C:\Users\...\Powerup.rpt: Powerup report contains rush current, wake-up time, and complete switch activation data
4: Info: First Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18497:NSLEEPIN @ 7.33883e-10s. In line 21, C:\Users\...\Powerup.rpt: Powerup report contains rush current, wake-up time, and complete switch activation data
5: Info: Last Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18559:NSLEEPIN @ 4.50069e-07s. In line 12, C:\Users\...\Powerup.rpt: Powerup report contains rush current, wake-up time, and complete switch activation data
6: Info: Please confirm your wake-up time and rush current followed customer requirements
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required rush current or wake-up time data not found in powerup report
ERROR Occurrence: 2
1: Error: INCOMPLETE ACTIVATION: Only 28000/28215 power switches turned on - 215 switches failed to activate
2: Error: MISSING METRIC: Rush current value not found in powerup report Summary section
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-19:
  description: "Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Powerup metrics are informational only for this non-PSO design"
      - "Note: Rush current and wake-up time validation deferred to customer review"
      - "Rationale: Design does not use power switch optimization (PSO), powerup analysis not applicable"
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
INFO Occurrence: 5
1: Info: [WAIVED_INFO] Explanation: Powerup metrics are informational only for this non-PSO design
2: Info: [WAIVED_INFO] Note: Rush current and wake-up time validation deferred to customer review
3: Info: [WAIVED_INFO] Rationale: Design does not use power switch optimization (PSO), powerup analysis not applicable
4: Info: [WAIVED_AS_INFO] INCOMPLETE ACTIVATION: Only 28000/28215 power switches turned on - 215 switches failed to activate
5: Info: [WAIVED_AS_INFO] MISSING METRIC: Rush current value not found in powerup report Summary section
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-19:
  description: "Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)"
  requirements:
    value: 2
    pattern_items:
      - "Rush Current"
      - "Wake-up Time"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items represent expected rush current and wake-up time metrics
- Use simplified format: "Rush Current: [value]A" and "Wake-up Time: [value]s"
- Values extracted from powerup report Summary section
- These are golden values for validation, NOT full display format

**Check Behavior:**
Type 2 searches for expected rush current and wake-up time values in the powerup report.
PASS if all pattern_items (expected metrics) are found and validated.
FAIL if any expected metric is missing or does not match.

**Sample Output (PASS):**
```
Status: PASS
Reason: All power switches turned on successfully (28215/28215), rush current and wake-up time metrics validated
INFO Occurrence: 6
1: Info: Rush Current: 0.427297A. In line 8, C:\Users\...\Powerup.rpt: All power switches turned on successfully, metrics validated
2: Info: Wake-up Time: 1.11e-07s. In line 9, C:\Users\...\Powerup.rpt: All power switches turned on successfully, metrics validated
3: Info: Switches: 28215/28215. In line 11, C:\Users\...\Powerup.rpt: All power switches turned on successfully, metrics validated
4: Info: First Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18497:NSLEEPIN @ 7.33883e-10s. In line 21, C:\Users\...\Powerup.rpt: All power switches turned on successfully, metrics validated
5: Info: Last Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18559:NSLEEPIN @ 4.50069e-07s. In line 12, C:\Users\...\Powerup.rpt: All power switches turned on successfully, metrics validated
6: Info: Please confirm your wake-up time and rush current followed customer requirements
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-19:
  description: "Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)"
  requirements:
    value: 2
    pattern_items:
      - "Rush Current"
      - "Wake-up Time"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Powerup metric validation is informational only for this design phase"
      - "Note: Rush current and wake-up time values will be validated against customer spec in final review"
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
INFO Occurrence: 4
1: Info: [WAIVED_INFO] Explanation: Powerup metric validation is informational only for this design phase
2: Info: [WAIVED_INFO] Note: Rush current and wake-up time values will be validated against customer spec in final review
3: Info: [WAIVED_AS_INFO] METRIC MISMATCH: Expected Rush Current: 0.427297A, found 0.450000A
4: Info: [WAIVED_AS_INFO] MISSING METRIC: Wake-up Time: 6.11e-08s not found in report
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-19:
  description: "Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)"
  requirements:
    value: 2
    pattern_items:
      - "Rush Current"
      - "Wake-up Time"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Rush Current"
        reason: "Waived - rush current is within acceptable range per customer spec (max 0.5A)"
      - name: "Wake-up Time"
        reason: "Waived - wake-up time meets customer requirement (max 100ns)"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Pattern items represent rush current and wake-up time metrics
- waive_items.name must use SAME format as pattern_items
- Format: "Rush Current: [value]A" and "Wake-up Time: [value]s"
- DO NOT use full display format or error messages

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found metrics against waive_items
- Unwaived items → ERROR (need customer confirmation)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found metrics are waived or validated.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO Occurrence: 8
1: Info: Rush Current: 0.427297A. In line 8, C:\Users\...\Powerup.rpt [WAIVER]
2: Info: Wake-up Time: 1.11e-07s. In line 9, C:\Users\...\Powerup.rpt [WAIVER]
3: Info: Switches: 28215/28215. In line 11, C:\Users\...\Powerup.rpt [WAIVER]
4: Info: First Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18497:NSLEEPIN @ 7.33883e-10s. In line 21, C:\Users\...\Powerup.rpt [WAIVER]
5: Info: Last Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18559:NSLEEPIN @ 4.50069e-07s. In line 12, C:\Users\...\Powerup.rpt [WAIVER]
6: Info: Please confirm your wake-up time and rush current followed customer requirements
WARN Occurrence: 1
1: Warn: Rush Current: 0.500000A: Waiver entry not matched - no corresponding powerup issue found in report [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-19:
  description: "Confirm you are aware of and follow the customers' requirement about wake-up/rush-current if they have.(For non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Rush Current"
        reason: "Waived - rush current 0.427A is within acceptable range per customer spec (max 0.5A)"
      - name: "Wake-up Time"
        reason: "Waived - wake-up time 61.1ns meets customer requirement (max 100ns)"
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
INFO Occurrence: 6
1: Info: Rush Current: 0.427297A. In line 8, C:\Users\...\Powerup.rpt [WAIVER]
2: Info: Wake-up Time: 1.11e-07s. In line 9, C:\Users\...\Powerup.rpt [WAIVER]
3: Info: Switches: 28215/28215. In line 11, C:\Users\...\Powerup.rpt [WAIVER]
4: Info: First Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18497:NSLEEPIN @ 7.33883e-10s. In line 21, C:\Users\...\Powerup.rpt [WAIVER]
5: Info: Last Switch: cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18559:NSLEEPIN @ 4.50069e-07s. In line 12, C:\Users\...\Powerup.rpt [WAIVER]
6: Info: Please confirm your wake-up time and rush current followed customer requirements
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-19 --force

# Run individual tests
python IMP-11-0-0-19.py
```

---

## Notes

**Key Implementation Details:**
1. **Report Structure**: The Powerup.rpt contains two main sections:
   - Summary: Contains aggregated metrics (rush current, wake-up time, switch counts)
   - Detailed Report: Lists individual switch activation times (used to find first switch)

2. **Scientific Notation Handling**: Wake-up time and switch times use scientific notation (e.g., 1.11e-07). The checker must handle both lowercase 'e' and uppercase 'E' formats.

3. **Switch Activation Validation**: The checker compares "switches turned on" vs "total switches" to ensure 100% activation. Partial activation indicates a power-up failure.

4. **First Switch Detection**: The first switch is identified by parsing the Detailed Report section and finding the earliest timestamp (typically 7.33883e-10s or similar).

5. **Line Number Tracking**: Each extracted metric includes its source line number and file path for traceability (e.g., "In line 8, C:\...\Powerup.rpt").

6. **Customer Requirement Reminder**: The checker outputs a reminder prompting designers to validate metrics against customer specifications. This appears as the last INFO item without line number information.

7. **Output Format**: Each metric is displayed on a separate line with complete traceability:
   - Rush Current (line 8)
   - Wake-up Time (line 9)
   - Switches count (line 11)
   - First Switch (line 21 from Detailed Report)
   - Last Switch (line 12 from Summary)
   - Customer reminder (last line)

8. **Non-PSO Designs**: For designs without Power Switch Optimization (PSO), this check may not be applicable. Use Type 1 with waivers.value=0 to mark as informational.

**Limitations:**
- The checker does not validate against specific customer thresholds (max rush current, max wake-up time) as these vary by project
- Assumes standard Powerup.rpt format from Cadence tools
- Does not analyze individual switch timing distributions (only first/last)

**Known Issues:**
- If Detailed Report section is missing, first switch cannot be identified (only last switch from Summary)
- Multiple Powerup.rpt files from different corners are not automatically aggregated