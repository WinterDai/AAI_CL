# IMP-3-0-0-02: List Conformal LEC tool version (eg. confrml/241/24.10.100)

## Overview

**Check ID:** IMP-3-0-0-02  
**Description:** List Conformal LEC tool version (eg. confrml/241/24.10.100)  
**Category:** 3.0_TOOL_VERSION  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl

This checker extracts and reports the Conformal LEC (Logical Equivalence Checking) tool version from the TCL setup configuration file. It searches for module load commands that specify the confrml tool version used in the VLSI implementation flow. The checker identifies version strings from both FV (Formal Verification) and CLP (Conformal Low Power) module configurations and reports them in the standard format (e.g., confrml/221/22.10.200).

---

## Check Logic

### Input Parsing
The checker parses the TCL setup_vars.tcl file line-by-line to extract Conformal LEC tool version information from module load commands. It searches for specific TCL variable assignments that contain module load directives.

**Key Patterns:**
```python
# Pattern 1: FV (Formal Verification) module load command
pattern1 = r'set\s+FV\(MODULE_CMD\)\s+"[^"]*module\s+load\s+confrml/(\S+)"'
# Example: "set FV(MODULE_CMD)                                                         "module unload confrml; module load confrml/221/22.10.200""

# Pattern 2: CLP (Conformal Low Power) module load command
pattern2 = r'set\s+CLP\(MODULE_CMD\)\s+"[^"]*module\s+load\s+confrml/(\S+)"'
# Example: "set CLP(MODULE_CMD)                                                        "module unload confrml; module load confrml/221/22.10.200""

# Pattern 3: Generic confrml module load (fallback)
pattern3 = r'module\s+load\s+confrml/(\d+)/(\S+)'
# Example: "module load confrml/221/22.10.200"
```

### Detection Logic
1. **File Reading**: Open and read setup_vars.tcl line-by-line
2. **Pattern Matching**: For each line, apply regex patterns to detect confrml module load commands
3. **Version Extraction**: 
   - Extract version string from FV(MODULE_CMD) variable (primary source)
   - Extract version string from CLP(MODULE_CMD) variable (secondary source)
   - Use generic pattern as fallback if specific variables not found
4. **Format Construction**: Construct output in format "confrml/[major_version]/[full_version]"
5. **Deduplication**: If multiple instances found, report unique versions
6. **Result Classification**:
   - PASS: At least one confrml version found
   - FAIL: No confrml version found in configuration file

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
item_desc = "List Conformal LEC tool version (eg. confrml/241/24.10.100)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Conformal LEC tool version found in setup configuration"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All required Conformal LEC tool versions matched in configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Conformal LEC tool version found in setup_vars.tcl"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Required Conformal LEC tool version patterns matched and validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Conformal LEC tool version not found in setup configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Required Conformal LEC tool version patterns not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Conformal LEC tool version not found in setup_vars.tcl - module load command missing"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required Conformal LEC tool version patterns not satisfied or missing from configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Conformal LEC tool version check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Conformal LEC tool version mismatch waived per tool configuration approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused Conformal LEC tool version waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding tool version found in configuration"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: confrml/[major_version]/[full_version]
  Example: confrml/221/22.10.200

ERROR01 (Violation/Fail items):
  Format: ERROR: Conformal LEC tool version not found in [file_path]
  Example: ERROR: Conformal LEC tool version not found in ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-02:
  description: "List Conformal LEC tool version (eg. confrml/241/24.10.100)"
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
Reason: Conformal LEC tool version found in setup_vars.tcl
INFO01:
  - confrml/221/22.10.200
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Conformal LEC tool version not found in setup_vars.tcl - module load command missing
ERROR01:
  - ERROR: Conformal LEC tool version not found in ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-02:
  description: "List Conformal LEC tool version (eg. confrml/241/24.10.100)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - tool version tracking for documentation purposes"
      - "Note: Missing Conformal LEC version is acceptable for designs not requiring formal verification"
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
  - "Explanation: This check is informational only - tool version tracking for documentation purposes"
  - "Note: Missing Conformal LEC version is acceptable for designs not requiring formal verification"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: Conformal LEC tool version not found in ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-02:
  description: "List Conformal LEC tool version (eg. confrml/241/24.10.100)"
  requirements:
    value: 2
    pattern_items:
      - "confrml/221/22.10.200"
      - "confrml/241/24.10.100"
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
Reason: Required Conformal LEC tool version patterns matched and validated
INFO01:
  - confrml/221/22.10.200
  - confrml/241/24.10.100
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-3-0-0-02:
  description: "List Conformal LEC tool version (eg. confrml/241/24.10.100)"
  requirements:
    value: 2
    pattern_items:
      - "confrml/221/22.10.200"
      - "confrml/241/24.10.100"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Tool version check is informational - version mismatches do not block signoff"
      - "Note: Different Conformal LEC versions are acceptable across project phases"
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
  - "Explanation: Tool version check is informational - version mismatches do not block signoff"
  - "Note: Different Conformal LEC versions are acceptable across project phases"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - confrml/231/23.15.500 [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-02:
  description: "List Conformal LEC tool version (eg. confrml/241/24.10.100)"
  requirements:
    value: 2
    pattern_items:
      - "confrml/221/22.10.200"
      - "confrml/241/24.10.100"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 2
    waive_items:
      - name: "confrml/231/23.15.500"
        reason: "Waived - intermediate tool version used for debug, will be updated to 241/24.10.100 before tapeout"
      - name: "confrml/211/21.08.100"
        reason: "Waived - legacy version acceptable for this IP block per tool team approval"
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
  - confrml/231/23.15.500 [WAIVER]
WARN01 (Unused Waivers):
  - confrml/211/21.08.100: Waiver entry not matched - no corresponding tool version found in configuration
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-3-0-0-02:
  description: "List Conformal LEC tool version (eg. confrml/241/24.10.100)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/tcl/2.0/setup_vars.tcl
  waivers:
    value: 2
    waive_items:
      - name: "confrml/231/23.15.500"
        reason: "Waived - intermediate tool version used for debug, will be updated to 241/24.10.100 before tapeout"
      - name: "confrml/211/21.08.100"
        reason: "Waived - legacy version acceptable for this IP block per tool team approval"
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
  - confrml/231/23.15.500 [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 3.0_TOOL_VERSION --checkers IMP-3-0-0-02 --force

# Run individual tests
python IMP-3-0-0-02.py
```

---

## Notes

- **Multi-tool Commands**: The setup_vars.tcl file may contain module load commands with multiple tools (e.g., "module load innovus/231/23.33-s082_1 quantus/231/23.10.000"). The checker specifically extracts only confrml versions.
- **FV vs CLP**: Both FV (Formal Verification) and CLP (Conformal Low Power) configurations may reference confrml. The checker reports all unique versions found.
- **Line Continuation**: TCL files may use backslash for line continuation. The checker should handle multi-line module load commands.
- **Variable Substitution**: If the TCL file uses variable substitution (e.g., ${CONFRML_VERSION}), the checker reports the literal string as-is.
- **Missing Version**: If no confrml module load command is found, the checker reports a FAIL with appropriate error message.
- **Version Format**: Output format strictly follows "confrml/[major]/[full_version]" (e.g., confrml/221/22.10.200) for consistency with tool module naming conventions.