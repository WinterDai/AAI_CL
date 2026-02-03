# IMP-3-0-0-05: List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)

## Overview

**Check ID:** IMP-3-0-0-05  
**Description:** List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)  
**Category:** Tool Version Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl`

This checker extracts and reports the Pegasus physical signoff tool version from the TCL setup configuration file. It parses MODULE_CMD variable definitions to identify the Pegasus version string in the format `pegasus/XXX/YY.YY.YYY` (e.g., `pegasus/232/23.25.000`). The checker searches multiple MODULE_CMD contexts (PVS, PEGASUS, MVS) where Pegasus may be loaded and validates version string consistency across all references.

---

## Check Logic

### Input Parsing
The checker parses the TCL setup file (`setup_vars.tcl`) line-by-line to extract tool version information from MODULE_CMD variable definitions. It focuses on identifying Pegasus version strings within `module load` commands.

**Key Patterns:**
```python
# Pattern 1: PVS MODULE_CMD with Pegasus version
pattern1 = r'set\s+PVS\(MODULE_CMD\)\s+"[^"]*module\s+load\s+pegasus/(\d+)/(\S+)'
# Example: "set PVS(MODULE_CMD)                                                        "module unload pegasus pvs; module load pegasus/232/23.25.000""

# Pattern 2: PEGASUS MODULE_CMD with version
pattern2 = r'set\s+PEGASUS\(MODULE_CMD\)\s+"[^"]*module\s+load\s+pegasus/(\d+)/(\S+)'
# Example: "set PEGASUS(MODULE_CMD)                                                    "module unload pegasus pvs; module load pegasus/232/23.25.000""

# Pattern 3: MVS MODULE_CMD with Pegasus version
pattern3 = r'set\s+MVS\(MODULE_CMD\)\s+"[^"]*module\s+load\s+pegasus/(\d+)/(\S+)'
# Example: "set MVS(MODULE_CMD)                                                        "module unload pegasus mvs; module load pegasus/232/23.25.000""

