# IMP-8-0-0-09: Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)

## Overview

**Check ID:** IMP-8-0-0-09  
**Description:** Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)  
**Category:** Physical Implementation - Power Optimization Configuration  
**Input Files:** 
- get_default_switching_activity (switching activity parameters)
- getNanoRouteMode (power-driven routing settings)
- getDesignMode (design-level power optimization mode)
- getOptMode (optimizer power effort level)

This checker validates that dynamic power optimization is correctly configured across the entire Innovus physical implementation flow by verifying critical power-related parameters in four configuration files. It ensures switching activity is properly defined, power-driven routing is enabled, design-level power effort is set appropriately, and optimizer power settings are configured for effective dynamic power reduction.

---

## Check Logic

### Input Parsing

This checker parses four configuration files to extract power optimization settings:

**File 1: get_default_switching_activity**
- Format: Parameter-value pairs with `-parameter {value}` syntax
- Extract switching activity configuration parameters
- Key parameters: `input_activity`, `clip_activity_to_domain_freq`

**File 2: getNanoRouteMode**
- Format: Parameter-value pairs with inline comments containing metadata
- Extract power-driven routing configuration
- Key parameters: `route_global_with_power_driven`, `route_global_exp_power_driven_effort`

**File 3: getDesignMode**
- Format: Parameter-value pairs with type/default/status metadata
- Extract design-level power optimization settings
- Key parameters: `powerEffort`, `propagateActivity`

**File 4: getOptMode**
- Format: Parameter-value pairs with type/default/status metadata
- Extract optimizer power effort configuration
- Key parameters: `opt_leakage_to_dynamic_ratio`, `opt_route_type_for_power`, `opt_power_effort`

**Key Patterns:**

```python
# Pattern 1: get_default_switching_activity parameter extraction
pattern1 = r'^-([a-zA-Z_]+)\s+\{\s*([^}]*)\s*\}'
# Example: "-input_activity  {0.15 }"
# Extracts: parameter_name="input_activity", value="0.15"

# Pattern 2: getNanoRouteMode/getDesignMode/getOptMode parameter extraction
pattern2 = r'^-([a-zA-Z_]+)\s+(\S+)\s*(?:#\s*(.+))?'
# Example: "-powerEffort high                       # enums={none low high}, default=none, user setting"
# Extracts: parameter_name="powerEffort", value="high", metadata="enums={none low high}, default=none, user setting"

# Pattern 3: Empty value detection (parameter defined but no value)
pattern3 = r'^-([a-zA-Z_]+)\s+\{\s*\}'
# Example: "-clip_activity_to_domain_freq  { }"
# Extracts: parameter_name="clip_activity_to_domain_freq", value="" (empty)
```

### Detection Logic

**Step 1: Parse all four configuration files**
- Read each file line by line
- Skip comment lines (starting with `#`) and empty lines
- Extract parameter names and values using patterns above
- Store parameters with source file tracking

**Step 2: Validate critical power optimization parameters**

For **get_default_switching_activity**:
- Check `input_activity` is defined and equals `0.15`
- Check `clip_activity_to_domain_freq` is defined and equals `true`
- Empty values `{ }` are treated as undefined → FAIL

For **getNanoRouteMode**:
- Check `route_global_with_power_driven` equals `true`
- Check `route_global_exp_power_driven_effort` equals `medium`

For **getDesignMode**:
- Check `powerEffort` equals `high`
- Check `propagateActivity` equals `true`

For **getOptMode**:
- Check `opt_leakage_to_dynamic_ratio` is defined and equals `0.2`
- Check `opt_route_type_for_power` equals `true`
- Check `opt_power_effort` equals `high`

**Step 3: Determine PASS/FAIL status**
- **PASS**: All critical parameters are correctly configured
- **FAIL**: Any critical parameter is missing, has empty value `{ }`, or has incorrect value
- All non-critical parameters are ignored (not checked or reported)

