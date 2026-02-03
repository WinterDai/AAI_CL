# IMP-3-0-0-04: List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)

## Overview

**Check ID:** IMP-3-0-0-04  
**Description:** List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)  
**Category:** Tool Version Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl`

This checker extracts and reports the versions of QRC and VOLTUS tools configured in the TCL setup file. It parses `MODULE_CMD` variable assignments to identify tool versions from module load commands.

---

## Check Logic

### Input Parsing
The checker parses the TCL configuration file line-by-line to extract tool version information from `set TOOLNAME(MODULE_CMD)` statements. Each statement contains module load commands with version strings in the format `module_name/major_version/full_version`.

**Key Patterns:**
```python
# Pattern 1: QRC module command
pattern1 = r'set\s+QRC\(MODULE_CMD\)\s+".*module\s+load\s+(?:quantus|qrc)/(\d+)/(\S+)"'
# Example: "set QRC(MODULE_CMD)                                                        "module unload quantus ext; module load quantus/231/23.10.000""
# Example: "set QRC(MODULE_CMD)                                                        "module unload qrc ext; module load qrc/231/23.10.000""

# Pattern 2: VOLTUS module command
pattern2 = r'set\s+VOLTUS\(MODULE_CMD\)\s+".*module\s+load\s+(?:voltus|ssv)/(\d+)/(\S+)"'
# Example: "set VOLTUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/202/20.20.000""

# Pattern 3: Tool variable name extraction
pattern3 = r'set\s+(QRC|VOLTUS)\(MODULE_CMD\)'
# Example: "set VOLTUS(MODULE_CMD)"
# Example: "set QRC(MODULE_CMD)"
```

### Detection Logic
1. **Scan for MODULE_CMD variables**: Iterate through each line looking for `set QRC(MODULE_CMD)` and `set VOLTUS(MODULE_CMD)` patterns (both must be present)
2. **Extract tool name**: Capture the tool variable name (QRC or VOLTUS) from the set command
3. **Parse module load command**: Within the quoted string, extract the module load command using regex
4. **Extract version components**: Parse module name, major version, and full version string
5. **Handle special cases**:
   - QRC variable can use either 'quantus' or 'qrc' module - map correctly
   - VOLTUS can use either 'voltus' or 'ssv' module - map correctly
   - Multiple module commands in same line (semicolon separated) - parse only 'load' commands
6. **Format output**: Display as `tool_name/major_version/full_version` (e.g., `voltus/202/20.20.000`)
7. **Report findings**: All discovered tool versions are reported as INFO01 items

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
item_desc = "List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "QRC and VOLTUS tool versions found in setup configuration"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All required QRC and VOLTUS tool versions matched in configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "QRC and VOLTUS tool version information successfully extracted from setup_vars.tcl"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All required QRC and VOLTUS tool version patterns matched and validated in setup configuration"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "QRC and VOLTUS tool version information not found in setup configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Required QRC and VOLTUS tool version patterns not satisfied in configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "QRC(MODULE_CMD) and VOLTUS(MODULE_CMD) variables not found in setup_vars.tcl or file missing"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Expected QRC and VOLTUS tool version patterns not satisfied or missing from setup configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "QRC or VOLTUS tool version mismatches waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "QRC or VOLTUS tool version mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused QRC or VOLTUS tool version waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding QRC or VOLTUS tool version found in configuration"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "tool_name/major_version/full_version"
  Example: "voltus/202/20.20.000"
  Example: "qrc/231/23.10.000"

ERROR01 (Violation/Fail items):
  Format: "ERROR: [description of missing tool version]"
  Example: "ERROR: No VOLTUS MODULE_CMD found in setup_vars.tcl"
  Example: "ERROR: No QRC MODULE_CMD found in setup_vars.tcl"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-04:
  description: "List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
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
Reason: QRC and VOLTUS tool version information successfully extracted from setup_vars.tcl
INFO01:
  - voltus/202/20.20.000
  - qrc/231/23.10.000
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: QRC(MODULE_CMD) and VOLTUS(MODULE_CMD) variables not found in setup_vars.tcl or file missing
ERROR01:
  - ERROR: No QRC and VOLTUS tool version information found in setup configuration
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-04:
  description: "List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - QRC and VOLTUS tool versions are reported for tracking purposes"
      - "Note: Missing tool versions are acceptable during early development phases"
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
  - "Explanation: This check is informational only - QRC and VOLTUS tool versions are reported for tracking purposes"
  - "Note: Missing tool versions are acceptable during early development phases"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: No VOLTUS MODULE_CMD found in setup_vars.tcl [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-04:
  description: "List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: 2
    pattern_items:
      - "voltus/202/20.20.000"
      - "qrc/231/23.10.000"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All required QRC and VOLTUS tool version patterns matched and validated in setup configuration
INFO01:
  - voltus/202/20.20.000
  - qrc/231/23.10.000
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-04:
  description: "List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: 2
    pattern_items:
      - "voltus/202/20.20.000"
      - "qrc/231/23.10.000"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - QRC and VOLTUS tool version mismatches are acceptable during development"
      - "Note: Pattern mismatches are expected when using alternative tool versions approved by design team"
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
  - "Explanation: This check is informational only - QRC and VOLTUS tool version mismatches are acceptable during development"
  - "Note: Pattern mismatches are expected when using alternative tool versions approved by design team"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - voltus/231/23.12.000 (expected: voltus/202/20.20.000) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-04:
  description: "List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: 2
    pattern_items:
      - "voltus/202/20.20.000"
      - "qrc/231/23.10.000"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 2
    waive_items:
      - name: "voltus/231/23.12.000"
        reason: "Waived - newer VOLTUS version approved for this design per tool team recommendation"
      - name: "qrc/202/20.20.000"
        reason: "Waived - older QRC version required for compatibility with legacy extraction flow"
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
  - voltus/231/23.12.000 [WAIVER]
  - qrc/202/20.20.000 [WAIVER]
WARN01 (Unused Waivers):
  - voltus/202/20.20.000: Waiver not matched - no corresponding QRC or VOLTUS tool version found in configuration
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-04:
  description: "List Voltus power and EMIR signoff tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 2
    waive_items:
      - name: "voltus/231/23.12.000"
        reason: "Waived - newer VOLTUS version approved for this design per tool team recommendation"
      - name: "qrc/202/20.20.000"
        reason: "Waived - older QRC version required for compatibility with legacy extraction flow"
```

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
  - voltus/231/23.12.000 [WAIVER]
  - qrc/202/20.20.000 [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 3.0_TOOL_VERSION --checkers IMP-3-0-0-04 --force

# Run individual tests
python IMP-3-0-0-04.py
```

---

## Notes

**Special Handling:**
- QRC variable name can map to either 'quantus' or 'qrc' module - the checker handles both mappings correctly
- VOLTUS can use either 'voltus' or 'ssv' module - the checker handles both mappings correctly
- Module commands may contain multiple semicolon-separated commands (e.g., "module unload ssv; module load ssv/202/20.20.000") - only 'load' commands are parsed

**Limitations:**
- Only parses QRC(MODULE_CMD) and VOLTUS(MODULE_CMD) variables in the specified format
- Does not validate if tool versions are compatible with each other
- Does not check if versions meet minimum requirements (this is an informational check)

**Known Issues:**
- Version format variations beyond X.Y.Z or X.YY.ZZZ may not be parsed correctly