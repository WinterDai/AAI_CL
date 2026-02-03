# IMP-12-0-0-06: Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)

## Overview

**Check ID:** IMP-12-0-0-06  
**Description:** Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)  
**Category:** Physical Verification - DRC Configuration Validation  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme

This checker validates that MIM (Metal-Insulator-Metal) capacitor related DRC check switches are configured correctly in the Pegasus/Calibre DRC rule deck. It verifies that MIM-related #DEFINE switches (SHDMIM, FHDMIM, KOZ spacing rules, etc.) match the expected configuration for the design. The checker parses both the intended configuration (sourceme script) and the actual parsed configuration (PVL log) to ensure consistency.

**Key Validation Points:**
- MIM capacitor type enablement (SHDMIM vs FHDMIM)
- Keep-Out-Zone (KOZ) spacing rules configuration
- CoWoS_S advanced packaging switch status
- Consistency between intended (sourceme) and actual (PVL log) configurations

---

## Check Logic

### Input Parsing

**File 1: do_cmd_3star_DRC_sourceme (Intended Configuration)**
This file contains the DRC rule deck configuration script with #DEFINE switches that represent the intended MIM configuration before rule deck parsing.

**File 2: do_pvs_DRC_pvl.log (Actual Configuration - Takes Precedence)**
This file contains the Pegasus PVL parsing log showing which #DEFINE switches were actually enabled during rule deck parsing. This represents the actual tool behavior and takes precedence over the sourceme file.

**Parsing Strategy:**
1. Parse sourceme file first to build initial configuration registry
2. Parse PVL log second - ALWAYS overwrite registry entries (represents actual tool behavior)
3. Compare final registry against expected pattern_items configuration
4. Use case-insensitive comparison for enabled/disabled states

**Key Patterns:**

```python
# Pattern 1: Enabled MIM switches in sourceme (intended config)
sourceme_enabled = r'^\s*#DEFINE\s+((?:SHD|FHD)MIM[A-Z0-9_]*|CoWoS_S|KOZ_High_subst_layer)\s*(?://.*)?$'
# Example: "#DEFINE SHDMIM              // Turn on to check related MIM.AP.* rules"

# Pattern 2: Disabled MIM switches in sourceme (commented out)
sourceme_disabled = r'^\s*(?://|#)\s*#?DEFINE\s+((?:SHD|FHD)MIM[A-Z0-9_]*|CoWoS_S|KOZ_High_subst_layer)\s*(?://.*)?$'
# Example: "//#DEFINE FHDMIM              // Turn on to check FHDMIM related rules"

# Pattern 3: Active MIM switches in PVL log (actual config - takes precedence)
pvl_enabled = r'^#DEFINE\s+(.*MIM.*|SHDMIM.*|.*MIMCAP.*|CoWoS_S|KOZ_High_subst_layer)\s*$'
# Example: "#DEFINE SHDMIM"

# Pattern 4: Rule file path header in PVL log
pvl_header = r'^Parsing Rule File\s+(.+\.pvl)\s+\.\.\.'
# Example: "Parsing Rule File scr/tv_chip.DRCwD.pvl ..."
```

### Detection Logic

