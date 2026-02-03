# IMP-12-0-0-07: Confirm the ANT rule deck setting is correct.

## Overview

**Check ID:** IMP-12-0-0-07  
**Description:** Confirm the ANT rule deck setting is correct.  
**Category:** Physical Verification - Antenna Rule Deck Configuration Validation  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_ANT_pvl.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_ANT_sourceme

This checker validates that the ANT (Antenna) rule deck configuration is correct by verifying that specific debug and optional switches are disabled. It parses both the PVS ANT log file (actual tool configuration) and the Calibre sourceme script (intended configuration), ensuring that debug modes and non-standard features are turned off for production runs. The checker follows a priority-based parsing strategy where the PVL log (actual configuration) takes precedence over the sourceme file (intended configuration).

---

## Check Logic

### Input Parsing

**File 1: do_pvs_ANT_pvl.log (Pegasus PVS ANT Log - HIGHEST PRIORITY)**

This file contains the actual configuration used by the Pegasus PVS tool during antenna checking. It shows rule deck parsing, variable definitions, and configuration settings.

**Key Patterns:**

```python
# Pattern 1: Variable definitions (debug switches)
# Extracts variable assignments that control debug modes and optional features
pattern_variable = r'^variable\s+(\w+)\s*=\s*"?([^";]+)"?;?'
# Example: "variable ACC_DEBUG = "disabled";"
# Extraction: Group 1 = variable name (e.g., "ACC_DEBUG"), Group 2 = value (e.g., "disabled")

# Pattern 2: Configuration warnings
# Captures warnings about duplicate or conflicting settings
pattern_warning = r'^\[WARN\]:\s*(.+?)\s+at line\s+(\d+)\s+in file\s+(.+?)\s+is\s+(.+)'
# Example: "[WARN]: LAYOUT_FORMAT at line 102 in file /projects/.../ANT.encrypt is ignored due to one specified before"
# Extraction: Group 1 = setting name, Group 2 = line number, Group 3 = file path, Group 4 = warning reason

# Pattern 3: Rule deck include path
# Extracts the ANT rule deck file path for verification
pattern_include = r'^include\s+"([^"]+)"'
# Example: 'include "/projects/TC73_DDR5_12800_N5P/libs/ruledeck/PEGASUS/ANT/PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"'
# Extraction: Group 1 = full path to ANT rule deck file
```

**File 2: do_cmd_3star_ANT_sourceme (Calibre DRC Sourceme - LOWER PRIORITY)**

This file contains the intended configuration with SVRF commands and preprocessor directives. It is parsed first, but values are overwritten by the PVL log.

**Key Patterns:**

```python
# Pattern 4: #DEFINE switches (metal schemes and debug modes)
# Extracts preprocessor defines that enable/disable features
pattern_define = r'^\s*(//)?#DEFINE\s+(\w+)\s*(?://(.*))?'
# Example: "//#DEFINE WITH_4MZ      // Turn on for run metal scheme with 4Mz"
# Extraction: Group 1 = "//" if commented (disabled), Group 2 = define name, Group 3 = comment text
# Logic: If Group 1 is None (no "//"), the define is ENABLED; otherwise DISABLED

# Pattern 5: LAYOUT SYSTEM declaration
# Extracts layout database format
pattern_layout_system = r'^LAYOUT\s+SYSTEM\s+(\w+)'
# Example: "LAYOUT SYSTEM OASIS"
# Extraction: Group 1 = system type (OASIS/GDSII)

# Pattern 6: LAYOUT PRIMARY cell name
# Extracts top-level design cell name
pattern_layout_primary = r'^LAYOUT\s+PRIMARY\s+(\S+)'
# Example: "LAYOUT PRIMARY CDN_104V_cdn_hs_phy_data_slice_NS"
# Extraction: Group 1 = primary cell name
```

### Detection Logic

**Step 1: Initialize Registry**
- Create empty registry dictionary to store all configuration settings
- Registry format: `{setting_name: {'value': value, 'source': 'pvl'|'sourceme', 'enabled': True|False}}`

**Step 2: Parse Sourceme File First (Lower Priority)**
- Read do_cmd_3star_ANT_sourceme line by line
- For each #DEFINE pattern match:
  - Extract define name (e.g., "ACC_DEBUG", "WITH_4MZ")
  - Determine enabled state: `enabled = (comment_prefix is None)` (case-insensitive)
  - Store in registry: `registry[name] = {'value': 'enabled' if enabled else 'disabled', 'source': 'sourceme', 'enabled': enabled}`