**Step 4: Generate detailed output**
- For PASS: Print all found power optimization settings with actual parameter values
- For FAIL: Print incorrect/missing settings and show expected correct values
- Format: `getDesignMode -powerEffort high` (command-style format)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

### Mode 2: `status_check` - 状态检查  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["get_default_switching_activity -input_activity 0.15", 
                "getNanoRouteMode -route_global_with_power_driven true"]
Input file contains: input_activity=0.15, route_global_with_power_driven=false

Result:
  found_items:   get_default_switching_activity -input_activity 0.15  ← Pattern matched AND status correct
  missing_items: getNanoRouteMode -route_global_with_power_driven true ← Pattern matched BUT status wrong
  (Other parameters not in pattern_items are ignored)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the STATUS of specific power optimization parameters (whether they are configured with correct values). The pattern_items represent the expected configurations that should exist. The checker only reports on these critical parameters and ignores all others. Items are matched against pattern_items, and their configuration status (correct value vs incorrect/missing) determines PASS/FAIL.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "Dynamic power optimization configuration validation across Innovus flow"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All power optimization settings found and correctly configured"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All required power optimization parameters matched expected configuration (7/7)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All power optimization settings found and correctly configured in all four configuration files"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All required power optimization parameters matched and validated: switching activity configured, power-driven routing enabled, design power effort set to high, optimizer power settings correct"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Required power optimization settings not found or incorrectly configured"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Required power optimization parameters not satisfied (5/7 correct, 2 missing/incorrect)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required power optimization settings not found or incorrectly configured in configuration files"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required power optimization parameters not satisfied: some parameters missing, have empty values, or incorrect configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Power optimization configuration issues waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Power optimization configuration deviation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused power optimization waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding power optimization configuration issue found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items - correctly configured parameters):
  Format: "[source_file] -[parameter_name] [value]"
  Example: "get_default_switching_activity -input_activity 0.15"
  Example: "getNanoRouteMode -route_global_with_power_driven true"
  Example: "getDesignMode -powerEffort high"
  Example: "getOptMode -opt_power_effort high"

ERROR01 (Violation/Fail items - missing or incorrect parameters):
  Format: "[source_file] -[parameter_name] [actual_value] (expected: [expected_value])"
  Example: "get_default_switching_activity -input_activity { } (expected: 0.15) - Parameter value not defined"
  Example: "getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled"
  Example: "getDesignMode -powerEffort none (expected: high) - Design power effort not configured"
  Example: "getOptMode -opt_leakage_to_dynamic_ratio <missing> (expected: 0.2) - Parameter not found in file"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-09:
  description: "Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\get_default_switching_activity
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getNanoRouteMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getDesignMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getOptMode
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of power optimization configuration across all four files. The checker validates that all 7 critical parameters are correctly configured. PASS if all parameters meet requirements, FAIL if any parameter is missing, empty, or has incorrect value.