**Step 1: Parse Sourceme File (Low Priority)**
- Scan all lines for MIM-related #DEFINE switches
- Track enabled switches (uncommented #DEFINE)
- Track disabled switches (commented with // or #)
- Build initial configuration registry: `{switch_name: 'enabled'/'disabled'}`

**Step 2: Parse PVL Log (High Priority - Overwrites)**
- Extract rule file path from header section
- Scan for all #DEFINE directives
- Filter for MIM-related switches (SHDMIM, FHDMIM, KOZ, CoWoS_S, etc.)
- ALWAYS overwrite registry entries from Step 1 (represents actual tool behavior)
- Final registry represents actual parsed configuration

**Step 3: Validate Against Requirements**
- Compare final registry against pattern_items (expected configuration)
- Each pattern_item is a dictionary: `{'switch_name': 'expected_state'}`
- Use case-insensitive comparison for states ('enabled', 'disabled', 'Enabled', 'DISABLED')
- Generate found_items (matching configuration) and missing_items (mismatches)

**Step 4: Special Cases**
- If no MIM switches found in either file → Return 'N/A - No MIMCAP inserted'
- If sourceme exists but PVL log missing → Use sourceme only (with warning)
- If PVL log exists but sourceme missing → Use PVL log only
- Conflicting states between files → PVL log wins (actual behavior)

**Edge Cases:**
- Switches with inline comments: `#DEFINE SHDMIM // comment` → Extract switch name only
- Case variations: SHDMIM vs shdmim → Normalize to uppercase for comparison
- Multiple rule files in same PVL log → Process all, track by file path
- Empty or malformed files → Report parsing error

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

### Mode 2: `status_check` - Status Check  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: [{'SHDMIM': 'enabled'}, {'FHDMIM': 'disabled'}]
Input file contains: SHDMIM(enabled), FHDMIM(enabled), CoWoS_S(disabled)

Result:
  found_items:   SHDMIM            ← Pattern matched AND status correct
  missing_items: FHDMIM            ← Pattern matched BUT status wrong
  (CoWoS_S not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the configuration STATUS of specific MIM-related switches. The pattern_items define which switches to check and their expected states (enabled/disabled). The checker only reports on switches listed in pattern_items, comparing their actual state against the expected state. Switches not in pattern_items are ignored. This is a status validation check, not an existence check.

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
item_desc = "Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "MIM configuration switches found in DRC rule deck"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "MIM switch configuration matched expected settings"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "MIM-related #DEFINE switches found in PVL parsing log and sourceme configuration"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "MIM switch state matched expected configuration (actual state matches requirement)"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Required MIM configuration switches not found in DRC setup"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "MIM switch configuration mismatch detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required MIM switches not found in PVL log or sourceme file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "MIM switch state does not match expected configuration (expected: {expected}, actual: {actual})"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived MIM configuration mismatches"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "MIM switch configuration mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused MIM configuration waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding MIM switch mismatch found in actual configuration"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [switch_name]: MIM switch state matched expected configuration (expected: enabled, actual: enabled)"
  Example: "- SHDMIM: MIM switch state matched expected configuration (expected: enabled, actual: enabled)"

ERROR01 (Violation/Fail items):
  Format: "- [switch_name]: MIM switch state does not match expected configuration (expected: enabled, actual: disabled)"
  Example: "- FHDMIM: MIM switch state does not match expected configuration (expected: disabled, actual: enabled)"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. The reason strings include both expected and actual states for clear debugging.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-06:
  description: "Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean check to verify if any MIM-related configuration exists in the DRC setup files. Returns PASS if MIM switches are found and properly configured, FAIL if configuration is missing or invalid.

**Sample Output (PASS):**
```
Status: PASS
Reason: MIM-related #DEFINE switches found in PVL parsing log and sourceme configuration

Log format (CheckList.rpt):
INFO01:
  - SHDMIM: enabled
  - FHDMIM: disabled
  - CoWoS_S: disabled

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: SHDMIM. In line 26, do_cmd_3star_DRC_sourceme: MIM-related #DEFINE switches found in PVL parsing log and sourceme configuration
2: Info: FHDMIM. In line 27, do_cmd_3star_DRC_sourceme: MIM-related #DEFINE switches found in PVL parsing log and sourceme configuration
3: Info: CoWoS_S. In line 25, do_cmd_3star_DRC_sourceme: MIM-related #DEFINE switches found in PVL parsing log and sourceme configuration
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required MIM switches not found in PVL log or sourceme file

Log format (CheckList.rpt):
ERROR01:
  - No MIM configuration detected

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: MIM configuration. In line 0, do_pvs_DRC_pvl.log: Required MIM switches not found in PVL log or sourceme file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-06:
  description: "Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: MIM configuration check is informational only for designs without MIMCAP"
      - "Note: Configuration mismatches are expected for non-MIM designs and do not require fixes"
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
  - "Explanation: MIM configuration check is informational only for designs without MIMCAP"
  - "Note: Configuration mismatches are expected for non-MIM designs and do not require fixes"
INFO02:
  - FHDMIM: enabled (expected: disabled)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: MIM configuration check is informational only for designs without MIMCAP. [WAIVED_INFO]
2: Info: Note: Configuration mismatches are expected for non-MIM designs and do not require fixes. [WAIVED_INFO]
3: Info: FHDMIM. In line 27, do_cmd_3star_DRC_sourceme: Required MIM switches not found in PVL log or sourceme file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-06:
  description: "Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"
  requirements:
    value: 8  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - CoWoS_S: "disabled"
      - SHDMIM: "enabled"
      - FHDMIM: "disabled"
      - KOZ_High_subst_layer: "disabled"
      - SHDMIM_KOZ_AP_SPACE_5um: "disabled"
      - SHDMIM_KOZ_AP_SPACE_5um_IP: "disabled"
      - FHDMIM_KOZ_AP_SPACE_5um: "disabled"
      - FHDMIM_KOZ_AP_SPACE_5um_IP: "disabled"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items are DICTIONARIES: `{'switch_name': 'expected_state'}`
- Each dictionary defines one switch and its expected enabled/disabled state
- States are case-insensitive: 'enabled', 'Enabled', 'ENABLED' all valid
- Switch names should match actual #DEFINE names in rule deck files

**Check Behavior:**
Type 2 searches for MIM-related switches in input files and validates their states against pattern_items.
- Parse sourceme file first (intended config)
- Parse PVL log second (actual config - overwrites sourceme)
- Compare final states against pattern_items
- PASS if all switches match expected states (missing_items empty)
- FAIL if any switch has wrong state (missing_items not empty)

**Sample Output (PASS):**
```
Status: PASS
Reason: MIM switch configuration matched expected settings (8/8)

Log format (CheckList.rpt):
INFO01:
  - CoWoS_S: disabled (matched)
  - SHDMIM: enabled (matched)
  - FHDMIM: disabled (matched)
  - KOZ_High_subst_layer: disabled (matched)
  - SHDMIM_KOZ_AP_SPACE_5um: disabled (matched)
  - SHDMIM_KOZ_AP_SPACE_5um_IP: disabled (matched)
  - FHDMIM_KOZ_AP_SPACE_5um: disabled (matched)
  - FHDMIM_KOZ_AP_SPACE_5um_IP: disabled (matched)

Report format (item_id.rpt):
Info Occurrence: 8
1: Info: CoWoS_S. In line 25, do_cmd_3star_DRC_sourceme: MIM switch state matched expected configuration (expected: disabled, actual: disabled)
2: Info: SHDMIM. In line 26, do_cmd_3star_DRC_sourceme: MIM switch state matched expected configuration (expected: enabled, actual: enabled)
...
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: MIM switch configuration mismatch detected (6/8 matched, 2 mismatches)

Log format (CheckList.rpt):
INFO01:
  - CoWoS_S: disabled (matched)
  - SHDMIM: enabled (matched)
  - KOZ_High_subst_layer: disabled (matched)
  - SHDMIM_KOZ_AP_SPACE_5um: disabled (matched)
  - SHDMIM_KOZ_AP_SPACE_5um_IP: disabled (matched)
  - FHDMIM_KOZ_AP_SPACE_5um: disabled (matched)
ERROR01:
  - FHDMIM: expected disabled, actual enabled
  - FHDMIM_KOZ_AP_SPACE_5um_IP: expected disabled, actual enabled

Report format (item_id.rpt):
Info Occurrence: 6
1: Info: CoWoS_S. In line 25, do_cmd_3star_DRC_sourceme: MIM switch state matched expected configuration (expected: disabled, actual: disabled)
...
Fail Occurrence: 2
1: Fail: FHDMIM. In line 27, do_cmd_3star_DRC_sourceme: MIM switch state does not match expected configuration (expected: disabled, actual: enabled)
2: Fail: FHDMIM_KOZ_AP_SPACE_5um_IP. In line 30, do_cmd_3star_DRC_sourceme: MIM switch state does not match expected configuration (expected: disabled, actual: enabled)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-06:
  description: "Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"
  requirements:
    value: 8
    pattern_items:
      - CoWoS_S: "disabled"
      - SHDMIM: "enabled"
      - FHDMIM: "disabled"
      - KOZ_High_subst_layer: "disabled"
      - SHDMIM_KOZ_AP_SPACE_5um: "disabled"
      - SHDMIM_KOZ_AP_SPACE_5um_IP: "disabled"
      - FHDMIM_KOZ_AP_SPACE_5um: "disabled"
      - FHDMIM_KOZ_AP_SPACE_5um_IP: "disabled"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: MIM configuration check is informational for legacy designs using non-standard MIM settings"
      - "Note: FHDMIM enablement is expected for certain test chips and does not require fixes"
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
  - "Explanation: MIM configuration check is informational for legacy designs using non-standard MIM settings"
  - "Note: FHDMIM enablement is expected for certain test chips and does not require fixes"
INFO02:
  - FHDMIM: expected disabled, actual enabled
  - FHDMIM_KOZ_AP_SPACE_5um_IP: expected disabled, actual enabled

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: MIM configuration check is informational for legacy designs using non-standard MIM settings. [WAIVED_INFO]
2: Info: Note: FHDMIM enablement is expected for certain test chips and does not require fixes. [WAIVED_INFO]
3: Info: FHDMIM. In line 27, do_cmd_3star_DRC_sourceme: MIM switch state does not match expected configuration (expected: disabled, actual: enabled) [WAIVED_AS_INFO]
4: Info: FHDMIM_KOZ_AP_SPACE_5um_IP. In line 30, do_cmd_3star_DRC_sourceme: MIM switch state does not match expected configuration (expected: disabled, actual: enabled) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-06:
  description: "Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"
  requirements:
    value: 8  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - CoWoS_S: "disabled"
      - SHDMIM: "enabled"
      - FHDMIM: "disabled"
      - KOZ_High_subst_layer: "disabled"
      - SHDMIM_KOZ_AP_SPACE_5um: "disabled"
      - SHDMIM_KOZ_AP_SPACE_5um_IP: "disabled"
      - FHDMIM_KOZ_AP_SPACE_5um: "disabled"
      - FHDMIM_KOZ_AP_SPACE_5um_IP: "disabled"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "FHDMIM"
        reason: "Waived - Test chip uses FHDMIM for characterization purposes per design team approval"
      - name: "FHDMIM_KOZ_AP_SPACE_5um_IP"
        reason: "Waived - IP-level KOZ spacing not required for this integration per foundry waiver"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Parse files and compare switch states against pattern_items
- Match mismatched switches against waive_items by name
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
- PASS if all mismatches are waived

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived (2 waived, 6 matched)

Log format (CheckList.rpt):
INFO01:
  - CoWoS_S: disabled (matched)
  - SHDMIM: enabled (matched)
  - KOZ_High_subst_layer: disabled (matched)
  - SHDMIM_KOZ_AP_SPACE_5um: disabled (matched)
  - SHDMIM_KOZ_AP_SPACE_5um_IP: disabled (matched)
  - FHDMIM_KOZ_AP_SPACE_5um: disabled (matched)
  - FHDMIM: expected disabled, actual enabled (waived)
  - FHDMIM_KOZ_AP_SPACE_5um_IP: expected disabled, actual enabled (waived)

Report format (item_id.rpt):
Info Occurrence: 8
1: Info: CoWoS_S. In line 25, do_cmd_3star_DRC_sourceme: MIM switch state matched expected configuration (expected: disabled, actual: disabled)
...
7: Info: FHDMIM. In line 27, do_cmd_3star_DRC_sourceme: MIM switch configuration mismatch waived per design team approval: Waived - Test chip uses FHDMIM for characterization purposes per design team approval [WAIVER]
8: Info: FHDMIM_KOZ_AP_SPACE_5um_IP. In line 30, do_cmd_3star_DRC_sourceme: MIM switch configuration mismatch waived per design team approval: Waived - IP-level KOZ spacing not required for this integration per foundry waiver [WAIVER]
```

**Sample Output (with unused waiver):**
```
Status: PASS
Reason: All violations waived (1 waived, 7 matched, 1 unused waiver)

Log format (CheckList.rpt):
INFO01:
  - [7 matched switches]
  - FHDMIM: expected disabled, actual enabled (waived)
WARN01:
  - FHDMIM_KOZ_AP_SPACE_5um_IP: waiver not used

Report format (item_id.rpt):
Info Occurrence: 8
...
Warn Occurrence: 1
1: Warn: FHDMIM_KOZ_AP_SPACE_5um_IP. In line 0, N/A: Waiver entry not matched - no corresponding MIM switch mismatch found in actual configuration: Waived - IP-level KOZ spacing not required for this integration per foundry waiver [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-06:
  description: "Confirm the MIM related check setting is correct. (Fill N/A if no MIMCAP inserted or no MIM related layers)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "FHDMIM"
        reason: "Waived - Test chip uses FHDMIM for characterization purposes per design team approval"
      - name: "FHDMIM_KOZ_AP_SPACE_5um_IP"
        reason: "Waived - IP-level KOZ spacing not required for this integration per foundry waiver"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (switch names to exempt)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Detect MIM configuration violations using custom logic
- Match violations against waive_items by switch name
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
- PASS if all violations are waived

**Sample Output:**
```
Status: PASS
Reason: All items waived (2 violations waived)

Log format (CheckList.rpt):
INFO01:
  - FHDMIM: configuration mismatch (waived)
  - FHDMIM_KOZ_AP_SPACE_5um_IP: configuration mismatch (waived)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: FHDMIM. In line 27, do_cmd_3star_DRC_sourceme: MIM switch configuration mismatch waived per design team approval: Waived - Test chip uses FHDMIM for characterization purposes per design team approval [WAIVER]
2: Info: FHDMIM_KOZ_AP_SPACE_5um_IP. In line 30, do_cmd_3star_DRC_sourceme: MIM switch configuration mismatch waived per design team approval: Waived - IP-level KOZ spacing not required for this integration per foundry waiver [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-06 --force

# Run individual tests
python IMP-12-0-0-06.py
```

---

## Notes

**Important Implementation Details:**

1. **Parsing Priority:** PVL log takes precedence over sourceme file
   - Sourceme represents intended configuration
   - PVL log represents actual parsed configuration (what tool sees)
   - Always overwrite sourceme entries with PVL log entries

2. **Case Sensitivity:**
   - Switch names: Case-sensitive matching (SHDMIM ≠ shdmim)
   - State values: Case-insensitive comparison ('enabled' == 'Enabled' == 'ENABLED')

3. **Dictionary Pattern Items:**
   - Each pattern_item is a dictionary: `{'switch_name': 'expected_state'}`
   - Must parse dictionary first before extracting switch name and state
   - State comparison uses case-insensitive logic

4. **N/A Handling:**
   - If no MIM switches found in either file → Return 'N/A - No MIMCAP inserted'
   - This is a valid PASS state (design doesn't use MIM capacitors)

5. **Multi-File Consistency:**
   - Checker validates consistency between intended (sourceme) and actual (PVL) config
   - Discrepancies indicate potential rule deck parsing issues
   - PVL log always wins in case of conflict

6. **Known Limitations:**
   - Assumes standard #DEFINE syntax in both files
   - Does not validate MIM layer geometry rules (only switch configuration)
   - Cannot detect runtime switch overrides not logged in PVL output