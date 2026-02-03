# IMP-10-0-0-26: Confirm check_design report has no issue.

## Overview

**Check ID:** IMP-10-0-0-26
**Description:** Confirm check_design report has no issue.
**Category:** Physical Design Verification
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_design_func.rpt`

This checker validates the physical design netlist by parsing the check_design report for 16 violation categories: (1) Cells with missing Timing data (2) Annotation to Verilog Netlist (3) Annotation to Physical Netlist (4) Floating Ports (5) Ports Connect to multiple Pads (6) Output pins connected to Power Ground net (7) Floating Instance terminals (8) Tie Hi/Lo output terms floating (9) Output term shorted to Power Ground net (10) Nets with tri-state driver (11) Nets with parallel drivers (12) Nets with multiple drivers (13) Nets with no driver (No FanIn) (14) Tie Hi/Lo instances connected to output (15) Verilog nets with multiple drivers (16) Dont use cells in design. The checker extracts violation counts for each category and reports FAIL if any count > 0.

---

## Check Logic

### Input Parsing

The checker parses the check_design report using a state machine approach to track section context. It identifies main sections (delimited by `==============================`) and subsections (delimited by `------------------------------`), then extracts metric counts and violation lists.

**Key Patterns:**

```python
# Pattern 1: Main section headers
section_header = r'^={30,}\s*$\n^([A-Za-z ]+)\s*$\n^={30,}\s*$'
# Example: "=============================="
#          "SPEF Coverage"
#          "=============================="

# Pattern 2: Subsection headers
subsection_header = r'^\s+-{30,}\s*$\n^\s+([A-Za-z ]+)\s*$\n^\s+-{30,}\s*$'
# Example: "    ------------------------------"
#          "    Floating Port"
#          "    ------------------------------"

# Pattern 3: Metric lines with counts or percentages
metric_line = r'^\s*([A-Za-z][A-Za-z0-9 /()]+):\s*(\d+%?|\d+\.\d+%)\s*$'
# Example: "Annotation to Verilog Netlist: 100%"
# Example: "Cells with missing Timing data: 0"

# Pattern 4: Violation item names (ports/nets/instances)
violation_item = r'^\s+([a-zA-Z_][a-zA-Z0-9_\[\]]*)\s*$'
# Example: "    avdd_h"
# Example: "    agnd"

# Pattern 5: Complex violation entries (multi-column)
complex_violation = r'^\s+([a-zA-Z0-9_/\[\]]+)\s+([a-zA-Z0-9_/\[\]]+)\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+.*?)\s*$'
# Example: "u_dtb_mux/u_reset_sync_scan_ats_mode/u_reset_sync_synth/genblk1_u_reset_sync_synth_4/u_reset_sync_synth_4_1  u_dtb_mux/u_reset_sync_scan_ats_mode/u_reset_sync_synth/genblk1_u_reset_sync_synth_4/PDphy_avdd_TIEHILO_PDphy_avdd_LTIEHI_NET  d  ssb"
```

### Detection Logic

1. **Parse report file line-by-line** searching for the 16 violation categories
2. **Extract violation counts** for each check type:
   - Cells with missing Timing data
   - Annotation to Verilog Netlist / Annotation to Physical Netlist (percentage check)
   - Floating Ports
   - Ports Connect to multiple Pads
   - Output pins connected to Power Ground net
   - Floating Instance terminals
   - Tie Hi/Lo output terms floating
   - Output term shorted to Power Ground net
   - Nets with tri-state driver
   - Nets with parallel drivers
   - Nets with multiple drivers
   - Nets with no driver (No FanIn)
   - Tie Hi/Lo instances connected to output
   - Verilog nets with multiple drivers
   - Dont use cells in design
3. **Collect violation details** when counts are non-zero (port names, net names, instance paths)
4. **Classify results**:
   - Categories with count=0 or 100% coverage → INFO01 (clean)
   - Categories with count>0 or coverage<100% → ERROR01 (violations)
5. **Determine PASS/FAIL**:
   - PASS: All 16 categories have count=0 (or 100% for annotation checks)
   - FAIL: Any category has count>0 (or <100% for annotation checks)

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# Item description for this checker
item_desc = "Confirm check_design report has no issue."

# PASS case - what message to show when check passes
found_reason = "All check_design categories passed with no violations"
found_desc = "Physical design verification clean"

# FAIL case - what message to show when check fails
missing_reason = "check_design violations detected in one or more categories"
missing_desc = "Physical design verification failed"

# WAIVED case (Type 3/4) - what message to show for waived items
waived_base_reason = "check_design violation waived per design team approval"
waived_desc = "Waived check_design violations"

# UNUSED waivers - what message to show for unused waiver entries
unused_waiver_reason = "Waiver not matched - no corresponding check_design violation found"
unused_desc = "Unused check_design waiver entries"
```

### INFO01/ERROR01/WARN01 Display Format