**Sample Output (PASS):**
```
Status: PASS
Reason: All power optimization settings found and correctly configured in all four configuration files
INFO01:
  - get_default_switching_activity -input_activity 0.15
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_with_power_driven true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -powerEffort high
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
  - getOptMode -opt_route_type_for_power true
  - getOptMode -opt_power_effort high
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required power optimization settings not found or incorrectly configured in configuration files
ERROR01:
  - get_default_switching_activity -input_activity { } (expected: 0.15) - Parameter value not defined
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled
  - getDesignMode -powerEffort none (expected: high) - Design power effort not configured
INFO01:
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
  - getOptMode -opt_route_type_for_power true
  - getOptMode -opt_power_effort high
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-09:
  description: "Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\get_default_switching_activity
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getNanoRouteMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getDesignMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getOptMode
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power optimization configuration check is informational only for early design stages"
      - "Note: Some power settings may not be finalized during initial implementation and do not require immediate fixes"
      - "Rationale: Design team will configure final power optimization settings during timing closure phase"
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
  - "Explanation: Power optimization configuration check is informational only for early design stages"
  - "Note: Some power settings may not be finalized during initial implementation and do not require immediate fixes"
  - "Rationale: Design team will configure final power optimization settings during timing closure phase"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - get_default_switching_activity -input_activity { } (expected: 0.15) - Parameter value not defined [WAIVED_AS_INFO]
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled [WAIVED_AS_INFO]
  - getDesignMode -powerEffort none (expected: high) - Design power effort not configured [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-09:
  description: "Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)"
  requirements:
    value: 7
    pattern_items:
      - "get_default_switching_activity -input_activity 0.15"
      - "get_default_switching_activity -clip_activity_to_domain_freq true"
      - "getNanoRouteMode -route_global_with_power_driven true"
      - "getNanoRouteMode -route_global_exp_power_driven_effort medium"
      - "getDesignMode -powerEffort high"
      - "getDesignMode -propagateActivity true"
      - "getOptMode -opt_leakage_to_dynamic_ratio 0.2"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\get_default_switching_activity
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getNanoRouteMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getDesignMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getOptMode
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches for the 7 critical power optimization parameter configurations in input files. This is a requirement check: PASS if all pattern_items are found with correct values (missing_items empty), FAIL if any pattern_items are missing or have incorrect values.

**Sample Output (PASS):**
```
Status: PASS
Reason: All required power optimization parameters matched and validated: switching activity configured, power-driven routing enabled, design power effort set to high, optimizer power settings correct
INFO01:
  - get_default_switching_activity -input_activity 0.15
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_with_power_driven true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -powerEffort high
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required power optimization parameters not satisfied: some parameters missing, have empty values, or incorrect configuration
ERROR01:
  - get_default_switching_activity -input_activity { } (expected: 0.15) - Parameter value not defined
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled
  - getDesignMode -powerEffort none (expected: high) - Design power effort not configured
