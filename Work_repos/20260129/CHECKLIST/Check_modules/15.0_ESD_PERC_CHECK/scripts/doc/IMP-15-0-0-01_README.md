# IMP-15-0-0-01: Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process.

## Overview

**Check ID:** IMP-15-0-0-01  
**Description:** Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process.  
**Category:** Process Technology Validation  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl`

This checker analyzes the VLSI tool setup configuration file to determine if CNOD (Cell-Near-Oxide-Diffusion) checks are required based on the process technology node. CNOD checks are specifically required for TSMCN5, TSMCN4, and TSMCN3 process technologies. The checker extracts the `DESIGN_PROCESS` variable from the TCL setup file and validates whether CNOD verification is needed.

---

## Check Logic

### Input Parsing

The checker parses the TCL setup configuration file (`setup_vars.tcl`) to extract process technology information. The file contains TCL variable assignments in the format `set VARIABLE_NAME value`.

**Key Patterns:**
```python
# Pattern 1: Extract DESIGN_PROCESS variable
pattern1 = r'^set\s+MISC\(DESIGN_PROCESS\)\s+(\w+)'
# Example: "set MISC(DESIGN_PROCESS)                                                   tsmc3"

# Pattern 2: Generic MISC variable extraction (fallback)
pattern2 = r'^set\s+MISC\(([^)]+)\)\s+(.+)$'
# Example: "set MISC(CON_MODE)                                                         ddr"
```

### Detection Logic

1. **Read setup_vars.tcl file** line by line
2. **Extract DESIGN_PROCESS variable** using regex pattern matching
3. **Identify process technology node** (e.g., tsmc3, tsmcn5, tsmcn4, tsmcn3, etc.)
4. **Determine CNOD requirement**:
   - If `DESIGN_PROCESS in ["tsmcn5", "tsmcn4", "tsmcn3"]` → CNOD check is REQUIRED
   - If `DESIGN_PROCESS not in ["tsmcn5", "tsmcn4", "tsmcn3"]` → CNOD check is NOT REQUIRED
5. **Report findings**:
   - PASS: Process identified and CNOD requirement determined
   - FAIL: DESIGN_PROCESS variable not found or invalid

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

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

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker verifies the existence of the DESIGN_PROCESS variable in the setup configuration file and determines CNOD check requirements based on its value. It's an existence check because we need to confirm the variable is present and readable.

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
item_desc = "Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Process technology identified and CNOD requirement determined"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "DESIGN_PROCESS variable matched and validated"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "DESIGN_PROCESS variable found in setup configuration"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "DESIGN_PROCESS pattern matched and CNOD requirement validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "DESIGN_PROCESS variable not found in setup configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "DESIGN_PROCESS pattern not satisfied in setup file"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required DESIGN_PROCESS variable not found in setup_vars.tcl"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "DESIGN_PROCESS pattern not satisfied or missing from configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Process technology check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "CNOD check requirement waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for process technology check"
unused_waiver_reason = "Waiver not matched - no corresponding process configuration found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Process: [process_name] | CNOD Check Required: [Yes/No] | Reason: [explanation]"
  Example: "Process: tsmc3 | CNOD Check Required: No | Reason: CNOD checks are only required for TSMCN5, TSMCN4, and TSMCN3 processes"

ERROR01 (Violation/Fail items):
  Format: "ERROR: [error_type] - [details]"
  Example: "ERROR: DESIGN_PROCESS variable not found in setup_vars.tcl"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-01:
  description: "Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
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
Reason: DESIGN_PROCESS variable found in setup configuration
INFO01:
  - Process: tsmc3 | CNOD Check Required: No | Reason: CNOD checks are only required for TSMCN5, TSMCN4, and TSMCN3 processes
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required DESIGN_PROCESS variable not found in setup_vars.tcl
ERROR01:
  - ERROR: DESIGN_PROCESS variable not found in setup_vars.tcl
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-01:
  description: "Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - CNOD requirement determination does not block design flow"
      - "Note: Missing DESIGN_PROCESS variable is acceptable for legacy designs using default process settings"
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
  - "Explanation: This check is informational only - CNOD requirement determination does not block design flow"
  - "Note: Missing DESIGN_PROCESS variable is acceptable for legacy designs using default process settings"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: DESIGN_PROCESS variable not found in setup_vars.tcl [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-01:
  description: "Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."
  requirements:
    value: 2
    pattern_items:
      - "tsmc3"
      - "tsmcn5"
      - "tsmcn4"
      - "tsmcn3"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
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
Reason: DESIGN_PROCESS pattern matched and CNOD requirement validated
INFO01:
  - Process: tsmc3 | CNOD Check Required: No | Reason: CNOD checks are only required for TSMCN5, TSMCN4, and TSMCN3 processes
  - Pattern matched: set MISC(DESIGN_PROCESS) tsmc3
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-01:
  description: "Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."
  requirements:
    value: 2
    pattern_items:
      - "tsmc3"
      - "tsmcn5"
      - "tsmcn4"
      - "tsmcn3"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - process technology identification does not block design flow"
      - "Note: Pattern mismatches are expected for legacy designs and do not require fixes"
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
  - "Explanation: This check is informational only - process technology identification does not block design flow"
  - "Note: Pattern mismatches are expected for legacy designs and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Pattern not found: set MISC(DESIGN_PROCESS) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-01:
  description: "Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."
  requirements:
    value: 2
    pattern_items:
      - "tsmc3"
      - "tsmcn5"
      - "tsmcn4"
      - "tsmcn3"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
  waivers:
    value: 2
    waive_items:
      - name: "tsmc3"
        reason: "Waived - legacy design uses implicit process definition from project settings"
      - name: "tsmcn5"
        reason: "Waived - process node identified through alternative configuration method"
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
  - tsmc3 [WAIVER]
  - tsmcn5 [WAIVER]
WARN01 (Unused Waivers):
  - No unused waivers
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-01:
  description: "Confirm whether CNOD check is needed. For example, we need to check CNOD for TSMCN5 process."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/setup_vars.tcl"
  waivers:
    value: 2
    waive_items:
      - name: "tsmc3"
        reason: "Waived - legacy design uses implicit process definition from project settings"
      - name: "tsmcn5"
        reason: "Waived - process node identified through alternative configuration method"
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
  - Process: tsmc3 | CNOD Check Required: No [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 15.0_ESD_PERC_CHECK --checkers IMP-15-0-0-01 --force

# Run individual tests
python IMP-15-0-0-01.py
```

---

## Notes

- **Process Technology Mapping**: The checker identifies TSMCN5, TSMCN4, and TSMCN3 as the processes requiring CNOD checks. Additional process nodes can be added to the logic as needed.
- **File Path Validation**: The checker assumes the setup_vars.tcl file exists at the specified path. Missing file will result in FAIL status.
- **TCL Parsing Limitations**: Multi-line TCL commands (using backslash continuation) are not currently supported. The checker processes single-line variable assignments only.
- **Case Sensitivity**: Process node names are case-sensitive (e.g., "tsmcn5" vs "TSMCN5"). Ensure consistent naming in setup files.
- **CNOD Check Scope**: This checker only determines IF CNOD checks are needed. Actual CNOD verification is performed by separate checkers in the ESD/PERC module.