- For LAYOUT SYSTEM/PRIMARY: Store as metadata (not checked against pattern_items)

**Step 3: Parse PVL Log File (Higher Priority - ALWAYS OVERWRITES)**
- Read do_pvs_ANT_pvl.log line by line
- For each variable definition match:
  - Extract variable name and value
  - **CRITICAL**: ALWAYS overwrite registry entry (remove "if not in registry" check)
  - Store: `registry[name] = {'value': value.lower(), 'source': 'pvl', 'enabled': (value.lower() != 'disabled')}`
  - This represents actual tool behavior and takes precedence
- For warnings: Log but don't affect registry (informational only)
- For include statements: Store rule deck path as metadata

**Step 4: Validate Against Pattern Items**
- Pattern items are YAML dictionaries: `[{'ACC_DEBUG': 'disabled'}, {'DEBUG_VIA': 'disabled'}, ...]`
- **CRITICAL**: Parse each pattern_item as dictionary first, then extract key-value
- For each pattern_item dictionary:
  - Extract key (setting name) and expected value (e.g., 'disabled')
  - Look up setting in registry
  - Compare actual value against expected value (case-insensitive)
  - If match: Add to found_items with reason "Setting correctly configured"
  - If mismatch or missing: Add to missing_items with reason "Setting incorrect or not found"

**Step 5: Classification**
- found_items: Settings that match expected configuration (disabled when should be disabled)
- missing_items: Settings that don't match or are missing from configuration
- PASS condition: `len(missing_items) == 0` (all required settings correctly configured)

**Edge Cases:**
1. **Duplicate settings**: PVL log warnings indicate conflicts - use the value that was actually applied (first occurrence in PVL log)
2. **Missing settings**: If a pattern_item is not found in either file, treat as missing_item
3. **Case sensitivity**: Use case-insensitive comparison for enabled/disabled states
4. **Commented vs uncommented defines**: In sourceme, "//#DEFINE" = disabled, "#DEFINE" = enabled
5. **Parse order**: Sourceme first (low priority), then PVL log overwrites (high priority)

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

**Rationale:** This checker validates the STATUS of specific ANT rule deck settings (whether they are enabled or disabled). The pattern_items define which settings to check and their expected states. We only report on the settings listed in pattern_items, not all settings in the files. A setting is "found" (correct) if its actual state matches the expected state, and "missing" (incorrect) if the state doesn't match or the setting is absent. This is a status validation check, not an existence check.

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
item_desc = "Confirm the ANT rule deck setting is correct."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "ANT rule deck configuration validated successfully"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "ANT rule deck settings matched expected configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All required ANT rule deck settings found and correctly configured"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Setting correctly configured and validated against expected state"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Required ANT rule deck settings not found or incorrectly configured"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "ANT rule deck settings do not match expected configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required setting not found in configuration files or has incorrect value"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Setting state does not match expected value or setting is missing from configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "ANT rule deck setting mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "ANT rule deck setting mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused ANT rule deck waiver entry"
unused_waiver_reason = "Waiver entry not matched - no corresponding configuration mismatch found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [setting_name]: [found_reason]"
  Example: "- ACC_DEBUG: Setting correctly configured and validated against expected state (disabled)"

ERROR01 (Violation/Fail items):
  Format: "- [setting_name]: [missing_reason]"
  Example: "- DEBUG_VIA: Setting state does not match expected value or setting is missing from configuration (expected: disabled, actual: enabled)"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-07:
  description: "Confirm the ANT rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_ANT_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_ANT_sourceme
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of ANT rule deck configuration. The checker parses both PVL log and sourceme files to build a complete configuration registry, then validates that critical settings exist and have correct values. PASS if all validation checks succeed, FAIL if any configuration issues are detected.

