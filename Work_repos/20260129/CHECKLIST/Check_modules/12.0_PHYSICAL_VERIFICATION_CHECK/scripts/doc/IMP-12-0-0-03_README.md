# IMP-12-0-0-03: Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA.

## Overview

**Check ID:** IMP-12-0-0-03  
**Description:** Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA.  
**Category:** Physical Verification - DRC Rule Deck Configuration Validation  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme

This checker validates DRC rule deck configuration by comparing switch settings and variable values against Foundry CTA (Calibre Technology Acceptance) reference requirements. It extracts all #DEFINE switches (enabled/disabled) and VARIABLE assignments from both Pegasus PVL parsing logs and Calibre DRC sourceme scripts, then verifies each setting matches the expected pattern_items configuration. The checker ensures design rule checking uses approved foundry settings to prevent silicon failures.

---

## Check Logic

### Input Parsing

**File 1: do_pvs_DRC_pvl.log (Pegasus PVL Parsing Log)**
- Extract enabled #DEFINE switches from parsing output
- Capture switch names and their enabled/disabled state
- Track source file path and line numbers for traceability

**File 2: do_cmd_3star_DRC_sourceme (Calibre DRC Configuration Script)**
- Extract active #DEFINE switches (uncommented lines)
- Extract commented/disabled #DEFINE switches (lines starting with //)
- Extract VARIABLE assignments with their values
- Parse LAYOUT directives for metadata

**Key Patterns:**

```python
# Pattern 1: Active #DEFINE switch (enabled)
pattern_enabled = r'^\s*#DEFINE\s+([A-Z_0-9]+)\s*(?://\s*(.*))?$'
# Example: "#DEFINE CHECK_LOW_DENSITY   // Turn off to skip local low density check"
# Extracts: switch_name="CHECK_LOW_DENSITY", status="enabled"

# Pattern 2: Commented/disabled #DEFINE switch
pattern_disabled = r'^\s*//\s*#DEFINE\s+([A-Z_0-9]+)\s*(?://\s*(.*))?$'
# Example: "//#DEFINE FULL_CHIP           // Turn on for chip level design"
# Extracts: switch_name="FULL_CHIP", status="disabled"

# Pattern 3: VARIABLE definitions with values
pattern_variable = r'^\s*VARIABLE\s+([A-Z_0-9]+)\s+"?([^"\n]+)"?\s*(?://\s*(.*))?$'
# Example: 'VARIABLE PAD_TEXT  "pad_atb? pad_cal_0"       // pin name of PAD'
# Extracts: variable_name="PAD_TEXT", value="pad_atb? pad_cal_0"

# Pattern 4: Pegasus PVL parsing log switches
pattern_pvl_define = r'^#DEFINE\s+([A-Za-z0-9_]+)\s*$'
# Example: "#DEFINE FULL_CHIP"
# Extracts: switch_name="FULL_CHIP"

# Pattern 5: Rule file path from parsing header
pattern_rule_file = r'^Parsing Rule File\s+(.+?)\s+\.\.\.$'
# Example: "Parsing Rule File scr/tv_chip.DRCwD.pvl ..."
# Extracts: rule_file_path="scr/tv_chip.DRCwD.pvl"
```

### Detection Logic

**Step 1: Parse Input Files**
- Scan do_pvs_DRC_pvl.log line-by-line to extract enabled switches from Pegasus parsing output
- Scan do_cmd_3star_DRC_sourceme line-by-line to extract all switches and variables
- Build registry: `{switch_name: {status: "enabled"/"disabled", line_number: N, file: "path"}}`
- Build variable registry: `{variable_name: {value: "...", line_number: N}}`

**Step 2: Compare Against Requirements (pattern_items)**
- For each pattern_item (key-value pair):
  - If key is a switch name: Check if actual status matches expected status ("enabled"/"disabled")
  - If key is a variable name: Check if actual value matches expected value
- Classify results:
  - **found_items**: Settings that match pattern_items (correct configuration)
  - **missing_items**: Settings that don't match pattern_items (mismatches or missing)

**Step 3: Generate Output**
- Report found_items as INFO01 (correct settings)
- Report missing_items as ERROR01 (configuration errors requiring justification)
- Include line numbers and file paths for traceability

