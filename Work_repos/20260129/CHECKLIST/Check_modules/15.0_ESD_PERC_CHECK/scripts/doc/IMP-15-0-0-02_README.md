# IMP-15-0-0-02: Confirm the PERC voltage setting is correct.(check the Note)

## Overview

**Check ID:** IMP-15-0-0-02  
**Description:** Confirm the PERC voltage setting is correct.(check the Note)  
**Category:** ESD/PERC Voltage Validation  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl`
- `${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/voltage.txt`

This checker validates PERC (Pad ESD and Rail Clamp) voltage settings by comparing TT corner DDRIO library voltage definitions against a voltage specification file. It specifically searches for TT corner DDRIO libraries (e.g., cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib) in setup_vars.tcl, extracts voltage_map information from all libraries in the TT corner, and validates these voltages against the voltage.txt specification file.

The checker performs voltage consistency validation:
1. **TT Corner DDRIO Library Detection**: Searches for library files containing "tt" and "ddrio" patterns (e.g., cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib) in setup_vars.tcl to identify TT corner DDRIO libraries
2. **Voltage Map Extraction**: Greps "voltage_map" from all TT corner library files to extract voltage definitions
3. **Voltage Specification Comparison**: Compares extracted voltages against voltage.txt to ensure consistency

**IMPORTANT: This checker focuses exclusively on TT corner libraries by searching for library filenames containing both "tt" and "ddrio" patterns!**

---

## Check Logic

### Input Parsing

**File 1: setup_vars.tcl**
Parses TCL library macro definitions to identify TT corner DDRIO libraries by examining the library file path.

**Key Patterns:**
```python
# Pattern 1: Library macro definition
lib_macro_pattern = r'set\s+LIB_MACRO\(([^,]+),([^)]+)\)\s+"([^"]+)"'
# Example: set LIB_MACRO(tt_0p75v_85c_typical,cdns_ddrio) "/projects/.../cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib"
# Extracts: corner_name="tt_0p75v_85c_typical", lib_type="cdns_ddrio", lib_path="/projects/.../cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib"

# Pattern 2: TT corner DDRIO library identification (applied to lib_path)
tt_ddrio_lib_pattern = r'.*tt.*ddrio.*\.lib'
# Example: "/projects/.../cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib" → matches (contains "tt" and "ddrio")
# Example: "/projects/.../cdns_ddr900_h_lpddr5x_ff_0p825v_0p550v_m40c.lib" → no match (contains "ff", not "tt")
# Example: "/projects/.../cdns_stdcell_tt_0p75v_85c.lib" → no match (contains "tt" but not "ddrio")

# Pattern 3: Voltage map extraction from library files
voltage_map_pattern = r'voltage_map\s*\(\s*"?([^"]+)"?\s*,\s*([0-9.]+)\s*\)'
# Example: voltage_map("VDD", 0.75) → extracts "VDD", "0.75"
# Example: voltage_map("VDDQ", 0.5) → extracts "VDDQ", "0.5"
```

**File 2: voltage.txt**
Parses VARIABLE declarations to extract signal names and voltage values.

**Key Patterns:**
```python
# Pattern 1: VARIABLE declaration
variable_pattern = r'^VARIABLE\s+"([^"]+)"\s+([0-9.]+)'
# Example: VARIABLE "VDD"	0.75
# Example: VARIABLE "VDDQ"	0.5

# Pattern 2: Voltage domain extraction
domain_pattern = r'^VARIABLE\s+"(V[DS][DS][DQ]?[QX]?[_A-Z0-9]*)"\s+([0-9.]+)'
# Example: VARIABLE "VDD"			0.75
# Example: VARIABLE "VDDQ"		0.5
```

### Detection Logic

**Step 1: Search TT corner DDRIO libraries in setup_vars.tcl**
1. Read setup_vars.tcl line-by-line
2. Match `set LIB_MACRO(...)` pattern
3. Extract corner_name, lib_type, lib_path
4. Filter for TT corner DDRIO libraries: lib_path contains both "tt" and "ddrio"
   - Example match: "/projects/.../cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib"
   - Example reject: "/projects/.../cdns_ddr900_h_lpddr5x_ff_0p825v_0p550v_m40c.lib" (FF corner)
   - Example reject: "/projects/.../cdns_stdcell_tt_0p75v_85c.lib" (not DDRIO)
5. Store matching TT corner DDRIO library paths

**Step 2: Extract voltage_map from TT corner libraries**
1. For each identified TT corner DDRIO library file:
   - Open the library file (.lib)
   - Grep for "voltage_map" entries
   - Parse voltage_map(domain, voltage) format
   - Extract voltage domain name and voltage value
   - Store all voltage_map entries from TT corner libraries

**Step 3: Parse voltage.txt specification**
1. Read voltage.txt line-by-line
2. Match `VARIABLE "name" value` pattern
3. Extract variable_name and voltage_value
4. Build expected voltage specification map

**Step 4: Compare TT corner voltages against specification**
1. For each voltage_map entry from TT corner libraries:
   - Look up corresponding entry in voltage.txt
   - Compare voltage values
   - If mismatch detected: record as violation
   - If match found: record as compliant
2. Check for missing voltage definitions (in spec but not in TT corner libs)
3. Check for extra voltage definitions (in TT corner libs but not in spec)

**Step 5: Aggregate Results**
1. Generate INFO01 for compliant items (voltage matches between TT corner libs and spec)
2. Generate ERROR01 for violations (voltage mismatches or missing/extra definitions)
3. Return PASS if no violations, FAIL otherwise

**Edge Cases Handled:**
- Multiple TT corner variants (tt_0p75v_85c, tt_0p80v_125c, etc.)
- Multiple DDRIO library types in TT corner
- Missing voltage_map entries in library files
- Voltage format variations (0.75 vs 0.750)
- Comments or continuation lines in library files
- Missing voltage.txt entries
- Non-numeric voltage values

**CRITICAL: Only TT corner DDRIO libraries (identified by lib_path containing both "tt" and "ddrio") are validated. Other corners (FF, SS, etc.) are ignored!**

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

**Rationale:** This checker validates voltage settings for TT corner DDRIO libraries by checking the STATUS (voltage correctness) of voltage_map entries against voltage.txt specifications. Only TT corner DDRIO items with voltage mismatches are reported as violations. Items not in the validation scope (non-TT corners, non-DDRIO libraries) are not reported. This is a status validation check for TT corner only, not an existence check.

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
item_desc = "Confirm the PERC voltage setting is correct in TT corner DDRIO libraries.(check the Note)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All TT corner DDRIO library voltage_map entries found and validated against voltage.txt"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All TT corner DDRIO library voltage_map entries matched voltage.txt specifications and validated"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All voltage_map entries from TT corner DDRIO libraries found to match voltage.txt specifications"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All voltage_map entries from TT corner DDRIO libraries matched voltage.txt specifications and validated successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "TT corner DDRIO library voltage mismatches found between voltage_map and voltage.txt"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "TT corner DDRIO library voltage settings not satisfied - mismatches detected between voltage_map and voltage.txt"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Voltage mismatches found in TT corner: voltage_map entries from DDRIO libraries do not match voltage.txt specifications"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "TT corner voltage specifications not satisfied: voltage_map mismatches or missing/extra voltage definitions detected in DDRIO libraries"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "TT corner DDRIO voltage violations waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "TT corner DDRIO voltage mismatch waived - approved exception per design team review"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused TT corner DDRIO voltage waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding TT corner voltage violation found in current design"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[lib_filename] voltage_map([domain])=[voltage]v - MATCHES voltage.txt"
  Example: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD)=0.75v - MATCHES voltage.txt"
  Example: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ)=0.5v - MATCHES voltage.txt"
  Example: "cdns_ddr900_h_lpddr5x_tt_0p800v_0p500v_125c.lib voltage_map(VDDQX)=1.05v - MATCHES voltage.txt"

ERROR01 (Violation/Fail items):
  Format: "[lib_filename] voltage_map([domain]): VOLTAGE MISMATCH - lib=[lib_voltage]v spec=[spec_voltage]v"
  Example: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v"
  Example: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt"
  Example: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib: EXTRA voltage_map(VDDX)=1.2v not defined in voltage.txt"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-02:
  description: "Confirm the PERC voltage setting is correct.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/voltage.txt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.
**Searches for TT corner DDRIO libraries (lib_path containing both "tt" and "ddrio") only and validates voltage_map against voltage.txt.**

**Sample Output (PASS):**
```
Status: PASS
Reason: All voltage_map entries from TT corner DDRIO libraries found to match voltage.txt specifications
INFO01:
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD)=0.75v - MATCHES voltage.txt
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ)=0.5v - MATCHES voltage.txt
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQX)=1.05v - MATCHES voltage.txt
  - cdns_ddr900_h_lpddr5x_tt_0p800v_0p500v_125c.lib voltage_map(VDD)=0.80v - MATCHES voltage.txt
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Voltage mismatches found in TT corner: voltage_map entries from DDRIO libraries do not match voltage.txt specifications
ERROR01:
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib: EXTRA voltage_map(VDDX)=1.2v not defined in voltage.txt
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-02:
  description: "Confirm the PERC voltage setting is correct.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/voltage.txt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: TT corner DDRIO voltage validation is informational only during early design phase"
      - "Note: Voltage mismatches in TT corner are expected in pre-silicon validation and will be corrected before tapeout"
      - "Rationale: Design team is aware of TT corner voltage discrepancies and tracking separately"
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
  - "Explanation: TT corner DDRIO voltage validation is informational only during early design phase"
  - "Note: Voltage mismatches in TT corner are expected in pre-silicon validation and will be corrected before tapeout"
  - "Rationale: Design team is aware of TT corner voltage discrepancies and tracking separately"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v [WAIVED_AS_INFO]
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt [WAIVED_AS_INFO]
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib: EXTRA voltage_map(VDDX)=1.2v not defined in voltage.txt [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-02:
  description: "Confirm the PERC voltage setting is correct.(check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD)"
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ)"
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQX)"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/voltage.txt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)
**Only validates TT corner DDRIO libraries (lib_path containing both "tt" and "ddrio") specified in pattern_items.**