**Sample Output (PASS):**
```
Status: PASS
Reason: All required ANT rule deck settings found and correctly configured

Log format (CheckList.rpt):
INFO01:
  - ANT rule deck configuration validated

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: ANT rule deck configuration validated. In line 1, do_pvs_ANT_pvl.log: All required ANT rule deck settings found and correctly configured
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required ANT rule deck settings not found or incorrectly configured

Log format (CheckList.rpt):
ERROR01:
  - ACC_DEBUG setting incorrect
  - DEBUG_VIA setting missing

Report format (item_id.rpt):
Fail Occurrence: 2
1: Fail: ACC_DEBUG setting incorrect. In line 45, do_pvs_ANT_pvl.log: Required setting not found in configuration files or has incorrect value (expected: disabled, actual: enabled)
2: Fail: DEBUG_VIA setting missing. In line 0, do_cmd_3star_ANT_sourceme: Required setting not found in configuration files or has incorrect value
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-07:
  description: "Confirm the ANT rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_ANT_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_ANT_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only for early development phase"
      - "Note: Debug settings may be enabled during bring-up and do not require immediate fixes"
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
  - "Explanation: This check is informational only for early development phase"
  - "Note: Debug settings may be enabled during bring-up and do not require immediate fixes"
INFO02:
  - ACC_DEBUG setting incorrect
  - DEBUG_VIA setting missing

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: This check is informational only for early development phase. [WAIVED_INFO]
2: Info: Note: Debug settings may be enabled during bring-up and do not require immediate fixes. [WAIVED_INFO]
3: Info: ACC_DEBUG setting incorrect. In line 45, do_pvs_ANT_pvl.log: Required setting not found in configuration files or has incorrect value (expected: disabled, actual: enabled) [WAIVED_AS_INFO]
4: Info: DEBUG_VIA setting missing. In line 0, do_cmd_3star_ANT_sourceme: Required setting not found in configuration files or has incorrect value [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-07:
  description: "Confirm the ANT rule deck setting is correct."
  requirements:
    value: 7
    pattern_items:
      - ACC_DEBUG: "disabled"
      - DEBUG_VIA: "disabled"
      - First_priority: "disabled"
      - Manufacturing_concern: "disabled"
      - DRC_TOLERANCE_FLOATING_POINT: "disabled"
      - DEBUG_MX: "disabled"
      - FHDMIM: "disabled"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_ANT_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_ANT_sourceme
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items are YAML DICTIONARIES with key-value pairs: `{setting_name: expected_value}`
- Each dictionary defines one setting to validate and its expected state
- Setting names: Configuration variable names (e.g., "ACC_DEBUG", "DEBUG_VIA")
- Expected values: Target states (e.g., "disabled", "enabled") - case-insensitive comparison
- Parser MUST extract dictionary key first, then value, before string formatting

**Check Behavior:**
Type 2 validates that specific ANT rule deck settings match their expected states. The checker parses configuration files to extract actual setting values, then compares against pattern_items dictionaries. PASS if all settings match expected values (all found_items, no missing_items). FAIL if any setting has wrong value or is missing.

**Sample Output (PASS):**
```
Status: PASS
Reason: ANT rule deck settings matched expected configuration

Log format (CheckList.rpt):
INFO01:
  - ACC_DEBUG
  - DEBUG_VIA
  - First_priority
  - Manufacturing_concern
  - DRC_TOLERANCE_FLOATING_POINT
  - DEBUG_MX
  - FHDMIM

Report format (item_id.rpt):
Info Occurrence: 7
1: Info: ACC_DEBUG. In line 45, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
2: Info: DEBUG_VIA. In line 52, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
3: Info: First_priority. In line 58, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
4: Info: Manufacturing_concern. In line 63, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
5: Info: DRC_TOLERANCE_FLOATING_POINT. In line 70, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
6: Info: DEBUG_MX. In line 75, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
7: Info: FHDMIM. In line 82, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: ANT rule deck settings do not match expected configuration

Log format (CheckList.rpt):
INFO01:
  - DEBUG_VIA
  - First_priority
  - Manufacturing_concern
  - DRC_TOLERANCE_FLOATING_POINT
  - DEBUG_MX
ERROR01:
  - ACC_DEBUG
  - FHDMIM

Report format (item_id.rpt):
Info Occurrence: 5
1: Info: DEBUG_VIA. In line 52, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
2: Info: First_priority. In line 58, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
3: Info: Manufacturing_concern. In line 63, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
4: Info: DRC_TOLERANCE_FLOATING_POINT. In line 70, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
5: Info: DEBUG_MX. In line 75, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
Fail Occurrence: 2
1: Fail: ACC_DEBUG. In line 45, do_pvs_ANT_pvl.log: Setting state does not match expected value or setting is missing from configuration (expected: disabled, actual: enabled)
2: Fail: FHDMIM. In line 0, do_cmd_3star_ANT_sourceme: Setting state does not match expected value or setting is missing from configuration (expected: disabled, not found in files)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-07:
  description: "Confirm the ANT rule deck setting is correct."
  requirements:
    value: 7
    pattern_items:
      - ACC_DEBUG: "disabled"
      - DEBUG_VIA: "disabled"
      - First_priority: "disabled"
      - Manufacturing_concern: "disabled"
      - DRC_TOLERANCE_FLOATING_POINT: "disabled"
      - DEBUG_MX: "disabled"
      - FHDMIM: "disabled"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_ANT_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_ANT_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Debug settings are allowed during development phase"
      - "Note: Configuration mismatches will be resolved before production release"
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
  - "Explanation: Debug settings are allowed during development phase"
  - "Note: Configuration mismatches will be resolved before production release"
