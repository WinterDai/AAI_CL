# IMP-7-0-0-03: Confirm all Warning messages during read constraints can be waived.

## Overview

**Check ID:** IMP-7-0-0-03  
**Description:** Confirm all Warning messages during read constraints can be waived.  
**Category:** Constraint Validation  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt`

This checker validates that all warning messages generated during Innovus constraint file reading can be waived. It parses the constraint reading log to extract warning messages (with codes, affected objects, and source file locations), then verifies that each warning has a corresponding waiver entry. The check ensures that all constraint-related warnings are either resolved or explicitly approved for waiver, preventing unintended design rule violations from propagating through the implementation flow.

---

## Check Logic

### Input Parsing
Parse the Innovus constraint reading log file to extract:
1. **Constraint mode context**: Track which constraint mode (func/scan/etc.) is active
2. **Constraint files**: Capture file paths being read and their reading status
3. **Warning messages**: Extract warning code, message text, affected object, source file, and line number
4. **Violation summaries**: Parse violation tables for severity counts

**Key Patterns:**
```python
# Pattern 1: Constraint file reading initiation
pattern1 = r"Reading timing constraints file '([^']+)'"
# Example: "Reading timing constraints file '/projects/yunbao_N6_80bits_EW_PHY_OD_6400/input/latest/innovus_cons/user_setup_6400.ets' ..."

# Pattern 2: Successful constraint reading confirmation
pattern2 = r"INFO\s*\(CTE\):\s*Constraints read successfully"
# Example: "INFO (CTE): Constraints read successfully."

# Pattern 3: WARNING messages during constraint reading (standard log format)
pattern3 = r"\*\*WARN:\s*\(([A-Z]+-\d+)\):\s*(.+?)(?:\(File\s+([^,]+),\s*Line\s+(\d+)\))?"
# Example: "**WARN: (TCLCMD-1531): 'set_case_analysis' has been applied on hierarchical pin..."

# Pattern 4: Message summary line (context for total warning count)
pattern4 = r"\*\*\*\s*Message Summary:\s*(\d+)\s*warning\(s\),\s*(\d+)\s*error\(s\)"
# Example: "*** Message Summary: 445953 warning(s), 4673 error(s)"

