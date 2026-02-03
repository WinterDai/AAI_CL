# IMP-7-0-0-05: Confirm no issue for check_design in Innovus.

## Overview

**Check ID:** IMP-7-0-0-05  
**Description:** Confirm no issue for check_design in Innovus.  
**Category:** Design Rule Check (DRC)  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-05.rpt`

This checker validates the Innovus `check_design` report to ensure no design rule violations exist across multiple categories including netlist connectivity, power intent, timing constraints, placement rules, and optimization checks. The checker parses Tcl dict-formatted violation data and reports errors/warnings by category and severity.

---

## Check Logic

### Input Parsing
The checker parses Innovus `check_design` reports in Tcl dict format, extracting violations grouped by category (netlist, power_intent, timing, place, opt). Each violation includes a check ID, severity level (error/warning), count, descriptive message, and list of violating objects.

**Key Patterns:**
```python
# Pattern 1: Design check category header
pattern1 = r'^#Design Check : (\w+) \((\d+)\)'
# Example: "#Design Check : netlist (5)"

# Pattern 2: Check ID and category block start
pattern2 = r'^dict set design_checks (\w+) ([A-Z0-9-]+) \{'
# Example: "dict set design_checks netlist CHKNETLIST-1 {"

# Pattern 3: Severity level
pattern3 = r'^\s+severity\s+(error|warning)'
# Example: "  severity warning"

# Pattern 4: Violation count
pattern4 = r'^\s+count\s+(\d+)'
# Example: "  count 5"

# Pattern 5: Violation list items
pattern5 = r'^\s+\{(.+?)\}\s*$'
# Example: "    {inst_data_lvl_top/dfi_rddata_en[1]}"

