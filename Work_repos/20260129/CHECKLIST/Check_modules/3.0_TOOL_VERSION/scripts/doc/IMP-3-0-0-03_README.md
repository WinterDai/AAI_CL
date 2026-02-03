# IMP-3-0-0-03: List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)

## Overview

**Check ID:** IMP-3-0-0-03  
**Description:** List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)  
**Category:** Tool Version Verification  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl

This checker extracts and reports the Tempus timing signoff tool version from the TCL setup configuration file. It searches for the `TEMPUS(MODULE_CMD)` variable which contains the module load command with the version string in the format `ssv/{major}/{version}` (e.g., ssv/202/20.20.000 or ssv/231/23.12-s092_1). The checker validates that the version information is present and properly formatted in the setup file.

---

## Check Logic

### Input Parsing

The checker parses the TCL configuration file `setup_vars.tcl` to locate the TEMPUS module version specification. It performs line-by-line scanning to find the `set TEMPUS(MODULE_CMD)` variable assignment and extracts the version string from the module load command.

**Key Patterns:**
```python
# Pattern 1: Primary extraction - TEMPUS MODULE_CMD with version string
pattern1 = r'set\s+TEMPUS\(MODULE_CMD\)\s+"[^"]*module\s+load\s+ssv/(\d+)/(\S+)"'
# Example: "set TEMPUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/202/20.20.000""

# Pattern 2: Simplified version path extraction
pattern2 = r'set\s+TEMPUS\(MODULE_CMD\)\s+".*?ssv/(\d+/[\d\.\-\w]+)"'
# Example: "set TEMPUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/231/23.12-s092_1""

# Pattern 3: Variable existence check
pattern3 = r'set\s+TEMPUS\(MODULE_CMD\)'
# Example: "set TEMPUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/202/20.20.000""

# Pattern 4: Full command extraction for validation
pattern4 = r'set\s+TEMPUS\(MODULE_CMD\)\s+"([^"]+)"'
# Example: "set TEMPUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/202/20.20.000""

# Pattern 5: Fallback - any ssv version string in file
pattern5 = r'ssv/(\d+)/(\S+)'
# Example: "module load ssv/202/20.20.000"
```

### Detection Logic

1. **File Reading**: Open and read the setup_vars.tcl file line by line
2. **Variable Search**: Scan each line for the `set TEMPUS(MODULE_CMD)` pattern
3. **Version Extraction**: 
   - Once the TEMPUS variable is found, extract the full quoted command string
   - Search within the command for the `module load ssv/` pattern
   - Extract the version string following `ssv/` in the format `{major}/{version}`
4. **Validation**:
   - Verify the TEMPUS variable exists in the file
   - Confirm the command contains a valid `module load ssv/` statement
   - Validate the version string format (major/version pattern)
5. **Output Formatting**: Format the extracted version as `ssv/{major}/{version}` for INFO01 display
6. **Error Handling**:
   - If TEMPUS variable not found → ERROR01: "TEMPUS(MODULE_CMD) variable not found"
   - If variable exists but no ssv version → ERROR01: "Tempus version string not found"
   - If version format is malformed → ERROR01: "Invalid version format"
7. **Termination**: Stop after first valid match or complete full file scan if not found

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
item_desc = "List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Tempus tool version found in setup configuration"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Tempus version pattern matched in setup configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Tempus tool version successfully extracted from TEMPUS(MODULE_CMD) in setup_vars.tcl"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Tempus version pattern matched and validated in setup configuration"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Tempus tool version not found in setup configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Tempus version pattern not satisfied in setup configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "TEMPUS(MODULE_CMD) variable not found or version string missing in setup_vars.tcl"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required Tempus version pattern not satisfied or missing in setup configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Tempus version check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Tempus version requirement waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused Tempus version waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding version issue found in setup_vars.tcl"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "ssv/{major}/{version}"
  Example: "ssv/202/20.20.000"
  Example: "ssv/231/23.12-s092_1"

