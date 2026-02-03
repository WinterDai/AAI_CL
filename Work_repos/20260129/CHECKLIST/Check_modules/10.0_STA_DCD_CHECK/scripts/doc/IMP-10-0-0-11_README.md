# IMP-10-0-0-11: Confirm the timing of all path groups is clean.

## Overview

**Check ID:** IMP-10-0-0-11  
**Description:** Confirm the timing of all path groups is clean.  
**Category:** Static Timing Analysis  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/check_signoff.results

### Purpose

This checker validates that all timing path groups across all PVT (Process, Voltage, Temperature) corners meet timing requirements with no setup or hold violations. It parses multi-corner/multi-mode (MCMM) timing signoff summary reports to ensure the design is ready for tape-out.

### Functional Description

**What is being checked?**
The checker extracts timing results from tabular signoff reports containing:
- View names (corner/mode combinations like `func_rcss_0p675v_125c_pcss_cmax_pcff3_setup`)
- Path groups (reg2reg, cgdefault, default)
- Timing check types (setup vs hold)
- Worst Negative Slack (WNS) values
- Violation counts per path group

It flags any negative slack values as timing violations and reports the worst slack and violation count per view/path group combination.

**Why is this check important for VLSI design?**
Timing closure is a critical signoff requirement. Any timing violations can cause functional failures in silicon, including:
- Setup violations: Data arrives too late, causing metastability or incorrect sampling
- Hold violations: Data changes too early, causing race conditions

This check ensures all timing corners are clean before proceeding to physical verification and tape-out, preventing costly silicon respins.

---

## Check Logic

### Input Parsing

The input file is a CSV-like tabular format with headers defining path groups and timing check types, followed by data rows containing slack values and violation counts for each view.

**Key Patterns:**
```python
# Pattern 1: Header line defining path groups
pattern_header = r'^[\w\d_]+\s*,\s*(.+)$'
# Example: "cdn_sd2101_i3p765_vm130_6x2ya2yb2yc2yd1ye1ga1gb                                 ,      reg2reg(),     cgdefault(),       default(),       reg2reg(),     cgdefault(),       default()"

# Pattern 2: Sub-header defining setup/hold columns
pattern_subheader = r'^View\s*,\s*(.+)$'
# Example: "View                                                                            , setup(vio_num),  setup(vio_num),  setup(vio_num),   hold(vio_num),   hold(vio_num),   hold(vio_num)"

# Pattern 3: Data row with timing results
pattern_datarow = r'^([\w\d_]+)\s*,\s*(.+)$'
# Example: "func_rcss_0p675v_125c_pcss_cmax_pcff3_setup                                     ,  0.0000(    0),      ---(    0),  -0.2318(   40),      ---(    0),      ---(    0),      ---(    0)"

# Pattern 4: Individual slack/violation cell
pattern_cell = r'(---|\-?\d+\.\d+)\(\s*(\d+)\)'
# Example: "-0.2318(   40)" captures slack=-0.2318, violations=40
# Example: "0.0000(    0)" captures slack=0.0000, violations=0
# Example: "---(    0)" captures not-applicable entries
```

### Detection Logic

1. **Parse Headers**: Read the first two lines to build a column map
   - Line 1: Extract path group names (reg2reg, cgdefault, default)
   - Line 2: Extract timing types (setup/hold) for each column
   - Build mapping: `{column_index: (path_group, timing_type)}`

2. **Parse Data Rows**: For each subsequent line:
   - Extract view name (first column)
   - Split remaining columns by comma
   - For each column, apply `pattern_cell` to extract slack and violation count
   - Skip columns with "---" (not applicable)

3. **Detect Violations**: For each parsed cell:
   - If slack < 0 and violation_count > 0: Flag as ERROR01
   - If slack >= 0 and violation_count == 0: Count as clean (INFO01)

4. **Aggregate Results**:
   - Count total views analyzed
   - Count clean views (all path groups clean)
   - Collect all violations with details: view, path_group, timing_type, WNS, count

5. **Determine Status**:
   - PASS: No violations found (all views clean)
   - FAIL: One or more violations detected

---

## Output Descriptions (CRITICAL - Code Generator Will Use These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**AI MUST fill in these values based on the check logic above.**

```python
# ⚠️ CRITICAL: These descriptions MUST be used IDENTICALLY across ALL Type 1/2/3/4!
# Same checker = Same descriptions, regardless of Type configuration

# Item description for this checker
item_desc = "Confirm the timing of all path groups is clean."

# PASS case - clean items (INFO)
found_desc = "Clean timing path groups"
found_reason = "Path group meets timing requirements"

# FAIL case - violations (ERROR)
missing_desc = "Timing violations detected"
missing_reason = "Timing violation detected"

# WAIVED case (Type 3/4) - waived violations (INFO)
waived_desc = "Waived timing violations"
waived_base_reason = "Timing violation waived per design approval"

# UNUSED waivers (WARN)
unused_desc = "Unused waiver entries"
unused_waiver_reason = "Waiver entry not matched"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "View '[view_name]' path_group '[path_group]' [timing_type]: WNS=[slack]ns (0 violations)"
  Example: "View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'reg2reg' setup: WNS=0.1234ns (0 violations)"

ERROR01 (Violation/Fail items):
  Format: "View '[view_name]' path_group '[path_group]' [timing_type]: WNS=[slack]ns ([count] violations)"
  Example: "View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'default' setup: WNS=-0.2318ns (40 violations)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-11:
  description: "Confirm the timing of all path groups is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/check_signoff.results
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a global boolean check: either all timing is clean (PASS) or violations exist (FAIL). No waivers are applied. The checker scans all views and path groups, reporting PASS only if every timing check shows non-negative slack with zero violations.

**Sample Output (PASS):**
```
Status: PASS
Reason: All timing path groups are clean across all PVT corners
INFO01:
  - View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'reg2reg' setup: WNS=0.1234ns (0 violations)
  - View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'cgdefault' setup: WNS=0.0567ns (0 violations)
  - View 'func_rcff_0p945v_m40c_pcff_cmin_pcss3_hold' path_group 'reg2reg' hold: WNS=0.0234ns (0 violations)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Timing violations detected in one or more path groups