```
INFO01 (Clean/Pass items - categories with count=0):
  Format: "{violation_category} ({count} occurrences)"
  Example: "Cells with missing Timing data (0 occurrences)"
  Example: "Floating Ports (0 occurrences)"
  Example: "Annotation to Verilog Netlist (100%)"
  Example: "Dont use cells in design (0 occurrences)"

ERROR01 (Violation/Fail items - categories with count>0):
  Format: "{violation_category} ({count} occurrences)"
  Example: "Floating Ports (3 occurrences)"
  Example: "Nets with parallel drivers (5 occurrences)"
  Example: "Annotation to Verilog Netlist (95%)"
  Example: "Dont use cells in design (2 occurrences)"

WARN01 (Warning items - if applicable):
  Format: "{violation_category} ({count} occurrences)"
  Example: "Output pins connected to Power Ground net (1 occurrences)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-26:
  description: "Confirm check_design report has no issue."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_design_func.rpt"
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
Reason: All check_design categories passed with no violations
INFO01:
  - SPEF Coverage: Annotation to Verilog Netlist=100%
  - SPEF Coverage: Annotation to Physical Netlist=100%
  - Top Level Netlist Check: Floating Ports=0
  - Instance Pin Check: Cells with missing Timing data=0
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: check_design violations detected in one or more categories
ERROR01:
  - Top Level Netlist Check - Floating Ports: 3 (avdd_h, agnd, avdd)
  - Instance Pin Check - Instances with input pins tied together: 1502
  - Top Level Netlist Check - Nets with parallel drivers: 5 (atb_1, atb_0, eDP, eDM, cmnda_rext)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-26:
  description: "Confirm check_design report has no issue."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_design_func.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Floating ports are expected for analog power pins (avdd_h, agnd, avdd) which are connected at top level"
      - "Note: Tied input pins are standard practice for scan chain integration and do not require fixes"
      - "Note: Parallel drivers on test buses (atb_1, atb_0) are intentional for analog test muxing"
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
  - "Explanation: Floating ports are expected for analog power pins (avdd_h, agnd, avdd) which are connected at top level"
  - "Note: Tied input pins are standard practice for scan chain integration and do not require fixes"
  - "Note: Parallel drivers on test buses (atb_1, atb_0) are intentional for analog test muxing"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Top Level Netlist Check - Floating Ports: 3 (avdd_h, agnd, avdd) [WAIVED_AS_INFO]
  - Instance Pin Check - Instances with input pins tied together: 1502 [WAIVED_AS_INFO]
  - Top Level Netlist Check - Nets with parallel drivers: 5 (atb_1, atb_0, eDP, eDM, cmnda_rext) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-26:
  description: "Confirm check_design report has no issue."
  requirements:
    value: 3
    pattern_items:
      - "Floating Ports: 0"
      - "Annotation to Verilog Netlist: 100%"
      - "Cells with missing Timing data: 0"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_design_func.rpt"
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
Reason: All check_design categories passed with no violations
INFO01:
  - Floating Ports: 0
  - Annotation to Verilog Netlist: 100%
  - Cells with missing Timing data: 0
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-26:
  description: "Confirm check_design report has no issue."
  requirements:
    value: 3
    pattern_items:
      - "Floating Ports"
      - "Annotation to Verilog Netlist"
      - "Cells with missing Timing data"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_design_func.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only during early design phases"
      - "Note: Pattern mismatches for SPEF coverage are expected before final parasitic extraction"
      - "Note: Floating ports will be resolved at top-level integration"
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
  - "Explanation: This check is informational only during early design phases"
  - "Note: Pattern mismatches for SPEF coverage are expected before final parasitic extraction"
  - "Note: Floating ports will be resolved at top-level integration"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Floating Ports: 3 (expected 0) [WAIVED_AS_INFO]
  - Annotation to Verilog Netlist: 95% (expected 100%) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-26:
  description: "Confirm check_design report has no issue."
  requirements:
    value: 3
    pattern_items:
      - "Floating Ports"
      - "Annotation to Verilog Netlist"
      - "Cells with missing Timing data"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_design_func.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Floating Ports"
        reason: "Analog power pins connected at top level - waived per analog team"
      - name: "Nets with parallel drivers"
        reason: "Intentional parallel drivers for analog test bus muxing - design requirement"
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
  - Top Level Netlist Check - Floating Ports: 3 (avdd_h, agnd, avdd) [WAIVER: Analog power pins connected at top level - waived per analog team]
  - Top Level Netlist Check - Nets with parallel drivers: 5 (atb_1, atb_0, eDP, eDM, cmnda_rext) [WAIVER: Intentional parallel drivers for analog test bus muxing - design requirement]
WARN01 (Unused Waivers):
  - (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-26:
  description: "Confirm check_design report has no issue."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_design_func.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Floating Ports"
        reason: "Analog power pins connected at top level - waived per analog team"
      - name: "Instances with input pins tied together"
        reason: "Standard scan chain tie-off practice - approved by DFT team"
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
  - Top Level Netlist Check - Floating Ports: 3 (avdd_h, agnd, avdd) [WAIVER: Analog power pins connected at top level - waived per analog team]
  - Instance Pin Check - Instances with input pins tied together: 1502 [WAIVER: Standard scan chain tie-off practice - approved by DFT team]
WARN01 (Unused Waivers):
  - (none)
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-26 --force

# Run individual tests
python IMP-10-0-0-26.py
```

---

## Notes

- **Multi-file aggregation**: If multiple check_design reports exist (e.g., different corners), violations are aggregated across all files
- **Section coverage**: The checker handles missing sections gracefully (some report variants may omit certain checks)
- **Whitespace handling**: Violation item names are stripped of leading/trailing whitespace to ensure consistent matching
- **Percentage vs count metrics**: The checker distinguishes between percentage-based metrics (e.g., "100%") and absolute counts (e.g., "0")
- **Complex violation formats**: Multi-column violation entries (instance/net pairs) are parsed and formatted for readability
- **Edge cases**: Empty sections with "0" violations are reported as PASS; sections with counts but no item lists are handled appropriately
- **State machine parsing**: The line-by-line parser maintains context for current section/subsection to correctly associate violations with their categories