INFO02:
  - DEBUG_VIA
  - First_priority
  - Manufacturing_concern
  - DRC_TOLERANCE_FLOATING_POINT
  - DEBUG_MX
  - ACC_DEBUG
  - FHDMIM

Report format (item_id.rpt):
Info Occurrence: 9
1: Info: Explanation: Debug settings are allowed during development phase. [WAIVED_INFO]
2: Info: Note: Configuration mismatches will be resolved before production release. [WAIVED_INFO]
3: Info: DEBUG_VIA. In line 52, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
4: Info: First_priority. In line 58, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
5: Info: Manufacturing_concern. In line 63, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
6: Info: DRC_TOLERANCE_FLOATING_POINT. In line 70, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
7: Info: DEBUG_MX. In line 75, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
8: Info: ACC_DEBUG. In line 45, do_pvs_ANT_pvl.log: Setting state does not match expected value or setting is missing from configuration (expected: disabled, actual: enabled) [WAIVED_AS_INFO]
9: Info: FHDMIM. In line 0, do_cmd_3star_ANT_sourceme: Setting state does not match expected value or setting is missing from configuration (expected: disabled, not found in files) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-07:
  description: "Confirm the ANT rule deck setting is correct."
  requirements:
    value: 7
    pattern_items:
      - ACC_DEBUG: "disabled"
      - DEBUG_VIA: "disabled"
      - First_priority: "disabled"
      - Manufacturing_concern: "disabled"
      - DRC_TOLERANCE_FLOATING_POINT: "disabled"
      - DEBUG_MX: "disabled"
      - FHDMIM: "disabled"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_ANT_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_ANT_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "ACC_DEBUG"
        reason: "Waived - ACC_DEBUG enabled for accelerated debug mode during bring-up phase"
      - name: "FHDMIM"
        reason: "Waived - FHDMIM feature required for high-density metal-insulator-metal capacitor analysis"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2 (validate settings against expected states), plus waiver classification:
- Match found_items (mismatched settings) against waive_items by setting name
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved exceptions)
- Unused waivers → WARN with [WAIVER] tag (waiver defined but no mismatch found)
PASS if all mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - ACC_DEBUG
  - FHDMIM
  - DEBUG_VIA
  - First_priority
  - Manufacturing_concern
  - DRC_TOLERANCE_FLOATING_POINT
  - DEBUG_MX

Report format (item_id.rpt):
Info Occurrence: 7
1: Info: ACC_DEBUG. In line 45, do_pvs_ANT_pvl.log: ANT rule deck setting mismatch waived per design team approval: Waived - ACC_DEBUG enabled for accelerated debug mode during bring-up phase [WAIVER]
2: Info: FHDMIM. In line 0, do_cmd_3star_ANT_sourceme: ANT rule deck setting mismatch waived per design team approval: Waived - FHDMIM feature required for high-density metal-insulator-metal capacitor analysis [WAIVER]
3: Info: DEBUG_VIA. In line 52, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
4: Info: First_priority. In line 58, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
5: Info: Manufacturing_concern. In line 63, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
6: Info: DRC_TOLERANCE_FLOATING_POINT. In line 70, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
7: Info: DEBUG_MX. In line 75, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
```

**Sample Output (with unused waiver):**
```
Status: FAIL
Reason: Unwaived violations found

Log format (CheckList.rpt):
INFO01:
  - FHDMIM
  - DEBUG_VIA
  - First_priority
  - Manufacturing_concern
  - DRC_TOLERANCE_FLOATING_POINT
  - DEBUG_MX
ERROR01:
  - ACC_DEBUG
WARN01:
  - DEBUG_MX

