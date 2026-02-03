# IMP-12-0-0-26: Confirm BUMP rule DRC result is clean.

## Overview

**Check ID:** IMP-12-0-0-26  
**Description:** Confirm BUMP rule DRC result is clean.  
**Category:** Physical Verification - DRC Check  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_BUMP.rep`
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_BUMP.rep`

This checker validates BUMP layer DRC (Design Rule Check) results from both Calibre and Pegasus verification tools. It parses DRC summary reports to extract violation counts per rule and determines if the design is DRC clean (zero violations across all rules). The checker supports multiple DRC reports and only passes when ALL reports show zero violations. It can waive specific DRC rule violations based on approved exceptions.

---

## Check Logic

### Input Parsing

The checker processes two types of DRC reports with different formats:

**Calibre Report Format:**
- Section-based parsing: Skip "RUNTIME WARNINGS" section, focus on "RULECHECK RESULTS" section
- Extract rule violations from lines matching pattern: `RULE_NAME .......... COUNT`
- Total violations from line: `TOTAL DRC Results Generated: COUNT`

**Pegasus Report Format:**
- Section-based parsing: Extract from DRC check results section
- Extract rule violations from lines matching pattern: `RULECHECK RULE_NAME ... Total Result COUNT`
- Total violations from line: `Total DRC Results : COUNT`

**Key Patterns:**

```python
# Pattern 1: Calibre RULECHECK RESULTS section header
calibre_section_header = r'^---\s+RULECHECK\s+RESULTS'
# Example: "--- RULECHECK RESULTS"

# Pattern 2: Calibre individual rule result with violation count
calibre_rule_result = r'^\s*RULECHECK\s+([A-Za-z0-9_.]+)\s+\.+\s+TOTAL\s+Result\s+Count\s+=\s+(\d+)\s*\('
# Example: "RULECHECK UBM.R.5 .......... TOTAL Result Count = 2 (2)"
# Captures: Group 1 = "UBM.R.5" (rule name), Group 2 = "2" (violation count)

# Pattern 3: Calibre total violations summary
calibre_total = r'^\s*TOTAL\s+DRC\s+Results\s+Generated:\s+(\d+)\s*\('
# Example: "TOTAL DRC Results Generated:     16819 (49568208)"
# Captures: Group 1 = "16819" (total violations)

# Pattern 4: Pegasus RULECHECK result with violation count
pegasus_rule_result = r'^\s*RULECHECK\s+([A-Za-z0-9_.]+)\s+\.+\s+Total\s+Result\s+(\d+)\s*\('
# Example: "RULECHECK UBM.R.5.1 .................................... Total Result          4 (         4)"
# Captures: Group 1 = "UBM.R.5.1" (rule name), Group 2 = "4" (violation count)

# Pattern 5: Pegasus total violations summary
pegasus_total = r'^\s*Total\s+DRC\s+Results\s*:\s+(\d+)\s*\('
# Example: "Total DRC Results                 : 258 (43252)"
# Captures: Group 1 = "258" (total violations)
```

### Detection Logic

1. **Multi-File Processing:**
   - Parse each DRC report file (Calibre and/or Pegasus)
   - Aggregate violations by rule name across all files
   - Track total violation count across all reports

2. **Calibre Report Parsing:**
   - Scan for "--- RULECHECK RESULTS" section header
   - Skip "--- RUNTIME WARNINGS" section (SKEW edges are informational, not violations)
   - Extract rule name and violation count from each RULECHECK line
   - Store rules with violations > 0
   - Extract total violation count from summary line

3. **Pegasus Report Parsing:**
   - Scan for RULECHECK result lines in DRC section
   - Extract rule name and violation count from each result line
   - Store rules with violations > 0
   - Extract total violation count from summary line

4. **Violation Aggregation:**
   - Combine violations from all reports
   - For each rule with violations, record: rule_name, violation_count
   - Calculate total_violations = sum of all rule violations

5. **Waiver Processing (Type 3/4):**
   - Match found violations against waive_items by rule name
   - Classify violations as: waived (approved exceptions) or unwaived (need fix)
   - Track unused waivers (waive_items not matched to any violation)

6. **Pass/Fail Determination:**
   - **Type 1/2:** PASS if total_violations == 0 (DRC clean)
   - **Type 3/4:** PASS if all violations are waived (unwaived_violations == 0)
   - **Type 1/2 with waivers.value=0:** Always PASS (violations shown as INFO)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - Existence Check
**Use when:** pattern_items are items that SHOULD EXIST in input files

```
pattern_items: ["item_A", "item_B", "item_C"]
Input file contains: item_A, item_B

Result:
  found_items:   item_A, item_B    ← Pattern found in file
  missing_items: item_C            ← Pattern NOT found in file

PASS: All pattern_items found in file
FAIL: Some pattern_items not found in file
```

### Mode 2: `status_check` - Status Check  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["port_A", "port_B"]
Input file contains: port_A(fixed), port_B(unfixed), port_C(unfixed)

