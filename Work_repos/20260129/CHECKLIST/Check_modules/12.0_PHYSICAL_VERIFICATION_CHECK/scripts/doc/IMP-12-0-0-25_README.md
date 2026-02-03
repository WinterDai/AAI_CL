# IMP-12-0-0-25: Confirm the BUMP DRC rule deck setting is correct.

## Overview

**Check ID:** IMP-12-0-0-25  
**Description:** Confirm the BUMP DRC rule deck setting is correct.  
**Category:** Physical Verification - DRC Rule Deck Configuration  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_BUMP_pvl.log`
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_BUMP_sourceme`

This checker validates BUMP DRC rule deck configuration by verifying switch states (enabled/disabled) and variable values in Pegasus log files or Calibre rule deck files. It ensures that all required switches and variables match the expected configuration for BUMP physical verification.

---

## Check Logic

### Input Parsing

The checker parses both Pegasus log format and Calibre rule deck format files to extract switch states and variable values.

**Key Patterns:**

```python
# Pattern 1: Switch definition (enabled)
pattern_enabled = r'^\s*#DEFINE\s+(\w+)'
# Example: "#DEFINE WITH_APRDL"

# Pattern 2: Switch definition (disabled - commented out)
# Note: The comment symbol "//" may have spaces between or after them
pattern_disabled = r'^\s*//\s*#DEFINE\s+(\w+)'
# Example: "//#DEFINE ChipWindowUsed"
# Example: "// #DEFINE ChipWindowUsed" (with space after //)
# Example: "  //  #DEFINE ChipWindowUsed" (with leading and internal spaces)

# Pattern 3: Variable definition (Pegasus format - lowercase "variable")
pattern_variable_pegasus = r'^\s*variable\s+(\w+)\s+(.+)'
# Example: "variable UBM_DN_4_Average_Density 0.25"
# Example: "variable USR_BUMP_PITCH 130 // User-defined BUMP pitch"
# Note: Comments (//) and trailing semicolons (;) are automatically removed from values

# Pattern 4: Variable definition (Calibre format - uppercase "VARIABLE")
pattern_variable_calibre = r'^\s*VARIABLE\s+(\w+)\s+(.+)'
# Example: "VARIABLE USR_BUMP_PITCH 130"
# Example: "VARIABLE UBM_DN_4_Average_Density 0.25;"
# Note: Comments (//) and trailing semicolons (;) are automatically removed from values
```

**Value Cleaning Rules:**
- Variable values are cleaned before comparison:
  1. Comments removed: `130 // comment` → `130`
  2. Trailing semicolons removed: `0.25;` → `0.25`
  3. Extra whitespace trimmed

### Detection Logic

1. **Parse Requirements**: Extract switch and variable requirements from YAML configuration
   - Requirements are dictionaries: `{'SWITCH_NAME': 'enabled/disabled'}` or `{'variable_name': numeric_value}`
   - Total count: 15 items (10 switches + 5 variables)

