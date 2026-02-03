# IMP-10-0-0-12: Confirm the max_transition check result is clean.

## Overview

**Check ID:** IMP-10-0-0-12  
**Description:** Confirm the max_transition check result is clean.  
**Category:** Static Timing Analysis  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_1.rpt, ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_2.rpt

### Purpose

This checker validates that all signals in the design meet maximum transition time constraints across all timing views. Maximum transition violations indicate signals that switch too slowly, which can cause timing failures, increased power consumption, and signal integrity issues.

### Functional Description

**What is being checked?**
The checker parses max_transition violation reports to extract pins that exceed their required transition time limits. For each violation, it captures the pin name, required limit, actual transition value, slack (negative indicates violation), and the timing view/corner where the violation occurs. The checker aggregates violations across multiple report files and validates that the total violation count is zero.

**Why is this check important for VLSI design?**
Maximum transition violations can cause:
- Setup/hold timing failures due to slow signal edges
- Increased dynamic power consumption
- Signal integrity issues (crosstalk susceptibility, noise margin degradation)
- Functional failures in high-speed interfaces
- Manufacturing yield loss

Clean max_transition results are mandatory for timing sign-off and ensure the design meets performance and reliability targets across all process corners.

---

## Check Logic

### Input Parsing

The checker processes max_transition violation reports with both single-line and multi-line entry formats.

**Key Patterns:**
```python
# Pattern 1: Report header validation
pattern_header = r'^Check type\s*:\s*max_transition'
# Example: "Check type : max_transition"

# Pattern 2: Table header (marks start of violation data)
pattern_table_header = r'^\s*Pin Name\s+Required\s+Actual\s+Slack\s+View\s*$'
# Example: "     Pin Name               Required          Actual            Slack             View              "

# Pattern 3: Single-line violation entry (all fields on one line)
pattern_single_line = r'^\s*(\S+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$'
# Example: "     cmn_ref_clk_int       0.4000            0.4306            -0.0306           at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold"

# Pattern 4: Multi-line entry - pin name on first line
pattern_pin_name = r'^\s*([a-zA-Z0-9_/]+)\s*$'
# Example: "     u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m"

# Pattern 5: Multi-line entry - continuation line with numeric values
pattern_continuation = r'^\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$'
# Example: "                           0.0000            0.5108            -0.5108           at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold"

# Pattern 6: Negative slack filter (violation indicator)
pattern_violation = r'(-\d+\.\d+)'
# Extracts negative slack values to identify actual violations
```

### Detection Logic

1. **File Validation**: Verify each input file contains "Check type : max_transition" header
2. **State Machine Parsing**:
   - INIT → HEADER: On detecting check type header
   - HEADER → TABLE_START: On finding table header with column names
   - TABLE_START → DATA: Begin parsing violation entries
   - DATA → DATA: Continue until end of file
3. **Violation Extraction**:
   - For single-line entries: Extract all 5 fields (pin, required, actual, slack, view) in one regex match
   - For multi-line entries: Capture pin name, then parse next line for numeric values
   - Track pending_pin_name state variable for multi-line handling
4. **Violation Filtering**: Only report entries where slack < 0 (negative slack = violation)
5. **Aggregation**: Combine violations from all input files, count total violations
6. **Success Criteria**: violation_count == 0 (all slacks >= 0 or no violation entries)

**Edge Cases Handled**:
- Empty reports (header only, no violations) → PASS with 0 violations
- Multi-line entries where hierarchical pin names wrap
- Whitespace variations in column alignment
- Mixed positive/negative slacks (only negative reported as violations)
- Missing view names (use "default" if omitted)
- Separator lines (dashes) between sections

---

## Output Descriptions (CRITICAL - Code Generator Will Use These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

**⚠️ CRITICAL RULE: These descriptions MUST be used IDENTICALLY across ALL Type 1/2/3/4!**
- Same checker = Same descriptions, regardless of which Type is detected at runtime
- Code generator should define these as CLASS CONSTANTS and reuse them in all _execute_typeN() methods