# Pattern 5: Table format - | ID | Severity | Count | Description |
pattern5 = r'^\|\s*([A-Z]+-\d+)\s*\|\s*(error|warning)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|$'
# Example: "| CHKPLC-18         | warning   | 29178       | Preplaced instance <%s> has vertical pin-track mask violation. |"
# Output format: WARNING_CODE: description (no | symbols)
# Example output: "CHKPLC-18: Preplaced instance <%s> has vertical pin-track mask violation."
```

### Detection Logic
1. **State Machine Tracking**: Track whether currently in constraint reading phase or in table parsing mode
2. **Constraint File Detection**: Identify all constraint files being read using Pattern 1
3. **Success Confirmation**: Track successful constraint reading using Pattern 2
4. **Standard WARNING Detection**: Capture `**WARN:` messages during constraint reading phase using Pattern 3
   - Extract warning code, message text, file path, and line number
5. **Table Format WARNING Detection**: Capture table-style warning messages using Pattern 5
   - Parse rows with format: `| ID | Severity | Count | Description |`
   - Extract warning code, count, and description (ignoring `|` delimiters)
   - Support multi-line descriptions (continuation lines)
   - Only capture rows with severity="warning", skip errors
6. **Result Classification**:
   - **PASS**: No WARNING messages found (neither standard format nor table format)
   - **FAIL**: One or more WARNING messages found
7. **Output Formatting**:
   - INFO01: List of waived warnings (Type 3/4 only)
   - ERROR01: List of unwaived WARNING messages with format `WARNING_CODE: description` (no `|` symbols)

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
item_desc = "Confirm all Warning messages during read constraints can be waived."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No constraint reading warnings found"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All constraint reading warnings matched waiver patterns"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No constraint reading warnings found in log file"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All constraint reading warnings matched and validated against waiver list"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Constraint reading warnings found without waivers"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Constraint reading warnings not satisfied by waiver patterns"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Constraint reading warnings found without corresponding waivers"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Constraint reading warnings not satisfied - waiver patterns missing or incomplete"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Constraint reading warnings waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Constraint reading warning waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused constraint warning waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding constraint warning found in log"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[WARNING_CODE]: message | Object: object_name | Source: file:line [WAIVER]"
  Example: "TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin | Object: inst_master_delay/inst_cal_dly_macro/inst_cal_delay_line/cal_qtr_delay_sel[2] | Source: cdn_hs_phy_data_slice.con.edi:501 [WAIVER]"

ERROR01 (Violation/Fail items):
  Format: "[WARNING_CODE]: message | Object: object_name | Source: file:line"
  Example: "TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin | Object: inst_master_delay/inst_cal_dly_macro/inst_cal_delay_line/cal_qtr_delay_sel[2] | Source: cdn_hs_phy_data_slice.con.edi:501"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-03:
  description: "Confirm all Warning messages during read constraints can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt"
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
Reason: No constraint reading warnings found in log file
INFO01:
  - Constraint files read successfully without warnings
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Constraint reading warnings found without corresponding waivers
ERROR01:
  - TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin
  - TCLCMD-1532: Clock network 'clk_slow' has conflicting timing constraints
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-03:
  description: "Confirm all Warning messages during read constraints can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Constraint reading warnings are informational only for this design phase"
      - "Note: Warnings related to set_case_analysis on hierarchical pins are expected in PHY designs and do not require fixes"
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
  - "Explanation: Constraint reading warnings are informational only for this design phase"
  - "Note: Warnings related to set_case_analysis on hierarchical pins are expected in PHY designs and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin [WAIVED_AS_INFO]
  - TCLCMD-1532: Clock network has conflicting timing constraints [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-03:
  description: "Confirm all Warning messages during read constraints can be waived."
  requirements:
    value: 2
    pattern_items:
      - "TCLCMD-1531"  # Match by warning code only
      - "TCLCMD-1532"  # Match by warning code only
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt"
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
Reason: All constraint reading warnings matched and validated against waiver list
INFO01:
  - TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin
  - TCLCMD-1532: Clock network has conflicting timing constraints
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-03:
  description: "Confirm all Warning messages during read constraints can be waived."
  requirements:
    value: 2
    pattern_items:
      - "TCLCMD-1531"  # Match by warning code only
      - "TCLCMD-1532"  # Match by warning code only
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Constraint reading warnings are informational only for this design phase"
      - "Note: Pattern mismatches for set_case_analysis warnings are expected in PHY designs and do not require fixes"
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
  - "Explanation: Constraint reading warnings are informational only for this design phase"
  - "Note: Pattern mismatches for set_case_analysis warnings are expected in PHY designs and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin [WAIVED_AS_INFO]
  - TCLCMD-1532: Clock network has conflicting timing constraints [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-03:
  description: "Confirm all Warning messages during read constraints can be waived."
  requirements:
    value: 2
    pattern_items:
      - "TCLCMD-1531"  # Match by warning code only
      - "TCLCMD-1532"  # Match by warning code only
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "TCLCMD-1531"  # Match by warning code only
        reason: "Waived - set_case_analysis on hierarchical pins is required for PHY calibration logic per design specification"
      - name: "TCLCMD-1532"  # Match by warning code only
        reason: "Waived - Clock network conflicts are expected during constraint reading phase"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items against waive_items (by warning code)
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin [WAIVER]
  - TCLCMD-1532: Clock network has conflicting timing constraints [WAIVER]
WARN01 (Unused Waivers):
  (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-03:
  description: "Confirm all Warning messages during read constraints can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-02.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "TCLCMD-1531"  # Match by warning code only
        reason: "Waived - set_case_analysis on hierarchical pins is required for PHY calibration logic per design specification"
      - name: "TCLCMD-1532"  # Match by warning code only
        reason: "Waived - Clock network conflicts are expected during constraint reading phase"
```

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items (by warning code)
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - TCLCMD-1531: 'set_case_analysis' has been applied on hierarchical pin [WAIVER]
  - TCLCMD-1532: Clock network has conflicting timing constraints [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 7.0_INNOVUS_DESIGN_IN_CHECK --checkers IMP-7-0-0-03 --force

# Run individual tests
python IMP-7-0-0-03.py
```

---

## Notes

- **Warning Code Matching**: The checker matches warnings by warning code only (e.g., TCLCMD-1531), not by full message text. This simplifies configuration and allows matching regardless of message variations
- **Table Format Support**: The checker supports both standard log format (`**WARN:` messages) and table format (`| ID | Severity | Count | Description |`)
- **Output Format**: Warning descriptions are formatted as `WARNING_CODE: description` with pipe symbols (`|`) removed for cleaner output
- **Source File Tracking**: File path and line number information is extracted when available in the log
- **Known Limitations**: 
  - Warning message format must match expected patterns (standard or table format)
  - Multi-line descriptions in table format may require continuation line parsing
  - Waiver matching is case-sensitive for warning codes