**Edge Cases:**
- Multiple rule file sections in PVL log (process each separately)
- Switches with inline comments: Extract switch name only
- Variables with quoted vs unquoted values: Normalize both formats
- Missing switches in input files: Report as missing_items
- Case sensitivity: Perform case-sensitive matching for switch/variable names

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

**Rationale:** This checker validates DRC rule deck settings against CTA requirements. The pattern_items define expected switch states (enabled/disabled) and variable values. The checker only reports on settings specified in pattern_items, comparing actual status/values against expected ones. Settings not in pattern_items are ignored. This is a status validation check, not an existence check - we verify that specified settings have correct configurations, not that all possible settings exist.

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
item_desc = "DRC rule deck switch and variable settings validated against Foundry CTA requirements"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "DRC rule deck configuration found and validated"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "DRC rule deck setting matches CTA requirement"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "DRC rule deck configuration found in input files and validated against CTA"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Switch/variable setting matched and validated against CTA requirement"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "DRC rule deck configuration not found or invalid"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "DRC rule deck setting does not match CTA requirement"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required DRC configuration not found in input files or validation failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Switch/variable setting does not match CTA requirement - justification required in comments"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "DRC rule deck setting mismatch waived with justification"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "DRC rule deck setting mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entry for DRC rule deck setting"
unused_waiver_reason = "Waiver entry not matched - no corresponding setting mismatch found in input files"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [switch_name or variable_name]: [found_reason]"
  Example: "- CHECK_LOW_DENSITY: Switch/variable setting matched and validated against CTA requirement (enabled)"

ERROR01 (Violation/Fail items):
  Format: "- [switch_name or variable_name]: [missing_reason]"
  Example: "- FULL_CHIP: Switch/variable setting does not match CTA requirement - justification required in comments (Expected: disabled, Found: enabled)"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-03:
  description: "Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA."
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
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.