# Pattern 6: Message text
pattern6 = r'^# Message: (.+)'
# Example: "# Message: Hierarchy instance input hpin '%s' is undriven."
```

### Detection Logic
1. **Scan for category headers**: Identify design check categories (netlist, power_intent, timing, place, opt) and their total violation counts
2. **Parse check blocks**: For each `dict set design_checks` block, extract:
   - Category name (netlist/power_intent/timing/place/opt)
   - Check ID (e.g., CHKNETLIST-1, IMPMSMV-8623)
   - Severity level (error or warning)
   - Violation count
   - Descriptive message
3. **Extract violation details**: Parse the violations list between `violations {` and closing `}`, handling nested braces for multi-element entries (coordinates, tuples)
4. **Aggregate results**: 
   - Sum violation counts by category and severity for summary statistics
   - Store individual violations grouped by check ID with full context
5. **Determine PASS/FAIL**:
   - PASS: No errors found (warnings may be acceptable depending on configuration)
   - FAIL: One or more errors detected in any category
6. **Handle edge cases**:
   - Empty violations lists (count > 0 but no items listed)
   - Multi-line violation entries with coordinates
   - Truncated reports (indicated by file size limits)
   - Missing severity or count fields
   - Special characters in violation strings (brackets, slashes, spaces)

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
item_desc = "Confirm no issue for check_design in Innovus."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No design rule violations found in check_design report"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All design check categories passed validation"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No errors found in check_design report across all categories"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All design check requirements satisfied and validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Design rule violations detected in check_design report"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Design check requirements not satisfied - violations detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Design rule violations found in check_design report"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Design check requirements not satisfied - violations present"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Design rule violations waived per design review"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Design rule violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for check_design violations"
unused_waiver_reason = "Waiver not matched - no corresponding violation found in check_design report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[category]: no violations (0 errors, 0 warnings)"
  Example: "netlist: no violations (0 errors, 0 warnings)"

ERROR01 (Violation/Fail items):
  Format: "[category]:[CHECK_ID] (severity: X, count: Y): message"
  Example: "power_intent: IMPMSMV-8623 (severity: error, count: 4): Multiple supply nets connected to power pin"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-05:
  description: "Confirm no issue for check_design in Innovus."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-05.rpt"
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
Reason: No errors found in check_design report across all categories
INFO01:
  - netlist: no violations (0 errors, 0 warnings)
  - power_intent: no violations (0 errors, 0 warnings)
  - timing: no violations (0 errors, 0 warnings)
  - place: no violations (0 errors, 0 warnings)
  - opt: no violations (0 errors, 0 warnings)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Design rule violations found in check_design report
ERROR01:
  - power_intent:IMPMSMV-8623 (severity: error, count: 4): Multiple supply nets connected to power pin
  - netlist:CHKNETLIST-1 (severity: warning, count: 5): Hierarchy instance input hpin is undriven
  - place:IMPSP-3508 (severity: error, count: 2): Short between nets
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-05:
  description: "Confirm no issue for check_design in Innovus."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-05.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - design is in early development phase"
      - "Note: Violations are expected during initial floorplanning and will be resolved in optimization phase"
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
  - "Explanation: This check is informational only - design is in early development phase"
  - "Note: Violations are expected during initial floorplanning and will be resolved in optimization phase"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - power_intent:IMPMSMV-8623 (severity: error, count: 4): Multiple supply nets connected to power pin [WAIVED_AS_INFO]
  - netlist:CHKNETLIST-1 (severity: warning, count: 5): Hierarchy instance input hpin is undriven [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-05:
  description: "Confirm no issue for check_design in Innovus."
  requirements:
    value: 5
    pattern_items:
      - "IMPMSMV-8623"
      - "CHKNETLIST-1"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-05.rpt"
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
Reason: All design check requirements satisfied and validated
INFO01:
  - netlist: no violations (0 errors, 0 warnings)
  - power_intent: no violations (0 errors, 0 warnings)
  - timing: no violations (0 errors, 0 warnings)
  - place: no violations (0 errors, 0 warnings)
  - opt: no violations (0 errors, 0 warnings)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-05:
  description: "Confirm no issue for check_design in Innovus."
  requirements:
    value: 0
    pattern_items:
      - "IMPMSMV-8623"
      - "CHKNETLIST-1"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-05.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - design is in pre-tapeout validation phase"
      - "Note: Pattern mismatches are expected during incremental design updates and do not require immediate fixes"
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
  - "Explanation: This check is informational only - design is in pre-tapeout validation phase"
  - "Note: Pattern mismatches are expected during incremental design updates and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - power_intent:IMPMSMV-8623 (severity: error, count: 4): Multiple supply nets connected to power pin [WAIVED_AS_INFO]
  - netlist:CHKNETLIST-1 (severity: warning, count: 5): Hierarchy instance input hpin is undriven [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-05:
  description: "Confirm no issue for check_design in Innovus."
  requirements:
    value: 5
    pattern_items:
      - "IMPMSMV-8623"
      - "CHKNETLIST-1"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-05.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "IMPMSMV-8623"
        reason: "Waived per design review - legacy IP block uses multiple supply routing for redundancy"
      - name: "CHKNETLIST-1"
        reason: "Waived - test mode signal intentionally left unconnected per verification plan"
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
  - power_intent:IMPMSMV-8623 (severity: error, count: 4): Multiple supply nets connected to power pin [WAIVER]
  - netlist CHKNETLIST-1 (severity: warning, count: 5): Hierarchy instance input hpin is undriven [WAIVER]
WARN01 (Unused Waivers):
  - place:IMPSP-3508 (severity: error, count: 2): Short between nets: Waiver not matched - no corresponding violation found in check_design report
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-05:
  description: "Confirm no issue for check_design in Innovus."
  requirements:
    value: N/A
    pattern_items:[]
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-05.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "IMPMSMV-8623"
        reason: "Waived per design review - legacy IP block uses multiple supply routing for redundancy"
      - name: "CHKNETLIST-1"
        reason: "Waived - test mode signal intentionally left unconnected per verification plan"
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
  - power_intent:IMPMSMV-8623 (severity: error, count: 4): Multiple supply nets connected to power pin [WAIVER]
  - netlist:CHKNETLIST-1 (severity: warning, count: 5): Hierarchy instance input hpin is undriven [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 7.0_INNOVUS_DESIGN_IN_CHECK --checkers IMP-7-0-0-05 --force

# Run individual tests
python IMP-7-0-0-05.py
```

---

## Notes

- **Multi-category validation**: The checker validates five design check categories (netlist, power_intent, timing, place, opt) in a single report
- **Severity handling**: Distinguishes between errors (must fix) and warnings (review recommended) based on Innovus severity classification
- **Tcl dict parsing**: Handles nested Tcl dictionary format with proper brace matching for multi-element violations
- **Coordinate handling**: Special parsing for placement violations containing coordinate pairs (x,y tuples)
- **Truncation awareness**: Reports may be truncated at 10KB limit - checker detects and warns about incomplete data
- **Empty violation lists**: Some checks may report count > 0 but omit violation details due to size limits
- **Special characters**: Violation strings may contain brackets, slashes, and spaces requiring careful regex escaping
- **Aggregation logic**: Supports multi-file aggregation to combine results from multiple check_design runs
- **State machine parsing**: Uses line-by-line state tracking to handle nested block structures correctly