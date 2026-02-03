# IMP-7-0-0-04: Confirm no issue for check_timing (all modes) in Innovus.

## Overview

**Check ID:** IMP-7-0-0-04  
**Description:** Confirm no issue for check_timing (all modes) in Innovus.  
**Category:** Timing Constraint Validation  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-04*.rpt`

This checker validates Innovus `check_timing` reports across all analysis views/modes to ensure timing constraints are properly defined. It parses timing constraint warnings (e.g., missing clocks, ideal clock waveforms, no drive assertions) and reports violations that could lead to incorrect timing analysis. The checker aggregates warnings across multiple view-specific report files and provides both summary statistics and detailed pin-level diagnostics.

---

## Check Logic

### Input Parsing

The checker parses Innovus `check_timing` reports containing three main sections:
1. **TIMING CHECK SUMMARY**: Aggregated warning counts by type
2. **TIMING CHECK DETAIL**: Pin-level warnings with view context
3. **TIMING CHECK IDEAL CLOCKS**: Clocks with ideal waveforms

**Key Patterns:**

```python
# Pattern 1: Warning summary table - extracts warning types and counts
pattern_summary = r'^\s*(\w+)\s+(.+?)\s+(\d+)\s*$'
# Example: "    clock_expected           Clock not found where clock is expected    2"
# Groups: (1) warning_type, (2) description, (3) count

# Pattern 2: Pin-level warning detail - extracts pin/signal name
pattern_pin = r'^\s*([^\s].+?)\s*$'
# Example: "    u_pma_top/u_xcvr_ra/u_pwr_isl_ctrl_sm_icfg_xcal/u_scan_mux_state_sandh/clk1"
# Groups: (1) hierarchical pin/signal path

# Pattern 3: Warning description for specific pin
pattern_description = r'^\s+([A-Z][a-z].+?)\s*$'
# Example: "                                     Clock not found where clock is expected"
# Groups: (1) warning description (capitalized sentence)

# Pattern 4: View name - timing analysis corner
pattern_view = r'^\s+(func_\S+|\S+_hold|\S+_setup)\s*$'
# Example: "                                                                      func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
# Groups: (1) view/corner name