```python
# ⚠️ CRITICAL: These descriptions MUST be used IDENTICALLY across ALL Type 1/2/3/4!
# Define as class constants, then use self.FOUND_DESC, self.MISSING_DESC, etc.

# Item description for this checker
item_desc = "Confirm the max_transition check result is clean."

# PASS case - clean items (used in ALL Types)
found_desc = "Clean max_transition checks (no violations)"
found_reason = "All pins meet maximum transition time requirements"

# FAIL case - violations (used in ALL Types)
missing_desc = "Max_transition violations detected"
missing_reason = "Pin(s) exceed maximum transition time limit"

# WAIVED case (Type 3/4) - waived items
waived_desc = "Waived max_transition violations"
waived_base_reason = "Max_transition violation waived per design approval"

# UNUSED waivers (Type 3/4) - unused waiver entries
unused_desc = "Unused max_transition waiver entries"
unused_waiver_reason = "Waiver entry not matched to any violation"
```

**Code Generator Pattern:**
```python
class CheckerName(BaseChecker, OutputBuilderMixin, WaiverHandlerMixin):
    # Define ONCE at class level - MUST be same across all Types!
    FOUND_DESC = "Clean max_transition checks (no violations)"
    MISSING_DESC = "Max_transition violations detected"
    WAIVED_DESC = "Waived max_transition violations"
    FOUND_REASON = "All pins meet maximum transition time requirements"
    MISSING_REASON = "Pin(s) exceed maximum transition time limit"
    WAIVED_BASE_REASON = "Max_transition violation waived per design approval"
    
    def _execute_type1(self):
        return self.build_complete_output(
            found_desc=self.FOUND_DESC,      # Use constant
            missing_desc=self.MISSING_DESC,  # Use constant
            ...
        )
    
    def _execute_type4(self):
        return self.build_complete_output(
            found_desc=self.FOUND_DESC,      # SAME as Type 1
            missing_desc=self.MISSING_DESC,  # SAME as Type 1
            waived_desc=self.WAIVED_DESC,    # Additional for Type 4
            ...
        )
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "View '[view_name]': 0 max_transition violations"
  Example: "View 'func_rcff_0p825v_125c_pcff_cmin_pcff3_hold': 0 max_transition violations"

ERROR01 (Violation/Fail items):
  Format: "Pin '[pin_name]': Required=[required]ns, Actual=[actual]ns, Slack=[slack]ns (View: [view_name])"
  Example: "Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-12:
  description: "Confirm the max_transition check result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_2.rpt
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a global boolean check across all input files without waivers. The checker aggregates all max_transition violations and returns PASS only if zero violations are found. All violations are reported as ERROR01 items.

**Sample Output (PASS):**
```
Status: PASS
Reason: All pins meet maximum transition time requirements
INFO01:
  - View 'at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold': 0 max_transition violations
  - View 'func_rcff_0p825v_125c_pcff_cmin_pcff3_hold': 0 max_transition violations
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Pin(s) exceed maximum transition time limit
ERROR01:
  - Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
  - Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
  - Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-10-0-0-12:
  description: "Confirm the max_transition check result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_2.rpt
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Pre-implementation phase - max_transition violations expected during floorplanning"
```

**Special Behavior (waivers.value=0):**
⚠️ **CRITICAL**: When `waivers.value=0`, `waive_items` MUST have content:
- `waive_items` strings → INFO with `[WAIVED_INFO]` suffix (shows reason for forced PASS)
- ALL detected violations → INFO with `[WAIVED_AS_INFO]` suffix (forced conversion)
- Result: **Always PASS** (informational check mode)

**Sample Output:**
```
Status: PASS (forced)
Reason: All items converted to informational
INFO01:
  - Pre-implementation phase - max_transition violations expected during floorplanning [WAIVED_INFO]
  - Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVED_AS_INFO]
  - Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVED_AS_INFO]