2. **Scan Input Files**: Read all input files line by line
   - Detect switch states using `#DEFINE` (enabled) or `//\s*#DEFINE` (disabled) patterns
   - Extract variable values using `variable` or `VARIABLE` keywords
   - Clean variable values by removing comments (//) and trailing characters (;)
   - Record line numbers and file paths for each finding

3. **Match Against Requirements**: Compare detected values with requirements
   - For switches: Check if state (enabled/disabled) matches requirement
   - For variables: Check if numeric value matches requirement (after cleaning)
   - Track matches and mismatches with file location information

4. **Generate Results**: Build output with detailed location information
   - Format: `"INFO/FAIL: detect switch/variable NAME status/value (match/mismatch requirement: expected_value) at line LINE_NUM of file FILE_PATH"`

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

**Rationale:** This checker validates configuration status (switch enabled/disabled, variable values). The pattern_items represent configuration items that must be checked for correct status/value. Only items in pattern_items are validated - other switches/variables in the file are ignored. This is a status validation check, not an existence check.

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
item_desc = "Confirm the BUMP DRC rule deck setting is correct."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "BUMP DRC rule deck configuration found and validated"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All BUMP DRC rule deck settings matched requirements (15/15)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "BUMP DRC rule deck configuration found with all required settings"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All switch states and variable values matched and validated against requirements"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "BUMP DRC rule deck configuration not found or incomplete"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "BUMP DRC rule deck settings mismatch detected (configuration errors found)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required BUMP DRC rule deck configuration not found in input files"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "One or more switch states or variable values not satisfied or mismatched with requirements"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "BUMP DRC rule deck configuration mismatches waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "BUMP DRC rule deck configuration mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused BUMP DRC rule deck waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding configuration mismatch found in rule deck files"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "INFO: detect switch/variable [NAME] [STATUS/VALUE] (match requirement: [EXPECTED]) at line [LINE_NUM] of file [FILE_PATH]"
  Example: "INFO: detect switch WITH_APRDL enabled (match requirement: enabled) at line 45 of file do_pvs_BUMP_pvl.log"
  Example: "INFO: detect variable USR_BUMP_PITCH 130 (match requirement: 130) at line 78 of file do_cmd_3star_BUMP_sourceme"

ERROR01 (Violation/Fail items):
  Format: "FAIL: detect switch/variable [NAME] [STATUS/VALUE] (mismatch requirement: [EXPECTED]) at line [LINE_NUM] of file [FILE_PATH]"
  Example: "FAIL: detect switch ChipWindowUsed enabled (mismatch requirement: disabled) at line 52 of file do_pvs_BUMP_pvl.log"
  Example: "FAIL: detect variable UBM_DN_4_Average_Density 0.30 (mismatch requirement: 0.25) at line 89 of file do_cmd_3star_BUMP_sourceme"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-25:
  description: "Confirm the BUMP DRC rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_BUMP_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_BUMP_sourceme"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of BUMP DRC rule deck configuration files. The checker scans input files to verify that all required switches and variables are present and correctly configured. PASS if all configuration items are found and valid, FAIL if any required configuration is missing or incorrect.

**Sample Output (PASS):**
```
Status: PASS
Reason: BUMP DRC rule deck configuration found with all required settings
INFO01:
  - INFO: detect switch WITH_APRDL enabled (match requirement: enabled) at line 45 of file do_pvs_BUMP_pvl.log
  - INFO: detect switch AP_28K_THICKNESS enabled (match requirement: enabled) at line 46 of file do_pvs_BUMP_pvl.log
  - INFO: detect variable USR_BUMP_PITCH 130 (match requirement: 130) at line 78 of file do_cmd_3star_BUMP_sourceme
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required BUMP DRC rule deck configuration not found in input files
ERROR01:
  - FAIL: detect switch ChipWindowUsed enabled (mismatch requirement: disabled) at line 52 of file do_pvs_BUMP_pvl.log
  - FAIL: detect variable UBM_DN_4_Average_Density 0.30 (mismatch requirement: 0.25) at line 89 of file do_cmd_3star_BUMP_sourceme
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-25:
  description: "Confirm the BUMP DRC rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_BUMP_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_BUMP_sourceme"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: BUMP DRC rule deck configuration check is informational only for early design stages"
      - "Note: Configuration mismatches are expected during initial setup and do not block design progress"
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
  - "Explanation: BUMP DRC rule deck configuration check is informational only for early design stages"
  - "Note: Configuration mismatches are expected during initial setup and do not block design progress"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - FAIL: detect switch ChipWindowUsed enabled (mismatch requirement: disabled) at line 52 of file do_pvs_BUMP_pvl.log [WAIVED_AS_INFO]
  - FAIL: detect variable UBM_DN_4_Average_Density 0.30 (mismatch requirement: 0.25) at line 89 of file do_cmd_3star_BUMP_sourceme [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-25:
  description: "Confirm the BUMP DRC rule deck setting is correct."
  requirements:
    value: 15
    pattern_items:
      - WITH_APRDL: "enabled"
      - AP_28K_THICKNESS: "enabled"
      - ChipWindowUsed: "disabled"
      - BUMP_PITCH_112.2um_132.7um: "disabled"
      - BUMP_PITCH_132.7um_153.1um: "enabled"
      - BUMP_PITCH_153.1um_183.7um: "disabled"
      - DFM: "enabled"
      - FULL_CHIP: "disabled"
      - TOP_METAL_Checking: "enabled"
      - USR_PITCH_WIDTH: "disabled"
      - UBM_DN_4_Average_Density: 0.25
      - USR_BUMP_PITCH: 130
      - USR_UBM_WIDTH: 70
      - USR_PM_WIDTH: 30
      - USR_CB2_WIDTH: 40
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_BUMP_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_BUMP_sourceme"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items are DICTIONARIES with switch/variable names as keys and expected states/values as values
- For switches: Use "enabled" or "disabled" as string values
- For variables: Use numeric values (int or float)
- Each pattern_item represents one configuration requirement to validate

**Check Behavior:**
Type 2 searches for switches and variables in input files and validates their states/values against pattern_items requirements. This is a requirement check: PASS if all pattern_items are found with correct status/values (missing_items empty), FAIL if any pattern_item has wrong status/value or is not found.

**Sample Output (PASS):**
```
Status: PASS
Reason: All switch states and variable values matched and validated against requirements
INFO01:
  - INFO: detect switch WITH_APRDL enabled (match requirement: enabled) at line 45 of file do_pvs_BUMP_pvl.log
  - INFO: detect switch AP_28K_THICKNESS enabled (match requirement: enabled) at line 46 of file do_pvs_BUMP_pvl.log
  - INFO: detect switch ChipWindowUsed disabled (match requirement: disabled) at line 47 of file do_pvs_BUMP_pvl.log
  - INFO: detect switch BUMP_PITCH_132.7um_153.1um enabled (match requirement: enabled) at line 50 of file do_pvs_BUMP_pvl.log
  - INFO: detect variable UBM_DN_4_Average_Density 0.25 (match requirement: 0.25) at line 78 of file do_cmd_3star_BUMP_sourceme
  - INFO: detect variable USR_BUMP_PITCH 130 (match requirement: 130) at line 79 of file do_cmd_3star_BUMP_sourceme
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-25:
  description: "Confirm the BUMP DRC rule deck setting is correct."
  requirements:
    value: 15
    pattern_items:
      - WITH_APRDL: "enabled"
      - AP_28K_THICKNESS: "enabled"
      - ChipWindowUsed: "disabled"
      - BUMP_PITCH_112.2um_132.7um: "disabled"
      - BUMP_PITCH_132.7um_153.1um: "enabled"
      - BUMP_PITCH_153.1um_183.7um: "disabled"
      - DFM: "enabled"
      - FULL_CHIP: "disabled"
      - TOP_METAL_Checking: "enabled"
      - USR_PITCH_WIDTH: "disabled"
      - UBM_DN_4_Average_Density: 0.25
      - USR_BUMP_PITCH: 130
      - USR_UBM_WIDTH: 70
      - USR_PM_WIDTH: 30
      - USR_CB2_WIDTH: 40
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_BUMP_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_BUMP_sourceme"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: BUMP DRC rule deck configuration validation is informational during initial design phase"
      - "Note: Configuration mismatches are expected when using alternative rule deck versions and do not require immediate fixes"
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
  - "Explanation: BUMP DRC rule deck configuration validation is informational during initial design phase"
  - "Note: Configuration mismatches are expected when using alternative rule deck versions and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - FAIL: detect switch ChipWindowUsed enabled (mismatch requirement: disabled) at line 52 of file do_pvs_BUMP_pvl.log [WAIVED_AS_INFO]
  - FAIL: detect variable UBM_DN_4_Average_Density 0.30 (mismatch requirement: 0.25) at line 89 of file do_cmd_3star_BUMP_sourceme [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-25:
  description: "Confirm the BUMP DRC rule deck setting is correct."
  requirements:
    value: 15
    pattern_items:
      - WITH_APRDL: "enabled"
      - AP_28K_THICKNESS: "enabled"
      - ChipWindowUsed: "disabled"
      - BUMP_PITCH_112.2um_132.7um: "disabled"
      - BUMP_PITCH_132.7um_153.1um: "enabled"
      - BUMP_PITCH_153.1um_183.7um: "disabled"
      - DFM: "enabled"
      - FULL_CHIP: "disabled"
      - TOP_METAL_Checking: "enabled"
      - USR_PITCH_WIDTH: "disabled"
      - UBM_DN_4_Average_Density: 0.25
      - USR_BUMP_PITCH: 130
      - USR_UBM_WIDTH: 70
      - USR_PM_WIDTH: 30
      - USR_CB2_WIDTH: 40
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_BUMP_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_BUMP_sourceme"
  waivers:
    value: 2
    waive_items:
      - name: "ChipWindowUsed"
        reason: "Waived - ChipWindowUsed switch enabled for specific test configuration per design team approval"
      - name: "UBM_DN_4_Average_Density"
        reason: "Waived - UBM density value 0.30 approved for this design variant, deviates from standard 0.25"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Pattern items are dictionaries with configuration names as keys
- waive_items.name should use the KEY from pattern_items (switch/variable name only)
- Example: If pattern_items has `ChipWindowUsed: "disabled"`, then waive_items.name = "ChipWindowUsed"
- DO NOT include the expected value in waive_items.name (e.g., NOT "ChipWindowUsed: disabled")

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match configuration mismatches against waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all configuration mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - FAIL: detect switch ChipWindowUsed enabled (mismatch requirement: disabled) at line 52 of file do_pvs_BUMP_pvl.log [WAIVER]
  - FAIL: detect variable UBM_DN_4_Average_Density 0.30 (mismatch requirement: 0.25) at line 89 of file do_cmd_3star_BUMP_sourceme [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-25:
  description: "Confirm the BUMP DRC rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_BUMP_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_BUMP_sourceme"
  waivers:
    value: 2
    waive_items:
      - name: "ChipWindowUsed"
        reason: "Waived - ChipWindowUsed switch enabled for specific test configuration per design team approval"
      - name: "UBM_DN_4_Average_Density"
        reason: "Waived - UBM density value 0.30 approved for this design variant, deviates from standard 0.25"
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
  - FAIL: detect switch ChipWindowUsed enabled (mismatch requirement: disabled) at line 52 of file do_pvs_BUMP_pvl.log [WAIVER]
  - FAIL: detect variable UBM_DN_4_Average_Density 0.30 (mismatch requirement: 0.25) at line 89 of file do_cmd_3star_BUMP_sourceme [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-25 --force

# Run individual tests
python IMP-12-0-0-25.py
```

---

## Notes

**Important Implementation Details:**

1. **File Format Flexibility**: The checker supports both Pegasus log format and Calibre rule deck format. The file format does not matter - only the switch status and variable values are validated.

2. **Switch Detection Logic**:
   - Enabled switch: `#DEFINE SWITCH_NAME` (not commented)
   - Disabled switch: `//\s*#DEFINE SWITCH_NAME` (commented out with optional spaces)
   - The comment symbol "//" may have spaces between or after them (e.g., "//#DEFINE", "// #DEFINE", "  //  #DEFINE")

3. **Variable Detection Logic**:
   - Pegasus format: `variable var_name value1 value2 ...` (lowercase "variable")
   - Calibre format: `VARIABLE var_name value1 value2 ...` (uppercase "VARIABLE")

4. **Dictionary Pattern Items**: The requirements.pattern_items are DICTIONARIES, not strings. Each item must be parsed as `{'KEY': 'value'}` before string formatting. The checker must extract the key-value pairs correctly.

5. **Output Format Requirement**: All output messages must follow the specified format with file location information:
   - `"INFO: detect switch/variable NAME status/value (match requirement: expected) at line LINE_NUM of file FILE_PATH"`
   - `"FAIL: detect switch/variable NAME status/value (mismatch requirement: expected) at line LINE_NUM of file FILE_PATH"`

6. **Multiple Input Files**: The checker may receive one or more input files with random names. All files must be scanned and all configuration items across all files must be validated.

7. **Limitations**: 
   - The checker assumes switch and variable definitions follow the standard format
   - Multi-line definitions are not supported
   - Variable values are compared as strings or numbers depending on the requirement type