INFO01:
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-09:
  description: "Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)"
  requirements:
    value: 7
    pattern_items:
      - "get_default_switching_activity -input_activity 0.15"
      - "get_default_switching_activity -clip_activity_to_domain_freq true"
      - "getNanoRouteMode -route_global_with_power_driven true"
      - "getNanoRouteMode -route_global_exp_power_driven_effort medium"
      - "getDesignMode -powerEffort high"
      - "getDesignMode -propagateActivity true"
      - "getOptMode -opt_leakage_to_dynamic_ratio 0.2"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\get_default_switching_activity
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getNanoRouteMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getDesignMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getOptMode
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power optimization parameter check is informational during early implementation phases"
      - "Note: Configuration mismatches are expected when using legacy design flows and do not require immediate fixes"
      - "Rationale: Final power optimization settings will be applied during timing closure and signoff stages"
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
  - "Explanation: Power optimization parameter check is informational during early implementation phases"
  - "Note: Configuration mismatches are expected when using legacy design flows and do not require immediate fixes"
  - "Rationale: Final power optimization settings will be applied during timing closure and signoff stages"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - get_default_switching_activity -input_activity { } (expected: 0.15) - Parameter value not defined [WAIVED_AS_INFO]
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled [WAIVED_AS_INFO]
  - getDesignMode -powerEffort none (expected: high) - Design power effort not configured [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-09:
  description: "Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)"
  requirements:
    value: 7
    pattern_items:
      - "get_default_switching_activity -input_activity 0.15"
      - "get_default_switching_activity -clip_activity_to_domain_freq true"
      - "getNanoRouteMode -route_global_with_power_driven true"
      - "getNanoRouteMode -route_global_exp_power_driven_effort medium"
      - "getDesignMode -powerEffort high"
      - "getDesignMode -propagateActivity true"
      - "getOptMode -opt_leakage_to_dynamic_ratio 0.2"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\get_default_switching_activity
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getNanoRouteMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getDesignMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getOptMode
  waivers:
    value: 2
    waive_items:
      - name: "getNanoRouteMode -route_global_with_power_driven true"
        reason: "Waived - power-driven routing disabled for this design due to runtime constraints, approved by design team"
      - name: "getDesignMode -powerEffort high"
        reason: "Waived - using medium power effort for initial implementation, will be increased during timing closure"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support. Same pattern search logic as Type 2 (searches for 7 critical power optimization parameters), plus waiver classification:
- Match found configuration issues against waive_items
- Unwaived issues → ERROR (need fix)
- Waived issues → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all configuration issues are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled [WAIVER]
  - getDesignMode -powerEffort medium (expected: high) - Design power effort not at maximum level [WAIVER]
INFO02 (Correctly configured):
  - get_default_switching_activity -input_activity 0.15
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
WARN01 (Unused Waivers):
  - (none - all waivers matched to actual configuration issues)
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Required power optimization parameters not satisfied: some parameters missing, have empty values, or incorrect configuration
ERROR01 (Unwaived violations):
  - get_default_switching_activity -input_activity { } (expected: 0.15) - Parameter value not defined
INFO01 (Waived):
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled [WAIVER]
  - getDesignMode -powerEffort medium (expected: high) - Design power effort not at maximum level [WAIVER]
INFO02 (Correctly configured):
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-09:
  description: "Confirm we take care of the dynamic power optimization in the whole innovs flow(Check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\get_default_switching_activity
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getNanoRouteMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getDesignMode
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-09\getOptMode
  waivers:
    value: 2
    waive_items:
      - name: "getNanoRouteMode -route_global_with_power_driven true"
        reason: "Waived - power-driven routing disabled for this design due to runtime constraints, approved by design team"
      - name: "getDesignMode -powerEffort high"
        reason: "Waived - using medium power effort for initial implementation, will be increased during timing closure"
```

**Check Behavior:**
Type 4 = Type 1 + waiver support. Same boolean check as Type 1 (validates all 7 critical power optimization parameters), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output (all violations waived):**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled [WAIVER]
  - getDesignMode -powerEffort medium (expected: high) - Design power effort not at maximum level [WAIVER]
INFO02 (Correctly configured):
  - get_default_switching_activity -input_activity 0.15
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Required power optimization settings not found or incorrectly configured in configuration files
ERROR01 (Unwaived violations):
  - get_default_switching_activity -input_activity { } (expected: 0.15) - Parameter value not defined
INFO01 (Waived):
  - getNanoRouteMode -route_global_with_power_driven false (expected: true) - Power-driven routing disabled [WAIVER]
  - getDesignMode -powerEffort medium (expected: high) - Design power effort not at maximum level [WAIVER]
INFO02 (Correctly configured):
  - get_default_switching_activity -clip_activity_to_domain_freq true
  - getNanoRouteMode -route_global_exp_power_driven_effort medium
  - getDesignMode -propagateActivity true
  - getOptMode -opt_leakage_to_dynamic_ratio 0.2
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-09 --force

# Run individual tests
python IMP-8-0-0-09.py
```

---

## Notes

**Critical Parameter Requirements:**
1. **get_default_switching_activity**: 
   - `input_activity` must be `0.15` (not empty `{ }`)
   - `clip_activity_to_domain_freq` must be `true`

2. **getNanoRouteMode**: 
   - `route_global_with_power_driven` must be `true`
   - `route_global_exp_power_driven_effort` must be `medium`

3. **getDesignMode**: 
   - `powerEffort` must be `high`
   - `propagateActivity` must be `true`

4. **getOptMode**: 
   - `opt_leakage_to_dynamic_ratio` must be `0.2` (not missing)
   - `opt_route_type_for_power` must be `true`
   - `opt_power_effort` must be `high`

**Edge Cases:**
- Empty parameter values `{ }` are treated as undefined and will cause FAIL
- Missing parameters (not present in file) will cause FAIL
- Missing input files will cause immediate error and FAIL
- All non-critical parameters are ignored (not checked or reported)
- Parameter values are case-sensitive (e.g., `true` vs `True`)

**Limitations:**
- Checker assumes parameter format follows Innovus command syntax
- Does not validate parameter interdependencies (e.g., whether power-driven routing settings are compatible)
- Does not check if power optimization actually improves design metrics
- Relies on exact string matching for parameter values