**Sample Output (PASS):**
```
Status: PASS
Reason: DRC rule deck configuration found in input files and validated against CTA

Log format (CheckList.rpt):
INFO01:
  - DRC rule deck configuration validated

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: DRC rule deck configuration validated. In line 1, do_cmd_3star_DRC_sourceme: DRC rule deck configuration found in input files and validated against CTA
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required DRC configuration not found in input files or validation failed

Log format (CheckList.rpt):
ERROR01:
  - DRC rule deck configuration missing

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: DRC rule deck configuration missing. In line 0, do_pvs_DRC_pvl.log: Required DRC configuration not found in input files or validation failed
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-03:
  description: "Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: DRC rule deck validation is informational only for this IP release"
      - "Note: CTA mismatches are expected for custom design rules and do not require fixes"
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
  - "Explanation: DRC rule deck validation is informational only for this IP release"
  - "Note: CTA mismatches are expected for custom design rules and do not require fixes"
INFO02:
  - DRC configuration mismatch

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: DRC rule deck validation is informational only for this IP release. [WAIVED_INFO]
2: Info: DRC configuration mismatch. In line 45, do_cmd_3star_DRC_sourceme: Required DRC configuration not found in input files or validation failed [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-03:
  description: "Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA."
  requirements:
    value: 111
    pattern_items:
      - DEBUG_VOLTAGE_RULE: disabled
      - DEBUG_VOLTAGE_RULE_WITH_METAL_CONNECTION: disabled
      - FULL_CHIP: disabled
      - WITH_SEALRING: disabled
      - CHECK_LOW_DENSITY: enabled
      - CHECK_HIGH_DENSITY: enabled
      - PT_CHECK: enabled
      - WITH_POLYIMIDE: enabled
      - WITH_APRDL: enabled
      - N4P_DTCO: disabled
      - SNAPPING_TOLERANCE: enabled
      - MASK_reduction: enabled
      - Lid: disabled
      - Ring: disabled
      - CoWoS_S: disabled
      - Check_Dummy_Under_INDDMY: enabled
      - SHDMIM: enabled
      - FHDMIM: disabled
      - G0_MASK_HINT: disabled
      - USE_IO_VOLTAGE_ON_CORE_TO_IO_NET: disabled
      - USE_SD_VOLTAGE_ON_CORE_TO_IO_NET: enabled
      - SKIP_CELL_BOUNDARY: disabled
      - LUP_FILTER: disabled
      - DEFINE_IOPAD_BY_IODMY: enabled
      - ALL_AREA_IO: enabled
      - DISCONNECT_ALL_RESISTOR: disabled
      - CONNECT_ALL_RESISTOR: disabled
      - DEFINE_PAD_BY_TEXT: enabled
      - CHECK_FLOATING_GATE_BY_TEXT: disabled
      - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT: enabled
      - GUIDELINE_ESD_CDM7A: disabled
      - GUIDELINE_ESD_CDM9A: disabled
      - IP_LEVEL_LUP_CHECK: enabled
      - LUP_MASK_HINT: disabled
      - LUP_SANITY_CHECK: enabled
      - ESDLU_IP_TIGHTEN_DENSITY: enabled
      - BOOST_VT_OP: disabled
      - NO_INDICATOR_OF_OFFGRID_DIRECTIONAL: disabled
      - KOZ_High_subst_layer: disabled
      - SHDMIM_KOZ_AP_SPACE_5um: disabled
      - SHDMIM_KOZ_AP_SPACE_5um_IP: disabled
      - FHDMIM_KOZ_AP_SPACE_5um: disabled
      - FHDMIM_KOZ_AP_SPACE_5um_IP: disabled
      - Multi_VOLTAGE_BIN_WITHIN_CHIP: enabled
      - SINGLE_VOLTAGE_BIN_WITHIN_CHIP: disabled
      - SINGLE_VOLTAGE_BIN_0D96: enabled
      - SINGLE_VOLTAGE_BIN_1D32: disabled
      - SINGLE_VOLTAGE_BIN_1D65: disabled
      - USER_DEFINED_DELTA_VOLTAGE: disabled
      - Flip_Chip: enabled
      - Flip_Chip_SUB_wi_presolder: enabled
      - Flip_Chip_Thin_Die: enabled
      - COD_RULE_CHECK: enabled
      - COD_MASK_HINT: disabled
      - COD_RULE_CHECK_ONLY: disabled
      - FRONT_END: enabled
      - BACK_END: enabled
      - prBoundary_GRID: enabled
      - DVIAxR3_For_NonFlipChip: enabled
      - GUIDELINE_ESD: enabled
      - GUIDELINE_ANALOG: disabled
      - G0_RULE_CHECK: enabled
      - G0_RULE_CHECK_ONLY: disabled
      - VOLTAGE_RULE_CHECK: enabled
      - VOLTAGE_RULE_CHECK_ONLY: disabled
      - ESD_LUP_RULE_CHECK: enabled
      - ESD_LUP_RULE_CHECK_ONLY: disabled
      - DENSITY_RULE_CHECK_ONLY: disabled
      - SRAM_SANITY_DRC: enabled
      - SRAM_SANITY_DRC_ONLY: disabled
      - UseprBoundary: enabled
      - ChipWindowUsed: disabled
      - DUMMY_PRE_CHECK: disabled
      - DUMMY_PRE_CHECK_TIGHTEN: disabled
      - IP_TIGHTEN_DENSITY: enabled
      - IP_TIGHTEN_BOUNDARY: enabled
      - DFM: disabled
      - DFM_ONLY: disabled
      - Recommended: disabled
      - Guideline: enabled
      - First_priority: enabled
      - Manufacturing_concern: enabled
      - Device_performance: enabled
      - DISABLE_CDN_DRC_MATCH_LOD: enabled
      - PAD_TEXT: ["bump", "rx_p", "rx_m", "tx_p", "tx_m", "tx_out_p", "tx_out_m"]
      - VDD_TEXT: ["vdd", "xcvr_avdd_h", "cmn_avdd_h", "avdd_h", "cmn_avdd", "avdd"]
      - VSS_TEXT: ["vss", "agnd", "gnd"]
      - PoP_PAD_TEXT: "pop?"
      - IP_PIN_TEXT: "?"
      - ULTRA_LOW_NOISE_PAD_TEXT: "_null_text_name_"
      - LOW_NOISE_PAD_TEXT: "_null_text_name1_"
      - MED_LOW_NOISE_PAD_TEXT: "_null_text_name2_"
      - MED_NOISE_PAD_TEXT: "_null_text_name3_"
      - HIGH_NOISE_PAD_TEXT: "_null_text_name4_"
      - DUMMY_PAD_TEXT: "_null_text_name5_"
      - WAIVE_ESD_R_1_PAD_TEXT: "_null_text_name9_"
      - D2D_INT_CDM05V_PAD_TEXT: "_null_text_name8_1_"
      - D2D_INT_CDM10V_PAD_TEXT: "_null_text_name8_2_"
      - D2D_INT_CDM30V_PAD_TEXT: "_null_text_name8_3_"
      - D2D_INT_CDM50V_PAD_TEXT: "_null_text_name8_4_"
      - xLB: 0.0
      - yLB: 0.0
      - xRT: 1000.0
      - yRT: 1000.0
      - ScribeLineX: 180.0
      - ScribeLineY: 180.0
      - CellsForRRuleRecommended: "*"
      - CellsForRRuleAnalog: "*"
      - CellsForRRuleGuideline: "*"
      - ExclCellsForRRuleRecommended: " "
      - ExclCellsForRRuleAnalog: " "
      - ExclCellsForRRuleGuideline: " "
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
  ❌ DO NOT use paths: "innovus/221/22.11-s119_1"
  ❌ DO NOT use filenames: "libtech.lef"
- If description contains "filename"/"name": Use COMPLETE FILENAMES (e.g., "design.v")
- If description contains "status": Use STATUS VALUES (e.g., "Loaded", "Skipped")

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: Switch/variable setting matched and validated against CTA requirement

Log format (CheckList.rpt):
INFO01:
  - CHECK_LOW_DENSITY
  - CHECK_HIGH_DENSITY
  - IP_TIGHTEN_DENSITY

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: CHECK_LOW_DENSITY. In line 23, do_cmd_3star_DRC_sourceme: Switch/variable setting matched and validated against CTA requirement (enabled)
2: Info: CHECK_HIGH_DENSITY. In line 24, do_cmd_3star_DRC_sourceme: Switch/variable setting matched and validated against CTA requirement (enabled)
3: Info: IP_TIGHTEN_DENSITY. In line 156, do_cmd_3star_DRC_sourceme: Switch/variable setting matched and validated against CTA requirement (enabled)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-03:
  description: "Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA."
  requirements:
    value: 0
    pattern_items:
      - DEBUG_VOLTAGE_RULE: disabled
      - FULL_CHIP: disabled
      - CHECK_LOW_DENSITY: enabled
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: DRC rule deck CTA validation is informational only for this custom IP"
      - "Note: Switch mismatches are expected for design-specific optimizations and do not require fixes"
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
  - "Explanation: DRC rule deck CTA validation is informational only for this custom IP"
  - "Note: Switch mismatches are expected for design-specific optimizations and do not require fixes"
INFO02:
  - FULL_CHIP

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: DRC rule deck CTA validation is informational only for this custom IP. [WAIVED_INFO]
2: Info: FULL_CHIP. In line 18, do_cmd_3star_DRC_sourceme: Switch/variable setting does not match CTA requirement - justification required in comments (Expected: disabled, Found: enabled) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-03:
  description: "Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA."
  requirements:
    value: 111
    pattern_items:
      - DEBUG_VOLTAGE_RULE: disabled
      - DEBUG_VOLTAGE_RULE_WITH_METAL_CONNECTION: disabled
      - FULL_CHIP: disabled
      - WITH_SEALRING: disabled
      - CHECK_LOW_DENSITY: enabled
      - CHECK_HIGH_DENSITY: enabled
      - PT_CHECK: enabled
      - WITH_POLYIMIDE: enabled
      - WITH_APRDL: enabled
      - N4P_DTCO: disabled
      - SNAPPING_TOLERANCE: enabled
      - MASK_reduction: enabled
      - Lid: disabled
      - Ring: disabled
      - CoWoS_S: disabled
      - Check_Dummy_Under_INDDMY: enabled
      - SHDMIM: enabled
      - FHDMIM: disabled
      - G0_MASK_HINT: disabled
      - USE_IO_VOLTAGE_ON_CORE_TO_IO_NET: disabled
      - USE_SD_VOLTAGE_ON_CORE_TO_IO_NET: enabled
      - SKIP_CELL_BOUNDARY: disabled
      - LUP_FILTER: disabled
      - DEFINE_IOPAD_BY_IODMY: enabled
      - ALL_AREA_IO: enabled
      - DISCONNECT_ALL_RESISTOR: disabled
      - CONNECT_ALL_RESISTOR: disabled
      - DEFINE_PAD_BY_TEXT: enabled
      - CHECK_FLOATING_GATE_BY_TEXT: disabled
      - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT: enabled
      - GUIDELINE_ESD_CDM7A: disabled
      - GUIDELINE_ESD_CDM9A: disabled
      - IP_LEVEL_LUP_CHECK: enabled
      - LUP_MASK_HINT: disabled
      - LUP_SANITY_CHECK: enabled
      - ESDLU_IP_TIGHTEN_DENSITY: enabled
      - BOOST_VT_OP: disabled
      - NO_INDICATOR_OF_OFFGRID_DIRECTIONAL: disabled
      - KOZ_High_subst_layer: disabled
      - SHDMIM_KOZ_AP_SPACE_5um: disabled
      - SHDMIM_KOZ_AP_SPACE_5um_IP: disabled
      - FHDMIM_KOZ_AP_SPACE_5um: disabled
      - FHDMIM_KOZ_AP_SPACE_5um_IP: disabled
      - Multi_VOLTAGE_BIN_WITHIN_CHIP: enabled
      - SINGLE_VOLTAGE_BIN_WITHIN_CHIP: disabled
      - SINGLE_VOLTAGE_BIN_0D96: enabled
      - SINGLE_VOLTAGE_BIN_1D32: disabled
      - SINGLE_VOLTAGE_BIN_1D65: disabled
      - USER_DEFINED_DELTA_VOLTAGE: disabled
      - Flip_Chip: enabled
      - Flip_Chip_SUB_wi_presolder: enabled
      - Flip_Chip_Thin_Die: enabled
      - COD_RULE_CHECK: enabled
      - COD_MASK_HINT: disabled
      - COD_RULE_CHECK_ONLY: disabled
      - FRONT_END: enabled
      - BACK_END: enabled
      - prBoundary_GRID: enabled
      - DVIAxR3_For_NonFlipChip: enabled
      - GUIDELINE_ESD: enabled
      - GUIDELINE_ANALOG: disabled
      - G0_RULE_CHECK: enabled
      - G0_RULE_CHECK_ONLY: disabled
      - VOLTAGE_RULE_CHECK: enabled
      - VOLTAGE_RULE_CHECK_ONLY: disabled
      - ESD_LUP_RULE_CHECK: enabled
      - ESD_LUP_RULE_CHECK_ONLY: disabled
      - DENSITY_RULE_CHECK_ONLY: disabled
      - SRAM_SANITY_DRC: enabled
      - SRAM_SANITY_DRC_ONLY: disabled
      - UseprBoundary: enabled
      - ChipWindowUsed: disabled
      - DUMMY_PRE_CHECK: disabled
      - DUMMY_PRE_CHECK_TIGHTEN: disabled
      - IP_TIGHTEN_DENSITY: enabled
      - IP_TIGHTEN_BOUNDARY: enabled
      - DFM: disabled
      - DFM_ONLY: disabled
      - Recommended: disabled
      - Guideline: enabled
      - First_priority: enabled
      - Manufacturing_concern: enabled
      - Device_performance: enabled
      - DISABLE_CDN_DRC_MATCH_LOD: enabled
      - PAD_TEXT: ["bump", "rx_p", "rx_m", "tx_p", "tx_m", "tx_out_p", "tx_out_m"]
      - VDD_TEXT: ["vdd", "xcvr_avdd_h", "cmn_avdd_h", "avdd_h", "cmn_avdd", "avdd"]
      - VSS_TEXT: ["vss", "agnd", "gnd"]
      - PoP_PAD_TEXT: "pop?"
      - IP_PIN_TEXT: "?"
      - ULTRA_LOW_NOISE_PAD_TEXT: "_null_text_name_"
      - LOW_NOISE_PAD_TEXT: "_null_text_name1_"
      - MED_LOW_NOISE_PAD_TEXT: "_null_text_name2_"
      - MED_NOISE_PAD_TEXT: "_null_text_name3_"
      - HIGH_NOISE_PAD_TEXT: "_null_text_name4_"
      - DUMMY_PAD_TEXT: "_null_text_name5_"
      - WAIVE_ESD_R_1_PAD_TEXT: "_null_text_name9_"
      - D2D_INT_CDM05V_PAD_TEXT: "_null_text_name8_1_"
      - D2D_INT_CDM10V_PAD_TEXT: "_null_text_name8_2_"
      - D2D_INT_CDM30V_PAD_TEXT: "_null_text_name8_3_"
      - D2D_INT_CDM50V_PAD_TEXT: "_null_text_name8_4_"
      - xLB: 0.0
      - yLB: 0.0
      - xRT: 1000.0
      - yRT: 1000.0
      - ScribeLineX: 180.0
      - ScribeLineY: 180.0
      - CellsForRRuleRecommended: "*"
      - CellsForRRuleAnalog: "*"
      - CellsForRRuleGuideline: "*"
      - ExclCellsForRRuleRecommended: " "
      - ExclCellsForRRuleAnalog: " "
      - ExclCellsForRRuleGuideline: " "
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "FULL_CHIP"
        reason: "Waived - IP-level design does not require full chip mode per design team approval"
      - name: "DEBUG_VOLTAGE_RULE"
        reason: "Waived - voltage debugging disabled for production release per foundry recommendation"
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

Log format (CheckList.rpt):
INFO01:
  - FULL_CHIP
WARN01:
  - DEBUG_VOLTAGE_RULE

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: FULL_CHIP. In line 18, do_cmd_3star_DRC_sourceme: DRC rule deck setting mismatch waived per design team approval: Waived - IP-level design does not require full chip mode per design team approval [WAIVER]
Warn Occurrence: 1
1: Warn: DEBUG_VOLTAGE_RULE. In line 0, N/A: Waiver entry not matched - no corresponding setting mismatch found in input files: Waived - voltage debugging disabled for production release per foundry recommendation [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-03:
  description: "Confirm the DRC rule deck setting is correct. Make sure the switch settings match with Foundry CTA (/local/method/CTAF/<process>/production in chamber). Please add justification in Comment if you changed some switching setting in CTA."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "FULL_CHIP"
        reason: "Waived - IP-level design does not require full chip mode per design team approval"
      - name: "DEBUG_VOLTAGE_RULE"
        reason: "Waived - voltage debugging disabled for production release per foundry recommendation"
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

Log format (CheckList.rpt):
INFO01:
  - FULL_CHIP
WARN01:
  - DEBUG_VOLTAGE_RULE

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: FULL_CHIP. In line 18, do_cmd_3star_DRC_sourceme: DRC rule deck setting mismatch waived per design team approval: Waived - IP-level design does not require full chip mode per design team approval [WAIVER]
Warn Occurrence: 1
1: Warn: DEBUG_VOLTAGE_RULE. In line 0, N/A: Waiver entry not matched - no corresponding setting mismatch found in input files: Waived - voltage debugging disabled for production release per foundry recommendation [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-03 --force

# Run individual tests
python IMP-12-0-0-03.py
```

---

## Notes

**Implementation Notes:**
- The checker must handle both Pegasus PVL log format and Calibre DRC sourceme script format
- Switch names are case-sensitive and must match exactly
- Variable values support both quoted and unquoted formats
- For list-type variables (e.g., PAD_TEXT), the checker should compare each element in the list
- Numeric variables should support floating-point comparison with tolerance
- Line numbers and file paths are tracked for all settings to enable traceability

**Known Limitations:**
- Conditional #DEFINE statements (e.g., "#DEFINE SWITCH if condition") are not fully supported
- Multi-line variable definitions may require special handling
- Comments within variable values may cause parsing issues

**Edge Cases:**
- Empty or missing input files should be reported as configuration errors
- Duplicate switch definitions (last occurrence takes precedence)
- Variables with special characters in values require proper escaping
- CTA reference file path may vary by process node - checker should handle missing CTA gracefully