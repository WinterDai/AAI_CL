# IMP-11-0-0-20: Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)

## Overview

**Check ID:** IMP-11-0-0-20  
**Description:** Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)  
**Category:** Power Analysis - Wake-up Time Validation  
**Input Files:** 
- `${CHECKLIST_ROOT}\IP_project_folder\reports\11.0\Powerup.rpt`

This checker validates that the measured wake-up time for power switch turn-on sequences meets customer specifications. It verifies that all power switches are properly activated and that the wake-up time is within acceptable limits. For non-PSO (Power Shut-Off) designs, this check should be marked as N/A.

The checker performs three critical validations:
1. Verifies all power switches are turned on during simulation
2. Extracts the measured wake-up time from the simulation report
3. Compares the measured wake-up time against customer requirements

---

## Check Logic

### Input Parsing

The checker parses the Powerup.rpt file which contains power switch simulation results including rush current analysis, wake-up time measurements, and power gate turn-on sequence data.

**Key Patterns:**

```python
# Pattern 1: Extract measured wake-up time from summary section
pattern_wake_up_time = r'Measured wake-up time for switched net\s*=\s*([0-9.eE+-]+)s'
# Example: "\tMeasured wake-up time for switched net = 6.11e-08s"

# Pattern 2: Extract power switch activation statistics
pattern_switch_stats = r'Number of power switches turned on in this simulation\s*=\s*(\d+)\s*\[of total\s*(\d+)\]'
# Example: "\tNumber of power switches turned on in this simulation = 28215 [of total 28215]"

# Pattern 3: Extract simulation metadata (time and threshold voltage)
pattern_sim_time = r'Simulation time\s*=\s*([0-9.eE+-]+)s'
pattern_threshold = r'Threshold \(Vt\)\s*=\s*([0-9.]+)V'
# Example: "\tSimulation time = 4.50155e-07s"
# Example: "\tThreshold (Vt)  = 0.675V"

# Pattern 4: Extract maximum rush current
pattern_rush_current = r'Measured maximum rush current\s*=\s*([0-9.eE+-]+)A'
# Example: "\tMeasured maximum rush current          = 0.427297A"

# Pattern 5: Extract last power switch turn-on information
pattern_last_switch = r"Last power switch to turn-on in this simulation is '([^']+)' at time ([0-9.eE+-]+)s"
# Example: "\tLast power switch to turn-on in this simulation is 'cdns_lp6_x48_ew_phy_top_SW_MODULE/PSW_18559:NSLEEPIN' at time 4.50069e-07s."
```

### Detection Logic

**Step 1: File Existence Check**
- Verify Powerup.rpt exists in the specified location
- If file missing → Return ERROR (cannot validate wake-up time)

**Step 2: Parse Summary Section**
- Locate "Summary" section in report (between "Summary" and "Detailed Report" markers)
- Extract key metrics using regex patterns:
  - Measured wake-up time (Pattern 1) - CRITICAL metric
  - Switch statistics (Pattern 2) - Validation completeness check
  - Simulation metadata (Pattern 3) - Context information
  - Rush current (Pattern 4) - Supporting data
  - Last switch info (Pattern 5) - Sequence completion verification

**Step 3: Validate Power Switch Activation**
- Check that `switches_turned_on == total_switches`
- If mismatch → Return ERROR ("Not all power switches activated")
- This ensures simulation completed successfully

**Step 4: Wake-up Time Validation**
- Extract customer requirement specification from pattern_items (expected wake-up time threshold)
- Compare measured wake-up time against requirement:
  - If `measured_wake_up_time <= customer_requirement` → PASS
  - If `measured_wake_up_time > customer_requirement` → FAIL
- Calculate delta for violation reporting: `delta = measured_wake_up_time - customer_requirement`

**Step 5: Edge Case Handling**
- Missing wake-up time value → ERROR ("Wake-up time not found in report")
- Scientific notation parsing → Use `float()` conversion
- Non-PSO design → Return N/A status (no power switches to validate)
- Empty or incomplete simulation → Check for "Summary" keyword presence

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

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

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates wake-up time STATUS against customer requirements. The pattern_items contain the customer requirement threshold value (e.g., "6.5e-08s"). The checker extracts the measured wake-up time from the report and compares it against this threshold. Only the measured value is output, and its status (pass/fail) is determined by comparing against the requirement. This is a status validation check, not an existence check.

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
item_desc = "Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Wake-up time validation completed - all power switches activated"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Wake-up time meets customer requirement"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All power switches turned on and wake-up time found in simulation report"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Measured wake-up time satisfied customer requirement threshold"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Wake-up time validation failed - required data not found in report"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Wake-up time exceeds customer requirement"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Wake-up time value not found in Powerup.rpt or power switches not fully activated"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Measured wake-up time exceeds customer requirement threshold"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Wake-up time requirement waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Wake-up time violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused wake-up time waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding wake-up time violation found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Wake-up time: {measured_value}s (Requirement: {spec_value}s) - PASS"
  Example: "Wake-up time: 6.11e-08s (Requirement: 1.0e-07s) - PASS"