**Sample Output (PASS):**
```
Status: PASS
Reason: All voltage_map entries from TT corner DDRIO libraries matched voltage.txt specifications and validated successfully
INFO01:
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD)=0.75v - MATCHES voltage.txt
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ)=0.5v - MATCHES voltage.txt
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQX)=1.05v - MATCHES voltage.txt
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-02:
  description: "Confirm the PERC voltage setting is correct.(check the Note)"
  requirements:
    value: 0
    pattern_items:
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD)"
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ)"
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQX)"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/voltage.txt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: TT corner DDRIO voltage pattern validation is informational during integration phase"
      - "Note: Pattern mismatches for TT corner DDRIO libraries are expected and tracked in design database"
      - "Rationale: TT corner voltage settings will be finalized after characterization completion"
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
  - "Explanation: TT corner DDRIO voltage pattern validation is informational during integration phase"
  - "Note: Pattern mismatches for TT corner DDRIO libraries are expected and tracked in design database"
  - "Rationale: TT corner voltage settings will be finalized after characterization completion"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v [WAIVED_AS_INFO]
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-02:
  description: "Confirm the PERC voltage setting is correct.(check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD)"
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ)"
      - "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQX)"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/voltage.txt"
  waivers:
    value: 2
    waive_items:
      - name: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v"
        reason: "Waived - TT corner library vendor confirmed 0.80v is correct characterization voltage per ECO-2024-156"
      - name: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt"
        reason: "Waived - VDDQ voltage_map intentionally omitted from voltage.txt for TT corner per design specification v2.3"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items against waive_items
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.
**Only validates TT corner DDRIO libraries (lib_path containing both "tt" and "ddrio").**

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v [WAIVER]
    Reason: Waived - TT corner library vendor confirmed 0.80v is correct characterization voltage per ECO-2024-156
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt [WAIVER]
    Reason: Waived - VDDQ voltage_map intentionally omitted from voltage.txt for TT corner per design specification v2.3
WARN01 (Unused Waivers):
  - (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-02:
  description: "Confirm the PERC voltage setting is correct.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/voltage.txt"
  waivers:
    value: 2
    waive_items:
      - name: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v"
        reason: "Waived - TT corner library vendor confirmed 0.80v is correct characterization voltage per ECO-2024-156"
      - name: "cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt"
        reason: "Waived - VDDQ voltage_map intentionally omitted from voltage.txt for TT corner per design specification v2.3"
```

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.
**Validates all TT corner DDRIO libraries (lib_path containing both "tt" and "ddrio") found in setup_vars.tcl.**

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDD): VOLTAGE MISMATCH - lib=0.80v spec=0.75v [WAIVER]
    Reason: Waived - TT corner library vendor confirmed 0.80v is correct characterization voltage per ECO-2024-156
  - cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib voltage_map(VDDQ): MISSING in voltage.txt [WAIVER]
    Reason: Waived - VDDQ voltage_map intentionally omitted from voltage.txt for TT corner per design specification v2.3
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 15.0_ESD_PERC_CHECK --checkers IMP-15-0-0-02 --force