Result:
  found_items:   port_A            ← Pattern matched AND status correct
  missing_items: port_B            ← Pattern matched BUT status wrong
  (port_C not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates DRC violation status. The pattern_items represent DRC rules to check, and the checker reports only those rules that have violations (wrong status). Rules with zero violations are not reported. This is a status check pattern where we verify that specified DRC rules have clean status (0 violations), and only output rules that fail this status check.

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
item_desc = "Confirm BUMP rule DRC result is clean."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "BUMP DRC verification clean - no violations found in all reports"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All DRC rules passed - zero violations across all checks"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All DRC reports show zero violations - design is DRC clean"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All DRC rule checks satisfied with zero violations"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "BUMP DRC violations detected in reports"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "DRC rule violations found - design not clean"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "DRC violations found - total violation count exceeds zero"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "DRC rule check not satisfied - violations detected"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived DRC violations (approved exceptions)"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "DRC violation waived per design review approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries - no matching violations found"
unused_waiver_reason = "Waiver entry not matched to any DRC violation in reports"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [rule_name]: No violations (0 errors)"
  Example: "- UBM.R.1: No violations (0 errors)"

ERROR01 (Violation/Fail items):
  Format: "- [rule_name]: [violation_count] violations"
  Example: "- UBM.R.5: 2 violations"
  Example: "- UBM.R.5.1: 4 violations"

Summary:
  Format: "Total DRC violations: [total_count] across [rule_count] rules"
  Example: "Total DRC violations: 258 across 15 rules"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-26:
  description: "Confirm BUMP rule DRC result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_BUMP.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_BUMP.rep"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean check: Parse all DRC reports and verify total violations == 0.
PASS if all reports show zero violations (DRC clean).
FAIL if any report shows violations > 0.

**Sample Output (PASS):**
```
Status: PASS
Reason: All DRC reports show zero violations - design is DRC clean
INFO01:
  - Calibre_BUMP.rep: 0 violations - DRC clean
  - Pegasus_BUMP.rep: 0 violations - DRC clean
  - Summary: Total DRC violations: 0 across all reports
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: DRC violations found - total violation count exceeds zero
ERROR01:
  - UBM.R.5: 2 violations (Calibre)
  - UBM.R.5.1: 4 violations (Pegasus)
  - BUMP.M.3: 15 violations (Calibre)
  - Summary: Total DRC violations: 21 across 3 rules
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-26:
  description: "Confirm BUMP rule DRC result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_BUMP.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_BUMP.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: BUMP DRC violations are informational only during early design phase"
      - "Note: Final DRC clean-up will be performed before tapeout"
      - "Rationale: Design team approved to proceed with known BUMP violations for timing closure"
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
  - "Explanation: BUMP DRC violations are informational only during early design phase"
  - "Note: Final DRC clean-up will be performed before tapeout"
  - "Rationale: Design team approved to proceed with known BUMP violations for timing closure"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - UBM.R.5: 2 violations (Calibre) [WAIVED_AS_INFO]
  - UBM.R.5.1: 4 violations (Pegasus) [WAIVED_AS_INFO]
  - BUMP.M.3: 15 violations (Calibre) [WAIVED_AS_INFO]
  - Summary: Total DRC violations: 21 across 3 rules [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-26:
  description: "Confirm BUMP rule DRC result is clean."
  requirements:
    value: 3
    pattern_items:
      - "UBM.R.5"      # Calibre BUMP rule to check
      - "UBM.R.5.1"    # Pegasus BUMP rule to check
      - "BUMP.M.3"     # Another BUMP rule to verify
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_BUMP.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_BUMP.rep"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items are DRC RULE NAMES to check for violations
- Use exact rule names as they appear in DRC reports (e.g., "UBM.R.5", "BUMP.M.3")
- Checker searches for these rules in reports and checks if violation count > 0
- found_items = rules with violations > 0 (FAIL)
- missing_items = rules with violations == 0 (PASS) or rules not found in report

**Check Behavior:**
Type 2 searches pattern_items (DRC rule names) in input files.
This is a VIOLATION CHECK: PASS if found_items empty (no violations detected for specified rules).
FAIL if any pattern_item rule has violations > 0.

**Sample Output (PASS):**
```
Status: PASS
Reason: All DRC rule checks satisfied with zero violations
INFO01:
  - UBM.R.5: 0 violations - rule passed
  - UBM.R.5.1: 0 violations - rule passed
  - BUMP.M.3: 0 violations - rule passed
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: DRC rule check not satisfied - violations detected
ERROR01:
  - UBM.R.5: 2 violations
  - UBM.R.5.1: 4 violations
INFO01:
  - BUMP.M.3: 0 violations - rule passed
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-26:
  description: "Confirm BUMP rule DRC result is clean."
  requirements:
    value: 3
    pattern_items:
      - "UBM.R.5"
      - "UBM.R.5.1"
      - "BUMP.M.3"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_BUMP.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_BUMP.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: These BUMP DRC rules are informational checks only"
      - "Note: Violations are expected during floorplan optimization phase"
      - "Rationale: Design team approved to defer BUMP DRC fixes to post-routing"
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
  - "Explanation: These BUMP DRC rules are informational checks only"
  - "Note: Violations are expected during floorplan optimization phase"
  - "Rationale: Design team approved to defer BUMP DRC fixes to post-routing"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - UBM.R.5: 2 violations [WAIVED_AS_INFO]
  - UBM.R.5.1: 4 violations [WAIVED_AS_INFO]
INFO03:
  - BUMP.M.3: 0 violations - rule passed
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-26:
  description: "Confirm BUMP rule DRC result is clean."
  requirements:
    value: 3
    pattern_items:
      - "UBM.R.5"      # Expected: 0 violations (golden value)
      - "UBM.R.5.1"    # Expected: 0 violations (golden value)
      - "BUMP.M.3"     # Expected: 0 violations (golden value)
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_BUMP.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_BUMP.rep"
  waivers:
    value: 2
    waive_items:
      - name: "UBM.R.5"  # DRC rule name to exempt (NOT violation count!)
        reason: "Waived per design review - legacy BUMP design constraint"
      - name: "BUMP.M.3"  # Another DRC rule to exempt
        reason: "Waived - acceptable spacing for this technology node"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Parse DRC reports and find rules with violations > 0
- Match found violations (by rule name) against waive_items
- Unwaived violations → ERROR (need fix)
- Waived violations → INFO with [WAIVER] tag (approved exceptions)
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived (unwaived_violations == 0).

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - UBM.R.5: DRC violation waived per design review approval: Waived per design review - legacy BUMP design constraint [WAIVER]
ERROR01 (Unwaived - need fix):
  - UBM.R.5.1: 4 violations - not waived
INFO02 (Clean rules):
  - BUMP.M.3: 0 violations - rule passed
WARN01 (Unused Waivers):
  - BUMP.M.3: Waiver entry not matched to any DRC violation in reports: Waived - acceptable spacing for this technology node [WAIVER]
```

**Sample Output (FAIL - unwaived violations):**
```
Status: FAIL
Reason: Unwaived DRC violations found
ERROR01 (Unwaived - need fix):
  - UBM.R.5.1: 4 violations - not waived
INFO01 (Waived):
  - UBM.R.5: DRC violation waived per design review approval: Waived per design review - legacy BUMP design constraint [WAIVER]
WARN01 (Unused Waivers):
  - BUMP.M.3: Waiver entry not matched to any DRC violation in reports: Waived - acceptable spacing for this technology node [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-26:
  description: "Confirm BUMP rule DRC result is clean."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_BUMP.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_BUMP.rep"
  waivers:
    value: 2
    waive_items:
      - name: "UBM.R.5"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived per design review - legacy BUMP design constraint"
      - name: "BUMP.M.3"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - acceptable spacing for this technology node"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (DRC rule names to exempt)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (parse all DRC reports, check total violations), plus waiver classification:
- Parse all DRC reports and extract violations by rule name
- Match violations against waive_items (by rule name)
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - UBM.R.5: DRC violation waived per design review approval: Waived per design review - legacy BUMP design constraint [WAIVER]
ERROR01 (Unwaived - need fix):
  - UBM.R.5.1: 4 violations - not waived
WARN01 (Unused Waivers):
  - BUMP.M.3: Waiver entry not matched to any DRC violation in reports: Waived - acceptable spacing for this technology node [WAIVER]
```

**Sample Output (FAIL - unwaived violations):**
```
Status: FAIL
Reason: Unwaived DRC violations found
ERROR01 (Unwaived - need fix):
  - UBM.R.5.1: 4 violations - not waived
  - BUMP.W.2: 8 violations - not waived
INFO01 (Waived):
  - UBM.R.5: DRC violation waived per design review approval: Waived per design review - legacy BUMP design constraint [WAIVER]
WARN01 (Unused Waivers):
  - BUMP.M.3: Waiver entry not matched to any DRC violation in reports: Waived - acceptable spacing for this technology node [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-26 --force

# Run individual tests
python IMP-12-0-0-26.py
```

---

## Notes

**Multi-Tool Support:**
- Checker supports both Calibre and Pegasus DRC reports in a single run
- Violations are aggregated across all input files
- DRC clean status requires ALL reports to show zero violations

**Report Format Differences:**
- Calibre uses format: `RULECHECK RULE_NAME ... TOTAL Result Count = N (M)`
- Pegasus uses format: `RULECHECK RULE_NAME ... Total Result N (M)`
- Both formats extract first number N as violation count, ignore parenthetical count M

**Waiver Matching:**
- Waivers match by DRC rule name (e.g., "UBM.R.5", "BUMP.M.3")
- Waiver applies to all violations of that rule across all reports
- Unused waivers indicate rule had zero violations or rule name mismatch

**Known Limitations:**
- RUNTIME WARNINGS (SKEW edges) in Calibre reports are ignored as informational
- Acute angle warnings in Pegasus reports are treated as informational, not violations
- Checker assumes DRC report format is consistent with provided examples
- Truncated or malformed reports may cause parsing errors

**Best Practices:**
- Use Type 1 for simple pass/fail DRC clean check
- Use Type 2 when checking specific critical DRC rules
- Use Type 3/4 when approved waivers exist for known violations
- Use waivers.value=0 mode during early design phases when violations are expected