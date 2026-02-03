# IMP-7-0-0-02: Confirm no ERROR message during read constraints.

## Overview

**Check ID:** IMP-7-0-0-02
**Description:** Confirm no ERROR message during read constraints.
**Category:** Innovus Design Import Validation
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt

This checker validates that the Innovus constraint reading process completes without ERROR messages. It parses the Innovus tool log to distinguish between actual constraint reading errors (which occur during the file parsing phase) and post-constraint violation summaries (which are reported after constraints are successfully loaded). The checker specifically looks for `**ERROR:` messages during the constraint file reading phase, ignoring warnings and violation tables that appear after constraints are loaded.

---

## Check Logic

### Input Parsing

The checker parses Innovus constraint reading logs line-by-line with state tracking to distinguish between:

1. **Constraint Reading Phase**: Lines between "Reading timing constraints file" and constraint loading completion
2. **Post-Constraint Phase**: Violation summaries and checks that occur after constraints are loaded

**Key Patterns:**

```python
# Pattern 1: Constraint file reading initiation
pattern1 = r"Reading timing constraints file '([^']+)'"
# Example: "Reading timing constraints file '/projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/user_setup_6400.ets' ..."

# Pattern 2: Successful constraint reading confirmation
pattern2 = r"INFO\s*\(CTE\):\s*Constraints read successfully"
# Example: "INFO (CTE): Constraints read successfully."

# Pattern 3: ERROR messages during constraint reading (critical detection)
pattern3 = r"\*\*ERROR:\s*\(([A-Z]+-\d+)\):\s*(.+?)(?:\(File\s+([^,]+),\s*Line\s+(\d+)\))?"
# Example: "**ERROR: (TCLCMD-5678): Undefined variable in constraint file (File /path/to/file.sdc, Line 123)"

# Pattern 4: WARNING messages during constraint reading (context only)
pattern4 = r"\*\*WARN:\s*\(([A-Z]+-\d+)\):\s*(.+?)(?:\(File\s+([^,]+),\s*Line\s+(\d+)\))?"
# Example: "**WARN: (TCLCMD-1531):	'set_case_analysis' has been applied on hierarchical pin 'inst_master_delay/inst_cal_dly_macro/inst_cal_delay_line/cal_qtr_delay_sel[2]' (File /projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/cdn_hs_phy_data_slice.con.edi, Line 501)."

# Pattern 5: Message summary line (context for total error count)
pattern5 = r"\*\*\*\s*Message Summary:\s*(\d+)\s*warning\(s\),\s*(\d+)\s*error\(s\)"
# Example: "*** Message Summary: 445953 warning(s), 4673 error(s)"

# Pattern 6: Parse-style ERROR messages with severity (NEW)
pattern6 = r"([A-Z]+-\d+)\s*\|\s*error\s*\|\s*\d+\s+(.+)"
# Example: "IMPMSMV-8350      | error     | 1 xxx"
```

### Detection Logic

1. **State Machine Tracking**: Track whether currently in constraint reading phase or post-constraint phase
2. **Constraint File Detection**: Identify all constraint files being read using Pattern 1
3. **Success Confirmation**: Track successful constraint reading using Pattern 2
4. **ERROR Detection**: Capture `**ERROR:` messages during constraint reading phase using Pattern 3
   - Extract error code, message, file path, and line number
   - Ignore errors in post-constraint violation tables (these are violation summaries, not reading errors)
5. **Parse-style ERROR Detection**: Capture parse-style error messages with severity="error" using Pattern 6
   - Extract error code and message text
   - These errors also indicate constraint reading failures
6. **Context Tracking**: Monitor warnings (Pattern 4) for context but do not treat as failures
7. **Result Classification**:
   - **PASS**: No `**ERROR:` messages or parse-style error messages found during constraint reading phase
   - **FAIL**: One or more `**ERROR:` messages or parse-style error messages found during constraint reading phase
8. **Output Formatting**:
   - INFO01: List of successfully read constraint files with status
   - ERROR01: List of ERROR messages with code, message, file, and line number (including parse-style errors)

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
item_desc = "Confirm no ERROR message during read constraints."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No ERROR messages found during constraint reading"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All constraint files read successfully without errors"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No ERROR messages found during constraint reading phase"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All constraint files successfully read and validated without ERROR messages"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "ERROR messages found during constraint reading"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Constraint reading failed - ERROR messages detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "ERROR messages found during constraint file reading phase"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Constraint reading validation failed - ERROR messages detected in reading phase"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Constraint reading errors waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Constraint reading ERROR waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused constraint error waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding constraint reading ERROR found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[constraint_file_path] - Status: SUCCESS"
  Example: "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/user_setup_6400.ets - Status: SUCCESS"