ERROR01 (Violation/Fail items):
  Format: "Wake-up time: {measured_value}s exceeds requirement {spec_value}s by {delta}s"
  Example: "Wake-up time: 1.5e-07s exceeds requirement 1.0e-07s by 5.0e-08s"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-20:
  description: "Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"
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
Type 1 performs custom boolean validation:
1. Verify Powerup.rpt exists
2. Check all power switches are activated (turned_on == total)
3. Verify wake-up time value is present in report
4. PASS if all validations succeed, FAIL otherwise

**Sample Output (PASS):**
```
Status: PASS
Reason: All power switches turned on and wake-up time found in simulation report
INFO01:
  - Wake-up time: 6.11e-08s | Switches: 28215/28215 activated | Rush current: 0.427297A
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Wake-up time value not found in Powerup.rpt or power switches not fully activated
ERROR01:
  - Power switch activation incomplete: 28000/28215 switches turned on
  - Wake-up time measurement missing from Summary section
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-20:
  description: "Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Wake-up time check is informational only for early design stages"
      - "Note: Power switch activation issues are expected during initial integration and do not block tapeout"
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
  - "Explanation: Wake-up time check is informational only for early design stages"
  - "Note: Power switch activation issues are expected during initial integration and do not block tapeout"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Power switch activation incomplete: 28000/28215 switches turned on [WAIVED_AS_INFO]
  - Wake-up time: 1.5e-07s exceeds typical range [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-20:
  description: "Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"
  requirements:
    value: 1
    pattern_items:
      - "1.0e-07"  # Customer requirement: wake-up time must be <= 100ns
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description requires "wake-up time" validation → Use TIME VALUES in seconds
- Pattern items represent customer requirement thresholds (maximum acceptable wake-up time)
- Use scientific notation format matching report output (e.g., "1.0e-07" for 100ns)
- ✅ Correct: "1.0e-07" (time value in seconds)
- ❌ Wrong: "100ns" (different unit), "wake_up_time" (identifier), "PASS" (status)

**Check Behavior:**
Type 2 extracts measured wake-up time and compares against pattern_items threshold.
- Extract measured wake-up time from Powerup.rpt Summary section
- Compare against customer requirement in pattern_items
- PASS if measured_time <= requirement (found_items contains measured value)
- FAIL if measured_time > requirement (missing_items contains violation)

**Sample Output (PASS):**
```
Status: PASS
Reason: Measured wake-up time satisfied customer requirement threshold
INFO01:
  - Wake-up time: 6.11e-08s (Requirement: 1.0e-07s) - PASS
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Measured wake-up time exceeds customer requirement threshold
ERROR01:
  - Wake-up time: 1.5e-07s exceeds requirement 1.0e-07s by 5.0e-08s
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-20:
  description: "Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"
  requirements:
    value: 1
    pattern_items:
      - "1.0e-07"  # Customer requirement threshold
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Wake-up time violations are acceptable for this low-power design"
      - "Note: Customer approved extended wake-up time for power optimization trade-off"
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
  - "Explanation: Wake-up time violations are acceptable for this low-power design"
  - "Note: Customer approved extended wake-up time for power optimization trade-off"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Wake-up time: 1.5e-07s exceeds requirement 1.0e-07s by 5.0e-08s [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-20:
  description: "Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"
  requirements:
    value: 1
    pattern_items:
      - "1.0e-07"  # Customer requirement threshold
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "1.5e-07"  # Waiver threshold: measured time ≤ 1.5e-07s will be waived
        reason: "Wake-up time up to 150ns waived - customer approved for low-power mode operation"
      - name: "2.0e-07"  # Another waiver threshold: measured time ≤ 2.0e-07s will be waived
        reason: "Wake-up time up to 200ns waived - acceptable for deep sleep recovery scenario"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must use TIME VALUES in seconds (scientific notation)
- pattern_items: Customer requirement threshold (e.g., "1.0e-07")
- waive_items.name: Waiver threshold values (e.g., "1.5e-07")
- **IMPORTANT**: Measured wake-up time is waived if it is **LESS THAN OR EQUAL TO** the waive_items.name threshold
- ✅ Correct: pattern_items=["1.0e-07"], waive_items.name="1.5e-07" → measured time ≤ 1.5e-07s will be waived
- ❌ Wrong: Expecting exact match - waiver uses threshold comparison, not exact matching

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same wake-up time comparison logic as Type 2, plus waiver classification:
- Extract measured wake-up time from report
- Compare against requirement threshold in pattern_items
- If violation found (measured_time > pattern_items threshold), check waiver:
  - If measured_time ≤ waive_items.name threshold → Waived violation (INFO with [WAIVER] tag)
  - If measured_time > waive_items.name threshold → Unwaived violation (ERROR)
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Wake-up time: 1.5e-07s exceeds requirement 1.0e-07s by 5.0e-08s [WAIVER]
    (Waived because 1.5e-07s ≤ waiver threshold 1.5e-07s)
WARN01 (Unused Waivers):
  - Waiver threshold 2.0e-07s: Waiver not matched - no corresponding violation found within this threshold
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Measured wake-up time exceeds customer requirement threshold
ERROR01:
  - Wake-up time: 3.0e-07s exceeds requirement 1.0e-07s by 2.0e-07s
    (Not waived because 3.0e-07s > highest waiver threshold 2.0e-07s)
INFO01 (Waived):
  - Wake-up time: 1.5e-07s exceeds requirement 1.0e-07s by 5.0e-08s [WAIVER]
    (Waived because 1.5e-07s ≤ waiver threshold 1.5e-07s)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-20:
  description: "Confirm wake-up time meet customer's requirement. (For non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\11.0\\Powerup.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Power switches"  # Waive switch activation check
        reason: "Power switch activation check waived - incomplete simulation acceptable for early verification stage"
      - name: "Wake-up time"  # Waive wake-up time presence check
        reason: "Wake-up time measurement waived - report format differs for legacy tool version"
```

🛑 CRITICAL RULE for Type 4 waive_items.name:
- Type 4 waives BOOLEAN CHECK violations (existence checks)
- waive_items.name must match the violation item names from Type 1 logic
- Common Type 1 violations: "Power switches" (activation incomplete), "Wake-up time" (not found), "Rush current" (missing)
- ⚠️ DO NOT use time thresholds like Type 3 - Type 4 checks existence, not values
- ✅ Correct: name="Power switches", name="Wake-up time"
- ❌ Wrong: name="1.5e-07" (this is for Type 3 value checks)

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean validation as Type 1 (verify switches activated, wake-up time present), plus waiver classification:
- Perform boolean checks (file exists, switches activated, wake-up time found)
- If violations found, match against waive_items using partial string matching
- Unwaived violations → ERROR (check fails)
- Waived violations → INFO with [WAIVER] tag (check passes)
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Found items):
  - Wake-up time: 1.11e-07s [line 9]
  - Power switches: 28215/28215 activated [line 11]
  - Rush current: 0.427297A [line 8]
```

**Sample Output (with violations partially waived):**
```
Status: FAIL
Reason: Wake-up time value not found in Powerup.rpt or power switches not fully activated
INFO01 (Waived violations):
  - Power switches: 28000/28215 activated [WAIVER] - Incomplete activation waived
ERROR01 (Unwaived violations):
  - Wake-up time: not found in Summary section - Not waived
WARN01 (Unused Waivers):
  - Rush current: Waiver not matched - no corresponding violation found
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-20 --force

# Run individual tests
python IMP-11-0-0-20.py
```

---

## Notes

**Design Applicability:**
- This check is ONLY applicable to PSO (Power Shut-Off) designs with power switch networks
- For non-PSO designs, mark this check as N/A in the checklist
- Checker should detect non-PSO designs (no Powerup.rpt or empty report) and return N/A status

**Wake-up Time Definition:**
- Wake-up time = Time for all power switches to turn on and power domain to reach stable voltage
- Measured from simulation start to when last power switch reaches threshold voltage (Vt)
- Includes rush current settling time and voltage stabilization

**Power Switch Validation:**
- All power switches MUST be activated (turned_on == total_switches)
- Incomplete activation indicates simulation failure or design issue
- Last switch turn-on time should correlate with measured wake-up time

**Customer Requirement Specification:**
- Wake-up time threshold typically specified in customer design requirements document
- Common range: 50ns - 200ns depending on application (mobile, automotive, IoT)
- Tighter requirements for fast wake-up applications (e.g., mobile processors)
- Relaxed requirements for low-power applications (e.g., IoT sensors)

**Scientific Notation Handling:**
- Report uses scientific notation (e.g., 6.11e-08s = 61.1ns)
- Checker must parse using `float()` conversion
- Pattern items should use same notation for consistency

**Edge Cases:**
- Missing Summary section → Return ERROR (incomplete simulation)
- Multiple Powerup.rpt files → Aggregate by taking maximum wake-up time (worst case)
- Zero wake-up time → Return ERROR (invalid measurement)
- Negative wake-up time → Return ERROR (simulation error)

**Related Checks:**
- Rush current validation (separate check for maximum current limits)
- Power switch instance validation (verify correct switch types used)
- Power domain voltage validation (verify stable voltage levels achieved)