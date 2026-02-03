# IMP-10-0-0-13: Confirm the max_capacitance check result is clean.

## Overview

**Check ID:** IMP-10-0-0-13
**Description:** Confirm the max_capacitance check result is clean.
**Category:** Static Timing Analysis - Design Rule Checks
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_1.rpt, ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_2.rpt

### Purpose

This checker validates that all nets in the design meet maximum capacitance constraints as defined by the technology library. It parses PrimeTime or similar STA tool reports to detect max_capacitance violations, which occur when the actual capacitance on a net exceeds the maximum allowed value for the driving pin.

### Functional Description

**What is being checked?**
The checker extracts max_capacitance violations from timing reports, identifying:

- Pin names with violations
- Required vs. actual capacitance values
- Slack (negative values indicate violations)
- Timing view/corner where violation occurs

It aggregates violations across multiple report files and provides summary statistics including total violation count, unique timing views affected, and per-violation details.

**Why is this check important for VLSI design?**
Max capacitance violations can cause:

- Signal integrity issues (slow transitions, increased noise susceptibility)
- Timing failures due to excessive RC delay
- Potential reliability problems (electromigration, IR drop)
- Drive strength violations that may not be caught by timing analysis alone

This is a critical sign-off check ensuring the design meets technology library constraints and will function reliably in silicon.

---

## Check Logic

### Input Parsing

The checker parses PrimeTime max_capacitance violation reports using a state machine approach to handle both single-line and multi-line violation entries.

**Key Patterns:**

```python
# Pattern 1: Check type header validation
pattern_check_type = r'^Check type\s*:\s*(\S+)'
# Example: "Check type : max_capacitance"

# Pattern 2: Single-line violation entry (all fields on one line)
pattern_violation_single = r'^\s*(\S+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$'
# Example: "     atb_0                 0.0830            0.1417            -0.0587           func_rcff_0p825v_125c_pcff_cmin_pcss3_hold"

# Pattern 3: Multi-line violation - pin name only (hierarchical paths)
pattern_pin_name = r'^\s*(\S+/\S+)\s*$'
# Example: "     u_pma_top/u_pma_ana_wrapper/u_pma_ana/cmnda_atb_core_0"

# Pattern 4: Multi-line violation - continuation with numeric values
pattern_continuation = r'^\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+(\S+)\s*$'
# Example: "                                                                                 0.1000            0.1417            -0.0417           func_rcff_0p825v_125c_pcff_cmin_pcss3_hold"

# Pattern 5: Table separator (state transition marker)
pattern_separator = r'^\s*-{10,}\s*$'
# Example: "     ----------------------------------------------------------------------------------------------"

# Pattern 6: Column header validation
pattern_header = r'^\s*Pin Name\s+Required\s+Actual\s+Slack\s+View\s*$'
# Example: "      Pin Name               Required          Actual            Slack             View"
```

### Detection Logic

1. **File Iteration**: Process all input files sequentially, aggregating violations across files
2. **State Machine**:
   - `SEARCHING_HEADER`: Look for "Check type : max_capacitance" line
   - `IN_TABLE`: Between separator lines, parse violation entries
   - `PENDING_VALUES`: Pin name captured, waiting for numeric values on next line (for multi-line entries)
3. **Violation Extraction**:
   - Match single-line pattern first (Pattern 2)
   - If no match, check for pin name only (Pattern 3) → transition to PENDING_VALUES state
   - In PENDING_VALUES state, match continuation pattern (Pattern 4) and combine with buffered pin name
4. **Validation**:
   - Only report violations with negative slack
   - Track unique timing views for summary statistics
   - Handle edge cases: empty files, no violations, wrapped pin names
5. **Aggregation**:
   - Combine violations from all input files
   - Generate summary: total count, unique views, severity distribution
   - Format individual violations for ERROR01 output

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
item_desc = "Confirm the max_capacitance check result is clean."

# PASS case - clean items (used in ALL Types)
found_desc = "Clean max_capacitance checks"
found_reason = "No max_capacitance violations detected"

# FAIL case - violations (used in ALL Types)
missing_desc = "Max_capacitance violations detected"
missing_reason = "Max_capacitance violation found"

# WAIVED case (Type 3/4) - waived items
waived_desc = "Waived max_capacitance violations"
waived_base_reason = "Max_capacitance violation waived per design approval"

# UNUSED waivers (Type 3/4) - unused waiver entries
unused_desc = "Unused max_capacitance waiver entries"
unused_waiver_reason = "Waiver entry not matched to any violation"
```

**Code Generator Pattern:**

```python
class CheckerName(BaseChecker, OutputBuilderMixin, WaiverHandlerMixin):
    # Define ONCE at class level - MUST be same across all Types!
    FOUND_DESC = "Clean max_capacitance checks"
    MISSING_DESC = "Max_capacitance violations detected"
    WAIVED_DESC = "Waived max_capacitance violations"
    FOUND_REASON = "No max_capacitance violations detected"
    MISSING_REASON = "Max_capacitance violation found"
    WAIVED_BASE_REASON = "Max_capacitance violation waived per design approval"
  
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
  Format: "Found [count] max_capacitance violations across [view_count] view(s)"
  Example: "Found 0 max_capacitance violations across 0 view(s)"

ERROR01 (Violation/Fail items):
  Format: "Pin '[pin_name]': Required=[required], Actual=[actual], Slack=[slack] (View: [view_name])"
  Example: "Pin 'atb_0': Required=0.0830, Actual=0.1417, Slack=-0.0587 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-13:
  description: "Confirm the max_capacitance check result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_2.rpt
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a global boolean check across all input files without waivers. The checker aggregates all max_capacitance violations and returns PASS only if zero violations are found. Any violation results in FAIL with detailed ERROR01 output showing pin name, slack, and timing view.