# Pattern 5: Ideal clock list - clock name and view
pattern_ideal_clock = r'^\s*(\S+)\s+(func_\S+|\S+_hold|\S+_setup)\s*$'
# Example: "    PHY_IO_RESET                     func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
# Groups: (1) clock_name, (2) view_name
```

### Detection Logic

1. **Multi-file aggregation**: Iterate through all `IMP-7-0-0-04*.rpt` files matching the glob pattern
2. **Section-based parsing**: Use state machine to identify sections by detecting `---` delimiter lines
3. **Summary section**: Parse warning type, description, and count using pattern_summary
4. **Detail section**: Use 3-line grouping logic:
   - Line 1: Pin/signal name (pattern_pin)
   - Line 2: Warning description (pattern_description)
   - Line 3: View name (pattern_view)
   - Reset grouping on blank line or new pin pattern
5. **Ideal clocks section**: Extract clock names and views using pattern_ideal_clock
6. **Aggregation**: Sum warning counts by type across all files, collect all pin-level violations
7. **Classification**:
   - **PASS**: No timing constraint warnings found (all counts = 0)
   - **FAIL**: Any timing constraint warnings detected (count > 0)
8. **Output formatting**:
   - INFO01: Summary statistics (warning_type: count) when clean
   - ERROR01: Pin-level violations with format `{warning_description} ({total_occurence} occurences) | View: {view_name}`

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
item_desc = "Confirm no issue for check_timing (all modes) in Innovus."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No timing constraint warnings found in check_timing reports"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All timing constraint checks satisfied across all views"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No timing constraint warnings found in check_timing reports across all analysis views"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All timing constraint requirements satisfied and validated across all analysis views"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Timing constraint warnings found in check_timing reports"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Timing constraint requirements not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Timing constraint warnings detected - clocks missing, ideal waveforms, or drive issues found"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Timing constraint requirements not satisfied - expected constraints missing or failed validation"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Timing constraint warnings waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Timing constraint warning waived per design team approval - non-critical path or known limitation"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for timing constraint warnings"
unused_waiver_reason = "Waiver not matched - no corresponding timing constraint warning found in check_timing reports"
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
IMP-7-0-0-04:
  description: "Confirm no issue for check_timing (all modes) in Innovus."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-04*.rpt"
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
Reason: No timing constraint warnings found in check_timing reports across all analysis views
INFO01:
  - clock_expected (0 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - ideal_clock_waveform (0 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - no_drive (0 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - uncons_endpoint (0 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Timing constraint warnings detected - clocks missing, ideal waveforms, or drive issues found
ERROR01:
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - clock_expected (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-04:
  description: "Confirm no issue for check_timing (all modes) in Innovus."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-04*.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Timing constraint warnings are informational during early design phases"
      - "Note: Missing clocks and ideal waveforms are expected in pre-CTS analysis and do not require immediate fixes"
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
  - "Explanation: Timing constraint warnings are informational during early design phases"
  - "Note: Missing clocks and ideal waveforms are expected in pre-CTS analysis and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-04:
  description: "Confirm no issue for check_timing (all modes) in Innovus."
  requirements:
    value: 3
    pattern_items:
      - "no_drive|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "no_drive|View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "ideal_clock_waveform|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-04*.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
- Pattern format: "warning_type|View: view_name" (substring match)
- Matches against grouped violations: "{warning_type} | View: {view}"
- PASS if all required patterns are found
- FAIL if any patterns are missing

**Sample Output (PASS):**
```
Status: PASS
Reason: All timing constraint requirements satisfied and validated across all analysis views (3/3 patterns found)
INFO01:
  - no_drive (2 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - no_drive (1 occurrences) | View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-04:
  description: "Confirm no issue for check_timing (all modes) in Innovus."
  requirements:
    value: 3
    pattern_items:
      - "no_drive|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "no_drive|View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "ideal_clock_waveform|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-04*.rpt"
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
  - ideal_clock_waveform (1 occurrences) | View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-04:
  description: "Confirm no issue for check_timing (all modes) in Innovus."
  requirements:
    value: 3
    pattern_items:
      - "no_drive|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "no_drive|View: scan_shift_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
      - "ideal_clock_waveform|View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-04*.rpt"
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
- Pattern format: "warning_type|View: view_name" (substring match)
- For each required pattern:
  - Pattern clean (no violations) → PASS (found_clean)
  - Pattern matched AND waived → PASS (found_waived)
  - Pattern matched but NOT waived → FAIL (missing_patterns)
- Other waived violations (not matching patterns) → INFO
- Unused waivers → WARN with [WAIVER] tag
- PASS if all required patterns are satisfied (clean or waived)

**Sample Output (with waived items):**
```
Status: FAIL
Reason: Timing constraint requirements not satisfied - expected constraints missing or failed validation
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
IMP-7-0-0-04:
  description: "Confirm no issue for check_timing (all modes) in Innovus."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-04*.rpt"
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
- PASS if all violations are waived

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
python common/regression_testing/create_all_snapshots.py --modules 7.0_INNOVUS_DESIGN_IN_CHECK --checkers IMP-7-0-0-04 --force

# Run individual tests
python IMP-7-0-0-04.py
```

---

## Notes

- **Multi-file aggregation**: The checker processes all files matching `IMP-7-0-0-04*.rpt` pattern and aggregates warnings across views
- **View-specific context**: Each violation includes the analysis view name (e.g., `func_rcff_0p825v_125c_pcff_cmin_pcff3_hold`) for debugging
- **3-line grouping logic**: Detail section parsing requires careful state management to associate pin names with descriptions and views
- **Edge cases handled**:
  - Empty reports (no warnings) → PASS with zero counts
  - Missing sections → gracefully skip unavailable sections
  - Port names vs hierarchical pins → both formats supported
  - Multi-word warning descriptions → full text captured with spaces
- **Common warning types**:
  - `clock_expected`: Clock signal missing at sequential element
  - `ideal_clock_waveform`: Clock defined with ideal (zero-delay) waveform
  - `no_drive`: Signal has no driving source
  - `no_input_delay`: Input port missing input delay constraint
  - `no_output_delay`: Output port missing output delay constraint
- **Waiver matching**: For Type 3/4, waiver names must match the full ERROR01 format including warning description, occurrence count, and view