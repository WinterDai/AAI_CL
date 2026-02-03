# IMP-10-0-0-25: Confirm check_timing report has no issue.

## Overview

**Check ID:** IMP-10-0-0-25**Description:** Confirm check_timing report has no issue.**Category:** Static Timing Analysis (STA) - Timing Constraints Verification**Input Files:**

- `${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_func.rpt`
- `${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_scan.rpt`

This checker validates that PrimeTime/Tempus `check_timing` reports contain no timing constraint issues. It parses both functional and scan mode reports to detect violations such as missing clocks, unconstrained endpoints, ideal clock waveforms, and missing drive assertions. The checker aggregates warning counts across all views and reports individual violations with their associated timing views.

---

## Check Logic

### Input Parsing

The checker parses PrimeTime/Tempus `check_timing` reports using a multi-section state machine approach:

1. **TIMING CHECK SUMMARY Section**: Extract warning type counts
2. **TIMING CHECK DETAIL Section**: Extract individual pin/signal violations (multi-line and single-line formats)
3. **TIMING CHECK IDEAL CLOCKS Section**: Extract ideal clock violations

**Key Patterns:**

```python
# Pattern 1: Summary table warning counts
pattern_summary = r'^\s*(\S+)\s+(.+?)\s+(\d+)\s*$'
# Example: "    clock_expected           Clock not found where clock is expected    2"
# Captures: ('clock_expected', 'Clock not found where clock is expected', '2')

# Pattern 2: Single-line detail violations (no_drive warnings)
pattern_single_line = r'^\s*(\S+)\s+(No drive assertion)\s+(func_\S+|scan_\S+)\s*$'
# Example: "    tx_bscan_ext_clockdr             No drive assertion               func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
# Captures: ('tx_bscan_ext_clockdr', 'No drive assertion', 'func_rcff_0p825v_125c_pcff_cmin_pcff3_hold')

# Pattern 3: Multi-line detail violations (pin name on first line)
pattern_pin_name = r'^\s*([^\s].+?)\s*$'
# Example: "    u_pma_top/u_xcvr_ra/u_pwr_isl_ctrl_sm_icfg_xcal/u_scan_mux_state_sandh/u_scan_mux_synth/u_scan_mux_synth/clk1"
# Next line (indented ~37 spaces): "                                     Clock not found where clock is expected"
# Next line (indented ~54 spaces): "                                                                      func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"

# Pattern 4: Ideal clock entries
pattern_ideal_clock = r'^\s*([A-Z_0-9]+)\s+(func_\S+|scan_\S+)\s*$'
# Example: "    PHY_IO_RESET                     func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
# Captures: ('PHY_IO_RESET', 'func_rcff_0p825v_125c_pcff_cmin_pcff3_hold')

# Pattern 5: Section headers for state machine control
pattern_section = r'^\s*(TIMING CHECK SUMMARY|TIMING CHECK DETAIL|TIMING CHECK IDEAL CLOCKS)\s*$'
# Example: "                                 TIMING CHECK SUMMARY"
```

### Detection Logic

1. **Initialize State Machine**: Track current parsing section (SUMMARY, DETAIL, IDEAL_CLOCKS, NONE)
2. **Parse Each File**:
   - Detect section headers to switch parsing modes
   - In SUMMARY section: Extract warning types and counts using pattern_summary
   - In DETAIL section:
     - Buffer consecutive non-empty lines
     - Classify as single-line (pattern_single_line) or multi-line (pattern_pin_name + continuation lines)
     - Extract pin/signal name, warning description, and view name
   - In IDEAL_CLOCKS section: Extract clock names and views using pattern_ideal_clock
3. **Aggregate Results**: Combine warning counts and violation lists across all input files
4. **Classification**:
   - **PASS**: Total warning count = 0 (no violations found)
   - **FAIL**: Total warning count > 0 (violations detected)
5. **Output Formatting**:
   - INFO01: For each view, display each warning_type once with its occurrence count (e.g., "clock_expected (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold")
   - ERROR01: For each view, display each warning_type once with its occurrence count (e.g., "clock_expected (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold")
   - WARN01: For each view, display each warning_type once with its occurrence count (e.g., "clock_expected (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold")

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# Item description for this checker
item_desc = "Confirm check_timing report has no issue."

# PASS case - what message to show when check passes
found_reason = "All timing views have no check_timing violations"
found_desc = "Check_timing verification passed - no constraint issues detected"

# FAIL case - what message to show when check fails
missing_reason = "Check_timing violations detected across timing views"
missing_desc = "Check_timing verification failed - constraint issues require resolution"

# WAIVED case (Type 3/4) - what message to show for waived items
waived_base_reason = "Check_timing violations waived per design team approval"
waived_desc = "Waived check_timing violations"

