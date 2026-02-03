# IMP-11-0-0-10: Confirm static power analysis results matches the requirement.

## Overview

**Check ID:** IMP-11-0-0-10  
**Description:** Confirm static power analysis results matches the requirement.  
**Category:** Power Analysis Validation  
**Input Files:** 
- VDD_VSS_div.iv (Static IR drop analysis report)
- results_VDD (VDD power rail analysis results)
- results_VSS (VSS power rail analysis results)

This checker validates static power analysis results against design requirements by:
1. Calculating Static IR Drop percentage from VDD_VSS_div.iv file (NOMINAL_VOLTAGE vs first instance DIV value)
2. Extracting Maximum Current Density (J/JMAX) from results_VDD and results_VSS files
3. Verifying all metrics meet their respective thresholds (Static_IR_Drop < 3%, Power_EM < 1.0)

---

## Check Logic

### Input Parsing

**File 1: VDD_VSS_div.iv - Static IR Drop Analysis**

This file contains instance-level voltage drop data. The checker extracts:
1. NOMINAL_VOLTAGE from header
2. First instance after BEGIN marker and its DIV value
3. Calculates: Static_IR_Drop = (NOMINAL_VOLTAGE - first_instance_DIV) / NOMINAL_VOLTAGE * 100%

**Key Patterns:**
```python
# Pattern 1: Extract nominal voltage from header
pattern_nominal = r'^NOMINAL_VOLTAGE\s+([\d.]+)'
# Example: "NOMINAL_VOLTAGE 0.825"
# Captures: group(1) = "0.825"

# Pattern 2: Identify data section start
pattern_begin = r'^BEGIN\s*$'
# Example: "BEGIN"

# Pattern 3: Extract first instance DIV value after BEGIN
pattern_instance = r'^-\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)'
# Example: "- inst_phy_dsfds/inst_phy_dssm_top/CTSfdinv_01010 0.888 0.999 0.00534 DCCKND4BWP210H6P51CNODULVT VDD VSS VDDG VSS"
# Captures: group(1) = instance_name, group(2) = pwr_iv (0.888), group(3) = gnd_iv, group(4) = div (0.00534)
# Note: According to user hints, the first number after instance name (0.888) is the DIV value to use
```

**File 2: results_VDD / results_VSS - Current Density Analysis**

These files contain power rail analysis results. The checker extracts Maximum Current Density (J/JMAX) from the "Results for rj:" section.

**Key Patterns:**
```python
# Pattern 1: Section header for current density results
pattern_rj_section = r'^Results for rj:\s*$'
# Example: "Results for rj:"

# Pattern 2: Extract maximum current density value
pattern_jmax = r'Minimum, Average, Maximum Current Density \(J/JMAX\):\s*([\d.eE+-]+),\s*([\d.eE+-]+),\s*([\d.eE+-]+)'
# Example: "	Minimum, Average, Maximum Current Density (J/JMAX): 0, 0.00140201, 0.890732"
# Captures: group(1) = minimum, group(2) = average, group(3) = maximum (0.890732)
```

### Detection Logic

