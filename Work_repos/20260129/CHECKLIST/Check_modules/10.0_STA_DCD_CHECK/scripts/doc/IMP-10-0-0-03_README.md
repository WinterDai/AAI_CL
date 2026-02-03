# IMP-10-0-0-03: Confirm the units in library match the units in the SDC.

## Overview

**Check ID:** IMP-10-0-0-03  
**Description:** Confirm the units in library match the units in the SDC.  
**Category:** TODO - Add category  
**Input Files:** TODO - List input files

TODO: Add functional description of the checker

---

## Check Logic

### Input Parsing
TODO: Describe how to parse input files

**Key Patterns:**
```python
# Pattern 1: [Description]
pattern1 = r'TODO: Add actual regex pattern'
# Example: "TODO: Add example line from file"
```

### Detection Logic
TODO: Describe check logic step by step

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# Item description for this checker
item_desc = "Confirm the units in library match the units in the SDC."

# PASS case - what message to show when check passes
found_reason = "TODO: e.g., 'All timing corners are clean'"
found_desc = "TODO: e.g., 'Timing signoff verification passed'"

# FAIL case - what message to show when check fails
missing_reason = "TODO: e.g., 'Timing violations detected in N corners'"
missing_desc = "TODO: e.g., 'Timing signoff verification failed'"

# WAIVED case (Type 3/4) - what message to show for waived items
waived_base_reason = "TODO: e.g., 'Timing violation waived per design team approval'"
waived_desc = "TODO: e.g., 'Waived timing violations'"

# UNUSED waivers - what message to show for unused waiver entries
unused_waiver_reason = "TODO: e.g., 'Waiver not matched - no corresponding violation found'"
unused_desc = "TODO: e.g., 'Unused waiver entries'"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: TODO: e.g., "[view_name]: all path groups clean"
  Example: TODO: e.g., "func_rcss_0p675v_125c: setup=0.123ns, hold=0.045ns"

ERROR01 (Violation/Fail items):
  Format: TODO: e.g., "[VIOLATION_TYPE]: [details]"
  Example: TODO: e.g., "TIMING VIOLATION: View=func_rcss, Slack=-0.012ns"
```

---

## Type 1: Boolean check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-03:
  description: "Confirm the units in library match the units in the SDC."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - TODO: Add input file path
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
TODO: Describe Type 1 behavior - global check without waivers.

**Sample Output (PASS):**
```
Status: PASS
Reason: [found_reason from Output Descriptions]
INFO01:
  - [item in INFO01 format]
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: [missing_reason from Output Descriptions]
ERROR01:
  - [item in ERROR01 format]
```

---

## Type 2: Value comparison

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-03:
  description: "Confirm the units in library match the units in the SDC."
  requirements:
    value: 0
    pattern_items:
      - "TODO: pattern1"
      - "TODO: pattern2"
  input_files:
    - TODO: Add input file path
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
TODO: Describe Type 2 behavior - value comparison without waivers.

**Sample Output (PASS):**
```
Status: PASS
Reason: [found_reason]
INFO01:
  - [items matching pattern_items]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-03:
  description: "Confirm the units in library match the units in the SDC."
  requirements:
    value: 0
    pattern_items:
      - "TODO: pattern1"
  input_files:
    - TODO: Add input file path
  waivers:
    value: 2
    waive_items:
      - name: "TODO: item_to_waive_1"
        reason: "TODO: waiver reason 1"
      - name: "TODO: item_to_waive_2"
        reason: "TODO: waiver reason 2"
```

**Check Behavior:**
TODO: Describe Type 3 behavior - value comparison with waivers.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - [waived_item] [WAIVER]
WARN01 (Unused Waivers):
  - [unused_waiver]: [unused_waiver_reason]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-03:
  description: "Confirm the units in library match the units in the SDC."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - TODO: Add input file path
  waivers:
    value: 1
    waive_items:
      - name: "TODO: exception_item"
        reason: "TODO: waiver reason"
```

**Check Behavior:**
TODO: Describe Type 4 behavior - boolean check with waivers.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - [waived_item] [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-03 --force

# Run individual tests
python IMP-10-0-0-03.py

# Type 4
# TODO: Add test commands
```

---

## Notes

TODO: Add notes, limitations, known issues, etc.