# Run individual tests
python IMP-15-0-0-02.py
```

---

## Notes

**TT Corner Focus:**
- **CRITICAL: This checker ONLY validates TT corner DDRIO libraries!**
- TT corner DDRIO libraries are identified by searching for library file paths (lib_path) that contain BOTH "tt" and "ddrio" patterns
- Example match: `/projects/.../cdns_ddr900_h_lpddr5x_tt_0p750v_0p500v_85c.lib` (contains "tt" and "ddrio")
- Example reject: `/projects/.../cdns_ddr900_h_lpddr5x_ff_0p825v_0p550v_m40c.lib` (FF corner, not TT)
- Example reject: `/projects/.../cdns_stdcell_tt_0p75v_85c.lib` (TT corner but not DDRIO)
- Other process corners (FF, SS, FS, SF, etc.) are explicitly ignored
- All validation logic applies exclusively to TT corner DDRIO libraries

**Voltage Map Extraction:**
- The checker greps "voltage_map" from TT corner DDRIO library files
- Parses voltage_map(domain, voltage) format from .lib files
- Extracts all voltage domains defined in TT corner libraries
- Compares against voltage.txt specification file

**Voltage Comparison Logic:**
- Validates voltage_map entries from TT corner libs against voltage.txt
- Detects mismatches: lib voltage ≠ spec voltage
- Detects missing entries: voltage_map in lib but not in voltage.txt
- Detects extra entries: voltage in voltage.txt but no voltage_map in lib

**Known Limitations:**
- Only TT corner DDRIO libraries (identified by lib_path pattern) are validated (by design)
- Assumes voltage_map format in library files follows standard syntax
- Voltage.txt must contain all expected voltage domains for TT corner
- Comments in library files may interfere with grep if not properly formatted
- Multiple TT corner variants are all validated (tt_0p75v, tt_0p80v, etc.)

**Reference Note:**
The checker implements validation rules based on TT corner PERC voltage specifications. Ensure the "Note" referenced in the check description is available to design team for TT corner voltage requirement details.