```

---

## Type 2: Value comparison

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-12:
  description: "Confirm the max_transition check result is clean."
  requirements:
    value: 2  # MUST equal the number of pattern_items (2 patterns below)
    pattern_items:
      - "Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
      - "Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_2.rpt
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 validates that exactly `requirements.value` violations matching the specified patterns are found. This is useful for regression testing where a known set of violations is expected. The checker returns PASS only if the detected violations exactly match the pattern_items list (both count and content).

**Sample Output (PASS):**
```
Status: PASS
Reason: All pins meet maximum transition time requirements
INFO01:
  - Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
  - Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-10-0-0-12:
  description: "Confirm the max_transition check result is clean."
  requirements:
    value: 2
    pattern_items:
      - "Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
      - "Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_2.rpt
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Debug mode - tracking known violations for analysis"
```

**Special Behavior (waivers.value=0):**
⚠️ **CRITICAL**: `waive_items` MUST have content:
- `waive_items` strings → INFO with `[WAIVED_INFO]` suffix
- ALL violations/missing items → INFO with `[WAIVED_AS_INFO]` suffix
- Result: **Always PASS**

---

## Type 3: Value Check with Waivers

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-12:
  description: "Confirm the max_transition check result is clean."
  requirements:
    value: 3  # MUST equal the number of pattern_items (3 patterns below)
    pattern_items:
      - "Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
      - "Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
      - "Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_2.rpt
  waivers:
    value: 2  # Number of waiver entries (separate from requirements.value)
    waive_items:
      - name: "Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
        reason: "Analog interface pin - transition controlled by external circuit"
      - name: "Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
        reason: "Low-speed reference clock - minor violation acceptable per design spec"
```

**Check Behavior:**
Type 3 validates that exactly `requirements.value` violations are found, but allows specific violations to be waived. The checker matches detected violations against waive_items and moves matched items to INFO01 with [WAIVER] tag. Only unwaived violations cause FAIL. Unused waiver entries are reported as WARN01.

**Sample Output (with waived items):**
```
Status: FAIL
Reason: Pin(s) exceed maximum transition time limit
INFO01 (Waived):
  - Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVER: Analog interface pin - transition controlled by external circuit]
  - Pin 'cmn_ref_clk_int': Required=0.4000ns, Actual=0.4306ns, Slack=-0.0306ns (View: at_speed_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVER: Low-speed reference clock - minor violation acceptable per design spec]
ERROR01:
  - Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
```

---

## Type 4: Boolean Check with Waivers

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-12:
  description: "Confirm the max_transition check result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxtran_2.rpt
  waivers:
    value: 2
    waive_items:
      - name: "Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
        reason: "Analog interface pin - transition controlled by external circuit"
      - name: "Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)"
        reason: "External resistor pin - slow transition by design"
```

**Check Behavior:**
Type 4 performs a global boolean check but allows specific violations to be waived. The checker aggregates all violations, matches them against waive_items, and returns PASS if all violations are waived. Unwaived violations cause FAIL. Unused waiver entries are reported as WARN01.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/pma_ana_data_m': Required=0.0000ns, Actual=0.5108ns, Slack=-0.5108ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVER: Analog interface pin - transition controlled by external circuit]
  - Pin 'cmnda_rext': Required=0.3000ns, Actual=0.7666ns, Slack=-0.4666ns (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVER: External resistor pin - slow transition by design]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-12 --force

# Run individual tests
python IMP-10-0-0-12.py
```

---

## Notes

**Multi-line Entry Handling**: The checker uses a state machine to handle violations where hierarchical pin names wrap to multiple lines. The pending_pin_name variable tracks partial entries across line boundaries.

**View Aggregation**: Violations are reported per timing view/corner. The same pin may violate in multiple views, and each instance is counted separately.

**Slack Interpretation**: Only negative slack values indicate violations. Positive or zero slack means the pin meets requirements.

**Report Format Variations**: The checker handles both Innovus and PrimeTime report formats, which may have slight differences in column alignment and separator lines.

**Performance Considerations**: For designs with thousands of violations, consider using Type 3/4 with waivers to focus on critical violations and reduce noise in the output.