**Step 1: Parse VDD_VSS_div.iv for Static IR Drop**
1. Read file line-by-line
2. Extract NOMINAL_VOLTAGE from header (e.g., 0.825V)
3. Find BEGIN marker
4. Parse first instance line after BEGIN
5. Extract first numeric value after instance name as DIV (per user hints: this is the instance's voltage, not the traditional DIV column)
6. Calculate: Static_IR_Drop_percent = (NOMINAL_VOLTAGE - first_instance_DIV) / NOMINAL_VOLTAGE * 100
7. Check: Static_IR_Drop_percent < 3.0% → PASS, else FAIL

**Step 2: Parse results_VDD for VDD Power EM**
1. Read file line-by-line
2. Locate "Results for rj:" section
3. Find line containing "Minimum, Average, Maximum Current Density (J/JMAX):"
4. Extract third value (maximum J/JMAX) as VDD_Power_EM
5. Check: VDD_Power_EM < 1.0 → PASS, else FAIL

**Step 3: Parse results_VSS for VSS Power EM**
1. Same logic as Step 2 for results_VSS file
2. Extract maximum J/JMAX as VSS_Power_EM
3. Check: VSS_Power_EM < 1.0 → PASS, else FAIL

**Step 4: Aggregate Results**
- Overall PASS: All three metrics meet requirements
- Overall FAIL: Any metric exceeds threshold
- Report all metrics with actual values and targets in output

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

**Rationale:** This checker validates the status of specific power metrics (Static_IR_Drop, VDD_Power_EM, VSS_Power_EM) against threshold requirements. The pattern_items represent the metrics to check, and the checker reports whether each metric's status (value vs threshold) is correct. Only the specified metrics are validated and reported.

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
item_desc = "Confirm static power analysis results matches the requirement."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All power analysis metrics found and meet requirements"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All power analysis metrics meet requirements (3/3 passed)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Static IR Drop and Power EM metrics found and validated successfully"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All power metrics matched requirements and validated successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Power analysis metrics not found or parsing failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Power analysis metrics exceed requirements (violations detected)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required power analysis data not found in input files"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Power metric exceeds threshold requirement"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived power analysis violations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Power analysis violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused power analysis waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding power violation found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [metric_name]: [value] (target: [threshold]) - [found_reason]"
  Example: "- Static_IR_Drop: 1.45% (target: <3.0%) - All power metrics matched requirements and validated successfully"
  Example: "- VDD_Power_EM: 0.891 (target: <1.0) - All power metrics matched requirements and validated successfully"

ERROR01 (Violation/Fail items):
  Format: "- [metric_name]: [value] (target: [threshold]) - [missing_reason]"
  Example: "- Static_IR_Drop: 3.52% (target: <3.0%) - Power metric exceeds threshold requirement"
  Example: "- VSS_Power_EM: 1.123 (target: <1.0) - Power metric exceeds threshold requirement"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-10:
  description: "Confirm static power analysis results matches the requirement."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\VDD_VSS_div.iv"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VDD"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VSS"
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
Reason: Static IR Drop and Power EM metrics found and validated successfully
INFO01:
  - Static_IR_Drop: 1.45% (target: <3.0%) - Static IR Drop and Power EM metrics found and validated successfully
  - VDD_Power_EM: 0.891 (target: <1.0) - Static IR Drop and Power EM metrics found and validated successfully
  - VSS_Power_EM: 0.548 (target: <1.0) - Static IR Drop and Power EM metrics found and validated successfully
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required power analysis data not found in input files
ERROR01:
  - Static_IR_Drop: Unable to parse (NOMINAL_VOLTAGE not found) - Required power analysis data not found in input files
  - VDD_Power_EM: Unable to parse (Results for rj section missing) - Required power analysis data not found in input files
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-10:
  description: "Confirm static power analysis results matches the requirement."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\VDD_VSS_div.iv"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VDD"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VSS"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power analysis violations are informational only during early design phase"
      - "Note: IR drop and EM violations will be addressed in final optimization pass"
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
  - "Explanation: Power analysis violations are informational only during early design phase"
  - "Note: IR drop and EM violations will be addressed in final optimization pass"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Static_IR_Drop: 3.52% (target: <3.0%) - Required power analysis data not found in input files [WAIVED_AS_INFO]
  - VDD_Power_EM: 1.123 (target: <1.0) - Required power analysis data not found in input files [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-10:
  description: "Confirm static power analysis results matches the requirement."
  requirements:
    value: 3
    pattern_items:
      - "Static_IR_Drop"
      - "VDD_Power_EM"
      - "VSS_Power_EM"
  input_files:
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\VDD_VSS_div.iv"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VDD"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VSS"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items represent the three power metrics to validate
- Each metric has a specific threshold: Static_IR_Drop < 3%, Power_EM < 1.0
- Checker extracts actual values and compares against thresholds
- found_items = metrics that meet requirements
- missing_items = metrics that exceed thresholds (violations)

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All power metrics matched requirements and validated successfully
INFO01:
  - Static_IR_Drop: 1.45% (target: <3.0%) - All power metrics matched requirements and validated successfully
  - VDD_Power_EM: 0.891 (target: <1.0) - All power metrics matched requirements and validated successfully
  - VSS_Power_EM: 0.548 (target: <1.0) - All power metrics matched requirements and validated successfully
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-10:
  description: "Confirm static power analysis results matches the requirement."
  requirements:
    value: 3
    pattern_items:
      - "Static_IR_Drop"
      - "VDD_Power_EM"
      - "VSS_Power_EM"
  input_files:
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\VDD_VSS_div.iv"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VDD"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VSS"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power analysis violations are informational during pre-layout phase"
      - "Note: IR drop and EM metrics will be optimized after placement refinement"
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
  - "Explanation: Power analysis violations are informational during pre-layout phase"
  - "Note: IR drop and EM metrics will be optimized after placement refinement"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Static_IR_Drop: 3.52% (target: <3.0%) [WAIVED_AS_INFO]
  - VDD_Power_EM: 1.123 (target: <1.0) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-10:
  description: "Confirm static power analysis results matches the requirement."
  requirements:
    value: 3
    pattern_items:
      - "Static_IR_Drop"
      - "VDD_Power_EM"
      - "VSS_Power_EM"
  input_files:
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\VDD_VSS_div.iv"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VDD"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VSS"
  waivers:
    value: 2
    waive_items:
      - name: "Static_IR_Drop"
        reason: "Waived - IR drop acceptable for low-power mode operation per design review"
      - name: "VDD_Power_EM"
        reason: "Waived - EM margin acceptable for target lifetime per reliability analysis"
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
  - Static_IR_Drop: 3.52% (target: <3.0%) - Power analysis violation waived per design team approval: Waived - IR drop acceptable for low-power mode operation per design review [WAIVER]
  - VDD_Power_EM: 1.123 (target: <1.0) - Power analysis violation waived per design team approval: Waived - EM margin acceptable for target lifetime per reliability analysis [WAIVER]
WARN01 (Unused Waivers):
  - VSS_Power_EM: Waiver not matched - no corresponding power violation found: Waived - example unused waiver [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-10:
  description: "Confirm static power analysis results matches the requirement."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\VDD_VSS_div.iv"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VDD"
    - "C:\\Users\\zhihan\\projects\\check_development\\CHECKLIST\\CHECKLIST\\IP_project_folder\\reports\\11.0\\results_VSS"
  waivers:
    value: 2
    waive_items:
      - name: "Static_IR_Drop"
        reason: "Waived - IR drop acceptable for low-power mode operation per design review"
      - name: "VDD_Power_EM"
        reason: "Waived - EM margin acceptable for target lifetime per reliability analysis"
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
INFO01 (Waived):
  - Static_IR_Drop: 3.52% (target: <3.0%) - Power analysis violation waived per design team approval: Waived - IR drop acceptable for low-power mode operation per design review [WAIVER]
  - VDD_Power_EM: 1.123 (target: <1.0) - Power analysis violation waived per design team approval: Waived - EM margin acceptable for target lifetime per reliability analysis [WAIVER]
WARN01 (Unused Waivers):
  - VSS_Power_EM: Waiver not matched - no corresponding power violation found: Waived - example unused waiver [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-10 --force

# Run individual tests
python IMP-11-0-0-10.py
```

---

## Notes

**Implementation Details:**
1. **Static IR Drop Calculation**: Per user hints, the first numeric value after the instance name in VDD_VSS_div.iv (column 2) represents the instance's power rail voltage. The DIV value is calculated as: (NOMINAL_VOLTAGE - first_instance_voltage) / NOMINAL_VOLTAGE * 100%

2. **Power EM Extraction**: Maximum Current Density (J/JMAX) is extracted from the third value in the "Minimum, Average, Maximum Current Density (J/JMAX):" line within the "Results for rj:" section.

3. **Threshold Requirements**:
   - Static_IR_Drop: Must be < 3.0%
   - VDD_Power_EM: Must be < 1.0
   - VSS_Power_EM: Must be < 1.0

4. **Error Handling**:
   - Missing NOMINAL_VOLTAGE → Report parsing error
   - Missing BEGIN marker → Report parsing error
   - Missing "Results for rj:" section → Report parsing error
   - Malformed data lines → Skip and report warning

5. **Output Format**: All metrics are reported with actual values, target thresholds, and pass/fail status for clear traceability.

**Known Limitations:**
- Checker assumes VDD_VSS_div.iv follows the exact format with BEGIN marker and instance data
- Scientific notation in current density values must be handled correctly (e.g., 1.23e-05)
- Large instance counts (2M+) may require efficient parsing strategies