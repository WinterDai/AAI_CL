# IMP-12-0-0-09: Confirm the LVS rule deck setting is correct.

## Overview

**Check ID:** IMP-12-0-0-09  
**Description:** Confirm the LVS rule deck setting is correct.  
**Category:** Physical Verification - LVS Configuration Validation  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme

This checker validates LVS (Layout vs Schematic) rule deck configuration settings by parsing both the Pegasus LVS log file (.pvl) and the Calibre LVS command file (sourceme). It verifies that critical LVS control flags (#define directives) are set to their expected enabled/disabled states according to design requirements. The checker ensures proper LVS execution by validating settings like WELL_TO_PG_CHECK, FLOATING_WELL_CHECK, extraction controls, and power/ground net definitions. It follows a two-stage parsing strategy where sourceme provides intended configuration and the PVL log represents actual tool behavior, with PVL taking precedence.

---

## Check Logic

### Input Parsing

**File 1: do_pvs_LVS_pvl.log (Pegasus LVS Log - Higher Priority)**
This file contains the actual LVS rule deck settings as executed by the Pegasus tool. It includes #DEFINE statements, SCHEMATIC/LAYOUT configuration, and include file paths.

**File 2: do_cmd_3star_LVS_sourceme (Calibre LVS Command File - Lower Priority)**
This file contains the intended LVS configuration with #define directives, VIRTUAL_CONNECT settings, and LAYOUT/SOURCE paths.

**Parsing Strategy:**
1. Parse sourceme file first (lower priority - intended configuration)
2. Parse PVL log file second (higher priority - actual configuration)
3. PVL log values ALWAYS overwrite sourceme values (represents actual tool behavior)
4. Use case-insensitive comparison for enabled/disabled states

**Key Patterns:**

```python
# Pattern 1: #DEFINE statements in PVL log (actual configuration)
pvl_define_pattern = r'^\s*#DEFINE\s+(\w+)'
# Example: "#DEFINE WELL_TO_PG_CHECK"
# Extracts: Group 1 = "WELL_TO_PG_CHECK" (enabled flag)

# Pattern 2: #define statements in sourceme (intended configuration)
sourceme_define_pattern = r'^\s*#define\s+(\w+)\s*(?://.*)?$'
# Example: "#define WELL_TO_PG_CHECK   //uncomment this line when..."
# Extracts: Group 1 = "WELL_TO_PG_CHECK" (enabled flag)

# Pattern 3: Commented out #define in sourceme (disabled flags)
sourceme_commented_pattern = r'^\s*//\s*#define\s+(\w+)\s*(?://.*)?$'
# Example: "//#define RC_DFM_RULE   //uncomment this line when..."
# Extracts: Group 1 = "RC_DFM_RULE" (disabled flag)

# Pattern 4: POWER_NAME list extraction (sourceme)
power_name_pattern = r'^\s*POWER\s+NAME\s+(.+?)(?:\s*//.*)?$'
# Example: "POWER NAME vdd vddg vddm"
# Extracts: Group 1 = "vdd vddg vddm" (space-separated power nets)

# Pattern 5: GROUND_NAME list extraction (sourceme)
ground_name_pattern = r'^\s*GROUND\s+NAME\s+(.+?)(?:\s*//.*)?$'
# Example: "GROUND NAME vss vssg gnd"
# Extracts: Group 1 = "vss vssg gnd" (space-separated ground nets)
```

### Detection Logic

**Step 1: Parse pattern_items from YAML configuration**
- Each pattern_item is a DICTIONARY: `{'KEY': 'value'}` (NOT a string!)
- Extract key name and expected state (enabled/disabled)
- Build expected configuration registry

**Step 2: Parse sourceme file (lower priority)**
```python
for line in sourceme_file:
    # Check for enabled #define
    if match := re.match(r'^\s*#define\s+(\w+)', line):
        flag_name = match.group(1)
        registry[flag_name] = 'enabled'
    
    # Check for disabled (commented) #define
    elif match := re.match(r'^\s*//\s*#define\s+(\w+)', line):
        flag_name = match.group(1)
        registry[flag_name] = 'disabled'
    
    # Parse POWER_NAME list
    elif match := re.match(r'^\s*POWER\s+NAME\s+(.+)', line):
        power_nets = match.group(1).split()
        registry['POWER_NAME'] = power_nets
    
    # Parse GROUND_NAME list
    elif match := re.match(r'^\s*GROUND\s+NAME\s+(.+)', line):
        ground_nets = match.group(1).split()
        registry['GROUND_NAME'] = ground_nets
```

**Step 3: Parse PVL log file (higher priority - ALWAYS overwrites)**
```python
for line in pvl_log_file:
    # PVL uses #DEFINE (uppercase)
    if match := re.match(r'^\s*#DEFINE\s+(\w+)', line):
        flag_name = match.group(1)
        # CRITICAL: ALWAYS overwrite registry (no "if not in registry" check!)
        registry[flag_name] = 'enabled'
```

**Step 4: Compare actual vs expected configuration**
```python
found_items = []      # Settings matching expected state
missing_items = []    # Settings NOT matching expected state

for pattern_dict in pattern_items:
    # Parse dictionary: {'KEY': 'value'}
    key_name = list(pattern_dict.keys())[0]
    expected_state = pattern_dict[key_name]
    
    # Get actual state from registry
    actual_state = registry.get(key_name, 'not_found')
    
    # Case-insensitive comparison
    if actual_state.lower() == expected_state.lower():
        found_items.append({
            'name': key_name,
            'expected': expected_state,
            'actual': actual_state,
            'status': 'MATCH'
        })
    else:
        missing_items.append({
            'name': key_name,
            'expected': expected_state,
            'actual': actual_state,
            'status': 'MISMATCH'
        })
```

**Step 5: Determine PASS/FAIL**
- PASS: All pattern_items match expected state (missing_items is empty)
- FAIL: Any pattern_item does NOT match expected state (missing_items not empty)

**Edge Cases:**
1. Flag defined in sourceme but not in PVL log → Use sourceme value (PVL didn't override)
2. Flag in PVL log but not in sourceme → PVL value takes precedence
3. Flag not in either file → Treat as 'disabled' (default state)
4. POWER_NAME/GROUND_NAME lists → Compare as sorted lists (order doesn't matter)
5. Case variations (e.g., "Enabled" vs "enabled") → Use case-insensitive comparison

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

**Rationale:** This checker validates the STATUS (enabled/disabled) of specific LVS configuration flags defined in pattern_items. It only checks flags explicitly listed in pattern_items (e.g., WELL_TO_PG_CHECK, RC_DFM_RULE) and ignores other flags present in the files. The checker compares actual state against expected state for each pattern_item, making it a status validation check rather than an existence check.

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
item_desc = "Confirm the LVS rule deck setting is correct."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "LVS rule deck configuration validated successfully"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "LVS rule deck setting matched expected configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All LVS configuration flags found with correct states in rule deck files"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "LVS configuration flag matched expected state (enabled/disabled as required)"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "LVS rule deck configuration validation failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "LVS rule deck setting does not match expected configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required LVS configuration flag not found or has incorrect state in rule deck files"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "LVS configuration flag state mismatch - expected: {expected}, actual: {actual}"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "LVS rule deck setting mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "LVS configuration mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused LVS configuration waiver entry"
unused_waiver_reason = "Waiver not matched - no corresponding LVS configuration mismatch found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [flag_name]: expected=[expected_state], actual=[actual_state] - LVS configuration flag matched expected state"
  Example: "- WELL_TO_PG_CHECK: expected=enabled, actual=enabled - LVS configuration flag matched expected state"

ERROR01 (Violation/Fail items):
  Format: "- [flag_name]: expected=[expected_state], actual=[actual_state] - LVS configuration flag state mismatch"
  Example: "- RC_DFM_RULE: expected=disabled, actual=enabled - LVS configuration flag state mismatch - expected: disabled, actual: enabled"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-09:
  description: "Confirm the LVS rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of LVS rule deck configuration files.
PASS if both files exist and contain valid LVS configuration syntax.
FAIL if files are missing, empty, or contain syntax errors.

**Sample Output (PASS):**
```
Status: PASS
Reason: All LVS configuration flags found with correct states in rule deck files

Log format (CheckList.rpt):
INFO01:
  - LVS rule deck files validated

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: LVS rule deck files validated. In line 1, do_pvs_LVS_pvl.log: All LVS configuration flags found with correct states in rule deck files
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required LVS configuration flag not found or has incorrect state in rule deck files

Log format (CheckList.rpt):
ERROR01:
  - LVS rule deck configuration invalid

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: LVS rule deck configuration invalid. In line 1, do_pvs_LVS_pvl.log: Required LVS configuration flag not found or has incorrect state in rule deck files
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-09:
  description: "Confirm the LVS rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: LVS rule deck validation is informational only for this design phase"
      - "Note: Configuration mismatches are expected during early development and do not block signoff"
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
  - "Explanation: LVS rule deck validation is informational only for this design phase"
  - "Note: Configuration mismatches are expected during early development and do not block signoff"
INFO02:
  - LVS configuration mismatch (waived)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: LVS rule deck validation is informational only for this design phase. [WAIVED_INFO]
2: Info: LVS configuration mismatch (waived). In line 35, do_cmd_3star_LVS_sourceme: Required LVS configuration flag not found or has incorrect state in rule deck files [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-09:
  description: "Confirm the LVS rule deck setting is correct."
  requirements:
    value: 41  # ⚠️ CRITICAL: MUST equal len(pattern_items)!
    pattern_items:
      - RC_DFM_RULE: disabled
      - SKIP_ODSE: disabled
      - FILTER_DGS_TIED_MOS: disabled
      - WELL_TO_PG_CHECK: enabled
      - GATE_TO_PG_CHECK: disabled
      - PATH_CHECK: disabled
      - DS_TO_PG_CHECK: enabled
      - FLOATING_WELL_CHECK: enabled
      - LVSDMY4_CHECK: enabled
      - NW_RING: disabled
      - unrecognized_device_checking: disabled
      - unexpected_layer_checking_INDDMY: enabled
      - PICKUP_CHECK: enabled
      - PSUB2_ERC_CHECK: enabled
      - MNPP_MPGG_VIRT_PWR_ENABLE: disabled
      - REGMOS_MNPP_MPGG_CHECK: enabled
      - MPODE_MNPP_MPGG_CHECK: enabled
      - FLRMOS_MNPP_MPGG_CHECK: enabled
      - MNPP_MPGG_LAYER_WAIVER_ENABLE: disabled
      - WELL_TEXT: disabled
      - SKIP_PLE: disabled
      - SKIP_CPO: disabled
      - SKIP_PODG: disabled
      - SKIP_VGP: disabled
      - SKIP_XVTMBE: disabled
      - SKIP_CODH: disabled
      - SEALRING_CHECK: disabled
      - FILTER_PODE: enabled
      - FILTER_MPODE: enabled
      - FILTER_FLRMOS: enabled
      - MATCHFLAG: enabled
      - METAL_MAIN_CHECK: enabled
      - extract_dnwpsub: disabled
      - extract_pwdnw: disabled
      - extract_pnwdio: disabled
      - LVS_REDUCE_PARALLEL_MOS: disabled
      - LVS_REDUCE_PARALLEL_MIMCAP: disabled
      - LVS_REDUCE_SPLIT_GATES: disabled
      - SELF_HEATING_EFFECT_EXTRACTION: disabled
      - CDN_ERC: enabled
      - POWER_NAME: [ahvdd, ahvddb, ahvddg, ahvddr, ahvddwell, avdd, avddb, avddbg, avddg, avddr, avdwell, dhvdd, dvdd, hvddwell, tacvdd, tavd33, tavd33pst, tavdd, tavddpst, tvdd, vd33, vdd, vdd5v, vddesd, vddg, vddm, vddpst, vddsa, vdwell]
      - GROUND_NAME: [agnd, ahvss, ahvssb, ahvssg, ahvssr, ahvssub, avss, avssb, avssbg, avssg, avssr, avssub, dhvss, dvss, gnd, hvssub, tacvss, tavss, tavsspst, tvss, vs33, vss, vssesd, vssg, vssm, vsspst, vssub]
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Each pattern_item is a DICTIONARY: `{'FLAG_NAME': 'expected_state'}`
- Expected state values: "enabled" or "disabled" (case-insensitive)
- For POWER_NAME/GROUND_NAME: Use list format `{'POWER_NAME': [net1, net2, ...]}`
- Pattern items represent GOLDEN VALUES (expected configuration states)

**Check Behavior:**
Type 2 validates LVS configuration flag states against expected values.
PASS if all pattern_items match their expected states (missing_items empty).
FAIL if any pattern_item does NOT match expected state (missing_items not empty).

**Sample Output (PASS):**
```
Status: PASS
Reason: LVS configuration flag matched expected state (enabled/disabled as required)

Log format (CheckList.rpt):
INFO01:
  - WELL_TO_PG_CHECK: expected=enabled, actual=enabled
  - FLOATING_WELL_CHECK: expected=enabled, actual=enabled
  - RC_DFM_RULE: expected=disabled, actual=disabled

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: WELL_TO_PG_CHECK: expected=enabled, actual=enabled. In line 85, do_pvs_LVS_pvl.log: LVS configuration flag matched expected state (enabled/disabled as required)
2: Info: FLOATING_WELL_CHECK: expected=enabled, actual=enabled. In line 92, do_pvs_LVS_pvl.log: LVS configuration flag matched expected state (enabled/disabled as required)
3: Info: RC_DFM_RULE: expected=disabled, actual=disabled. In line 20, do_cmd_3star_LVS_sourceme: LVS configuration flag matched expected state (enabled/disabled as required)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-09:
  description: "Confirm the LVS rule deck setting is correct."
  requirements:
    value: 41
    pattern_items:
      - RC_DFM_RULE: disabled
      - WELL_TO_PG_CHECK: enabled
      # ... (same 41 items as above)
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: LVS configuration check is informational during early design phase"
      - "Note: Flag state mismatches are expected and will be corrected before final signoff"
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
  - "Explanation: LVS configuration check is informational during early design phase"
  - "Note: Flag state mismatches are expected and will be corrected before final signoff"
INFO02:
  - RC_DFM_RULE: expected=disabled, actual=enabled (waived)
  - GATE_TO_PG_CHECK: expected=disabled, actual=enabled (waived)

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: LVS configuration check is informational during early design phase. [WAIVED_INFO]
2: Info: Note: Flag state mismatches are expected and will be corrected before final signoff. [WAIVED_INFO]
3: Info: RC_DFM_RULE: expected=disabled, actual=enabled. In line 22, do_cmd_3star_LVS_sourceme: LVS configuration flag state mismatch - expected: disabled, actual: enabled [WAIVED_AS_INFO]
4: Info: GATE_TO_PG_CHECK: expected=disabled, actual=enabled. In line 88, do_pvs_LVS_pvl.log: LVS configuration flag state mismatch - expected: disabled, actual: enabled [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-09:
  description: "Confirm the LVS rule deck setting is correct."
  requirements:
    value: 41  # ⚠️ CRITICAL: MUST equal len(pattern_items)!
    pattern_items:
      - RC_DFM_RULE: disabled
      - SKIP_ODSE: disabled
      - FILTER_DGS_TIED_MOS: disabled
      - WELL_TO_PG_CHECK: enabled
      - GATE_TO_PG_CHECK: disabled
      - PATH_CHECK: disabled
      - DS_TO_PG_CHECK: enabled
      - FLOATING_WELL_CHECK: enabled
      - LVSDMY4_CHECK: enabled
      - NW_RING: disabled
      - unrecognized_device_checking: disabled
      - unexpected_layer_checking_INDDMY: enabled
      - PICKUP_CHECK: enabled
      - PSUB2_ERC_CHECK: enabled
      - MNPP_MPGG_VIRT_PWR_ENABLE: disabled
      - REGMOS_MNPP_MPGG_CHECK: enabled
      - MPODE_MNPP_MPGG_CHECK: enabled
      - FLRMOS_MNPP_MPGG_CHECK: enabled
      - MNPP_MPGG_LAYER_WAIVER_ENABLE: disabled
      - WELL_TEXT: disabled
      - SKIP_PLE: disabled
      - SKIP_CPO: disabled
      - SKIP_PODG: disabled
      - SKIP_VGP: disabled
      - SKIP_XVTMBE: disabled
      - SKIP_CODH: disabled
      - SEALRING_CHECK: disabled
      - FILTER_PODE: enabled
      - FILTER_MPODE: enabled
      - FILTER_FLRMOS: enabled
      - MATCHFLAG: enabled
      - METAL_MAIN_CHECK: enabled
      - extract_dnwpsub: disabled
      - extract_pwdnw: disabled
      - extract_pnwdio: disabled
      - LVS_REDUCE_PARALLEL_MOS: disabled
      - LVS_REDUCE_PARALLEL_MIMCAP: disabled
      - LVS_REDUCE_SPLIT_GATES: disabled
      - SELF_HEATING_EFFECT_EXTRACTION: disabled
      - CDN_ERC: enabled
      - POWER_NAME: [ahvdd, ahvddb, ahvddg, ahvddr, ahvddwell, avdd, avddb, avddbg, avddg, avddr, avdwell, dhvdd, dvdd, hvddwell, tacvdd, tavd33, tavd33pst, tavdd, tavddpst, tvdd, vd33, vdd, vdd5v, vddesd, vddg, vddm, vddpst, vddsa, vdwell]
      - GROUND_NAME: [agnd, ahvss, ahvssb, ahvssg, ahvssr, ahvssub, avss, avssb, avssbg, avssg, avssr, avssub, dhvss, dvss, gnd, hvssub, tacvss, tavss, tavsspst, tvss, vs33, vss, vssesd, vssg, vssm, vsspst, vssub]
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "RC_DFM_RULE"  # ⚠️ EXEMPTION - Flag name to exempt (NOT expected state!)
        reason: "Waived - DFM rule checking not required for this design per foundry approval"
      - name: "GATE_TO_PG_CHECK"
        reason: "Waived - Gate-to-power/ground check disabled for analog blocks per design team"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items (mismatches) against waive_items by flag name
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - RC_DFM_RULE: expected=disabled, actual=enabled (waived)
  - GATE_TO_PG_CHECK: expected=disabled, actual=enabled (waived)
WARN01:
  - (No unused waivers in this example)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: RC_DFM_RULE: expected=disabled, actual=enabled. In line 22, do_cmd_3star_LVS_sourceme: LVS configuration mismatch waived per design team approval: Waived - DFM rule checking not required for this design per foundry approval [WAIVER]
2: Info: GATE_TO_PG_CHECK: expected=disabled, actual=enabled. In line 88, do_pvs_LVS_pvl.log: LVS configuration mismatch waived per design team approval: Waived - Gate-to-power/ground check disabled for analog blocks per design team [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-09:
  description: "Confirm the LVS rule deck setting is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "RC_DFM_RULE"  # ⚠️ MUST match Type 3 waive_items!
        reason: "Waived - DFM rule checking not required for this design per foundry approval"
      - name: "GATE_TO_PG_CHECK"
        reason: "Waived - Gate-to-power/ground check disabled for analog blocks per design team"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep flag names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items by flag name
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
  - RC_DFM_RULE configuration mismatch (waived)
  - GATE_TO_PG_CHECK configuration mismatch (waived)
WARN01:
  - (No unused waivers in this example)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: RC_DFM_RULE configuration mismatch. In line 22, do_cmd_3star_LVS_sourceme: LVS configuration mismatch waived per design team approval: Waived - DFM rule checking not required for this design per foundry approval [WAIVER]
2: Info: GATE_TO_PG_CHECK configuration mismatch. In line 88, do_pvs_LVS_pvl.log: LVS configuration mismatch waived per design team approval: Waived - Gate-to-power/ground check disabled for analog blocks per design team [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-09 --force

# Run individual tests
python IMP-12-0-0-09.py
```

---

## Notes

**Important Implementation Details:**

1. **Parsing Priority:** PVL log file ALWAYS takes precedence over sourceme file. This represents actual tool behavior vs intended configuration.

2. **Dictionary Pattern Items:** Each pattern_item is a DICTIONARY `{'KEY': 'value'}`, NOT a plain string. Parser must extract key and value separately.

3. **Case-Insensitive Comparison:** Use `.lower()` when comparing enabled/disabled states to handle variations like "Enabled", "ENABLED", "enabled".

4. **Registry Overwrite Logic:** When parsing PVL log, ALWAYS overwrite registry values. Do NOT check "if key not in registry" - PVL represents actual execution state.

5. **Power/Ground Name Lists:** POWER_NAME and GROUND_NAME are lists of net names. Compare as sorted sets (order doesn't matter).

6. **File Format Differences:**
   - PVL log uses `#DEFINE` (uppercase)
   - Sourceme uses `#define` (lowercase)
   - Commented flags in sourceme: `//\s*#define`

7. **Edge Case Handling:**
   - Flag in PVL but not sourceme → Use PVL value (actual execution)
   - Flag in sourceme but not PVL → Use sourceme value (intended config)
   - Flag in neither file → Treat as 'disabled' (default state)

8. **Waiver Matching:** For Type 3/4, match waive_items by flag NAME (not by expected state). The name field identifies which flag mismatch is approved for exemption.

**Known Limitations:**

- Checker assumes standard LVS rule deck format (Pegasus/Calibre syntax)
- Does not validate semantic correctness of flag combinations (e.g., conflicting settings)
- POWER_NAME/GROUND_NAME list comparison is order-independent but requires exact name matches
- Multi-line #define statements are not supported (assumes single-line format)