Report format (item_id.rpt):
Info Occurrence: 6
1: Info: FHDMIM. In line 0, do_cmd_3star_ANT_sourceme: ANT rule deck setting mismatch waived per design team approval: Waived - FHDMIM feature required for high-density metal-insulator-metal capacitor analysis [WAIVER]
2: Info: DEBUG_VIA. In line 52, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
3: Info: First_priority. In line 58, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
4: Info: Manufacturing_concern. In line 63, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
5: Info: DRC_TOLERANCE_FLOATING_POINT. In line 70, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
6: Info: DEBUG_MX. In line 75, do_pvs_ANT_pvl.log: Setting correctly configured and validated against expected state (disabled)
Fail Occurrence: 1
1: Fail: ACC_DEBUG. In line 45, do_pvs_ANT_pvl.log: Setting state does not match expected value or setting is missing from configuration (expected: disabled, actual: enabled)
Warn Occurrence: 1
1: Warn: DEBUG_MX. In line 0, waiver_config: Waiver entry not matched - no corresponding configuration mismatch found: Waived - DEBUG_MX enabled for metal layer debugging [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-07:
  description: "Confirm the ANT rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_ANT_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_ANT_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "ACC_DEBUG"
        reason: "Waived - ACC_DEBUG enabled for accelerated debug mode during bring-up phase"
      - name: "FHDMIM"
        reason: "Waived - FHDMIM feature required for high-density metal-insulator-metal capacitor analysis"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (setting names: "ACC_DEBUG", "FHDMIM")
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (validate ANT rule deck configuration without pattern_items), plus waiver classification:
- Match violations (incorrect settings) against waive_items by setting name
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
  - ACC_DEBUG
  - FHDMIM
WARN01:
  - (none - all waivers used)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: ACC_DEBUG. In line 45, do_pvs_ANT_pvl.log: ANT rule deck setting mismatch waived per design team approval: Waived - ACC_DEBUG enabled for accelerated debug mode during bring-up phase [WAIVER]
2: Info: FHDMIM. In line 0, do_cmd_3star_ANT_sourceme: ANT rule deck setting mismatch waived per design team approval: Waived - FHDMIM feature required for high-density metal-insulator-metal capacitor analysis [WAIVER]
```

**Sample Output (with unwaived violation):**
```
Status: FAIL
Reason: Unwaived violations found

Log format (CheckList.rpt):
INFO01:
  - FHDMIM
ERROR01:
  - ACC_DEBUG
  - DEBUG_VIA
WARN01:
  - (none)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: FHDMIM. In line 0, do_cmd_3star_ANT_sourceme: ANT rule deck setting mismatch waived per design team approval: Waived - FHDMIM feature required for high-density metal-insulator-metal capacitor analysis [WAIVER]
Fail Occurrence: 2
1: Fail: ACC_DEBUG. In line 45, do_pvs_ANT_pvl.log: Required setting not found in configuration files or has incorrect value (expected: disabled, actual: enabled)
2: Fail: DEBUG_VIA. In line 52, do_pvs_ANT_pvl.log: Required setting not found in configuration files or has incorrect value (expected: disabled, actual: enabled)
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-07 --force

# Run individual tests
python IMP-12-0-0-07.py
```

---

## Notes

**Implementation Notes:**
1. **Parse Order Critical**: Always parse sourceme file first (lower priority), then PVL log file (higher priority). PVL log values ALWAYS overwrite sourceme values in the registry.

2. **Dictionary Pattern Items**: The pattern_items in requirements are YAML dictionaries `{'setting_name': 'expected_value'}`, not simple strings. Parser must extract the dictionary key-value pair before processing.

3. **Case-Insensitive Comparison**: All state comparisons (enabled/disabled) should be case-insensitive to handle variations in file formats.

4. **Commented Defines**: In sourceme files, "//#DEFINE" indicates a disabled setting, while "#DEFINE" (no comment prefix) indicates enabled.

5. **Registry Overwrite**: The PVL log parser must ALWAYS overwrite registry entries, even if they already exist from sourceme parsing. This represents actual tool behavior.

**Known Limitations:**
- Checker assumes PVL log format is consistent with Pegasus PVS output
- Sourceme file must follow Calibre SVRF syntax conventions
- If both files are missing or corrupted, checker will report all settings as missing

**Edge Cases:**
- **Encrypted rule decks**: File paths may end with ".encrypt" extension - this is valid
- **Compressed GDS files**: Layout paths may end with ".gz" extension - this is valid
- **Duplicate settings**: PVL log warnings indicate conflicts - use first occurrence value
- **Missing settings**: If a pattern_item setting is not found in either file, treat as violation