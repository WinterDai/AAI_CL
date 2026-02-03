# IMP-3-0-0-00: List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)

## Overview

**Check ID:** IMP-3-0-0-00
**Description:** List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)
**Category:** Tool Version Verification
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl

This checker extracts and reports the Innovus implementation tool version from the setup configuration file. It parses the TCL setup_vars.tcl file to locate the INNOVUS(MODULE_CMD) variable and extracts the version string from the module load command. This information is critical for ensuring consistent tool versions across the implementation flow and for debugging tool-specific issues.

---

## Check Logic

### Input Parsing

The checker reads the TCL configuration file `setup_vars.tcl` line by line, searching for the INNOVUS(MODULE_CMD) variable that contains the module load command with the tool version.

**Key Patterns:**

```python
# Pattern 1: INNOVUS MODULE_CMD with version in module load command
pattern1 = r'set\s+INNOVUS\(MODULE_CMD\)\s+"[^"]*module\s+load\s+innovus/([^\s"]+)'
# Example: "set INNOVUS(MODULE_CMD)                                                    "module unload innovus quantus pegasus pvs genus; module load innovus/231/23.33-s082_1 quantus/231/23.10.000 pegasus/232/23.25.000 genus/201/20.10.000""
# Captures: 231/23.33-s082_1

# Pattern 2: Alternative format with different spacing
pattern2 = r'set\s+INNOVUS\(MODULE_CMD\).*?innovus/(\S+)'
# Example: "set INNOVUS(MODULE_CMD) "module load innovus/221/22.11-s119_1""
# Captures: 221/22.11-s119_1

# Pattern 3: Comment lines to skip
pattern3 = r'^\s*#'
# Example: "###TOOL VARS###"

# Pattern 4: Empty lines to skip
pattern4 = r'^\s*$'
```

### Detection Logic

1. **File Reading**: Open and read setup_vars.tcl line by line
2. **Line Filtering**: Skip comment lines (starting with #) and empty lines
3. **Pattern Matching**: Search for lines containing `set INNOVUS(MODULE_CMD)`
4. **Version Extraction**: Apply regex pattern to extract version string from the module load command
5. **Output Construction**: Prepend "innovus/" to the captured version string to create the full version path (e.g., "innovus/231/23.33-s082_1")
6. **Early Exit**: Return immediately upon first successful match
7. **Error Handling**: If no match found by end of file, return error message

**Edge Cases Handled:**

- File not found or empty → ERROR01
- INNOVUS(MODULE_CMD) exists but no version pattern → ERROR01
- Multiple INNOVUS(MODULE_CMD) definitions → Return first match
- Version strings with special characters (underscores, dots, hyphens) → Handled by \S+ pattern
- Multiline TCL continuation (backslash) → Assumes single line format

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# Item description for this checker
item_desc = "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"

# PASS case - what message to show when check passes
found_reason = "Innovus tool version successfully extracted from setup_vars.tcl"
found_desc = "Innovus version information retrieved"

# FAIL case - what message to show when check fails
missing_reason = "Innovus version not found in setup_vars.tcl or file parsing failed"
missing_desc = "Failed to extract Innovus version information"

# WAIVED case (Type 3/4) - what message to show for waived items
waived_base_reason = "Version extraction failure waived"
waived_desc = "Waived version extraction issues"

# UNUSED waivers - what message to show for unused waiver entries
unused_waiver_reason = "Waiver not matched - version was successfully extracted"
unused_desc = "Unused waiver entries"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "innovus/<version_path>"
  Example: "innovus/231/23.33-s082_1"
  Example: "innovus/221/22.11-s119_1"

ERROR01 (Violation/Fail items):
  Format: "ERROR: <error_description>"
  Example: "ERROR: Innovus version not found in setup_vars.tcl"
  Example: "ERROR: File not found or empty: setup_vars.tcl"
  Example: "ERROR: Innovus version pattern not found in MODULE_CMD"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-3-0-0-00:
  description: "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"
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
Reason: Innovus tool version successfully extracted from setup_vars.tcl
INFO01:
  - innovus/231/23.33-s082_1
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Innovus version not found in setup_vars.tcl or file parsing failed
ERROR01:
  - ERROR: Innovus version not found in setup_vars.tcl
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-3-0-0-00:
  description: "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - version extraction failure does not block signoff"
      - "Note: Version information is used for tracking purposes only and can be manually verified if extraction fails"
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
  - "Explanation: This check is informational only - version extraction failure does not block signoff"
  - "Note: Version information is used for tracking purposes only and can be manually verified if extraction fails"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: Innovus version not found in setup_vars.tcl [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-3-0-0-00:
  description: "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"
  requirements:
    value: 2
    pattern_items:
      - "innovus/231/23.33-s082_1"
      - "innovus/221/22.11-s119_1"
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
Reason: Innovus tool version successfully extracted from setup_vars.tcl
INFO01:
  - innovus/231/23.33-s082_1
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-3-0-0-00:
  description: "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"
  requirements:
    value: 2
    pattern_items:
      - "innovus/231/23.33-s082_1"
      - "innovus/221/22.11-s119_1"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - version mismatch does not block signoff"
      - "Note: Version pattern mismatches are expected during tool migration and do not require immediate fixes"
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
  - "Explanation: This check is informational only - version mismatch does not block signoff"
  - "Note: Version pattern mismatches are expected during tool migration and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - innovus/201/20.10.000 [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-3-0-0-00:
  description: "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"
  requirements:
    value: 2
    pattern_items:
      - "innovus/231/23.33-s082_1"
      - "innovus/221/22.11-s119_1"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 1
    waive_items:
      - name: "innovus/201/20.10.000"
        reason: "Legacy version approved for this project - migration to 23.x planned for next tapeout"
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
  - innovus/201/20.10.000 [WAIVER]
WARN01 (Unused Waivers):
  - innovus/191/19.15.000: Waiver not matched - version was successfully extracted
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-3-0-0-00:
  description: "List Innovus implementation tool version (eg. innovus/221/22.11-s119_1)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 1
    waive_items:
    - name: "innovus/201/20.10.000"
      reason: "Legacy version approved for this project - migration to 23.x planned for next tapeout"
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
  - ERROR: Innovus version not found in setup_vars.tcl [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 3.0_TOOL_VERSION --checkers IMP-3-0-0-00 --force

# Run individual tests
python IMP-3-0-0-00.py
```

---

## Notes

**Implementation Details:**

- The checker uses early exit optimization - returns immediately upon first version match
- Regex pattern `\S+` captures version strings with underscores, dots, and hyphens
- Current implementation assumes single-line format; multiline TCL continuation (backslash) may require line joining logic if encountered

**Limitations:**

- Only extracts the first INNOVUS(MODULE_CMD) definition found (TCL would use last definition if multiple exist)
- Does not validate version format or check against approved version lists
- Assumes standard module load command format; non-standard formats may not be detected

**Known Issues:**

- If setup_vars.tcl uses TCL line continuation (backslash), the version may not be extracted correctly
- Version extraction is case-sensitive for the "innovus" tool name

**Best Practices:**

- Use Type 1 for simple version reporting (informational)
- Use Type 2 when validating against specific approved versions
- Use Type 3/4 with waivers when legacy versions are temporarily approved
- Use waivers.value=0 for informational-only checks during tool migration periods