# UNUSED waivers - what message to show for unused waiver entries
unused_waiver_reason = "Waiver not matched - no corresponding check_timing violation found"
unused_desc = "Unused check_timing waiver entries"
```

### INFO01/ERROR01/WARN01 Display Format

```
INFO01 (Clean/Pass items - summary counts per view):
  Format: "{warning_type} ({count} occurrences) | View: {view}"
  Example: "clock_expected (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  Example: "ideal_clock_waveform (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  Example: "no_drive (3 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"

ERROR01 (Violation/Fail items - summary counts per view):
  Format: "{warning_type} ({count} occurrences) | View: {view}"
  Example: "no_drive (3 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  Example: "clock_expected (2 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  Example: "ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"

WARN01 (Warning items - summary counts per view):
  Format: "{warning_type} ({count} occurrences) | View: {view}"
  Example: "uncons_endpoint (5 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  Example: "no_input_delay (2 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-25:
  description: "Confirm check_timing report has no issue."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_func.rpt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_scan.rpt"
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
Reason: All timing views have no check_timing violations
INFO01:
  - clock_expected (0 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - ideal_clock_waveform (0 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - no_drive (0 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - uncons_endpoint (0 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Check_timing violations detected across timing views
ERROR01:
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - clock_expected (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-25:
  description: "Confirm check_timing report has no issue."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_func.rpt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_scan.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Check_timing violations are informational only for this IP release"
      - "Note: Missing drive assertions on scan clocks are expected in DFT mode and do not affect functional timing"
      - "Note: Ideal clock waveforms on reset signals are acceptable per design specification"
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
  - "Explanation: Check_timing violations are informational only for this IP release"
  - "Note: Missing drive assertions on scan clocks are expected in DFT mode and do not affect functional timing"
  - "Note: Ideal clock waveforms on reset signals are acceptable per design specification"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-25:
  description: "Confirm check_timing report has no issue."
  requirements:
    value: 3
    pattern_items:
      - "no_drive|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "no_drive|View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "ideal_clock_waveform|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_func.rpt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_scan.rpt"
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
Reason: All timing views have no check_timing violations
INFO01:
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-25:
  description: "Confirm check_timing report has no issue."
  requirements:
    value: 3
    pattern_items:
      - "no_drive|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "no_drive|View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "ideal_clock_waveform|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_func.rpt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_scan.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Check_timing pattern mismatches are informational only for this verification phase"
      - "Note: Drive assertion warnings on BSCAN signals are expected in boundary scan mode"
      - "Note: Ideal clock waveforms on asynchronous resets are acceptable per STA methodology"
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
  - "Explanation: Check_timing pattern mismatches are informational only for this verification phase"
  - "Note: Drive assertion warnings on BSCAN signals are expected in boundary scan mode"
  - "Note: Ideal clock waveforms on asynchronous resets are acceptable per STA methodology"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-25:
  description: "Confirm check_timing report has no issue."
  requirements:
    value: 3
    pattern_items:
      - "no_drive|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "no_drive|View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "ideal_clock_waveform|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_func.rpt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_scan.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "no_drive | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
        reason: "Waived per design review - BSCAN clock driven externally by test controller"
      - name: "ideal_clock_waveform | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
        reason: "Waived per STA methodology - asynchronous reset with ideal waveform is acceptable"
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
Status: FAIL
Reason: Check_timing violations detected across timing views
INFO01 (Waived):
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVER: Waived per design review - BSCAN clock driven externally by test controller]
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVER: Waived per STA methodology - asynchronous reset with ideal waveform is acceptable]
ERROR01 (Unwaived):
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-25:
  description: "Confirm check_timing report has no issue."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_func.rpt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/check_timing_scan.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "no_drive | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
        reason: "Waived per design review - BSCAN clock driven externally by test controller"
      - name: "ideal_clock_waveform | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
        reason: "Waived per STA methodology - asynchronous reset with ideal waveform is acceptable"
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
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVER: Waived per design review - BSCAN clock driven externally by test controller]
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVER: Waived per STA methodology - asynchronous reset with ideal waveform is acceptable]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-25 --force

# Run individual tests
python IMP-10-0-0-25.py
```

---

## Notes

- **Multi-line Parsing**: The checker handles both single-line violations (e.g., "No drive assertion") and multi-line violations (pin name on first line, warning on second line, view on third line). A line buffer is used to accumulate multi-line entries before processing.
- **State Machine**: Section headers control parsing mode. The checker switches between SUMMARY, DETAIL, and IDEAL_CLOCKS states to apply appropriate regex patterns.
- **View Aggregation**: Violations are reported with their associated timing view names (e.g., `func_rcff_0p825v_125c_pcff_cmin_pcff3_hold`, `scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold`) to enable view-specific debugging.
- **Warning Categories**: Common warning types include `clock_expected`, `ideal_clock_waveform`, `no_drive`, and `uncons_endpoint`. The checker aggregates counts across all categories.
- **Indentation Detection**: Multi-line entries are identified by indentation level (pin names at column 4-5, warnings indented ~37 spaces, views indented ~54 spaces).
- **File Aggregation**: Results from both `check_timing_func.rpt` and `check_timing_scan.rpt` are combined into a single violation list.
- **Per-View Warning Type Display**: Each warning_type is displayed only once per view, with the total occurrence count for that warning_type in that specific view. This provides a cleaner summary while maintaining view-specific granularity. The format applies to INFO, ERROR, and WARN outputs.