# Pattern 4: Generic module load parser (within MODULE_CMD strings)
pattern4 = r'module\s+load\s+pegasus/(\d+)/(\S+)'
# Example: "module load pegasus/232/23.25.000"
```

### Detection Logic
1. **File Reading**: Open and read `setup_vars.tcl` line-by-line
2. **MODULE_CMD Extraction**: Identify lines containing `set <TOOL>(MODULE_CMD)` definitions
3. **Version Parsing**: Extract quoted string values and parse `module load` commands within them
4. **Pegasus Filtering**: Filter for tool name `pegasus` specifically
5. **Version Extraction**: Extract version path in format `pegasus/XXX/YY.YY.YYY`
   - Group 1: Major version number (e.g., `232`)
   - Group 2: Full version string (e.g., `23.25.000`)
   - Complete path: `pegasus/232/23.25.000`
6. **Consistency Validation**: Check if Pegasus appears in multiple MODULE_CMD contexts (PVS, PEGASUS, MVS) and verify version consistency
7. **Result Classification**:
   - **PASS**: Pegasus version found and extracted successfully
   - **FAIL**: Pegasus version not found or parsing error
8. **Edge Cases Handled**:
   - Multiple MODULE_CMD definitions for same tool (use last occurrence)
   - Pegasus referenced in multiple tool contexts (validate consistency)
   - Missing MODULE_CMD for PEGASUS (report not found)
   - Malformed version strings (report parsing error)
   - Comments or disabled lines (ignore lines starting with #)
   - Empty or missing file (report file not found)

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
item_desc = "List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Pegasus tool version found in setup configuration"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Pegasus version pattern matched in MODULE_CMD"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Pegasus tool version successfully extracted from setup_vars.tcl"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Pegasus version pattern matched and validated in MODULE_CMD definitions"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Pegasus tool version not found in setup configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Pegasus version pattern not satisfied in MODULE_CMD"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Pegasus MODULE_CMD definition not found or version string missing in setup_vars.tcl"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required Pegasus version pattern not satisfied or missing from MODULE_CMD definitions"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Pegasus version check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Pegasus version requirement waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused Pegasus version waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding Pegasus version issue found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "pegasus/XXX/YY.YY.YYY"
  Example: "pegasus/232/23.25.000"

ERROR01 (Violation/Fail items):
  Format: "ERROR: [error_description]"
  Example: "ERROR: Pegasus MODULE_CMD not found in setup_vars.tcl"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-05:
  description: "List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"
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
Reason: Pegasus tool version successfully extracted from setup_vars.tcl
INFO01:
  - pegasus/232/23.25.000
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Pegasus MODULE_CMD definition not found or version string missing in setup_vars.tcl
ERROR01:
  - ERROR: Pegasus MODULE_CMD not found in setup_vars.tcl
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-05:
  description: "List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - Pegasus version tracking for documentation purposes"
      - "Note: Missing Pegasus version is acceptable for designs not requiring physical signoff"
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
  - Explanation: This check is informational only - Pegasus version tracking for documentation purposes
  - Note: Missing Pegasus version is acceptable for designs not requiring physical signoff
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: Pegasus MODULE_CMD not found in setup_vars.tcl [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-05:
  description: "List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"
  requirements:
    value: 2
    pattern_items:
      - "pegasus/232/23.25.000"
      - "pegasus/231/23.10.000"
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
Reason: Pegasus version pattern matched and validated in MODULE_CMD definitions
INFO01:
  - pegasus/232/23.25.000
  - pegasus/231/23.10.000
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-05:
  description: "List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"
  requirements:
    value: 2
    pattern_items:
      - "pegasus/232/23.25.000"
      - "pegasus/231/23.10.000"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - Pegasus version verification for audit trail"
      - "Note: Version mismatches are expected during tool migration and do not require immediate fixes"
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
  - Explanation: This check is informational only - Pegasus version verification for audit trail
  - Note: Version mismatches are expected during tool migration and do not require immediate fixes
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - ERROR: Expected version 'pegasus/232/23.25.000' not found, actual version 'pegasus/232/23.20.000' [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-05:
  description: "List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"
  requirements:
    value: 2
    pattern_items:
      - "pegasus/232/23.25.000"
      - "pegasus/231/23.10.000"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 2
    waive_items:
      - name: "pegasus/232/23.20.000"
        reason: "Waived - intermediate version approved for this design phase"
      - name: "pegasus/231/23.05.000"
        reason: "Waived - legacy version used for compatibility with existing signoff flow"
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
  - pegasus/232/23.20.000 [WAIVER]
  - pegasus/231/23.05.000 [WAIVER]
WARN01 (Unused Waivers):
  - pegasus/230/23.00.000: Waiver not matched - no corresponding Pegasus version issue found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-05:
  description: "List Pegasus physical signoff tool version (eg. pegasus/232/23.25.000)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 2
    waive_items:
      - name: "pegasus/232/23.20.000"
        reason: "Waived - intermediate version approved for this design phase"
      - name: "pegasus/231/23.05.000"
        reason: "Waived - legacy version used for compatibility with existing signoff flow"
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
  - pegasus/232/23.20.000 [WAIVER]
  - pegasus/231/23.05.000 [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 3.0_TOOL_VERSION --checkers IMP-3-0-0-05 --force

# Run individual tests
python IMP-3-0-0-05.py
```

---

## Notes

- **Multi-Context Search**: The checker searches for Pegasus version in multiple MODULE_CMD contexts (PVS, PEGASUS, MVS) to ensure comprehensive detection
- **Version Consistency**: If Pegasus appears in multiple MODULE_CMD variables, the checker validates that all references use the same version
- **Version Format**: Expected format is `pegasus/XXX/YY.YY.YYY` where XXX is the major version (e.g., 232) and YY.YY.YYY is the full version (e.g., 23.25.000)
- **TCL Parsing**: The checker handles TCL-specific syntax including quoted strings, line continuations (backslash), and comments (# prefix)
- **Error Handling**: Gracefully handles missing files, malformed version strings, and empty MODULE_CMD definitions
- **Use Case**: Primarily used for tool version tracking, audit trails, and ensuring consistent tool versions across design flows