ERROR01 (Violation/Fail items):
  Format: "ERROR: {error_description}"
  Example: "ERROR: TEMPUS(MODULE_CMD) variable not found in setup_vars.tcl"
  Example: "ERROR: Tempus version string not found in TEMPUS(MODULE_CMD)"
  Example: "ERROR: Invalid Tempus version format in setup_vars.tcl"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-03:
  description: "List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
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
Reason: Tempus tool version successfully extracted from TEMPUS(MODULE_CMD) in setup_vars.tcl
INFO01:
  - ssv/202/20.20.000
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: TEMPUS(MODULE_CMD) variable not found or version string missing in setup_vars.tcl
ERROR01:
  - ERROR: TEMPUS(MODULE_CMD) variable not found in setup_vars.tcl
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-03:
  description: "List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - Tempus version reporting does not block signoff"
      - "Note: Version mismatches or missing version strings are tracked but do not require immediate fixes"
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
  - "Explanation: This check is informational only - Tempus version reporting does not block signoff"
  - "Note: Version mismatches or missing version strings are tracked but do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: TEMPUS(MODULE_CMD) variable not found in setup_vars.tcl [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-03:
  description: "List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"
  requirements:
    value: 2
    pattern_items:
      - "ssv/202/20.20.000"
      - "ssv/231/23.12-s092_1"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
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
Reason: Tempus version pattern matched and validated in setup configuration
INFO01:
  - ssv/202/20.20.000
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-03:
  description: "List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"
  requirements:
    value: 2
    pattern_items:
      - "ssv/202/20.20.000"
      - "ssv/231/23.12-s092_1"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - version pattern matching does not block signoff"
      - "Note: Pattern mismatches are expected during tool version transitions and do not require fixes"
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
  - "Explanation: This check is informational only - version pattern matching does not block signoff"
  - "Note: Pattern mismatches are expected during tool version transitions and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - ERROR: Expected version 'ssv/231/23.12-s092_1' not found, actual version 'ssv/202/20.20.000' [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-03:
  description: "List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"
  requirements:
    value: 2
    pattern_items:
      - "ssv/202/20.20.000"
      - "ssv/231/23.12-s092_1"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 2
    waive_items:
      - name: "ssv/202/20.20.000"
        reason: "Waived - older Tempus version approved for this design due to tool stability requirements"
      - name: "ssv/231/23.15-s092_1"
        reason: "Waived - intermediate tool version used for debug, will be updated before tapeout"
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
  - ssv/202/20.20.000 [WAIVER]
WARN01 (Unused Waivers):
  - ssv/231/23.15-s092_1: Waiver not matched - no corresponding version issue found in setup_vars.tcl
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-03:
  description: "List Tempus timing signoff tool version (eg. ssv/231/23.12-s092_1)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 2
    waive_items:
      - name: "ssv/202/20.20.000"
        reason: "Waived - older Tempus version approved for this design due to tool stability requirements"
      - name: "ssv/231/23.15-s092_1"
        reason: "Waived - intermediate tool version used for debug, will be updated before tapeout"
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
  - ssv/202/20.20.000 [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 3.0_TOOL_VERSION --checkers IMP-3-0-0-03 --force

# Run individual tests
python IMP-3-0-0-03.py
```

---

## Notes

**Limitations:**
- The checker assumes the TEMPUS(MODULE_CMD) variable follows the standard format with `module load ssv/{major}/{version}`
- Multi-line TCL continuation (backslash) is supported but may require special handling
- If multiple TEMPUS variables exist in the file, only the first valid match is reported

**Known Issues:**
- Version format variations (e.g., ssv/231/23.10 vs ssv/231/23.10.000) are both accepted - any format after `ssv/` is captured until whitespace or quote
- If the file contains multiple module load commands on the same line, only the ssv version is extracted (other tools like quantus, innovus are ignored)

**Edge Cases Handled:**
- Empty or comment-only files → ERROR: "TEMPUS(MODULE_CMD) variable not found"
- TEMPUS variable exists but contains no ssv version → ERROR: "Tempus version string not found"
- Malformed version strings → ERROR: "Invalid version format"
- File not found or unreadable → ERROR with appropriate file access message