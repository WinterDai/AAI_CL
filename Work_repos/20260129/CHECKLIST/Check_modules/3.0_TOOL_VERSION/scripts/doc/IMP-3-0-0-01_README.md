# IMP-3-0-0-01: List Quantus RC extraction tool version (eg. quantus/231/23.11.000)

## Overview

**Check ID:** IMP-3-0-0-01  
**Description:** List Quantus RC extraction tool version (eg. quantus/231/23.11.000)  
**Category:** Tool Version Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl`

This checker extracts and reports the Quantus RC extraction tool version from the TCL setup configuration file. It searches for module load commands in both the INNOVUS and QRC sections to identify the version string in the format `quantus/XXX/YY.YY.YYY`. The checker validates that Quantus is properly configured for RC extraction by verifying the presence of version information in the setup file.

---

## Check Logic

### Input Parsing

The checker parses the TCL configuration file line-by-line to extract Quantus version information from module load commands.

**Key Patterns:**
```python
# Pattern 1: Quantus version in module load command (generic)
pattern1 = r'quantus/(\d+)/(\d+\.\d+\.\d+)'
# Example: "module load innovus/231/23.33-s082_1 quantus/231/23.10.000 pegasus/232/23.25.000"

# Pattern 2: INNOVUS section module command
pattern2 = r'set\s+INNOVUS\(MODULE_CMD\)\s+.*module\s+load\s+quantus/([^\s"]+)'
# Example: "set INNOVUS(MODULE_CMD)                                                    \"module unload innovus quantus pegasus pvs genus; module load innovus/231/23.33-s082_1 quantus/231/23.10.000 pegasus/232/23.25.000 genus/201/20.10.000\""

# Pattern 3: QRC section module command
pattern3 = r'set\s+QRC\(MODULE_CMD\)\s+.*module\s+load\s+quantus/([^\s"]+)'
# Example: "set QRC(MODULE_CMD)                                                        \"module unload quantus ext; module load quantus/231/23.10.000\""
```

### Detection Logic

1. **File Reading**: Open and read the setup_vars.tcl file line-by-line
2. **Pattern Matching**: Search each line for Quantus version patterns using regex
3. **Version Extraction**: Extract version strings in format `XXX/YY.YY.YYY` from matched lines
4. **Validation**: 
   - Skip commented lines (starting with #)
   - Collect all found versions
   - Check for consistency between INNOVUS and QRC sections
5. **Result Classification**:
   - **PASS**: At least one valid Quantus version found
   - **FAIL**: No Quantus version found in the setup file
6. **Output Formatting**: Display found versions in format `quantus/231/23.10.000`

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# ⚠️ CRITICAL: Reason parameter usage by Type (API-025)
# ALL Types pass found_reason/missing_reason, but use different constants:
#   Type 1/4 (Boolean): Use FOUND_REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use FOUND_REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "List Quantus RC extraction tool version (eg. quantus/231/23.11.000)"

# PASS case descriptions (ALL Types need these)
found_desc = "Quantus RC extraction tool version found in setup configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Quantus version found in setup_vars.tcl configuration file"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Quantus version pattern matched and validated in configuration"

# FAIL case descriptions (ALL Types need these)
missing_desc = "Quantus RC extraction tool version not found in setup configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Quantus version not found in setup_vars.tcl - RC extraction tool not configured"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required Quantus version pattern not satisfied or missing from configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Quantus version check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Quantus version requirement waived per project configuration approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused Quantus version waiver entries"
unused_waiver_reason = "Waiver not matched - specified Quantus version not found in configuration"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: quantus/[major_version]/[full_version]
  Example: quantus/231/23.10.000

ERROR01 (Violation/Fail items):
  Format: Quantus version not found in [file_location]
  Example: Quantus version not found in setup_vars.tcl - check INNOVUS(MODULE_CMD) and QRC(MODULE_CMD) settings
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-01:
  description: "List Quantus RC extraction tool version (eg. quantus/231/23.11.000)"
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
Reason: Quantus version found in setup_vars.tcl configuration file
INFO01:
  - quantus/231/23.10.000
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Quantus version not found in setup_vars.tcl - RC extraction tool not configured
ERROR01:
  - Quantus version not found in setup_vars.tcl - check INNOVUS(MODULE_CMD) and QRC(MODULE_CMD) settings
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-01:
  description: "List Quantus RC extraction tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - Quantus version listing for documentation purposes"
      - "Note: Missing Quantus version is acceptable if RC extraction is not required for this project phase"
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
  - "Explanation: This check is informational only - Quantus version listing for documentation purposes"
  - "Note: Missing Quantus version is acceptable if RC extraction is not required for this project phase"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Quantus version not found in setup_vars.tcl - check INNOVUS(MODULE_CMD) and QRC(MODULE_CMD) settings [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-01:
  description: "List Quantus RC extraction tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: 2
    pattern_items:
      - "quantus/231/23.10.000"
      - "quantus/231/23.11.000"
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
Reason: Quantus version pattern matched and validated in configuration
INFO01:
  - quantus/231/23.10.000
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-01:
  description: "List Quantus RC extraction tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: 2
    pattern_items:
      - "quantus/231/23.10.000"
      - "quantus/231/23.11.000"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - version mismatch acceptable for development phase"
      - "Note: Pattern mismatches are expected when using alternative Quantus versions and do not require fixes"
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
  - "Explanation: This check is informational only - version mismatch acceptable for development phase"
  - "Note: Pattern mismatches are expected when using alternative Quantus versions and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - quantus/231/23.10.000 [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-01:
  description: "List Quantus RC extraction tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: 2
    pattern_items:
      - "quantus/231/23.10.000"
      - "quantus/231/23.11.000"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
    value: 1
    waive_items:
      - name: "quantus/231/23.10.000"
        reason: "Older version approved for legacy compatibility - waived per EDA team"
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
  - quantus/231/23.10.000 [WAIVER]
WARN01 (Unused Waivers):
  - quantus/231/23.11.000: Waiver not matched - specified Quantus version not found in configuration
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-01:
  description: "List Quantus RC extraction tool version (eg. quantus/231/23.11.000)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl"
  waivers:
  waivers:
    value: 1
    waive_items:
      - name: "quantus/231/23.10.000"
        reason: "Older version approved for legacy compatibility - waived per EDA team"
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
  - Quantus version not found in setup_vars.tcl - check INNOVUS(MODULE_CMD) and QRC(MODULE_CMD) settings [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 3.0_TOOL_VERSION --checkers IMP-3-0-0-01 --force

# Run individual tests
python IMP-3-0-0-01.py
```

---

## Notes

- **Version Format**: The checker expects Quantus versions in the format `quantus/XXX/YY.YY.YYY` (e.g., `quantus/231/23.10.000`)
- **Multiple Locations**: Quantus version may appear in both INNOVUS(MODULE_CMD) and QRC(MODULE_CMD) sections - checker reports all found instances
- **Consistency Check**: If different versions are found in INNOVUS vs QRC sections, all versions are reported for manual review
- **Commented Lines**: Lines starting with `#` are ignored during parsing
- **Context Validation**: The checker also validates presence of QRC-related configuration (TECHLIBFILE, LAYERMAP) to ensure RC extraction is properly set up
- **Edge Cases Handled**:
  - Missing setup_vars.tcl file
  - No module load commands present
  - Malformed version strings
  - Multiple different Quantus versions in same file (potential configuration error)