ERROR01:
  - View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'default' setup: WNS=-0.2318ns (40 violations)
  - View 'test_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'reg2reg' setup: WNS=-0.0145ns (3 violations)
```

---

## Type 2: Value comparison

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-11:
  description: "Confirm the timing of all path groups is clean."
  requirements:
    value: 2  # MUST equal the number of pattern_items (2 patterns below)
    pattern_items:
      - "View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'reg2reg' setup"
      - "View 'func_rcff_0p945v_m40c_pcff_cmin_pcss3_hold' path_group 'default' hold"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/check_signoff.results
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 checks if the number of clean timing results matching the specified patterns equals the expected value. The checker searches for INFO01 entries (clean timing) that match each pattern string. PASS occurs when exactly `requirements.value` patterns are found clean. This is useful for verifying specific critical corners are clean.

**Sample Output (PASS):**
```
Status: PASS
Reason: All timing path groups are clean across all PVT corners
INFO01:
  - View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'reg2reg' setup: WNS=0.1234ns (0 violations)
  - View 'func_rcff_0p945v_m40c_pcff_cmin_pcss3_hold' path_group 'default' hold: WNS=0.0456ns (0 violations)
```

---

## Type 3: Value Check with Waivers

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-11:
  description: "Confirm the timing of all path groups is clean."
  requirements:
    value: 1  # MUST equal the number of pattern_items (1 pattern below)
    pattern_items:
      - "View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'reg2reg' setup"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/check_signoff.results
  waivers:
    value: 2  # Number of waiver entries (separate from requirements.value)
    waive_items:
      - name: "View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'default' setup: WNS=-0.2318ns (40 violations)"
        reason: "Waived per design review - non-critical debug path, will be fixed in next revision"
      - name: "View 'test_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'cgdefault' setup: WNS=-0.0145ns (3 violations)"
        reason: "Waived - test mode only, does not affect functional operation"
```

**Check Behavior:**
Type 3 combines value comparison with waiver support. The checker verifies that the number of clean (non-waived) timing results matching `pattern_items` equals `requirements.value`. Violations matching `waive_items` are excluded from ERROR01 and moved to INFO01 with [WAIVER] tag. Unused waivers are reported in WARN01.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Clean):
  - View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'reg2reg' setup: WNS=0.1234ns (0 violations)
INFO01 (Waived):
  - View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'default' setup: WNS=-0.2318ns (40 violations) [WAIVER: Waived per design review - non-critical debug path, will be fixed in next revision]
  - View 'test_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'cgdefault' setup: WNS=-0.0145ns (3 violations) [WAIVER: Waived - test mode only, does not affect functional operation]
```

---

## Type 4: Boolean Check with Waivers

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-11:
  description: "Confirm the timing of all path groups is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/check_signoff.results
  waivers:
    value: 1
    waive_items:
      - name: "View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'default' setup: WNS=-0.2318ns (40 violations)"
        reason: "Approved waiver - false path not properly constrained, will be fixed in SDC update"
```

**Check Behavior:**
Type 4 performs a global boolean check with waiver support. All timing violations are checked; those matching `waive_items` are moved to INFO01 with [WAIVER] tag. If all violations are waived, status is PASS. If any unwaived violations remain, status is FAIL. Unused waivers are reported in WARN01.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Clean):
  - View 'func_rcff_0p945v_m40c_pcff_cmin_pcss3_hold' path_group 'reg2reg' hold: WNS=0.0234ns (0 violations)
INFO01 (Waived):
  - View 'func_rcss_0p675v_125c_pcss_cmax_pcff3_setup' path_group 'default' setup: WNS=-0.2318ns (40 violations) [WAIVER: Approved waiver - false path not properly constrained, will be fixed in SDC update]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-11 --force

# Run individual tests
python IMP-10-0-0-11.py
```

---

## Notes

- **Column Alignment**: The parser handles flexible whitespace in CSV-like format. Columns may be aligned with varying spaces.
- **Not Applicable Entries**: Cells with "---" indicate the timing check was not performed for that path group/corner combination (e.g., hold checks not run on setup-only views).
- **Multiple Files**: If multiple report files exist, results are aggregated across all files.
- **Edge Cases**:
  - Empty files: Report INFO01 with "0 views analyzed"
  - Missing headers: Cannot parse, report ERROR01 format issue
  - All "---" columns for a view: Skip view or report as INFO (view not analyzed)
- **Waiver Matching**: Waiver names must exactly match the ERROR01 format string including view name, path group, timing type, WNS value, and violation count.
- **Performance**: For large reports with hundreds of corners, parsing may take several seconds. Consider optimizing regex compilation if performance issues arise.