ERROR01 (Violation/Fail items):
  Format: "ERROR: (error_code) message_text [File: file_path, Line: line_number]"
  Example: "ERROR: (TCLCMD-1234) Constraint parsing failed [File: user_setup.sdc, Line: 45]"
  
  OR (for parse-style errors):
  Format: "ERROR: (error_code) message_text"
  Example: "ERROR: (IMPMSMV-8350) xxx"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-7-0-0-02:
  description: "Confirm no ERROR message during read constraints."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt
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
Reason: No ERROR messages found during constraint reading phase
INFO01:
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/user_setup_6400.ets - Status: SUCCESS
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/cdn_hs_phy_data_slice.con.edi - Status: SUCCESS
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: ERROR messages found during constraint file reading phase
ERROR01:
  - ERROR: (TCLCMD-1234) Constraint parsing failed [File: /projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/user_setup_6400.ets, Line: 45]
  - ERROR: (TCLCMD-5678) Undefined variable in constraint file [File: /projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/cdn_hs_phy_data_slice.con.edi, Line: 123]
  - ERROR: (IMPMSMV-8350) xxx
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-7-0-0-02:
  description: "Confirm no ERROR message during read constraints."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Constraint reading errors are informational only during early design phases"
      - "Note: Errors are expected when using legacy constraint files and do not block design progress"
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
  - Explanation: Constraint reading errors are informational only during early design phases
  - Note: Errors are expected when using legacy constraint files and do not block design progress
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: (TCLCMD-1234) Constraint parsing failed [File: user_setup_6400.ets, Line: 45] [WAIVED_AS_INFO]
  - ERROR: (TCLCMD-5678) Undefined variable in constraint file [File: cdn_hs_phy_data_slice.con.edi, Line: 123] [WAIVED_AS_INFO]
  - ERROR: (IMPMSMV-8350) xxx [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-7-0-0-02:
  description: "Confirm no ERROR message during read constraints."
  requirements:
    value: 3
    pattern_items:
      - "TCLCMD-1234"
      - "TCLCMD-5678"
      - "IMPMSMV-8350"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt
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
Reason: All constraint files successfully read and validated without ERROR messages
INFO01:
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/user_setup_6400.ets - Status: SUCCESS
  - /projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/cdn_hs_phy_data_slice.con.edi - Status: SUCCESS
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-7-0-0-02:
  description: "Confirm no ERROR message during read constraints."
  requirements:
    value: 2
    pattern_items:
      - "TCLCMD-1234"
      - "IMPMSMV-8350"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Constraint reading errors are informational only during early design phases"
      - "Note: Pattern mismatches are expected when using legacy constraint files and do not require fixes"
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
  - Explanation: Constraint reading errors are informational only during early design phases
  - Note: Pattern mismatches are expected when using legacy constraint files and do not require fixes
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - ERROR: (TCLCMD-1234) Constraint parsing failed [File: user_setup_6400.ets, Line: 45] [WAIVED_AS_INFO]
  - ERROR: (TCLCMD-5678) Undefined variable in constraint file [File: cdn_hs_phy_data_slice.con.edi, Line: 123] [WAIVED_AS_INFO]
  - ERROR: (IMPMSMV-8350) xxx [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-7-0-0-02:
  description: "Confirm no ERROR message during read constraints."
  requirements:
    value: 2
    pattern_items:
      - "TCLCMD-1234"
      - "IMPMSMV-8350"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt
  waivers:
    value: 3
    waive_items:
      - name: "TCLCMD-1234"
        reason: "Waived - legacy constraint file uses deprecated syntax, will be updated in next release"
      - name: "TCLCMD-5678"
        reason: "Waived - variable defined in separate include file, error is benign"
      - name: "IMPMSMV-8350"
        reason: "Waived - parse error is expected for this design configuration"
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
  - ERROR: (TCLCMD-1234) Constraint parsing failed [File: user_setup_6400.ets, Line: 45] [WAIVER]
  - ERROR: (TCLCMD-5678) Undefined variable in constraint file [File: cdn_hs_phy_data_slice.con.edi, Line: 123] [WAIVER]
  - ERROR: (IMPMSMV-8350) xxx [WAIVER]
WARN01 (Unused Waivers):
  - (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-7-0-0-02:
  description: "Confirm no ERROR message during read constraints."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt
  waivers:
    value: 3
    waive_items:
      - name: "TCLCMD-1234"
        reason: "Waived - legacy constraint file uses deprecated syntax, will be updated in next release"
      - name: "TCLCMD-5678"
        reason: "Waived - variable defined in separate include file, error is benign"
      - name: "IMPMSMV-8350"
        reason: "Waived - parse error is expected for this design configuration"
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
  - ERROR: (TCLCMD-1234) Constraint parsing failed [File: user_setup_6400.ets, Line: 45] [WAIVER]
  - ERROR: (TCLCMD-5678) Undefined variable in constraint file [File: cdn_hs_phy_data_slice.con.edi, Line: 123] [WAIVER]
  - ERROR: (IMPMSMV-8350) xxx [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 7.0_INNOVUS_DESIGN_IN_CHECK --checkers IMP-7-0-0-02 --force

# Run individual tests
python IMP-7-0-0-02.py
```

---

## Notes

**Critical Distinctions:**

- This checker focuses ONLY on errors during the constraint **reading** phase, not post-constraint violation summaries
- `**WARN:` messages are tracked for context but do not cause FAIL status
- Violation tables (IMPMSMV-*, CHKPLC-*, etc.) that appear after constraint loading are NOT constraint reading errors
- The Message Summary line shows total errors including post-constraint violations, so individual `**ERROR:` lines must be parsed to distinguish reading errors
- Parse-style error messages with severity="error" (e.g., "IMPMSMV-8350 | error | 1 xxx") are also treated as constraint reading errors

**Known Limitations:**

- Checker assumes constraint reading errors appear as `**ERROR:` messages or parse-style error messages in the log
- State machine tracking may need adjustment if Innovus log format changes
- Multi-file constraint reading is supported by tracking each "Reading timing constraints file" marker

**File Format Dependencies:**

- Requires Innovus log format with "Reading timing constraints file" markers
- Expects `**ERROR:`, `**WARN:`, and `INFO (CTE):` message formats
- Supports parse-style error format: "ERROR_CODE | error | count message"
- Relies on consistent message formatting with optional file/line number information