**Sample Output (PASS):**

```
Status: PASS
Reason: No max_capacitance violations detected
INFO01:
  - Found 0 max_capacitance violations across 0 view(s)
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Max_capacitance violation found
ERROR01:
  - Pin 'atb_0': Required=0.0830, Actual=0.1417, Slack=-0.0587 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold)
  - Pin 'atb_1': Required=0.0850, Actual=0.1397, Slack=-0.0547 (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
  - Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/cmnda_atb_core_0': Required=0.1000, Actual=0.1417, Slack=-0.0417 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-13:
  description: "Confirm the max_capacitance check result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_2.rpt
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Pre-implementation phase - max_capacitance violations expected before buffer insertion"
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
  - Pre-implementation phase - max_capacitance violations expected before buffer insertion [WAIVED_INFO]
  - Pin 'atb_0': Required=0.0830, Actual=0.1417, Slack=-0.0587 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold) [WAIVED_AS_INFO]
  - Pin 'atb_1': Required=0.0850, Actual=0.1397, Slack=-0.0547 (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVED_AS_INFO]
```

---

## Type 2: Value comparison

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-13:
  description: "Confirm the max_capacitance check result is clean."
  requirements:
    value: 2  # MUST equal the number of pattern_items (2 patterns below)
    pattern_items:
      - "atb_0"
      - "atb_1"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_2.rpt
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 validates that the exact set of expected violations (defined in pattern_items) are found in the reports. The checker returns PASS only if the detected violations exactly match the pattern_items list (both count and content). This is useful for regression testing where specific violations are expected and tracked.

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Max_capacitance violation found
ERROR01:
  - Pin 'atb_0': Required=0.0830, Actual=0.1417, Slack=-0.0587 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold)
  - Pin 'atb_1': Required=0.0850, Actual=0.1397, Slack=-0.0547 (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-13:
  description: "Confirm the max_capacitance check result is clean."
  requirements:
    value: 2
    pattern_items:
      - "atb_0"
      - "atb_1"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_2.rpt
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Debug mode - tracking violations for analysis only"
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
IMP-10-0-0-13:
  description: "Confirm the max_capacitance check result is clean."
  requirements:
    value: 3  # MUST equal the number of pattern_items (3 patterns below)
    pattern_items:
      - "atb_0'"
      - "atb_1"
      - "u_pma_top/u_pma_ana_wrapper/u_pma_ana/cmnda_atb_core_0"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_2.rpt
  waivers:
    value: 2  # Number of waiver entries (separate from requirements.value)
    waive_items:
      - name: "atb_0"
        reason: "Waived per design review - test mode pin with relaxed constraints"
      - name: "atb_1"
        reason: "Waived per design review - analog test bus with external buffering"
```

**Check Behavior:**
Type 3 validates that expected violations match pattern_items, but allows specific violations to be waived. The checker matches detected violations against waive_items and moves matched violations to INFO01 with [WAIVER] tag. PASS is achieved when all violations are either waived or match expected patterns. Unused waivers are reported in WARN01.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Pin 'atb_0': Required=0.0830, Actual=0.1417, Slack=-0.0587 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold) [WAIVER]
  - Pin 'atb_1': Required=0.0850, Actual=0.1397, Slack=-0.0547 (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold) [WAIVER]
ERROR01:
  - Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/cmnda_atb_core_0': Required=0.1000, Actual=0.1417, Slack=-0.0417 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold)
```

---

## Type 4: Boolean Check with Waivers

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-13:
  description: "Confirm the max_capacitance check result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_1.rpt
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/maxcap_2.rpt
  waivers:
    value: 2
    waive_items:
      - name: "atb_0"
        reason: "Waived per design review - test mode pin with relaxed constraints"
      - name: "u_pma_top/u_pma_ana_wrapper/u_pma_ana/cmnda_atb_core_0"
        reason: "Waived per design review - analog core pin with external load management"
```

**Check Behavior:**
Type 4 performs a global boolean check but allows specific violations to be waived. The checker aggregates all violations, matches them against waive_items, and returns PASS if all violations are waived. Unwaived violations result in FAIL with ERROR01 output. Unused waivers are reported in WARN01.

**Sample Output:**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Pin 'atb_0': Required=0.0830, Actual=0.1417, Slack=-0.0587 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold) [WAIVER]
  - Pin 'u_pma_top/u_pma_ana_wrapper/u_pma_ana/cmnda_atb_core_0': Required=0.1000, Actual=0.1417, Slack=-0.0417 (View: func_rcff_0p825v_125c_pcff_cmin_pcss3_hold) [WAIVER]
WARN01 (Unused Waivers):
  - Pin 'atb_1': Required=0.0850, Actual=0.1397, Slack=-0.0547 (View: func_rcff_0p825v_125c_pcff_cmin_pcff3_hold): Waiver entry not matched to any violation
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-13 --force

# Run individual tests
python IMP-10-0-0-13.py
```

---

## Notes

- **Multi-line Handling**: The checker uses a state machine to handle hierarchical pin names that wrap across multiple lines in the report
- **View Aggregation**: Violations are tracked per timing view/corner to support multi-corner analysis
- **Slack Filtering**: Only negative slack values are reported as violations (positive slack indicates margin)
- **File Aggregation**: All input files are processed and violations are combined for a comprehensive check
- **Edge Cases**:
  - Empty reports or reports with no violations return clean status
  - Truncated reports (with limit messages) are handled gracefully
  - Missing view columns (older report formats) are supported with degraded information
- **Performance**: For large designs with thousands of violations, consider using pattern_items (Type 2/3) to focus on critical nets only
